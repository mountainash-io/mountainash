"""Backend-independent GeoJSON and TopoJSON semantic validation."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Any

from mountainash.validation.jsonschema import compile_json_schema


_SCHEMA_PATH = Path(__file__).with_name("schemas") / "GeoJSON.json"
_GEOMETRY_TYPES = frozenset(
    {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"}
)


@dataclass(frozen=True)
class GeospatialDiagnostic:
    """A stable geospatial data-quality diagnostic."""

    instance_path: str
    validator: str
    message: str


@lru_cache(maxsize=1)
def _geojson_schema() -> Any:
    """Compile the vendored schema once; never read network-controlled input."""
    return compile_json_schema(json.loads(_SCHEMA_PATH.read_text(encoding="utf-8")))


def _diagnostic(path: str, validator: str, message: str) -> GeospatialDiagnostic:
    return GeospatialDiagnostic(path, validator, message)


def _is_number(value: Any) -> bool:
    return type(value) in {int, float} and math.isfinite(float(value))


def _position(value: Any, path: str, diagnostics: list[GeospatialDiagnostic]) -> int | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) < 2:
        diagnostics.append(_diagnostic(path, "geojson.position", "position must contain at least two numbers"))
        return None
    if any(not _is_number(item) for item in value):
        diagnostics.append(_diagnostic(path, "geojson.position", "position elements must be finite numbers"))
        return None
    return len(value)


def _ring(value: Any, path: str, diagnostics: list[GeospatialDiagnostic]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) < 4:
        diagnostics.append(_diagnostic(path, "geojson.ring_length", "linear ring must contain at least four positions"))
        return
    for index, position in enumerate(value):
        _position(position, f"{path}/{index}", diagnostics)
    if value[0] != value[-1]:
        diagnostics.append(_diagnostic(path, "geojson.ring_closed", "linear ring must be closed"))


def _coordinates(value: Any, geometry_type: str, path: str, diagnostics: list[GeospatialDiagnostic]) -> None:
    if geometry_type == "Point":
        _position(value, path, diagnostics)
    elif geometry_type == "MultiPoint":
        for index, position in enumerate(value if isinstance(value, Sequence) else []):
            _position(position, f"{path}/{index}", diagnostics)
    elif geometry_type == "LineString":
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) < 2:
            diagnostics.append(_diagnostic(path, "geojson.line_length", "LineString must contain at least two positions"))
            return
        for index, position in enumerate(value):
            _position(position, f"{path}/{index}", diagnostics)
    elif geometry_type == "MultiLineString":
        for index, line in enumerate(value if isinstance(value, Sequence) else []):
            _coordinates(line, "LineString", f"{path}/{index}", diagnostics)
    elif geometry_type == "Polygon":
        for index, ring in enumerate(value if isinstance(value, Sequence) else []):
            _ring(ring, f"{path}/{index}", diagnostics)
    elif geometry_type == "MultiPolygon":
        for index, polygon in enumerate(value if isinstance(value, Sequence) else []):
            _coordinates(polygon, "Polygon", f"{path}/{index}", diagnostics)


def _bbox(value: Any, path: str, diagnostics: list[GeospatialDiagnostic]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) < 4 or len(value) % 2:
        diagnostics.append(_diagnostic(path, "geojson.bbox", "bbox must have even length of at least four"))
        return
    if any(not _is_number(item) for item in value):
        diagnostics.append(_diagnostic(path, "geojson.bbox", "bbox members must be finite numbers"))
        return
    dimensions = len(value) // 2
    lower, upper = value[:dimensions], value[dimensions:]
    for index, (minimum, maximum) in enumerate(zip(lower, upper, strict=True)):
        if index != 0 and minimum > maximum:
            diagnostics.append(_diagnostic(path, "geojson.bbox_order", "bbox lower bound exceeds upper bound"))


def _validate_geojson_object(value: Any, path: str, diagnostics: list[GeospatialDiagnostic]) -> None:
    if not isinstance(value, Mapping):
        diagnostics.append(_diagnostic(path, "geojson.object", "GeoJSON value must be an object"))
        return
    geo_type = value.get("type")
    if geo_type in _GEOMETRY_TYPES:
        if geo_type == "GeometryCollection":
            geometries = value.get("geometries")
            if not isinstance(geometries, Sequence) or isinstance(geometries, (str, bytes)):
                diagnostics.append(_diagnostic(f"{path}/geometries", "geojson.geometries", "GeometryCollection geometries must be an array"))
            else:
                for index, geometry in enumerate(geometries):
                    _validate_geojson_object(geometry, f"{path}/geometries/{index}", diagnostics)
        else:
            _coordinates(value.get("coordinates"), geo_type, f"{path}/coordinates", diagnostics)
    elif geo_type == "Feature":
        geometry = value.get("geometry")
        if geometry is not None:
            _validate_geojson_object(geometry, f"{path}/geometry", diagnostics)
        properties = value.get("properties")
        if properties is not None and not isinstance(properties, Mapping):
            diagnostics.append(_diagnostic(f"{path}/properties", "geojson.properties", "Feature properties must be an object or null"))
    elif geo_type == "FeatureCollection":
        features = value.get("features")
        if not isinstance(features, Sequence) or isinstance(features, (str, bytes)):
            diagnostics.append(_diagnostic(f"{path}/features", "geojson.features", "FeatureCollection features must be an array"))
        else:
            for index, feature in enumerate(features):
                _validate_geojson_object(feature, f"{path}/features/{index}", diagnostics)
    else:
        diagnostics.append(_diagnostic(f"{path}/type", "geojson.type", "unrecognized GeoJSON type"))
    if "bbox" in value:
        _bbox(value["bbox"], f"{path}/bbox", diagnostics)


def validate_geojson(value: Any) -> tuple[GeospatialDiagnostic, ...]:
    """Validate vendored-schema and RFC 7946 structural semantics."""
    diagnostics = [
        _diagnostic(item.instance_path, f"jsonschema.{item.validator}", item.message)
        for item in _geojson_schema().validate(value)
    ]
    _validate_geojson_object(value, "", diagnostics)
    return tuple(sorted(diagnostics, key=lambda item: (item.instance_path, item.validator, item.message)))


def _decoded_arc(topology: Mapping[str, Any], index: int) -> list[tuple[float, ...]]:
    arcs = topology.get("arcs")
    if not isinstance(arcs, Sequence) or index < 0 or index >= len(arcs):
        raise ValueError(f"TopoJSON arc index {index} is out of range")
    arc = arcs[index]
    if not isinstance(arc, Sequence):
        raise ValueError(f"TopoJSON arc {index} must be an array")
    previous: list[float] | None = None
    decoded: list[tuple[float, ...]] = []
    for position in arc:
        if not isinstance(position, Sequence) or isinstance(position, (str, bytes)) or len(position) < 2:
            raise ValueError(f"TopoJSON arc {index} contains an invalid position")
        if any(not _is_number(value) for value in position):
            raise ValueError(f"TopoJSON arc {index} contains a non-finite coordinate")
        if previous is None:
            previous = [float(value) for value in position]
        else:
            previous = [
                previous[dimension] + float(value)
                for dimension, value in enumerate(position)
            ]
        decoded.append(tuple(previous))
    transform = topology.get("transform")
    if transform is not None:
        scale = transform.get("scale") if isinstance(transform, Mapping) else None
        translate = transform.get("translate") if isinstance(transform, Mapping) else None
        if not (isinstance(scale, Sequence) and isinstance(translate, Sequence) and len(scale) == len(translate) == 2):
            raise ValueError("TopoJSON transform requires two-element scale and translate")
        decoded = [
            (point[0] * float(scale[0]) + float(translate[0]), point[1] * float(scale[1]) + float(translate[1]), *point[2:])
            for point in decoded
        ]
    return decoded


def reconstruct_topojson_line(
    topology: Mapping[str, Any], *, arc_indexes: Sequence[int]
) -> list[tuple[float, ...]]:
    """Decode, reverse, and stitch a TopoJSON line's arc references."""
    line: list[tuple[float, ...]] = []
    for arc_index in arc_indexes:
        if type(arc_index) is not int:  # noqa: E721 — bool is not an arc index
            raise ValueError("TopoJSON arc reference must be an integer")
        selected = _decoded_arc(topology, arc_index if arc_index >= 0 else ~arc_index)
        if arc_index < 0:
            selected.reverse()
        if line and selected and line[-1] == selected[0]:
            selected = selected[1:]
        line.extend(selected)
    return line


