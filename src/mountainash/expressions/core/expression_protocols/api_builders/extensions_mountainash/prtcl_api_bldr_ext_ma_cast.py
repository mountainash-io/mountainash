"""Public contract for Mountainash checked casts."""
from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, TYPE_CHECKING

from mountainash.core.dtypes import CanonicalDtype

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class CaseFailureBehaviour(str, Enum):
    THROW = "throw"
    NULL = "null"


class NumericRounding(str, Enum):
    TIE_TO_EVEN = "TIE_TO_EVEN"
    TIE_AWAY_FROM_ZERO = "TIE_AWAY_FROM_ZERO"


class MountainAshCastAPIBuilderProtocol(Protocol):
    """Checked numeric casts and ordinary backend casts through one facade."""

    def cast(
        self,
        dtype: CanonicalDtype | Any,
        failure_behavior: CaseFailureBehaviour | str = "throw",
        *,
        rounding: NumericRounding | str = "TIE_TO_EVEN",
    ) -> BaseExpressionAPI:
        """Cast to a dtype; decimal and lexical targets use checked numeric semantics."""
        ...
