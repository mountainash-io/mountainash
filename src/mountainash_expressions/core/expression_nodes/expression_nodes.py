from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional, final, TYPE_CHECKING, Collection

# from ibis.expr.types import s  # Removed - not used and causes import error

from ..constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..visitor.expression_visitor import ExpressionVisitor




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
        return CONST_EXPRESSION_NODE_TYPES.NATIVE_BACKEND

    def __init__(self, operator: str, native_expr: Any):
        self.native_expr = native_expr


class SourceExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.SOURCE

    def __init__(self, operator: str, value: Any):
        self.value = value


class LiteralExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LITERAL

    def __init__(self, operator: str, value: Any):
        self.operator = operator
        self.value = value


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
        return CONST_EXPRESSION_NODE_TYPES.UNARY

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
        return CONST_EXPRESSION_NODE_TYPES.COMPARISON



class ArithmeticExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.ARITHMETIC


    def __init__(self, operator: str, left: Any, right: Any):
        self.operator = operator
        self.left = left
        self.right = right


class ConditionalIfElseExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.CONDITIONAL_IF_ELSE

    def __init__(self, operator: str, condition: Any, consequence: Any, alternative: Any ):

        self.operator = operator

        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative

class CollectionExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.COLLECTION


    def __init__(self, operator: str, element: Any, container: Any ):
        self.operator = operator
        self.operands = element
        self.operands = container

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


# class TemporalExpressionNode(ExpressionNode):

#     @property
#     @final
#     def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
#         return CONST_EXPRESSION_NODE_TYPES.CONDITIONAL


#     def __init__(self, operator: str, condition, ):
#         self.operator = operator
#         self.operands = operands

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
