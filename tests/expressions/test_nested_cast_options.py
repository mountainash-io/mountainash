"""Nested struct/list cast option contract: ordered named definitions and complete elements."""
from __future__ import annotations

import inspect

import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.errors import InvalidOptionValueError
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import (
    MountainAshScalarListAPIBuilderProtocol,
    MountainAshScalarStructAPIBuilderProtocol,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarListExpressionSystemProtocol,
    MountainAshScalarStructExpressionSystemProtocol,
)
from mountainash.typespec.spec import FieldDefinition

I64 = FieldDefinition(dtype=D.I64)
TEXT = FieldDefinition(dtype=D.STRING)
RECORD = FieldDefinition(fields={"id": I64})


def test_struct_cast_carries_named_definitions_in_declared_order():
    declared = {"b": I64, "a": TEXT}
    node = ma.col("p").struct.cast(fields=declared, field_name="p")._node
    assert list(node.options["fields"]) == ["b", "a"]
    assert node.options["fields"]["b"] is I64
    assert node.options["fields"]["a"] is TEXT


def test_struct_cast_owns_its_field_mapping():
    declared = {"id": I64}
    node = ma.col("p").struct.cast(fields=declared, field_name="p")._node
    declared["late"] = TEXT
    assert list(node.options["fields"]) == ["id"]


def test_list_cast_carries_complete_element_definition():
    nested = FieldDefinition(element=RECORD)
    node = ma.col("xs").list.cast_items(element=nested, field_name="xs")._node
    assert node.options["element"] is nested


def test_list_cast_lexical_item_type_stays_distinct_from_element():
    node = ma.col("xs").list.cast_items(item_type="integer", field_name="xs")._node
    assert node.options["item_type"] == "integer"
    assert node.options.get("element") is None


@pytest.mark.parametrize(
    "fields",
    [
        None,
        (("id", I64),),
        [I64],
        {"id": object()},
        {"id": "i64"},
        {1: I64},
    ],
    ids=["none", "pairs", "sequence", "object-child", "string-child", "non-str-name"],
)
def test_struct_cast_rejects_non_mapping_of_definitions(fields):
    with pytest.raises(InvalidOptionValueError):
        ma.col("p").struct.cast(fields=fields, field_name="p")


def test_struct_cast_accepts_declared_empty_record():
    node = ma.col("p").struct.cast(fields={}, field_name="p")._node
    assert dict(node.options["fields"]) == {}


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"element": None},
        {"element": object()},
        {"element": {"id": I64}},
        {"element": (I64,)},
    ],
    ids=["missing", "none", "object", "field-mapping", "definition-sequence"],
)
def test_list_cast_requires_one_complete_definition_when_no_item_type(kwargs):
    with pytest.raises(InvalidOptionValueError):
        ma.col("xs").list.cast_items(field_name="xs", **kwargs)


def test_retired_object_field_keywords_are_not_accepted():
    with pytest.raises(TypeError):
        ma.col("xs").list.cast_items(item_object_fields=(I64,), field_name="xs")
    with pytest.raises(TypeError):
        ma.col("p").struct.cast(object_fields=(I64,), field_name="p")


@pytest.mark.parametrize(
    ("owner", "method", "present", "absent"),
    [
        (MountainAshScalarStructAPIBuilderProtocol, "cast", "fields", None),
        (MountainAshScalarStructExpressionSystemProtocol, "cast_struct", "fields", None),
        (MountainAshScalarListAPIBuilderProtocol, "cast_items", "element", "item_object_fields"),
        (MountainAshScalarListExpressionSystemProtocol, "cast_list_items", "element", "item_object_fields"),
    ],
)
def test_protocols_publish_new_option_names(owner, method, present, absent):
    parameters = inspect.signature(getattr(owner, method)).parameters
    assert present in parameters
    if absent is not None:
        assert absent not in parameters
