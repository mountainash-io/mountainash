"""Polars implementation of geospatial operations."""
from __future__ import annotations

import json
import math
import re

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
def _parse_default_throw(value):
    if value is None:
        return None
    if not re.fullmatch(DEFAULT_PATTERN, value):
        raise ValueError(f"invalid default geopoint: {value!r}")
    return value


def _parse_array_lexical_throw(value):
    if value is None:
        return None
    match = re.fullmatch(ARRAY_PATTERN, value)
    if match is None:
        raise ValueError(f"invalid array geopoint: {value!r}")
    return [float(match.group(1)), float(match.group(2))]


def _parse_array_native_throw(value):
    if value is None:
        return None
    if isinstance(value, pl.Series):
        value = value.to_list()
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"invalid native array geopoint: {value!r}")
    try:
        coordinates = [float(value[0]), float(value[1])]
    except (TypeError, ValueError):
        raise ValueError(f"invalid native array geopoint: {value!r}") from None
    if not all(math.isfinite(coordinate) for coordinate in coordinates):
        raise ValueError(f"invalid native array geopoint: {value!r}")
    return coordinates


def _parse_object_native_throw(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"invalid native object geopoint: {value!r}")
    try:
        coordinates = {"lon": float(value["lon"]), "lat": float(value["lat"])}
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"invalid native object geopoint: {value!r}") from None
    if not all(math.isfinite(coordinate) for coordinate in coordinates.values()):
        raise ValueError(f"invalid native object geopoint: {value!r}")
    return coordinates


def _parse_geojson_throw(value):
    if value is None:
        return None
    if not isinstance(value, str) or not value.lstrip().startswith("{"):
        raise ValueError(f"invalid GeoJSON value: {value!r}")
    try:
        json.loads(value)
    except (TypeError, ValueError):
        raise ValueError(f"invalid GeoJSON value: {value!r}") from None
    return value


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
            return x.map_elements(_parse_default_throw, return_dtype=pl.String)

        if format == "array" and source_representation == "lexical":
            valid = x.str.contains(ARRAY_PATTERN, literal=False)
            lon = x.str.extract(ARRAY_PATTERN, group_index=1).cast(pl.Float64, strict=False)
            lat = x.str.extract(ARRAY_PATTERN, group_index=2).cast(pl.Float64, strict=False)
            typed_null = pl.lit(None, dtype=pl.List(pl.Float64))
            value = pl.concat_list([lon, lat])
            if failure_behavior == "null":
                return pl.when(x.is_null()).then(typed_null).when(valid).then(value).otherwise(typed_null)
            return x.map_elements(_parse_array_lexical_throw, return_dtype=pl.List(pl.Float64))

        if format == "array" and source_representation == "native":
            if failure_behavior == "throw":
                return x.map_elements(_parse_array_native_throw, return_dtype=pl.List(pl.Float64))
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
            return pl.when(x.is_null()).then(typed_null).when(valid).then(value).otherwise(typed_null)

        if format == "object" and source_representation == "native":
            if failure_behavior == "throw":
                return x.map_elements(
                    _parse_object_native_throw,
                    return_dtype=pl.Struct({"lon": pl.Float64, "lat": pl.Float64}),
                )
            lon = x.struct.field("lon").cast(pl.Float64, strict=False)
            lat = x.struct.field("lat").cast(pl.Float64, strict=False)
            valid = lon.is_not_null() & lat.is_not_null() & lon.is_finite() & lat.is_finite()
            dtype = pl.Struct({"lon": pl.Float64, "lat": pl.Float64})
            typed_null = pl.lit(None, dtype=dtype)
            value = pl.struct([lon.alias("lon"), lat.alias("lat")])
            return pl.when(x.is_null()).then(typed_null).when(valid).then(value).otherwise(typed_null)

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
        object_root = stripped.str.starts_with("{")
        if failure_behavior == "null":
            valid = object_root & x.str.json_path_match("$").is_not_null()
            return pl.when(x.is_null()).then(pl.lit(None, dtype=pl.String)).when(valid).then(x).otherwise(pl.lit(None, dtype=pl.String))
        if failure_behavior == "throw":
            return x.map_elements(_parse_geojson_throw, return_dtype=pl.String)
        decoded = x.str.json_decode(dtype=pl.Struct({}))
        valid = object_root & decoded.is_not_null()
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
