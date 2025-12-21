"""Base ExpressionSystem interface for backend primitives.

This module defines the abstract interface that all backend-specific
ExpressionSystem implementations must follow. It separates backend
primitives from logic dispatch.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Type, TYPE_CHECKING

# Import protocols used for class inheritance (must be at runtime)

from ..expression_protocols.substrait import (
CastExpressionProtocol,
ConditionalExpressionProtocol,
FieldReferenceExpressionProtocol,
LiteralExpressionProtocol,
ScalarAggregateExpressionProtocol,
ScalarArithmeticExpressionProtocol,
ScalarBooleanExpressionProtocol,
ScalarComparisonExpressionProtocol,
ScalarDatetimeExpressionProtocol,
ScalarLogarithmicExpressionProtocol,
ScalarRoundingExpressionProtocol,
ScalarSetExpressionProtocol,
ScalarStringExpressionProtocol,
)

if TYPE_CHECKING:
    from ..constants import CONST_VISITOR_BACKENDS



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

CastExpressionProtocol,
ConditionalExpressionProtocol,
FieldReferenceExpressionProtocol,
LiteralExpressionProtocol,

# ScalarAggregateExpressionProtocol,
ScalarArithmeticExpressionProtocol,
ScalarBooleanExpressionProtocol,
ScalarComparisonExpressionProtocol,
ScalarDatetimeExpressionProtocol,
# ScalarLogarithmicExpressionProtocol,
# ScalarRoundingExpressionProtocol,
ScalarSetExpressionProtocol,
ScalarStringExpressionProtocol,


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
    def backend_type(self) -> "CONST_VISITOR_BACKENDS":
        """Return the backend type constant for this ExpressionSystem."""
        pass


    @abstractmethod
    def is_native_expression(self, expr: Any) -> bool:
        """Return True if the expression is a native expression for this backend."""
        pass


# Registry for ExpressionSystem implementations
_expression_system_registry: Dict[str, Type[ExpressionSystem]] = {}


def register_expression_system(backend: "CONST_VISITOR_BACKENDS"):
    """Decorator for registering ExpressionSystem classes.

    Usage:
        @register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
        class PolarsExpressionSystem(ExpressionSystem):
            ...

    Args:
        backend: The backend type constant.

    Returns:
        Decorator function.
    """
    def decorator(cls: Type[ExpressionSystem]) -> Type[ExpressionSystem]:
        _expression_system_registry[backend.value] = cls
        return cls
    return decorator


def get_expression_system(backend: "CONST_VISITOR_BACKENDS") -> Type[ExpressionSystem]:
    """Get the ExpressionSystem class for a backend.

    Args:
        backend: The backend type constant.

    Returns:
        The ExpressionSystem class for the backend.

    Raises:
        KeyError: If no ExpressionSystem is registered for the backend.
    """
    return _expression_system_registry[backend.value]
