"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.expressions.types import SupportedExpressions

class SubstraitScalarSetExpressionSystemProtocol(Protocol):
    """Protocol for set operations.

    Auto-generated from Substrait set extension.
    """

    def is_in(
        self,
        needle: SupportedExpressions, /, *haystack: SupportedExpressions
    ) -> SupportedExpressions:
        """Check if value is in the given set of values.

        Substrait: index_in (returns bool based on >= 0)
        """
        ...

    def is_not_in(
        self,
        needle: SupportedExpressions, /, *haystack: SupportedExpressions
    ) -> SupportedExpressions:
        """Check if value is not in the given set of values.

        Substrait: index_in (returns bool based on < 0)
        """
        ...
