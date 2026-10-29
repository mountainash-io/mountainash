"""Struct operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.core.dtypes import StructDtype
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarStructAPIBuilderProtocol
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.expressions.core.expression_nodes import CastNode, IfThenNode, LiteralNode, ScalarFunctionNode
from ._operation_options import invalid, validate_container_dtype, validate_failure_behavior, validate_field_name
if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from mountainash.core.dtypes import CastTarget


class MountainAshScalarStructAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarStructAPIBuilderProtocol):
    """API builder for the .struct namespace."""
    def cast(
        self,
        *,
        dtype: "CastTarget",
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
        converted_fields: tuple[tuple[str, "BaseExpressionAPI"], ...] = (),
        converted_validity: "BaseExpressionAPI | None" = None,
    ) -> BaseExpressionAPI:
        """Cast a native struct to the complete ``dtype`` target.

        Without ``converted_fields`` the original value is cast directly. With
        them, the target is rebuilt from the ordered child expressions (which
        must cover the target's ordered members). ``converted_validity``
        yields a typed null when false.
        """
        target = validate_container_dtype("struct.cast", dtype, StructDtype)
        validate_field_name("struct.cast", field_name)
        failure = validate_failure_behavior("struct.cast", failure_behavior)
        if not isinstance(converted_fields, tuple) or any(
            not isinstance(pair, tuple) or len(pair) != 2 or not isinstance(pair[0], str)
            or not hasattr(pair[1], "_node")
            for pair in converted_fields
        ):
            invalid("struct.cast", "converted_fields", "must be a tuple of (name, expression) pairs")
        if converted_validity is not None and not hasattr(converted_validity, "_node"):
            invalid("struct.cast", "converted_validity", "must be an expression or None")
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
            arguments=[self._node, *(value._node for _, value in converted_fields)],
            options={
                "dtype": target,
                "field_names": tuple(name for name, _ in converted_fields),
                "failure_behavior": failure.value,
            },
            diagnostic_context={
                "field_name": field_name,
                "logical_type": "struct",
                "format": "default",
            },
        )
        if converted_validity is not None:
            node = IfThenNode(
                conditions=[(converted_validity._node, node)],
                else_clause=CastNode(input=LiteralNode(value=None), target_type=target, failure_behavior="throw"),
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
