"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions

class SubstraitScalarSetExpressionSystemProtocol(Protocol):
    """Protocol for set operations.

    Auto-generated from Substrait set extension.
    """

    def index_in(self, needle: SupportedExpressions, /, *haystack: SupportedExpressions) -> SupportedExpressions:
        """Return the 0-indexed position of needle in haystack, or -1 if not found.

        Substrait: index_in
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_set.yaml
        """
        ...
