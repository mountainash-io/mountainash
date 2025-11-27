"""
Namespaces package.

Provides namespace classes that group related operations on expressions,
and entry point functions for creating expressions.
"""

from .base import BaseNamespace

# Flat namespaces (methods accessed directly on API)
from .comparison.boolean import BooleanComparisonNamespace
from .logical.boolean import BooleanLogicalNamespace
from .arithmetic import ArithmeticNamespace
from .null import NullNamespace
from .type import TypeNamespace
from .iterable import IterableNamespace
from .native import NativeNamespace
from .conditional import ConditionalNamespace, WhenBuilder, WhenThenBuilder

# Explicit namespaces (accessed via descriptors: .str, .dt, .name)
from .string import StringNamespace
from .datetime import DateTimeNamespace
from .name import NameNamespace

# Entry point functions
from .entrypoints import col, lit, coalesce, greatest, least, when

__all__ = [
    # Base
    "BaseNamespace",
    # Flat namespaces
    "BooleanComparisonNamespace",
    "BooleanLogicalNamespace",
    "ArithmeticNamespace",
    "NullNamespace",
    "TypeNamespace",
    "IterableNamespace",
    "NativeNamespace",
    "ConditionalNamespace",
    # Explicit namespaces
    "StringNamespace",
    "DateTimeNamespace",
    "NameNamespace",
    # Conditional builders
    "WhenBuilder",
    "WhenThenBuilder",
    # Entry point functions
    "col",
    "lit",
    "coalesce",
    "greatest",
    "least",
    "when",
]
