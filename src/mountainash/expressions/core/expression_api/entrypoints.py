"""Public entry point functions for creating expressions.

This module contains all standalone factory functions that create expressions:
- col(name): Create a column reference
- lit(value): Create a literal value
- coalesce(*exprs): Return first non-null value
- greatest(*exprs): Return maximum value
- least(*exprs): Return minimum value
- when(condition): Start a conditional expression

These are the primary entry points for the expression API.
The api/ layer re-exports these for user convenience.
"""

from __future__ import annotations
from typing import Any, Optional, Union, TYPE_CHECKING

from ..expression_nodes import (
    FieldReferenceNode,
    LiteralNode,
    ScalarFunctionNode,
)
from ..expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON
from .api_builders.substrait.api_bldr_conditional import SubstraitWhenAPIBuilder

if TYPE_CHECKING:
    from .api_base import BaseExpressionAPI
    from ..expression_nodes import ExpressionNode


# ============================================================================
# Core Entry Points (Substrait-aligned)
# ============================================================================

def col(name: str) -> BaseExpressionAPI:
    """
    Create a column reference expression.

    This is the primary entry point for building expressions.
    Creates an ExpressionBuilder wrapping a FieldReferenceNode.

    Args:
        name: Column name

    Returns:
        BooleanExpressionAPI for chaining operations

    Example:
        >>> expr = col("age").gt(30)
        >>> expr = col("name").eq("Alice")
        >>> expr = col("price").add(col("tax"))
    """
    from ..expression_api import BooleanExpressionAPI

    node = FieldReferenceNode(field=name)
    return BooleanExpressionAPI(node)


def lit(value: Any) -> BaseExpressionAPI:
    """
    Create a literal value expression.

    Wraps a constant value (int, float, str, bool, etc.) in an
    ExpressionBuilder for use in expressions.

    Args:
        value: Literal value (int, float, str, bool, None, etc.)

    Returns:
        BooleanExpressionAPI for chaining operations

    Example:
        >>> expr = lit(42)
        >>> expr = lit("hello")
        >>> expr = col("age").gt(lit(30))
        >>> expr = col("name").eq(lit(None))  # NULL check
    """
    from ..expression_api import BooleanExpressionAPI

    node = LiteralNode(value=value)
    return BooleanExpressionAPI(node)


def duration(
    *,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    milliseconds: int = 0,
    microseconds: int = 0,
) -> BaseExpressionAPI:
    """Create a duration literal expression.

    All parameters are keyword-only and literal-only (int, not Expr).

    Args:
        weeks: Number of weeks.
        days: Number of days.
        hours: Number of hours.
        minutes: Number of minutes.
        seconds: Number of seconds.
        milliseconds: Number of milliseconds.
        microseconds: Number of microseconds.

    Returns:
        Expression wrapping a timedelta literal.
    """
    from datetime import timedelta

    td = timedelta(
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds,
        microseconds=microseconds,
    )
    return lit(td)


# ============================================================================
# Horizontal Entry Points (Substrait-aligned)
# ============================================================================

def _to_substrait_node(val: Any) -> ExpressionNode:
    """Helper to convert a value to a ExpressionNode."""
    from ..expression_nodes import ExpressionNode, LiteralNode

    if hasattr(val, '_node'):
        node = val._node
        if isinstance(node, ExpressionNode):
            return node
        # Legacy node - wrap the API result
        return val._node

    # Raw value - wrap in LiteralNode
    return LiteralNode(value=val)


def coalesce(*exprs: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """
    Return the first non-null value from multiple expressions.

    Args:
        *exprs: Two or more expressions or values

    Returns:
        BooleanExpressionAPI with coalesce expression

    Raises:
        ValueError: If fewer than 2 arguments provided

    Example:
        >>> expr = coalesce(col("phone_mobile"), col("phone_home"), col("phone_work"))
        >>> expr = coalesce(col("nickname"), col("name"), lit("Anonymous"))
    """
    if len(exprs) < 2:
        raise ValueError("coalesce requires at least 2 arguments")

    from ..expression_api import BooleanExpressionAPI

    operands = [_to_substrait_node(e) for e in exprs]
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE,
        arguments=operands,
    )
    return BooleanExpressionAPI(node)


def greatest(*exprs: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """
    Return the maximum value across multiple expressions (element-wise).

    Args:
        *exprs: Two or more expressions or values

    Returns:
        BooleanExpressionAPI with greatest expression

    Raises:
        ValueError: If fewer than 2 arguments provided

    Example:
        >>> expr = greatest(col("a"), col("b"), col("c"))
        >>> expr = greatest(col("price"), lit(0))  # Ensure non-negative
    """
    if len(exprs) < 2:
        raise ValueError("greatest requires at least 2 arguments")

    from ..expression_api import BooleanExpressionAPI

    operands = [_to_substrait_node(e) for e in exprs]
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST,
        arguments=operands,
    )
    return BooleanExpressionAPI(node)


