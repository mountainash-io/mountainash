"""Substrait extension URIs.

DEPRECATED: Function key enums have been moved to:
    mountainash.expressions.core.expression_system.function_keys.enums

This package now only exports SubstraitExtension URIs.

For function keys, import from the canonical location:
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
        FKEY_MOUNTAINASH_SCALAR_TERNARY,
        # etc.
    )
"""

from .substrait import SubstraitExtension

__all__ = [
    "SubstraitExtension",
]
