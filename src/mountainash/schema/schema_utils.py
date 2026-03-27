fom __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Sequence, Set, Tuple, TypeVar, Union

# Runtime imports for actual functionality

if TYPE_CHECKING:
    # import pandas as pd
    # import polars as pl
    # import pyarrow as pa
    import ibis
    # import ibis.expr.types as ir
    import ibis.expr.schema as ibis_schema
    # import narwhals as nw

from .constants import CONST_DATAFRAME_FRAMEWORK

from .typing import (
    SupportedDataFrames,
    PandasFrame,
    PyArrowTable,
    IbisTable,
    NarwhalsFrameTypes,
    PolarsFrameTypes,
    PolarsFrame,
    PolarsLazyFrame,
    PandasSeries,
    PolarsSeries,
    SupportedPythonData,
)
# Factories
from .cast import DataFrameCastFactory, BaseCastDataFrame
from .filter_expressions import FilterExpressionStrategyFactory
from .ingress import PydataConverterFactory
# from .export import DataclassExportFactory

from .introspect import DataFrameIntrospectFactory
from .join import DataFrameJoinFactory
# from .reshape import DataFrameSelectFactory
from .schema_config import SchemaConfig
# from .schema_transform import SchemaTransformFactory
from .select import DataFrameSelectFactory

# Mixins
from .mixins import DynamicInputHandlerMixin

# Generic type variable for dataclass types
T = TypeVar('T')


