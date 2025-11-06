from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional, final, TYPE_CHECKING, Collection

# from ibis.expr.types import s  # Removed - not used and causes import error

from ..constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..expression_visitors.expression_visitor import ExpressionVisitor


class ExpressionNode(ABC):


    @property
    @abstractmethod
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        pass

    @property
    @abstractmethod
    def logic_type(self) -> CONST_LOGIC_TYPES:
        pass


    @abstractmethod
    def accept(self, visitor: "ExpressionVisitor") -> Callable:
        pass

    @abstractmethod
    def eval(self) -> Callable:
        pass


class NativeBackendExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.NATIVE

    def __init__(self, operator: str, native_expr: Any):
        self.operator = operator
        self.native_expr = native_expr


class SourceExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.SOURCE

    def __init__(self, operator: str, value: Any):
        self.operator = operator
        self.value = value


class LiteralExpressionNode(ExpressionNode):
    """
    Literal value expression node.

    Represents a constant literal value (string, number, boolean, etc.).
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LITERAL

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """Literals work with any logic system."""
        return CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: str, value: Any):
        self.operator = operator
        self.value = value

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_literal_expression(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_literal_expression(self)
        return eval_expr


class CastExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.CAST

    def __init__(self, operator: str, value: Any, type: Any, **kwargs):
        self.operator = operator
        self.value = value
        self.type = type
        self.kwargs = kwargs



class LogicalConstantExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LOGICAL_CONSTANT

    def __init__(self, operator: str):
        self.operator = operator

class UnaryExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LOGICAL_UNARY

    def __init__(self, operator: str, operand: Any):
        self.operator = operator
        self.operand = operand


class LogicalExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LOGICAL


    def __init__(self, operator: str, operands: Any):
        self.operator = operator
        self.operands = operands


class ComparisonExpressionNode(ExpressionNode):

    def __init__(self, operator: str, left: Any, right: Any, **kwargs):

        self.operator = operator
        self.left = left
        self.right = right
        self.kwargs = kwargs


    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LOGICAL_COMPARISON

class CollectionExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.COLLECTION


    def __init__(self, operator: str, element: Any, container: Any ):
        self.operator = operator
        self.element = element
        self.container = container

class ArithmeticExpressionNode(ExpressionNode):
    """
    Node representing arithmetic operations (ADD, SUBTRACT, MULTIPLY, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.ARITHMETIC

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """
        Arithmetic operations can work with any logic system.
        Defaults to BOOLEAN but can be overridden.
        """
        return CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: str, left: Any, right: Any):
        self.operator = operator
        self.left = left
        self.right = right

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_arithmetic_expression(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_arithmetic_expression(self)
        return eval_expr


class StringExpressionNode(ExpressionNode):
    """
    Node representing string operations (UPPER, LOWER, TRIM, SUBSTRING, etc.).

    String operations return string values (or integers for LENGTH) and are universal
    across all logic systems.

    Supports both:
    - Unary operations: UPPER, LOWER, TRIM, LENGTH (just operand)
    - Operations with arguments: SUBSTRING(start, end), REPLACE(old, new), CONCAT(*args)
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.STRING

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """
        String operations can work with any logic system.
        Defaults to BOOLEAN but can be overridden.
        """
        return CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: str, operand: Any, *args, **kwargs):
        """
        Initialize string expression node.

        Args:
            operator: String operator (from CONST_EXPRESSION_STRING_OPERATORS)
            operand: The string expression to operate on
            *args: Additional positional arguments (e.g., start, end for substring)
            **kwargs: Additional keyword arguments
        """
        self.operator = operator
        self.operand = operand
        self.args = args
        self.kwargs = kwargs

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_string_expression(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_string_expression(self)
        return eval_expr


class ConditionalIfElseExpressionNode(ExpressionNode):
    """
    Conditional if-then-else operations are universal across logic systems.

    Includes WHEN-THEN-OTHERWISE, COALESCE, and FILL_NULL operations.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.CONDITIONAL_IF_ELSE

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """
        Conditional operations can work with any logic system.
        Defaults to BOOLEAN but can be overridden.
        """
        return CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: str, condition: Any = None, consequence: Any = None, alternative: Any = None, values: list = None):
        """
        Initialize conditional expression node.

        Args:
            operator: Conditional operator (from CONST_EXPRESSION_CONDITIONAL_OPERATORS)
            condition: Condition to evaluate (for WHEN)
            consequence: Value if condition is true (for WHEN)
            alternative: Value if condition is false (for WHEN)
            values: List of values (for COALESCE)
        """
        self.operator = operator
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative
        self.values = values or []

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_conditional_expression(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_conditional_expression(self)
        return eval_expr


class PatternExpressionNode(ExpressionNode):
    """
    Pattern matching operations return boolean values and are universal across logic systems.

    Pattern operations include SQL LIKE, regex matching, and regex replacement.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.PATTERN

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """
        Pattern operations can work with any logic system.
        Defaults to BOOLEAN but can be overridden.
        """
        return CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: str, operand: Any, pattern: Any, *args, **kwargs):
        """
        Initialize pattern expression node.

        Args:
            operator: Pattern operator (from CONST_EXPRESSION_PATTERN_OPERATORS)
            operand: The string expression to match against
            pattern: The pattern to use (string or regex)
            *args: Additional positional arguments (e.g., replacement for regex_replace)
            **kwargs: Additional keyword arguments
        """
        self.operator = operator
        self.operand = operand
        self.pattern = pattern
        self.args = args
        self.kwargs = kwargs

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_pattern_expression(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_pattern_expression(self)
        return eval_expr


# class PatternExpressionNode(ExpressionNode):

#     @property
#     @final
#     def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
#         return CONST_EXPRESSION_NODE_TYPES.PATTERN


#     def __init__(self, operator: str, string:Any, pattern:Any):

#         self.operator = operator

#         self.string = string
#         self.pattern = pattern

# class StringConcatExpressionNode(ExpressionNode):

#     @property
#     @final
#     def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
#         return CONST_EXPRESSION_NODE_TYPES.STRING_CONCAT


#     def __init__(self, operator: str, strings:Any ):
#         self.operator = operator
#         self.strings = strings

# class StringSubstringExpressionNode(ExpressionNode):

#     @property
#     @final
#     def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
#         return CONST_EXPRESSION_NODE_TYPES.STRING_SUBSTRING


#     def __init__(self, operator: str, string: Any, start:Any, length:Any ):

#         self.operator = operator
#         self.string = string
#         self.start = start
#         self.length = length


class TemporalExpressionNode(ExpressionNode):
    """
    Node representing temporal/datetime operations (YEAR, MONTH, DAY, HOUR, etc.).

    Temporal operations extract date/time components or perform date arithmetic.
    They are universal across all logic systems.

    Supports both:
    - Extraction operations: YEAR, MONTH, DAY, HOUR, MINUTE, SECOND (just operand)
    - Arithmetic operations: ADD_DAYS(days), ADD_MONTHS(months), DIFF_DAYS(other_date)
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.TEMPORAL

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """
        Temporal operations can work with any logic system.
        Defaults to BOOLEAN but can be overridden.
        """
        return CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: str, operand: Any, *args, **kwargs):
        """
        Initialize temporal expression node.

        Args:
            operator: Temporal operator (from CONST_EXPRESSION_TEMPORAL_OPERATORS)
            operand: The datetime expression to operate on
            *args: Additional positional arguments (e.g., days for ADD_DAYS, other date for DIFF_DAYS)
            **kwargs: Additional keyword arguments
        """
        self.operator = operator
        self.operand = operand
        self.args = args
        self.kwargs = kwargs

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_temporal_expression(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_temporal_expression(self)
        return eval_expr

# class SpatialExpressionNode(ExpressionNode):

#     @property
#     @final
#     def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
#         return CONST_EXPRESSION_NODE_TYPES.CONDITIONAL


#     def __init__(self, operator: str, condition, ):
#         self.operator = operator
#         self.operands = operands

# class BitwiseExpressionNode(ExpressionNode):

#     @property
#     @final
#     def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
#         return CONST_EXPRESSION_NODE_TYPES.CONDITIONAL


#     def __init__(self, operator: str, condition, ):
#         self.operator = operator
#         self.operands = operands
