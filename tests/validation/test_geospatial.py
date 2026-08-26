"""Pinned GeoJSON and TopoJSON semantic validation."""

from hashlib import sha256
from pathlib import Path

from mountainash.validation.geospatial import (
    reconstruct_topojson_line,
    validate_geojson,
)


_SCHEMA = Path(__file__).parents[2] / "src/mountainash/validation/schemas/GeoJSON.json"


def test_vendored_geojson_schema_has_pinned_checksum() -> None:
    """A source update must be deliberate and reviewable."""
    assert sha256(_SCHEMA.read_bytes()).hexdigest() == (
        "5456d0bdf070d3b654ee6b78c7d807c2663756931cf9f5e50726ed6241535666"
    )


def test_geojson_polygon_requires_closed_linear_rings() -> None:
    """The base schema cannot express RFC 7946 ring closure."""
    diagnostics = validate_geojson(
        {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
        }
    )

    assert [(item.instance_path, item.validator) for item in diagnostics] == [
        ("/coordinates/0", "geojson.ring_closed")
    ]


def test_topology_negative_arc_index_uses_bitwise_complement() -> None:
    """TopoJSON negative arc references select and reverse ``~index``."""
    topology = {
        "type": "Topology",
        "arcs": [
            [[0, 0], [1, 0]],
            [[1, 1], [0, -1]],
        ],
        "objects": {},
    }

    assert reconstruct_topojson_line(topology, arc_indexes=[0, -2]) == [
        (0.0, 0.0),
        (1.0, 0.0),
        (1.0, 1.0),
    ]
