"""
Factory for backend-specific column transformation strategies.

Follows the established BaseStrategyFactory pattern with lazy loading.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.factories import BaseStrategyFactory, DataFrameTypeFactoryMixin
from mountainash.core.constants import CONST_DATAFRAME_TYPE

if TYPE_CHECKING:
    from mountainash.core.types import SupportedDataFrames
    from .base_schema_transform_strategy import BaseCastSchemaStrategy


class CastSchemaFactory(
    DataFrameTypeFactoryMixin,
    BaseStrategyFactory[Any, Any]
):
    """
    Factory for backend-specific schema transformation strategies.

    Automatically detects DataFrame backend and returns appropriate strategy
    for applying schema transformations (rename, cast, null_fill, defaults).

    Uses lazy loading to avoid unnecessary imports - strategies are only
    loaded when first used.

    Example:
        >>> from mountainash.schema.transform import CastSchemaFactory
        >>> from mountainash.schema.config import SchemaConfig
        >>> config = SchemaConfig(columns={"old": {"rename": "new"}})
        >>> strategy = CastSchemaFactory.get_strategy(df)  # Auto-detects backend
        >>> result = strategy.apply(df, config)
    """

    @classmethod
    def _configure_strategy_mapping(cls) -> None:
        """
        Configure strategy module and class mappings for lazy loading.

        Maps each DataFrame backend type to its corresponding strategy
        implementation. Strategies are imported only when first accessed.
        """
        cls._strategy_modules = {
            CONST_DATAFRAME_TYPE.PANDAS_DATAFRAME:  "mountainash.schema.transform",
            CONST_DATAFRAME_TYPE.POLARS_DATAFRAME:  "mountainash.schema.transform",
            CONST_DATAFRAME_TYPE.POLARS_LAZYFRAME:  "mountainash.schema.transform",
            CONST_DATAFRAME_TYPE.IBIS_TABLE:        "mountainash.schema.transform",
            CONST_DATAFRAME_TYPE.PYARROW_TABLE:     "mountainash.schema.transform",
            CONST_DATAFRAME_TYPE.NARWHALS_DATAFRAME:"mountainash.schema.transform",
            CONST_DATAFRAME_TYPE.NARWHALS_LAZYFRAME:"mountainash.schema.transform",
        }

        cls._strategy_classes = {
            CONST_DATAFRAME_TYPE.PANDAS_DATAFRAME:  "CastSchemaPandas",
            CONST_DATAFRAME_TYPE.POLARS_DATAFRAME:  "CastSchemaPolars",
            CONST_DATAFRAME_TYPE.POLARS_LAZYFRAME:  "CastSchemaPolarsLazy",
            CONST_DATAFRAME_TYPE.IBIS_TABLE:        "CastSchemaIbis",
            CONST_DATAFRAME_TYPE.PYARROW_TABLE:     "CastSchemaPyArrow",
            CONST_DATAFRAME_TYPE.NARWHALS_DATAFRAME:"CastSchemaNarwhals",
            CONST_DATAFRAME_TYPE.NARWHALS_LAZYFRAME:"CastSchemaNarwhals",
        }


# Backward compatibility alias
# DEPRECATED: Use CastSchemaFactory instead
# Will be removed in version 3.0.0
# ColumnTransformFactory = CastSchemaFactory
