from __future__ import annotations
from typing import Any, Callable, Dict

from ...constants import CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor

class BooleanConstantExpressionVisitor(ExpressionVisitor):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN



    # ===============
    # Operations Maps
    # ===============




    @property
    def boolean_logical_constant_ops(self) -> Dict[str, Callable]:
        boolean_logical_constant_ops = {
            CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS.ALWAYS_TRUE:   self._B_always_true,
            CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS.ALWAYS_FALSE:  self._B_always_false,
        }

        return boolean_logical_constant_ops


    # ===============
    # Expression Visitor Methods
    # ===============


    # ===============
    # Logical Constant Expressions
    def visit_logical_constant_expression(self, expression_node: LogicalConstantExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_logical_constant_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        return self._process_boolean_logical_constant_expression(expression_node)


    def _process_logical_constant_expression(self, expression_node: LogicalConstantExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_logical_constant_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_logical_constant_ops[expression_node.operator]
        return op_func()



    # Logical Operations
    # ===============


    # Logical Constant Operations
    def _B_always_true(self) -> Any:
        """Always true expression."""
        return self._lit(True)

    def _B_always_false(self) -> Any:
        """Always false expression."""
        return self._lit(False)
