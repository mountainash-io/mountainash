from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union
import logging
from enum import Enum

from mountainash.core.factories import BaseStrategyFactory
from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT

from .base_pydata_ingress_handler import BasePydataIngressHandler
from mountainash.core.types import PolarsFrame

if TYPE_CHECKING:
    import polars as pl
    from mountainash.schema.config import SchemaConfig

logger = logging.getLogger(__name__)

class PydataIngressFactory(BaseStrategyFactory[Any, BasePydataIngressHandler]):
    """Factory for creating appropriate Python data conversion strategies with lazy loading."""

    @classmethod
    def convert(cls,
                data: Any, /,
                column_config: Optional[Union["SchemaConfig", Dict[str, Any], str]] = None
    ) -> PolarsFrame:
        """
        Convert Python data structure to Polars DataFrame.

        This is the main public interface for data conversion.

        Args:
            data: Input data (dataclass, Pydantic model, dict of lists, or list of dicts)
            column_config: Optional column transformation configuration

        Returns:
            pl.DataFrame: Converted DataFrame

        Raises:
            ValueError: If no suitable strategy is found or conversion fails

        Example:
            # >>> factory = PydataConverterFactory()
            >>> df = PydataConverter.convert([{"id": 1, "name": "Alice"}])
            >>> isinstance(df, pl.DataFrame)
            True
        """
        strategy = cls.get_strategy(data)
        return strategy.convert(data, column_config=column_config)


    @classmethod
    def _configure_strategy_mapping(cls) -> None:
        """
        Configure the mapping from strategy keys to module paths and class names.

        This method should populate _strategy_modules and _strategy_classes
        with the mapping information, but NOT import anything.
        """

        cls._strategy_modules = {
            CONST_PYTHON_DATAFORMAT.DATACLASS:     "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.PYDANTIC:      "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.PYDICT:        "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.PYLIST:        "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.NAMEDTUPLE:    "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.TUPLE:         "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.INDEXED_DATA:  "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.SERIES_DICT:   "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.COLLECTION:    "mountainash.pydata.ingress",
            CONST_PYTHON_DATAFORMAT.UNKNOWN:       "mountainash.pydata.ingress",
        }

        cls._strategy_classes = {
            CONST_PYTHON_DATAFORMAT.DATACLASS:     "DataframeFromDataclass",
            CONST_PYTHON_DATAFORMAT.PYDANTIC:      "DataframeFromPydantic",
            CONST_PYTHON_DATAFORMAT.PYDICT:        "DataframeFromPydict",
            CONST_PYTHON_DATAFORMAT.PYLIST:        "DataframeFromPylist",
            CONST_PYTHON_DATAFORMAT.NAMEDTUPLE:    "DataframeFromNamedTuple",
            CONST_PYTHON_DATAFORMAT.TUPLE:         "DataframeFromTuple",
            CONST_PYTHON_DATAFORMAT.INDEXED_DATA:  "DataframeFromIndexedData",
            CONST_PYTHON_DATAFORMAT.SERIES_DICT:   "DataframeFromSeriesDict",
            CONST_PYTHON_DATAFORMAT.COLLECTION:    "DataframeFromCollection",
            CONST_PYTHON_DATAFORMAT.UNKNOWN:       "DataframeFromDefault",


        }


    @classmethod
    def _get_strategy_key(cls, data: Any, /, **kwargs) -> Optional[Enum]:
        """Determine the strategy key based on data type."""
        # Check for Pydantic models
        if hasattr(data, '__pydantic_core_schema__'):
            return CONST_PYTHON_DATAFORMAT.PYDANTIC

        # Check for dataclasses
        if hasattr(data, '__dataclass_fields__'):
            return CONST_PYTHON_DATAFORMAT.DATACLASS

        # Check for named tuples (single or in a list)
        # Named tuples have _fields attribute, must check before generic tuple checks
        if hasattr(data, '_fields') and isinstance(data._fields, tuple):
            return CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

        # Check for plain tuples (single or in a list)
        # Plain tuples do NOT have _fields attribute
        if isinstance(data, tuple) and not hasattr(data, '_fields'):
            return CONST_PYTHON_DATAFORMAT.TUPLE

        # Check for dictionary of Series (must check BEFORE indexed data and PYDICT)
        # Series have specific type signatures we can detect
        if isinstance(data, dict) and data:
            first_value = next(iter(data.values()))
            type_name = type(first_value).__name__
            module_name = type(first_value).__module__

            # Check for Polars or Pandas Series
            if (module_name.startswith('polars') or module_name.startswith('pandas')) and type_name == 'Series':
                return CONST_PYTHON_DATAFORMAT.SERIES_DICT

        # Check for indexed data structures (Dict[key, List[rows]])
        # Must check BEFORE PYDICT to distinguish indexed data from column data
        if isinstance(data, dict) and data:
            first_value = next(iter(data.values()))
            if isinstance(first_value, (list, tuple)) and first_value:
                first_item = first_value[0]
                # If first item is tuple/dict/namedtuple, it's indexed data (rows)
                # If it's a scalar, it's PYDICT (column values)
                if isinstance(first_item, (tuple, dict)) or hasattr(first_item, '_fields'):
                    return CONST_PYTHON_DATAFORMAT.INDEXED_DATA

        # Check for dictionary of lists (column-oriented data)
        if isinstance(data, dict) and all(isinstance(v, (list, tuple)) for v in data.values()):
            return CONST_PYTHON_DATAFORMAT.PYDICT

        # Check for basic collections (list/set/frozenset of scalars)
        # Must check BEFORE PYLIST to distinguish scalar lists from list of dicts
        if isinstance(data, (list, set, frozenset)):
            if not data:
                # Empty collections are valid for COLLECTION
                return CONST_PYTHON_DATAFORMAT.COLLECTION
            first_item = next(iter(data))
            # Exclude complex types that should use other converters
            if not isinstance(first_item, dict) and \
               not hasattr(first_item, '__dataclass_fields__') and \
               not hasattr(first_item, '__pydantic_core_schema__') and \
               not hasattr(first_item, '_fields') and \
               not isinstance(first_item, tuple):
                # It's a scalar - this is a basic collection
                return CONST_PYTHON_DATAFORMAT.COLLECTION

        # Check for list of dictionaries
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return CONST_PYTHON_DATAFORMAT.PYLIST

        # Check for list of Pydantic models
        if isinstance(data, list) and data and hasattr(data[0], '__pydantic_core_schema__'):
            return CONST_PYTHON_DATAFORMAT.PYDANTIC

        # Check for list of dataclasses
        if isinstance(data, list) and data and hasattr(data[0], '__dataclass_fields__'):
            return CONST_PYTHON_DATAFORMAT.DATACLASS

        # Check for list of named tuples
        if isinstance(data, (list, tuple)) and data and hasattr(data[0], '_fields') and isinstance(data[0]._fields, tuple):
            return CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

        # Check for list of plain tuples
        if isinstance(data, (list, tuple)) and data:
            first_item = data[0]
            if isinstance(first_item, tuple) and not hasattr(first_item, '_fields'):
                return CONST_PYTHON_DATAFORMAT.TUPLE

        # Fallback to default strategy
        return CONST_PYTHON_DATAFORMAT.UNKNOWN

    # @classmethod
    # def _select_strategy(cls, strategy_key: str, data: Any, **kwargs):
    #     """Select conversion strategy with intelligent fallbacks."""
    #     # Direct strategy mapping
    #     if strategy_key in cls._strategies:
    #         return cls._strategies.get(strategy_key)

    #     # Fallback to compatible strategies
    #     if strategy_key == "pydantic" and "dataclass" in cls._strategies:
    #         logger.debug("Pydantic not available, falling back to dataclass converter")
    #         return cls._strategies.get("dataclass")

    #     # Fallback to default strategy
    #     if "default" in cls._strategies:
    #         logger.debug(f"No specific strategy for {strategy_key}, using default converter")
    #         return cls._strategies.get("default")

    #     return super()._select_strategy(strategy_key, data, **kwargs)



    # @classmethod
    # def _register_strategies(cls, backends: Dict[str, bool]) -> None:
    #     """Register available conversion strategies."""
    #     # Core strategies always available
    #     try:
    #         from .dataframe_from_pydict import DataframeFromPydict
    #         from .dataframe_from_pylist import DataframeFromPylist
    #         cls._strategies["pydict"] = DataframeFromPydict
    #         cls._strategies["pylist"] = DataframeFromPylist
    #     except ImportError as e:
    #         logger.debug(f"Could not import core conversion strategies: {e}")

    #     # Optional strategies based on available backends
    #     if backends.get("pydantic", False):
    #         try:
    #             from .dataframe_from_pydantic import DataframeFromPydantic
    #             cls._strategies["pydantic"] = DataframeFromPydantic
    #         except ImportError as e:
    #             logger.debug(f"Could not import Pydantic converter: {e}")

    #     # Dataclass support (standard library)
    #     try:
    #         from .dataframe_from_dataclass import DataframeFromDataclass
    #         cls._strategies["dataclass"] = DataframeFromDataclass
    #     except ImportError as e:
    #         logger.debug(f"Could not import dataclass converter: {e}")

    #     # Default strategy if available
    #     try:
    #         from .dataframe_from_default import DataframeFromDefault
    #         cls._strategies["default"] = DataframeFromDefault
    #     except ImportError as e:
    #         logger.debug(f"Could not import default converter: {e}")
