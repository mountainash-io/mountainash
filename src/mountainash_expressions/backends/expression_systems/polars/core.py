"""Polars backend implementation of ExpressionSystem."""

from typing import Any
import polars as pl


from .base import PolarsBaseExpressionSystem
from ....core.protocols import CoreExpressionProtocol

from ....types import PolarsExpr


class PolarsCoreExpressionSystem(PolarsBaseExpressionSystem,
                                  CoreExpressionProtocol):

    # ========================================
    # Core Primitives
    # ========================================

    def col(self, name: str, **kwargs) -> PolarsExpr:
        """
        Create a Polars column reference expression.

        Args:
            name: Column name
            **kwargs: Additional options for pl.col()

        Returns:
            pl.Expr representing the column reference

        TODO: create another method for referencing multiple columns - cols(*selector)
        """
        # pl = import_polars()
        return pl.col(name, **kwargs)

    def lit(self, value: Any) -> PolarsExpr:
        """
        Create a Polars literal value expression.

        Args:
            value: The literal value (int, float, str, bool, etc.)

        Returns:
            pl.Expr representing the literal value
        """
        # pl = import_polars()
        return pl.lit(value)
