"""Ibis name/alias operations implementation."""

from typing import Any
import ibis

from .base import IbisBaseExpressionSystem
from ....core.protocols import NameExpressionProtocol


class IbisNameExpressionSystem(IbisBaseExpressionSystem, NameExpressionProtocol):
    """Ibis implementation of name/alias operations."""

    def alias(self, operand: Any, name: str) -> Any:
        """
        Rename an expression/column.

        Args:
            operand: Expression to rename
            name: New name for the expression

        Returns:
            Expression with new alias
        """
        return operand.name(name)

    def prefix(self, operand: Any, prefix: str) -> Any:
        """
        Add prefix to column name.

        Args:
            operand: Column expression
            prefix: Prefix to add

        Returns:
            Expression with prefixed name

        Note:
            ISSUE: Ibis doesn't have name.prefix() like Polars.
            This implementation assumes operand is a column reference
            and reconstructs it with the prefixed name.
        """
        # Get current column name (if it's a column reference)
        if hasattr(operand, 'get_name'):
            current_name = operand.get_name()
            return ibis._[f"{prefix}{current_name}"]
        else:
            # Fallback: try to get name and reapply
            return operand.name(f"{prefix}{{name}}")

    def suffix(self, operand: Any, suffix: str) -> Any:
        """
        Add suffix to column name.

        Args:
            operand: Column expression
            suffix: Suffix to add

        Returns:
            Expression with suffixed name

        Note:
            ISSUE: Ibis doesn't have name.suffix() like Polars.
            This implementation assumes operand is a column reference
            and reconstructs it with the suffixed name.
        """
        # Get current column name (if it's a column reference)
        if hasattr(operand, 'get_name'):
            current_name = operand.get_name()
            return ibis._[f"{current_name}{suffix}"]
        else:
            # Fallback: try to get name and reapply
            return operand.name(f"{{name}}{suffix}")

    def to_upper(self, operand: Any) -> Any:
        """
        Convert column name to uppercase.

        Args:
            operand: Column expression

        Returns:
            Expression with uppercase name

        Note:
            ISSUE: Ibis doesn't have name.to_uppercase() like Polars.
            This implementation assumes operand is a column reference
            and reconstructs it with uppercase name.
        """
        if hasattr(operand, 'get_name'):
            current_name = operand.get_name()
            return ibis._[current_name.upper()]
        else:
            # This won't work properly - placeholderset_name
            return operand

    def to_lower(self, operand: Any) -> Any:
        """
        Convert column name to lowercase.

        Args:
            operand: Column expression

        Returns:
            Expression with lowercase name

        Note:
            ISSUE: Ibis doesn't have name.to_lowercase() like Polars.
            This implementation assumes operand is a column reference
            and reconstructs it with lowercase name.
        """
        if hasattr(operand, 'get_name'):
            current_name = operand.get_name()
            return ibis._[current_name.lower()]
        else:
            # This won't work properly - placeholder
            return operand
