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


def test_geojson_value_rule_preserves_structured_diagnostic() -> None:
    """GeoJSON semantic failures retain their instance path and validator."""
    import polars as pl

    from mountainash.validation import ValidationRunner, ValueRule, ValueValidatorKey

    result = ValidationRunner().validate_relation(
        pl.DataFrame(
            {
                "geometry": [
                    {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                    }
                ]
            }
        ),
        [
            ValueRule(
                id="geometry_geojson",
                fields=["geometry"],
                validator=ValueValidatorKey.GEOJSON,
                options={},
            )
        ],
    )

    assert result.failure_cases.select(
        "instance_path", "schema_path", "validator"
    ).to_dicts() == [
        {
            "instance_path": "/coordinates/0",
            "schema_path": None,
            "validator": "geojson.ring_closed",
        }
    ]


def test_topology_negative_arc_index_uses_bitwise_complement() -> None:
    """TopoJSON negative arc references select and reverse ``~index``."""
    topology = {
        "type": "Topology",
        "transform": {"scale": [1, 1], "translate": [0, 0]},
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


def test_unquantized_topojson_arcs_are_absolute_positions() -> None:
    """Only transformed TopoJSON arcs use delta encoding."""
    topology = {
        "type": "Topology",
        "arcs": [[[10, 10], [20, 20]]],
        "objects": {},
    }

    assert reconstruct_topojson_line(topology, arc_indexes=[0]) == [
        (10.0, 10.0),
        (20.0, 20.0),
    ]


def test_topojson_rejects_out_of_range_object_arc_reference() -> None:
    """Object geometry arc indexes must resolve against the topology table."""
    from mountainash.validation.geospatial import validate_topojson

    diagnostics = validate_topojson(
        {
            "type": "Topology",
            "arcs": [[[0, 0], [1, 1]]],
            "objects": {"bad": {"type": "LineString", "arcs": [99]}},
        }
    )

    assert [(item.instance_path, item.validator) for item in diagnostics] == [
        ("/objects/bad/arcs/0", "topojson.arc_index")
    ]
