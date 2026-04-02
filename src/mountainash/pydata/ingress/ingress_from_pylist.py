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

class DataframeFromPylist(BasePydataIngressHandler):
    """Strategy for handling list of dictionaries."""

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        return (isinstance(data, list) and
                len(data) > 0 and
                isinstance(data[0], dict))

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None
    ) -> PolarsFrame:
        """
        Convert list of dictionaries to Polars DataFrame.

        Uses HYBRID STRATEGY for optimal performance:
        - Custom converters: Apply at EDGES (Python layer, before DataFrame)
        - Native conversions: Apply in CENTER (DataFrame layer, vectorized)

        This is ~10x faster than applying custom conversions in DataFrame!

        Args:
            data: List of dictionaries (row format)
                  Example: [{"col1": 1, "col2": "a"}, {"col1": 2, "col2": "b"}]
            type_spec: Optional TypeSpec for column type coercion and renaming

        Returns:
            Polars DataFrame with hybrid conversions applied
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Apply hybrid conversion strategy if spec provided
        if type_spec is not None:
            from .custom_type_helpers import apply_hybrid_conversion

            # HYBRID STRATEGY:
            # 1. Custom converters at edges (Python layer)
            # 2. Native conversions in DataFrame (vectorized, FAST!)
            df = apply_hybrid_conversion(data, type_spec)
        else:
            # No spec - just create DataFrame
            df = pl.DataFrame(data, strict=False)

        return df
