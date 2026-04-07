"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Optional

from mountainash.core.types import ExpressionT


class SubstraitScalarLogarithmicExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for scalar logarithmic operations.

    Auto-generated from Substrait logarithmic extension.
    Function type: scalar
    """

    def ln(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None, on_log_zero: Optional[str] = None) -> ExpressionT:
        """Natural logarithm of the value

        Substrait: ln
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log10(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None, on_log_zero: Optional[str] = None) -> ExpressionT:
        """Logarithm to base 10 of the value

        Substrait: log10
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log2(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None, on_log_zero: Optional[str] = None) -> ExpressionT:
        """Logarithm to base 2 of the value

        Substrait: log2
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def logb(self, x: ExpressionT, /, base: ExpressionT, rounding: Optional[str] = None, on_domain_error: Optional[str] = None, on_log_zero: Optional[str] = None) -> ExpressionT:
        """Logarithm of the value with the given base
logb(x, b) => log_{b} (x)


        Substrait: logb
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log1p(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None, on_log_zero: Optional[str] = None) -> ExpressionT:
        """Natural logarithm (base e) of 1 + x
log1p(x) => log(1+x)


        Substrait: log1p
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...
