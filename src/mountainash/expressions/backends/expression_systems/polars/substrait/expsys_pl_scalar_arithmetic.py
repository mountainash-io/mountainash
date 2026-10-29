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

    Omitted options use native Polars behavior. Explicit rounding is unsupported.
    Integer overflow modes are validated here; native wrapping is available as
    SILENT except for division, which has no implemented integer overflow mode.
    """

    def add(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Omit it or use SILENT for native Polars integer wrapping.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.

        Returns:
            Sum of x and y.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports SILENT overflow handling. Omit overflow or use SILENT for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            )
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            )
        return x + y

    def subtract(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Omit it or use SILENT for native Polars integer wrapping.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.

        Returns:
            Difference x - y.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports SILENT overflow handling. Omit overflow or use SILENT for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            )
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            )
        return x - y

    def multiply(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Omit it or use SILENT for native Polars integer wrapping.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.

        Returns:
            Product of x and y.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports SILENT overflow handling. Omit overflow or use SILENT for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            )
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            )
        return x * y

    def divide(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Explicit overflow handling is unsupported; omit it for native Polars behavior.
            on_domain_error: Omit it or use NAN for native Polars behavior.
            on_division_by_zero: Omit it or use IEEE for native Polars behavior.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.

        Returns:
            Quotient x / y.
        """
        if overflow is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit overflow handling. Omit overflow to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if on_domain_error is not None and on_domain_error != "NAN":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports NAN domain-error handling. Omit on_domain_error or use NAN for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if on_division_by_zero is not None and on_division_by_zero != "IEEE":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports IEEE division-by-zero handling. Omit on_division_by_zero or use IEEE for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
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
            division_type: Omit it or use FLOOR for native Polars behavior.
            overflow: Omit it or use SILENT for native Polars integer wrapping.
            on_domain_error: ERROR is unavailable; otherwise native remainder behavior.

        Returns:
            Remainder of x / y.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports SILENT overflow handling. Omit overflow or use SILENT for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
        if division_type is not None and division_type != "FLOOR":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports FLOOR remainder division mode. Omit division_type or use FLOOR for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
        if on_domain_error == "ERROR":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars remainder cannot raise on domain errors.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
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
            overflow: Omit it or use SILENT for native Polars integer wrapping.

        Returns:
            x raised to the power y.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports SILENT overflow handling. Omit overflow or use SILENT for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
            )
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
            overflow: Omit it or use SILENT for native Polars integer wrapping.

        Returns:
            Negated value (-x).
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports SILENT overflow handling. Omit overflow or use SILENT for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
            )
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
        """Square root of the value.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
            on_domain_error: Omit it or use NAN for native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            )
        if on_domain_error is not None and on_domain_error != "NAN":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports NAN domain-error handling. Omit on_domain_error or use NAN for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            )
        return x.sqrt()

    def exp(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """The mathematical constant e raised to the power of x.

        Args:
            x: Exponent value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
            )
        return x.exp()

    def abs(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Calculate the absolute value.

        Args:
            x: Input value.
            overflow: Omit it or use SILENT for native Polars integer wrapping.
        """
        if overflow is not None and overflow != "SILENT":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports SILENT overflow handling. Omit overflow or use SILENT for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            )
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

        Args:
            n: Integer input.
            overflow: Overflow mode (ignored in Polars).

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
        """Get the sine of a value in radians.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
            )
        return x.sin()

    def cos(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the cosine of a value in radians.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
            )
        return x.cos()

    def tan(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the tangent of a value in radians.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
            )
        return x.tan()

    def sinh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic sine of a value.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH,
            )
        return x.sinh()

    def cosh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic cosine of a value.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH,
            )
        return x.cosh()

    def tanh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic tangent of a value.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH,
            )
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
        """Get the arcsine of a value in radians.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
            on_domain_error: Omit it or use NAN for native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
            )
        if on_domain_error is not None and on_domain_error != "NAN":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports NAN domain-error handling. Omit on_domain_error or use NAN for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
            )
        return x.arcsin()

    def acos(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the arccosine of a value in radians.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
            on_domain_error: Omit it or use NAN for native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
            )
        if on_domain_error is not None and on_domain_error != "NAN":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports NAN domain-error handling. Omit on_domain_error or use NAN for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
            )
        return x.arccos()

    def atan(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the arctangent of a value in radians.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
            )
        return x.arctan()

    def asinh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic arcsine of a value.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH,
            )
        return x.arcsinh()

    def acosh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic arccosine of a value.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
            on_domain_error: Omit it or use NAN for native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
            )
        if on_domain_error is not None and on_domain_error != "NAN":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports NAN domain-error handling. Omit on_domain_error or use NAN for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH,
            )
        return x.arccosh()

    def atanh(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the hyperbolic arctangent of a value.

        Args:
            x: Input value.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
            on_domain_error: Omit it or use NAN for native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
            )
        if on_domain_error is not None and on_domain_error != "NAN":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports NAN domain-error handling. Omit on_domain_error or use NAN for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH,
            )
        return x.arctanh()

    def atan2(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        rounding: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Get the arctangent of y/x, using signs to determine the quadrant.

        Args:
            x: First coordinate.
            y: Second coordinate.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
            on_domain_error: Omit it or use NAN for native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
            )
        if on_domain_error is not None and on_domain_error != "NAN":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars only supports NAN domain-error handling. Omit on_domain_error or use NAN for native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
            )
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
        """Convert angle from degrees to radians.

        Args:
            x: Input angle.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
            )
        return x.radians()

    def degrees(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Convert angle from radians to degrees.

        Args:
            x: Input angle.
            rounding: Explicit rounding is unsupported; omit it to use native Polars behavior.
        """
        if rounding is not None:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

            raise BackendCapabilityError(
                "Polars does not support explicit rounding. Omit rounding to use native Polars behavior.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
            )
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
        return ~x

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
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "Polars does not support bitwise shift_left. Use Ibis backend for shift operations.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_LEFT,
        )

    def shift_right(
        self,
        base: PolarsExpr,
        shift: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Bitwise signed shift right."""
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "Polars does not support bitwise shift_right. Use Ibis backend for shift operations.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT,
        )

    def shift_right_unsigned(
        self,
        base: PolarsExpr,
        shift: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Bitwise unsigned shift right."""
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        raise BackendCapabilityError(
            "No backend supports bitwise shift_right_unsigned.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED,
        )
