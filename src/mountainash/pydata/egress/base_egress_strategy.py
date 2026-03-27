# path: src/mountainash_data/dataframes/utils/base_dataframe_strategy.py

from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple

# Runtime imports - only import what's needed when actually used
# from ..typing_utils import SupportedDataFrames


if TYPE_CHECKING:
    import ibis as ibis
    # import ibis.expr.types as ir
    # import pandas as pd
    # import polars as pl
    # import pyarrow as pa
    # import narwhals as nw

    from mountainash.dataframes.typing import (
    SupportedDataFrames,
    PandasFrame, PyArrowTable, IbisTable,
    PolarsFrameTypes, NarwhalsFrameTypes, PolarsLazyFrame, PolarsFrame,
    PandasSeries,PolarsSeries,
    )


class BaseEgressDataFrame(ABC):

    # @classmethod
    # @abstractmethod
    # def can_handle(cls, data: Any) -> bool:
    #     """
    #     Check if this strategy can handle the input data.
    #     """
    #     pass


    @classmethod
    @abstractmethod
    def convert_exception(cls, data: Any, e: Exception) -> Any:
        """
        Handle casting exceptions
        """
        pass


    @classmethod
    @abstractmethod
    def _to_pandas(cls, df: Any, /) -> PandasFrame:
        pass

    @classmethod
    def to_pandas(cls, df: SupportedDataFrames, /) -> PandasFrame:
        try:
            return cls._to_pandas(df)
        except Exception as e:
            raise cls.convert_exception(df, e)


    @classmethod
    @abstractmethod
    def _to_polars(cls, df: Any, /, as_lazy: Optional[bool] = None) -> PolarsFrameTypes:
        """
        Convert to Polars DataFrame or LazyFrame.

        Args:
            df: Input DataFrame
            as_lazy: Output mode control
                - None (default): Preserve input laziness (lazy → lazy, eager → eager)
                - True: Force lazy output (converts eager to lazy if needed)
                - False: Force eager output (collects lazy frames)

        Returns:
            pl.DataFrame or pl.LazyFrame based on as_lazy parameter
        """
        pass

    @classmethod
    def to_polars(cls, df: SupportedDataFrames, /, as_lazy: Optional[bool] = None) -> PolarsFrameTypes:
        try:
            return cls._to_polars(df, as_lazy=as_lazy)
        except Exception as e:
            raise cls.convert_exception(df, e)


    @classmethod
    @abstractmethod
    def _to_polars_lazy(cls, df: Any, /) -> PolarsLazyFrame:
        pass

    @classmethod
    def to_polars_lazy(cls, df: SupportedDataFrames, /) -> PolarsLazyFrame:
        try:
            return cls._to_polars_lazy(df)
        except Exception as e:
            raise cls.convert_exception(df, e)


    @classmethod
    @abstractmethod
    def _to_polars_eager(cls, df: Any, /) -> PolarsFrame:
        pass

    @classmethod
    def to_polars_eager(cls, df: SupportedDataFrames, /) -> PolarsFrame:
        try:
            return cls._to_polars_eager(df)
        except Exception as e:
            raise cls.convert_exception(df, e)


    @classmethod
    @abstractmethod
    def _to_narwhals(cls, df: Any, /, as_lazy: Optional[bool] = None) -> NarwhalsFrameTypes:
        """
        Convert to Narwhals DataFrame or LazyFrame.

        Args:
            df: Input DataFrame
            as_lazy: Output mode control
                - None (default): Preserve input laziness (lazy → lazy, eager → eager)
                - True: Force lazy output (converts eager to lazy if needed)
                - False: Force eager output (collects lazy frames)

        Returns:
            nw.DataFrame or nw.LazyFrame based on as_lazy parameter
        """
        pass

    @classmethod
    def to_narwhals(cls, df: SupportedDataFrames, /, as_lazy: Optional[bool] = None) -> NarwhalsFrameTypes:
        try:
            return cls._to_narwhals(df, as_lazy=as_lazy)
        except Exception as e:
            raise cls.convert_exception(df, e)


    @classmethod
    @abstractmethod
    def _to_pyarrow(cls, df: Any, /) -> PyArrowTable:
        pass

    @classmethod
    def to_pyarrow(cls, df: SupportedDataFrames, /) -> PyArrowTable:

        try:
            return cls._to_pyarrow(df)
        except Exception as e:
            raise cls.convert_exception(df, e)


    @classmethod
    @abstractmethod
    def _to_ibis(cls,
                df: SupportedDataFrames,
                /,
                ibis_backend: Optional[ibis.BaseBackend] = None,
                tablename: Optional[str] = None,
                tablename_prefix: Optional[str] = None,
                temp: Optional[bool] = False,
                overwrite: Optional[bool] = False   ) -> IbisTable:
        pass

    @classmethod
    def to_ibis(cls,
                     df: SupportedDataFrames,
                     /,
                     ibis_backend: Optional[ibis.BaseBackend] = None,
                     tablename: Optional[str] = None,
                     tablename_prefix: Optional[str] = None,
                     temp: Optional[bool] = False,
                     overwrite: Optional[bool] = False  ) -> IbisTable:

        try:
            return cls._to_ibis(df,
                                ibis_backend=ibis_backend,
                                tablename=tablename,
                                tablename_prefix=tablename_prefix,
                                temp=temp,
                                overwrite=overwrite)
        except Exception as e:
            raise cls.convert_exception(df, e)



    @classmethod
    @abstractmethod
    def _to_dictionary_of_lists(cls, df: Any, /) -> Dict[Any,List[Any]]:
        pass

    @classmethod
    def to_dictionary_of_lists(cls, df: SupportedDataFrames, /) -> Dict[Any,List[Any]]:
        try:
            return cls._to_dictionary_of_lists(df)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    @abstractmethod
    def _to_dictionary_of_series_polars(cls, df: Any, /) -> Dict[str,PolarsSeries]:
        pass

    @classmethod
    def to_dictionary_of_series_polars(cls, df: SupportedDataFrames, /) -> Dict[str,PolarsSeries]:
        try:
            return cls._to_dictionary_of_series_polars(df)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    @abstractmethod
    def _to_dictionary_of_series_pandas(cls, df: Any, /) -> Dict[str,PandasSeries]:
        pass

    @classmethod
    def to_dictionary_of_series_pandas(cls, df: SupportedDataFrames, /) -> Dict[str,PandasSeries]:
        try:
            return cls._to_dictionary_of_series_pandas(df)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    @abstractmethod
    def _to_list_of_dictionaries(cls, df: Any, /) -> List[Dict[Any,Any]]:
        pass

    @classmethod
    def to_list_of_dictionaries(cls, df: SupportedDataFrames, /) -> List[Dict[Any,Any]]:
        try:
            return cls._to_list_of_dictionaries(df)
        except Exception as e:
            raise cls.convert_exception(df, e)






    @classmethod
    @abstractmethod
    def _to_list_of_named_tuples(cls, df: Any, /) -> Sequence[Tuple]:
        pass

    @classmethod
    @abstractmethod
    def _to_list_of_typed_named_tuples(cls, df: Any, /) -> Sequence[Tuple]:
        pass

    @classmethod
    @abstractmethod
    def _to_index_of_dictionaries(cls, df: Any, /, index_fields: str|List[str]) -> Dict[str, List]:
        pass

    @classmethod
    @abstractmethod
    def _to_index_of_tuples(cls, df: Any, /, index_fields: str|List[str]) -> Dict[str, List]:
        pass

    @classmethod
    @abstractmethod
    def _to_index_of_named_tuples(cls, df: Any, /, index_fields: str|List[str]) -> Dict[str, List]:
        pass

    @classmethod
    @abstractmethod
    def _to_index_of_typed_named_tuples(cls, df: Any, /, index_fields: str|List[str], preserve_dates: Optional[bool] = False) -> Dict[str, List]:
        pass


    @classmethod
    def to_list_of_named_tuples(cls, df: SupportedDataFrames, /) -> Sequence[Tuple]:
        try:
            return cls._to_list_of_named_tuples(df)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    def to_list_of_typed_named_tuples(cls, df: SupportedDataFrames, /) -> Sequence[Tuple]:
        try:
            return cls._to_list_of_typed_named_tuples(df)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    def to_index_of_dictionaries(cls, df: SupportedDataFrames, /, index_fields: str|List[str]) -> Dict[str, List]:
        try:
            return cls._to_index_of_dictionaries(df, index_fields=index_fields)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    def to_index_of_tuples(cls, df: SupportedDataFrames, /, index_fields: str|List[str]) -> Dict[str, List]:
        try:
            return cls._to_index_of_tuples(df, index_fields=index_fields)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    def to_index_of_named_tuples(cls, df: SupportedDataFrames, /, index_fields: str|List[str]) -> Dict[str, List]:
        try:
            return cls._to_index_of_named_tuples(df, index_fields=index_fields)
        except Exception as e:
            raise cls.convert_exception(df, e)

    @classmethod
    def to_index_of_typed_named_tuples(cls, df: SupportedDataFrames, /, index_fields: str|List[str], preserve_dates: Optional[bool] = False) -> Dict[str, List]:
        try:
            return cls._to_index_of_typed_named_tuples(df, index_fields=index_fields, preserve_dates=preserve_dates)
        except Exception as e:
            raise cls.convert_exception(df, e)



    # @abstractmethod
    # def _cast_to_pyarrow_recordbatch(cls, df: Any,  batchsize: int) -> List[pa.RecordBatch]:
    #     pass

    # def cast_to_pyarrow_recordbatch(cls,
    #                                     df: SUPPORTED_DATAFRAMES,
    #                                     batchsize: int = 1) -> List[pa.RecordBatch]:

    #     cls.validate_dataframe_input(df)

    #     if cls.supports_pyarrow_interchange(df):
    #         temp_df = cls._cast_to_pyarrow_table(df)
    #         return from_dataframe(temp_df).to_batches(max_chunksize=batchsize)
    #     else:
    #         return cls._cast_to_pyarrow_recordbatch(df, batchsize=batchsize)



    # =======================
    # Helpers for all classes
    # =======================
    # @classmethod
    # def supports_pyarrow_interchange(cls,
    #                                  df: Union[pa.Table, pd.DataFrame, pl.DataFrame, pl.LazyFrame, ir.Table]) -> bool:

    #     #See whether dataframes support the interchange method:
    #     # https://arrow.apache.org/docs/python/generated/pyarrow.interchange.from_dataframe.html


    #     #If the dataframe has the __dataframe__ method
    #     if hasattr(df, '__dataframe__'):
    #         return True
    #     return False

    # @classmethod
    # def generate_tablename(cls, prefix: Optional[str] = None) -> str:

    #     if prefix:
    #         temp_tablename = f"{prefix}_{str(object=uuid.uuid4())}"
    #     else:
    #         temp_tablename = str(object=uuid.uuid4())

    #     return temp_tablename

    # #Move to mountainash data!
    # def create_temp_table_ibis(cls,
    #                       df: SUPPORTED_DATAFRAMES,
    #                       tablename_prefix: Optional[str] = None,
    #                       current_ibis_backend: Optional[ibis.BaseBackend] = None,
    #                       target_ibis_backend: Optional[ibis.BaseBackend] = None,
    #                       overwrite: Optional[bool] = True,
    #                       create_as_view: Optional[bool] = False
    #         ) -> ir.Table:


    #     cls.validate_dataframe(df)

    #     if overwrite is None:
    #         overwrite = True

    #     tablename = cls.generate_tablename(prefix=tablename_prefix)

    #     if target_ibis_backend is None:

    #         #This will use the default backend in-memory connection
    #         new_table  = ibis.memtable(df,
    #                             columns=cls._get_column_names(df),
    #                             name=tablename)

    #     else:

    #         if current_ibis_backend is target_ibis_backend:

    #             if create_as_view and isinstance(df, ir.Table):
    #                 new_table =  target_ibis_backend.create_view(tablename, obj=df, overwrite=overwrite)
    #                 return new_table
    #         else:
    #             #When moving between backends, we need materialise to move to the new backend
    #             if isinstance(df, ir.Table):
    #                 df = cls._to_pyarrow(df)

    #         if target_ibis_backend.supports_temporary_tables:
    #             new_table =  target_ibis_backend.create_table(tablename, obj=df, overwrite=overwrite, temp=True)
    #         else:
    #             new_table =  target_ibis_backend.create_table(tablename, obj=df, overwrite=overwrite)


    #     return new_table

    # @classmethod
    # def _is_recordbatch(cls, df: Any) -> bool:

    #     if isinstance(df, list):
    #         return isinstance(df[0], pa.RecordBatch)
    #     else:
    #         return isinstance(df, pa.RecordBatch)


    #######################



    # @abstractmethod
    # def _get_column_names(cls, df: Any) -> List[str]:
    #     pass

    # def get_column_names(cls, df: SUPPORTED_DATAFRAMES) -> List[str]:
    #     cls.validate_dataframe_input(df)
    #     return cls._get_column_names(df)


    # #This one is implemented in reverse in the subclasses
    # @abstractmethod
    # def get_table_schema(cls, df) -> ibis_schema.Schema:
    #     pass

    # def _get_table_schema(cls, df) -> ibis_schema.Schema:

    #     df_head = cls.head(df, n=0)
    #     df_pl: pl.DataFrame = cls._to_polars(df_head)
    #     native_schema = df_pl.schema
    #     return ibis_schema.Schema.from_polars(polars_schema=native_schema)



    # @abstractmethod
    # def _drop(cls,
    #           df: Any,
    #           columns: List[str]) -> SUPPORTED_DATAFRAMES:
    #     pass


    # def drop(cls,
    #          df: Union[pd.DataFrame, pl.DataFrame, pl.LazyFrame, ir.Table, pa.Table, pa.RecordBatch, np.ndarray],
    #          columns: List[str]|str) -> SUPPORTED_DATAFRAMES:

    #     cls.validate_dataframe_input(df)

    #     if isinstance(columns, str):
    #         columns = [columns]

    #     existing_columns = cls._get_column_names(df)
    #     columns_to_drop = [col for col in columns if col in existing_columns]

    #     #if an empty list, just retrun the original dataframe!
    #     if not columns_to_drop or len(columns_to_drop) == 0:
    #         return df

    #     return cls._drop(df, columns=columns_to_drop)




    # @abstractmethod
    # def _select(cls,
    #             df: Any,
    #             columns: List[str]) -> SUPPORTED_DATAFRAMES:
    #     pass


    # def select(cls,
    #            df: SUPPORTED_DATAFRAMES,
    #            columns: List[str]|str
    #            ) -> SUPPORTED_DATAFRAMES:

    #     cls.validate_dataframe_input(df)

    #     if isinstance(columns, str):
    #         columns = [columns]

    #     existing_columns = cls._get_column_names(df)
    #     columns_to_select = [col for col in columns if col in existing_columns]

    #     if not columns_to_select or len(columns_to_select) == 0:
    #         return df

    #     return cls._select(df, columns=columns_to_select)




    # @abstractmethod
    # def _head(cls,
    #           df: Any,
    #           n: int) -> SUPPORTED_DATAFRAMES:
    #     pass

    # def head(cls,
    #          df: SUPPORTED_DATAFRAMES,
    #          n: int) -> SUPPORTED_DATAFRAMES:

    #     if n < 0:
    #         raise ValueError("n must be greater than or equal to 0")

    #     cls.validate_dataframe_input(df)
    #     return cls._head(df, n=n)

    # @abstractmethod
    # def _count(cls, df: Any) -> int:
    #     pass

    # def count(cls,
    #           df: SUPPORTED_DATAFRAMES) -> int:
    #     cls.validate_dataframe_input(df)
    #     return cls._count(df)


    # @abstractmethod
    # def _filter(cls, df: Any, condition: ExpressionNode) -> Any:
    #     pass

    # def filter(cls, df: SUPPORTED_DATAFRAMES, condition: ExpressionNode) -> SUPPORTED_DATAFRAMES:
    #     cls.validate_dataframe_input(df)
    #     return cls._filter(df, condition)


    # @abstractmethod
    # def _split_in_batches(cls, df: Any, batch_size: int) -> List[Any]:
    #     pass

    # def split_in_batches(cls,
    #         df: SUPPORTED_DATAFRAMES,
    #         batch_size: int
    #     ) -> List[SUPPORTED_DATAFRAMES]:

    #     cls.validate_dataframe_input(df)
    #     if batch_size <= 0:
    #         raise ValueError("batch_size must be greater than 0")

    #     return cls._split_in_batches(df, batch_size)


    # @abstractmethod
    # def _rename(cls,
    #         df: Any,
    #         mapping: Dict[str, str],
    #         **kwargs) -> SUPPORTED_DATAFRAMES:

    #     pass

    # def rename(cls,
    #         df: SUPPORTED_DATAFRAMES,
    #         mapping: Dict[str, str],
    #     ) -> SUPPORTED_DATAFRAMES:

    #     """Rename columns in a dataframe.

    #     Args:
    #         df: Input dataframe
    #         mapping: Dictionary mapping old column names to new column names
    #         **kwargs: Additional keyword arguments passed to underlying rename implementation

    #     Returns:
    #         DataFrame with renamed columns

    #     Raises:
    #         ValueError: If mapping contains invalid column names
    #     """

    #     cls.validate_dataframe_input(df)

    #     return cls._rename(df, mapping)


    # @abstractmethod
    # def _get_shape(cls, df: Any) -> Any:
    #     """Get native shape format for the specific dataframe type.

    #     Returns the esoteric/native shape format that each library uses internally.
    #     This may be a tuple, individual properties, or other library-specific format.
    #     """
    #     pass

    # def get_shape(cls, df: SUPPORTED_DATAFRAMES) -> tuple:
    #     """Get shape as consistent (rows, columns) tuple across all dataframe types.

    #     Args:
    #         df: Input dataframe of any supported type

    #     Returns:
    #         tuple[int, int]: (rows, columns) tuple

    #     Raises:
    #         TypeError: If dataframe type is not supported
    #     """
    #     cls.validate_dataframe_input(df)
    #     native_shape = cls._get_shape(df)

    #     # Convert native shape format to standardized tuple
    #     if isinstance(native_shape, tuple) and len(native_shape) >= 2:
    #         return (int(native_shape[0]), int(native_shape[1]))
    #     elif isinstance(native_shape, dict) and 'rows' in native_shape and 'columns' in native_shape:
    #         return (int(native_shape['rows']), int(native_shape['columns']))
    #     else:
    #         # Fallback using existing count and column methods
    #         rows = cls.count(df)
    #         cols = len(cls.get_column_names(df))
    #         return (rows, cols)
