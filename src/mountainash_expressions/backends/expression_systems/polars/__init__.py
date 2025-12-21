"""Polars backend expression system.

This module composes all Polars protocol implementations into a single
PolarsExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.core.expression_system.expsys_base import register_expression_system

# Foundation protocols
from .field_reference import PolarsFieldReferenceSystem
from .literal import PolarsLiteralSystem
from .cast import PolarsCastSystem
from .conditional import PolarsConditionalSystem

# Scalar protocols
from .scalar_comparison import PolarsScalarComparisonSystem
from .scalar_boolean import PolarsScalarBooleanSystem
from .scalar_arithmetic import PolarsScalarArithmeticSystem
from .scalar_string import PolarsScalarStringSystem
from .scalar_datetime import PolarsScalarDatetimeSystem
from .scalar_rounding import PolarsScalarRoundingSystem
from .scalar_logarithmic import PolarsScalarLogarithmicSystem
from .scalar_set import PolarsScalarSetSystem
from .scalar_aggregate import PolarsScalarAggregateSystem


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
]
