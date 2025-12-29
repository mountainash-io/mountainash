"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions





class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol):
    """Protocol for arithmetic operations.

    Auto-generated from Substrait arithmetic extension.
    """

    def add(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Add two values.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def subtract(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Subtract one value from another.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def multiply(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Multiply two values.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def divide(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None, on_domain_error: Any = None, on_division_by_zero: Any = None) -> SupportedExpressions:
        """Divide x by y. In the case of integer division, partial values are truncated (i.e. rounded towards 0). The `on_division_by_zero` option governs behavior in cases where y is 0.  If the option is IEEE then the IEEE754 standard is followed: all values except +/-infinity return NaN and +/-infinity are unchanged. If the option is LIMIT then the result is +/-infinity in all cases. If either x or y are NaN then behavior will be governed by `on_domain_error`. If x and y are both +/-infinity, behavior will be governed by `on_domain_error`.


        Substrait: divide
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def negate(self, x: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Negation of the value

        Substrait: negate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def modulus(self, x: SupportedExpressions, y: SupportedExpressions, /, division_type: Any = None, overflow: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
        """Calculate the remainder (r) when dividing dividend (x) by divisor (y).
In mathematics, many conventions for the modulus (mod) operation exists. The result of a mod operation depends on the software implementation and underlying hardware. Substrait is a format for describing compute operations on structured data and designed for interoperability. Therefore the user is responsible for determining a definition of division as defined by the quotient (q).
The following basic conditions of division are satisfied: (1) q ∈ ℤ (the quotient is an integer) (2) x = y * q + r (division rule) (3) abs(r) < abs(y) where q is the quotient.
The `division_type` option determines the mathematical definition of quotient to use in the above definition of division.
When `division_type`=TRUNCATE, q = trunc(x/y). When `division_type`=FLOOR, q = floor(x/y).
In the cases of TRUNCATE and FLOOR division: remainder r = x - round_func(x/y)
The `on_domain_error` option governs behavior in cases where y is 0, y is +/-inf, or x is +/-inf. In these cases the mod is undefined. The `overflow` option governs behavior when integer overflow occurs. If x and y are both 0 or both +/-infinity, behavior will be governed by `on_domain_error`.


        Substrait: modulus
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def power(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Take the power with x as the base and y as exponent.

        Substrait: power
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...