def least(*exprs: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """
    Return the minimum value across multiple expressions (element-wise).

    Args:
        *exprs: Two or more expressions or values

    Returns:
        BooleanExpressionAPI with least expression

    Raises:
        ValueError: If fewer than 2 arguments provided

    Example:
        >>> expr = least(col("a"), col("b"), col("c"))
        >>> expr = least(col("price"), lit(100))  # Cap at 100
    """
    if len(exprs) < 2:
        raise ValueError("least requires at least 2 arguments")

    from ..expression_api import BooleanExpressionAPI

    operands = [_to_substrait_node(e) for e in exprs]
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST,
        arguments=operands,
    )
    return BooleanExpressionAPI(node)


# ============================================================================
# Conditional Entry Points
# ============================================================================

def when(condition: Union[BaseExpressionAPI, ExpressionNode, Any]) -> SubstraitWhenAPIBuilder:
    """
    Start a conditional when-then-otherwise expression.

    Args:
        condition: Boolean condition to evaluate

    Returns:
        WhenBuilder to continue chain with then()

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
        >>> expr = when(col("score") >= 90).then("A").otherwise("B")
    """
    from ..expression_api import BooleanExpressionAPI

    condition_node = _to_substrait_node(condition)
    return SubstraitWhenAPIBuilder(
        condition=condition_node,
        prior_conditions=[],
        expression_api_class=BooleanExpressionAPI,
    )


# ============================================================================
# Native Expression Entry Points
# ============================================================================

def native(expr: Any) -> BaseExpressionAPI:
    """
    Wrap a backend-native expression in the abstract expression API.

    This is an "escape hatch" that allows mixing backend-specific expressions
    with mountainash expressions. The native expression is passed through
    unchanged during compilation.

    IMPORTANT: The native expression must match the backend of the DataFrame
    it will be used with. A Polars expression cannot be used with an Ibis table.

    Args:
        expr: A backend-native expression (pl.Expr, nw.Expr, ibis.Expr, etc.)

    Returns:
        BooleanExpressionAPI wrapping the native expression

    Example:
        >>> import polars as pl
        >>> import mountainash.expressions as ma
        >>>
        >>> # Use a native Polars expression
        >>> native_filter = pl.col("status").is_in(["active", "pending"])
        >>> ma_expr = ma.native(native_filter)
        >>>
        >>> # Combine with mountainash expressions
        >>> combined = ma_expr.and_(ma.col("age").gt(18))
        >>>
        >>> # Use in filter
        >>> result = df.filter(combined.compile(df))
    """
    from ..expression_api import BooleanExpressionAPI

    # Native expressions are stored as LiteralNode with a special dtype hint
    # The unified visitor will recognize this and pass it through
    node = LiteralNode(value=expr, dtype="native")
    return BooleanExpressionAPI(node)


# ============================================================================
# Ternary Entry Points (Substrait-aligned)
# ============================================================================

def t_col(name: str, unknown: set[Any] | None = None) -> BaseExpressionAPI:
    """
    Create a ternary-aware column reference with optional sentinel values.

    Unlike regular col(), t_col() tracks which values should be treated
    as UNKNOWN in ternary comparisons.

    Args:
        name: Column name
        unknown: Set of values to treat as UNKNOWN (default: {None})

    Returns:
        BooleanExpressionAPI for chaining ternary operations

    Example:
        >>> # Default: NULL is UNKNOWN
        >>> expr = t_col("score").t_gt(50)

        >>> # Custom sentinel: -99999 means "not evaluated"
        >>> expr = t_col("legacy_score", unknown={-99999, None}).t_gt(50)

        >>> # Multiple sentinels
        >>> expr = t_col("status", unknown={"NA", "<MISSING>", None}).t_eq("active")
    """
    from ..expression_api import BooleanExpressionAPI

    # Use FieldReferenceNode with unknown_values for ternary column references
    node = FieldReferenceNode(
        field=name,
        unknown_values=unknown,
    )
    return BooleanExpressionAPI(node)


def count_records() -> BaseExpressionAPI:
    """Substrait count_records() — counts all rows including nulls.

    Produces a backend-agnostic aggregate expression suitable for use inside
    ``relation.group_by(...).agg(...)`` or as a measure in an aggregate plan.

    Returns:
        A BaseExpressionAPI wrapping a ScalarFunctionNode with COUNT_RECORDS.
    """
    from ..expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    from ..expression_api import BooleanExpressionAPI

    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS,
        arguments=[],
        options={},
    )
    return BooleanExpressionAPI(node)


