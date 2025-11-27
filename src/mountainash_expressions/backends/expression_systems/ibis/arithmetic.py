"""Ibis arithmetic operations implementation."""

from typing import Any
from .base import IbisBaseExpressionSystem
from ....core.protocols import ArithmeticExpressionProtocol


class IbisArithmeticExpressionSystem(IbisBaseExpressionSystem, ArithmeticExpressionProtocol):
    """
    Ibis implementation of arithmetic operations.

    Note:
        ISSUE: Deprecated backend had duplicate methods (subtract/sub, multiply/mul, modulo/mod).
        This implementation uses only the full names.
    """

    def add(self, left: Any, right: Any) -> Any:
        return left + right

    def subtract(self, left: Any, right: Any) -> Any:
        return left - right

    def multiply(self, left: Any, right: Any) -> Any:
        return left * right

    def divide(self, left: Any, right: Any) -> Any:
        return left / right

    def modulo(self, left: Any, right: Any) -> Any:
        return left % right

    def power(self, left: Any, right: Any) -> Any:
        return left ** right

    def floor_divide(self, left: Any, right: Any) -> Any:
        return left // right
