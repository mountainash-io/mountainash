"""Struct operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarStructAPIBuilderProtocol
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from ._operation_options import validate_failure_behavior, validate_field_name, validate_fields
if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from mountainash.typespec.spec import FieldSpec


class MountainAshScalarStructAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarStructAPIBuilderProtocol):
    """API builder for the .struct namespace."""
    def cast(
        self,
        *,
        fields: tuple["FieldSpec", ...],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI:
        """Recursively cast a native struct value."""
        fields = validate_fields("struct.cast", "fields", fields)
        validate_field_name("struct.cast", field_name)
        failure = validate_failure_behavior("struct.cast", failure_behavior)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
            arguments=[self._node],
            options={"fields": fields, "failure_behavior": failure.value},
            diagnostic_context={
                "field_name": field_name,
                "logical_type": "struct",
                "format": "default",
            },
        )
        return self._build(node)

    def field(self, name: str) -> BaseExpressionAPI:
        """Extract a named field from a struct column.

        Args:
            name: Field name to extract.

        Returns:
            Expression containing the extracted field value.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
            arguments=[self._node],
            options={"field_name": name},
        )
        return self._build(node)
