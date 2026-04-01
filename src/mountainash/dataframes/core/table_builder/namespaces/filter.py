"""
FilterNamespace - Row filtering operations.

Provides:
    - filter(expression) - Filter rows by expression
    - where(expression) - Alias for filter
    - query(expression) - Alias for filter

Supports three types of expressions:
    1. Native backend expressions (pl.Expr, nw.Expr, ir.Expr, pd.Series)
    2. Mountainash expressions (from mountainash-expressions package)
    3. Callable that receives the builder and returns an expression

Uses OperationResolver for unified cross-backend resolution.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Union

if TYPE_CHECKING:
    from ..base import BaseTableBuilder

from ..base import BaseNamespace
from ...protocols import FilterBuilderProtocol
from ...constants import InputType

# Import type detection utilities from core.typing
from ...typing import (
    is_mountainash_expression,
    is_native_expression,
    is_native_series,
)

# Import expression compiler and unified resolver
from ...utils import compile_expression
from ...operations import OperationResolver

logger = logging.getLogger(__name__)


def _is_native_filter_input(obj: Any) -> bool:
    """
    Check if object is a native filter input (expression or series).

    This is the union of native expressions and native series,
    used to determine if an input can be passed directly to the backend.
    """
    return is_native_expression(obj) or is_native_series(obj)


class FilterNamespace(BaseNamespace, FilterBuilderProtocol):
    """
    Namespace for row filtering operations.

    All methods return a new TableBuilder instance for chaining.

    Expression Types:
        The filter() method intelligently handles multiple expression types:

        1. **Native expressions**: Backend-specific expressions are passed through
           directly (pl.Expr, nw.Expr, ir.Expr, pd.Series).

        2. **Mountainash expressions**: Expressions from mountainash-expressions
           are automatically compiled against the current DataFrame. For pandas/
           PyArrow DataFrames, expressions are compiled via Narwhals wrapping.

        3. **Callables**: Functions that receive the builder and return an
           expression are executed to obtain the expression.
    """

    def _resolve_expression(
        self,
        expression: Union[Any, Callable[["BaseTableBuilder"], Any]],
    ) -> Any:
        """
        Resolve an expression to a native backend expression.

        Detection order (important - native expressions like pl.Expr are callable!):
        1. Native expressions/series (pl.Expr, nw.Expr, ir.Expr, pd.Series): Pass through
        2. Mountainash expressions: Compile against current DataFrame
        3. Callables: Execute with builder, then recurse to resolve result
        4. Unknown: Pass through and let backend handle/error

        Args:
            expression: Expression in any supported format

        Returns:
            Native backend expression ready for filtering
        """
        # Step 1: Native expression or series? Pass through unchanged
        # MUST check this first - native expressions like pl.Expr are callable!
        if _is_native_filter_input(expression):
            logger.debug(f"Native filter input detected: {type(expression).__name__}")
            return expression

        # Step 2: Mountainash expression? Compile it
        # For pandas/PyArrow, this compiles via Narwhals → returns nw.Expr
        if is_mountainash_expression(expression):
            logger.debug(f"Compiling mountainash expression: {type(expression).__name__}")
            return compile_expression(expression, self._df)

        # Step 3: Callable? Execute and recurse to resolve the result. Callable might be a bit generic!! WHAT IS THIS?
        if callable(expression):
            logger.debug(f"Executing callable: {type(expression).__name__}")
            result = expression(self._builder)
            return self._resolve_expression(result)

        # Step 4: Unknown - pass through and let backend handle it
        logger.debug(f"Passing through unknown expression type: {type(expression).__name__}")
        return expression

    def _apply_filter(self, expression: Any) -> Any:
        """
        Apply a filter expression to the current DataFrame.

        Uses OperationResolver for unified cross-backend resolution:
        - Handles expression wrapping (e.g., nw.Expr on pandas)
        - Handles series conversion (e.g., pl.Series on pandas)
        - Returns unwrapped result in original DataFrame type

        Args:
            expression: Native expression or series to apply

        Returns:
            Filtered DataFrame
        """
        # Use OperationResolver for unified resolution
        ctx = OperationResolver.resolve(self._df, expression)
        logger.debug(f"Resolved: {ctx}")

        # Execute filter via DataFrameSystem
        result = self._execute_filter(ctx.dataframe, ctx.input, ctx.input_type)

        # Unwrap result back to original DataFrame type
        return ctx.unwrap(result)

    def _execute_filter(self, df: Any, expression: Any, input_type: InputType) -> Any:
        """
        Execute the actual filter operation on a resolved DataFrame.

        At this point, df and expression are guaranteed to be compatible.
        Delegates to DataFrameSystem for backend-specific filtering.

        Args:
            df: Resolved DataFrame (possibly wrapped in Narwhals)
            expression: Resolved expression/series (converted to match df)
            input_type: Type of input (EXPRESSION or SERIES)

        Returns:
            Filtered DataFrame
        """
        from ...dataframe_system import DataFrameSystemFactory

        # Get the appropriate DataFrameSystem
        system = DataFrameSystemFactory.get_system(df)

        # Execute filter through the system
        logger.debug(
            f"Executing filter: system={system.backend_type.name}, "
            f"input_type={input_type.name}"
        )
        return system.filter(df, expression)

    def filter(
        self,
        expression: Union[Any, Callable[["BaseTableBuilder"], Any]],
    ) -> "BaseTableBuilder":
        """
        Filter DataFrame rows by expression.

        Supports:
        - Native backend expressions (Polars Expr, pandas Series, Ibis column)
        - Mountainash expressions (automatically compiled against DataFrame)
        - Callable that receives the builder and returns an expression

        Args:
            expression: Filter expression or callable

        Returns:
            New TableBuilder with filtered rows

        Examples:
            # Native Polars expression
            table(df).filter(pl.col("value") > 100)

            # Lambda with column access
            table(df).filter(lambda t: t["value"] > 100)

            # Mountainash expression (auto-compiled)
            from mountainash.expressions import col
            table(df).filter(col("value").gt(100))

            # Complex mountainash expression
            table(df).filter(col("age").gt(30).and_(col("score").ge(85)))
        """
        resolved = self._resolve_expression(expression)
        result = self._apply_filter(resolved)
        return self._build(result)

    def where(
        self,
        expression: Union[Any, Callable[["BaseTableBuilder"], Any]],
    ) -> "BaseTableBuilder":
        """
        Alias for filter.

        Supports native, mountainash, and callable expressions.

        Args:
            expression: Filter expression or callable

        Returns:
            New TableBuilder with filtered rows

        Example:
            table(df).where(col("status").eq("active"))
        """
        return self.filter(expression)

    def query(
        self,
        expression: Union[Any, Callable[["BaseTableBuilder"], Any]],
    ) -> "BaseTableBuilder":
        """
        Alias for filter (pandas-style naming).

        Supports native, mountainash, and callable expressions.

        Args:
            expression: Filter expression or callable

        Returns:
            New TableBuilder with filtered rows

        Example:
            table(df).query(col("age").ge(18))
        """
        return self.filter(expression)

    def filter_by(self, column: str, value: Any) -> "BaseTableBuilder":
        """
        Filter rows where column equals value.

        Convenience method for simple equality filters.

        Args:
            column: Column name to filter on
            value: Value to match

        Returns:
            New TableBuilder with filtered rows

        Example:
            table(df).filter_by("status", "active")
        """
        # Use native column access for the comparison
        col_expr = self._df[column]

        # Create comparison based on backend type
        if hasattr(col_expr, "__eq__"):
            expression = col_expr == value
        else:
            expression = col_expr.eq(value)

        return self.filter(expression)

    def filter_not_null(self, column: str) -> "BaseTableBuilder":
        """
        Filter rows where column is not null.

        Args:
            column: Column name to check

        Returns:
            New TableBuilder with non-null rows

        Example:
            table(df).filter_not_null("email")
        """
        col_expr = self._df[column]

        # Handle different backends
        if hasattr(col_expr, "is_not_null"):
            expression = col_expr.is_not_null()
        elif hasattr(col_expr, "notna"):
            expression = col_expr.notna()
        elif hasattr(col_expr, "notnull"):
            expression = col_expr.notnull()
        else:
            raise NotImplementedError(
                f"filter_not_null not implemented for {type(col_expr)}"
            )

        return self.filter(expression)

    def filter_null(self, column: str) -> "BaseTableBuilder":
        """
        Filter rows where column is null.

        Args:
            column: Column name to check

        Returns:
            New TableBuilder with null rows

        Example:
            table(df).filter_null("optional_field")
        """
        col_expr = self._df[column]

        # Handle different backends
        if hasattr(col_expr, "is_null"):
            expression = col_expr.is_null()
        elif hasattr(col_expr, "isna"):
            expression = col_expr.isna()
        elif hasattr(col_expr, "isnull"):
            expression = col_expr.isnull()
        else:
            raise NotImplementedError(
                f"filter_null not implemented for {type(col_expr)}"
            )

        return self.filter(expression)
