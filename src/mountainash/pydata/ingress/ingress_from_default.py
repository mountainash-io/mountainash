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


class DataframeFromDefault(BasePydataIngressHandler):
    """Default strategy for handling any data that can be passed to polars.DataFrame."""

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        return True

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None,
    ) -> PolarsFrame:
        """Convert data to Polars DataFrame using default behavior."""
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Create DataFrame
        df = pl.DataFrame(data, strict=False)

        if type_spec is not None:
            from mountainash.conform.compiler import compile_conform
            df = compile_conform(type_spec, df)

        return df
