"""Substrait extension URIs.

DEPRECATED: Function key ENUMs have been moved to:
    mountainash.expressions.core.expression_system.function_keys.enums

This module now only contains Substrait extension URI constants for serialization.

For function keys, use:
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_COMPARISON,
        FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
        # etc.
    )
"""

from __future__ import annotations

import warnings

# Emit deprecation warning when this module is imported
warnings.warn(
    "mountainash.expressions.core.expression_nodes.enums.substrait is deprecated. "
    "Function keys have moved to mountainash.expressions.core.expression_system.function_keys.enums. "
    "Only SubstraitExtension URIs remain in this module.",
    DeprecationWarning,
    stacklevel=2,
)


# =============================================================================
# Substrait Extension URIs (kept for serialization)
# =============================================================================

class SubstraitExtension:
    """Substrait extension URIs for serialization.

    These URIs identify Substrait extension YAML files that define function signatures.
    Used when serializing/deserializing expression trees to Substrait format.
    """

    COMPARISON = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_comparison.yaml"
    BOOLEAN = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml"
    ARITHMETIC = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_arithmetic.yaml"
    STRING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_string.yaml"
    DATETIME = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_datetime.yaml"
    ROUNDING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_rounding.yaml"
    LOGARITHMIC = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_logarithmic.yaml"
    SET = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_set.yaml"
    AGGREGATE = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_aggregate_generic.yaml"

    # Custom Mountainash extensions
    MOUNTAINASH = "https://mountainash.dev/extensions/functions_custom.yaml"


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "SubstraitExtension",
]
