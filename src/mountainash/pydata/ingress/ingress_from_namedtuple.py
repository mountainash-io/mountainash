from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.core.types import PolarsFrame

from .base_pydata_ingress_handler import BasePydataIngressHandler

logger = logging.getLogger(__name__)

class DataframeFromNamedTuple(BasePydataIngressHandler):
    """Strategy for handling named tuples (single or list)."""

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        """
        Check if data is a named tuple or list of named tuples.

        Named tuples have a _fields attribute that regular tuples don't have.
        """
        # Single named tuple
        if hasattr(data, '_fields') and isinstance(data._fields, tuple):
            return True

        # List of named tuples
        if isinstance(data, (list, tuple)) and len(data) > 0:
            first_item = data[0]
            if hasattr(first_item, '_fields') and isinstance(first_item._fields, tuple):
                return True

        return False

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None,
    ) -> PolarsFrame:
        """
        Convert named tuple(s) to Polars DataFrame.

        Args:
            data: Single named tuple or sequence of named tuples
            column_config: Optional column transformation configuration

        Returns:
            pl.DataFrame: Converted DataFrame

        Raises:
            ImportError: If polars is not available
            ValueError: If data format is invalid

        Examples:
            >>> from collections import namedtuple
            >>> Person = namedtuple('Person', ['name', 'age', 'city'])
            >>>
            >>> # Single named tuple
            >>> person = Person('Alice', 30, 'NYC')
            >>> df = DataframeFromNamedTuple.convert(person)
            >>>
            >>> # List of named tuples
            >>> people = [Person('Alice', 30, 'NYC'), Person('Bob', 25, 'LA')]
            >>> df = DataframeFromNamedTuple.convert(people)
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Handle single named tuple - convert to list
        if hasattr(data, '_fields') and not isinstance(data, (list, tuple, Sequence)):
            data = [data]
        elif hasattr(data, '_fields'):
            # It's a single named tuple that happens to be iterable
            # Check if it's really a sequence of named tuples or just one
            if not (isinstance(data, (list, tuple)) and len(data) > 0 and hasattr(data[0], '_fields')):
                data = [data]

        # Validate we have data
        if not data or len(data) == 0:
            raise ValueError("Cannot convert empty sequence of named tuples")

        # Get field names from first item
        first_item = data[0] if isinstance(data, (list, tuple)) else data
        if not hasattr(first_item, '_fields'):
            raise ValueError("Data does not contain valid named tuples")

        field_names = first_item._fields

        # Convert named tuples to list of dictionaries
        # This allows Polars to handle type inference properly
        dict_data = []
        for item in data:
            if not hasattr(item, '_fields'):
                raise ValueError(f"All items must be named tuples, got {type(item)}")

            # Verify field consistency
            if item._fields != field_names:
                raise ValueError(
                    f"Inconsistent named tuple fields. Expected {field_names}, got {item._fields}"
                )

            # Convert to dict using _asdict() method if available, otherwise manual
            if hasattr(item, '_asdict'):
                dict_data.append(item._asdict())
            else:
                dict_data.append(dict(zip(field_names, item)))

        # Create DataFrame from list of dictionaries
        df = pl.DataFrame(dict_data, strict=False)

        # Apply column transformations if provided
        if type_spec is not None:
            from mountainash.conform.compiler import compile_conform
            df = compile_conform(type_spec, df)

        return df
