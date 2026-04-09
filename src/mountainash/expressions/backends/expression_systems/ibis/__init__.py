"""Ibis backend expression system.

This module composes all Ibis protocol implementations into a single
IbisExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.core.expression_system.expsys_base import register_expression_system


from .substrait.expsys_ib_cast import SubstraitIbisCastExpressionSystem
from .substrait.expsys_ib_conditional import SubstraitIbisConditionalExpressionSystem
from .substrait.expsys_ib_field_reference import SubstraitIbisFieldReferenceExpressionSystem
from .substrait.expsys_ib_literal import SubstraitIbisLiteralExpressionSystem

from .substrait.expsys_ib_aggregate_arithmetic import SubstraitIbisAggregateArithmeticExpressionSystem
from .substrait.expsys_ib_aggregate_boolean import    SubstraitIbisAggregateBooleanExpressionSystem
from .substrait.expsys_ib_aggregate_generic import    SubstraitIbisAggregateGenericExpressionSystem
from .substrait.expsys_ib_aggregate_string import     SubstraitIbisAggregateStringExpressionSystem


from .substrait.expsys_ib_scalar_arithmetic import SubstraitIbisScalarArithmeticExpressionSystem
from .substrait.expsys_ib_scalar_boolean import SubstraitIbisScalarBooleanExpressionSystem
from .substrait.expsys_ib_scalar_comparison import SubstraitIbisScalarComparisonExpressionSystem
from .substrait.expsys_ib_scalar_datetime import SubstraitIbisScalarDatetimeExpressionSystem
from .substrait.expsys_ib_scalar_logarithmic import SubstraitIbisScalarLogarithmicExpressionSystem
from .substrait.expsys_ib_scalar_rounding import SubstraitIbisScalarRoundingExpressionSystem
from .substrait.expsys_ib_scalar_set import SubstraitIbisScalarSetExpressionSystem
from .substrait.expsys_ib_scalar_string import SubstraitIbisScalarStringExpressionSystem

# Window protocols
from .substrait.expsys_ib_window_arithmetic import SubstraitIbisWindowArithmeticExpressionSystem

# Geometry protocols
from .substrait.expsys_ib_scalar_geometry import SubstraitIbisScalarGeometryExpressionSystem

# Ibis Mountainash Extensions
from .extensions_mountainash.expsys_ib_ext_ma_name import MountainAshIbisNameExpressionSystem
from .extensions_mountainash.expsys_ib_ext_ma_null import MountainAshIbisNullExpressionSystem
from .extensions_mountainash.expsys_ib_ext_ma_scalar_arithmetic import MountainAshIbisScalarArithmeticExpressionSystem
from .extensions_mountainash.expsys_ib_ext_ma_scalar_datetime import MountainAshIbisScalarDatetimeExpressionSystem
from .extensions_mountainash.expsys_ib_ext_ma_scalar_set import SubstraitIbisScalarSetExpressionSystem as MountainAshIbisScalarSetExpressionSystem
from .extensions_mountainash.expsys_ib_ext_ma_scalar_boolean import SubstraitIbisScalarBooleanExpressionSystem as MountainAshIbisScalarBooleanExpressionSystem
from .extensions_mountainash.expsys_ib_ext_ma_scalar_string import SubstraitIbisScalarStringExpressionSystem as MountainAshIbisScalarStringExpressionSystem
from .extensions_mountainash.expsys_ib_ext_ma_scalar_ternary import MountainAshIbisScalarTernaryExpressionSystem




@register_expression_system(CONST_VISITOR_BACKENDS.IBIS)
class IbisExpressionSystem(
    # Foundation protocols
    SubstraitIbisCastExpressionSystem,
    SubstraitIbisConditionalExpressionSystem,
    SubstraitIbisFieldReferenceExpressionSystem,
    SubstraitIbisLiteralExpressionSystem,
    # Scalar protocols
    SubstraitIbisAggregateArithmeticExpressionSystem,
    SubstraitIbisAggregateBooleanExpressionSystem,
    SubstraitIbisAggregateGenericExpressionSystem,
    SubstraitIbisAggregateStringExpressionSystem,
    SubstraitIbisScalarArithmeticExpressionSystem,
    SubstraitIbisScalarBooleanExpressionSystem,
    SubstraitIbisScalarComparisonExpressionSystem,
    SubstraitIbisScalarDatetimeExpressionSystem,
    SubstraitIbisScalarLogarithmicExpressionSystem,
    SubstraitIbisScalarRoundingExpressionSystem,
    SubstraitIbisScalarSetExpressionSystem,
    SubstraitIbisScalarStringExpressionSystem,
    # Window protocols
    SubstraitIbisWindowArithmeticExpressionSystem,
    # Geometry protocols
    SubstraitIbisScalarGeometryExpressionSystem,
    # Mountainash extension protocols
    MountainAshIbisNameExpressionSystem,
    MountainAshIbisNullExpressionSystem,
    MountainAshIbisScalarArithmeticExpressionSystem,
    MountainAshIbisScalarDatetimeExpressionSystem,
    MountainAshIbisScalarBooleanExpressionSystem,
    MountainAshIbisScalarStringExpressionSystem,
    MountainAshIbisScalarSetExpressionSystem,
    MountainAshIbisScalarTernaryExpressionSystem,

):
    """Complete Ibis backend expression system.

    Composes all protocol implementations via multiple inheritance.
    Registered with the visitor factory for automatic backend detection.
    """

    pass


__all__ = [
    "IbisExpressionSystem",
    # Foundation protocols
    "SubstraitIbisCastExpressionSystem",
    "SubstraitIbisConditionalExpressionSystem",
    "SubstraitIbisFieldReferenceExpressionSystem",
    "SubstraitIbisLiteralExpressionSystem",
    # Scalar protocols
    "SubstraitIbisAggregateArithmeticExpressionSystem",
    "SubstraitIbisAggregateBooleanExpressionSystem",
    "SubstraitIbisAggregateGenericExpressionSystem",
    "SubstraitIbisAggregateStringExpressionSystem",
    "SubstraitIbisScalarArithmeticExpressionSystem",
    "SubstraitIbisScalarBooleanExpressionSystem",
    "SubstraitIbisScalarComparisonExpressionSystem",
    "SubstraitIbisScalarDatetimeExpressionSystem",
    "SubstraitIbisScalarLogarithmicExpressionSystem",
    "SubstraitIbisScalarRoundingExpressionSystem",
    "SubstraitIbisScalarSetExpressionSystem",
    "SubstraitIbisScalarStringExpressionSystem",
    # Window protocols
    "SubstraitIbisWindowArithmeticExpressionSystem",
    # Geometry protocols
    "SubstraitIbisScalarGeometryExpressionSystem",
    # Mountainash extension protocols
    "MountainAshIbisNameExpressionSystem",
    "MountainAshIbisNullExpressionSystem",
    "MountainAshIbisScalarArithmeticExpressionSystem",
    "MountainAshIbisScalarDatetimeExpressionSystem",
    "MountainAshIbisScalarSetExpressionSystem",
    "MountainAshIbisScalarTernaryExpressionSystem"
]