class SchemaUtils():

    ################################
    # Schema Extraction & Validation Methods

    @classmethod
    def extract_schema(cls, source: Any) -> 'TableSchema':
        """
        Extract TableSchema from DataFrame or Python type.

        Convenience wrapper that auto-detects the source type and calls
        the appropriate extractor (from_dataframe, from_dataclass, from_pydantic).

        Args:
            source: DataFrame, dataclass type, or Pydantic model to extract schema from

        Returns:
            TableSchema representing the source structure

        Examples:
            >>> # From DataFrame
            >>> schema = DataFrameUtils.extract_schema(df)

            >>> # From dataclass
            >>> @dataclass
            >>> class User:
            ...     id: int
            ...     name: str
            >>> schema = DataFrameUtils.extract_schema(User)

            >>> # From Pydantic model
            >>> schema = DataFrameUtils.extract_schema(UserModel)
        """
        from .schema_config import from_dataframe, from_dataclass, from_pydantic

        # Auto-detect source type and extract
        if hasattr(source, '__dataclass_fields__'):
            return from_dataclass(source)
        elif hasattr(source, '__pydantic_core_schema__') or hasattr(source, '__fields__'):
            # Pydantic v2 or v1
            return from_pydantic(source)
        else:
            # Assume it's a DataFrame
            return from_dataframe(source)

    @classmethod
    def validate_schema(
        cls,
        df: SupportedDataFrames,
        expected_schema: 'TableSchema',
        strict: bool = True
    ) -> bool:
        """
        Validate that DataFrame matches expected schema.

        Args:
            df: DataFrame to validate
            expected_schema: Expected TableSchema
            strict: If True, extra columns are errors. If False, extra columns allowed.

        Returns:
            True if schema matches, False otherwise

        Examples:
            >>> from mountainash.dataframes.schema_config import TableSchema
            >>> expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
            >>> is_valid = DataFrameUtils.validate_schema(df, expected)
            >>> if not is_valid:
            ...     print("Schema mismatch!")
        """
        from .schema_config import validate_schema_match

        is_valid, _ = validate_schema_match(df, expected_schema, strict)
        return is_valid

    @classmethod
    def assert_schema(
        cls,
        df: SupportedDataFrames,
        expected_schema: 'TableSchema',
        strict: bool = True
    ) -> None:
        """
        Assert that DataFrame matches expected schema (raises on failure).

        Args:
            df: DataFrame to validate
            expected_schema: Expected TableSchema
            strict: If True, extra columns are errors

        Raises:
            SchemaValidationError: If validation fails

        Examples:
            >>> from mountainash.dataframes.schema_config import TableSchema
            >>> expected = TableSchema.from_simple_dict({"id": "integer"})
            >>> DataFrameUtils.assert_schema(df, expected)  # Raises if invalid
        """
        from .schema_config import assert_schema_match

        assert_schema_match(df, expected_schema, strict)

    @classmethod
    def transform_with_schema(
        cls,
        df: SupportedDataFrames,
        config: SchemaConfig
    ) -> SupportedDataFrames:
        """
        Apply schema transformation to DataFrame.

        Convenience wrapper for SchemaTransformFactory.

        Args:
            df: DataFrame to transform
            config: SchemaConfig with transformation specifications

        Returns:
            Transformed DataFrame (same backend as input)

        Examples:
            >>> from mountainash.dataframes.schema_config import SchemaConfig
            >>> config = SchemaConfig(columns={"old_id": {"rename": "id", "cast": "integer"}})
            >>> result = DataFrameUtils.transform_with_schema(df, config)
        """
        from .schema_transform import SchemaTransformFactory

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(df)
        return strategy.apply(df, config)

    @classmethod
    def transform_from_schemas(
        cls,
        df: SupportedDataFrames,
        source_schema: 'TableSchema',
        target_schema: 'TableSchema',
        fuzzy_match_threshold: float = 0.6,
        auto_cast: bool = True,
        keep_unmapped_source: bool = False
    ) -> SupportedDataFrames:
        """
        Transform DataFrame from source schema to target schema.

        Auto-generates SchemaConfig using schema diffing and fuzzy matching,
        then applies the transformation.

        Args:
            df: DataFrame to transform
            source_schema: Source TableSchema
            target_schema: Target TableSchema
            fuzzy_match_threshold: Similarity threshold for fuzzy matching (0.0-1.0)
            auto_cast: Automatically add type casts when types differ
            keep_unmapped_source: Keep source columns not mapped to target

        Returns:
            Transformed DataFrame matching target schema

        Examples:
            >>> from mountainash.dataframes.schema_config import TableSchema
            >>> source = TableSchema.from_simple_dict({"user_id": "string"})
            >>> target = TableSchema.from_simple_dict({"user_id": "integer"})
            >>> result = DataFrameUtils.transform_from_schemas(df, source, target)
        """
        from .schema_config import SchemaConfig

        config = SchemaConfig.from_schemas(
            source_schema,
            target_schema,
            fuzzy_match_threshold=fuzzy_match_threshold,
            auto_cast=auto_cast,
            keep_unmapped_source=keep_unmapped_source
        )

        return cls.transform_with_schema(df, config)

    @classmethod
    def validate_transformation(
        cls,
        target_df: SupportedDataFrames,
        source_df: SupportedDataFrames,
        config: SchemaConfig
    ) -> bool:
        """
        Validate that transformation produced expected output.

        Compares the actual output schema with the predicted schema
        from the SchemaConfig.

        Args:
            target_df: Transformed DataFrame (output)
            source_df: Original DataFrame (input)
            config: SchemaConfig used for transformation

        Returns:
            True if transformation is valid, False otherwise

        Examples:
            >>> from mountainash.dataframes.schema_config import SchemaConfig
            >>> config = SchemaConfig(columns={"old": {"rename": "new"}})
            >>> result = DataFrameUtils.transform_with_schema(source, config)
            >>> is_valid = DataFrameUtils.validate_transformation(result, source, config)
        """
        from .schema_config import validate_round_trip

        is_valid, _ = validate_round_trip(target_df, source_df, config)
        return is_valid

    @classmethod
    def assert_transformation(
        cls,
        target_df: SupportedDataFrames,
        source_df: SupportedDataFrames,
        config: SchemaConfig
    ) -> None:
        """
        Assert that transformation produced expected output (raises on failure).

        Args:
            target_df: Transformed DataFrame (output)
            source_df: Original DataFrame (input)
            config: SchemaConfig used for transformation

        Raises:
            SchemaValidationError: If validation fails

        Examples:
            >>> from mountainash.dataframes.schema_config import SchemaConfig
            >>> config = SchemaConfig(columns={"old": {"rename": "new"}})
            >>> result = DataFrameUtils.transform_with_schema(source, config)
            >>> DataFrameUtils.assert_transformation(result, source, config)
        """
        from .schema_config import assert_round_trip

        assert_round_trip(target_df, source_df, config)


