"""Polars backend implementation of ExpressionSystem."""

from typing import Any, List, TYPE_CHECKING
import polars as pl

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS

from .base import IbisBaseExpressionSystem
from ....core.protocols.core.column import ColumnExpressionProtocol
from ....core.protocols.core.literal import LiteralExpressionProtocol

if TYPE_CHECKING:
    import ibis as ibis
    import ibis.expr.types as ir
    import polars as pl
    import narwhals as nw
    from ....types import IbisExpr

    from ....runtime_imports import import_ibis

class IbisCoreExpressionSystem(IbisBaseExpressionSystem, ColumnExpressionProtocol, LiteralExpressionProtocol):

    # ========================================
    # Core Primitives
    # ========================================


    def col(self, name: str, **kwargs) -> IbisExpr:
        """
        Create a Ibis column reference expression.

        Args:
            name: Column name
            **kwargs: Additional options for pl.col()

        Returns:
            pl.Expr representing the column reference
        """
        ibis = import_ibis()
        return ibis._[name]


    def lit(self, value: Any) -> IbisExpr:
        """
        Create a Ibis literal value expression.

        Args:
            value: The literal value (int, float, str, bool, etc.)

        Returns:
            pl.Expr representing the literal value
        """
        # ibis = import_ibis()
        return ibis.literal(value)
