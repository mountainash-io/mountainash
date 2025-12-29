"""Polars FieldReferenceExpressionProtocol implementation.

Implements column reference operations for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitFieldReferenceExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr


class PolarsFieldReferenceExpressionSystem(PolarsBaseExpressionSystem, SubstraitFieldReferenceExpressionSystemProtocol):
    """Polars implementation of FieldReferenceExpressionProtocol."""

    def col(self, x: str) -> PolarsExpr:
        """Create a column reference expression.

        Args:
            x: The column name to reference.

        Returns:
            A Polars expression referencing the named column.
        """
        return pl.col(x)
