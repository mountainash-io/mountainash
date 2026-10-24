"""Nested struct/list cast builder contract: complete container dtype, real rejection, exact signatures."""
from __future__ import annotations

import inspect

import pytest

import mountainash as ma
from mountainash.core.dtypes import ListDtype, MountainashDtype as D, StructDtype
from mountainash.core.errors import InvalidOptionValueError
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import (
    MountainAshScalarListAPIBuilderProtocol,
    MountainAshScalarStructAPIBuilderProtocol,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarListExpressionSystemProtocol,
    MountainAshScalarStructExpressionSystemProtocol,
)

RECORD = StructDtype((("id", D.I64),))


@pytest.mark.parametrize(
    "dtype",
    [None, D.I64, ListDtype(D.I64), "i64", ()],
    ids=["none", "scalar", "list", "scalar-alias", "tuple"],
)
def test_struct_cast_rejects_non_struct_dtype(dtype):
    with pytest.raises(InvalidOptionValueError):
        ma.col("p").struct.cast(dtype=dtype, field_name="p")


@pytest.mark.parametrize(
    "dtype",
    [None, D.I64, RECORD, "i64"],
    ids=["none", "scalar", "struct", "scalar-alias"],
)
def test_list_cast_rejects_non_list_dtype(dtype):
    with pytest.raises(InvalidOptionValueError):
        ma.col("xs").list.cast_items(dtype=dtype, field_name="xs")


@pytest.mark.parametrize(
    "converted_fields",
    [[("id", ma.lit(1))], (("id",),), ((1, ma.lit(1)),), (("id", 1),), "id"],
    ids=["list", "short-pair", "non-str-name", "non-expression", "string"],
)
def test_struct_cast_rejects_malformed_converted_fields(converted_fields):
    with pytest.raises(InvalidOptionValueError):
        ma.col("p").struct.cast(dtype=RECORD, field_name="p", converted_fields=converted_fields)


def test_struct_cast_rejects_non_expression_validity():
    with pytest.raises(InvalidOptionValueError):
        ma.col("p").struct.cast(dtype=RECORD, field_name="p", converted_validity=True)


@pytest.mark.parametrize(
    "kwargs,error",
    [({}, TypeError), ({"dtype": None}, InvalidOptionValueError)],
    ids=["missing", "none"],
)
def test_dtype_is_mandatory(kwargs, error):
    with pytest.raises(error):
        ma.col("xs").list.cast_items(field_name="xs", **kwargs)
    with pytest.raises(error):
        ma.col("p").struct.cast(field_name="p", **kwargs)


def test_superseded_authoring_keywords_are_not_accepted():
    for build in (
        lambda: ma.col("xs").list.cast_items(element=object(), field_name="xs"),
        lambda: ma.col("xs").list.cast_items(item_type="integer", field_name="xs"),
        lambda: ma.col("xs").list.cast_items(item_object_fields=(), field_name="xs"),
        lambda: ma.col("p").struct.cast(fields={}, field_name="p"),
        lambda: ma.col("p").struct.cast(object_fields=(), field_name="p"),
    ):
        with pytest.raises(TypeError):
            build()


@pytest.mark.parametrize(
    ("owner", "method", "expected"),
    [
        (MountainAshScalarStructAPIBuilderProtocol, "cast",
         ["self", "dtype", "field_name", "failure_behavior", "converted_fields", "converted_validity"]),
        (MountainAshScalarListAPIBuilderProtocol, "cast_items",
         ["self", "dtype", "field_name", "failure_behavior"]),
        (MountainAshScalarStructExpressionSystemProtocol, "cast_struct",
         ["self", "x", "converted_fields", "dtype", "field_names", "failure_behavior"]),
        (MountainAshScalarListExpressionSystemProtocol, "cast_list_items",
         ["self", "x", "dtype", "failure_behavior"]),
    ],
)
def test_protocols_publish_dtype_signature(owner, method, expected):
    parameters = inspect.signature(getattr(owner, method)).parameters
    assert list(parameters) == expected
    assert parameters["dtype"].default is inspect.Parameter.empty
    assert parameters["dtype"].kind is inspect.Parameter.KEYWORD_ONLY
    for retired in ("fields", "element", "item_type", "resolved_target"):
        assert retired not in parameters


def test_execution_protocol_child_and_policy_channels():
    struct = inspect.signature(MountainAshScalarStructExpressionSystemProtocol.cast_struct).parameters
    assert struct["x"].kind is inspect.Parameter.POSITIONAL_ONLY
    assert struct["converted_fields"].kind is inspect.Parameter.VAR_POSITIONAL
    assert struct["field_names"].default == ()
    assert struct["failure_behavior"].default == "throw"
    items = inspect.signature(MountainAshScalarListExpressionSystemProtocol.cast_list_items).parameters
    assert items["x"].kind is inspect.Parameter.POSITIONAL_ONLY
    assert items["failure_behavior"].default == "throw"
