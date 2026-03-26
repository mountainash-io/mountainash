"""Mountainash comparison extension protocol.

Mountainash Extension: Comparison
URI: file://extensions/functions_comparison.yaml

Extensions beyond Substrait standard:
- Short aliases: eq, ne, ge, le
- Polars-compatible: is_between
- Convenience: is_not_nan, clip
"""

from __future__ import annotations

from typing import Union, Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


class MountainAshScalarComparisonAPIBuilderProtocol(Protocol):
    """Builder protocol for Mountainash comparison extensions.

    These operations extend beyond the Substrait standard comparison
    functions to provide short aliases and Polars-compatible naming.
    """

    # Short aliases
    def eq(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Alias for equal()."""
        ...

    def ne(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Alias for not_equal()."""
        ...

    def ge(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Alias for gte()."""
        ...

    def le(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Alias for lte()."""
        ...

    # Polars-compatible aliases
    def is_between(
        self,
        low: Union[BaseExpressionAPI, ExpressionNode, Any],
        high: Union[BaseExpressionAPI, ExpressionNode, Any],
        closed: str = "both",
    ) -> BaseExpressionAPI:
        """Alias for between() — Polars compatibility."""
        ...

    # Convenience methods (AST-level composition)
    def is_not_nan(self) -> BaseExpressionAPI:
        """Whether value is not NaN. Equivalent to not_(is_nan())."""
        ...

    def clip(
        self,
        lower: Union[BaseExpressionAPI, ExpressionNode, Any, None] = None,
        upper: Union[BaseExpressionAPI, ExpressionNode, Any, None] = None,
    ) -> BaseExpressionAPI:
        """Clip values to a range."""
        ...

    # Null-safe comparison
    def eq_missing(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Null-safe equality: None == None returns True."""
        ...

    def ne_missing(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Null-safe inequality: None == None returns False."""
        ...

    def is_close(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], abs_tol: float = 1e-8, rel_tol: float = 1e-5) -> BaseExpressionAPI:
        """Whether two values are approximately equal."""
        ...
