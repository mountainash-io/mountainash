"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions


class SubstraitConditionalExpressionSystemProtocol(Protocol):
    """Protocol for conditional operations.

    Auto-generated from Substrait conditional extension.
    """

    def if_then_else(
        self,
        condition: SupportedExpressions,
        if_true: SupportedExpressions,
        if_false: SupportedExpressions, /
    ) -> SupportedExpressions:
        """Create a conditional if-then-else expression.

        Substrait: if_then
        """
        ...
