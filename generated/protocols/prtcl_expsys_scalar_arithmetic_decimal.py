"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitScalarArithmeticDecimalExpressionSystemProtocol(Protocol):
    """Protocol for scalar arithmetic_decimal operations.

    Auto-generated from Substrait arithmetic_decimal extension.
    Function type: scalar
    """

    def add(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Add two decimal values.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def subtract(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait subtract function.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def multiply(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait multiply function.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def divide(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait divide function.

        Substrait: divide
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def modulus(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait modulus function.

        Substrait: modulus
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def abs(self, x: SupportedExpressions) -> SupportedExpressions:
        """Calculate the absolute value of the argument.

        Substrait: abs
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def bitwise_and(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise AND result for two decimal inputs. In inputs scale must be 0 (i.e. only integer types are allowed)


        Substrait: bitwise_and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def bitwise_or(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise OR result for two given decimal inputs. In inputs scale must be 0 (i.e. only integer types are allowed)


        Substrait: bitwise_or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def bitwise_xor(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise XOR result for two given decimal inputs. In inputs scale must be 0 (i.e. only integer types are allowed)


        Substrait: bitwise_xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def sqrt(self, x: SupportedExpressions) -> SupportedExpressions:
        """Square root of the value. Sqrt of 0 is 0 and sqrt of negative values will raise an error.

        Substrait: sqrt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def factorial(self, n: SupportedExpressions) -> SupportedExpressions:
        """Return the factorial of a given decimal input. Scale should be 0 for factorial decimal input. The factorial of 0! is 1 by convention. Negative inputs will raise an error. Input which cause overflow of result will raise an error.


        Substrait: factorial
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def power(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None, complex_number_result: Any = None) -> SupportedExpressions:
        """Take the power with x as the base and y as exponent. Behavior for complex number result is indicated by option complex_number_result

        Substrait: power
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

