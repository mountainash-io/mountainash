"""Base ExpressionSystem interface for backend primitives.

This module defines the abstract interface that all backend-specific
ExpressionSystem implementations must follow. It separates backend
primitives from logic dispatch.

Also provides backend detection and expression system registry functions.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Type, TYPE_CHECKING

from ..constants import CONST_VISITOR_BACKENDS

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


def get_expression_system(backend: CONST_VISITOR_BACKENDS) -> Type[ExpressionSystem]:
    """Get the ExpressionSystem class for a backend.

    Args:
        backend: The backend type constant.

    Returns:
        The ExpressionSystem class for the backend.

    Raises:
        KeyError: If no ExpressionSystem is registered for the backend.
    """
    return _expression_system_registry[backend.value]


# Backend alias mapping
_BACKEND_ALIASES: Dict[str, CONST_VISITOR_BACKENDS] = {
    # Polars
    "polars": CONST_VISITOR_BACKENDS.POLARS,
    "pl": CONST_VISITOR_BACKENDS.POLARS,
    # Ibis
    "ibis": CONST_VISITOR_BACKENDS.IBIS,
    "ir": CONST_VISITOR_BACKENDS.IBIS,
    # Narwhals
    "narwhals": CONST_VISITOR_BACKENDS.NARWHALS,
    "nw": CONST_VISITOR_BACKENDS.NARWHALS,
    # Pandas
    "pandas": CONST_VISITOR_BACKENDS.PANDAS,
    "pd": CONST_VISITOR_BACKENDS.PANDAS,
}


def identify_backend(dataframe_or_backend: Any) -> CONST_VISITOR_BACKENDS:
    """
    Identify the backend framework from a DataFrame/Table object or string identifier.

    Args:
        dataframe_or_backend: Either:
            - A DataFrame/Table object (pl.DataFrame, nw.DataFrame, ir.Table, etc.)
            - A string identifier ("polars", "pl", "ibis", "ir", "narwhals", "nw")
            - A CONST_VISITOR_BACKENDS enum value

    Returns:
        The identified backend constant

    Raises:
        ValueError: If backend cannot be identified

    Examples:
        >>> identify_backend(polars_df)  # Auto-detect from DataFrame
        >>> identify_backend("polars")   # Explicit string
        >>> identify_backend("ibis")     # Explicit string
        >>> identify_backend(CONST_VISITOR_BACKENDS.POLARS)  # Pass-through
    """
    # Handle string identifiers
    if isinstance(dataframe_or_backend, str):
        backend_lower = dataframe_or_backend.lower()
        if backend_lower in _BACKEND_ALIASES:
            return _BACKEND_ALIASES[backend_lower]
        raise ValueError(
            f"Unknown backend identifier: '{dataframe_or_backend}'. "
            f"Valid options: {list(_BACKEND_ALIASES.keys())}"
        )

    # Handle CONST_VISITOR_BACKENDS enum directly (pass-through)
    if isinstance(dataframe_or_backend, CONST_VISITOR_BACKENDS):
        return dataframe_or_backend

    # Auto-detect from DataFrame object
    dataframe = dataframe_or_backend

    # Get the module and class name
    module_name = type(dataframe).__module__
    class_name = type(dataframe).__name__

    # Narwhals detection FIRST - check for narwhals DataFrame/LazyFrame
    # Narwhals wraps other backends, so we need to check for it before checking for polars/pandas
    if "narwhals" in module_name or hasattr(dataframe, "_compliant_frame"):
        # Check if Narwhals is wrapping Ibis - this is not supported
        if hasattr(dataframe, "implementation"):
            impl = dataframe.implementation
            # Check if it's wrapping Ibis (impl.value == 'ibis')
            if hasattr(impl, "value") and impl.value == "ibis":
                raise ValueError(
                    "Narwhals-wrapped Ibis tables are not supported due to upstream compatibility issues. "
                    "Please unwrap the Ibis table using `df.to_native()` and use the Ibis backend directly."
                )
        # Use Narwhals backend for other implementations (Polars, Pandas, etc.)
        return CONST_VISITOR_BACKENDS.NARWHALS

    # Ibis detection
    if "ibis" in module_name:
        return CONST_VISITOR_BACKENDS.IBIS

    # Polars detection
    if "polars" in module_name or class_name in ("DataFrame", "LazyFrame"):
        # Check if it's really polars
        if hasattr(dataframe, "lazy"):  # polars-specific method
            return CONST_VISITOR_BACKENDS.POLARS

    # Fallback: try wrapping in narwhals
    # This handles pandas, pyarrow, and other narwhals-compatible backends
    try:
        import narwhals as nw
        nw.from_native(dataframe)
        # If we get here, narwhals can handle it
        return CONST_VISITOR_BACKENDS.NARWHALS
    except (TypeError, ValueError):
        # Narwhals couldn't wrap it
        pass

    raise ValueError(
        f"Cannot identify backend for type {type(dataframe)}. "
        f"Module: {module_name}, Class: {class_name}. "
        f"Tip: Try wrapping your DataFrame with narwhals: nw.from_native(df)"
    )
