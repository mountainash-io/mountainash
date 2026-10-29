"""Mountainash geospatial API builder protocol."""
from __future__ import annotations

from typing import Protocol, TYPE_CHECKING, Literal

from ..substrait.prtcl_api_bldr_cast import CaseFailureBehaviour

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshScalarGeospatialAPIBuilderProtocol(Protocol):
    """User-facing geospatial namespace methods."""

    def parse_geopoint(
        self,
        *,
        format: Literal["default", "array", "object"],
        source_representation: Literal["lexical", "native"],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI: ...

    def parse_geojson(
        self,
        *,
        format: Literal["default", "topojson"],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI: ...

    def serialize_geojson(
        self,
        *,
        format: Literal["default", "topojson"],
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI: ...