def _ring_area(ring: Sequence[Sequence[float]]) -> float:
    """Shoelace area in a locally unwrapped longitude frame."""
    area = 0.0
    longitude = float(ring[0][0])
    previous = (longitude, float(ring[0][1]))
    for position in ring[1:]:
        next_longitude = float(position[0])
        while next_longitude - longitude > 180:
            next_longitude -= 360
        while next_longitude - longitude < -180:
            next_longitude += 360
        current = (next_longitude, float(position[1]))
        area += previous[0] * current[1] - current[0] * previous[1]
        longitude = next_longitude
        previous = current
    return area / 2


def _winding(
    value: Any, path: str, diagnostics: list[GeospatialDiagnostic]
) -> None:
    if not isinstance(value, Mapping):
        return
    geo_type = value.get("type")
    if geo_type == "Feature":
        geometry = value.get("geometry")
        if geometry is not None:
            _winding(geometry, f"{path}/geometry", diagnostics)
    elif geo_type == "FeatureCollection":
        for index, feature in enumerate(value.get("features", ())):
            _winding(feature, f"{path}/features/{index}", diagnostics)
    elif geo_type == "GeometryCollection":
        for index, geometry in enumerate(value.get("geometries", ())):
            _winding(geometry, f"{path}/geometries/{index}", diagnostics)
    elif geo_type in {"Polygon", "MultiPolygon"}:
        polygons = value.get("coordinates", ())
        if geo_type == "Polygon":
            polygons = [polygons]
        for polygon_index, polygon in enumerate(polygons):
            for ring_index, ring in enumerate(polygon):
                if (
                    isinstance(ring, Sequence)
                    and len(ring) >= 4
                    and all(isinstance(position, Sequence) and len(position) >= 2 for position in ring)
                ):
                    area = _ring_area(ring)
                    expected_positive = ring_index == 0
                    if area and (area > 0) != expected_positive:
                        diagnostics.append(
                            _diagnostic(
                                f"{path}/coordinates/{polygon_index if geo_type == 'MultiPolygon' else ring_index}",
                                "geojson.winding",
                                "polygon ring violates RFC 7946 right-hand orientation",
                            )
                        )