#---------------------------------
# Module Level Helper Functions
#---------------------------------

def create_dataframe(
            data: Dict[str, Union[Sequence,List]] | List[Dict[str, Any]],
            /,
            dataframe_framework: str,
            column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None
         ) -> SupportedDataFrames:
    return DataFrameUtils.create_dataframe(data,
                                            dataframe_framework=dataframe_framework,
                                          column_config=column_config)

def create_pandas(
            data: Dict[str, Union[Sequence,List]] | List[Dict[str, Any]],
            /,

            # column_dict: Optional[Dict[str, str|Dict[str,str]]]=None,
            column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None
            ) -> PandasFrame:
    return DataFrameUtils.create_pandas(data,
                                       column_config=column_config)

def create_polars(
            data: Dict[str, Union[Sequence,List]] | List[Dict[str, Any]],
            /,

            # column_dict: Optional[Dict[str, str|Dict[str,str]]]=None,
            column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None

            ) -> PolarsFrameTypes:
    return DataFrameUtils.create_polars(data,
                                       column_config=column_config)

def create_pyarrow(
        data: Dict[str, Union[Sequence, List]] | List[Dict[str, Any]],
        /,

        # column_dict: Optional[Dict[str, str|Dict[str,str]]] = None,
        column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None

    ) -> PyArrowTable:
    return DataFrameUtils.create_pyarrow(data,
                                       column_config=column_config)

def create_ibis(
            data: Dict[str, Union[Sequence,List]] | List[Dict[str, Any]],
            /,

            # column_dict: Optional[Dict[str, str|Dict[str,str]]] = None,
            column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None
            ) -> IbisTable:
    return DataFrameUtils.create_ibis(data,
                                       column_config=column_config)


def cast_dataframe(
                       data: Union[SupportedDataFrames,SupportedPythonData],
                       /,

                       dataframe_framework: str) -> SupportedDataFrames:
    return DataFrameUtils.cast_dataframe(data, dataframe_framework=dataframe_framework)


def to_narwhals(data: Union[SupportedDataFrames,SupportedPythonData], /, as_lazy: Optional[bool] = None) -> NarwhalsFrameTypes:
    return DataFrameUtils.to_narwhals(data, as_lazy=as_lazy)

def to_pandas(data: Union[SupportedDataFrames,SupportedPythonData], /) -> PandasFrame:
    return DataFrameUtils.to_pandas(data)

def to_polars(data: Union[SupportedDataFrames,SupportedPythonData], /, as_lazy: Optional[bool] = None) -> PolarsFrameTypes:
    return DataFrameUtils.to_polars(data, as_lazy=as_lazy)

def to_polars_lazy(data: Union[SupportedDataFrames,SupportedPythonData], /) -> PolarsLazyFrame:
    return DataFrameUtils.to_polars_lazy(data)

def to_polars_eager(data: Union[SupportedDataFrames,SupportedPythonData], /) -> PolarsFrame:
    return DataFrameUtils.to_polars_eager(data)


def to_pyarrow(data: SupportedDataFrames) -> PyArrowTable:
    return DataFrameUtils.to_pyarrow(data)

def to_ibis(data: Union[SupportedDataFrames,SupportedPythonData], /,
            ibis_backend=None,
            tablename_prefix=None  ) -> IbisTable:
    return DataFrameUtils.to_ibis(data, ibis_backend=ibis_backend, tablename_prefix=tablename_prefix)

