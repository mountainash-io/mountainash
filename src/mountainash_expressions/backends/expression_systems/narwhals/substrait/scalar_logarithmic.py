"""Narwhals ScalarLogarithmicExpressionProtocol implementation.

Implements logarithmic operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait import (
        ScalarLogarithmicExpressionProtocol,
    )

if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr


class NarwhalsScalarLogarithmicExpressionSystem(NarwhalsBaseExpressionSystem, ScalarLogarithmicExpressionProtocol):
    """Narwhals implementation of ScalarLogarithmicExpressionProtocol.

    Implements 4 logarithmic methods:
    - ln: Natural logarithm (base e)
    - log10: Logarithm base 10
    - log2: Logarithm base 2
    - logb: Logarithm with arbitrary base
    """

    def ln(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> NarwhalsExpr:
        """Logarithm base 10.

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Log base 10 of x.
        """
        # Use change of base formula: log10(x) = ln(x) / ln(10)
        return x.log() / nw.lit(2.302585092994046)  # ln(10)

    def log2(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> NarwhalsExpr:
        """Logarithm base 2.

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Log base 2 of x.
        """
        # Use change of base formula: log2(x) = ln(x) / ln(2)
        return x.log() / nw.lit(0.6931471805599453)  # ln(2)

    def logb(
        self,
        x: NarwhalsExpr,
        /,
        base: NarwhalsExpr,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> NarwhalsExpr:
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
        # Change of base formula: log_b(x) = ln(x) / ln(b)
        if isinstance(base, (int, float)):
            import math
            return x.log() / nw.lit(math.log(base))
        # For expression base
        return x.log() / base.log()
