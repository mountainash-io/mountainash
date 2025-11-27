"""
Public API for Mountain Ash Expressions.

This module provides a Polars/Narwhals-style API for building expressions
that compile to backend-native expressions.

Example:
    >>> import mountainash_expressions as ma
    >>>
    >>> # Build expression (backend-agnostic)
    >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
    >>>
    >>> # Compile to backend-native expression
    >>> backend_expr = expr.compile(df)
    >>>
    >>> # Use with dataframe
    >>> result = df.filter(backend_expr)

Helper Functions:
    >>> # For convenience, use helper functions
    >>> result = ma.filter(df, ma.col("age").gt(30))
    >>>
    >>> # Or compile inline
    >>> result = df.filter(ma.col("age").gt(30).compile(df))
"""

from typing import Any, List, Union

from .expression_builder import ExpressionBuilder
from ..core.constants import (
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_SOURCE_OPERATORS,
    CONST_EXPRESSION_LITERAL_OPERATORS,
    CONST_EXPRESSION_CONDITIONAL_OPERATORS,
)
from ..core.expression_nodes import (
    SourceExpressionNode,
    LiteralExpressionNode,
    ConditionalIfElseExpressionNode,
)


# ========================================
# Entry Point Functions
# ========================================

def col(name: str, logic_type: CONST_LOGIC_TYPES = CONST_LOGIC_TYPES.BOOLEAN) -> ExpressionBuilder:
    """
    Create a column reference expression.

    This is the primary entry point for building expressions.

    Args:
        name: Column name
        logic_type: Logic system to use (BOOLEAN or TERNARY)

    Returns:
        ExpressionBuilder for chaining operations

    Example:
        >>> expr = col("age").gt(30)
        >>> expr = col("name").eq("Alice")
    """
    # For columns, we can just store the string directly
    # The visitor's _process_operand() will handle converting it
    return ExpressionBuilder(name, logic_type)


def lit(value: Any, logic_type: CONST_LOGIC_TYPES = CONST_LOGIC_TYPES.BOOLEAN) -> ExpressionBuilder:
    """
    Create a literal value expression.

    Args:
        value: Literal value (int, float, str, bool, etc.)
        logic_type: Logic system to use (BOOLEAN or TERNARY)

    Returns:
        ExpressionBuilder for chaining operations

    Example:
        >>> expr = lit(42)
        >>> expr = lit("hello")
    """
    # Create a proper LiteralExpressionNode
    node = LiteralExpressionNode(CONST_EXPRESSION_LITERAL_OPERATORS.LIT, value)
    return ExpressionBuilder(node, logic_type)


# ========================================
# Helper Functions (Convenience)
# ========================================

def filter(dataframe: Any, expr: ExpressionBuilder, logic_type: CONST_LOGIC_TYPES = None) -> Any:
    """
    Helper function to filter a dataframe with an expression.

    This is a convenience function that automatically compiles the expression
    and applies it to the dataframe.

    Args:
        dataframe: DataFrame to filter
        expr: ExpressionBuilder or backend-native expression
        logic_type: Logic type override (optional)

    Returns:
        Filtered dataframe

    Example:
        >>> result = filter(df, col("age").gt(30))
        >>> # Equivalent to:
        >>> # result = df.filter(col("age").gt(30).compile(df))
    """
    if isinstance(expr, ExpressionBuilder):
        # Compile to backend-native expression
        backend_expr = expr.compile(dataframe, logic_type=logic_type)
    else:
        # Already a backend-native expression
        backend_expr = expr

    # Apply filter
    return dataframe.filter(backend_expr)


def select(dataframe: Any, *exprs: ExpressionBuilder, logic_type: CONST_LOGIC_TYPES = None) -> Any:
    """
    Helper function to select columns/expressions from a dataframe.

    Args:
        dataframe: DataFrame to select from
        *exprs: ExpressionBuilder instances or column names
        logic_type: Logic type override (optional)

    Returns:
        DataFrame with selected columns

    Example:
        >>> result = select(df, col("age"), col("name"))
    """
    # Compile expressions
    backend_exprs = []
    for expr in exprs:
        if isinstance(expr, ExpressionBuilder):
            backend_exprs.append(expr.compile(dataframe, logic_type=logic_type))
        elif isinstance(expr, str):
            # String column name - convert to column expression
            backend_exprs.append(col(expr).compile(dataframe, logic_type=logic_type))
        else:
            # Already backend-native
            backend_exprs.append(expr)

    # Apply select
    return dataframe.select(*backend_exprs)


def with_columns(dataframe: Any, **named_exprs) -> Any:
    """
    Helper function to add or replace columns in a dataframe.

    Args:
        dataframe: DataFrame to modify
        **named_exprs: Column names mapped to ExpressionBuilder instances

    Returns:
        DataFrame with new/modified columns

    Example:
        >>> result = with_columns(
        ...     df,
        ...     age_group=col("age").gt(30)
        ... )
    """
    # Compile expressions
    compiled_exprs = {}
    for name, expr in named_exprs.items():
        if isinstance(expr, ExpressionBuilder):
            compiled_exprs[name] = expr.compile(dataframe)
        else:
            # Already backend-native
            compiled_exprs[name] = expr

    # Apply with_columns (if backend supports it)
    if hasattr(dataframe, 'with_columns'):
        return dataframe.with_columns(**compiled_exprs)
    else:
        raise NotImplementedError(f"Backend {type(dataframe)} does not support with_columns")


# ========================================
# Conditional Operations
# ========================================

