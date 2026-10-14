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
                type_spec: Optional['TypeSpec'] = None, *,
                source_spec: Optional['TypeSpec'] = None,
                inline_conform: bool = True
    ) -> PolarsFrame:
        """Convert data to Polars DataFrame using default behavior.

        Args:
            source_spec: Optional source schema for constructor dtype overrides.
            inline_conform: Whether to apply type_spec after construction.
        """
        from .custom_type_helpers import _source_schema_overrides
        schema_overrides = _source_schema_overrides(source_spec)
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Create DataFrame
        df = pl.DataFrame(data, strict=False, schema_overrides=schema_overrides)

        if type_spec is not None and inline_conform:
            import mountainash as ma
            df = ma.relation(df).conform(type_spec).to_polars()

        return df
