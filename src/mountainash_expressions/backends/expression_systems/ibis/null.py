"""Ibis null operations implementation."""

from typing import Any
import ibis

from .base import IbisBaseExpressionSystem
from ....core.protocols import NullExpressionProtocol


class IbisNullExpressionSystem(IbisBaseExpressionSystem, NullExpressionProtocol):
    """Ibis implementation of null operations."""

    def is_null(self, operand: Any) -> Any:
        """Check if operand is NULL using Ibis isnull() method."""
        return operand.isnull()

    def fill_null(self, operand: Any, value: Any) -> Any:
        """Fill null values with specified value."""
        return operand.fill_null(value)

    def null_if(self, operand: Any, condition: Any) -> Any:
        """Return NULL if condition is true, otherwise return operand."""
        return ibis.ifelse(condition, ibis.null(), operand)

    def always_null(self) -> Any:
        """Return a NULL literal expression."""
        return ibis.null()

    def not_null(self, operand: Any) -> Any:
        """Check if operand is NOT NULL using Ibis notnull() method."""
        return operand.notnull()
