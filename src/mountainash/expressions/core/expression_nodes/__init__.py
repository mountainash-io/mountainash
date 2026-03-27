"""Substrait-aligned expression nodes.

This module provides the 6 core node types that align with Substrait's
expression model:

1. LiteralNode - Constant values
2. FieldReferenceNode - Column references
3. ScalarFunctionNode - Function calls (most operations)
4. IfThenNode - Conditional expressions (when/then/otherwise)
5. CastNode - Type conversions
6. SingularOrListNode - Membership tests (IN operator)

These nodes replace the previous categorical node system (40+ classes)
with a minimal set that maps directly to Substrait's expression types.

Function identifiers are defined as ENUMs in the function_keys.enums module
for compile-time safety and IDE autocomplete.
"""

from .substrait.exn_base import ExpressionNode
from .substrait.exn_literal import LiteralNode
from .substrait.exn_field_reference import FieldReferenceNode
from .substrait.exn_scalar_function import ScalarFunctionNode
from .substrait.exn_ifthen import IfThenNode
from .substrait.exn_cast import CastNode
from .substrait.exn_singular_or_list import SingularOrListNode

# Extension URIs (kept here for backwards compatibility)
from .enums import SubstraitExtension

# Function keys are now in expression_system.function_keys.enums
# Import from the canonical location:
#   from mountainash.expressions.core.expression_system.function_keys.enums import (
#       KEY_SCALAR_COMPARISON,
#       KEY_SCALAR_BOOLEAN,
#       # etc.
#   )


__all__ = [
    # Base class
    "ExpressionNode",
    # Node types
    "CastNode",
    "FieldReferenceNode",
    "IfThenNode",
    "LiteralNode",
    "ScalarFunctionNode",
    "SingularOrListNode",
    # Extension URIs
    "SubstraitExtension",
]
