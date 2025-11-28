"""
Namespaces package.

Provides namespace classes that group related operations on expressions,
and entry point functions for creating expressions.
"""

from .base import BaseNamespace

# Flat namespaces (methods accessed directly on API)
from .boolean import BooleanNamespace
from .arithmetic import ArithmeticNamespace

# Backwards compatibility aliases
BooleanComparisonNamespace = BooleanNamespace
BooleanLogicalNamespace = BooleanNamespace
from .null import NullNamespace
from .type import TypeNamespace
from .horizontal import HorizontalNamespace
from .native import NativeNamespace
from .conditional import ConditionalNamespace, WhenBuilder, WhenThenBuilder
from .ternary import TernaryNamespace

# Explicit namespaces (accessed via descriptors: .str, .dt, .name)
from .string import StringNamespace
from .datetime import DateTimeNamespace
from .name import NameNamespace

# Entry point functions
from .entrypoints import (
    col, lit, coalesce, greatest, least, when, native,
    t_col, always_true, always_false, always_unknown,
)

__all__ = [
    # Base
    "BaseNamespace",
    # Flat namespaces
    "BooleanNamespace",
    "BooleanComparisonNamespace",  # Backwards compatibility alias
    "BooleanLogicalNamespace",  # Backwards compatibility alias
    "ArithmeticNamespace",
    "NullNamespace",
    "TypeNamespace",
    "HorizontalNamespace",
    "NativeNamespace",
    "ConditionalNamespace",
    "TernaryNamespace",
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
    "native",
    # Ternary entry points
    "t_col",
    "always_true",
    "always_false",
    "always_unknown",
]
