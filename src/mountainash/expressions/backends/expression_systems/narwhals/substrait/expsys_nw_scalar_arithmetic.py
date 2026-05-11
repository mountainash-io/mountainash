"""Narwhals ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarArithmeticExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr



class SubstraitNarwhalsScalarArithmeticExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarArithmeticExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of ScalarArithmeticExpressionProtocol.

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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Sum of x and y.
        """
        return x + y

    def subtract(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Difference x - y.
        """
        return x - y

    def multiply(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Product of x and y.
        """
        return x * y

    def divide(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
    ) -> NarwhalsExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Overflow handling (ignored in Narwhals).
            on_domain_error: Domain error handling (ignored in Narwhals).
            on_division_by_zero: Division by zero handling (ignored in Narwhals).

        Returns:
            Quotient x / y.
        """
        return x / y

    def modulus(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        division_type: Any = None,
        overflow: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Calculate the remainder when dividing x by y.

        Args:
            x: Dividend.
            y: Divisor.
            division_type: TRUNCATE or FLOOR (Narwhals uses backend default).
            overflow: Overflow handling (ignored in Narwhals).
            on_domain_error: Domain error handling (ignored in Narwhals).

        Returns:
            Remainder of x / y.
        """
        return x % y

    def power(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Raise x to the power of y.

        Args:
            x: Base.
            y: Exponent.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            x raised to the power y.
        """
        return x ** y

    def negate(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Negate a value.

        Args:
            x: Value to negate.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Negated value (-x).
        """
        return x * nw.lit(-1)

    # =========================================================================
    # Math Functions
    # =========================================================================

    def sqrt(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Square root of the value."""
        raise NotImplementedError(
            "sqrt() is not supported by the Narwhals backend."
        )

    def exp(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """The mathematical constant e raised to the power of x."""
        raise NotImplementedError(
            "exp() is not supported by the Narwhals backend."
        )

    def abs(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Calculate the absolute value."""
        return x.abs()

    def sign(
        self,
        x: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Return the sign of the value (-1, 0, or 1)."""
        raise NotImplementedError(
            "sign() is not supported by the Narwhals backend."
        )

    def factorial(
        self,
        n: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Return the factorial of a given integer input."""
        raise NotImplementedError(
            "factorial() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Trigonometric Functions
    # =========================================================================

    def sin(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the sine of a value in radians."""
        raise NotImplementedError(
            "sin() is not supported by the Narwhals backend."
        )

    def cos(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the cosine of a value in radians."""
        raise NotImplementedError(
            "cos() is not supported by the Narwhals backend."
        )

    def tan(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the tangent of a value in radians."""
        raise NotImplementedError(
            "tan() is not supported by the Narwhals backend."
        )

    def sinh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic sine of a value."""
        raise NotImplementedError(
            "sinh() is not supported by the Narwhals backend."
        )

    def cosh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic cosine of a value."""
        raise NotImplementedError(
            "cosh() is not supported by the Narwhals backend."
        )

    def tanh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic tangent of a value."""
        raise NotImplementedError(
            "tanh() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Inverse Trigonometric Functions
    # =========================================================================

    def asin(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Get the arcsine of a value in radians."""
        raise NotImplementedError(
            "asin() is not supported by the Narwhals backend."
        )

    def acos(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Get the arccosine of a value in radians."""
        raise NotImplementedError(
            "acos() is not supported by the Narwhals backend."
        )

    def atan(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the arctangent of a value in radians."""
        raise NotImplementedError(
            "atan() is not supported by the Narwhals backend."
        )

    def asinh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic arcsine of a value."""
        raise NotImplementedError(
            "asinh() is not supported by the Narwhals backend."
        )

    def acosh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic arccosine of a value."""
        raise NotImplementedError(
            "acosh() is not supported by the Narwhals backend."
        )

    def atanh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic arctangent of a value."""
        raise NotImplementedError(
            "atanh() is not supported by the Narwhals backend."
        )

    def atan2(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Get the arctangent of y/x, using the signs to determine the quadrant."""
        raise NotImplementedError(
            "atan2() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Angular Conversions
    # =========================================================================

    def radians(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Convert angle from degrees to radians."""
        raise NotImplementedError(
            "radians() is not supported by the Narwhals backend."
        )

    def degrees(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Convert angle from radians to degrees."""
        raise NotImplementedError(
            "degrees() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Bitwise Operations
    # =========================================================================

    def bitwise_not(
        self,
        x: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Return the bitwise NOT of an integer."""
        return ~x

    def bitwise_and(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Return the bitwise AND of two integers."""
        return x & y

    def bitwise_or(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Return the bitwise OR of two integers."""
        return x | y

    def bitwise_xor(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Return the bitwise XOR of two integers."""
        return x ^ y

    def shift_left(
        self,
        base: NarwhalsExpr,
        shift: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Bitwise shift left."""
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "Narwhals does not support bitwise shift_left. Use Ibis backend for shift operations.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_LEFT,
        )

    def shift_right(
        self,
        base: NarwhalsExpr,
        shift: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Bitwise signed shift right."""
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "Narwhals does not support bitwise shift_right. Use Ibis backend for shift operations.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT,
        )

    def shift_right_unsigned(
        self,
        base: NarwhalsExpr,
        shift: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Bitwise unsigned shift right."""
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "No backend supports bitwise shift_right_unsigned.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED,
        )
