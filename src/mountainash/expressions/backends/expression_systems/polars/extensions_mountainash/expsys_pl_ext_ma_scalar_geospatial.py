"""Polars implementation of geospatial operations."""
from __future__ import annotations

import polars as pl
from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarGeospatialExpressionSystemProtocol,
)

FRICTIONLESS_NUMBER = r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:E[+-]?[0-9]+)?"
SPECIAL_NUMBER = r"(?i:NaN|INF|-INF)"
DEFAULT_NUMBER = rf"(?:{FRICTIONLESS_NUMBER}|{SPECIAL_NUMBER})"
JSON_NUMBER = r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?"
DEFAULT_PATTERN = rf"^{DEFAULT_NUMBER}, ?{DEFAULT_NUMBER}$"
ARRAY_PATTERN = rf"^\s*\[\s*({JSON_NUMBER})\s*,\s*({JSON_NUMBER})\s*\]\s*$"


def _throw_marker(valid: pl.Expr, source: pl.Expr) -> pl.Expr:
    """Create a data-dependent cast marker for throw mode."""
    return (
        pl.when(valid | source.is_null())
        .then(pl.lit("0"))
        .otherwise(pl.lit("__invalid__"))
        .cast(pl.Int8)
    )


class MountainAshPolarsScalarGeospatialExpressionSystem(
    PolarsBaseExpressionSystem,
    MountainAshScalarGeospatialExpressionSystemProtocol[pl.Expr],
):
    """Native Polars geospatial expression implementations."""

    def parse_geopoint(
        self,
        x: pl.Expr,
        /,
        *,
        format: str,
        source_representation: str,
        failure_behavior: str = "throw",
    ) -> pl.Expr:
        if format == "default":
            valid = x.str.contains(DEFAULT_PATTERN, literal=False)
            if failure_behavior == "null":
                return pl.when(x.is_null() | valid).then(x).otherwise(pl.lit(None, dtype=pl.String))
            marker = _throw_marker(valid, x)
            return x + marker.cast(pl.String).str.replace("0", "")

        if format == "array" and source_representation == "lexical":
            valid = x.str.contains(ARRAY_PATTERN, literal=False)
            lon = x.str.extract(ARRAY_PATTERN, group_index=1).cast(pl.Float64, strict=False)
            lat = x.str.extract(ARRAY_PATTERN, group_index=2).cast(pl.Float64, strict=False)
            typed_null = pl.lit(None, dtype=pl.List(pl.Float64))
            value = pl.concat_list([lon, lat])
            if failure_behavior == "null":
                return pl.when(x.is_null()).then(typed_null).when(valid).then(value).otherwise(typed_null)
            marker = _throw_marker(valid, x)
            checked = valid & (marker == 0)
            return pl.when(checked).then(value).otherwise(typed_null)

        if format == "array" and source_representation == "native":
            native = x.cast(pl.List(pl.Float64), strict=False)
            lon = native.list.get(0, null_on_oob=True)
            lat = native.list.get(1, null_on_oob=True)
            valid = (
                (native.list.len() == 2)
                & lon.is_not_null()
                & lat.is_not_null()
                & lon.is_finite()
                & lat.is_finite()
            )
            typed_null = pl.lit(None, dtype=pl.List(pl.Float64))
            value = pl.concat_list([lon, lat])
            if failure_behavior == "null":
                return pl.when(x.is_null()).then(typed_null).when(valid).then(value).otherwise(typed_null)
            marker = _throw_marker(valid, x)
            checked = valid & (marker == 0)
            return pl.when(checked).then(value).otherwise(typed_null)

        if format == "object" and source_representation == "native":
            lon = x.struct.field("lon").cast(pl.Float64, strict=False)
            lat = x.struct.field("lat").cast(pl.Float64, strict=False)
            valid = lon.is_not_null() & lat.is_not_null() & lon.is_finite() & lat.is_finite()
            dtype = pl.Struct({"lon": pl.Float64, "lat": pl.Float64})
            typed_null = pl.lit(None, dtype=dtype)
            value = pl.struct([lon.alias("lon"), lat.alias("lat")])
            if failure_behavior == "null":
                return pl.when(x.is_null()).then(typed_null).when(valid).then(value).otherwise(typed_null)
            marker = _throw_marker(valid, x)
            checked = valid & (marker == 0)
            return pl.when(checked).then(value).otherwise(typed_null)

        raise ValueError(f"unsupported geopoint format/representation: {format}/{source_representation}")

    def parse_geojson(
        self,
        x: pl.Expr,
        /,
        *,
        format: str,
        failure_behavior: str = "throw",
    ) -> pl.Expr:
        stripped = x.str.strip_chars()
        valid = stripped.str.starts_with("{") & x.str.json_path_match("$").is_not_null()
        if failure_behavior == "null":
            return (
                pl.when(x.is_null())
                .then(pl.lit(None, dtype=pl.String))
                .when(valid)
                .then(x)
                .otherwise(pl.lit(None, dtype=pl.String))
            )
        marker = _throw_marker(valid, x)
        suffix = marker.cast(pl.String).str.replace("0", "")
        return x + suffix

    def serialize_geojson(
        self,
        x: pl.Expr,
        /,
        *,
        format: str,
        failure_behavior: str = "throw",
    ) -> pl.Expr:
        return pl.when(x.is_null()).then(
            pl.lit(None, dtype=pl.String)
        ).otherwise(x.struct.json_encode())
