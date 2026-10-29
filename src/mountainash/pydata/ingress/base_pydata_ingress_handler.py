from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from mountainash.typespec.spec import TableSchema
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
                table_schema: Optional['TableSchema'] = None,
                *,
                source_table_schema: Optional['TableSchema'] = None,
                inline_conform: bool = True,
    ) -> PolarsFrame:
        """
        Convert input data to a Polars DataFrame.

        Args:
            data: Input data to convert
            table_schema: Optional conversion target, not source evidence.
            source_table_schema: Optional source dtype declarations.
            inline_conform: Whether to apply target conversions.

        Returns:
            pl.DataFrame: Converted data
        """
        pass
