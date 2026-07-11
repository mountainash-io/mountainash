"""Mountainash comparison extension protocol.

Mountainash Extension: Comparison
URI: file://extensions/functions_comparison.yaml

Extensions beyond Substrait standard:
- is_duplicated: per-row duplicate flag
"""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarComparisonExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for Mountainash comparison extensions.

    These operations extend beyond the Substrait standard comparison
    functions.
    """

    def is_duplicated(self, x: ExpressionT, /) -> ExpressionT:
        """Whether the value appears more than once in the column.

        Mountainash extension: is_duplicated
        URI: file://extensions/functions_comparison.yaml
        """
        ...
