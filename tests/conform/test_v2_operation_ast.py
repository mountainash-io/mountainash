"""Closed wiring and AST contracts for Unit C list/category/struct operations."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.errors import InvalidOptionValueError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT,
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
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
