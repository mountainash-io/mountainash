"""
Cross-module factory infrastructure for mountainash.

Provides BaseStrategyFactory (lazy-loading strategy pattern) and
DataFrameTypeFactoryMixin (DataFrame type detection via string inspection).

These are shared by schema, pydata, and dataframes modules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Type, Optional, Generic, TypeVar, List, Union
import importlib
import importlib.util
import logging
import re
from enum import Enum

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ============================================================================
# Base Factory Mixin
# ============================================================================

class BaseFactoryMixin(ABC):

    @classmethod
    @abstractmethod
    def _type_map(cls) -> Dict[tuple, Enum]:
        pass


# ============================================================================
# Base Strategy Factory
# ============================================================================

# Generic type variables for universal input and strategy types
InputT = TypeVar('InputT')  # Input type constraint
StrategyT = TypeVar('StrategyT')  # Strategy class type constraint
StrategyKeyT = TypeVar('StrategyKeyT')  # Strategy key type constraint


class BaseStrategyFactory(ABC, Generic[InputT, StrategyT]):
    """
    Truly lazy factory that loads strategies only when first needed.

    This factory eliminates the get_available_backends() anti-pattern by:
    1. Using string-based type detection only (no imports)
    2. Loading strategies on first use only
    3. Caching loaded strategies for subsequent use
    4. Providing intelligent fallbacks without upfront availability checking

    Type Parameters:
        InputT: The type constraint for input data
        StrategyT: The strategy class type returned by the factory
    """

    # Class-level storage for each subclass
    _strategy_cache: Dict[Enum, Optional[Type[StrategyT]]] = {}
    _strategy_modules: Dict[Enum, str] = {}
    _strategy_classes: Dict[Enum, str] = {}

    def __init_subclass__(cls, **kwargs):
        """Initialize each subclass with its own strategy storage."""
        super().__init_subclass__(**kwargs)
        cls._strategy_cache = {}
        cls._strategy_modules = {}
        cls._strategy_classes = {}

    @classmethod
    @abstractmethod
    def _configure_strategy_mapping(cls) -> None:
        """
        Configure the mapping from strategy keys to module paths and class names.

        This method should populate _strategy_modules and _strategy_classes
        with the mapping information, but NOT import anything.
        """
        pass

    @classmethod
    @abstractmethod
    def _get_strategy_key(cls, data: InputT, /, **kwargs) -> Optional[Enum]:
        """
        Determine the strategy key for the given input data.
        This should use string-based type detection only, no imports.
        """
        pass

    @classmethod
    def get_strategy(cls, data: InputT, /, **kwargs) -> Type[StrategyT]:
        """
        Get the appropriate strategy for the given input data.
        """
        # Ensure configuration is loaded
        if not cls._strategy_modules:
            cls._configure_strategy_mapping()

        # Step 1: Detect backend using string inspection (no imports)
        strategy_key = cls._get_strategy_key(data, **kwargs)

        if strategy_key is None:
            raise ValueError(f"No strategy key found for data of type {type(data)}")

        # Step 2: Check cache
        if cls._strategy_cache.get(strategy_key, None) is not None:
            strategy_class = cls._strategy_cache.get(strategy_key, None)
            if strategy_class is not None:
                return strategy_class

        # Step 3: Import ONLY this strategy
        try:
            strategy_class = cls._lazy_load_strategy_class(strategy_key) if strategy_key else None

            cls._strategy_cache[strategy_key] = strategy_class if strategy_class else None

            if strategy_class is not None:
                return strategy_class
            else:
                raise ValueError(f"Failed to load strategy for key {strategy_key}: strategy class is None")

        except Exception as e:
            logger.warning(f"Failed to load strategy {strategy_key}: {e}")
            # Cache the failure
            cls._strategy_cache[strategy_key] = None

            raise ValueError(f"Failed to load strategy for key {strategy_key}: {e}")

    @classmethod
    def _lazy_load_strategy_class(cls, strategy_key: Enum) -> Type[StrategyT]:
        """
        Import strategy for specific backend only.
        """
        if strategy_key not in cls._strategy_modules:
            raise ImportError(f"No module mapping for strategy key: {strategy_key}")

        module_path = cls._strategy_modules[strategy_key]
        class_name = cls._strategy_classes[strategy_key]

        module = importlib.import_module(module_path)

        strategy_class = getattr(module, class_name)

        return strategy_class


# ============================================================================
# DataFrame Type Factory Mixin
# ============================================================================

class DataFrameTypeFactoryMixin(BaseFactoryMixin):
    """
    Factory mixin for DataFrame type detection with lazy loading.

    Features enhanced module pattern matching for future-proofing against
    library refactors and reorganizations.
    """

    # Lazy import to avoid circular dependency
    _constants_loaded = False
    _CONST_DATAFRAME_TYPE = None

    @classmethod
    def _ensure_constants(cls):
        if not cls._constants_loaded:
            from mountainash.dataframes.constants import CONST_DATAFRAME_TYPE
            cls._CONST_DATAFRAME_TYPE = CONST_DATAFRAME_TYPE
            cls._constants_loaded = True
        return cls._CONST_DATAFRAME_TYPE

    # Runtime type registration storage (class-level)
    _runtime_type_map: Dict[tuple[str, str], Enum] = {}

    @classmethod
    def _type_map(cls) -> Dict[tuple[str, str], Enum]:
        """
        Static type mappings - exact matches for known library versions.
        Merges with runtime registrations for types discovered via pattern matching.
        """
        CDT = cls._ensure_constants()

        TYPE_MAP = {
            ("pandas.core.frame", "DataFrame"):      CDT.PANDAS_DATAFRAME,

            ("polars.dataframe.frame", "DataFrame"): CDT.POLARS_DATAFRAME,
            ("polars.lazyframe.frame", "LazyFrame"): CDT.POLARS_LAZYFRAME,
            ("polars", "DataFrame"):                 CDT.POLARS_DATAFRAME,
            ("polars", "LazyFrame"):                 CDT.POLARS_LAZYFRAME,

            ("pyarrow.lib", "Table"):                CDT.PYARROW_TABLE,
            ("pyarrow", "Table"):                    CDT.PYARROW_TABLE,

            ("narwhals._pandas_like.dataframe", "DataFrame"): CDT.NARWHALS_DATAFRAME,
            ("narwhals", "DataFrame"):                        CDT.NARWHALS_DATAFRAME,
            ("narwhals.dataframe", "DataFrame"):              CDT.NARWHALS_DATAFRAME,

            ("narwhals._pandas_like.dataframe", "LazyFrame"): CDT.NARWHALS_LAZYFRAME,
            ("narwhals", "LazyFrame"):                        CDT.NARWHALS_LAZYFRAME,
            ("narwhals.dataframe", "LazyFrame"):              CDT.NARWHALS_LAZYFRAME,

            ("ibis.backends.polars", "Backend"):    CDT.IBIS_TABLE,
            ("ibis.backends.duckdb", "Backend"):    CDT.IBIS_TABLE,
            ("ibis.backends.sqlite", "Backend"):    CDT.IBIS_TABLE,
            ("ibis.backends.bigquery", "Backend"):  CDT.IBIS_TABLE,
            ("ibis.backends.databricks", "Backend"): CDT.IBIS_TABLE,
            ("ibis.backends.mssql", "Backend"):     CDT.IBIS_TABLE,
            ("ibis.backends.mysql", "Backend"):     CDT.IBIS_TABLE,
            ("ibis.backends.oracle", "Backend"):    CDT.IBIS_TABLE,
            ("ibis.backends.postgres", "Backend"):  CDT.IBIS_TABLE,
            ("ibis.backends.pyspark", "Backend"):   CDT.IBIS_TABLE,
            ("ibis.backends.snowflake", "Backend"): CDT.IBIS_TABLE,
            ("ibis.backends.sql", "Backend"):       CDT.IBIS_TABLE,
            ("ibis.backends.trino", "Backend"):     CDT.IBIS_TABLE,

            ("ibis.expr.types.relations", "Table"): CDT.IBIS_TABLE,
            ("ibis.expr.types.joins", "Join"): CDT.IBIS_TABLE,
        }

        # Merge with runtime registrations
        return {**TYPE_MAP, **cls._runtime_type_map}

    @classmethod
    def pattern_map(cls) -> Dict[str, Union[tuple[str, Enum], List[tuple[str, Enum]]]]:
        """
        Flexible pattern-based mappings for handling library refactors.
        """
        CDT = cls._ensure_constants()

        PATTERN_MAP = {
            r"^pandas\..*": ("DataFrame", CDT.PANDAS_DATAFRAME),
            r"^polars\..*": [
                ("DataFrame", CDT.POLARS_DATAFRAME),
                ("LazyFrame", CDT.POLARS_LAZYFRAME),
            ],
            r"^pyarrow\..*": ("Table", CDT.PYARROW_TABLE),
            r"^narwhals\..*": [
                ("DataFrame", CDT.NARWHALS_DATAFRAME),
                ("LazyFrame", CDT.NARWHALS_LAZYFRAME),
            ],
            r"^ibis\.backends\..*": ("Backend", CDT.IBIS_TABLE),
            r"^ibis\.expr\..*": [
                ("Table", CDT.IBIS_TABLE),
                ("Join", CDT.IBIS_TABLE),
            ],
        }
        return PATTERN_MAP

    @classmethod
    def _get_type_key(cls, module: str, name: str) -> tuple[str, str]:
        """Cache type information to avoid repeated string operations."""
        return (module, name)

    @classmethod
    def _get_strategy_key(cls, data, /, **kwargs) -> Optional[Enum]:
        """
        Enhanced detection with exact match -> pattern match -> logging.
        """
        obj_type = type(data)
        module = obj_type.__module__
        name = obj_type.__name__
        type_key = cls._get_type_key(module, name)
        type_map = cls._type_map()

        # Layer 1: Exact match (fast path)
        if type_key in type_map:
            backend = type_map.get(type_key)
            logger.debug(f"Exact match: {type_key} -> {backend}")
            return backend

        # Layer 2: Pattern matching (flexible fallback)
        backend = cls._match_by_pattern(module, name)
        if backend:
            logger.info(
                f"Pattern match: {type_key} -> {backend} "
                f"(consider adding to type_map for better performance)"
            )
            # Auto-register for future fast path
            cls._runtime_type_map[type_key] = backend
            return backend

        # Layer 3: Failed - log for monitoring
        logger.warning(
            f"Unmapped type detected: {type_key}\n"
            f"  Module: {module}\n"
            f"  Class: {name}\n"
            f"  MRO: {[c.__module__ + '.' + c.__name__ for c in obj_type.__mro__[:5]]}\n"
            f"  Please register this type or report to maintainers."
        )

        return None

    @classmethod
    def _match_by_pattern(cls, module: str, name: str) -> Optional[Enum]:
        """
        Match module and classname against flexible regex patterns.
        """
        for pattern, mapping in cls.pattern_map().items():
            if re.match(pattern, module):
                mappings = [mapping] if not isinstance(mapping, list) else mapping
                for class_name, backend_type in mappings:
                    if name == class_name:
                        return backend_type
        return None

    @classmethod
    def register_type(
        cls,
        module: str,
        class_name: str,
        backend_type: Enum,
    ) -> None:
        """Runtime registration of new types for exact matching."""
        type_key = (module, class_name)
        cls._runtime_type_map[type_key] = backend_type
        logger.info(f"Registered type: {module}.{class_name} -> {backend_type}")

    @classmethod
    def get_unmapped_types(cls) -> List[tuple[str, str]]:
        """Get list of types that were matched via patterns but not in static map."""
        return list(cls._runtime_type_map.keys())
