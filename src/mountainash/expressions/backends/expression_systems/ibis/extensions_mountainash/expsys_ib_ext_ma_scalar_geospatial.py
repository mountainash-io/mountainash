"""Ibis implementation of supported geospatial operations."""
from __future__ import annotations

import ibis

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarGeospatialExpressionSystemProtocol,
)
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL


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
        if source_representation == "native" and format in {"array", "object"}:
            if self.dialect == "ibis-sqlite":
                raise BackendCapabilityError(
                    "Ibis SQLite does not support native array or object geopoint parsing.",
                    backend=self.BACKEND_NAME,
                    function_key=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                )
            if self.dialect == "ibis-polars" and failure_behavior == "null":
                raise BackendCapabilityError(
                    "Ibis Polars native array or object geopoint parsing cannot return null on failure.",
                    backend=self.BACKEND_NAME,
                    function_key=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                )
        if (
            self.dialect == "ibis-sqlite"
            and format == "array"
            and source_representation == "lexical"
        ):
            raise BackendCapabilityError(
                "Ibis SQLite cannot parse lexical array geopoints.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
            )
        if format == "default" and source_representation == "lexical":
            if self.dialect == "ibis-sqlite" and failure_behavior == "throw":
                raise BackendCapabilityError(
                    "SQLite cannot raise for invalid lexical geopoints; only null failure behavior is supported.",
                    backend=self.BACKEND_NAME,
                    function_key=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                )
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
                & ~lon.isnan()
                & ~lat.isnan()
                & ~lon.isinf()
                & ~lat.isinf()
            )
            marker = ibis.ifelse(x.isnull() | valid, ibis.literal("0"), ibis.literal("__invalid__")).cast("int8")
            rebuilt = ibis.array([
                lon + marker.cast("float64") * 0,
                lat + marker.cast("float64") * 0,
            ])
            if failure_behavior == "null":
                return ibis.ifelse(x.isnull(), ibis.null(), ibis.ifelse(valid, rebuilt, ibis.null()))
            return ibis.ifelse(x.isnull(), ibis.null(), rebuilt)
        if format == "object" and source_representation == "native":
            lon = x["lon"].cast("float64")
            lat = x["lat"].cast("float64")
            valid = lon.notnull() & lat.notnull() & ~lon.isnan() & ~lat.isnan() & ~lon.isinf() & ~lat.isinf()
            marker = ibis.ifelse(x.isnull() | valid, ibis.literal("0"), ibis.literal("__invalid__")).cast("int8")
            value = ibis.struct({
                "lon": lon + marker.cast("float64") * 0,
                "lat": lat + marker.cast("float64") * 0,
            })
            if failure_behavior == "null":
                return ibis.ifelse(x.isnull(), ibis.null(), ibis.ifelse(valid, value, ibis.null()))
            return ibis.ifelse(x.isnull(), ibis.null(), value)
        raise NotImplementedError("Ibis geospatial cell is unavailable")

    def parse_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("Ibis GeoJSON is unavailable")

    def serialize_geojson(self, x, /, *, format: str, failure_behavior: str = "throw"):
        raise NotImplementedError("Ibis GeoJSON is unavailable")
