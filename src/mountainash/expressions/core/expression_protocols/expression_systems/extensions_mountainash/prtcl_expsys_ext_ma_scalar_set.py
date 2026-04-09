"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT

class SubstraitScalarSetExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for set operations.

    Auto-generated from Substrait set extension.
    """

    def is_in(
        self,
        needle: ExpressionT, /, *haystack: ExpressionT
    ) -> ExpressionT:
        """Check if value is in the given set of values.

        Substrait: index_in (returns bool based on >= 0)
        """
        ...

    def is_not_in(
        self,
        needle: ExpressionT, /, *haystack: ExpressionT
    ) -> ExpressionT:
        """Check if value is not in the given set of values.

        Substrait: index_in (returns bool based on < 0)
        """
        ...
