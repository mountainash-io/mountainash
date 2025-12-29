"""Ibis backend expression system.

This module composes all Ibis protocol implementations into a single
IbisExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.core.expression_system.expsys_base import register_expression_system

# Foundation protocols
from substrait.field_reference import IbisFieldReferenceSystem
from substrait.literal import IbisLiteralSystem
from substrait.cast import IbisCastSystem
from substrait.conditional import IbisConditionalSystem

# Scalar protocols
from .substrait.scalar_comparison import IbisScalarComparisonSystem
from .substrait.scalar_boolean import IbisScalarBooleanSystem
from .substrait.scalar_arithmetic import IbisScalarArithmeticSystem
from .substrait.scalar_string import IbisScalarStringSystem
from .substrait.scalar_datetime import IbisScalarDatetimeSystem
from .substrait.scalar_rounding import IbisScalarRoundingSystem
from .substrait.scalar_logarithmic import IbisScalarLogarithmicSystem
from .substrait.scalar_set import IbisScalarSetSystem
from .substrait.scalar_aggregate import IbisScalarAggregateSystem

# Mountainash extension protocols
from mountainash_extensions.ext_ternary import IbisTernarySystem
from mountainash_extensions.ext_null import IbisNullExtensionSystem
from mountainash_extensions.ext_name import IbisNameExtensionSystem


@register_expression_system(CONST_VISITOR_BACKENDS.IBIS)
class IbisExpressionSystem(
    # Foundation protocols
    IbisFieldReferenceSystem,
    IbisLiteralSystem,
    IbisCastSystem,
    IbisConditionalSystem,
    # Scalar protocols
    IbisScalarComparisonSystem,
    IbisScalarBooleanSystem,
    IbisScalarArithmeticSystem,
    IbisScalarStringSystem,
    IbisScalarDatetimeSystem,
    IbisScalarRoundingSystem,
    IbisScalarLogarithmicSystem,
    IbisScalarSetSystem,
    IbisScalarAggregateSystem,
    # Mountainash extension protocols
    IbisTernarySystem,
    IbisNullExtensionSystem,
    IbisNameExtensionSystem,
):
    """Complete Ibis backend expression system.

    Composes all protocol implementations via multiple inheritance.
    Registered with the visitor factory for automatic backend detection.

    Ibis supports multiple backends (DuckDB, SQLite, Polars, Postgres, etc.)
    through a unified interface. Some operations may behave differently
    depending on the underlying database engine.
    """

    pass


__all__ = [
    "IbisExpressionSystem",
    # Foundation protocols
    "IbisFieldReferenceSystem",
    "IbisLiteralSystem",
    "IbisCastSystem",
    "IbisConditionalSystem",
    # Scalar protocols
    "IbisScalarComparisonSystem",
    "IbisScalarBooleanSystem",
    "IbisScalarArithmeticSystem",
    "IbisScalarStringSystem",
    "IbisScalarDatetimeSystem",
    "IbisScalarRoundingSystem",
    "IbisScalarLogarithmicSystem",
    "IbisScalarSetSystem",
    "IbisScalarAggregateSystem",
    # Mountainash extension protocols
    "IbisTernarySystem",
    "IbisNullExtensionSystem",
    "IbisNameExtensionSystem",
]
