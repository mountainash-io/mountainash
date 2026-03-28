"""
Mixin for casting DataFrames to Python data structures.

Provides backend-agnostic implementation for converting DataFrames to:
- Python collections (tuples, dicts, named tuples) - delegates to CastFromPolars
- Dataclass/Pydantic instances with schema-aware transformations - full implementation

All collection methods delegate through Polars eager for consistency and efficiency.
Schema-aware conversions (dataclass/Pydantic) contain full implementation.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple, Type

from mountainash_utils_dataclasses import DataclassUtils, PydanticUtils

if TYPE_CHECKING:
    from mountainash.dataframes.core.typing import SupportedDataFrames, PandasSeries, PolarsSeries
    from mountainash.schema.config import SchemaConfig


from mountainash.schema.config import (
    SchemaConfig,
    extract_schema_from_dataframe,
    extract_schema_from_dataclass,
    build_schema_config_with_fuzzy_matching,
    extract_schema_from_pydantic
)

from .egress_helpers import (
    apply_native_conversions_for_egress,
    apply_custom_converters_to_python_data
)
import logging
logger = logging.getLogger(__name__)

from .egress_pydata_from_polars import EgressPydataFromPolars
from mountainash.schema.transform import CastDataFrame

class EgressToPythonData:
    """
    Mixin for ALL Python data structure conversions.

    Provides backend-agnostic implementations for converting DataFrames to:
    - Tuples (plain, named, typed named)
    - Dictionaries (of lists, of series, indexed)
    - Dataclasses (with schema transformations)
    - Pydantic models (with schema transformations)

    Collection methods (tuples/dicts) delegate through Polars eager for efficiency.
    Schema-aware conversions (dataclass/Pydantic) contain full implementation.

    Classes using this mixin must implement:
    - _to_polars(df, as_lazy=False) method to convert to Polars DataFrame

    Example:
        class CastFromPandas(CastToPythonDataMixin, BaseCastDataFrame):
            # Inherits ALL Python data conversions from mixin
            pass

    Note: CastFromPolars does NOT inherit this mixin - it contains the actual
    implementations that the mixin delegates to.
    """

    # ======================
    # Collection conversions - delegate to CastFromPolars
    # ======================

    @classmethod
    def _to_list_of_tuples(cls, df: 'SupportedDataFrames', /) -> List[Tuple]:
        """Convert DataFrame to list of tuples via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_list_of_tuples(pl_df)

    @classmethod
    def _to_list_of_dictionaries(cls, df: 'SupportedDataFrames', /) -> List[Dict[Any, Any]]:
        """Convert DataFrame to list of dictionaries via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_list_of_dictionaries(pl_df)

    @classmethod
    def _to_dictionary_of_lists(cls, df: 'SupportedDataFrames', /) -> Dict[Any, List[Any]]:
        """Convert DataFrame to dictionary of lists via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_dictionary_of_lists(pl_df)

    @classmethod
    def _to_dictionary_of_series_pandas(cls, df: 'SupportedDataFrames', /) -> Dict[str, 'PandasSeries']:
        """Convert DataFrame to dict of pandas Series via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_dictionary_of_series_pandas(pl_df)

    @classmethod
    def _to_dictionary_of_series_polars(cls, df: 'SupportedDataFrames', /) -> Dict[str, 'PolarsSeries']:
        """Convert DataFrame to dict of Polars Series via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_dictionary_of_series_polars(pl_df)

    @classmethod
    def _to_list_of_named_tuples(cls, df: 'SupportedDataFrames', /) -> Sequence[Tuple]:
        """Convert DataFrame to list of named tuples via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_list_of_named_tuples(pl_df)

    @classmethod
    def _to_list_of_typed_named_tuples(cls, df: 'SupportedDataFrames', /, preserve_dates: Optional[bool] = False) -> Sequence[Tuple]:
        """Convert DataFrame to list of typed named tuples via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_list_of_typed_named_tuples(pl_df, preserve_dates=preserve_dates)

    @classmethod
    def _to_index_of_dictionaries(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str]) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of dicts via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_index_of_dictionaries(pl_df, index_fields=index_fields)

    @classmethod
    def _to_index_of_tuples(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str]) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of tuples via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_index_of_tuples(pl_df, index_fields=index_fields)

    @classmethod
    def _to_index_of_named_tuples(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str]) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of named tuples via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_index_of_named_tuples(pl_df, index_fields=index_fields)

    @classmethod
    def _to_index_of_typed_named_tuples(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str], preserve_dates: Optional[bool] = False) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of typed named tuples via Polars."""
        pl_df = CastDataFrame.to_polars_eager(df)
        return EgressPydataFromPolars._to_index_of_typed_named_tuples(pl_df, index_fields=index_fields, preserve_dates=preserve_dates)

    # ======================
    # Schema-aware conversions - full implementation
    # ======================

    @classmethod
    def _to_list_of_dataclasses(
        cls,
        df: 'SupportedDataFrames',
        /,
        dataclass_type: Type,
        schema_config: Optional['SchemaConfig'] = None,
        auto_derive_schema: bool = True,
        fuzzy_match_threshold: float = 0.6,
        apply_defaults: bool = False
    ) -> List[Any]:
        """
        Convert DataFrame to list of dataclass instances with schema-aware transformations.

        BREAKING CHANGE: 'mapping' parameter removed. Use 'schema_config' instead.

        Applies schema transformations to source DataFrame before conversion.
        Auto-derives schemas from DataFrame and dataclass if not provided.

        Args:
            df: Input DataFrame (any backend - pandas, Polars, Ibis, PyArrow, Narwhals)
            dataclass_type: The dataclass type to instantiate
            schema_config: Optional schema configuration for transformations
            auto_derive_schema: Auto-derive schemas if config not provided (default: True)
            fuzzy_match_threshold: Column name similarity threshold 0.0-1.0 (default: 0.6)
            apply_defaults: Whether to apply dataclass field defaults

        Returns:
            List of dataclass instances

        Example:
            from dataclasses import dataclass

            @dataclass
            class User:
                id: int
                name: str

            # Auto-derivation with fuzzy matching
            users = strategy._to_list_of_dataclasses(df, User)

            # Explicit schema
            config = SchemaConfig(columns={"user_id": {"rename": "id"}})
            users = strategy._to_list_of_dataclasses(df, User, schema_config=config)
        """


        # Auto-derive schema if needed
        if schema_config is None and auto_derive_schema:
            # Extract schemas from DataFrame and dataclass
            source_schema = extract_schema_from_dataframe(df, include_backend_types=False)
            target_schema = extract_schema_from_dataclass(dataclass_type, use_cache=True)

            # Build config with fuzzy matching
            schema_config = build_schema_config_with_fuzzy_matching(
                source_schema=source_schema,
                target_schema=target_schema,
                fuzzy_match_threshold=fuzzy_match_threshold,
                strict=False  # Default to lenient for auto-derived schemas
            )

        # Apply schema transformations using HYBRID STRATEGY
        if schema_config is not None:
            # Validate against source schema (if strict)
            if schema_config.strict and schema_config.source_schema:
                schema_config.validate_against_dataframe(df, mode='source')

            # HYBRID STRATEGY FOR EGRESS:
            # TIER 1: Apply NATIVE conversions in DataFrame (vectorized, FAST!)
            # TIER 2: Extract to named tuples
            # TIER 3: Apply CUSTOM converters after extraction (Python layer)


            logger.debug(f"EGRESS TRACE: Starting hybrid egress for dataclass")

            # Apply only native conversions in DataFrame
            logger.debug(f"  Step 1: Applying native conversions")
            df = apply_native_conversions_for_egress(df, schema_config)
            logger.debug(f"  After native: df.columns={df.columns}")

            # Extract to named tuples
            logger.debug(f"  Step 2: Extracting to named tuples")
            named_tuples = cls._to_list_of_named_tuples(df)
            logger.debug(f"  Extracted {len(named_tuples)} named tuples")
            if named_tuples:
                logger.debug(f"  First tuple fields: {named_tuples[0]._fields if hasattr(named_tuples[0], '_fields') else 'N/A'}")

            # Apply custom converters to named tuples (if any)
            logger.debug(f"  Step 3: Applying custom converters")
            named_tuples = apply_custom_converters_to_python_data(
                named_tuples,
                schema_config,
                data_format="namedtuple"
            )
            logger.debug(f"  After custom converters: {len(named_tuples)} tuples")
        else:
            # No schema config - just extract
            named_tuples = cls._to_list_of_named_tuples(df)

        # Convert to dataclass instances (no mapping needed - schema already applied)
        return DataclassUtils.map_list_of_namedtuples_to_dataclasses(
            named_tuples,
            dataclass_type,
            mapping=None,  # Schema transformations already applied
            apply_defaults=apply_defaults
        )

    @classmethod
    def _to_list_of_pydantic(
        cls,
        df: 'SupportedDataFrames',
        /,
        model_class: Type,
        schema_config: Optional['SchemaConfig'] = None,
        auto_derive_schema: bool = True,
        fuzzy_match_threshold: float = 0.6
    ) -> List[Any]:
        """
        Convert DataFrame to list of Pydantic model instances with schema-aware transformations.

        BREAKING CHANGE: 'mapping' parameter removed. Use 'schema_config' instead.

        Applies schema transformations to source DataFrame before conversion.
        Auto-derives schemas from DataFrame and Pydantic model if not provided.
        Pydantic handles validation and type coercion automatically.

        Args:
            df: Input DataFrame (any backend - pandas, Polars, Ibis, PyArrow, Narwhals)
            model_class: The Pydantic model class to instantiate
            schema_config: Optional schema configuration for transformations
            auto_derive_schema: Auto-derive schemas if config not provided (default: True)
            fuzzy_match_threshold: Column name similarity threshold 0.0-1.0 (default: 0.6)

        Returns:
            List of Pydantic model instances

        Raises:
            ImportError: If pydantic or mountainash-utils-dataclasses not installed

        Example:
            from pydantic import BaseModel

            class User(BaseModel):
                id: int
                name: str

            # Auto-derivation with fuzzy matching
            users = strategy._to_list_of_pydantic(df, User)

            # Explicit schema
            config = SchemaConfig(columns={"user_id": {"rename": "id"}})
            users = strategy._to_list_of_pydantic(df, User, schema_config=config)
        """
        # Auto-derive schema if needed
        if schema_config is None and auto_derive_schema:
            # Extract schemas from DataFrame and Pydantic model
            source_schema = extract_schema_from_dataframe(df, include_backend_types=False)
            target_schema = extract_schema_from_pydantic(model_class, use_cache=True)

            # Build config with fuzzy matching
            schema_config = build_schema_config_with_fuzzy_matching(
                source_schema=source_schema,
                target_schema=target_schema,
                fuzzy_match_threshold=fuzzy_match_threshold,
                strict=False  # Default to lenient for auto-derived schemas
            )

        # Apply schema transformations using HYBRID STRATEGY
        if schema_config is not None:
            # Validate against source schema (if strict)
            if schema_config.strict and schema_config.source_schema:
                schema_config.validate_against_dataframe(df, mode='source')

            # HYBRID STRATEGY FOR EGRESS:
            # TIER 1: Apply NATIVE conversions in DataFrame (vectorized, FAST!)
            # TIER 2: Extract to named tuples
            # TIER 3: Apply CUSTOM converters after extraction (Python layer)
            from .egress_helpers import (
                apply_native_conversions_for_egress,
                apply_custom_converters_to_python_data
            )
            import logging
            logger = logging.getLogger(__name__)

            logger.debug(f"EGRESS TRACE: Starting hybrid egress for dataclass")

            # Apply only native conversions in DataFrame
            logger.debug(f"  Step 1: Applying native conversions")
            df = apply_native_conversions_for_egress(df, schema_config)
            logger.debug(f"  After native: df.columns={df.columns}")

            # Extract to named tuples
            logger.debug(f"  Step 2: Extracting to named tuples")
            named_tuples = cls._to_list_of_named_tuples(df)
            logger.debug(f"  Extracted {len(named_tuples)} named tuples")
            if named_tuples:
                logger.debug(f"  First tuple fields: {named_tuples[0]._fields if hasattr(named_tuples[0], '_fields') else 'N/A'}")

            # Apply custom converters to named tuples (if any)
            logger.debug(f"  Step 3: Applying custom converters")
            named_tuples = apply_custom_converters_to_python_data(
                named_tuples,
                schema_config,
                data_format="namedtuple"
            )
            logger.debug(f"  After custom converters: {len(named_tuples)} tuples")
        else:
            # No schema config - just extract
            named_tuples = cls._to_list_of_named_tuples(df)

        # Convert to Pydantic instances (no mapping needed - schema already applied)
        return PydanticUtils.map_list_of_namedtuples_to_pydantic(
            named_tuples,
            model_class,
            mapping=None  # Schema transformations already applied
        )


__all__ = ['CastToPythonDataMixin']
