"""Ibis type operations implementation."""

from typing import Any
from .base import IbisBaseExpressionSystem
from ....core.protocols import TypeExpressionProtocol


class IbisTypeExpressionSystem(IbisBaseExpressionSystem, TypeExpressionProtocol):
    """Ibis implementation of type operations."""

    def cast(self, value: Any, dtype: Any, **kwargs) -> Any:
        """Cast value to specified type using Ibis cast() method."""
        return value.cast(dtype, **kwargs)
