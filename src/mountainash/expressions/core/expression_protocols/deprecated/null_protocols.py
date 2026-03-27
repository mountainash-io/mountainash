
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union
from typing import Protocol
from enum import Enum, auto


if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode, NullExpressionNode, NullConstantExpressionNode, NullConditionalExpressionNode, NullLogicalExpressionNode,SupportedNullExpressionNodeTypes
    from ...types import SupportedExpressions
    from ..namespaces import BaseNamespace


class ENUM_NULL_OPERATORS(Enum):
    """
    Enumeration for pattern matching operators.

    Attributes:
        - COALESCE: Return first non-null value from list
        - FILL_NULL: Replace null values with specified value
        - NULL_IF: Return null if condition met
    """
    FILL_NULL = auto()
    NULL_IF = auto()

    ALWAYS_NULL = auto()

    IS_NULL = auto()
    NOT_NULL = auto()



class NullVisitorProtocol(Protocol):

    def visit_expression_node(self, node: SupportedNullExpressionNodeTypes) -> Any: ...

    def fill_null(self, node: NullExpressionNode) -> SupportedExpressions: ...
    def null_if(self, node: NullConditionalExpressionNode) -> SupportedExpressions: ...

    def always_null(self, node: NullConstantExpressionNode) -> SupportedExpressions: ...

    def is_null(self, node: NullLogicalExpressionNode) -> Any: ...
    def not_null(self, node: NullLogicalExpressionNode) -> Any: ...


class NullExpressionProtocol(Protocol):

    def fill_null(self, operand: SupportedExpressions, value: SupportedExpressions) -> SupportedExpressions: ...
    def null_if(self, operand: SupportedExpressions, condition: SupportedExpressions) -> SupportedExpressions: ...

    def always_null(self) -> SupportedExpressions: ...

    def is_null(self, operand: SupportedExpressions) -> SupportedExpressions: ...
    def not_null(self, operand: SupportedExpressions) -> SupportedExpressions: ...


class NullBuilderProtocol(Protocol):

    def fill_null(self, value: Union[BaseNamespace,ExpressionNode, Any]) -> BaseNamespace: ...
    def null_if(self, condition: Union[BaseNamespace,ExpressionNode, Any]) -> BaseNamespace: ...

    def always_null(self) -> BaseNamespace: ...

    def is_null(self) -> BaseNamespace: ...
    def not_null(self) -> BaseNamespace: ...
