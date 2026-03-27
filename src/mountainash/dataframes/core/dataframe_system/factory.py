"""
DataFrameSystemFactory - Factory for creating backend-specific DataFrameSystems.

Provides:
- Automatic backend detection from DataFrame objects
- @register_dataframe_system decorator for auto-registration
- Caching of instantiated systems
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type

from .base import DataFrameSystem
from .constants import CONST_DATAFRAME_BACKEND

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Registry for backend systems
_dataframe_systems_registry: Dict[CONST_DATAFRAME_BACKEND, Type[DataFrameSystem]] = {}

# Cache for instantiated systems (singleton per backend)
_dataframe_systems_cache: Dict[CONST_DATAFRAME_BACKEND, DataFrameSystem] = {}


def register_dataframe_system(
    backend: CONST_DATAFRAME_BACKEND,
) -> Callable[[Type[DataFrameSystem]], Type[DataFrameSystem]]:
    """
    Decorator for registering DataFrameSystem implementations.

    Usage:
        @register_dataframe_system(CONST_DATAFRAME_BACKEND.POLARS)
        class PolarsDataFrameSystem(DataFrameSystem):
            ...

    Args:
        backend: The backend type this system handles

    Returns:
        Decorator function that registers the class
    """

    def decorator(cls: Type[DataFrameSystem]) -> Type[DataFrameSystem]:
        _dataframe_systems_registry[backend] = cls
        logger.debug(f"Registered DataFrameSystem: {backend.name} -> {cls.__name__}")
        return cls

    return decorator


class DataFrameSystemFactory:
    """
    Factory for creating and caching DataFrameSystem instances.

    Features:
    - Automatic backend detection from DataFrame objects
    - Three-tier detection: exact match → pattern match → fallback
    - Singleton caching of system instances
    - Auto-registration via @register_dataframe_system decorator
    """

    # =========================================================================
    # Type Detection Maps
    # =========================================================================

    # Exact match map: (module, classname) → backend
    TYPE_MAP: Dict[tuple[str, str], CONST_DATAFRAME_BACKEND] = {
        # Polars
        ("polars.dataframe.frame", "DataFrame"): CONST_DATAFRAME_BACKEND.POLARS,
        ("polars.lazyframe.frame", "LazyFrame"): CONST_DATAFRAME_BACKEND.POLARS,
        ("polars", "DataFrame"): CONST_DATAFRAME_BACKEND.POLARS,
        ("polars", "LazyFrame"): CONST_DATAFRAME_BACKEND.POLARS,
        # Narwhals
        ("narwhals._pandas_like.dataframe", "DataFrame"): CONST_DATAFRAME_BACKEND.NARWHALS,
        ("narwhals.dataframe", "DataFrame"): CONST_DATAFRAME_BACKEND.NARWHALS,
        ("narwhals", "DataFrame"): CONST_DATAFRAME_BACKEND.NARWHALS,
        ("narwhals._pandas_like.dataframe", "LazyFrame"): CONST_DATAFRAME_BACKEND.NARWHALS,
        ("narwhals.dataframe", "LazyFrame"): CONST_DATAFRAME_BACKEND.NARWHALS,
        ("narwhals", "LazyFrame"): CONST_DATAFRAME_BACKEND.NARWHALS,
        # Ibis
        ("ibis.expr.types.relations", "Table"): CONST_DATAFRAME_BACKEND.IBIS,
        ("ibis.expr.types.joins", "Join"): CONST_DATAFRAME_BACKEND.IBIS,
    }

    # Pattern match map: regex → [(classname, backend), ...]
    PATTERN_MAP: Dict[str, list[tuple[str, CONST_DATAFRAME_BACKEND]]] = {
        # Polars patterns
        r"^polars\..*": [
            ("DataFrame", CONST_DATAFRAME_BACKEND.POLARS),
            ("LazyFrame", CONST_DATAFRAME_BACKEND.POLARS),
        ],
        # Narwhals patterns (handles internal reorganizations)
        r"^narwhals\..*": [
            ("DataFrame", CONST_DATAFRAME_BACKEND.NARWHALS),
            ("LazyFrame", CONST_DATAFRAME_BACKEND.NARWHALS),
        ],
        # Ibis patterns
        r"^ibis\.backends\..*": [
            ("Backend", CONST_DATAFRAME_BACKEND.IBIS),
        ],
        r"^ibis\.expr\..*": [
            ("Table", CONST_DATAFRAME_BACKEND.IBIS),
            ("Join", CONST_DATAFRAME_BACKEND.IBIS),
        ],
    }

    # Narwhals-wrapped types: route pandas/pyarrow through Narwhals
    NARWHALS_WRAPPED_PATTERNS: list[str] = [
        r"^pandas\..*",
        r"^pyarrow\..*",
        r"^cudf\..*",
    ]

    # Runtime type registration (for pattern-matched types)
    _runtime_type_map: Dict[tuple[str, str], CONST_DATAFRAME_BACKEND] = {}

    # =========================================================================
    # Public API
    # =========================================================================

    @classmethod
    def get_system(cls, df: Any) -> DataFrameSystem:
        """
        Get the appropriate DataFrameSystem for a DataFrame.

        Args:
            df: Any supported DataFrame type

        Returns:
            DataFrameSystem instance for the detected backend

        Raises:
            ValueError: If no system found for the DataFrame type
        """
        backend = cls._detect_backend(df)
        return cls._get_or_create_system(backend)

    @classmethod
    def get_system_for_backend(cls, backend: CONST_DATAFRAME_BACKEND) -> DataFrameSystem:
        """
        Get DataFrameSystem for a specific backend.

        Args:
            backend: The backend to get system for

        Returns:
            DataFrameSystem instance for the backend
        """
        return cls._get_or_create_system(backend)

    @classmethod
    def detect_backend(cls, df: Any) -> CONST_DATAFRAME_BACKEND:
        """
        Detect the backend type for a DataFrame (public method).

        Args:
            df: Any supported DataFrame type

        Returns:
            CONST_DATAFRAME_BACKEND enum value
        """
        return cls._detect_backend(df)

    # =========================================================================
    # Backend Detection (Three-Tier)
    # =========================================================================

    @classmethod
    def _detect_backend(cls, df: Any) -> CONST_DATAFRAME_BACKEND:
        """
        Detect backend using three-tier approach:
        1. Exact match in TYPE_MAP (fastest)
        2. Pattern matching (handles library refactors)
        3. Narwhals fallback for pandas/pyarrow

        Args:
            df: DataFrame to detect backend for

        Returns:
            CONST_DATAFRAME_BACKEND enum value

        Raises:
            ValueError: If no backend detected
        """
        obj_type = type(df)
        module = obj_type.__module__
        name = obj_type.__name__
        type_key = (module, name)

        # Tier 1: Exact match (fast path)
        all_types = {**cls.TYPE_MAP, **cls._runtime_type_map}
        if type_key in all_types:
            backend = all_types[type_key]
            logger.debug(f"Exact match: {type_key} -> {backend.name}")
            return backend

        # Tier 2: Check for Narwhals-wrapped types (pandas, pyarrow, cudf)
        for pattern in cls.NARWHALS_WRAPPED_PATTERNS:
            if re.match(pattern, module):
                backend = CONST_DATAFRAME_BACKEND.NARWHALS
                logger.info(f"Narwhals-wrapped type: {type_key} -> {backend.name}")
                cls._runtime_type_map[type_key] = backend
                return backend

        # Tier 3: Pattern matching
        backend = cls._match_by_pattern(module, name)
        if backend is not None:
            logger.info(f"Pattern match: {type_key} -> {backend.name}")
            cls._runtime_type_map[type_key] = backend
            return backend

        # Failed - log for monitoring
        logger.warning(
            f"Unmapped DataFrame type: {module}.{name}\n"
            f"  MRO: {[c.__module__ + '.' + c.__name__ for c in obj_type.__mro__[:5]]}"
        )
        raise ValueError(f"No DataFrameSystem found for type: {module}.{name}")

    @classmethod
    def _match_by_pattern(
        cls, module: str, name: str
    ) -> Optional[CONST_DATAFRAME_BACKEND]:
        """Match module and classname against pattern map."""
        for pattern, mappings in cls.PATTERN_MAP.items():
            if re.match(pattern, module):
                for class_name, backend in mappings:
                    if name == class_name:
                        return backend
        return None

    # =========================================================================
    # System Instantiation and Caching
    # =========================================================================

    @classmethod
    def _get_or_create_system(cls, backend: CONST_DATAFRAME_BACKEND) -> DataFrameSystem:
        """
        Get cached system or create new one.

        Args:
            backend: Backend to get system for

        Returns:
            DataFrameSystem instance (cached singleton)
        """
        if backend in _dataframe_systems_cache:
            return _dataframe_systems_cache[backend]

        # Ensure backend is registered
        cls._ensure_backend_registered(backend)

        if backend not in _dataframe_systems_registry:
            raise ValueError(
                f"No DataFrameSystem registered for backend: {backend.name}. "
                f"Available: {[b.name for b in _dataframe_systems_registry.keys()]}"
            )

        # Create and cache
        system_class = _dataframe_systems_registry[backend]
        system = system_class()
        _dataframe_systems_cache[backend] = system
        logger.debug(f"Created DataFrameSystem: {backend.name} -> {system_class.__name__}")
        return system

    @classmethod
    def _ensure_backend_registered(cls, backend: CONST_DATAFRAME_BACKEND) -> None:
        """
        Ensure backend system is imported and registered.

        Auto-imports backend modules to trigger @register_dataframe_system decorators.
        """
        if backend in _dataframe_systems_registry:
            return

        # Import backend module to trigger registration
        try:
            if backend == CONST_DATAFRAME_BACKEND.POLARS:
                from ...backends.polars import dataframe_system  # noqa: F401
            elif backend == CONST_DATAFRAME_BACKEND.NARWHALS:
                from ...backends.narwhals import dataframe_system  # noqa: F401
            elif backend == CONST_DATAFRAME_BACKEND.IBIS:
                from ...backends.ibis import dataframe_system  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import backend {backend.name}: {e}")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    @classmethod
    def get_registered_backends(cls) -> list[CONST_DATAFRAME_BACKEND]:
        """Get list of registered backends."""
        return list(_dataframe_systems_registry.keys())

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the system cache (for testing)."""
        _dataframe_systems_cache.clear()
        cls._runtime_type_map.clear()
        logger.debug("DataFrameSystem cache cleared")

    @classmethod
    def register_type(
        cls,
        module: str,
        class_name: str,
        backend: CONST_DATAFRAME_BACKEND,
    ) -> None:
        """
        Runtime registration of new types.

        Args:
            module: Module path
            class_name: Class name
            backend: Backend to route to
        """
        type_key = (module, class_name)
        cls._runtime_type_map[type_key] = backend
        logger.info(f"Registered type: {module}.{class_name} -> {backend.name}")
