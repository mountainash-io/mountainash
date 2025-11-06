from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional

from ...constants import CONST_EXPRESSION_STRING_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode, StringExpressionNode
from ...expression_parameters import ExpressionParameter


class StringOperatorsExpressionVisitor(ExpressionVisitor):
    """
    Mixin for handling string operations.

    This mixin provides the visitor methods for string expressions
    like UPPER, LOWER, TRIM, SUBSTRING, CONCAT, etc.

    String operations are universal (no logic prefix) as they work the
    same way regardless of Boolean/Ternary logic system.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN

    # ===============
    # Operations Maps
    # ===============

    @property
    def string_ops(self) -> Dict[str, Callable]:
        """Map string operators to their implementation methods."""
        return {
            CONST_EXPRESSION_STRING_OPERATORS.UPPER:        self._str_upper,
            CONST_EXPRESSION_STRING_OPERATORS.LOWER:        self._str_lower,
            CONST_EXPRESSION_STRING_OPERATORS.TRIM:         self._str_trim,
            CONST_EXPRESSION_STRING_OPERATORS.LTRIM:        self._str_ltrim,
            CONST_EXPRESSION_STRING_OPERATORS.RTRIM:        self._str_rtrim,
            CONST_EXPRESSION_STRING_OPERATORS.SUBSTRING:    self._str_substring,
            CONST_EXPRESSION_STRING_OPERATORS.CONCAT:       self._str_concat,
            CONST_EXPRESSION_STRING_OPERATORS.LENGTH:       self._str_length,
            CONST_EXPRESSION_STRING_OPERATORS.REPLACE:      self._str_replace,
            CONST_EXPRESSION_STRING_OPERATORS.CONTAINS:     self._str_contains,
            CONST_EXPRESSION_STRING_OPERATORS.STARTS_WITH:  self._str_starts_with,
            CONST_EXPRESSION_STRING_OPERATORS.ENDS_WITH:    self._str_ends_with,
        }

    # ===============
    # Expression Visitor Methods
    # ===============

    def visit_string_expression(self, expression_node: StringExpressionNode) -> Any:
        """
        Visit a string expression node.

        Args:
            expression_node: The string expression to visit

        Returns:
            Backend-specific string expression
        """
        if expression_node.operator not in self.string_ops:
            raise ValueError(f"Unsupported string operator: {expression_node.operator}")

        # Resolve the operand (the string to operate on)
        operand_parameter = ExpressionParameter(expression_node.operand)
        operand_resolved = operand_parameter.resolve_to_expression_node()

        # Resolve any additional arguments
        args_resolved = []
        if expression_node.args:
            for arg in expression_node.args:
                arg_param = ExpressionParameter(arg)
                args_resolved.append(arg_param.resolve_to_expression_node())

        return self._process_string_expression(
            expression_node,
            operand_resolved,
            args_resolved,
            expression_node.kwargs
        )

    def _process_string_expression(
        self,
        expression_node: StringExpressionNode,
        operand: ExpressionNode,
        args: List[Any],
        kwargs: Dict[str, Any]
    ) -> Any:
        """
        Process a string expression with resolved operands.

        Args:
            expression_node: The string expression
            operand: Resolved operand (the string to operate on)
            args: Resolved additional arguments
            kwargs: Additional keyword arguments

        Returns:
            Backend-specific string expression
        """
        if expression_node.operator not in self.string_ops:
            raise ValueError(f"Unsupported string operator: {expression_node.operator}")

        op_func = self.string_ops[expression_node.operator]
        return op_func(operand, *args, **kwargs)

    # ===============
    # String Operations (Abstract Methods)
    # ===============

    # Case conversion
    @abstractmethod
    def _str_upper(self, operand: ExpressionNode) -> Any:
        """Convert string to uppercase"""
        pass

    @abstractmethod
    def _str_lower(self, operand: ExpressionNode) -> Any:
        """Convert string to lowercase"""
        pass

    # Whitespace trimming
    @abstractmethod
    def _str_trim(self, operand: ExpressionNode) -> Any:
        """Trim whitespace from both sides"""
        pass

    @abstractmethod
    def _str_ltrim(self, operand: ExpressionNode) -> Any:
        """Trim whitespace from left side"""
        pass

    @abstractmethod
    def _str_rtrim(self, operand: ExpressionNode) -> Any:
        """Trim whitespace from right side"""
        pass

    # String manipulation
    @abstractmethod
    def _str_substring(self, operand: ExpressionNode, start: Any, length: Optional[Any] = None, **kwargs) -> Any:
        """Extract substring: operand[start:start+length]"""
        pass

    @abstractmethod
    def _str_concat(self, operand: ExpressionNode, *others: Any, **kwargs) -> Any:
        """Concatenate strings"""
        pass

    @abstractmethod
    def _str_length(self, operand: ExpressionNode) -> Any:
        """Get string length"""
        pass

    @abstractmethod
    def _str_replace(self, operand: ExpressionNode, old: Any, new: Any, **kwargs) -> Any:
        """Replace substring: operand.replace(old, new)"""
        pass

    # String checks (return boolean)
    @abstractmethod
    def _str_contains(self, operand: ExpressionNode, substring: Any, **kwargs) -> Any:
        """Check if string contains substring"""
        pass

    @abstractmethod
    def _str_starts_with(self, operand: ExpressionNode, prefix: Any, **kwargs) -> Any:
        """Check if string starts with prefix"""
        pass

    @abstractmethod
    def _str_ends_with(self, operand: ExpressionNode, suffix: Any, **kwargs) -> Any:
        """Check if string ends with suffix"""
        pass
