"""Ibis backend expression system.

This module composes all Ibis protocol implementations into a single
IbisExpressionSystem class that can be registered with the visitor factory.
"""

from __future__ import annotations

from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash_expressions.core.expression_system.expsys_base import register_expression_system

# Foundation protocols
from .field_reference import IbisFieldReferenceSystem
from .literal import IbisLiteralSystem
from .cast import IbisCastSystem
from .conditional import IbisConditionalSystem

# Scalar protocols
from .scalar_comparison import IbisScalarComparisonSystem
from .scalar_boolean import IbisScalarBooleanSystem
from .scalar_arithmetic import IbisScalarArithmeticSystem
from .scalar_string import IbisScalarStringSystem
from .scalar_datetime import IbisScalarDatetimeSystem
from .scalar_rounding import IbisScalarRoundingSystem
from .scalar_logarithmic import IbisScalarLogarithmicSystem
from .scalar_set import IbisScalarSetSystem
from .scalar_aggregate import IbisScalarAggregateSystem


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
]
