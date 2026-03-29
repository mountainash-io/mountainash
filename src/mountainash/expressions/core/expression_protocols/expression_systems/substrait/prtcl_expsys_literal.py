"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.types import SupportedExpressions


class SubstraitLiteralExpressionSystemProtocol(Protocol):
    """Protocol for rounding operations.

    Auto-generated from Substrait rounding extension.
    """

    def lit(self, x: Any, /) -> SupportedExpressions:
        """Literal Value.

        Substrait: lit
        # URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/??
        """
        ...