class WhenBuilder:
    """
    Builder for fluent when().then().otherwise() conditional expressions.

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
    """

    def __init__(self, condition: ExpressionBuilder, logic_type: CONST_LOGIC_TYPES = CONST_LOGIC_TYPES.BOOLEAN):
        self._condition = condition
        self._logic_type = logic_type

    def then(self, consequence: Union[ExpressionBuilder, Any]) -> "WhenThenBuilder":
        """
        Specify the value to return if condition is true.

        Args:
            consequence: Value if condition is true

        Returns:
            WhenThenBuilder to continue chain with otherwise()
        """
        return WhenThenBuilder(self._condition, consequence, self._logic_type)


class WhenThenBuilder:
    """
    Intermediate builder after then(), requires otherwise() to complete.

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
    """

    def __init__(self, condition: ExpressionBuilder, consequence: Any, logic_type: CONST_LOGIC_TYPES):
        self._condition = condition
        self._consequence = consequence
        self._logic_type = logic_type

    def otherwise(self, alternative: Union[ExpressionBuilder, Any]) -> ExpressionBuilder:
        """
        Specify the value to return if condition is false.

        Args:
            alternative: Value if condition is false

        Returns:
            ExpressionBuilder with complete conditional expression
        """
        # Helper to convert value to ExpressionBuilder
        def to_builder(val):
            if isinstance(val, ExpressionBuilder):
                return val
            else:
                # Wrap as literal
                return lit(val, self._logic_type)

        # Convert all parts to ExpressionBuilder
        condition_builder = to_builder(self._condition)
        consequence_builder = to_builder(self._consequence)
        alternative_builder = to_builder(alternative)

        node = ConditionalIfElseExpressionNode(
            CONST_EXPRESSION_CONDITIONAL_OPERATORS.WHEN,
            condition=condition_builder._node,
            consequence=consequence_builder._node,
            alternative=alternative_builder._node
        )
        return ExpressionBuilder(node, self._logic_type)


def when(condition: ExpressionBuilder, logic_type: CONST_LOGIC_TYPES = CONST_LOGIC_TYPES.BOOLEAN) -> WhenBuilder:
    """
    Start a conditional when-then-otherwise expression.

    Args:
        condition: Boolean condition to evaluate
        logic_type: Logic system to use (BOOLEAN or TERNARY)

    Returns:
        WhenBuilder to continue chain with then()

    Example:
        >>> expr = when(col("age") > 65).then("senior").otherwise("non-senior")
        >>> expr = when(col("score") >= 90).then("A").otherwise("B")
    """
    return WhenBuilder(condition, logic_type)


def coalesce(*values: Union[ExpressionBuilder, Any], logic_type: CONST_LOGIC_TYPES = CONST_LOGIC_TYPES.BOOLEAN) -> ExpressionBuilder:
    """
    Return first non-null value from a list.

    Args:
        *values: Two or more expressions or values
        logic_type: Logic system to use (BOOLEAN or TERNARY)

    Returns:
        ExpressionBuilder with coalesce expression

    Example:
        >>> expr = coalesce(col("phone_mobile"), col("phone_home"), col("phone_work"))
        >>> expr = coalesce(col("preferred_name"), col("first_name"))
    """
    if len(values) < 2:
        raise ValueError("coalesce() requires at least 2 values")

    # Convert all values to nodes
    value_nodes = []
    for value in values:
        if isinstance(value, ExpressionBuilder):
            value_nodes.append(value._node)
        else:
            value_nodes.append(value)

    node = ConditionalIfElseExpressionNode(
        CONST_EXPRESSION_CONDITIONAL_OPERATORS.COALESCE,
        values=value_nodes
    )
    return ExpressionBuilder(node, logic_type)


# ========================================
# Logical Combinators (for convenience)
# ========================================

def and_(*exprs: ExpressionBuilder) -> ExpressionBuilder:
    """
    Combine multiple expressions with AND.

    Args:
        *exprs: Two or more ExpressionBuilder instances

    Returns:
        ExpressionBuilder with AND operation

    Example:
        >>> expr = and_(
        ...     col("age").gt(30),
        ...     col("score").ge(85),
        ...     col("active").eq(True)
        ... )
    """
    if len(exprs) < 2:
        raise ValueError("and_() requires at least 2 expressions")

    result = exprs[0]
    for expr in exprs[1:]:
        result = result.and_(expr)
    return result


def or_(*exprs: ExpressionBuilder) -> ExpressionBuilder:
    """
    Combine multiple expressions with OR.

    Args:
        *exprs: Two or more ExpressionBuilder instances

    Returns:
        ExpressionBuilder with OR operation

    Example:
        >>> expr = or_(
        ...     col("age").lt(18),
        ...     col("age").gt(65)
        ... )
    """
    if len(exprs) < 2:
        raise ValueError("or_() requires at least 2 expressions")

    result = exprs[0]
    for expr in exprs[1:]:
        result = result.or_(expr)
    return result


def not_(expr: ExpressionBuilder) -> ExpressionBuilder:
    """
    Negate an expression.

    Args:
        expr: ExpressionBuilder to negate

    Returns:
        ExpressionBuilder with NOT operation

    Example:
        >>> expr = not_(col("active"))
    """
    return expr.not_()


# ========================================
# Exports
# ========================================

__all__ = [
    # Builder class
    "ExpressionBuilder",
    # Entry points
    "col",
    "lit",
    # Helper functions
    "filter",
    "select",
    "with_columns",
    # Conditional operations
    "when",
    "coalesce",
    # Logical combinators
    "and_",
    "or_",
    "not_",
]
