"""Narwhals type operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import TypeExpressionProtocol


class NarwhalsTypeExpressionSystem(NarwhalsBaseExpressionSystem, TypeExpressionProtocol):
    """Narwhals implementation of type operations."""

    def cast(self, value: Any, dtype: Any, **kwargs) -> nw.Expr:
        """Cast value to specified type using Narwhals cast() method."""
        return value.cast(dtype, **kwargs)
