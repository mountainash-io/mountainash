"""Polars backend expression system.

This module composes all Polars protocol implementations into a single
PolarsExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.core.expression_system.expsys_base import register_expression_system

# Foundation protocols
from .substrait.field_reference import PolarsFieldReferenceSystem
from .substrait.literal import PolarsLiteralSystem
from .substrait.cast import PolarsCastSystem
from .substrait.conditional import PolarsConditionalSystem

# Scalar protocols
from substrait.scalar_comparison import PolarsScalarComparisonSystem
from substrait.scalar_boolean import PolarsScalarBooleanSystem
from substrait.scalar_arithmetic import PolarsScalarArithmeticSystem
from substrait.scalar_string import PolarsScalarStringSystem
from substrait.scalar_datetime import PolarsScalarDatetimeSystem
from substrait.scalar_rounding import PolarsScalarRoundingSystem
from substrait.scalar_logarithmic import PolarsScalarLogarithmicSystem
from substrait.scalar_set import PolarsScalarSetSystem
from substrait.scalar_aggregate import PolarsScalarAggregateSystem

# Mountainash extension protocols
from .mountainash_extensions.ext_ternary import PolarsTernarySystem
from .mountainash_extensions.ext_null import PolarsNullExtensionSystem
from .mountainash_extensions.ext_name import PolarsNameExtensionSystem


@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
class PolarsExpressionSystem(
    # Foundation protocols
    PolarsFieldReferenceSystem,
    PolarsLiteralSystem,
    PolarsCastSystem,
    PolarsConditionalSystem,
    # Scalar protocols
    PolarsScalarComparisonSystem,
    PolarsScalarBooleanSystem,
    PolarsScalarArithmeticSystem,
    PolarsScalarStringSystem,
    PolarsScalarDatetimeSystem,
    PolarsScalarRoundingSystem,
    PolarsScalarLogarithmicSystem,
    PolarsScalarSetSystem,
    PolarsScalarAggregateSystem,
    # Mountainash extension protocols
    PolarsTernarySystem,
    PolarsNullExtensionSystem,
    PolarsNameExtensionSystem,
):
    """Complete Polars backend expression system.

    Composes all protocol implementations via multiple inheritance.
    Registered with the visitor factory for automatic backend detection.
    """

    pass


__all__ = [
    "PolarsExpressionSystem",
    # Foundation protocols
    "PolarsFieldReferenceSystem",
    "PolarsLiteralSystem",
    "PolarsCastSystem",
    "PolarsConditionalSystem",
    # Scalar protocols
    "PolarsScalarComparisonSystem",
    "PolarsScalarBooleanSystem",
    "PolarsScalarArithmeticSystem",
    "PolarsScalarStringSystem",
    "PolarsScalarDatetimeSystem",
    "PolarsScalarRoundingSystem",
    "PolarsScalarLogarithmicSystem",
    "PolarsScalarSetSystem",
    "PolarsScalarAggregateSystem",
    # Mountainash extension protocols
    "PolarsTernarySystem",
    "PolarsNullExtensionSystem",
    "PolarsNameExtensionSystem",
]
