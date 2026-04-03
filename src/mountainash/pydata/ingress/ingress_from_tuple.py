from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.core.types import PolarsFrame

from .base_pydata_ingress_handler import BasePydataIngressHandler

logger = logging.getLogger(__name__)

class DataframeFromTuple(BasePydataIngressHandler):
    """Strategy for handling plain tuples (single or list).

    Note: Since plain tuples don't have field names, column names must be provided
    either through the column_config or will be auto-generated as col_0, col_1, etc.
    """

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        """
        Check if data is a plain tuple or list of plain tuples.

        Plain tuples do NOT have _fields attribute (unlike named tuples).
        """
        # Single tuple (but not named tuple)
        if isinstance(data, tuple) and not hasattr(data, '_fields'):
            return True

        # List of tuples (but not named tuples)
        if isinstance(data, (list, tuple)) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, tuple) and not hasattr(first_item, '_fields'):
                return True

        return False

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None,
                column_names: Optional[List[str]] = None) -> PolarsFrame:
        """
        Convert plain tuple(s) to Polars DataFrame.

        Args:
            data: Single tuple or sequence of tuples
            column_config: Optional column transformation configuration
            column_names: Optional list of column names. If not provided, auto-generates col_0, col_1, etc.

        Returns:
            pl.DataFrame: Converted DataFrame

        Raises:
            ImportError: If polars is not available
            ValueError: If data format is invalid or column count mismatch

        Examples:
            >>> # List of tuples with column names
            >>> data = [(1, 'Alice', 30), (2, 'Bob', 25)]
            >>> df = DataframeFromTuple.convert(data, column_names=['id', 'name', 'age'])
            >>>
            >>> # Single tuple with auto-generated column names
            >>> data = (1, 'Alice', 30)
            >>> df = DataframeFromTuple.convert(data)  # Columns: col_0, col_1, col_2
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Handle single tuple - convert to list
        if isinstance(data, tuple) and not isinstance(data[0] if data else None, tuple):
            data = [data]

        # Validate we have data
        if not data or len(data) == 0:
            raise ValueError("Cannot convert empty sequence of tuples")

        # Get first item to determine number of columns
        first_item = data[0] if isinstance(data, (list, tuple)) else data
        if not isinstance(first_item, tuple):
            raise ValueError("Data does not contain valid tuples")

        if hasattr(first_item, '_fields'):
            raise ValueError(
                "Data contains named tuples. Use DataframeFromNamedTuple instead. "
                "This converter is for plain tuples only."
            )

        num_columns = len(first_item)

        # Generate column names if not provided
        if column_names is None:
            column_names = [f"col_{i}" for i in range(num_columns)]
        else:
            if len(column_names) != num_columns:
                raise ValueError(
                    f"Column name count mismatch. Expected {num_columns} names, got {len(column_names)}"
                )

        # Validate all tuples have the same length
        for idx, item in enumerate(data):
            if not isinstance(item, tuple):
                raise ValueError(f"All items must be tuples, got {type(item)} at index {idx}")

            if hasattr(item, '_fields'):
                raise ValueError(
                    f"Mixed tuple types detected at index {idx}. Found named tuple in plain tuple list."
                )

            if len(item) != num_columns:
                raise ValueError(
                    f"Inconsistent tuple length at index {idx}. Expected {num_columns}, got {len(item)}"
                )

        # Convert tuples to list of dictionaries for Polars
        dict_data = []
        for item in data:
            dict_data.append(dict(zip(column_names, item)))

        # Create DataFrame from list of dictionaries
        df = pl.DataFrame(dict_data, strict=False)

        # Apply column transformations if provided
        if type_spec is not None:
            from mountainash.conform.compiler import compile_conform
            df = compile_conform(type_spec, df)

        return df