def to_dictionary_of_lists(data: Union[SupportedDataFrames,SupportedPythonData], /) -> Dict[Any, List[Any]]:
    return DataFrameUtils.to_dictionary_of_lists(data)

def to_dictionary_of_series_pandas( data: Union[SupportedDataFrames,SupportedPythonData], /) -> Dict[str, PandasSeries]:
    return DataFrameUtils.to_dictionary_of_series_pandas(data)

def to_dictionary_of_series_polars( data: Union[SupportedDataFrames,SupportedPythonData], /,) -> Dict[str, PolarsSeries]:
    return DataFrameUtils.to_dictionary_of_series_polars(data)

def to_list_of_dictionaries(  data: Union[SupportedDataFrames,SupportedPythonData], /) -> List[Dict[Any, Any]]:
    return DataFrameUtils.to_list_of_dictionaries(data)

def to_list_of_tuples(  data: Union[SupportedDataFrames,SupportedPythonData], /) -> List[Dict[Any, Any]]:
    return DataFrameUtils.to_list_of_tuples(data)

def to_list_of_named_tuples(  data: Union[SupportedDataFrames,SupportedPythonData], /) -> List[Dict[Any, Any]]:
    return DataFrameUtils.to_list_of_named_tuples(data)

def to_list_of_typed_named_tuples(  data: Union[SupportedDataFrames,SupportedPythonData], /, preserve_dates: Optional[bool] = False) -> List[Dict[Any, Any]]:
    return DataFrameUtils.to_list_of_typed_named_tuples(data, preserve_dates=preserve_dates)


def to_index_of_dictionaries(  data: Union[SupportedDataFrames,SupportedPythonData], /, index_fields: str|List[str]) -> Dict[str, List]:
    return DataFrameUtils.to_index_of_dictionaries(data, index_fields=index_fields)

def to_index_of_tuples(  data: Union[SupportedDataFrames,SupportedPythonData], /, index_fields: str|List[str]) -> Dict[str, List]:
    return DataFrameUtils.to_index_of_tuples(data, index_fields=index_fields)

def to_index_of_named_tuples(  data: Union[SupportedDataFrames,SupportedPythonData], /, index_fields: str|List[str]) -> Dict[str, List]:
    return DataFrameUtils.to_index_of_named_tuples(data, index_fields=index_fields)

def to_index_of_typed_named_tuples(  data: Union[SupportedDataFrames,SupportedPythonData], /, index_fields: str|List[str], preserve_dates: Optional[bool] = False) -> Dict[str, List]:
    return DataFrameUtils.to_index_of_typed_named_tuples(data, index_fields=index_fields, preserve_dates=preserve_dates)

def to_list_of_dataclasses( data: Union[SupportedDataFrames,SupportedPythonData], /,
                            dataclass_type: Any,
                            mapping: Optional[Dict[str, str]] = None,
                            apply_defaults: bool = False) -> List[Any]:
    return DataFrameUtils.to_list_of_dataclasses(data, dataclass_type=dataclass_type, mapping=mapping, apply_defaults=apply_defaults)

def to_list_of_pydantic( data: Union[SupportedDataFrames,SupportedPythonData], /,
                         model_class: Any,
                         mapping: Optional[Dict[str, str]] = None) -> List[Any]:
    return DataFrameUtils.to_list_of_pydantic(data, model_class=model_class, mapping=mapping)



def column_names( data: Union[SupportedDataFrames,SupportedPythonData], /) -> List[str]:
    return DataFrameUtils.column_names(data)

def table_schema_ibis( data: Union[SupportedDataFrames,SupportedPythonData], /) -> "ibis_schema.Schema":
    return DataFrameUtils.table_schema_ibis(data)

def drop(data: Union[SupportedDataFrames,SupportedPythonData], /,
             columns: List[str]|str) -> SupportedDataFrames:
    return DataFrameUtils.drop(data, columns=columns)

