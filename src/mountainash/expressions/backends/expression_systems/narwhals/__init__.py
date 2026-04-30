"""Narwhals backend expression system.

This module composes all Narwhals protocol implementations into a single
NarwhalsExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.core.expression_system.expsys_base import register_expression_system


from .substrait.expsys_nw_cast import SubstraitNarwhalsCastExpressionSystem
from .substrait.expsys_nw_conditional import SubstraitNarwhalsConditionalExpressionSystem
from .substrait.expsys_nw_field_reference import SubstraitNarwhalsFieldReferenceExpressionSystem
from .substrait.expsys_nw_literal import SubstraitNarwhalsLiteralExpressionSystem

from .substrait.expsys_nw_aggregate_arithmetic import SubstraitNarwhalsAggregateArithmeticExpressionSystem
from .substrait.expsys_nw_aggregate_boolean import    SubstraitNarwhalsAggregateBooleanExpressionSystem
from .substrait.expsys_nw_aggregate_generic import    SubstraitNarwhalsAggregateGenericExpressionSystem
from .substrait.expsys_nw_aggregate_string import     SubstraitNarwhalsAggregateStringExpressionSystem


from .substrait.expsys_nw_scalar_arithmetic import SubstraitNarwhalsScalarArithmeticExpressionSystem
from .substrait.expsys_nw_scalar_boolean import SubstraitNarwhalsScalarBooleanExpressionSystem
from .substrait.expsys_nw_scalar_comparison import SubstraitNarwhalsScalarComparisonExpressionSystem
from .substrait.expsys_nw_scalar_datetime import SubstraitNarwhalsScalarDatetimeExpressionSystem
from .substrait.expsys_nw_scalar_logarithmic import SubstraitNarwhalsScalarLogarithmicExpressionSystem
from .substrait.expsys_nw_scalar_rounding import SubstraitNarwhalsScalarRoundingExpressionSystem
from .substrait.expsys_nw_scalar_set import SubstraitNarwhalsScalarSetExpressionSystem
from .substrait.expsys_nw_scalar_string import SubstraitNarwhalsScalarStringExpressionSystem

# Window protocols
from .substrait.expsys_nw_window_arithmetic import SubstraitNarwhalsWindowArithmeticExpressionSystem

# Geometry protocols
from .substrait.expsys_nw_scalar_geometry import SubstraitNarwhalsScalarGeometryExpressionSystem

# Narwhals Mountainash Extensions
from .extensions_mountainash.expsys_nw_ext_ma_name import MountainAshNarwhalsNameExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_null import MountainAshNarwhalsNullExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_arithmetic import MountainAshNarwhalsScalarArithmeticExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_datetime import MountainAshNarwhalsScalarDatetimeExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_set import SubstraitNarwhalsScalarSetExpressionSystem as MountainAshNarwhalsScalarSetExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_boolean import MountainAshNarwhalsScalarBooleanExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_string import SubstraitNarwhalsScalarStringExpressionSystem as MountainAshNarwhalsScalarStringExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_ternary import MountainAshNarwhalsScalarTernaryExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_window import MountainAshNarwhalsWindowExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_struct import MountainAshNarwhalsScalarStructExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_list import MountainAshNarwhalsScalarListExpressionSystem
from .extensions_mountainash.expsys_nw_ext_ma_scalar_aggregate import MountainAshNarwhalsScalarAggregateExpressionSystem




@register_expression_system(CONST_VISITOR_BACKENDS.NARWHALS)
class NarwhalsExpressionSystem(
    # Foundation protocols
    SubstraitNarwhalsCastExpressionSystem,
    SubstraitNarwhalsConditionalExpressionSystem,
    SubstraitNarwhalsFieldReferenceExpressionSystem,
    SubstraitNarwhalsLiteralExpressionSystem,
    # Scalar protocols
    SubstraitNarwhalsAggregateArithmeticExpressionSystem,
    SubstraitNarwhalsAggregateBooleanExpressionSystem,
    SubstraitNarwhalsAggregateGenericExpressionSystem,
    SubstraitNarwhalsAggregateStringExpressionSystem,
    SubstraitNarwhalsScalarArithmeticExpressionSystem,
    SubstraitNarwhalsScalarBooleanExpressionSystem,
    SubstraitNarwhalsScalarComparisonExpressionSystem,
    SubstraitNarwhalsScalarDatetimeExpressionSystem,
    SubstraitNarwhalsScalarLogarithmicExpressionSystem,
    SubstraitNarwhalsScalarRoundingExpressionSystem,
    SubstraitNarwhalsScalarSetExpressionSystem,
    SubstraitNarwhalsScalarStringExpressionSystem,
    # Window protocols
    SubstraitNarwhalsWindowArithmeticExpressionSystem,
    # Geometry protocols
    SubstraitNarwhalsScalarGeometryExpressionSystem,
    # Mountainash extension protocols
    MountainAshNarwhalsNameExpressionSystem,
    MountainAshNarwhalsNullExpressionSystem,
    MountainAshNarwhalsScalarArithmeticExpressionSystem,
    MountainAshNarwhalsScalarDatetimeExpressionSystem,
    MountainAshNarwhalsScalarBooleanExpressionSystem,
    MountainAshNarwhalsScalarStringExpressionSystem,
    MountainAshNarwhalsScalarSetExpressionSystem,
    MountainAshNarwhalsScalarTernaryExpressionSystem,
    MountainAshNarwhalsWindowExpressionSystem,
    MountainAshNarwhalsScalarStructExpressionSystem,
    MountainAshNarwhalsScalarListExpressionSystem,
    MountainAshNarwhalsScalarAggregateExpressionSystem,

):
    """Complete Narwhals backend expression system.

    Composes all protocol implementations via multiple inheritance.
    Registered with the visitor factory for automatic backend detection.
    """

    pass


__all__ = [
    "NarwhalsExpressionSystem",
    # Foundation protocols
    "SubstraitNarwhalsCastExpressionSystem",
    "SubstraitNarwhalsConditionalExpressionSystem",
    "SubstraitNarwhalsFieldReferenceExpressionSystem",
    "SubstraitNarwhalsLiteralExpressionSystem",
    # Scalar protocols
    "SubstraitNarwhalsAggregateArithmeticExpressionSystem",
    "SubstraitNarwhalsAggregateBooleanExpressionSystem",
    "SubstraitNarwhalsAggregateGenericExpressionSystem",
    "SubstraitNarwhalsAggregateStringExpressionSystem",
    "SubstraitNarwhalsScalarArithmeticExpressionSystem",
    "SubstraitNarwhalsScalarBooleanExpressionSystem",
    "SubstraitNarwhalsScalarComparisonExpressionSystem",
    "SubstraitNarwhalsScalarDatetimeExpressionSystem",
    "SubstraitNarwhalsScalarLogarithmicExpressionSystem",
    "SubstraitNarwhalsScalarRoundingExpressionSystem",
    "SubstraitNarwhalsScalarSetExpressionSystem",
    "SubstraitNarwhalsScalarStringExpressionSystem",
    # Window protocols
    "SubstraitNarwhalsWindowArithmeticExpressionSystem",
    # Geometry protocols
    "SubstraitNarwhalsScalarGeometryExpressionSystem",
    # Mountainash extension protocols
    "MountainAshNarwhalsNameExpressionSystem",
    "MountainAshNarwhalsNullExpressionSystem",
    "MountainAshNarwhalsScalarArithmeticExpressionSystem",
    "MountainAshNarwhalsScalarDatetimeExpressionSystem",
    "MountainAshNarwhalsScalarSetExpressionSystem",
    "MountainAshNarwhalsScalarTernaryExpressionSystem"
]
