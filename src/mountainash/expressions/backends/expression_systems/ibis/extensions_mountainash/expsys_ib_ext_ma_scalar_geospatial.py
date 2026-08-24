"""Ibis implementation of supported geospatial operations."""
from __future__ import annotations

import ibis

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarGeospatialExpressionSystemProtocol,
)


FRICTIONLESS_NUMBER = r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:E[+-]?[0-9]+)?"
SPECIAL_NUMBER = r"(?:NaN|INF|-INF)"
DEFAULT_NUMBER = rf"(?:{FRICTIONLESS_NUMBER}|{SPECIAL_NUMBER})"
DEFAULT_PATTERN = rf"^{DEFAULT_NUMBER}, ?{DEFAULT_NUMBER}$"


class MountainAshIbisScalarGeospatialExpressionSystem(
    IbisBaseExpressionSystem,
    MountainAshScalarGeospatialExpressionSystemProtocol["IbisValueExpr"],
):
    """Ibis geospatial subset shared by supported SQL dialects."""

    def parse_geopoint(
        self,
        x,
        /,
        *,
        format: str,
        source_representation: str,
        failure_behavior: str = "throw",
    ):
        if format == "default" and source_representation == "lexical":
            valid = x.re_search(DEFAULT_PATTERN)
            if failure_behavior == "null":
                return ibis.ifelse(x.isnull(), ibis.null(), ibis.ifelse(valid, x, ibis.null()))
            return x
        if format == "array" and source_representation == "native":
            return x.cast("array<float64>")
        if format == "object" and source_representation == "native":
            return ibis.struct({"lon": x["lon"].cast("float64"), "lat": x["lat"].cast("float64")})
        raise NotImplementedError("Ibis geospatial cell is unavailable")

    def parse_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("Ibis GeoJSON is unavailable")

    def serialize_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("Ibis GeoJSON is unavailable")
