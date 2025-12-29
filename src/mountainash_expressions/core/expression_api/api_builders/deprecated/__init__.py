"""
DEPRECATED: Namespaces package.

This package is deprecated. Use the core namespace implementations instead:
    from mountainash_expressions.core.expression_api.api_namespaces.core import (
        ScalarBooleanNamespace,
        ScalarComparisonNamespace,
        ScalarArithmeticNamespace,
        # etc.
    )

The new namespaces follow Substrait naming conventions and use the KEY_SCALAR_*
enum system from function_keys.enums.
"""

import warnings

warnings.warn(
    "mountainash_expressions.core.expression_api.api_namespaces.deprecated is deprecated. "
    "Use api_namespaces.core instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .base import BaseNamespace

# Flat namespaces (methods accessed directly on API)
from .boolean import BooleanNamespace
from .arithmetic import ArithmeticNamespace

# Backwards compatibility aliases
BooleanComparisonNamespace = BooleanNamespace
BooleanLogicalNamespace = BooleanNamespace
from .null import NullNamespace
from .horizontal import HorizontalNamespace
from .native import NativeNamespace
from .conditional import ConditionalNamespace, WhenBuilder, WhenThenBuilder
from .ternary import TernaryNamespace

# Explicit namespaces (accessed via descriptors: .str, .dt, .name)
from .string import StringNamespace
from .datetime import DateTimeNamespace
from .name import NameNamespace

from .cast import CastNamespace


# Entry point functions


__all__ = [
    # Base
    "BaseNamespace",

    "CastNamespace",


    # Flat namespaces
    "BooleanNamespace",
    "BooleanComparisonNamespace",  # Backwards compatibility alias
    "BooleanLogicalNamespace",  # Backwards compatibility alias
    "ArithmeticNamespace",
    "NullNamespace",
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