def validate_geojson_winding(value: Any) -> tuple[GeospatialDiagnostic, ...]:
    """Report, but do not reject, RFC 7946 polygon ring orientation."""
    diagnostics: list[GeospatialDiagnostic] = []
    _winding(value, "", diagnostics)
    return tuple(sorted(diagnostics, key=lambda item: (item.instance_path, item.validator)))


def validate_topojson(value: Any) -> tuple[GeospatialDiagnostic, ...]:
    """Validate TopoJSON topology structure before reconstructed geometry use."""
    diagnostics: list[GeospatialDiagnostic] = []
    if not isinstance(value, Mapping):
        return (_diagnostic("", "topojson.object", "TopoJSON value must be an object"),)
    if value.get("type") != "Topology":
        diagnostics.append(_diagnostic("/type", "topojson.type", "type must equal 'Topology'"))
    if not isinstance(value.get("objects"), Mapping):
        diagnostics.append(_diagnostic("/objects", "topojson.objects", "objects must be an object"))
    arcs = value.get("arcs")
    if not isinstance(arcs, Sequence) or isinstance(arcs, (str, bytes)):
        diagnostics.append(_diagnostic("/arcs", "topojson.arcs", "arcs must be an array"))
    else:
        for index, arc in enumerate(arcs):
            try:
                decoded = _decoded_arc(value, index)
                if len(decoded) < 2:
                    diagnostics.append(_diagnostic(f"/arcs/{index}", "topojson.arc_length", "arc must have at least two positions"))
            except ValueError as error:
                diagnostics.append(_diagnostic(f"/arcs/{index}", "topojson.arc", str(error)))
    return tuple(sorted(diagnostics, key=lambda item: (item.instance_path, item.validator, item.message)))
