"""Ibis ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING


from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarArithmeticExpressionSystemProtocol
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

if TYPE_CHECKING:
    from mountainash.core.types import IbisNumericExpr


def _sqlite_abs_error(x: IbisNumericExpr) -> IbisNumericExpr:
    dtype = x.type()
    if dtype.is_integer() and not dtype.is_int64():

        raise BackendCapabilityError(
            f"SQLite ABS cannot enforce overflow=ERROR for declared {dtype}; "
            "use Int64 operands or an engine preserving that integer width.",
            backend="ibis",
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
        )
    return x.abs()


def _modulus_null(result: IbisNumericExpr) -> IbisNumericExpr:
    if result.type().is_floating():
        raise BackendCapabilityError(
            "Ibis floating remainder does not implement on_domain_error=NULL for zero and infinite operands.",
            backend="ibis",
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
        )
    return result


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

    Omitted options use native Ibis behavior. Explicit rounding is unsupported.
    Integer overflow validation belongs to these methods and uses the bound
    engine's implemented modes, not optional capability policy.
    """

    def add(self,
    x: IbisNumericExpr,
    y: IbisNumericExpr,
    /,
    overflow: Any = None,
    rounding: Any = None,) -> IbisNumericExpr:
        """Add two values.
    
        Args:
            x: First operand.
            y: Second operand.
            overflow: ERROR on DuckDB, SILENT on Polars; otherwise omit.
            rounding: Unsupported when explicit; omission uses native rounding.
    
        Returns:
            Sum of x and y.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            )
        if overflow is not None and not (
            overflow == "ERROR" and self.dialect == "ibis-duckdb"
            or overflow == "SILENT" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this integer overflow mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            )
        x, y = self._lift_deferred(x, y)
        return x + y

    def subtract(self,
    x: IbisNumericExpr,
    y: IbisNumericExpr,
    /,
    overflow: Any = None,
    rounding: Any = None,) -> IbisNumericExpr:
        """Subtract y from x.
    
        Args:
            x: First operand.
            y: Second operand.
            overflow: ERROR on DuckDB, SILENT on Polars; otherwise omit.
            rounding: Unsupported when explicit; omission uses native rounding.
    
        Returns:
            Difference x - y.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            )
        if overflow is not None and not (
            overflow == "ERROR" and self.dialect == "ibis-duckdb"
            or overflow == "SILENT" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this integer overflow mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            )
        x, y = self._lift_deferred(x, y)
        return x - y

    def multiply(self,
    x: IbisNumericExpr,
    y: IbisNumericExpr,
    /,
    overflow: Any = None,
    rounding: Any = None,) -> IbisNumericExpr:
        """Multiply two values.
    
        Args:
            x: First operand.
            y: Second operand.
            overflow: ERROR on DuckDB, SILENT on Polars; otherwise omit.
            rounding: Unsupported when explicit; omission uses native rounding.
    
        Returns:
            Product of x and y.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            )
        if overflow is not None and not (
            overflow == "ERROR" and self.dialect == "ibis-duckdb"
            or overflow == "SILENT" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this integer overflow mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            )
        x, y = self._lift_deferred(x, y)
        return x * y

    def divide(self,
    x: IbisNumericExpr,
    y: IbisNumericExpr,
    /,
    overflow: Any = None,
    on_domain_error: Any = None,
    on_division_by_zero: Any = None,
    rounding: Any = None,) -> IbisNumericExpr:
        """Divide x by y.
    
        Native Ibis division produces a floating-point quotient.
    
        Args:
            x: Dividend.
            y: Divisor.
            overflow: Unsupported when explicit; omission uses native behavior.
            on_domain_error: NAN on DuckDB/Polars, NULL on SQLite; otherwise omit.
            on_division_by_zero: IEEE on DuckDB/Polars, NULL on SQLite; otherwise omit.
            rounding: Unsupported when explicit; omission uses native rounding.
    
        Returns:
            Quotient x / y.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if overflow is not None:
            raise BackendCapabilityError(
                "Ibis divide does not implement integer overflow modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if on_domain_error is not None and not (
            on_domain_error == "NAN" and self.dialect in ("ibis-duckdb", "ibis-polars")
            or on_domain_error == "NULL" and self.dialect == "ibis-sqlite"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this division domain-error mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        if on_division_by_zero is not None and not (
            on_division_by_zero == "IEEE" and self.dialect in ("ibis-duckdb", "ibis-polars")
            or on_division_by_zero == "NULL" and self.dialect == "ibis-sqlite"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this division-by-zero mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            )
        x, y = self._lift_deferred(x, y)
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
            division_type: TRUNCATE on DuckDB/SQLite, FLOOR on Polars; otherwise omit.
            overflow: ERROR on DuckDB, SILENT on Polars; otherwise omit.
            on_domain_error: NULL for non-floating remainder; ERROR is unavailable.

        Returns:
            Remainder of x / y.
        """
        if overflow is not None and not (
            overflow == "ERROR" and self.dialect == "ibis-duckdb"
            or overflow == "SILENT" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this integer overflow mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
        if division_type is not None and not (
            division_type == "TRUNCATE" and self.dialect in ("ibis-duckdb", "ibis-sqlite")
            or division_type == "FLOOR" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this remainder division mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
        if on_domain_error is not None and on_domain_error != "NULL":
            raise BackendCapabilityError(
                "Ibis remainder cannot raise on domain errors.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            )
        x, y = self._lift_deferred(x, y)
        result = x % y
        return result.pipe(_modulus_null) if on_domain_error == "NULL" else result

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
            overflow: Unsupported when explicit; omission uses native behavior.

        Returns:
            x raised to the power y.
        """
        if overflow is not None:
            raise BackendCapabilityError(
                "Ibis power does not implement integer overflow modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
            )
        x, y = self._lift_deferred(x, y)
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
            overflow: ERROR on DuckDB, SILENT on Polars; otherwise omit.

        Returns:
            Negated value (-x).
        """
        if overflow is not None and not (
            overflow == "ERROR" and self.dialect == "ibis-duckdb"
            or overflow == "SILENT" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this integer overflow mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
            )
        return -x

    # =========================================================================
    # Math Functions
    # =========================================================================

    def sqrt(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,
    on_domain_error: Any = None,) -> IbisNumericExpr:
        """Square root of the value.
    
        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
            on_domain_error: ERROR on DuckDB, NAN on Polars; otherwise omit.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            )
        if on_domain_error is not None and not (
            on_domain_error == "ERROR" and self.dialect == "ibis-duckdb"
            or on_domain_error == "NAN" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this square-root domain-error mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            )
        return x.sqrt()

    def exp(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,) -> IbisNumericExpr:
        """The mathematical constant e raised to the power of x.
    
        Args:
            x: Exponent value.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
            )
        return x.exp()

    def abs(
        self,
        x: IbisNumericExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericExpr:
        """Calculate the absolute value.

        Args:
            x: Input value.
            overflow: Native overflow mode; SQLite ERROR requires Int64 integer operands.
        """
        if overflow == "ERROR" and self.dialect == "ibis-sqlite":
            # Ibis Deferred.pipe resolves the operand before inspecting its
            # declared type, without evaluating rows or guessing table storage.
            return x.pipe(_sqlite_abs_error)
        if overflow is not None and not (
            overflow == "ERROR" and self.dialect == "ibis-duckdb"
            or overflow == "SILENT" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this integer overflow mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            )
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
        """Return the factorial of a given integer input.

        Args:
            n: Integer input.
            overflow: Overflow mode (ignored in Ibis).
        """
        raise NotImplementedError(
            "factorial() is not supported by the Ibis backend."
        )

    # =========================================================================
    # Trigonometric Functions
    # =========================================================================

    def sin(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,) -> IbisNumericExpr:
        """Get the sine of a value in radians.
    
        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN,
            )
        return x.sin()

    def cos(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,) -> IbisNumericExpr:
        """Get the cosine of a value in radians.
    
        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS,
            )
        return x.cos()

    def tan(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,) -> IbisNumericExpr:
        """Get the tangent of a value in radians.
    
        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN,
            )
        return x.tan()

    def sinh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic sine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Ibis).
        """
        raise NotImplementedError(
            "sinh() is not directly supported by the Ibis backend."
        )

    def cosh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic cosine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Ibis).
        """
        raise NotImplementedError(
            "cosh() is not directly supported by the Ibis backend."
        )

    def tanh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic tangent of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Ibis).
        """
        raise NotImplementedError(
            "tanh() is not directly supported by the Ibis backend."
        )

    # =========================================================================
    # Inverse Trigonometric Functions
    # =========================================================================

    def asin(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,
    on_domain_error: Any = None,) -> IbisNumericExpr:
        """Get the arcsine of a value in radians.
    
        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
            on_domain_error: ERROR on DuckDB, NAN on Polars; otherwise omit.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
            )
        if on_domain_error is not None and not (
            on_domain_error == "ERROR" and self.dialect == "ibis-duckdb"
            or on_domain_error == "NAN" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this arcsine domain-error mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN,
            )
        return x.asin()

    def acos(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,
    on_domain_error: Any = None,) -> IbisNumericExpr:
        """Get the arccosine of a value in radians.
    
        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
            on_domain_error: ERROR on DuckDB, NAN on Polars; otherwise omit.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
            )
        if on_domain_error is not None and not (
            on_domain_error == "ERROR" and self.dialect == "ibis-duckdb"
            or on_domain_error == "NAN" and self.dialect == "ibis-polars"
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this arccosine domain-error mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS,
            )
        return x.acos()

    def atan(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,) -> IbisNumericExpr:
        """Get the arctangent of a value in radians.
    
        Args:
            x: Input value.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN,
            )
        return x.atan()

    def asinh(
        self,
        x: IbisNumericExpr,
        /,
        rounding: Any = None,
    ) -> IbisNumericExpr:
        """Get the hyperbolic arcsine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Ibis).
        """
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
        """Get the hyperbolic arccosine of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Ibis).
            on_domain_error: Domain error policy (ignored in Ibis).
        """
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
        """Get the hyperbolic arctangent of a value.

        Args:
            x: Input value.
            rounding: IEEE rounding mode (ignored in Ibis).
            on_domain_error: Domain error policy (ignored in Ibis).
        """
        raise NotImplementedError(
            "atanh() is not directly supported by the Ibis backend."
        )

    def atan2(self,
    x: IbisNumericExpr,
    y: IbisNumericExpr,
    /,
    rounding: Any = None,
    on_domain_error: Any = None,) -> IbisNumericExpr:
        """Get the arctangent of y/x, using signs to determine the quadrant.
    
        Args:
            x: First coordinate.
            y: Second coordinate.
            rounding: Unsupported when explicit; omission uses native rounding.
            on_domain_error: NAN on DuckDB/Polars; otherwise omit.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
            )
        if on_domain_error is not None and not (
            on_domain_error == "NAN" and self.dialect in ("ibis-duckdb", "ibis-polars")
        ):
            raise BackendCapabilityError(
                "The selected Ibis engine does not implement this atan2 domain-error mode.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2,
            )
        x, y = self._lift_deferred(x, y)
        return x.atan2(y)

    # =========================================================================
    # Angular Conversions
    # =========================================================================

    def radians(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,) -> IbisNumericExpr:
        """Convert angle from degrees to radians.
    
        Args:
            x: Input angle.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS,
            )
        return x.radians()

    def degrees(self,
    x: IbisNumericExpr,
    /,
    rounding: Any = None,) -> IbisNumericExpr:
        """Convert angle from radians to degrees.
    
        Args:
            x: Input angle.
            rounding: Unsupported when explicit; omission uses native rounding.
        """
        if rounding is not None:
            raise BackendCapabilityError(
                "Ibis does not implement explicit arithmetic rounding modes.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES,
            )
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
        x, y = self._lift_deferred(x, y)
        return x & y

    def bitwise_or(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Return the bitwise OR of two integers."""
        x, y = self._lift_deferred(x, y)
        return x | y

    def bitwise_xor(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Return the bitwise XOR of two integers."""
        x, y = self._lift_deferred(x, y)
        return x ^ y

    def shift_left(
        self,
        base: IbisNumericExpr,
        shift: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Bitwise shift left."""
        base, shift = self._lift_deferred(base, shift)
        return base << shift

    def shift_right(
        self,
        base: IbisNumericExpr,
        shift: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Bitwise signed shift right."""
        base, shift = self._lift_deferred(base, shift)
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
