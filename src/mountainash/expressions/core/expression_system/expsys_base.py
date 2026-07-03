"""Base ExpressionSystem interface for backend primitives.

This module defines the abstract interface that all backend-specific
ExpressionSystem implementations must follow. It separates backend
primitives from logic dispatch.

Also provides backend detection and expression system registry functions.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Type

from mountainash.core.registries import KeyedRegistry
from ..constants import CONST_BACKEND

# Import protocols used for class inheritance (must be at runtime)

from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_cast import SubstraitCastExpressionSystemProtocol #, CastBuilderProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_conditional import (
    SubstraitConditionalExpressionSystemProtocol,
    # ConditionalBuilderProtocol,
    # WhenBuilderProtocol,
    # ThenBuilderProtocol,
)
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_field_reference import SubstraitFieldReferenceExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_literal import SubstraitLiteralExpressionSystemProtocol

# from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_aggregate import SubstraitScalarAggregateExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_arithmetic import  SubstraitScalarArithmeticExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_boolean import  SubstraitScalarBooleanExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_comparison import SubstraitScalarComparisonExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_datetime import  SubstraitScalarDatetimeExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_logarithmic import SubstraitScalarLogarithmicExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_rounding import  SubstraitScalarRoundingExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_set import SubstraitScalarSetExpressionSystemProtocol
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_string import  SubstraitScalarStringExpressionSystemProtocol





class ExpressionSystem(
    # CoreExpressionProtocol,
    # BooleanExpressionProtocol,
    # ArithmeticExpressionProtocol,
    # NullExpressionProtocol,
    # StringExpressionProtocol,
    # TemporalExpressionProtocol,
    # TypeExpressionProtocol,
    # NameExpressionProtocol,
    # HorizontalExpressionProtocol,
    # NativeExpressionProtocol,

SubstraitCastExpressionSystemProtocol,
SubstraitConditionalExpressionSystemProtocol,
SubstraitFieldReferenceExpressionSystemProtocol,
SubstraitLiteralExpressionSystemProtocol,

# ScalarAggregateExpressionProtocol,
# SubstraitScalarAggregateExpressionSystemProtocol,
SubstraitScalarArithmeticExpressionSystemProtocol,
SubstraitScalarBooleanExpressionSystemProtocol,
SubstraitScalarComparisonExpressionSystemProtocol,
SubstraitScalarDatetimeExpressionSystemProtocol,
SubstraitScalarLogarithmicExpressionSystemProtocol,
SubstraitScalarRoundingExpressionSystemProtocol,
SubstraitScalarSetExpressionSystemProtocol,
SubstraitScalarStringExpressionSystemProtocol


):
    """
    Abstract base class for backend-specific expression systems.

    ExpressionSystem encapsulates all backend-specific operations,
    providing a uniform interface for visitors to use regardless of
    the underlying DataFrame library (Narwhals, Polars, Pandas, Ibis, etc.).

    The visitor pattern uses this interface to build backend-native
    expressions without knowing the specific backend implementation.
    """

    @property
    @abstractmethod
    def backend_type(self) -> "CONST_BACKEND":
        """Return the backend type constant for this ExpressionSystem."""
        pass


    @abstractmethod
    def is_native_expression(self, expr: Any) -> bool:
        """Return True if the expression is a native expression for this backend."""
        pass


# Registry for ExpressionSystem implementations
_expression_system_registry: KeyedRegistry[str, Type[ExpressionSystem]] = KeyedRegistry(
    "expression system"
)


def register_expression_system(backend: "CONST_BACKEND"):
    """Decorator for registering ExpressionSystem classes.

    Usage:
        @register_expression_system(CONST_BACKEND.POLARS)
        class PolarsExpressionSystem(ExpressionSystem):
            ...

    Args:
        backend: The backend type constant.

    Returns:
        Decorator function.
    """
    return _expression_system_registry.decorator(backend.value)


def get_expression_system(backend: CONST_BACKEND) -> Type[ExpressionSystem]:
    """Get the ExpressionSystem class for a backend.

    Args:
        backend: The backend type constant.

    Returns:
        The ExpressionSystem class for the backend.

    Raises:
        KeyError: If no ExpressionSystem is registered for the backend.
    """
    return _expression_system_registry.get(backend.value)


# Moved to core (spec: relations-dispatch-parity §3.2). Re-exported for
# backwards compatibility — import from mountainash.core.backend_detection.
from mountainash.core.backend_detection import (  # noqa: F401
    _BACKEND_ALIASES,
    identify_backend,
)
