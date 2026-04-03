from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.core.types import PolarsFrame

from .base_pydata_ingress_handler import BasePydataIngressHandler

logger = logging.getLogger(__name__)

class IngressFromCollection(BasePydataIngressHandler):
    """Strategy for handling basic Python collections (list, set, frozenset).

    Basic collections are single-column data structures containing scalar values.
    Since they have no metadata, a column name must be provided or will default to 'value'.

    Supported collections:
    - list (of scalars, not dicts/tuples/dataclasses)
    - set
    - frozenset

    Examples:
        [1, 2, 3, 4, 5]                    # list of integers
        {'apple', 'banana', 'cherry'}       # set of strings
        frozenset([1.0, 2.5, 3.7])         # frozenset of floats
    """

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        """
        Check if data is a basic container (list/set/frozenset of scalars).

        Containers of complex objects (dicts, tuples, dataclasses) are handled
        by other converters.
        """
        # Must be list, set, or frozenset (NOT dict - that's handled by DataframeFromPydict)
        if not isinstance(data, (list, set, frozenset)):
            return False

        # Empty containers are valid
        if len(data) == 0:
            return True

        # Get first item to check if it's a scalar
        first_item = next(iter(data))

        # Exclude if it's a complex type handled by other converters
        # - dict → PYLIST converter
        # - tuple with _fields → NAMEDTUPLE converter
        # - tuple without _fields → TUPLE converter (but only if list of tuples)
        # - dataclass → DATACLASS converter
        # - pydantic → PYDANTIC converter

        if isinstance(first_item, dict):
            return False  # Handled by PYLIST

        if hasattr(first_item, '__dataclass_fields__'):
            return False  # Handled by DATACLASS

        if hasattr(first_item, '__pydantic_core_schema__'):
            return False  # Handled by PYDANTIC

        if hasattr(first_item, '_fields'):
            return False  # Handled by NAMEDTUPLE

        if isinstance(first_item, tuple):
            return False  # Handled by TUPLE

        # If it's a scalar (int, str, float, bool, None, etc.), this converter handles it
        return True

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None,
                column_name: Optional[str] = None) -> PolarsFrame:
        """
        Convert basic container (list/set/frozenset) to single-column Polars DataFrame.

        Args:
            data: List, set, or frozenset of scalar values
            column_config: Optional column transformation configuration
            column_name: Name for the single column. Defaults to 'value'

        Returns:
            pl.DataFrame: Single-column DataFrame

        Raises:
            ImportError: If polars is not available
            ValueError: If data format is invalid

        Examples:
            >>> # List of integers with default column name
            >>> data = [1, 2, 3, 4, 5]
            >>> df = DataframeFromContainer.convert(data)
            >>> # Columns: ['value']
            >>>
            >>> # Set of strings with custom column name
            >>> data = {'apple', 'banana', 'cherry'}
            >>> df = DataframeFromContainer.convert(data, column_name='fruit')
            >>> # Columns: ['fruit']
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Validate input type
        if not isinstance(data, (list, set, frozenset)):
            raise ValueError(
                f"Container data must be list, set, or frozenset. Got {type(data)}"
            )

        # Determine column name
        if column_name is None:
            column_name = 'value'

        # Convert set/frozenset to list for Polars
        if isinstance(data, (set, frozenset)):
            data_list = list(data)
        else:
            data_list = data

        # Validate items are scalars
        for idx, item in enumerate(data_list):
            # Check if item is a complex type that should use other converters
            if isinstance(item, dict):
                raise ValueError(
                    f"Container has dict items at index {idx}. Use list of dicts with PYLIST converter instead."
                )
            if hasattr(item, '__dataclass_fields__'):
                raise ValueError(
                    f"Container has dataclass items at index {idx}. Use DATACLASS converter instead."
                )
            if hasattr(item, '__pydantic_core_schema__'):
                raise ValueError(
                    f"Container has Pydantic items at index {idx}. Use PYDANTIC converter instead."
                )
            if hasattr(item, '_fields'):
                raise ValueError(
                    f"Container has named tuple items at index {idx}. Use NAMEDTUPLE converter instead."
                )
            if isinstance(item, tuple):
                raise ValueError(
                    f"Container has tuple items at index {idx}. Use TUPLE converter instead."
                )

        # Create single-column DataFrame
        df = pl.DataFrame({column_name: data_list})

        # Apply column transformations if provided
        if type_spec is not None:
            from mountainash.conform.compiler import compile_conform
            df = compile_conform(type_spec, df)

        return df
