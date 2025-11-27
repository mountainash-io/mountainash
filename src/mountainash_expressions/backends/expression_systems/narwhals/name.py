"""Narwhals name/alias operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import NameExpressionProtocol


class NarwhalsNameExpressionSystem(NarwhalsBaseExpressionSystem, NameExpressionProtocol):
    """Narwhals implementation of name/alias operations."""

    def alias(self, operand: Any, name: str) -> nw.Expr:
        """
        Rename an expression/column.

        Args:
            operand: Expression to rename
            name: New name for the expression

        Returns:
            Expression with new alias
        """
        return operand.alias(name)

    def prefix(self, operand: Any, prefix: str) -> nw.Expr:
        """
        Add prefix to column name.

        Args:
            operand: Column expression
            prefix: Prefix to add

        Returns:
            Expression with prefixed name

        Note:
            Narwhals uses name.prefix() similar to Polars.
        """
        return operand.name.prefix(prefix)

    def suffix(self, operand: Any, suffix: str) -> nw.Expr:
        """
        Add suffix to column name.

        Args:
            operand: Column expression
            suffix: Suffix to add

        Returns:
            Expression with suffixed name

        Note:
            Narwhals uses name.suffix() similar to Polars.
        """
        return operand.name.suffix(suffix)

    def to_upper(self, operand: Any) -> nw.Expr:
        """
        Convert column name to uppercase.

        Args:
            operand: Column expression

        Returns:
            Expression with uppercase name

        Note:
            Narwhals uses name.to_uppercase() similar to Polars.
        """
        return operand.name.to_uppercase()

    def to_lower(self, operand: Any) -> nw.Expr:
        """
        Convert column name to lowercase.

        Args:
            operand: Column expression

        Returns:
            Expression with lowercase name

        Note:
            Narwhals uses name.to_lowercase() similar to Polars.
        """
        return operand.name.to_lowercase()
