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

    Omitted options use native Narwhals behavior. Explicit rounding is unsupported.
    Integer overflow modes are validated here; native wrapping is available as
    SILENT except for division, which has no implemented integer overflow mode.
    """

    def add(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Omitted or SILENT uses native integer wrapping.
            rounding: Unsupported when explicit; omission uses native rounding.

        Returns:
            Sum of x and y.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support add() with rounding.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            )
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support add() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            )
        return x + y

    def subtract(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Omitted or SILENT uses native integer wrapping.
            rounding: Unsupported when explicit; omission uses native rounding.

        Returns:
            Difference x - y.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support subtract() with rounding.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            )
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support subtract() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            )
        return x - y

    def multiply(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Omitted or SILENT uses native integer wrapping.
            rounding: Unsupported when explicit; omission uses native rounding.

        Returns:
            Product of x and y.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support multiply() with rounding.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            )
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support multiply() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            )
        return x * y

    def divide(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero. Omitted
        options preserve native Narwhals lowering.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Unsupported when explicit.
            on_domain_error: NAN on Narwhals Polars/Lazy or NULL on Narwhals
                Pandas; otherwise omit for native behavior.
            on_division_by_zero: IEEE on Narwhals Polars/Lazy; otherwise omit
                for native behavior.
            rounding: Unsupported when explicit; omission uses native rounding.

        Returns:
            Quotient x / y.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support divide() with rounding.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if overflow is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support divide() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if on_domain_error is not None and not (
            on_domain_error == "NAN"
            and self.dialect in ("narwhals-polars", "narwhals-lazy")
            or on_domain_error == "NULL" and self.dialect == "narwhals-pandas"
        ):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "The selected Narwhals dialect does not implement this division "
                "domain-error mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if on_division_by_zero is not None and not (
            on_division_by_zero == "IEEE"
            and self.dialect in ("narwhals-polars", "narwhals-lazy")
        ):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "The selected Narwhals dialect does not implement this "
                "division-by-zero mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
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

        Omitted options preserve native Narwhals lowering.

        Args:
            x: Dividend.
            y: Divisor.
            division_type: Omit for native remainder behavior, or use FLOOR.
            overflow: Omitted or SILENT uses native integer wrapping.
            on_domain_error: ERROR is unavailable; otherwise native remainder behavior.

        Returns:
            Remainder of x / y.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support modulus() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
        if division_type is not None and division_type != "FLOOR":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support modulus() with this division type.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
        if on_domain_error == "ERROR":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Narwhals remainder cannot raise on domain errors.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
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
            overflow: Omitted or SILENT uses native integer wrapping.

        Returns:
            x raised to the power y.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support power() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
            )
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
            overflow: Omitted or SILENT uses native integer wrapping.

        Returns:
            Negated value (-x).
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support negate() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
            )
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
        """Square root of the value.

        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
            on_domain_error: NAN on Narwhals Polars/Lazy; otherwise omit for
                native behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support sqrt() with rounding.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            )
        if on_domain_error is not None and not (
            on_domain_error == "NAN"
            and self.dialect in ("narwhals-polars", "narwhals-lazy")
        ):
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "The selected Narwhals dialect does not implement this "
                "square-root domain-error mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            )
        return x.sqrt()

    def exp(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """The mathematical constant e raised to the power of x.

        Args:
            x: Exponent value.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support exp() with rounding.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
            )
        return x.exp()

    def abs(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Calculate the absolute value.

        Args:
            x: Input value.
            overflow: Omitted or SILENT uses native integer wrapping.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
            raise BackendCapabilityError(
                "Narwhals does not support abs() with overflow.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            )
        return x.abs()

    def sign(
        self,
        x: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Return the sign of the value (-1, 0, or 1)."""
        import narwhals as nw
        return (x > 0).cast(nw.Int64) - (x < 0).cast(nw.Int64)

    def factorial(
        self,
        n: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Return the factorial of a given integer input.

        Args:
            n: Integer input.
            overflow: Overflow mode (ignored in Narwhals).
        """
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
        """Get the sine of a value in radians.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
        raise NotImplementedError(
            "sin() is not supported by the Narwhals backend."
        )

    def cos(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the cosine of a value in radians.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
        raise NotImplementedError(
            "cos() is not supported by the Narwhals backend."
        )

    def tan(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the tangent of a value in radians.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
        raise NotImplementedError(
            "tan() is not supported by the Narwhals backend."
        )

    def sinh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic sine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
        raise NotImplementedError(
            "sinh() is not supported by the Narwhals backend."
        )

    def cosh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic cosine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
        raise NotImplementedError(
            "cosh() is not supported by the Narwhals backend."
        )

    def tanh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic tangent of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
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
        """Get the arcsine of a value in radians.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
            on_domain_error: Domain error policy (ignored in Narwhals).
        """
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
        """Get the arccosine of a value in radians.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
            on_domain_error: Domain error policy (ignored in Narwhals).
        """
        raise NotImplementedError(
            "acos() is not supported by the Narwhals backend."
        )

    def atan(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the arctangent of a value in radians.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
        raise NotImplementedError(
            "atan() is not supported by the Narwhals backend."
        )

    def asinh(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Get the hyperbolic arcsine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
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
        """Get the hyperbolic arccosine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
            on_domain_error: Domain error policy (ignored in Narwhals).
        """
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
        """Get the hyperbolic arctangent of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Narwhals).
            on_domain_error: Domain error policy (ignored in Narwhals).
        """
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
        """Get the arctangent of y/x, using signs to determine the quadrant.

        Args:
            x: First coordinate.
            y: Second coordinate.
            rounding: IEEE rounding mode (ignored in Narwhals).
            on_domain_error: Domain error policy (ignored in Narwhals).
        """
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
        """Convert angle from degrees to radians.

        Args:
            x: Input angle.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
        raise NotImplementedError(
            "radians() is not supported by the Narwhals backend."
        )

    def degrees(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Convert angle from radians to degrees.

        Args:
            x: Input angle.
            rounding: IEEE rounding mode (ignored in Narwhals).
        """
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
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "Narwhals does not support bitwise_xor. Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.BITWISE_XOR,
        )

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
