
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple, Type

from mountainash.pydata.mappers.dataclass_mapping import map_list_of_namedtuples_to_dataclasses
from mountainash.pydata.mappers.pydantic_mapping import map_list_of_namedtuples_to_pydantic

if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames, PandasSeries, PolarsSeries
    from mountainash.typespec.spec import TypeSpec


from mountainash.typespec.extraction import (
    extract_schema_from_dataclass,
    extract_schema_from_pydantic,
)

from .egress_helpers import (
    apply_native_conversions_for_egress,
    apply_custom_converters_to_python_data
)

from .egress_pydata_from_polars import EgressPydataFromPolars
import mountainash as ma

import logging
logger = logging.getLogger(__name__)


"""
Mixin for casting DataFrames to Python data structures.

Provides backend-agnostic implementation for converting DataFrames to:
- Python collections (tuples, dicts, named tuples) - delegates to EgressPydataFromPolars
- Dataclass/Pydantic instances with schema-aware transformations - full implementation

All collection methods delegate through Polars eager for consistency and efficiency.
Schema-aware conversions (dataclass/Pydantic) contain full implementation.
"""

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

    Note: EgressPydataFromPolars does NOT inherit this mixin - it contains the actual
    implementations that the mixin delegates to.
    """

    # ======================
    # Collection conversions - delegate to EgressPydataFromPolars via relation API
    # ======================

    @classmethod
    def _to_list_of_tuples(cls, df: 'SupportedDataFrames', /) -> List[Tuple]:
        """Convert DataFrame to list of tuples via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_list_of_tuples(pl_df)

    @classmethod
    def _to_list_of_dictionaries(cls, df: 'SupportedDataFrames', /) -> List[Dict[Any, Any]]:
        """Convert DataFrame to list of dictionaries via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_list_of_dictionaries(pl_df)

    @classmethod
    def _to_dictionary_of_lists(cls, df: 'SupportedDataFrames', /) -> Dict[Any, List[Any]]:
        """Convert DataFrame to dictionary of lists via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_dictionary_of_lists(pl_df)

    @classmethod
    def _to_dictionary_of_series_pandas(cls, df: 'SupportedDataFrames', /) -> Dict[str, 'PandasSeries']:
        """Convert DataFrame to dict of pandas Series via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_dictionary_of_series_pandas(pl_df)

    @classmethod
    def _to_dictionary_of_series_polars(cls, df: 'SupportedDataFrames', /) -> Dict[str, 'PolarsSeries']:
        """Convert DataFrame to dict of Polars Series via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_dictionary_of_series_polars(pl_df)

    @classmethod
    def _to_list_of_named_tuples(cls, df: 'SupportedDataFrames', /) -> Sequence[Tuple]:
        """Convert DataFrame to list of named tuples via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_list_of_named_tuples(pl_df)

    @classmethod
    def _to_list_of_typed_named_tuples(cls, df: 'SupportedDataFrames', /, preserve_dates: Optional[bool] = False) -> Sequence[Tuple]:
        """Convert DataFrame to list of typed named tuples via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_list_of_typed_named_tuples(pl_df, preserve_dates=preserve_dates)

    @classmethod
    def _to_index_of_dictionaries(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str]) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of dicts via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_index_of_dictionaries(pl_df, index_fields=index_fields)

    @classmethod
    def _to_index_of_tuples(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str]) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of tuples via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_index_of_tuples(pl_df, index_fields=index_fields)

    @classmethod
    def _to_index_of_named_tuples(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str]) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of named tuples via Polars."""
        pl_df = ma.relation(df).to_polars()
        return EgressPydataFromPolars._to_index_of_named_tuples(pl_df, index_fields=index_fields)

    @classmethod
    def _to_index_of_typed_named_tuples(cls, df: 'SupportedDataFrames', /, index_fields: str|List[str], preserve_dates: Optional[bool] = False) -> Dict[str, List]:
        """Convert DataFrame to indexed dict of typed named tuples via Polars."""
        pl_df = ma.relation(df).to_polars()
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
        spec: Optional['TypeSpec'] = None,
        auto_derive_schema: bool = True,
        apply_defaults: bool = False
    ) -> List[Any]:
        """
        Convert DataFrame to list of dataclass instances with schema-aware transformations.

        Applies schema transformations to source DataFrame before conversion.
        Auto-derives schemas from DataFrame and dataclass if not provided.

        Args:
            df: Input DataFrame (any backend - pandas, Polars, Ibis, PyArrow, Narwhals)
            dataclass_type: The dataclass type to instantiate
            spec: Optional TypeSpec for transformations
            auto_derive_schema: Auto-derive TypeSpec if not provided (default: True)
            apply_defaults: Whether to apply dataclass field defaults

        Returns:
            List of dataclass instances

        Example:
            from dataclasses import dataclass

            @dataclass
            class User:
                id: int
                name: str

            # Auto-derivation
            users = strategy._to_list_of_dataclasses(df, User)
        """

        # Auto-derive schema if needed
        if spec is None and auto_derive_schema:
            # Extract TypeSpec from the dataclass (field names + types)
            spec = extract_schema_from_dataclass(dataclass_type, use_cache=True)

        # Apply schema transformations using HYBRID STRATEGY
        if spec is not None:
            logger.debug("EGRESS TRACE: Starting hybrid egress for dataclass")

            # Apply only native conversions in DataFrame (TIER 1)
            logger.debug("  Step 1: Applying native conversions")
            df, python_only_custom = apply_native_conversions_for_egress(df, spec)
            logger.debug(f"  After native: type(df)={type(df).__name__}")

            # Extract to named tuples (TIER 2)
            logger.debug("  Step 2: Extracting to named tuples")
            named_tuples = cls._to_list_of_named_tuples(df)
            logger.debug(f"  Extracted {len(named_tuples)} named tuples")
            if named_tuples:
                logger.debug(f"  First tuple fields: {named_tuples[0]._fields if hasattr(named_tuples[0], '_fields') else 'N/A'}")

            # Apply custom converters to named tuples (TIER 3)
            logger.debug("  Step 3: Applying custom converters")
            named_tuples = apply_custom_converters_to_python_data(
                named_tuples,
                python_only_custom,
                data_format="namedtuple"
            )
            logger.debug(f"  After custom converters: {len(named_tuples)} tuples")
        else:
            # No schema config - just extract
            named_tuples = cls._to_list_of_named_tuples(df)

        # Convert to dataclass instances (no mapping needed - schema already applied)
        return map_list_of_namedtuples_to_dataclasses(
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
        spec: Optional['TypeSpec'] = None,
        auto_derive_schema: bool = True,
    ) -> List[Any]:
        """
        Convert DataFrame to list of Pydantic model instances with schema-aware transformations.

        Applies schema transformations to source DataFrame before conversion.
        Auto-derives schemas from DataFrame and Pydantic model if not provided.
        Pydantic handles validation and type coercion automatically.

        Args:
            df: Input DataFrame (any backend - pandas, Polars, Ibis, PyArrow, Narwhals)
            model_class: The Pydantic model class to instantiate
            spec: Optional TypeSpec for transformations
            auto_derive_schema: Auto-derive TypeSpec if not provided (default: True)

        Returns:
            List of Pydantic model instances

        Raises:
            ImportError: If pydantic or mountainash-utils-dataclasses not installed

        Example:
            from pydantic import BaseModel

            class User(BaseModel):
                id: int
                name: str

            # Auto-derivation
            users = strategy._to_list_of_pydantic(df, User)
        """
        # Auto-derive schema if needed
        if spec is None and auto_derive_schema:
            # Extract TypeSpec from the Pydantic model
            spec = extract_schema_from_pydantic(model_class, use_cache=True)

        # Apply schema transformations using HYBRID STRATEGY
        if spec is not None:
            logger.debug("EGRESS TRACE: Starting hybrid egress for pydantic")

            # Apply only native conversions in DataFrame (TIER 1)
            logger.debug("  Step 1: Applying native conversions")
            df, python_only_custom = apply_native_conversions_for_egress(df, spec)
            logger.debug(f"  After native: type(df)={type(df).__name__}")

            # Extract to named tuples (TIER 2)
            logger.debug("  Step 2: Extracting to named tuples")
            named_tuples = cls._to_list_of_named_tuples(df)
            logger.debug(f"  Extracted {len(named_tuples)} named tuples")
            if named_tuples:
                logger.debug(f"  First tuple fields: {named_tuples[0]._fields if hasattr(named_tuples[0], '_fields') else 'N/A'}")

            # Apply custom converters to named tuples (TIER 3)
            logger.debug("  Step 3: Applying custom converters")
            named_tuples = apply_custom_converters_to_python_data(
                named_tuples,
                python_only_custom,
                data_format="namedtuple"
            )
            logger.debug(f"  After custom converters: {len(named_tuples)} tuples")
        else:
            # No schema config - just extract
            named_tuples = cls._to_list_of_named_tuples(df)

        # Convert to Pydantic instances (no mapping needed - schema already applied)
        return map_list_of_namedtuples_to_pydantic(
            named_tuples,
            model_class,
            mapping=None  # Schema transformations already applied
        )


__all__ = ['EgressToPythonData']
