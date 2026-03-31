"""Polars ScalarLogarithmicExpressionProtocol implementation.

Implements logarithmic operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarLogarithmicExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr

class SubstraitPolarsScalarLogarithmicExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarLogarithmicExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarLogarithmicExpressionProtocol.

    Implements 4 logarithmic methods:
    - ln: Natural logarithm (base e)
    - log10: Logarithm base 10
    - log2: Logarithm base 2
    - logb: Logarithm with arbitrary base
    """

    def ln(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> PolarsExpr:
        """Natural logarithm (base e).

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Natural log of x.
        """
        return x.log()

    def log10(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> PolarsExpr:
        """Logarithm base 10.

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Log base 10 of x.
        """
        return x.log(10)

    def log2(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> PolarsExpr:
        """Logarithm base 2.

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Log base 2 of x.
        """
        return x.log(2)

    def logb(
        self,
        x: PolarsExpr,
        /,
        base: PolarsExpr,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> PolarsExpr:
        """Logarithm with arbitrary base.

        logb(x, b) = log_b(x)

        Args:
            x: Value to take log of.
            base: Logarithm base.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Log base `base` of x.
        """
        base_val = self._extract_literal_value(base)
        if isinstance(base_val, (int, float)):
            return x.log(base_val)
        # Fallback: change of base formula for expression base
        return x.log() / base.log()

    def log1p(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> PolarsExpr:
        """Natural logarithm of (1 + x).

        log1p(x) = ln(1 + x)

        More accurate than log(1 + x) for small values of x.

        Args:
            x: Value to compute log1p of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Natural log of (1 + x).
        """
        return x.log1p()
