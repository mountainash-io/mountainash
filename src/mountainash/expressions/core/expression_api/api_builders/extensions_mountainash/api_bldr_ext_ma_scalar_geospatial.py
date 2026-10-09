"""API builder for geospatial operations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import (
    MountainAshScalarGeospatialAPIBuilderProtocol,
)
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL,
)
from ._operation_options import (
    validate_failure_behavior,
    validate_field_name,
    validate_geojson_format,
    validate_geopoint_options,
)
from ..api_builder_base import BaseExpressionAPIBuilder

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarGeospatialAPIBuilder(
    BaseExpressionAPIBuilder,
    MountainAshScalarGeospatialAPIBuilderProtocol,
):
    """User-facing `.geo` operation builder."""

    def parse_geopoint(
        self,
        *,
        format: Literal["default", "array", "object"],
        source_representation: Literal["lexical", "native"],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI:
        method = "geo.parse_geopoint"
        format, source_representation = validate_geopoint_options(method, format, source_representation)
        validate_field_name(method, field_name)
        failure = validate_failure_behavior(method, failure_behavior)
        return self._build(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                arguments=[self._node],
                options={
                    "format": format,
                    "source_representation": source_representation,
                    "failure_behavior": failure.value,
                },
                diagnostic_context={
                    "field_name": field_name,
                    "logical_type": "geopoint",
                    "format": format,
                },
            )
        )

    def parse_geojson(
        self,
        *,
        format: Literal["default", "topojson"],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI:
        method = "geo.parse_geojson"
        format = validate_geojson_format(method, format)
        validate_field_name(method, field_name)
        failure = validate_failure_behavior(method, failure_behavior)
        return self._build(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON,
                arguments=[self._node],
                options={"format": format, "failure_behavior": failure.value},
                diagnostic_context={
                    "field_name": field_name,
                    "logical_type": "geojson",
                    "format": format,
                },
            )
        )

    def serialize_geojson(
        self,
        *,
        format: Literal["default", "topojson"],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI:
        method = "geo.serialize_geojson"
        format = validate_geojson_format(method, format)
        validate_field_name(method, field_name)
        failure = validate_failure_behavior(method, failure_behavior)
        return self._build(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON,
                arguments=[self._node],
                options={"format": format, "failure_behavior": failure.value},
                diagnostic_context={
                    "field_name": field_name,
                    "logical_type": "geojson",
                    "format": format,
                },
            )
        )
