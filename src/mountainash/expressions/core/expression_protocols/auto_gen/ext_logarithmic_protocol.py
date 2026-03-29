"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol

# Placeholder - use your actual type
SupportedExpressions = Any



class LogarithmicExpressionProtocol(Protocol):
    """Protocol for logarithmic operations.

    Auto-generated from Substrait logarithmic extension.
    """

    def ln(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Natural logarithm of the value

        Substrait: ln
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log10(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm to base 10 of the value

        Substrait: log10
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log2(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm to base 2 of the value

        Substrait: log2
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def logb(self, x: SupportedExpressions, base: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm of the value with the given base
logb(x, b) => log_{b} (x)


        Substrait: logb
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log1p(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Natural logarithm (base e) of 1 + x
log1p(x) => log(1+x)


        Substrait: log1p
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...
