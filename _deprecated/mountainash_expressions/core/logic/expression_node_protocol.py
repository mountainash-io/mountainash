from typing import  Protocol, Callable, TYPE_CHECKING

from ..constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..visitor.expression_visitor_protocol import ExpressionVisitorProtocol


class ExpressionNodeProtocol(Protocol):
    """Protocol for expression nodes"""
    @property
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES: ...

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES: ...

    def accept(self, visitor: "ExpressionVisitorProtocol") -> Callable: ...

    def eval(self) -> Callable: ...
