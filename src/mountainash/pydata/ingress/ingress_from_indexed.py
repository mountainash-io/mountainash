from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.core.types import PolarsFrame

from .base_pydata_ingress_handler import BasePydataIngressHandler

logger = logging.getLogger(__name__)

class DataframeFromIndexedData(BasePydataIngressHandler):
    """Strategy for handling indexed data structures.

    Indexed data is a dictionary where:
    - Keys are index values (scalar or tuple for composite keys)
    - Values are lists of data rows (tuples, dicts, or named tuples)

    This format is returned by cast module methods like:
    - to_index_of_tuples()
    - to_index_of_dictionaries()
    - to_index_of_named_tuples()
    - to_index_of_typed_named_tuples()

    Example formats:
        # Simple index with tuple values
        {
            'key1': [(val1, val2), (val3, val4)],
            'key2': [(val5, val6)]
        }

        # Composite index with dict values
        {
            ('2024', 'Q1'): [{'revenue': 100, 'cost': 50}],
            ('2024', 'Q2'): [{'revenue': 120, 'cost': 55}]
        }
    """

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        """
        Check if data is an indexed data structure.

        Indexed data is a dict where values are lists/tuples.
        """
        if not isinstance(data, dict):
            return False

        if len(data) == 0:
            return True  # Empty dict with indexed format is valid

        # Check if all values are lists or tuples
        first_value = next(iter(data.values()))
        if not isinstance(first_value, (list, tuple)):
            return False

        # Distinguish from PYDICT (dict of lists where keys are column names)
        # In indexed data, values are lists of ROWS (tuples/dicts/namedtuples)
        # In PYDICT, values are lists of COLUMN VALUES (scalars)

        if len(first_value) == 0:
            return True  # Empty list - could be either, accept as indexed

        first_item = first_value[0]

        # If the first item in the list is a tuple, dict, or has _fields (namedtuple),
        # it's indexed data (rows)
        if isinstance(first_item, (tuple, dict)) or hasattr(first_item, '_fields'):
            return True

        # If it's a scalar, it's PYDICT (column values), not indexed data
        return False

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None,
                index_column_names: Optional[Union[str, List[str]]] = None) -> PolarsFrame:
        """
        Convert indexed data structure to Polars DataFrame.

        Args:
            data: Indexed data structure (Dict[key, List[row]])
            column_config: Optional column transformation configuration
            index_column_names: Name(s) for index column(s). If not provided:
                - Single key: 'index'
                - Composite key: 'index_0', 'index_1', etc.

        Returns:
            pl.DataFrame: Converted DataFrame with index values as columns

        Raises:
            ImportError: If polars is not available
            ValueError: If data format is invalid

        Examples:
            >>> # Simple index with tuple rows
            >>> data = {'A': [(1, 'x'), (2, 'y')], 'B': [(3, 'z')]}
            >>> df = DataframeFromIndexedData.convert(
            ...     data,
            ...     column_names=['value', 'label']
            ... )
            >>> # Result: index | value | label
            >>> #         A     | 1     | x
            >>> #         A     | 2     | y
            >>> #         B     | 3     | z
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        if not isinstance(data, dict):
            raise ValueError("Indexed data must be a dictionary")

        if len(data) == 0:
            # Return empty DataFrame
            return pl.DataFrame()

        # Collect all rows with their index values
        all_rows = []

        for key, rows in data.items():
            if not isinstance(rows, (list, tuple)):
                raise ValueError(
                    f"All values in indexed data must be lists or tuples, got {type(rows)} for key {key}"
                )

            # Determine if key is composite (tuple) or simple
            is_composite_key = isinstance(key, tuple)

            for row in rows:
                # Convert row to dict
                if isinstance(row, dict):
                    row_dict = dict(row)
                elif hasattr(row, '_fields'):
                    # Named tuple
                    row_dict = row._asdict() if hasattr(row, '_asdict') else dict(zip(row._fields, row))
                elif isinstance(row, tuple):
                    # Plain tuple - need to generate column names
                    # Use col_0, col_1, etc. for now
                    row_dict = {f"col_{i}": val for i, val in enumerate(row)}
                else:
                    raise ValueError(
                        f"Unsupported row type in indexed data: {type(row)}. "
                        f"Expected tuple, dict, or named tuple."
                    )

                # Add index column(s)
                if is_composite_key:
                    # Composite key - multiple index columns
                    if index_column_names is None:
                        index_col_names = [f"index_{i}" for i in range(len(key))]
                    elif isinstance(index_column_names, str):
                        # Single name provided but key is composite - error
                        raise ValueError(
                            f"Composite key has {len(key)} values but only one index column name provided"
                        )
                    else:
                        if len(index_column_names) != len(key):
                            raise ValueError(
                                f"Composite key length ({len(key)}) doesn't match "
                                f"index column names count ({len(index_column_names)})"
                            )
                        index_col_names = index_column_names

                    # Add each key component as a separate column
                    for idx, (col_name, key_val) in enumerate(zip(index_col_names, key)):
                        row_dict[col_name] = key_val
                else:
                    # Simple key - single index column
                    index_col_name = index_column_names if isinstance(index_column_names, str) else (
                        index_column_names[0] if index_column_names else 'index'
                    )
                    row_dict[index_col_name] = key

                all_rows.append(row_dict)

        # Create DataFrame from all rows
        df = pl.DataFrame(all_rows, strict=False)

        # Apply column transformations if provided
        if type_spec is not None:
            import mountainash as ma
            df = ma.relation(df).conform(type_spec).to_polars()

        return df
