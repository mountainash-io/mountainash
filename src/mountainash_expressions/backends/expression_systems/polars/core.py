"""Polars backend implementation of ExpressionSystem."""

from typing import Any, List
import polars as pl

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS

from .base import PolarsBaseExpressionSystem
from ....core.protocols.core.column import ColumnExpressionProtocol
from ....core.protocols.core.literal import LiteralExpressionProtocol
from ....runtime_imports import import_polars

from ....types import PolarsExpr

class PolarsCoreExpressionSystem(PolarsBaseExpressionSystem, ColumnExpressionProtocol, LiteralExpressionProtocol):

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
