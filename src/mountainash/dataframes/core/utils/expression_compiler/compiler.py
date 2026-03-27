"""
Mountainash expression compiler.

Compiles mountainash expressions (from mountainash-expressions package)
to native backend expressions based on the target DataFrame type.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compile_expression(expression: Any, dataframe: Any) -> Any:
    """
    Compile a mountainash expression against a DataFrame.

    The compilation target is determined by the DataFrame's backend:
    - Polars DataFrame/LazyFrame: compiles to pl.Expr
    - Ibis Table: compiles to ir.Expr
    - Narwhals DataFrame/LazyFrame: compiles to nw.Expr
    - pandas DataFrame: wraps in Narwhals, compiles to nw.Expr
    - PyArrow Table: wraps in Narwhals, compiles to nw.Expr

    Args:
        expression: Mountainash expression (BaseExpressionAPI or ExpressionNode).
                   Must have a `compile(dataframe)` method.
        dataframe: DataFrame to compile against (determines backend)

    Returns:
        Compiled native expression (pl.Expr, nw.Expr, ir.Expr, etc.)

    Raises:
        TypeError: If expression doesn't have a compile method
        ImportError: If narwhals is required but not installed
    """
    if not hasattr(expression, "compile"):
        raise TypeError(
            f"Cannot compile expression of type {type(expression).__name__}. "
            f"Expected mountainash expression with compile() method. "
            f"Use mountainash_expressions API (e.g., col('x').gt(5)) instead of raw nodes."
        )

    df_type = type(dataframe)
    module = df_type.__module__

    # Polars/Ibis/Narwhals - compile directly against native DataFrame
    if module.startswith(("polars", "ibis", "narwhals")):
        logger.debug(f"Compiling expression directly against {module} DataFrame")
        return expression.compile(dataframe)

    # pandas/PyArrow - wrap in Narwhals first, compile to nw.Expr
    if module.startswith(("pandas", "pyarrow")):
        try:
            import narwhals as nw

            wrapped_df = nw.from_native(dataframe, eager_only=True)
            compiled = expression.compile(wrapped_df)
            logger.debug(f"Compiled to {type(compiled).__name__} via Narwhals wrapping")
            return compiled
        except ImportError:
            raise ImportError(
                "narwhals is required to use mountainash-expressions with pandas/pyarrow DataFrames. "
                "Install with: pip install narwhals"
            )

    # Unknown backend - try direct compilation
    logger.debug(f"Unknown backend {module}, attempting direct compilation")
    return expression.compile(dataframe)


__all__ = ["compile_expression"]
