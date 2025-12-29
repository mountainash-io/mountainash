"""Narwhals backend expression system.

This module composes all Narwhals protocol implementations into a single
NarwhalsExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.core.expression_system.expsys_base import register_expression_system

# Foundation protocols
from .substrait.field_reference import NarwhalsFieldReferenceSystem
from .substrait.literal import NarwhalsLiteralSystem
from .substrait.cast import NarwhalsCastSystem
from .substrait.conditional import NarwhalsConditionalSystem

# Scalar protocols
from .substrait.scalar_comparison import NarwhalsScalarComparisonSystem
from .substrait.scalar_boolean import NarwhalsScalarBooleanSystem
from .substrait.scalar_arithmetic import NarwhalsScalarArithmeticSystem
from .substrait.scalar_string import NarwhalsScalarStringSystem
from .substrait.scalar_datetime import NarwhalsScalarDatetimeSystem
from .substrait.scalar_rounding import NarwhalsScalarRoundingSystem
from .substrait.scalar_logarithmic import NarwhalsScalarLogarithmicSystem
from .substrait.scalar_set import NarwhalsScalarSetSystem
from .substrait.scalar_aggregate import NarwhalsScalarAggregateSystem

# Mountainash extension protocols
from .mountainash_extensions.ext_ternary import NarwhalsTernarySystem
from .mountainash_extensions.ext_null import NarwhalsNullExtensionSystem
from .mountainash_extensions.ext_name import NarwhalsNameExtensionSystem


@register_expression_system(CONST_VISITOR_BACKENDS.NARWHALS)
class NarwhalsExpressionSystem(
    # Foundation protocols
    NarwhalsFieldReferenceSystem,
    NarwhalsLiteralSystem,
    NarwhalsCastSystem,
    NarwhalsConditionalSystem,
    # Scalar protocols
    NarwhalsScalarComparisonSystem,
    NarwhalsScalarBooleanSystem,
    NarwhalsScalarArithmeticSystem,
    NarwhalsScalarStringSystem,
    NarwhalsScalarDatetimeSystem,
    NarwhalsScalarRoundingSystem,
    NarwhalsScalarLogarithmicSystem,
    NarwhalsScalarSetSystem,
    NarwhalsScalarAggregateSystem,
    # Mountainash extension protocols
    NarwhalsTernarySystem,
    NarwhalsNullExtensionSystem,
    NarwhalsNameExtensionSystem,
):
    """Complete Narwhals backend expression system.

    Composes all protocol implementations via multiple inheritance.
    Registered with the visitor factory for automatic backend detection.

    Note: Narwhals is a compatibility layer that works across multiple
    DataFrame backends (Polars, Pandas, etc.). Some operations may have
    limited functionality compared to native Polars implementations.
    """

    pass


__all__ = [
    "NarwhalsExpressionSystem",
    # Foundation protocols
    "NarwhalsFieldReferenceSystem",
    "NarwhalsLiteralSystem",
    "NarwhalsCastSystem",
    "NarwhalsConditionalSystem",
    # Scalar protocols
    "NarwhalsScalarComparisonSystem",
    "NarwhalsScalarBooleanSystem",
    "NarwhalsScalarArithmeticSystem",
    "NarwhalsScalarStringSystem",
    "NarwhalsScalarDatetimeSystem",
    "NarwhalsScalarRoundingSystem",
    "NarwhalsScalarLogarithmicSystem",
    "NarwhalsScalarSetSystem",
    "NarwhalsScalarAggregateSystem",
    # Mountainash extension protocols
    "NarwhalsTernarySystem",
    "NarwhalsNullExtensionSystem",
    "NarwhalsNameExtensionSystem",
]
