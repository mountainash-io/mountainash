"""Closed wiring and AST contracts for Unit C list/category/struct operations."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.errors import InvalidOptionValueError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT,
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
)
from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType


def test_structural_keys_have_one_exact_mapping() -> None:
    expected = {
        FK_LIST.PARSE: ("parse_list", "parse_list"),
        FK_LIST.CAST_ITEMS: ("cast_list_items", "cast_list_items"),
        FK_CAT.CAST: ("cast_categorical", "cast_categorical"),
        FK_STRUCT.CAST: ("cast_struct", "cast_struct"),
    }
    for key, (name, protocol) in expected.items():
        fdef = ExpressionFunctionRegistry.get(key)
        assert fdef.substrait_name == name
        assert fdef.protocol_method.__name__ == protocol


def test_structural_nodes_keep_arguments_options_and_diagnostics_separate() -> None:
    expr = ma.col("source")
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    nodes = (
        expr.str.parse_list(item_type="integer", delimiter="|", field_name="values", failure_behavior=CaseFailureBehaviour.THROW),
        expr.list.cast_items(item_object_fields=(field,), field_name="items"),
        expr.cat.cast(value_type="integer", categories=(1, 2), ordered=True, field_name="status"),
        expr.struct.cast(fields=(field,), field_name="payload"),
    )
    for built in nodes:
        node = built._node
        assert len(node.arguments) == 1
        assert all(not hasattr(value, "_node") for value in node.options.values())
        assert "field_name" not in node.options
        assert node.diagnostic_context["field_name"]


@pytest.mark.parametrize(
    ("builder", "kwargs"),
    [
        (lambda e: e.str.parse_list(field_name="x", item_type=[]), {}),
        (lambda e: e.str.parse_list(field_name="x", delimiter=""), {}),
        (lambda e: e.list.cast_items(field_name="x", item_object_fields=()), {}),
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
        lambda e: e.list.cast_items(item_object_fields=(object(),), field_name="x"),
        lambda e: e.cat.cast(value_type="string", categories=(1,), ordered=False, field_name="x"),
        lambda e: e.cat.cast(value_type="string", categories=("x",), ordered=1, field_name="x"),
        lambda e: e.struct.cast(fields=(object(),), field_name="x"),
    ],
)
def test_every_new_builder_rejects_invalid_literal_options(builder) -> None:
    with pytest.raises(InvalidOptionValueError):
        builder(ma.col("source"))


def test_recursive_fields_remain_raw_serializable_options() -> None:
    nested = FieldSpec(
        name="payload",
        type=UniversalType.OBJECT,
        object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
    )
    node = ma.col("source").struct.cast(fields=(nested,), field_name="payload")._node
    dumped = node.model_dump(mode="json")
    assert dumped["options"]["fields"][0]["object_fields"][0]["name"] == "id"
    assert not any(type(value).__name__ == "NativeNode" for value in node.options.values())
def test_structural_builders_reject_every_invalid_literal_shape() -> None:
    source = ma.col("source")
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    invalid_builders = (
        lambda: source.str.parse_list(field_name=None),
        lambda: source.str.parse_list(field_name="x", item_type=None),
        lambda: source.str.parse_list(field_name="x", item_type=object()),
        lambda: source.str.parse_list(field_name="x", delimiter=None),
        lambda: source.str.parse_list(field_name="x", delimiter=1),
        lambda: source.str.parse_list(field_name="x", failure_behavior="throw"),
        lambda: source.list.cast_items(field_name="x", item_object_fields=None),
        lambda: source.list.cast_items(field_name="x", item_object_fields=[field]),
        lambda: source.list.cast_items(field_name="x", item_object_fields=(object(),)),
        lambda: source.cat.cast(field_name="x", value_type=None, categories=(), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="float", categories=(), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="string", categories=["x"], ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="string", categories=(1,), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="integer", categories=(True,), ordered=False),
        lambda: source.cat.cast(field_name="x", value_type="integer", categories=(1,), ordered=1),
        lambda: source.struct.cast(field_name="x", fields=None),
        lambda: source.struct.cast(field_name="x", fields=[field]),
        lambda: source.struct.cast(field_name="x", fields=(object(),)),
    )
    for build in invalid_builders:
        with pytest.raises(InvalidOptionValueError):
            build()


def test_recursive_list_and_struct_options_are_backend_agnostic() -> None:
    nested = FieldSpec(
        name="items",
        type=UniversalType.ARRAY,
        item_object_fields=[
            FieldSpec(
                name="payload",
                type=UniversalType.OBJECT,
                object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
            )
        ],
    )
    nodes = (
        ma.col("source").list.cast_items(item_object_fields=(nested,), field_name="items"),
        ma.col("source").struct.cast(fields=(nested,), field_name="payload"),
    )
    forbidden = ("NativeNode", "Expr", "DataType", "DType")
    for built in nodes:
        dumped = built._node.model_dump(mode="json")
        assert dumped["options"]
        key = "item_object_fields" if "item_object_fields" in dumped["options"] else "fields"
        assert dumped["options"][key][0]["name"] == "items"
        nested_key = "item_object_fields" if "item_object_fields" in dumped["options"][key][0] else "object_fields"
        assert dumped["options"][key][0][nested_key][0]["name"] == "payload"
        def walk(value):
            if isinstance(value, dict):
                for child in value.values():
                    yield from walk(child)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    yield from walk(child)
            else:
                yield value
        assert not any(type(value).__name__ in forbidden for value in walk(built._node.options))
        assert not any(
            type(value).__module__.startswith(("polars", "narwhals", "ibis"))
            for value in walk(built._node.options)
        )


def test_geospatial_keys_have_one_exact_mapping() -> None:
    expected = {
        FK_GEO.PARSE_GEOPOINT: ("parse_geopoint", "parse_geopoint"),
        FK_GEO.PARSE_GEOJSON: ("parse_geojson", "parse_geojson"),
        FK_GEO.SERIALIZE_GEOJSON: ("serialize_geojson", "serialize_geojson"),
    }
    for key, (name, protocol) in expected.items():
        fdef = ExpressionFunctionRegistry.get(key)
        assert fdef.substrait_name == name
        assert fdef.protocol_method.__name__ == protocol


def test_geospatial_nodes_keep_raw_options_and_diagnostics_separate() -> None:
    source = ma.col("source")
    nodes = (
        source.geo.parse_geopoint(
            format="default",
            source_representation="lexical",
            field_name="point",
        ),
        source.geo.parse_geojson(format="default", field_name="geometry"),
        source.geo.serialize_geojson(format="topojson", field_name="geometry"),
    )
    for built in nodes:
        node = built._node
        assert len(node.arguments) == 1
        assert node.options
        assert "field_name" not in node.options
        assert node.diagnostic_context["field_name"]


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


def test_geopoint_legal_format_representation_pairs() -> None:
    source = ma.col("source")
    legal = {
        ("default", "lexical"),
        ("array", "lexical"),
        ("array", "native"),
        ("object", "native"),
    }
    for format_, representation in legal:
        node = source.geo.parse_geopoint(
            format=format_,
            source_representation=representation,
            field_name="point",
        )._node
        assert node.options["format"] == format_
        assert node.options["source_representation"] == representation
