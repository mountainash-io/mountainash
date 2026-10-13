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
                type_spec: Optional['TypeSpec'] = None,
                *,
                source_spec: Optional['TypeSpec'] = None,
                inline_conform: bool = True,
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
            type_spec: Optional TypeSpec for column type coercion and renaming
            source_spec: Optional source dtype declarations.
            inline_conform: Whether to apply target conversions.

        Returns:
            Polars DataFrame with hybrid conversions applied
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        from .custom_type_helpers import _source_schema_overrides, apply_hybrid_conversion

        overrides = _source_schema_overrides(source_spec)
        if type_spec is not None and inline_conform:

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
            df = apply_hybrid_conversion(data_dicts, type_spec, schema_overrides=overrides)
        else:
            # No spec - just create DataFrame directly from columnar data
            df = pl.DataFrame(data, strict=False, schema_overrides=overrides)

        return df