def corr(
    x: Union["BaseExpressionAPI", "ExpressionNode", Any],
    y: Union["BaseExpressionAPI", "ExpressionNode", Any],
    *,
    rounding: Optional[str] = None,
) -> "BaseExpressionAPI":
    """Pearson correlation between two expressions. Substrait ``corr(x, y)``.

    Args:
        x: First column expression.
        y: Second column expression.
        rounding: Optional Substrait rounding mode.

    Returns:
        BooleanExpressionAPI wrapping a ScalarFunctionNode with CORR.
    """
    from ..expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    from ..expression_api import BooleanExpressionAPI

    operands = [_to_substrait_node(x), _to_substrait_node(y)]
    opts: dict = {}
    if rounding is not None:
        opts["rounding"] = rounding
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR,
        arguments=operands,
        options=opts,
    )
    return BooleanExpressionAPI(node)


def median(
    precision: Union["BaseExpressionAPI", "ExpressionNode", Any],
    x: Union["BaseExpressionAPI", "ExpressionNode", Any],
    *,
    rounding: Optional[str] = None,
) -> "BaseExpressionAPI":
    """Median value. Substrait ``median(precision, x)``.

    Args:
        precision: Precision parameter (per Substrait spec).
        x: Column expression to take the median of.
        rounding: Optional Substrait rounding mode.
    """
    from ..expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    from ..expression_api import BooleanExpressionAPI

    operands = [_to_substrait_node(precision), _to_substrait_node(x)]
    opts: dict = {}
    if rounding is not None:
        opts["rounding"] = rounding
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN,
        arguments=operands,
        options=opts,
    )
    return BooleanExpressionAPI(node)


def quantile(
    boundaries: Union["BaseExpressionAPI", "ExpressionNode", Any],
    precision: Union["BaseExpressionAPI", "ExpressionNode", Any],
    n: Union["BaseExpressionAPI", "ExpressionNode", Any],
    distribution: Union["BaseExpressionAPI", "ExpressionNode", Any],
    *,
    rounding: Optional[str] = None,
) -> "BaseExpressionAPI":
    """Quantile aggregate. Substrait ``quantile(boundaries, precision, n, distribution)``.

    Args:
        boundaries: Quantile boundaries (e.g. 0.5 for median).
        precision: Precision parameter.
        n: Sample-size hint.
        distribution: Distribution mode (e.g. "linear").
        rounding: Optional Substrait rounding mode.
    """
    from ..expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    from ..expression_api import BooleanExpressionAPI

    operands = [
        _to_substrait_node(boundaries),
        _to_substrait_node(precision),
        _to_substrait_node(n),
        _to_substrait_node(distribution),
    ]
    opts: dict = {}
    if rounding is not None:
        opts["rounding"] = rounding
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE,
        arguments=operands,
        options=opts,
    )
    return BooleanExpressionAPI(node)


def always_true() -> "BaseExpressionAPI":
    """
    Create a constant TRUE (1) ternary expression.

    Returns:
        BooleanExpressionAPI with constant TRUE node

    Example:
        >>> expr = always_true()  # Returns 1 for all rows
    """
    from ..expression_api import BooleanExpressionAPI
    from ..expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY

    # Use ScalarFunctionNode so it flows through auto-booleanization
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_TRUE,
        arguments=[],
    )
    return BooleanExpressionAPI(node)


def always_false() -> BaseExpressionAPI:
    """
    Create a constant FALSE (-1) ternary expression.

    Returns:
        BooleanExpressionAPI with constant FALSE node

    Example:
        >>> expr = always_false()  # Returns -1 for all rows
    """
    from ..expression_api import BooleanExpressionAPI
    from ..expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY

    # Use ScalarFunctionNode so it flows through auto-booleanization
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_FALSE,
        arguments=[],
    )
    return BooleanExpressionAPI(node)


def always_unknown() -> BaseExpressionAPI:
    """
    Create a constant UNKNOWN (0) ternary expression.

    Returns:
        BooleanExpressionAPI with constant UNKNOWN node

    Example:
        >>> expr = always_unknown()  # Returns 0 for all rows
        >>> expr = when(condition).then(value).otherwise(always_unknown())
    """
    from ..expression_api import BooleanExpressionAPI
    from ..expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY

    # Use ScalarFunctionNode so it flows through auto-booleanization
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_UNKNOWN,
        arguments=[],
    )
    return BooleanExpressionAPI(node)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core
    "col",
    "lit",
    "duration",
    # Horizontal
    "coalesce",
    "greatest",
    "least",
    # Aggregate
    "count_records",
    "corr",
    "median",
    "quantile",
    # Conditional
    "when",
    # Native
    "native",
    # Ternary
    "t_col",
    "always_true",
    "always_false",
    "always_unknown",
]
