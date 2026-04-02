from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec

from .base_pydata_ingress_handler import BasePydataIngressHandler
from mountainash.core.types import PolarsFrame

logger = logging.getLogger(__name__)

class DataframeFromSeriesDict(BasePydataIngressHandler):
    """Strategy for handling dictionaries of Series (Polars or Pandas).

    This format is returned by cast module methods:
    - to_dictionary_of_series_polars()
    - to_dictionary_of_series_pandas()

    Input format: Dict[str, Series] where Series can be:
    - polars.Series
    - pandas.Series

    Example:
        {
            'column1': pl.Series([1, 2, 3]),
            'column2': pl.Series(['a', 'b', 'c'])
        }
    """

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        """
        Check if data is a dictionary of Series objects.

        Series have specific type signatures we can detect without importing.
        """
        if not isinstance(data, dict):
            return False

        if len(data) == 0:
            return False  # Empty dict - can't determine type

        # Get first value to check
        first_value = next(iter(data.values()))

        # Check if it's a Series by looking at type name and module
        type_name = type(first_value).__name__
        module_name = type(first_value).__module__

        # Check for Polars Series
        if module_name.startswith('polars') and type_name == 'Series':
            return True

        # Check for Pandas Series
        if module_name.startswith('pandas') and type_name == 'Series':
            return True

        return False

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None
        ) -> PolarsFrame:
        """
        Convert dictionary of Series to Polars DataFrame.

        Args:
            data: Dictionary mapping column names to Series objects
            column_config: Optional column transformation configuration

        Returns:
            pl.DataFrame: Converted DataFrame

        Raises:
            ImportError: If polars is not available
            ValueError: If data format is invalid

        Examples:
            >>> import polars as pl
            >>> data = {
            ...     'id': pl.Series([1, 2, 3]),
            ...     'name': pl.Series(['Alice', 'Bob', 'Charlie'])
            ... }
            >>> df = DataframeFromSeriesDict.convert(data)
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        if not isinstance(data, dict):
            raise ValueError("Series dict data must be a dictionary")

        if len(data) == 0:
            return pl.DataFrame()

        # Verify all values are Series
        for key, value in data.items():
            type_name = type(value).__name__
            module_name = type(value).__module__

            if not (
                (module_name.startswith('polars') and type_name == 'Series') or
                (module_name.startswith('pandas') and type_name == 'Series')
            ):
                raise ValueError(
                    f"All values must be Series objects. Got {type(value)} for key '{key}'"
                )

        # Determine if we have Polars or Pandas Series
        first_value = next(iter(data.values()))
        module_name = type(first_value).__module__

        if module_name.startswith('polars'):
            # Native Polars Series - can create DataFrame directly
            df = pl.DataFrame(data)
        elif module_name.startswith('pandas'):
            # Pandas Series - need to convert
            # Import pandas only if needed
            try:
                import pandas as pd
            except ImportError:
                raise ImportError(
                    "pandas is required to convert pandas Series to DataFrame. "
                    "Install with: pip install pandas"
                )

            # Verify all are pandas Series
            from mountainash.core.types import is_pandas_series
            for key, value in data.items():
                if not is_pandas_series(value):
                    raise ValueError(f"Mixed Series types detected. Key '{key}' is not a pandas Series")

            # Create pandas DataFrame first, then convert to Polars
            pandas_df = pd.DataFrame(data)
            df = pl.from_pandas(pandas_df)
        else:
            raise ValueError(f"Unsupported Series type from module: {module_name}")

        # Apply column transformations if provided
        if type_spec is not None:
            from mountainash.conform.compiler import compile_conform
            df = compile_conform(type_spec, df)

        return df
