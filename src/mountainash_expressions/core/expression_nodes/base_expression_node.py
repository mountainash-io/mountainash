from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict
# from ibis.expr.types import s  # Removed - not used and causes import error


if TYPE_CHECKING:
    from ..expression_visitors import SupportedExpressionVisitors
    from ...types import SupportedExpressions


class ExpressionNode(BaseModel, ABC):


    model_config = ConfigDict(
        use_enum_values=False,  # CRITICAL: Keep Enum identity, don't convert to values
        validate_assignment=True,
        arbitrary_types_allowed=True,  # For Callable if needed
    )
    # operator: Enum = Field()

    operator: Any = Field()


    @abstractmethod
    def accept(self, visitor: SupportedExpressionVisitors) -> SupportedExpressions:
        pass

    @abstractmethod
    def eval(self) -> Callable:
        pass
