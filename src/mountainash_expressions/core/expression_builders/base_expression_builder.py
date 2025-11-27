
from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING
from abc import ABC, abstractmethod

from ibis.common.collections import Abstract

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

# from . import (BooleanExpressionBuilder,
# ArithmeticExpressionBuilder,
# TypeExpressionBuilder,
# NativeExpressionBuilder,
# IterableExpressionBuilder,
# NullExpressionBuilder,
# NameExpressionBuilder,
# StringExpressionBuilder,
# TemporalExpressionBuilder
# )


class BaseExpressionBuilder(ABC

    # BooleanExpressionBuilder,
    # ArithmeticExpressionBuilder,
    # TypeExpressionBuilder,
    # NativeExpressionBuilder,
    # IterableExpressionBuilder,
    # NullExpressionBuilder,
    # NameExpressionBuilder,
    # StringExpressionBuilder,
    # TemporalExpressionBuilder,
):
    """
    Fluent API builder for expressions.

    This class provides a chainable interface for building expressions
    that follows the Polars/Narwhals pattern. Under the hood, it builds
    an ExpressionNode AST that can be compiled to any backend.

    Composed from mixins providing:
    - Boolean operations (eq, ne, gt, lt, ge, le, and_, or_, not_, etc.)
    - Arithmetic operations (add, subtract, multiply, divide, modulo, power, floor_divide)
    - Type operations (cast)
    - Native expression wrapping (native)
    - Iterable operations (coalesce, greatest, least)
    - NULL operations (is_null, not_null, fill_null, null_if, always_null)
    - Name operations (alias, prefix, suffix, to_upper, to_lower)
    - String operations (str_upper, str_lower, str_trim, str_contains, pat_regex_match, etc.)
    - Temporal operations (dt_year, dt_month, dt_add_days, dt_diff_hours, etc.)

    Example:
        >>> from .mixins.core import col, lit
        >>> expr = col("age").gt(30).and_(col("score").ge(85))
        >>> # Compile and use with a backend DataFrame
    """

    def __init__(self, node: Union[ExpressionNode, Any]):
        """
        Initialize with an ExpressionNode or raw value.

        Args:
            node: The underlying expression node or raw value (string, int, etc.)
        """
        self._node = node

    @classmethod
    @abstractmethod
    def create(cls, node: ExpressionNode) -> BaseExpressionBuilder:
        raise NotImplementedError("Subclasses must implement this method")

    @property
    def node(self) -> Union[ExpressionNode, Any]:
        """Get the underlying expression node or raw value."""
        return self._node


    # ========================================
    # Helper Methods
    # ========================================

    def _to_node_or_value(self, other: Union[BaseExpressionBuilder, Any]) -> Any:
        """
        Convert value to node representation.

        Args:
            other: ExpressionBuilder, ExpressionNode, or raw value

        Returns:
            Node representation (ExpressionNode or raw value)

        Note:
            Raw values (strings, ints, etc.) are kept as-is.
            The visitor's _process_operand() will handle converting them.
        """
        if isinstance(other, BaseExpressionBuilder):
            return other._node
        else:
            # Keep raw values as-is (visitor will handle them)
            return other

    def compile(self, dataframe: Any, logic_type: Any = None) -> Any:
        """
        Compile expression to backend-native expression.

        This is the main entry point for converting a backend-agnostic
        ExpressionBuilder to a backend-specific expression (pl.Expr, nw.Expr, ir.Expr).

        Args:
            dataframe: DataFrame to detect backend from (pl.DataFrame, nw.DataFrame, ir.Table, etc.)
            logic_type: Logic system (defaults to BOOLEAN)

        Returns:
            Backend-native expression (pl.Expr | nw.Expr | ir.Expr)

        Example:
            >>> import mountainash_expressions as ma
            >>> expr = ma.col("age").gt(30)
            >>> backend_expr = expr.compile(df)  # df is Polars DataFrame
            >>> result = df.filter(backend_expr)
        """
        from ..expression_visitors import ExpressionVisitorFactory
        from ...constants import CONST_LOGIC_TYPES
        from ..expression_nodes import ExpressionNode

        logic = logic_type or CONST_LOGIC_TYPES.BOOLEAN

        # Detect backend and get ExpressionSystem
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system_class = ExpressionVisitorFactory._expression_systems_registry[backend_type]
        expression_system = expression_system_class()

        # Get appropriate visitor for the top-level node
        if isinstance(self._node, ExpressionNode):
            visitor = ExpressionVisitorFactory.get_visitor_for_node(
                self._node,
                expression_system,
                logic
            )
            return self._node.accept(visitor)
        else:
            # Handle raw values
            from ..expression_parameters import ExpressionParameter
            return ExpressionParameter(
                self._node,
                expression_system=expression_system
            ).to_native_expression()
