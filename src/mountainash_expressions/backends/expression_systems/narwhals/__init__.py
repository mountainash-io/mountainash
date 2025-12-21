"""Narwhals backend expression system.

This module composes all Narwhals protocol implementations into a single
NarwhalsExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.core.expression_system.expsys_base import register_expression_system

# Foundation protocols
from .field_reference import NarwhalsFieldReferenceSystem
from .literal import NarwhalsLiteralSystem
from .cast import NarwhalsCastSystem
from .conditional import NarwhalsConditionalSystem

# Scalar protocols
from .scalar_comparison import NarwhalsScalarComparisonSystem
from .scalar_boolean import NarwhalsScalarBooleanSystem
from .scalar_arithmetic import NarwhalsScalarArithmeticSystem
from .scalar_string import NarwhalsScalarStringSystem
from .scalar_datetime import NarwhalsScalarDatetimeSystem
from .scalar_rounding import NarwhalsScalarRoundingSystem
from .scalar_logarithmic import NarwhalsScalarLogarithmicSystem
from .scalar_set import NarwhalsScalarSetSystem
from .scalar_aggregate import NarwhalsScalarAggregateSystem


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
]
