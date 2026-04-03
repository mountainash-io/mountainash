from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Sequence, Type
import logging
from collections import namedtuple
import datetime

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_narwhals, import_polars

from .base_egress_strategy import BaseEgressDataFrame

if TYPE_CHECKING:
    from mountainash.core.types import (
        PandasFrame, PyArrowTable, PolarsFrameTypes, PolarsFrame, PolarsLazyFrame,
        NarwhalsFrame,
        PandasSeries, PolarsSeries,
    )

logger = logging.getLogger(__name__)



class EgressFromPolars(BaseEgressDataFrame):
    """
    Strategy for handling Polars DataFrame operations.

    This class contains the actual implementations for Python collection conversions.
    Other backends inherit CastToPythonDataMixin which delegates to these methods.
    """

    @classmethod
    def _type_map_dates_as_strings(cls):

        pl = import_polars()
        TYPE_MAP: Dict[Any, Any] = {
            pl.Int8: int,
            pl.Int16: int,
            pl.Int32: int,
            pl.Int64: int,
            pl.UInt8: int,
            pl.UInt16: int,
            pl.UInt32: int,
            pl.UInt64: int,
            pl.Float32: float,
            pl.Float64: float,
            pl.Boolean: bool,
            pl.Utf8: str,
            pl.String: str,
            pl.Date: str,  # or datetime.date if you want to convert
            pl.Datetime: str,  # or datetime.datetime
            pl.Time: str,  # or datetime.time
        }
        return TYPE_MAP

    @classmethod
    def _type_map_dates_preserved(cls):

        pl = import_polars()
        TYPE_MAP: Dict[Any, Any] = {
            pl.Int8: int,
            pl.Int16: int,
            pl.Int32: int,
            pl.Int64: int,
            pl.UInt8: int,
            pl.UInt16: int,
            pl.UInt32: int,
            pl.UInt64: int,
            pl.Float32: float,
            pl.Float64: float,
            pl.Boolean: bool,
            pl.Utf8: str,
            pl.String: str,
            pl.Date: datetime.date,  # or datetime.date if you want to convert
            pl.Datetime: datetime.datetime,  # or datetime.datetime
            pl.Time: datetime.time,  # or datetime.time
        }
        return TYPE_MAP

    @classmethod
    def convert_exception(cls, data: Any, e: Exception) -> Any:
        raise ValueError(f"Could not convert {data} with type {type(data)} using Polars DataFrame strategy. Error: {e}") from e

    # ======================
    # Dataframe to Dataframe

    @classmethod
    def _to_narwhals(cls, df: PolarsFrame, /, as_lazy: Optional[bool] = None) -> NarwhalsFrame:
        nw = import_narwhals()

        if as_lazy is None:
            # Default: preserve input type (polars eager → narwhals eager)
            return nw.from_native(df)
        elif as_lazy:
            # Force lazy
            return nw.from_native(df.lazy())
        else:
            # Force eager (already eager)
            return nw.from_native(df)

    @classmethod
    def _to_pandas(cls, df: PolarsFrame, /) -> PandasFrame:
        nw = import_narwhals()
        return nw.from_native(df).to_pandas()

    @classmethod
    def _to_polars(cls, df: PolarsFrame, /, as_lazy: Optional[bool] = None) -> PolarsFrameTypes:
        if as_lazy is None:
            # Default: preserve input type (already eager)
            return df
        elif as_lazy:
            # Force lazy
            return df.lazy()
        else:
            # Force eager (already eager)
            return df


    @classmethod
    def _to_polars_lazy(cls, df: PolarsFrame, /) -> PolarsLazyFrame:
        return df.lazy()


    @classmethod
    def _to_polars_eager(cls, df: PolarsFrame, /) -> PolarsFrame:
        return df




    @classmethod
    def _to_pyarrow(cls, df: PolarsFrame, /) -> PyArrowTable:
        """Convert Polars DataFrame to PyArrow Table."""
        nw = import_narwhals()
        return nw.from_native(df).to_arrow()

    # def _to_pyarrow_recordbatch(cls, df: PolarsFrame, batchsize: int = 1):
    #     """Convert Polars DataFrame to PyArrow RecordBatch."""
    #     temp = cls._to_pyarrow_table(df)
    #     return temp.to_batches(max_chunksize=batchsize)

    @classmethod
    def _to_dictionary_of_lists(cls, df: PolarsFrame, /) -> Dict[Any,List[Any]]:
        return df.to_dict(as_series=False)

    @classmethod
    def _to_dictionary_of_series_pandas(cls, df: PolarsFrame, /) -> Dict[str, PandasSeries]:
        nw = import_narwhals()
        return nw.from_native(df).to_pandas().to_dict(orient='series')


    @classmethod
    def _to_dictionary_of_series_polars(cls, df: PolarsFrame, /) -> Dict[str,PolarsSeries]:
        return df.to_dict(as_series=True)

    @classmethod
    def _to_list_of_dictionaries(cls, df: PolarsFrame, /) -> List[Dict[Any,Any]]:
        return df.rows(named=True)

    @classmethod
    def _to_list_of_tuples(cls, df: PolarsFrame, /) -> List[Tuple]:
        return df.rows()

    # @classmethod
    # def _to_list_of_ndarray(cls, df: PolarsFrame, /) -> List[np.ndarray]:
    #     return df.to

    @classmethod
    def _to_list_of_named_tuples(cls, df: PolarsFrame, /) -> Sequence[Tuple]:
        RecordClass = namedtuple('Row', df.columns)
        return [RecordClass(*row) for row in df.rows()]

    @classmethod
    def _to_list_of_typed_named_tuples(cls,
                                        df: PolarsFrame, /,
                                        preserve_dates: Optional[bool] = False) -> Sequence[Tuple]:

        if bool(preserve_dates):
            type_map = cls._type_map_dates_preserved()
        else:
            type_map = cls._type_map_dates_as_strings()

        # Create with type annotations
        field_types = [(col, type_map.get(dtype, Any))
                        for col, dtype in df.schema.items()]

        RecordClass = namedtuple('Row', [name for name, _ in field_types])
        RecordClass.__annotations__ = {name: type_ for name, type_ in field_types}

        return [RecordClass(*row) for row in df.rows()]


    @classmethod
    def _to_index_of_dictionaries(cls,
                                    df: PolarsFrame, /,
                                    index_fields: str|List[str]) -> Dict[str, List]:

        if index_fields is None:
            index_fields = df.columns[0]

        return df.rows_by_key(key=index_fields, named=True, include_key=True)

    @classmethod
    def _to_index_of_tuples(cls,
                                    df: PolarsFrame, /,
                                    index_fields: str|List[str]) -> Dict[str, List]:
        if index_fields is None:
            index_fields = df.columns[0]
        return df.rows_by_key(key=index_fields, include_key=True)

    @classmethod
    def _to_index_of_named_tuples(cls,
                                    df: PolarsFrame, /,
                                    index_fields: str|List[str]) -> Dict[str, List]:

        if index_fields is None:
            index_fields = df.columns[0]

        RecordClass = namedtuple('Row', df.columns)

        def row_generator(df):
            for key, rows in df.rows_by_key(key=index_fields, include_key=True).items():
                yield key, [RecordClass(*row) for row in rows]

        return {key: rows for key, rows in row_generator(df)}

    @classmethod
    def _to_index_of_typed_named_tuples(cls,
                                        df: PolarsFrame, /,
                                        index_fields: str|List[str],
                                        preserve_dates: Optional[bool] = False) -> Dict[str, List]:

        if index_fields is None:
            index_fields = df.columns[0]

        if bool(preserve_dates):
            type_map = cls._type_map_dates_preserved()
        else:
            type_map = cls._type_map_dates_as_strings()

        # Create with type annotations
        field_types = [(col, type_map.get(dtype, Any))
                        for col, dtype in df.schema.items()]

        RecordClass = namedtuple('Row', [name for name, _ in field_types])
        RecordClass.__annotations__ = {name: type_ for name, type_ in field_types}

        def row_generator(df):
            for key, rows in df.rows_by_key(key=index_fields, include_key=True).items():
                yield key, [RecordClass(*row) for row in rows]

        return {key: rows for key, rows in row_generator(df)}

    # ======================
    # Schema-aware conversions - direct implementation
    # ======================

    @classmethod
    def _to_list_of_dataclasses(
        cls,
        df: PolarsFrame,
        /,
        dataclass_type: Type,
        spec: Optional[Any] = None,
        auto_derive_schema: bool = True,
        apply_defaults: bool = False
    ) -> List[Any]:
        """
        Convert DataFrame to list of dataclass instances with schema-aware transformations.

        Args:
            df: Input Polars DataFrame
            dataclass_type: The dataclass type to instantiate
            spec: Optional TypeSpec for transformations
            auto_derive_schema: Auto-derive TypeSpec if not provided (default: True)
            apply_defaults: Whether to apply dataclass field defaults

        Returns:
            List of dataclass instances
        """
        # Import dependencies at runtime
        from mountainash.pydata.mappers.dataclass_mapping import map_list_of_namedtuples_to_dataclasses

        from mountainash.typespec.extraction import extract_schema_from_dataclass
        from .egress_helpers import (
            apply_native_conversions_for_egress,
            apply_custom_converters_to_python_data
        )

        # Auto-derive schema if needed
        if spec is None and auto_derive_schema:
            spec = extract_schema_from_dataclass(dataclass_type, use_cache=True)

        # Apply schema transformations using HYBRID STRATEGY
        if spec is not None:
            # HYBRID STRATEGY FOR EGRESS:
            # TIER 1: Apply NATIVE conversions in DataFrame (vectorized, FAST!)
            # TIER 2: Extract to named tuples
            # TIER 3: Apply CUSTOM converters after extraction (Python layer)

            # Apply only native conversions in DataFrame
            df, python_only_custom = apply_native_conversions_for_egress(df, spec)

            # Extract to named tuples
            named_tuples = cls._to_list_of_named_tuples(df)

            # Apply custom converters to named tuples (if any)
            named_tuples = apply_custom_converters_to_python_data(
                named_tuples,
                python_only_custom,
                data_format="namedtuple"
            )
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
        df: PolarsFrame,
        /,
        model_class: Type,
        spec: Optional[Any] = None,
        auto_derive_schema: bool = True,
    ) -> List[Any]:
        """
        Convert DataFrame to list of Pydantic model instances with schema-aware transformations.

        Args:
            df: Input Polars DataFrame
            model_class: The Pydantic model class to instantiate
            spec: Optional TypeSpec for transformations
            auto_derive_schema: Auto-derive TypeSpec if not provided (default: True)

        Returns:
            List of Pydantic model instances
        """
        # Import dependencies at runtime
        from mountainash.pydata.mappers.pydantic_mapping import map_list_of_namedtuples_to_pydantic

        from mountainash.typespec.extraction import extract_schema_from_pydantic
        from .egress_helpers import (
            apply_native_conversions_for_egress,
            apply_custom_converters_to_python_data
        )

        # Auto-derive schema if needed
        if spec is None and auto_derive_schema:
            spec = extract_schema_from_pydantic(model_class, use_cache=True)

        # Apply schema transformations using HYBRID STRATEGY
        if spec is not None:
            # HYBRID STRATEGY FOR EGRESS:
            # TIER 1: Apply NATIVE conversions in DataFrame (vectorized, FAST!)
            # TIER 2: Extract to named tuples
            # TIER 3: Apply CUSTOM converters after extraction (Python layer)

            # Apply only native conversions in DataFrame
            df, python_only_custom = apply_native_conversions_for_egress(df, spec)

            # Extract to named tuples
            named_tuples = cls._to_list_of_named_tuples(df)

            # Apply custom converters to named tuples (if any)
            named_tuples = apply_custom_converters_to_python_data(
                named_tuples,
                python_only_custom,
                data_format="namedtuple"
            )
        else:
            # No schema config - just extract
            named_tuples = cls._to_list_of_named_tuples(df)

        # Convert to Pydantic instances (no mapping needed - schema already applied)
        return map_list_of_namedtuples_to_pydantic(
            named_tuples,
            model_class,
            mapping=None  # Schema transformations already applied
        )

    @classmethod
    def _to_ibis(cls, df: PolarsFrame, /, **kwargs):
        """Convert to Ibis table via PyArrow."""
        try:
            import ibis
        except ImportError as e:
            raise ImportError("ibis-framework is required for Ibis conversion.") from e
        arrow_table = cls._to_pyarrow(df)
        return ibis.memtable(arrow_table)


# Alias used by DataFrameEgressFactory and __init__.py exports
EgressPydataFromPolars = EgressFromPolars
