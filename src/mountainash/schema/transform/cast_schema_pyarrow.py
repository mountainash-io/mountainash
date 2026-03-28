"""
PyArrow-specific column transformation strategy.

Implements column transformations using PyArrow Table API.
For complex transformations, delegates to Narwhals for universal support.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.lazy_imports import import_pyarrow, import_narwhals
from .base_schema_transform_strategy import BaseCastSchemaStrategy


if TYPE_CHECKING:
    import pyarrow as pa
    from mountainash.core.types import PyArrowTable
    from mountainash.schema.config import SchemaConfig


class CastSchemaPyArrow(BaseCastSchemaStrategy):
    """
    PyArrow Table column transformation strategy.

    PyArrow has limited transformation capabilities compared to pandas/polars.
    For most operations, we convert to Narwhals, transform, then convert back.

    This ensures consistent behavior while leveraging PyArrow's memory efficiency.
    """

    @classmethod
    def _apply(cls,
               df: 'PyArrowTable',
               config: 'SchemaConfig') -> 'PyArrowTable':
        """
        Apply column transformations to PyArrow Table.

        Uses Narwhals as an intermediate for transformations due to
        PyArrow's limited transformation API.

        Args:
            df: PyArrow Table
            config: SchemaConfig with transformation specs

        Returns:
            Transformed PyArrow Table
        """
        nw = import_narwhals()
        if nw is None:
            raise ImportError("narwhals is required for PyArrow column transformations")

        # Convert to Narwhals
        nw_df = nw.from_native(df, eager_only=True)

        # Use Narwhals transformation logic
        # Note: Narwhals._apply() returns native DataFrame, not Narwhals DF
        from .schema_transform_narwhals import CastSchemaNarwhals

        transformed = CastSchemaNarwhals._apply(nw_df, config)

        # transformed is already a PyArrow Table (Narwhals returns native type)
        return transformed
