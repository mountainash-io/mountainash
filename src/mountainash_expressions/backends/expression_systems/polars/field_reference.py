"""Polars FieldReferenceExpressionProtocol implementation.

Implements column reference operations for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from .base import PolarsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_field_reference import (
        FieldReferenceExpressionProtocol,
    )


class PolarsFieldReferenceSystem(PolarsBaseExpressionSystem):
    """Polars implementation of FieldReferenceExpressionProtocol."""

    def col(self, x: str) -> pl.Expr:
        """Create a column reference expression.

        Args:
            x: The column name to reference.

        Returns:
            A Polars expression referencing the named column.
        """
        return pl.col(x)
