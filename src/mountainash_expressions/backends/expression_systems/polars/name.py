"""Polars name/alias operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import NameExpressionProtocol


class PolarsNameExpressionSystem(PolarsBaseExpressionSystem, NameExpressionProtocol):
    """Polars implementation of name/alias operations."""

    def alias(self, operand: Any, name: str) -> pl.Expr:
        """
        Rename an expression/column.

        Args:
            operand: Expression to rename
            name: New name for the expression

        Returns:
            Expression with new alias
        """
        return operand.alias(name)

    def prefix(self, operand: Any, prefix: str) -> pl.Expr:
        """
        Add prefix to column name.

        Args:
            operand: Column expression
            prefix: Prefix to add

        Returns:
            Expression with prefixed name
        """
        return operand.name.prefix(prefix)

    def suffix(self, operand: Any, suffix: str) -> pl.Expr:
        """
        Add suffix to column name.

        Args:
            operand: Column expression
            suffix: Suffix to add

        Returns:
            Expression with suffixed name
        """
        return operand.name.suffix(suffix)

    def to_upper(self, operand: Any) -> pl.Expr:
        """
        Convert column name to uppercase.

        Args:
            operand: Column expression

        Returns:
            Expression with uppercase name
        """
        return operand.name.to_uppercase()

    def to_lower(self, operand: Any) -> pl.Expr:
        """
        Convert column name to lowercase.

        Args:
            operand: Column expression

        Returns:
            Expression with lowercase name
        """
        return operand.name.to_lowercase()
