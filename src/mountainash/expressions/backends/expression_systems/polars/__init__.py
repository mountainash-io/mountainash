"""Polars backend expression system.

This module composes all Polars protocol implementations into a single
PolarsExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.core.expression_system.expsys_base import register_expression_system


from .substrait.expsys_pl_cast import SubstraitPolarsCastExpressionSystem
from .substrait.expsys_pl_conditional import SubstraitPolarsConditionalExpressionSystem
from .substrait.expsys_pl_field_reference import SubstraitPolarsFieldReferenceExpressionSystem
from .substrait.expsys_pl_literal import SubstraitPolarsLiteralExpressionSystem

from .substrait.expsys_pl_aggregate_arithmetic import SubstraitPolarsAggregateArithmeticExpressionSystem
from .substrait.expsys_pl_aggregate_boolean import SubstraitPolarsAggregateBooleanExpressionSystem
from .substrait.expsys_pl_aggregate_generic import SubstraitPolarsAggregateGenericExpressionSystem
from .substrait.expsys_pl_aggregate_string import SubstraitPolarsAggregateStringExpressionSystem


from .substrait.expsys_pl_scalar_arithmetic import SubstraitPolarsScalarArithmeticExpressionSystem
from .substrait.expsys_pl_scalar_boolean import SubstraitPolarsScalarBooleanExpressionSystem
from .substrait.expsys_pl_scalar_comparison import SubstraitPolarsScalarComparisonExpressionSystem
from .substrait.expsys_pl_scalar_datetime import SubstraitPolarsScalarDatetimeExpressionSystem
from .substrait.expsys_pl_scalar_logarithmic import SubstraitPolarsScalarLogarithmicExpressionSystem
from .substrait.expsys_pl_scalar_rounding import SubstraitPolarsScalarRoundingExpressionSystem
from .substrait.expsys_pl_scalar_set import SubstraitPolarsScalarSetExpressionSystem
from .substrait.expsys_pl_scalar_string import SubstraitPolarsScalarStringExpressionSystem

# Window protocols
from .substrait.expsys_pl_window_arithmetic import SubstraitPolarsWindowArithmeticExpressionSystem

# Geometry protocols
from .substrait.expsys_pl_scalar_geometry import SubstraitPolarsScalarGeometryExpressionSystem

# Polars Mountainash Extensions
from .extensions_mountainash.expsys_pl_ext_ma_name import MountainAshPolarsNameExpressionSystem
from .extensions_mountainash.expsys_pl_ext_ma_null import MountainAshPolarsNullExpressionSystem
from .extensions_mountainash.expsys_pl_ext_ma_scalar_arithmetic import MountainAshPolarsScalarArithmeticExpressionSystem
from .extensions_mountainash.expsys_pl_ext_ma_scalar_datetime import MountainAshPolarsScalarDatetimeExpressionSystem
from .extensions_mountainash.expsys_pl_ext_ma_scalar_set import SubstraitPolarsScalarSetExpressionSystem as MountainAshPolarsScalarSetExpressionSystem
from .extensions_mountainash.expsys_pl_ext_ma_scalar_boolean import SubstraitPolarsScalarBooleanExpressionSystem as MountainAshPolarsScalarBooleanExpressionSystem
from .extensions_mountainash.expsys_pl_ext_ma_scalar_ternary import MountainAshPolarsScalarTernaryExpressionSystem




@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
class PolarsExpressionSystem(
    # Foundation protocols
    SubstraitPolarsCastExpressionSystem,
    SubstraitPolarsConditionalExpressionSystem,
    SubstraitPolarsFieldReferenceExpressionSystem,
    SubstraitPolarsLiteralExpressionSystem,
    # Scalar protocols
    SubstraitPolarsAggregateArithmeticExpressionSystem,
    SubstraitPolarsAggregateBooleanExpressionSystem,
    SubstraitPolarsAggregateGenericExpressionSystem,
    SubstraitPolarsAggregateStringExpressionSystem,
    SubstraitPolarsScalarArithmeticExpressionSystem,
    SubstraitPolarsScalarBooleanExpressionSystem,
    SubstraitPolarsScalarComparisonExpressionSystem,
    SubstraitPolarsScalarDatetimeExpressionSystem,
    SubstraitPolarsScalarLogarithmicExpressionSystem,
    SubstraitPolarsScalarRoundingExpressionSystem,
    SubstraitPolarsScalarSetExpressionSystem,
    SubstraitPolarsScalarStringExpressionSystem,
    # Window protocols
    SubstraitPolarsWindowArithmeticExpressionSystem,
    # Geometry protocols
    SubstraitPolarsScalarGeometryExpressionSystem,
    # Mountainash extension protocols
    MountainAshPolarsNameExpressionSystem,
    MountainAshPolarsNullExpressionSystem,
    MountainAshPolarsScalarArithmeticExpressionSystem,
    MountainAshPolarsScalarDatetimeExpressionSystem,
    MountainAshPolarsScalarBooleanExpressionSystem,
    MountainAshPolarsScalarSetExpressionSystem,
    MountainAshPolarsScalarTernaryExpressionSystem,

):
    """Complete Polars backend expression system.

    Composes all protocol implementations via multiple inheritance.
    Registered with the visitor factory for automatic backend detection.
    """

    pass


__all__ = [
    "PolarsExpressionSystem",
    # Foundation protocols
    "SubstraitPolarsCastExpressionSystem",
    "SubstraitPolarsConditionalExpressionSystem",
    "SubstraitPolarsFieldReferenceExpressionSystem",
    "SubstraitPolarsLiteralExpressionSystem",
    # Scalar protocols
    "SubstraitPolarsAggregateArithmeticExpressionSystem",
    "SubstraitPolarsAggregateBooleanExpressionSystem",
    "SubstraitPolarsAggregateGenericExpressionSystem",
    "SubstraitPolarsAggregateStringExpressionSystem",
    "SubstraitPolarsScalarArithmeticExpressionSystem",
    "SubstraitPolarsScalarBooleanExpressionSystem",
    "SubstraitPolarsScalarComparisonExpressionSystem",
    "SubstraitPolarsScalarDatetimeExpressionSystem",
    "SubstraitPolarsScalarLogarithmicExpressionSystem",
    "SubstraitPolarsScalarRoundingExpressionSystem",
    "SubstraitPolarsScalarSetExpressionSystem",
    "SubstraitPolarsScalarStringExpressionSystem",
    # Window protocols
    "SubstraitPolarsWindowArithmeticExpressionSystem",
    # Geometry protocols
    "SubstraitPolarsScalarGeometryExpressionSystem",
    # Mountainash extension protocols
    "MountainAshPolarsNameExpressionSystem",
    "MountainAshPolarsNullExpressionSystem",
    "MountainAshPolarsScalarArithmeticExpressionSystem",
    "MountainAshPolarsScalarDatetimeExpressionSystem",
    "MountainAshPolarsScalarTernaryExpressionSystem"
]
