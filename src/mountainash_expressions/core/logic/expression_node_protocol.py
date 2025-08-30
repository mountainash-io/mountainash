from typing import  Protocol

from ..constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES


class ExpressionNodeProtocol(Protocol):
    """Protocol for expression nodes"""
    @property
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES: ...

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES: ...
