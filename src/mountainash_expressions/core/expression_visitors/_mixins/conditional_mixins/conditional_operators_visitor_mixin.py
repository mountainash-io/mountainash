from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional

from ...constants import CONST_EXPRESSION_CONDITIONAL_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode, ConditionalIfElseExpressionNode
from ...expression_parameters import ExpressionParameter


class ConditionalOperatorsExpressionVisitor(ExpressionVisitor):
    """
    Mixin for handling conditional operations.

    This mixin provides the visitor methods for conditional expressions
    like WHEN-THEN-OTHERWISE, COALESCE, and FILL_NULL.

    Conditional operations are universal (no logic prefix) as they work the
    same way regardless of Boolean/Ternary logic system.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN

    # ===============
    # Operations Maps
    # ===============

    @property
    def conditional_ops(self) -> Dict[str, Callable]:
        """Map conditional operators to their implementation methods."""
        return {
            CONST_EXPRESSION_CONDITIONAL_OPERATORS.WHEN:        self._conditional_when,
            CONST_EXPRESSION_CONDITIONAL_OPERATORS.COALESCE:    self._conditional_coalesce,
            CONST_EXPRESSION_CONDITIONAL_OPERATORS.FILL_NULL:   self._conditional_fill_null,
        }

    # ===============
    # Expression Visitor Methods
    # ===============

    def visit_conditional_expression(self, expression_node: ConditionalIfElseExpressionNode) -> Any:
        """
        Visit a conditional expression node.

        Args:
            expression_node: The conditional expression to visit

        Returns:
            Backend-specific conditional expression
        """
        if expression_node.operator not in self.conditional_ops:
            raise ValueError(f"Unsupported conditional operator: {expression_node.operator}")

        # Different operations need different resolution
        if expression_node.operator == CONST_EXPRESSION_CONDITIONAL_OPERATORS.WHEN:
            # WHEN needs: condition, consequence, alternative
            condition_param = ExpressionParameter(expression_node.condition)
            condition_resolved = condition_param.resolve_to_expression_node()

            consequence_param = ExpressionParameter(expression_node.consequence)
            consequence_resolved = consequence_param.resolve_to_expression_node()

            alternative_param = ExpressionParameter(expression_node.alternative)
            alternative_resolved = alternative_param.resolve_to_expression_node()

            return self._process_when_expression(
                condition_resolved,
                consequence_resolved,
                alternative_resolved
            )

        elif expression_node.operator == CONST_EXPRESSION_CONDITIONAL_OPERATORS.COALESCE:
            # COALESCE needs: list of values
            values_resolved = []
            for value in expression_node.values:
                value_param = ExpressionParameter(value)
                values_resolved.append(value_param.resolve_to_expression_node())

            return self._process_coalesce_expression(values_resolved)

        elif expression_node.operator == CONST_EXPRESSION_CONDITIONAL_OPERATORS.FILL_NULL:
            # FILL_NULL needs: operand, fill_value
            operand_param = ExpressionParameter(expression_node.condition)  # Using condition for operand
            operand_resolved = operand_param.resolve_to_expression_node()

            fill_value_param = ExpressionParameter(expression_node.consequence)  # Using consequence for fill_value
            fill_value_resolved = fill_value_param.resolve_to_expression_node()

            return self._process_fill_null_expression(operand_resolved, fill_value_resolved)

    def _process_when_expression(
        self,
        condition: ExpressionNode,
        consequence: ExpressionNode,
        alternative: ExpressionNode
    ) -> Any:
        """
        Process a WHEN-THEN-OTHERWISE expression.

        Args:
            condition: Condition to evaluate
            consequence: Value if condition is true
            alternative: Value if condition is false

        Returns:
            Backend-specific conditional expression
        """
        return self._conditional_when(condition, consequence, alternative)

    def _process_coalesce_expression(self, values: List[ExpressionNode]) -> Any:
        """
        Process a COALESCE expression.

        Args:
            values: List of values to check for non-null

        Returns:
            Backend-specific coalesce expression
        """
        return self._conditional_coalesce(values)

    def _process_fill_null_expression(self, operand: ExpressionNode, fill_value: ExpressionNode) -> Any:
        """
        Process a FILL_NULL expression.

        Args:
            operand: Expression that may contain nulls
            fill_value: Value to use for nulls

        Returns:
            Backend-specific fill_null expression
        """
        return self._conditional_fill_null(operand, fill_value)

    # ===============
    # Abstract Methods (to be implemented by concrete visitors)
    # ===============

    @abstractmethod
    def _conditional_when(
        self,
        condition: ExpressionNode,
        consequence: ExpressionNode,
        alternative: ExpressionNode
    ) -> Any:
        """
        Conditional if-then-else expression.

        Args:
            condition: Boolean condition to evaluate
            consequence: Value to return if condition is true
            alternative: Value to return if condition is false

        Returns:
            Backend-specific conditional expression
        """
        pass

    @abstractmethod
    def _conditional_coalesce(self, values: List[ExpressionNode]) -> Any:
        """
        Return first non-null value from a list.

        Args:
            values: List of values to check

        Returns:
            First non-null value
        """
        pass

    @abstractmethod
    def _conditional_fill_null(self, operand: ExpressionNode, fill_value: ExpressionNode) -> Any:
        """
        Replace null values with specified value.

        Args:
            operand: Expression that may contain nulls
            fill_value: Value to use for nulls

        Returns:
            Expression with nulls replaced
        """
        pass
