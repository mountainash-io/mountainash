"""Narwhals FieldReferenceExpressionProtocol implementation.

Implements column reference operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitFieldReferenceExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr



class SubstraitNarwhalsFieldReferenceExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitFieldReferenceExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of FieldReferenceExpressionProtocol."""

    def col(self, x: str) -> NarwhalsExpr:
        """Create a column reference expression.

        Args:
            x: The column name to reference.

        Returns:
            A Narwhals expression referencing the named column.
        """
        return nw.col(x)
