"""Narwhals FieldReferenceExpressionProtocol implementation.

Implements column reference operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from .base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_field_reference import (
        FieldReferenceExpressionProtocol,
    )


class NarwhalsFieldReferenceSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of FieldReferenceExpressionProtocol."""

    def col(self, x: str) -> nw.Expr:
        """Create a column reference expression.

        Args:
            x: The column name to reference.

        Returns:
            A Narwhals expression referencing the named column.
        """
        return nw.col(x)
