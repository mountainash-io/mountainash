from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    import polars as pl

from mountainash.schema.config import SchemaConfig
from mountainash.core.types import PolarsFrame

# class PydataInputType(Enum):
#     """Enumeration of supported input data structure types."""
#     LIST_OF_DICTS = auto()
#     DICT_OF_LISTS = auto()
#     DATACLASS = auto()
#     PYDANTIC = auto()
#     DATAFRAME = auto()
#     UNKNOWN = auto()

class BasePydataIngressHandler(ABC):
    """Abstract base class for data structure conversion strategies."""

    @classmethod
    @abstractmethod
    def can_handle(cls, data: Any, /) -> bool:
        """
        Check if this strategy can handle the input data.
        """
        pass

    @classmethod
    @abstractmethod
    def convert(cls,
                data: Any, /,
                column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None
    ) -> PolarsFrame:
        """
        Convert input data to a Polars DataFrame.

        Args:
            data: Input data to convert
            column_mapping: Optional column mapping dictionary

        Returns:
            pl.DataFrame: Converted data
        """
        pass
