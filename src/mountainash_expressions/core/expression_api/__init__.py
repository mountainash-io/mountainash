"""
Expression API package.

Provides the fluent API facades for building expressions.
"""

from .descriptor import NamespaceDescriptor
from .api_base import BaseExpressionAPI
from .boolean import BooleanExpressionAPI

from .entrypoints import (
    col, lit, coalesce, greatest, least, when, native,
    t_col, always_true, always_false, always_unknown,
)


__all__ = [
    "NamespaceDescriptor",
    "BaseExpressionAPI",
    "BooleanExpressionAPI",
]
