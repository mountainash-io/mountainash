"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace


class ScalarLogarithmicExpressionProtocol(Protocol):
    """Protocol for logarithmic operations.

    Auto-generated from Substrait logarithmic extension.
    """

    def ln(self, x: SupportedExpressions, /, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Natural logarithm of the value

        Substrait: ln
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log10(self, x: SupportedExpressions, /, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm to base 10 of the value

        Substrait: log10
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log2(self, x: SupportedExpressions, /, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm to base 2 of the value

        Substrait: log2
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def logb(self, x: SupportedExpressions, /, base: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm of the value with the given base
logb(x, b) => log_{b} (x)

        Substrait: logb
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

#     def log1p(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
#         """Natural logarithm (base e) of 1 + x
# log1p(x) => log(1+x)


#         Substrait: log1p
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
#         """
#         ...


class ScalarLogarithmicBuilderProtocol(Protocol):
    """Builder protocol for logarithmic operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def ln(self) -> "BaseNamespace":
        """Natural logarithm (base e).

        Substrait: ln
        """
        ...

    def log10(self) -> "BaseNamespace":
        """Logarithm base 10.

        Substrait: log10
        """
        ...

    def log2(self) -> "BaseNamespace":
        """Logarithm base 2.

        Substrait: log2
        """
        ...

    def log(
        self,
        base: Union["BaseNamespace", "ExpressionNode", Any, float],
    ) -> "BaseNamespace":
        """Logarithm with custom base.

        Substrait: logb
        """
        ...
