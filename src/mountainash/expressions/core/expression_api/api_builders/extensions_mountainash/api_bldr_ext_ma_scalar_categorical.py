"""Categorical operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarCategoricalAPIBuilderProtocol
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_CATEGORICAL
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from ._operation_options import validate_categories, validate_failure_behavior, validate_field_name

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarCategoricalAPIBuilder(
    BaseExpressionAPIBuilder,
    MountainAshScalarCategoricalAPIBuilderProtocol,
):
    """API builder for the .cat namespace."""

    def cast(
        self,
        *,
        value_type: str,
        categories: tuple[Any, ...],
        ordered: bool,
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI:
        """Cast to a categorical base scalar; metadata is not encoded."""
        categories = validate_categories("cat.cast", value_type, categories, ordered)
        validate_field_name("cat.cast", field_name)
        failure = validate_failure_behavior("cat.cast", failure_behavior)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_CATEGORICAL.CAST,
            arguments=[self._node],
            options={
                "value_type": value_type,
                "categories": categories,
                "ordered": ordered,
                "failure_behavior": failure.value,
            },
            diagnostic_context={
                "field_name": field_name,
                "logical_type": "categorical",
                "format": "default",
            },
        )
        return self._build(node)
