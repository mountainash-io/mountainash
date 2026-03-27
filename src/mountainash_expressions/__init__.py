"""Backwards-compatibility shim for mountainash_expressions.

This package has been renamed to `mountainash`.
Please update your imports:
    import mountainash as ma  # NEW
    import mountainash_expressions as ma  # DEPRECATED
"""
import warnings

warnings.warn(
    "mountainash_expressions is deprecated. "
    "Use 'import mountainash as ma' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the new location
from mountainash import *  # noqa: F401,F403
from mountainash import __version__  # noqa: F401

# Re-export submodules so deep imports work
# e.g., from mountainash_expressions.core.expression_nodes import ScalarFunctionNode
import mountainash.expressions.core as core  # noqa: F401
import mountainash.expressions.backends as backends  # noqa: F401
