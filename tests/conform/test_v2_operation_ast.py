"""Input validation for list/category/struct and geospatial operation builders."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.errors import InvalidOptionValueError
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.typespec.spec import FieldDefinition
from mountainash.typespec.universal_types import UniversalType


@pytest.mark.parametrize(
    ("builder", "kwargs"),
    [
        (lambda e: e.str.parse_list(field_name="x", item_type=[]), {}),
        (lambda e: e.str.parse_list(field_name="x", delimiter=""), {}),
        (lambda e: e.list.cast_items(field_name="x", element=None), {}),
        (lambda e: e.cat.cast(field_name="x", value_type="bad", categories=(), ordered=False), {}),
        (lambda e: e.struct.cast(field_name="x", fields=()), {}),
        (lambda e: e.cat.cast(field_name="x", value_type="integer", categories=(True,), ordered=False), {}),
    ],
)
def test_invalid_options_fail_before_node_creation(builder, kwargs) -> None:
    with pytest.raises(InvalidOptionValueError):
        builder(ma.col("source"), **kwargs)


@pytest.mark.parametrize(
    "builder",
    [
        lambda e: e.str.parse_list(field_name="", failure_behavior=CaseFailureBehaviour.THROW),
        lambda e: e.str.parse_list(field_name="x", failure_behavior="throw"),
        lambda e: e.list.cast_items(element=object(), field_name="x"),
        lambda e: e.cat.cast(value_type="string", categories=(1,), ordered=False, field_name="x"),
        lambda e: e.cat.cast(value_type="string", categories=("x",), ordered=1, field_name="x"),
        lambda e: e.struct.cast(fields=(object(),), field_name="x"),
    ],
)
def test_every_new_builder_rejects_invalid_literal_options(builder) -> None:
    with pytest.raises(InvalidOptionValueError):
        builder(ma.col("source"))


def test_structural_builders_reject_every_invalid_literal_shape() -> None:
    source = ma.col("source")
    field = FieldDefinition(type=UniversalType.INTEGER)
    invalid_builders = (
        lambda: source.str.parse_list(field_name=None),
        lambda: source.str.parse_list(field_name="x", item_type=None),
        lambda: source.str.parse_list(field_name="x", item_type=object()),
        lambda: source.str.parse_list(field_name="x", delimiter=None),
        lambda: source.str.parse_list(field_name="x", delimiter=1),
        lambda: source.str.parse_list(field_name="x", failure_behavior="throw"),
        lambda: source.cat.cast(field_name="x", value_type=None, categories=(), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="float", categories=(), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="string", categories=["x"], ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="string", categories=(1,), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="integer", categories=(True,), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="integer", categories=(1,), ordered=1),
        lambda: source.struct.cast(field_name="x", fields=None),
        lambda: source.struct.cast(field_name="x", fields=[field]),
        lambda: source.struct.cast(field_name="x", fields={"id": object()}),
    )
    for build in invalid_builders:
        with pytest.raises(InvalidOptionValueError):
            build()


@pytest.mark.parametrize(
    "build",
    [
        lambda source: source.geo.parse_geopoint(
            format="default",
            source_representation="native",
            field_name="point",
        ),
        lambda source: source.geo.parse_geopoint(
            format="object",
            source_representation="lexical",
            field_name="point",
        ),
        lambda source: source.geo.parse_geopoint(
            format="bad",
            source_representation="lexical",
            field_name="point",
        ),
        lambda source: source.geo.parse_geopoint(
            format="array",
            source_representation="lexical",
            field_name="point",
            failure_behavior="throw",
        ),
        lambda source: source.geo.parse_geojson(format="bad", field_name="geometry"),
        lambda source: source.geo.parse_geopoint(
            format="default",
            source_representation="lexical",
            field_name="",
        ),
    ],
)
def test_geospatial_builders_reject_invalid_options_before_node_creation(build) -> None:
    with pytest.raises(InvalidOptionValueError):
        build(ma.col("source"))


