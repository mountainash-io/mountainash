"""
Abstract base class for logic type converters.

This module defines the interface for converting expression nodes between different logic types
(e.g., boolean to ternary, ternary to boolean). Each logic type implements its own converter
that handles conversion from other logic types to its target type.
"""

from abc import ABC, abstractmethod
from typing import Any, Union
from .base_nodes import ExpressionNode, LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode


class ExpressionConverter(ABC):
    """Abstract base class for logic type converters.

    Each logic type (boolean, ternary, etc.) should implement its own converter
    that can convert expression nodes from other logic types to its target type.
    """

    @property
    @abstractmethod
    def target_logic_type(self) -> str:
        """The target logic type this converter produces.

        Returns:
            String identifier for the target logic type (e.g., "ternary", "boolean")
        """
        pass

    @abstractmethod
    def can_convert_from(self, source_logic_type: str) -> bool:
        """Check if this converter can convert from the given source logic type.

        Args:
            source_logic_type: Logic type of the source expression node

        Returns:
            True if conversion is supported, False otherwise
        """
        pass

    @abstractmethod
    def convert(self, expression_node: ExpressionNode) -> ExpressionNode:
        """Convert expression node to target logic type.

        Args:
            expression_node: Source expression node to convert

        Returns:
            Converted expression node with target logic type

        Raises:
            ValueError: If conversion is not supported for this expression type
        """
        pass

    @abstractmethod
    def convert_literal(self, literal_node: LiteralExpressionNode) -> ExpressionNode:
        """Convert literal expression node to target logic type.

        Args:
            literal_node: Literal expression node to convert

        Returns:
            Converted literal expression node
        """
        pass

    @abstractmethod
    def convert_column(self, column_node: ColumnExpressionNode) -> ExpressionNode:
        """Convert column expression node to target logic type.

        Args:
            column_node: Column expression node to convert

        Returns:
            Converted column expression node
        """
        pass

    @abstractmethod
    def convert_logical(self, logical_node: LogicalExpressionNode) -> ExpressionNode:
        """Convert logical expression node to target logic type.

        Args:
            logical_node: Logical expression node to convert

        Returns:
            Converted logical expression node
        """
        pass

    def needs_conversion(self, expression_node: ExpressionNode, visitor_logic_type: str) -> bool:
        """Check if expression node needs conversion to target logic type.

        Args:
            expression_node: Expression node to check

        Returns:
            True if conversion is needed, False otherwise
        """
        if not hasattr(expression_node, 'logic_type'):
            return False

        return expression_node.logic_type != self.target_logic_type
