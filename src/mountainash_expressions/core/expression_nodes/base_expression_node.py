from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional, final, TYPE_CHECKING, Collection
from enum import Enum

# from ibis.expr.types import s  # Removed - not used and causes import error

from ...constants import CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..expression_visitors.expression_visitor import ExpressionVisitor
    from ...types import SupportedExpressions


class ExpressionNode(ABC):

    #TODO: Should I make expression nodes pydantic classes??

    # @property
    # @abstractmethod
    # def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
    #     pass

    @property
    @abstractmethod
    def logic_type(self) -> CONST_LOGIC_TYPES:
        pass


    @abstractmethod
    def accept(self, visitor: ExpressionVisitor) -> SupportedExpressions:
        pass

    @abstractmethod
    def eval(self) -> Callable:
        pass


    @property
    def operator(self) -> Enum:
        return self._operator

    @operator.setter
    def operator(self, operator: Enum):
        self._operator = operator
