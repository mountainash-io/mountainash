"""Mountainash struct extension protocol.

Mountainash Extension: Struct Operations
URI: file://extensions/functions_struct.yaml

Extensions beyond Substrait standard:
- Struct field extraction
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from ..substrait.prtcl_api_bldr_cast import CaseFailureBehaviour

if TYPE_CHECKING:
    from mountainash.typespec.spec import FieldSpec
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshScalarStructAPIBuilderProtocol(Protocol):
    """Builder protocol for struct operations.

    Defines user-facing fluent API methods for the .struct namespace.
    """

    def field(self, name: str) -> BaseExpressionAPI:
        """Extract a named field from a struct column."""
        ...

    def cast(
        self,
        *,
        fields: tuple["FieldSpec", ...],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI:
        """Recursively cast a native struct."""
        ...
