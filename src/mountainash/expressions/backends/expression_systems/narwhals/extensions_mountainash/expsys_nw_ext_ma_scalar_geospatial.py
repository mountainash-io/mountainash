"""Narwhals implementation of supported geospatial operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarGeospatialExpressionSystemProtocol,
)


FRICTIONLESS_NUMBER = r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:E[+-]?[0-9]+)?"
SPECIAL_NUMBER = r"(?i:NaN|INF|-INF)"
DEFAULT_NUMBER = rf"(?:{FRICTIONLESS_NUMBER}|{SPECIAL_NUMBER})"
DEFAULT_PATTERN = rf"^{DEFAULT_NUMBER}, ?{DEFAULT_NUMBER}$"


class MountainAshNarwhalsScalarGeospatialExpressionSystem(
    NarwhalsBaseExpressionSystem,
    MountainAshScalarGeospatialExpressionSystemProtocol[nw.Expr],
):
    """Portable Narwhals geospatial subset."""

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
            valid = x.str.contains(DEFAULT_PATTERN)
            if failure_behavior == "null":
                return nw.when(x.is_null() | valid).then(x).otherwise(nw.lit(None))
            marker = nw.when(x.is_null() | valid).then(nw.lit("0")).otherwise(nw.lit("__invalid__")).cast(nw.Int8)
            suffix = marker.cast(nw.String).str.replace("0", "")
            return x + suffix
        if format == "array" and source_representation == "native":
            native = x.cast(nw.List(nw.Float64))
            lon = native.list.get(0)
            lat = native.list.get(1)
            valid = (
                (native.list.len() == 2)
                & lon.is_not_null()
                & lat.is_not_null()
                & lon.is_finite()
                & lat.is_finite()
            )
            if failure_behavior == "null":
                return nw.when(x.is_null() | valid).then(native).otherwise(nw.lit(None))
            marker = nw.when(x.is_null() | valid).then(nw.lit("0")).otherwise(nw.lit("__invalid__")).cast(nw.Int8)
            return nw.when(x.is_null() | valid).then(native).otherwise((lon + marker.cast(nw.Float64) * 0).cast(nw.List(nw.Float64)))
        raise NotImplementedError("portable Narwhals geospatial cell is unavailable")

    def parse_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("portable Narwhals GeoJSON is unavailable")

    def serialize_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("portable Narwhals GeoJSON is unavailable")
