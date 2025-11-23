"""Polars backend implementation of ExpressionSystem."""

from typing import Any, List
from ibis.expr.operations.strings import VarTuple
import narwhals as nw

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols.core.column import ColumnExpressionProtocol
from ....core.protocols.core.literal import LiteralExpressionProtocol
from ....runtime_imports import import_narwhals
from ....types import NarwhalsExpr

class PolarsCoreExpressionSystem(NarwhalsBaseExpressionSystem, ColumnExpressionProtocol, LiteralExpressionProtocol):

    # ========================================
    # Core Primitives
    # ========================================

    def col(self, name: str, **kwargs) -> NarwhalsExpr:
        """
        Create a Polars column reference expression.

        Args:
            name: Column name
            **kwargs: Additional options for pl.col()

        Returns:
            pl.Expr representing the column reference
        """
        # nw = import_narwhals()
        return nw.col(name, **kwargs)

    def lit(self, value: Any) -> NarwhalsExpr:
        """
        Create a Polars literal value expression.

        Args:
            value: The literal value (int, float, str, bool, etc.)

        Returns:
            pl.Expr representing the literal value
        """
        # nw = import_narwhals()
        return nw.lit(value)
