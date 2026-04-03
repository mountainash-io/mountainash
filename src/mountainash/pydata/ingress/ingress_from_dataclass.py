from __future__ import annotations

from dataclasses import is_dataclass, fields
from typing import TYPE_CHECKING, Any, Optional
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.core.types import PolarsFrame

from .base_pydata_ingress_handler import BasePydataIngressHandler

logger = logging.getLogger(__name__)


class DataframeFromDataclass(BasePydataIngressHandler):
    """Strategy for handling dataclass instances."""

    @classmethod
    def can_handle(cls, data: Any) -> bool:
        return (is_dataclass(data) or
                (isinstance(data, list) and
                 len(data) > 0 and
                 is_dataclass(data[0])))

    @classmethod
    def convert(cls,
                data: Any,
                type_spec: Optional['TypeSpec'] = None,
    ) -> PolarsFrame:
        """
        Convert dataclass instance(s) to Polars DataFrame.

        Uses HYBRID STRATEGY for optimal performance:
        - Custom converters: Apply at EDGES (Python layer, before DataFrame)
        - Native conversions: Apply in CENTER (DataFrame layer, vectorized)

        This is ~10x faster than applying custom conversions in DataFrame!

        Args:
            data: Single dataclass instance or list of dataclass instances
            type_spec: Optional TypeSpec for column type coercion and renaming

        Returns:
            Polars DataFrame with hybrid conversions applied
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Convert to list of dicts
        if isinstance(data, list):
            data_dicts = [
                {field.name: getattr(item, field.name) for field in fields(item)}
                for item in data
            ]
        else:
            data_dicts = [{
                field.name: getattr(data, field.name) for field in fields(data)
            }]

        # Apply hybrid conversion strategy if spec provided
        if type_spec is not None:
            from .custom_type_helpers import apply_hybrid_conversion

            # HYBRID STRATEGY:
            # 1. Custom converters at edges (Python layer)
            # 2. Native conversions in DataFrame (vectorized, FAST!)
            df = apply_hybrid_conversion(data_dicts, type_spec)
        else:
            # No spec - just create DataFrame
            df = pl.DataFrame(data_dicts, strict=False)

        return df
