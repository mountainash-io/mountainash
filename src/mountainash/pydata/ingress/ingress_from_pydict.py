from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Union
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    import polars as pl

from .base_pydata_ingress_handler import BasePydataIngressHandler
from mountainash.schema.config import SchemaConfig, init_column_config
from mountainash.core.types import PolarsFrame

logger = logging.getLogger(__name__)


class DataframeFromPydict(BasePydataIngressHandler):
    """Strategy for handling dictionary of lists."""

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        return (isinstance(data, dict) and
                all(isinstance(v, (list, tuple, Sequence))
                    for v in data.values()))

    @classmethod
    def convert(cls,
                data: Any, /,
                column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None
    ) -> PolarsFrame:
        """
        Convert dictionary of lists to Polars DataFrame.

        Uses HYBRID STRATEGY for optimal performance:
        - Custom converters: Apply at EDGES (Python layer, before DataFrame)
        - Native conversions: Apply in CENTER (DataFrame layer, vectorized)

        This is ~10x faster than applying custom conversions in DataFrame!

        Args:
            data: Dictionary of lists (columnar format)
                  Example: {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
            column_config: Optional column transformation config

        Returns:
            Polars DataFrame with hybrid conversions applied
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Apply hybrid conversion strategy if config provided
        if column_config is not None:
            from .custom_type_helpers import apply_hybrid_conversion

            column_transforms: SchemaConfig = init_column_config(column_config)

            # Convert columnar format (dict of lists) to row format (list of dicts)
            # for hybrid conversion
            if not data:
                data_dicts = []
            else:
                # Get number of rows from first column
                first_col = next(iter(data.values()))
                num_rows = len(first_col)

                # Convert to list of dicts
                data_dicts = [
                    {col: data[col][i] for col in data.keys()}
                    for i in range(num_rows)
                ]

            # HYBRID STRATEGY:
            # 1. Custom converters at edges (Python layer)
            # 2. Native conversions in DataFrame (vectorized, FAST!)
            df = apply_hybrid_conversion(data_dicts, column_transforms)
        else:
            # No config - just create DataFrame directly from columnar data
            df = pl.DataFrame(data, strict=False)

        return df
