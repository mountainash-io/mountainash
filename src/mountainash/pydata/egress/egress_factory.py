#file: mountainash_dataframes/cast/cast_factory.py
"""
Factory for DataFrame casting strategies with lazy loading.

This module implements lazy loading of strategy classes to avoid importing
all dataframe libraries at module load time.
"""

from __future__ import annotations

import logging

from mountainash.dataframes.core.typing import SupportedDataFrames

from mountainash.core.constants import CONST_DATAFRAME_TYPE

from .base_egress_strategy import BaseEgressDataFrame as BaseCastDataFrame
from mountainash.core.factories import DataFrameTypeFactoryMixin, BaseStrategyFactory

logger = logging.getLogger(__name__)


class DataFrameEgressFactory(DataFrameTypeFactoryMixin, BaseStrategyFactory[SupportedDataFrames, BaseCastDataFrame]):
    """Factory for selecting appropriate DataFrame casting strategies with lazy loading."""

    @classmethod
    def _configure_strategy_mapping(cls) -> None:
        """
        Configure the mapping from strategy keys to module paths and class names.

        This method should populate _strategy_modules and _strategy_classes
        with the mapping information, but NOT import anything.
        """

        cls._strategy_modules = {
            CONST_DATAFRAME_TYPE.PANDAS_DATAFRAME:     "mountainash.pydata.egress",
            CONST_DATAFRAME_TYPE.POLARS_DATAFRAME:     "mountainash.pydata.egress",
            CONST_DATAFRAME_TYPE.POLARS_LAZYFRAME:     "mountainash.pydata.egress",
            CONST_DATAFRAME_TYPE.IBIS_TABLE:           "mountainash.pydata.egress",
            CONST_DATAFRAME_TYPE.PYARROW_TABLE:        "mountainash.pydata.egress",
            CONST_DATAFRAME_TYPE.NARWHALS_DATAFRAME:   "mountainash.pydata.egress",
            CONST_DATAFRAME_TYPE.NARWHALS_LAZYFRAME:   "mountainash.pydata.egress"
        }

        cls._strategy_classes = {
            CONST_DATAFRAME_TYPE.PANDAS_DATAFRAME:     "EgressPydataFromPolars",
            CONST_DATAFRAME_TYPE.POLARS_DATAFRAME:     "EgressPydataFromPolars",
            CONST_DATAFRAME_TYPE.POLARS_LAZYFRAME:     "EgressPydataFromPolars",
            CONST_DATAFRAME_TYPE.IBIS_TABLE:           "EgressPydataFromPolars",
            CONST_DATAFRAME_TYPE.PYARROW_TABLE:        "EgressPydataFromPolars",
            CONST_DATAFRAME_TYPE.NARWHALS_DATAFRAME:   "EgressPydataFromPolars",
            CONST_DATAFRAME_TYPE.NARWHALS_LAZYFRAME:   "EgressPydataFromPolars"
        }

    # @lru_cache(maxsize=128)
    # @classmethod
    # def _get_type_key(cls, module: str, name: str) -> tuple[str, str]:
    #     """Cache type information to avoid repeated string operations."""
    #     return (module, name)


    # @classmethod
    # def _get_strategy_key(cls, data: SupportedDataFrames, **kwargs) -> Optional[Enum]:
    #     """
    #     Detect the backend type of a dataframe object without importing libraries.
    #     """

    #     obj_type = type(data)
    #     type_key = cls._get_type_key(obj_type.__module__, obj_type.__name__)
    #     type_map = cls._type_map()

    #     # Direct lookup first
    #     if type_key in type_map:
    #         return type_map.get(type_key)

    #     # Fallback with module prefix matching for edge cases
    #     module, name = type_key
    #     for (mod_pattern, class_name), backend in type_map.items():
    #         if name == class_name and module.startswith(mod_pattern.split('.')[0]):
    #             return backend
