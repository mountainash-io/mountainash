"""Executable nested struct/list casts driven by complete field definitions."""
from __future__ import annotations

import pytest
from ibis.common.exceptions import UnsupportedBackendType

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
)
from mountainash.typespec.spec import FieldDefinition

I16 = FieldDefinition(dtype=D.I16)
I64 = FieldDefinition(dtype=D.I64)
TEXT = FieldDefinition(dtype=D.STRING)
LIST_BACKENDS = ("polars", "polars-lazy", "ibis-duckdb")


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListCastElements:
    def test_scalar_element_dtype_cast(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"xs": [["1", "2"], None]}, backend_name)
        expr = ma.col("xs").list.cast_items(element=I64, field_name="xs")
        assert collect_expr(df, expr) == [[1, 2], None]

    def test_scalar_element_conversion_is_executed(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"xs": [[1, None], [2], None]}, backend_name)
        expr = ma.col("xs").list.agg(ma.element().fill_null(0)).list.cast_items(
            element=I16,
            field_name="xs",
        )
        assert collect_expr(df, expr) == [[1, 0], [2], None]

    def test_nested_collection_dtype_cast(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"xs": [[[{"id": "1"}], [{"id": "2"}]]]}, backend_name)
        element = FieldDefinition(element=FieldDefinition(fields={"id": I64}))
        expr = ma.col("xs").list.cast_items(element=element, field_name="xs")
        assert collect_expr(df, expr) == [[[{"id": 1}], [{"id": 2}]]]

    def test_nested_scalar_conversion_reaches_innermost_elements(
        self, backend_name, backend_factory, collect_expr,
    ):
        df = backend_factory.create({"xs": [[[1, None], [2]], None]}, backend_name)
        inner = ma.element().list.agg(ma.element().fill_null(0)).list.cast_items(
            element=I16,
            field_name="xs",
        )
        expr = ma.col("xs").list.agg(inner)
        assert collect_expr(df, expr) == [[[1, 0], [2]], None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ("polars", "ibis-duckdb"))
class TestStructCastChildren:
    def test_children_follow_mapping_order(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(
            {"p": [{"y": 1, "x": "a"}, None], "v": [10, 20], "w": ["q", "r"]}, backend_name,
        )
        expr = ma.col("p").struct.cast(
            fields={"y": I64, "x": TEXT},
            converted_fields=(("y", ma.col("v")), ("x", ma.col("w"))),
            field_name="p",
        )
        values = collect_expr(df, expr)
        assert values == [{"y": 10, "x": "q"}, None]
        assert list(values[0]) == ["y", "x"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_struct_null_mode_atomicity_is_supported_only_where_declared(
    backend_name, backend_factory, collect_expr,
):
    if backend_name == "ibis-sqlite":
        with pytest.raises(UnsupportedBackendType):
            backend_factory.create({"p": [{"id": "bad"}, {"id": "2"}]}, backend_name)
        return
    df = backend_factory.create({"p": [{"id": "bad"}, {"id": "2"}]}, backend_name)
    expr = ma.col("p").struct.cast(
        fields={"id": I64}, field_name="p", failure_behavior=CaseFailureBehaviour.NULL,
    )
    if backend_name in {"polars", "polars-lazy"}:
        assert collect_expr(df, expr) == [None, {"id": 2}]
        return
    with pytest.raises(BackendCapabilityError) as error:
        collect_expr(df, expr)
    assert error.value.function_key is FK_STRUCT.CAST
