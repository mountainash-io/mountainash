"""Ibis ScalarLogarithmicExpressionProtocol implementation.

Implements logarithmic operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait import (
        ScalarLogarithmicExpressionProtocol,
    )

# Type alias for expression type
from mountainash_expressions.types import IbisExpr


class IbisScalarLogarithmicExpressionSystem(IbisBaseExpressionSystem, ScalarLogarithmicExpressionProtocol):
    """Ibis implementation of ScalarLogarithmicExpressionProtocol.

    Implements 4 logarithmic methods:
    - ln: Natural logarithm (base e)
    - log10: Logarithm base 10
    - log2: Logarithm base 2
    - logb: Logarithm with arbitrary base
    """

    def ln(
        self,
        x: IbisExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> IbisExpr:
        """Natural logarithm (base e).

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Natural log of x.
        """
        return x.ln()

    def log10(
        self,
        x: IbisExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> IbisExpr:
        """Logarithm base 10.

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Log base 10 of x.
        """
        return x.log10()

    def log2(
        self,
        x: IbisExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> IbisExpr:
        """Logarithm base 2.

        Args:
            x: Value to take log of.
            rounding: Rounding mode (ignored).
            on_domain_error: Domain error handling (ignored).
            on_log_zero: Log of zero handling (ignored).

        Returns:
            Log base 2 of x.
        """
        return x.log2()

    def logb(
        self,
        x: IbisExpr,
        /,
        base: IbisExpr,
        rounding: Any = None,
        on_domain_error: Any = None,
        on_log_zero: Any = None,
    ) -> IbisExpr:
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
        # Ibis has log(x, base)
        if isinstance(base, (int, float)):
            return x.log(base)
        # For expression base, use change of base formula
        return x.ln() / base.ln()
