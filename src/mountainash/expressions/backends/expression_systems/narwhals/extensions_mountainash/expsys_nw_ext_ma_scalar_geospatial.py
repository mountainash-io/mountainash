"""Narwhals implementation of supported geospatial operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarGeospatialExpressionSystemProtocol,
)


FRICTIONLESS_NUMBER = r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:E[+-]?[0-9]+)?"
SPECIAL_NUMBER = r"(?:NaN|INF|-INF)"
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
            return nw.when(x.is_null() | valid).then(x).otherwise(
                nw.lit(None) if failure_behavior == "null" else x
            )
        if format == "array" and source_representation == "native":
            return x.cast(nw.List(nw.Float64))
        raise NotImplementedError("portable Narwhals geospatial cell is unavailable")

    def parse_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("portable Narwhals GeoJSON is unavailable")

    def serialize_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("portable Narwhals GeoJSON is unavailable")
