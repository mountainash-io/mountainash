from abc import abstractmethod
from typing import Any, List, Callable, Dict, TYPE_CHECKING

from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, ConditionalExpressionNode, ArithmeticExpressionNode, CollectionExpressionNode, StringExpressionNode

from functools import reduce

class BooleanExpressionVisitor(ExpressionVisitor):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN



    # ===============
    # Operations Maps
    # ===============




    @property
    def boolean_logical_constant_ops(self) -> Dict[str, Callable]:
        boolean_logical_constant_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE:   self._always_true,
            CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE:  self._always_false,
        }

        return boolean_logical_constant_ops


    @property
    def boolean_unary_ops(self) -> Dict[str, Callable]:
        boolean_unary_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE:       self._is_true,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_FALSE:      self._is_false,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL:       self._is_null,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL:   self._not_null,
        }

        return boolean_unary_ops


    @property
    def boolean_logical_ops(self) -> Dict[str, Callable]:

        boolean_logical_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.NOT:           self._negate,
            CONST_EXPRESSION_LOGIC_OPERATORS.AND:           self._and,
            CONST_EXPRESSION_LOGIC_OPERATORS.OR:            self._or,
            CONST_EXPRESSION_LOGIC_OPERATORS.XOR_EXCLUSIVE: self._xor_exclusive,
            CONST_EXPRESSION_LOGIC_OPERATORS.XOR_PARITY:    self._xor_parity
        }

        return boolean_logical_ops


    @property
    def boolean_comparison_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        boolean_comparison_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.EQ:            self._eq,
            CONST_EXPRESSION_LOGIC_OPERATORS.NE:            self._ne,
            CONST_EXPRESSION_LOGIC_OPERATORS.GT:            self._gt,
            CONST_EXPRESSION_LOGIC_OPERATORS.LT:            self._lt,
            CONST_EXPRESSION_LOGIC_OPERATORS.GE:            self._ge,
            CONST_EXPRESSION_LOGIC_OPERATORS.LE:            self._le,
        }

        return boolean_comparison_ops

    @property
    def boolean_collection_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        boolean_comparison_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.IN:            self._in,
            CONST_EXPRESSION_LOGIC_OPERATORS.NOT_IN:        self._not_in,
        }

        return boolean_comparison_ops







    # @abstractmethod
    # def _col(self,  column: str, table: Any) -> Any:
    #     pass

    # @abstractmethod
    # def _lit(self, value: Any, table: Any) -> Any:
    #     pass



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

    # ===============
    # Unary Expressions
    def visit_unary_expression(self, expression_node: UnaryExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_unary_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        operand_parameter =  ExpressionParameter(expression_node.operand)
        operand_expression_node = operand_parameter.resolve_to_expression_node()

        return self._process_unary_expression(expression_node, operand_expression_node)


    def _process_unary_expression(self, expression_node: UnaryExpressionNode, operand_expression_node: ExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_unary_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_unary_ops[expression_node.operator]
        return op_func(operand_expression_node)


    # ===============
    # Logical Expressions
    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Any:

        if not issubclass(type(expression_node), (LogicalExpressionNode)):
            raise TypeError("Expected a LogicalExpressionNode instance")

        operands_resolved_expression_nodes =  [ ExpressionParameter(operand).resolve_to_expression_node() for operand in expression_node.operands ]


        return self._process_logical_expression(expression_node, operands_resolved_expression_nodes)


    def _process_logical_expression(self, expression_node: LogicalExpressionNode,  operands_expression_nodes: [ExpressionNode]) -> Any:

        if not issubclass(type(expression_node), (LogicalExpressionNode)):
            raise TypeError("Expected a LogicalExpressionNode instance")

        if expression_node.operator not in self.boolean_logical_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_logical_ops[expression_node.operator]
        return op_func(operands_expression_nodes)




    # ===============
    # Literal Comparison Expression
    def visit_comparison_expression(self, expression_node: ComparisonExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        left_expression_parameter =  ExpressionParameter(expression_node.left)
        right_expression_parameter = ExpressionParameter(expression_node.right)

        left_resolved_expr = left_expression_parameter.resolve_to_expression_node()
        right_resolved_expr = right_expression_parameter.resolve_to_expression_node()

        return self._process_boolean_comparison_expression(expression_node, left_resolved_expr, right_resolved_expr)


    def _process_comparison_expression(self, expression_node: ComparisonExpressionNode, left: ExpressionNode, right: ExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_comparison_ops[expression_node.operator]
        return op_func(left, right)



    # ===============
    # Literal Collection Expression
    def visit_collection_expression(self, expression_node: CollectionExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        element_expression_parameter =  ExpressionParameter(expression_node.element)
        container_expression_parameter = ExpressionParameter(expression_node.container)

        left_resolved_expr = element_expression_parameter.resolve_to_expression_node()
        right_resolved_expr = container_expression_parameter.resolve_to_expression_node()

        return self._process_collection_expression(expression_node, left_resolved_expr, right_resolved_expr)


    def _process_collection_expression(self, expression_node: CollectionExpressionNode, element: ExpressionNode, container: ExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_comparison_ops[expression_node.operator]
        return op_func(element, container)





    # Logical Operations
    # ===============


    # Logical Constant Operations
    def _B_always_true(self) -> Any:
        """Always true expression."""
        return self._lit(True)

    def _B_always_false(self) -> Any:
        """Always false expression."""
        return self._lit(False)


    @abstractmethod
    def _B_is_true(self, expression_node: LogicalExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_is_false(self, expression_node: LogicalExpressionNode) -> Any:
        pass


    @abstractmethod
    def _B_and(self, expression_node: LogicalExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_or(self, expression_node: LogicalExpressionNode) -> Any:
        pass


    @abstractmethod
    def _B_negate(self, expression_node: LogicalExpressionNode ) -> Any:
        """Abstract method to combine expressions using a specified function."""
        pass



    @abstractmethod
    def _B_xor_exclusive(self, expression_node: LogicalExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_xor_parity(self, expression_node: LogicalExpressionNode) -> Any:
        pass



    # Comparison Operations
    # ===============

    @abstractmethod
    def _B_eq(self, LHS: ExpressionNode, RHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_ne(self, LHS: ExpressionNode, RHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_gt(self, LHS: ExpressionNode, RHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_lt(self, LHS: ExpressionNode, RHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_ge(self, LHS: ExpressionNode, RHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_le(self, LHS: ExpressionNode, RHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_in(self, LHS: ExpressionNode, RHS: ExpressionNode) -> Any:
        pass


    # Unary Operations
    # ===============

    @abstractmethod
    def _B_is_null(self, LHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_not_null(self, LHS: ExpressionNode) -> Any:
        pass


    # ===============
    # Helper Methods
    # ===============

    def _combine(self, table: Any, expression_nodes: List["ExpressionNode"], combine_func):
        """ Combine multiple expressions using a specified function."""

        if not expression_nodes:
            raise ValueError("Cannot perform operations on empty operands list")

        expressions = [expression_node.accept(self)(table)
                        for expression_node in expression_nodes]

        # Handle single operand case
        if len(expressions) == 1:
            return expressions[0]

        return reduce(combine_func, expressions)
