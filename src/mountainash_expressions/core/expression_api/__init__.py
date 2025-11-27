"""
Expression API package.

Provides the fluent API facades for building expressions.
"""

from .descriptor import NamespaceDescriptor
from .base import BaseExpressionAPI
from .boolean import BooleanExpressionAPI

__all__ = [
    "NamespaceDescriptor",
    "BaseExpressionAPI",
    "BooleanExpressionAPI",
]
