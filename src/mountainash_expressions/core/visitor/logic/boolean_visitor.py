from abc import abstractmethod
from typing import Any, List, Callable, Dict, TYPE_CHECKING

from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor

if TYPE_CHECKING:
    from ...logic import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode
else:
    from ...logic import ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode

from functools import reduce

class BooleanExpressionVisitor(ExpressionVisitor):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN


    @abstractmethod
    def _format_column(self,  column: str, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_literal(self, value: Any, table: Any) -> Any:
        pass

    @abstractmethod
    def _format_list(self, value: Any) -> Any:
        pass


    # ===============
    # Expression Visitor Methods
    # ===============

    # ===============
    # Literal Comparison Expression
    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        # #Combine into one!
        # conversion_result = conversion_analysis(expression_node, self.logic_type)
        # # node_conversion_required = should_convert_node(expression_node, self.logic_type)

        # if conversion_result.convert_node == True:
        #     expression_node = convert_expression(expression_node, self.logic_type)

        # if conversion_result.convert_visitor == True:
        #     delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, expression_node.logic_type)
        #     return expression_node.accept(delegate_visitor)

        return self._process_literal_expression(expression_node)



    def _process_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_comparison_ops[expression_node.operator]

        if expression_node.operator == CONST_EXPRESSION_LOGIC_OPERATORS.IN:
            return lambda table: op_func(self._format_literal(expression_node.value1, table), self._format_list(expression_node.value2))
        elif expression_node.operator in (CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL):
                return lambda table: op_func(self._format_literal(expression_node.value1, table))
        else:
            return lambda table: op_func(self._format_literal(expression_node.value1, table), self._format_literal(expression_node.value2, table))

    # ===============
    # Column Comparison Expression

    def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:

        if not issubclass(type(expression_node), (ColumnExpressionNode)):
            raise TypeError("Expected a ColumnExpressionNode instance")

        # conversion_result = conversion_analysis(expression_node, self.logic_type)

        # if conversion_result.convert_node == True:
        #     expression_node = convert_expression(expression_node, self.logic_type)

        # if conversion_result.convert_visitor == True:
        #     delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, expression_node.logic_type)
        #     return expression_node.accept(delegate_visitor)

        return self._process_column_expression(expression_node)


    def _process_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:

        if not issubclass(type(expression_node), (ColumnExpressionNode)):
            raise TypeError("Expected a ColumnExpressionNode instance")


        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_comparison_ops[expression_node.operator]

        if expression_node.compare_column is not None:
            return lambda table: op_func(self._format_column(expression_node.column, table), self._format_column(expression_node.compare_column, table))
        else:
            if expression_node.operator == CONST_EXPRESSION_LOGIC_OPERATORS.IN:
                return lambda table: op_func(self._format_column(expression_node.column, table), self._format_list(expression_node.value))
            elif expression_node.operator in (CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL):
                return lambda table: op_func(self._format_column(expression_node.column, table))
            else:
                return lambda table: op_func(self._format_column(expression_node.column, table), self._format_literal(expression_node.value, table))

    # ===============
    # Logical Expression
    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:

        if not issubclass(type(expression_node), (LogicalExpressionNode)):
            raise TypeError("Expected a LogicalExpressionNode instance")

        # conversion_result = conversion_analysis(expression_node, self.logic_type)

        # if conversion_result.convert_node == True:
        #     expression_node = convert_expression(expression_node, self.logic_type)

        # if conversion_result.convert_visitor == True:
        #     delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, expression_node.logic_type)
        #     return expression_node.accept(delegate_visitor)

        return self._process_logical_expression(expression_node)


    def _process_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:

        if not issubclass(type(expression_node), (LogicalExpressionNode)):
            raise TypeError("Expected a LogicalExpressionNode instance")

        if expression_node.operator not in self.boolean_logical_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_logical_ops[expression_node.operator]

        if expression_node.operator in  (CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE, CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE):
            return lambda table: op_func()(table)
        else:
            return lambda table: op_func(expression_node)(table)


    # ===============
    # Operations Maps
    # ===============

    def _boolean_comparison_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        boolean_comparison_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.EQ:            self._eq,
            CONST_EXPRESSION_LOGIC_OPERATORS.NE:            self._ne,
            CONST_EXPRESSION_LOGIC_OPERATORS.GT:            self._gt,
            CONST_EXPRESSION_LOGIC_OPERATORS.LT:            self._lt,
            CONST_EXPRESSION_LOGIC_OPERATORS.GE:            self._ge,
            CONST_EXPRESSION_LOGIC_OPERATORS.LE:            self._le,
            CONST_EXPRESSION_LOGIC_OPERATORS.IN:            self._in,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL:       self._is_null,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL:   self._not_null,
        }

        return boolean_comparison_ops

    def _boolean_logical_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        boolean_logical_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE:   self._always_true,
            CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE:  self._always_false,

            CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE:       self._is_true,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_FALSE:      self._is_false,

            CONST_EXPRESSION_LOGIC_OPERATORS.NOT:           self._negate,
            CONST_EXPRESSION_LOGIC_OPERATORS.AND:           self._and,
            CONST_EXPRESSION_LOGIC_OPERATORS.OR:            self._or,
            CONST_EXPRESSION_LOGIC_OPERATORS.XOR_EXCLUSIVE: self._xor_exclusive,
            CONST_EXPRESSION_LOGIC_OPERATORS.XOR_PARITY:    self._xor_parity
        }

        return boolean_logical_ops


    @property
    def boolean_comparison_ops(self) -> Dict[str, Callable]:
        """Dynamic property to get boolean comparison operations with current mode."""
        return self._boolean_comparison_ops()

    @property
    def boolean_logical_ops(self) -> Dict[str, Callable]:
        """Dynamic property to get boolean logical operations with current filter mode."""
        return self._boolean_logical_ops()



    # Logical Operations
    # ===============


    # Constant Operations
    def _always_true(self) -> Callable:
        """Always true expression."""
        return lambda table: self._format_literal(True, table)

    def _always_false(self) -> Callable:
        """Always false expression."""
        return lambda table: self._format_literal(False, table)

    # @abstractmethod
    # def _always_true(self) -> Callable:
    #     """Abstract method to return an always true expression."""
    #     pass

    # @abstractmethod
    # def _always_false(self) -> Callable:
    #     """Abstract method to return always false expression."""
    #     pass

    @abstractmethod
    def _is_true(self, expression_node: LogicalExpressionNode) -> Callable:
        pass

    @abstractmethod
    def _is_false(self, expression_node: LogicalExpressionNode) -> Callable:
        pass


    @abstractmethod
    def _and(self, expression_node: LogicalExpressionNode) -> Callable:
        pass

    @abstractmethod
    def _or(self, expression_node: LogicalExpressionNode) -> Callable:
        pass


    @abstractmethod
    def _negate(self, expression_node: LogicalExpressionNode ) -> Callable:
        """Abstract method to combine expressions using a specified function."""
        pass



    @abstractmethod
    def _xor_exclusive(self, expression_node: LogicalExpressionNode) -> Callable:
        pass

    @abstractmethod
    def _xor_parity(self, expression_node: LogicalExpressionNode) -> Callable:
        pass



    # Comparison Operations
    # ===============

    @abstractmethod
    def _eq(self, LHS: Any, RHS: Any) -> Any:
        pass

    @abstractmethod
    def _ne(self, LHS: Any, RHS: Any) -> Any:
        pass

    @abstractmethod
    def _gt(self, LHS: Any, RHS: Any) -> Any:
        pass

    @abstractmethod
    def _lt(self, LHS: Any, RHS: Any) -> Any:
        pass

    @abstractmethod
    def _ge(self, LHS: Any, RHS: Any) -> Any:
        pass

    @abstractmethod
    def _le(self, LHS: Any, RHS: Any) -> Any:
        pass

    @abstractmethod
    def _in(self, LHS: Any, RHS: Any) -> Any:
        pass


    # Unary Operations
    # ===============

    @abstractmethod
    def _is_null(self, LHS: Any) -> Any:
        pass

    @abstractmethod
    def _not_null(self, LHS: Any) -> Any:
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
