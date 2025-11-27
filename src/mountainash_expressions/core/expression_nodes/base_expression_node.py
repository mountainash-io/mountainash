from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict


if TYPE_CHECKING:
    from ..expression_visitors import SupportedExpressionVisitors
    from ...types import SupportedExpressions


class ExpressionNode(BaseModel, ABC):


    model_config = ConfigDict(
        use_enum_values=False,  # CRITICAL: Keep Enum identity, don't convert to values
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    operator: Any = Field()


    @abstractmethod
    def accept(self, visitor: SupportedExpressionVisitors) -> SupportedExpressions:
        pass

    @abstractmethod
    def eval(self, dataframe: Any) -> SupportedExpressions:
        """Evaluate this node against a DataFrame.

        Args:
            dataframe: DataFrame to detect backend from (pl.DataFrame, nw.DataFrame, ir.Table, etc.)

        Returns:
            Backend-native expression (pl.Expr | nw.Expr | ir.Expr)
        """
        pass
