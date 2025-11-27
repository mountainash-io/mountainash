"""Polars null operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import NullExpressionProtocol


class PolarsNullExpressionSystem(PolarsBaseExpressionSystem, NullExpressionProtocol):
    """
    Polars implementation of null operations.

    Implements NullExpressionProtocol methods.
    """

    # ========================================
    # Null Operations
    # ========================================

    def is_null(self, operand: Any) -> pl.Expr:
        """
        Check if operand is NULL using Polars is_null() method.

        Args:
            operand: Operand to check (pl.Expr)

        Returns:
            pl.Expr representing null check
        """
        return operand.is_null()

    def fill_null(self, operand: Any, value: Any) -> pl.Expr:
        """
        Fill null values with specified value.

        Args:
            operand: Operand expression (pl.Expr)
            value: Value to fill nulls with (pl.Expr or literal)

        Returns:
            pl.Expr with nulls filled
        """
        return operand.fill_null(value)

    def null_if(self, operand: Any, condition: Any) -> pl.Expr:
        """
        Return NULL if condition is true, otherwise return operand.

        Args:
            operand: Operand expression (pl.Expr)
            condition: Condition to check (pl.Expr)

        Returns:
            pl.Expr representing null_if result
        """
        return pl.when(condition).then(pl.lit(None)).otherwise(operand)

    def always_null(self) -> pl.Expr:
        """
        Return a NULL literal expression.

        Returns:
            pl.Expr representing NULL
        """
        return pl.lit(None)

    def not_null(self, operand: Any) -> pl.Expr:
        """
        Check if operand is NOT NULL using Polars is_not_null() method.

        Args:
            operand: Operand to check (pl.Expr)

        Returns:
            pl.Expr representing not-null check
        """
        return operand.is_not_null()
