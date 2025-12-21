"""Polars ScalarLogarithmicExpressionProtocol implementation.

Implements logarithmic operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from .base import PolarsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_logarithmic import (
        ScalarLogarithmicExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = pl.Expr


class PolarsScalarLogarithmicSystem(PolarsBaseExpressionSystem):
    """Polars implementation of ScalarLogarithmicExpressionProtocol.

    Implements 4 logarithmic methods:
    - ln: Natural logarithm (base e)
    - log10: Logarithm base 10
    - log2: Logarithm base 2
    - logb: Logarithm with arbitrary base
    """

    def ln(
        self,
        x: SupportedExpressions,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        /,
        base: SupportedExpressions,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> SupportedExpressions:
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
        # Polars log() accepts a base parameter
        # For expression base, we need to use change of base formula
        if isinstance(base, (int, float)):
            return x.log(base)
        # Change of base: log_b(x) = ln(x) / ln(b)
        return x.log() / base.log()
