"""Protocol for Mountainash geospatial operations."""
from __future__ import annotations

from typing import Literal, Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarGeospatialExpressionSystemProtocol(Protocol[ExpressionT]):
    """Geopoint and GeoJSON operations across backends."""

    def parse_geopoint(
        self,
        x: ExpressionT,
        /,
        *,
        format: Literal["default", "array", "object"],
        source_representation: Literal["lexical", "native"],
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT: ...

    def parse_geojson(
        self,
        x: ExpressionT,
        /,
        *,
        format: Literal["default", "topojson"],
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT: ...

    def serialize_geojson(
        self,
        x: ExpressionT,
        /,
        *,
        format: Literal["default", "topojson"],
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT: ...
