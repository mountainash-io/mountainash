"""Disposable numeric-conversion protocol for item 241."""
from typing import Protocol, TypeVar

from mountainash.core.dtypes.spike_numeric import NumericDtype

ExpressionT = TypeVar("ExpressionT")


class SpikeNumericProtocol(Protocol[ExpressionT]):
    def numeric_cast(self, x: ExpressionT, /, dtype: NumericDtype, rounding: str = "TIE_TO_EVEN", failure_behavior: str = "throw", preserve: bool = False) -> ExpressionT:
        ...
