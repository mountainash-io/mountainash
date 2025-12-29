"""Substrait extension URIs.

DEPRECATED: Function key enums have been moved to:
    mountainash_expressions.core.expression_system.function_keys.enums

This package now only exports SubstraitExtension URIs.

For function keys, import from the canonical location:
    from mountainash_expressions.core.expression_system.function_keys.enums import (
        KEY_SCALAR_COMPARISON,
        KEY_SCALAR_BOOLEAN,
        KEY_SCALAR_ARITHMETIC,
        MOUNTAINASH_TERNARY,
        # etc.
    )
"""

from .substrait import SubstraitExtension

__all__ = [
    "SubstraitExtension",
]
