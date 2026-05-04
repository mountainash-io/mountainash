"""Mountainash struct extension protocol.

Mountainash Extension: Struct Operations
URI: file://extensions/functions_struct.yaml

Extensions beyond Substrait standard:
- Struct field extraction
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshScalarStructAPIBuilderProtocol(Protocol):
    """Builder protocol for struct operations.

    Defines user-facing fluent API methods for the .struct namespace.
    """

    def field(self, name: str) -> BaseExpressionAPI:
        """Extract a named field from a struct column."""
        ...