def select(data: Union[SupportedDataFrames,SupportedPythonData], /,
               columns: List[str]|str) -> SupportedDataFrames:
    return DataFrameUtils.select(data, columns=columns)

def head(data: Union[SupportedDataFrames,SupportedPythonData], /,
             n: int) -> SupportedDataFrames:
    return DataFrameUtils.head(data, n=n)

def count(
              data: Union[SupportedDataFrames,SupportedPythonData], /) -> int:
    return DataFrameUtils.count(data)

def split_dataframe_in_batches(
    data: Union[SupportedDataFrames,SupportedPythonData], /,
    batch_size: int
) -> Tuple[List[SupportedDataFrames], int]:
    """Split DataFrame into batches with single materialization.

    Module-level function wrapping DataFrameUtils.split_dataframe_in_batches.
    See DataFrameUtils.split_dataframe_in_batches for full documentation.
    """
    return DataFrameUtils.split_dataframe_in_batches(data, batch_size=batch_size)

def split_dataframe_in_batches_generator(
    data: Union[SupportedDataFrames,SupportedPythonData], /,
    batch_size: int
) -> Generator[SupportedDataFrames, None, None]:
    """Memory-efficient batch generator for large DataFrames.

    Module-level function wrapping DataFrameUtils.split_dataframe_in_batches_generator.
    See DataFrameUtils.split_dataframe_in_batches_generator for full documentation.
    """
    yield from DataFrameUtils.split_dataframe_in_batches_generator(data, batch_size=batch_size)

def filter(
               data: Union[SupportedDataFrames,SupportedPythonData], /,
               expression: Any) -> SupportedDataFrames:
    return DataFrameUtils.filter(data, expression=expression)

def get_dataframe_info(data: Union[SupportedDataFrames,SupportedPythonData], /) -> Dict[str, Any]:
    return DataFrameUtils.get_dataframe_info(data)

def get_column_as_list(
            data: Union[SupportedDataFrames,SupportedPythonData], /,
            column:str
        ) -> List[Any]:
    return DataFrameUtils.get_column_as_list(data, column=column)

def get_column_as_series_pandas(
            data: Union[SupportedDataFrames,SupportedPythonData], /,
            column:str
        ) -> Optional[PandasSeries]:
    return DataFrameUtils.get_column_as_series_pandas(data, column=column)

def get_column_as_series_polars(
            data: Union[SupportedDataFrames,SupportedPythonData], /,
            column:str
        ) -> Optional[PolarsSeries]:
    return DataFrameUtils.get_column_as_series_polars(data, column=column)

def get_column_as_set(
            data: Union[SupportedDataFrames,SupportedPythonData], /,
            column:str
        ) -> Set[Any]:
    return DataFrameUtils.get_column_as_set(data, column=column)

def get_first_row_as_dict(
            data: Union[SupportedDataFrames,SupportedPythonData], /
        ) -> Dict[Any,Any]:
    return DataFrameUtils.get_first_row_as_dict(data)


def inner_join(
        left: SupportedDataFrames,
        right: SupportedDataFrames,
        predicates: Any,
        execute_on: Optional["str"] = None,
        **kwargs
    ) -> SupportedDataFrames:

    return DataFrameUtils.inner_join(left=left, right=right, predicates=predicates, execute_on=execute_on, **kwargs)


def left_join(
        left: SupportedDataFrames,
        right: SupportedDataFrames,
        predicates: Any,
        execute_on: Optional["str"] = None,
        **kwargs
    ) -> SupportedDataFrames:

    return DataFrameUtils.left_join(left=left, right=right, predicates=predicates, execute_on=execute_on, **kwargs)


def outer_join(
        left: SupportedDataFrames,
        right: SupportedDataFrames,
        predicates: Any,
        execute_on: Optional["str"] = None,
        **kwargs
    ) -> SupportedDataFrames:

    return DataFrameUtils.outer_join(left=left, right=right, predicates=predicates, execute_on=execute_on, **kwargs)
