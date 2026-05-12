"""Ibis ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING


from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarArithmeticExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisNumericExpr


class SubstraitIbisScalarArithmeticExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarArithmeticExpressionSystemProtocol["IbisNumericExpr"]):
    """Ibis implementation of ScalarArithmeticExpressionProtocol.

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
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Sum of x and y.
        """
        return x + y

    def subtract(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Difference x - y.
        """
        return x - y

    def multiply(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Product of x and y.
        """
        return x * y

    def divide(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
    ) -> IbisNumericExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Overflow handling (ignored in Ibis).
            on_domain_error: Domain error handling (ignored in Ibis).
            on_division_by_zero: Division by zero handling (ignored in Ibis).

        Returns:
            Quotient x / y.
        """
        return x / y

    def modulus(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
        division_type: Any = None,
        overflow: Any = None,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Calculate the remainder when dividing x by y.

        Args:
            x: Dividend.
            y: Divisor.
            division_type: TRUNCATE or FLOOR (Ibis uses backend default).
            overflow: Overflow handling (ignored in Ibis).
            on_domain_error: Domain error handling (ignored in Ibis).

        Returns:
            Remainder of x / y.
        """
        return x % y

    def power(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Raise x to the power of y.

        Args:
            x: Base.
            y: Exponent.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            x raised to the power y.
        """
        return x.pow(y)

    def negate(
        self,
        x: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Negate a value.

        Args:
            x: Value to negate.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Negated value (-x).
        """
        return -x

    # =========================================================================
    # Math Functions
    # =========================================================================

    def sqrt(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Square root of the value."""
        return x.sqrt()

    def exp(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """The mathematical constant e raised to the power of x."""
        return x.exp()

    def abs(
        self,
        x: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Calculate the absolute value."""
        return x.abs()

    def sign(
        self,
        x: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Return the sign of the value (-1, 0, or 1)."""
        return x.sign()

    def factorial(
        self,
        n: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Return the factorial of a given integer input."""
        raise NotImplementedError(
            "factorial() is not supported by the Ibis backend."
        )

    # =========================================================================
    # Trigonometric Functions
    # =========================================================================

    def sin(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the sine of a value in radians."""
        return x.sin()

    def cos(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the cosine of a value in radians."""
        return x.cos()

    def tan(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the tangent of a value in radians."""
        return x.tan()

    def sinh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic sine of a value."""
        raise NotImplementedError(
            "sinh() is not directly supported by the Ibis backend."
        )

    def cosh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic cosine of a value."""
        raise NotImplementedError(
            "cosh() is not directly supported by the Ibis backend."
        )

    def tanh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic tangent of a value."""
        raise NotImplementedError(
            "tanh() is not directly supported by the Ibis backend."
        )

    # =========================================================================
    # Inverse Trigonometric Functions
    # =========================================================================

    def asin(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Get the arcsine of a value in radians."""
        return x.asin()

    def acos(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Get the arccosine of a value in radians."""
        return x.acos()

    def atan(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the arctangent of a value in radians."""
        return x.atan()

    def asinh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic arcsine of a value."""
        raise NotImplementedError(
            "asinh() is not directly supported by the Ibis backend."
        )

    def acosh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic arccosine of a value."""
        raise NotImplementedError(
            "acosh() is not directly supported by the Ibis backend."
        )

    def atanh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic arctangent of a value."""
        raise NotImplementedError(
            "atanh() is not directly supported by the Ibis backend."
        )

    def atan2(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Get the arctangent of y/x, using the signs to determine the quadrant."""
        return x.atan2(y)

    # =========================================================================
    # Angular Conversions
    # =========================================================================

    def radians(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Convert angle from degrees to radians."""
        return x.radians()

    def degrees(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Convert angle from radians to degrees."""
        return x.degrees()

    # =========================================================================
    # Bitwise Operations
    # =========================================================================

    def bitwise_not(
        self,
        x: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Return the bitwise NOT of an integer."""
        return ~x

    def bitwise_and(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Return the bitwise AND of two integers."""
        return x & y

    def bitwise_or(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Return the bitwise OR of two integers."""
        return x | y

    def bitwise_xor(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Return the bitwise XOR of two integers."""
        return x ^ y

    def shift_left(
        self,
        base: IbisNumericExpr,
        shift: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Bitwise shift left."""
        return base << shift

    def shift_right(
        self,
        base: IbisNumericExpr,
        shift: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Bitwise signed shift right."""
        return base >> shift

    def shift_right_unsigned(
        self,
        base: IbisNumericExpr,
        shift: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Bitwise unsigned shift right."""
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "No backend supports bitwise shift_right_unsigned.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED,
        )
