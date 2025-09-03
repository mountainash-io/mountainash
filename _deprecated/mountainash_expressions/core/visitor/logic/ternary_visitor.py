# file: src/mountainash_dataframes/utils/expressions/ternary/base.py



from abc import abstractmethod
from typing import Any, List, Callable, Dict, TYPE_CHECKING
from functools import reduce

from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_LOGIC_TYPES, CONST_TERNARY_LOGIC_VALUES
from ..expression_visitor import ExpressionVisitor

if TYPE_CHECKING:
    from ...logic import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode
else:
    from ...logic import ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode

class TernaryExpressionVisitor(ExpressionVisitor):


    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.TERNARY


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
    # Logic Type Conversion
    # ===============

    def __init__(
        # self, logic_converter: Optional[TernaryLogicTypeConverter] = None
        ):
        """Initialize ternary visitor with logic type converter.

        Args: None
        """
        # self.logic_converter = logic_converter or TernaryLogicTypeConverter()
        pass



    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:
        """Convert literal expression to ternary expression.

        Args:
            expression: Literal expression to process

        Returns:
            Callable that returns expression with ternary results
        """

        if not issubclass(type(expression_node), (LiteralExpressionNode)):
            raise TypeError("Expected a LiteralExpressionNode instance")

        # # Check if conversion needed
        # if TernaryExpressionConverter.needs_conversion(expression_node,  self.logic_type):
        #     expression_node = TernaryExpressionConverter.convert(expression_node,  self.logic_type)

        if expression_node.operator not in self.comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.comparison_ops[expression_node.operator]

        #boolean original
        if expression_node.operator == CONST_EXPRESSION_LOGIC_OPERATORS.IN:

            return lambda table: op_func(self._format_literal(expression_node.value1, table), self._format_list(expression_node.value2))
        elif expression_node.operator in (CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL):
                return lambda table: op_func(self._format_literal(expression_node.value1, table))
        else:
            return lambda table: op_func(self._format_literal(expression_node.value1, table), self._format_literal(expression_node.value2, table))


    def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:

        if not issubclass(type(expression_node), (ColumnExpressionNode)):
            raise TypeError("Expected a ColumnExpressionNode instance")

        # # Check if conversion needed
        # if self.logic_converter.needs_conversion(expression_node):
        #     expression_node = self.convert_to_ternary(expression_node)

        if expression_node.operator not in self.comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.comparison_ops[expression_node.operator]

        if expression_node.compare_column is not None:
            return lambda table: op_func(self._format_column(expression_node.column, table), self._format_column(expression_node.compare_column, table))
        else:
            if expression_node.operator == CONST_EXPRESSION_LOGIC_OPERATORS.IN:
                return lambda table: op_func(self._format_column(expression_node.column, table), self._format_list(expression_node.value))
            elif expression_node.operator in (CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL):
                    return lambda table: op_func(self._format_column(expression_node.column, table))
            else:
                return lambda table: op_func(self._format_column(expression_node.column, table), self._format_literal(expression_node.value, table))



    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:

        if not issubclass(type(expression_node), (LogicalExpressionNode)):
            raise TypeError("Expected a LogicalExpressionNode instance")

        # # Check if conversion needed
        # if self.logic_converter.needs_conversion(expression_node):
        #     expression_node = self.convert_to_ternary(expression_node)

        if expression_node.operator not in self.logical_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.logical_ops[expression_node.operator]

        if expression_node.operator in  (CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE,
                                         CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE,
                                         CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_UNKNOWN
        ):
            return lambda table: op_func()(table)
        else:
            return lambda table: op_func(expression_node)(table)

    # ===============
    # Operations Maps
    # ===============

    def _comparison_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        _comparison_ops = {
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

        return _comparison_ops

    def _logical_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        _logical_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE:   self._always_true,
            CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE:  self._always_false,
            CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_UNKNOWN:self._always_unknown,

            CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE:       self._is_true,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_FALSE:      self._is_false,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_UNKNOWN:    self._is_unknown,

            CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_TRUE:    self._maybe_true,
            CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_FALSE:   self._maybe_false,
            CONST_EXPRESSION_LOGIC_OPERATORS.IS_KNOWN:      self._is_known,


            CONST_EXPRESSION_LOGIC_OPERATORS.NOT:           self._negate,
            CONST_EXPRESSION_LOGIC_OPERATORS.AND:           self._and,
            CONST_EXPRESSION_LOGIC_OPERATORS.OR:            self._or,
            CONST_EXPRESSION_LOGIC_OPERATORS.XOR_EXCLUSIVE: self._xor,
        }

        return _logical_ops

    @property
    def comparison_ops(self) -> Dict[str, Callable]:
        """Dynamic property to get boolean comparison operations with current mode."""
        return self._comparison_ops()


    @property
    def logical_ops(self) -> Dict[str, Callable]:
        """Dynamic property to get boolean logical operations with current filter mode."""
        return self._logical_ops()

    # ===============
    # Concrete Universal Helper Methods
    # ===============

    def _combine(self, table: Any, expression_nodes: List["ExpressionNode"], combine_func):
        """ Combine multiple expressions using a specified function."""

        if not expression_nodes:
            raise ValueError("Cannot perform operations on empty expression_nodes list")

        expressions = [expression_node.accept(self)(table)
                        for expression_node in expression_nodes]

        # Handle single expression_node case
        if len(expressions) == 1:
            return expressions[0]

        return reduce(combine_func, expressions)

    # ===============
    # Concrete Universal Visitor Operations
    # ===============

    # Constant Operations
    def _always_true(self) -> Callable:
        """Always true expression."""
        return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, table)

    def _always_false(self) -> Callable:
        """Always false expression."""
        return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE, table)

    def _always_unknown(self) -> Callable:
        """Always false expression."""
        return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


    # ===============
    # Logical Operations
    # ===============

    @abstractmethod
    def _is_true(self, expression_node: LogicalExpressionNode) -> Callable:
        """Abstract method to return is true expression."""
        pass

    @abstractmethod
    def _is_false(self, expression_node: LogicalExpressionNode) -> Callable:
        """Abstract method to return is false expression."""
        pass

    @abstractmethod
    def _is_unknown(self, expression_node: LogicalExpressionNode) -> Callable:
        """Abstract method to return is unknown expression."""
        pass

    @abstractmethod
    def _maybe_true(self, expression_node: LogicalExpressionNode) -> Callable:
        """Abstract method to return is true or unknown expression."""
        pass

    @abstractmethod
    def _maybe_false(self, expression_node: LogicalExpressionNode) -> Callable:
        """Abstract method to return is false or unknown expression."""
        pass

    @abstractmethod
    def _is_known(self, expression_node: LogicalExpressionNode) -> Callable:
        """Abstract method to return is known expression."""
        pass




    @abstractmethod
    def _and(self, expression_node: LogicalExpressionNode) -> Callable:
        pass

    @abstractmethod
    def _or(self, expression_node: LogicalExpressionNode) -> Callable:
        pass


    @abstractmethod
    def _negate(self, expression_node: LogicalExpressionNode ) -> Callable:
        pass



    @abstractmethod
    def _xor(self, expression_node: LogicalExpressionNode) -> Callable:
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
