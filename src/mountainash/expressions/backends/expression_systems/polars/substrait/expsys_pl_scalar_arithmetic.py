"""Polars ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarArithmeticExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsScalarArithmeticExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarArithmeticExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarArithmeticExpressionProtocol.

    Implements 7 arithmetic methods:
    - add: Addition
    - subtract: Subtraction
    - multiply: Multiplication
    - divide: Division
    - modulus: Modulo/remainder
    - power: Exponentiation
    - negate: Negation
    """

    def add(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Sum of x and y.
        """
        return x + y

    def subtract(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Difference x - y.
        """
        return x - y

    def multiply(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Product of x and y.
        """
        return x * y

    def divide(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
    ) -> PolarsExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Overflow handling (ignored in Polars).
            on_domain_error: Domain error handling (ignored in Polars).
            on_division_by_zero: Division by zero handling (ignored in Polars).

        Returns:
            Quotient x / y.
        """
        return x / y

    def modulus(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        division_type: Any = None,
        overflow: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Calculate the remainder when dividing x by y.

        Args:
            x: Dividend.
            y: Divisor.
            division_type: TRUNCATE or FLOOR (Polars uses TRUNCATE by default).
            overflow: Overflow handling (ignored in Polars).
            on_domain_error: Domain error handling (ignored in Polars).

        Returns:
            Remainder of x / y.
        """
        return x % y

    def power(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Raise x to the power of y.

        Args:
            x: Base.
            y: Exponent.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            x raised to the power y.
        """
        return x.pow(y)

    def negate(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Negate a value.

        Args:
            x: Value to negate.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Negated value (-x).
        """
        return -x

    # =========================================================================
    # Math Functions
    # =========================================================================

    def sqrt(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Square root of the value."""
        return x.sqrt()

    def exp(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """The mathematical constant e raised to the power of x."""
        return x.exp()

    def abs(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Calculate the absolute value."""
        return x.abs()

    def sign(
        self,
        x: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Return the sign of the value (-1, 0, or 1)."""
        return x.sign()

    def factorial(
        self,
        n: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Return the factorial of a given integer input.

        Note: Polars does not have native factorial support.
        """
        raise NotImplementedError(
            "factorial() is not supported by the Polars backend. "
            "Consider using a UDF or pre-computing factorial values."
        )

    # =========================================================================
    # Trigonometric Functions
    # =========================================================================

    def sin(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the sine of a value in radians."""
        return x.sin()

    def cos(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the cosine of a value in radians."""
        return x.cos()

    def tan(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the tangent of a value in radians."""
        return x.tan()

    def sinh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic sine of a value."""
        return x.sinh()

    def cosh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic cosine of a value."""
        return x.cosh()

    def tanh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic tangent of a value."""
        return x.tanh()

    # =========================================================================
    # Inverse Trigonometric Functions
    # =========================================================================

    def asin(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the arcsine of a value in radians."""
        return x.arcsin()

    def acos(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the arccosine of a value in radians."""
        return x.arccos()

    def atan(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the arctangent of a value in radians."""
        return x.arctan()

    def asinh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic arcsine of a value."""
        return x.arcsinh()

    def acosh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic arccosine of a value."""
        return x.arccosh()

    def atanh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic arctangent of a value."""
        return x.arctanh()

    def atan2(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the arctangent of y/x, using the signs to determine the quadrant."""
        return pl.arctan2(x, y)

    # =========================================================================
    # Angular Conversions
    # =========================================================================

    def radians(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Convert angle from degrees to radians."""
        return x.radians()

    def degrees(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Convert angle from radians to degrees."""
        return x.degrees()

    # =========================================================================
    # Bitwise Operations
    # =========================================================================

    def bitwise_not(
        self,
        x: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Return the bitwise NOT of an integer."""
        raise NotImplementedError(
            "bitwise_not() is not directly supported by the Polars backend. "
            "Consider using XOR with -1 or a custom implementation."
        )

    def bitwise_and(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Return the bitwise AND of two integers."""
        return x & y

    def bitwise_or(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Return the bitwise OR of two integers."""
        return x | y

    def bitwise_xor(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Return the bitwise XOR of two integers."""
        return x ^ y

    def shift_left(
        self,
        base: PolarsExpr,
        shift: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Bitwise shift left."""
        raise NotImplementedError(
            "shift_left() is not directly supported by the Polars backend. "
            "Consider using multiplication by powers of 2."
        )

    def shift_right(
        self,
        base: PolarsExpr,
        shift: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Bitwise signed shift right."""
        raise NotImplementedError(
            "shift_right() is not directly supported by the Polars backend. "
            "Consider using floor division by powers of 2."
        )

    def shift_right_unsigned(
        self,
        base: PolarsExpr,
        shift: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Bitwise unsigned shift right."""
        raise NotImplementedError(
            "shift_right_unsigned() is not directly supported by the Polars backend."
        )
