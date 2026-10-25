from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    from mountainash.typespec.spec import TableSchema
    from mountainash.core.types import PolarsFrame

from .base_pydata_ingress_handler import BasePydataIngressHandler
from mountainash.core.lowering_reuse import REPEATABLE, declare_lowering

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
                table_schema: Optional['TableSchema'] = None,
                *,
                source_table_schema: Optional['TableSchema'] = None,
                inline_conform: bool = True,
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
            table_schema: Optional TableSchema for column type coercion and renaming
            source_table_schema: Optional source dtype declarations.
            inline_conform: Whether to apply target conversions.

        Returns:
            Polars DataFrame with hybrid conversions applied
        """
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        from .custom_type_helpers import _source_schema_overrides, apply_hybrid_conversion

        df = apply_hybrid_conversion(
            data, table_schema, schema_overrides=_source_schema_overrides(source_table_schema),
            inline_conform=inline_conform,
        )

        return df
declare_lowering(DataframeFromPylist.convert.__func__, REPEATABLE)
