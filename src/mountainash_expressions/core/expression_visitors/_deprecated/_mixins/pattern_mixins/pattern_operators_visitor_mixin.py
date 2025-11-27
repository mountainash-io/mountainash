from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Dict, List

from ...constants import CONST_EXPRESSION_PATTERN_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode, PatternExpressionNode
from ...expression_parameters import ExpressionParameter


class PatternOperatorsExpressionVisitor(ExpressionVisitor):
    """
    Mixin for handling pattern matching operations.

    This mixin provides the visitor methods for pattern expressions
    like LIKE, REGEX_MATCH, REGEX_CONTAINS, and REGEX_REPLACE.

    Pattern operations are universal (no logic prefix) as they work the
    same way regardless of Boolean/Ternary logic system.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN

    # ===============
    # Operations Maps
    # ===============

    @property
    def pattern_ops(self) -> Dict[str, Callable]:
        """Map pattern operators to their implementation methods."""
        return {
            CONST_EXPRESSION_PATTERN_OPERATORS.LIKE:            self._pattern_like,
            CONST_EXPRESSION_PATTERN_OPERATORS.REGEX_MATCH:     self._pattern_regex_match,
            CONST_EXPRESSION_PATTERN_OPERATORS.REGEX_CONTAINS:  self._pattern_regex_contains,
            CONST_EXPRESSION_PATTERN_OPERATORS.REGEX_REPLACE:   self._pattern_regex_replace,
        }

    # ===============
    # Expression Visitor Methods
    # ===============

    def visit_pattern_expression(self, expression_node: PatternExpressionNode) -> Any:
        """
        Visit a pattern expression node.

        Args:
            expression_node: The pattern expression to visit

        Returns:
            Backend-specific pattern expression
        """
        if expression_node.operator not in self.pattern_ops:
            raise ValueError(f"Unsupported pattern operator: {expression_node.operator}")

        # Resolve the operand (the string to match against)
        operand_parameter = ExpressionParameter(expression_node.operand)
        operand_resolved = operand_parameter.resolve_to_expression_node()

        # Resolve the pattern
        pattern_parameter = ExpressionParameter(expression_node.pattern)
        pattern_resolved = pattern_parameter.resolve_to_expression_node()

        # Resolve any additional arguments (e.g., replacement string for regex_replace)
        args_resolved = []
        if expression_node.args:
            for arg in expression_node.args:
                arg_param = ExpressionParameter(arg)
                args_resolved.append(arg_param.resolve_to_expression_node())

        return self._process_pattern_expression(
            expression_node,
            operand_resolved,
            pattern_resolved,
            args_resolved,
            expression_node.kwargs
        )

    def _process_pattern_expression(
        self,
        expression_node: PatternExpressionNode,
        operand_resolved: ExpressionNode,
        pattern_resolved: ExpressionNode,
        args_resolved: List[ExpressionNode],
        kwargs: Dict[str, Any]
    ) -> Any:
        """
        Process a pattern expression by calling the appropriate method.

        Args:
            expression_node: The original pattern expression node
            operand_resolved: Resolved operand node
            pattern_resolved: Resolved pattern node
            args_resolved: Resolved additional arguments
            kwargs: Additional keyword arguments

        Returns:
            Backend-specific pattern expression
        """
        op_method = self.pattern_ops[expression_node.operator]

        # Call the appropriate method with resolved arguments
        if expression_node.operator == CONST_EXPRESSION_PATTERN_OPERATORS.REGEX_REPLACE:
            # regex_replace needs: operand, pattern, replacement
            if not args_resolved:
                raise ValueError("regex_replace requires a replacement argument")
            return op_method(operand_resolved, pattern_resolved, args_resolved[0], **kwargs)
        else:
            # like, regex_match, regex_contains: operand, pattern
            return op_method(operand_resolved, pattern_resolved, **kwargs)

    # ===============
    # Abstract Methods (to be implemented by concrete visitors)
    # ===============

    @abstractmethod
    def _pattern_like(self, operand: ExpressionNode, pattern: ExpressionNode, **kwargs) -> Any:
        """
        SQL LIKE pattern matching.

        Args:
            operand: String expression to match
            pattern: Pattern with % (any chars) and _ (single char) wildcards

        Returns:
            Boolean expression indicating if operand matches pattern
        """
        pass

    @abstractmethod
    def _pattern_regex_match(self, operand: ExpressionNode, pattern: ExpressionNode, **kwargs) -> Any:
        """
        Check if string fully matches regex pattern.

        Args:
            operand: String expression to match
            pattern: Regular expression pattern

        Returns:
            Boolean expression indicating if operand matches pattern
        """
        pass

    @abstractmethod
    def _pattern_regex_contains(self, operand: ExpressionNode, pattern: ExpressionNode, **kwargs) -> Any:
        """
        Check if string contains regex pattern.

        Args:
            operand: String expression to search
            pattern: Regular expression pattern

        Returns:
            Boolean expression indicating if operand contains pattern
        """
        pass

    @abstractmethod
    def _pattern_regex_replace(
        self,
        operand: ExpressionNode,
        pattern: ExpressionNode,
        replacement: ExpressionNode,
        **kwargs
    ) -> Any:
        """
        Replace text matching regex pattern.

        Args:
            operand: String expression to modify
            pattern: Regular expression pattern
            replacement: Replacement string

        Returns:
            String expression with replacements applied
        """
        pass
