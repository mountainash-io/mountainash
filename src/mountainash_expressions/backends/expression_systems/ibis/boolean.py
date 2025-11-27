"""Ibis boolean operations implementation."""

from typing import Any, List, Optional
import ibis

from .base import IbisBaseExpressionSystem
from ....core.protocols import BooleanExpressionProtocol


class IbisBooleanExpressionSystem(IbisBaseExpressionSystem, BooleanExpressionProtocol):
    """Ibis implementation of boolean operations."""

    # Comparison
    def eq(self, left: Any, right: Any) -> Any:
        return left == right

    def ne(self, left: Any, right: Any) -> Any:
        return left != right

    def gt(self, left: Any, right: Any) -> Any:
        return left > right

    def lt(self, left: Any, right: Any) -> Any:
        return left < right

    def ge(self, left: Any, right: Any) -> Any:
        return left >= right

    def le(self, left: Any, right: Any) -> Any:
        return left <= right

    def is_close(self, left: Any, right: Any, precision: Optional[float] = None) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        if precision is None:
            precision = 1e-5
        return (left - right).abs() <= ibis.literal(precision)

    def between(self, value: Any, lower: Any, upper: Any, closed: Optional[str] = "both") -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return value.between(lower, upper, closed=closed)

    # Logical
    def and_(self, left: Any, right: Any) -> Any:
        return left & right

    def or_(self, left: Any, right: Any) -> Any:
        return left | right

    def xor_(self, left: Any, right: Any) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Ibis may not support XOR directly - implementing as (a | b) & ~(a & b).
        """
        return (left | right) & ~(left & right)

    def xor_parity(self, left: Any, right: Any) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return (left | right) & ~(left & right)

    def not_(self, operand: Any) -> Any:
        return ~operand

    def is_true(self, operand: Any) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return operand == ibis.literal(True)

    def is_false(self, operand: Any) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return operand == ibis.literal(False)

    # Collection
    def is_in(self, element: Any, collection: List[Any]) -> Any:
        return element.isin(collection)

    def is_not_in(self, element: Any, collection: List[Any]) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return ~element.isin(collection)

    # Constants
    def always_true(self) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return ibis.literal(True)

    def always_false(self) -> Any:
        """
        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return ibis.literal(False)
