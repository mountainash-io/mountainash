"""Ibis implementation of supported geospatial operations."""
from __future__ import annotations

import ibis

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarGeospatialExpressionSystemProtocol,
)


FRICTIONLESS_NUMBER = r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:E[+-]?[0-9]+)?"
SPECIAL_NUMBER = r"(?i:NaN|INF|-INF)"
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
            marker = ibis.ifelse(x.isnull() | valid, ibis.literal("0"), ibis.literal("__invalid__")).cast("int8")
            return x + marker.cast("string").re_replace("0", "")
        if format == "array" and source_representation == "native":
            native = x.cast("array<float64>")
            lon = native[0]
            lat = native[1]
            valid = (
                (native.length() == 2)
                & lon.notnull()
                & lat.notnull()
                & lon.is_finite()
                & lat.is_finite()
            )
            if failure_behavior == "null":
                return ibis.ifelse(x.isnull(), ibis.null(), ibis.ifelse(valid, native, ibis.null()))
            invalid = ibis.literal("__invalid__").cast("array<float64>")
            return ibis.ifelse(x.isnull() | valid, native, invalid)
        if format == "object" and source_representation == "native":
            lon = x["lon"].cast("float64")
            lat = x["lat"].cast("float64")
            valid = lon.notnull() & lat.notnull() & lon.is_finite() & lat.is_finite()
            value = ibis.struct({"lon": lon, "lat": lat})
            if failure_behavior == "null":
                return ibis.ifelse(x.isnull(), ibis.null(), ibis.ifelse(valid, value, ibis.null()))
            invalid = ibis.literal("__invalid__").cast("struct<lon:float64,lat:float64>")
            return ibis.ifelse(x.isnull() | valid, value, invalid)
        raise NotImplementedError("Ibis geospatial cell is unavailable")

    def parse_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("Ibis GeoJSON is unavailable")

    def serialize_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("Ibis GeoJSON is unavailable")
