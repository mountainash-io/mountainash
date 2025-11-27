"""Narwhals null operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import NullExpressionProtocol


class NarwhalsNullExpressionSystem(NarwhalsBaseExpressionSystem, NullExpressionProtocol):
    """Narwhals implementation of null operations."""

    def is_null(self, operand: Any) -> nw.Expr:
        """Check if operand is NULL using Narwhals is_null() method."""
        return operand.is_null()

    def fill_null(self, operand: Any, value: Any) -> nw.Expr:
        """Fill null values with specified value."""
        return operand.fill_null(value)

    def null_if(self, operand: Any, condition: Any) -> nw.Expr:
        """Return NULL if condition is true, otherwise return operand."""
        return nw.when(condition).then(nw.lit(None)).otherwise(operand)

    def always_null(self) -> nw.Expr:
        """Return a NULL literal expression."""
        return nw.lit(None)

    def not_null(self, operand: Any) -> nw.Expr:
        """Check if operand is NOT NULL using Narwhals is_not_null() method."""
        return operand.is_not_null()
