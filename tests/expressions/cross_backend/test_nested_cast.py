"""Executable nested struct/list casts driven by complete container dtypes."""
from __future__ import annotations

import pytest
from ibis.common.exceptions import UnsupportedBackendType

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.core.dtypes import ListDtype, MountainashDtype as D, StructDtype
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
)

LIST_BACKENDS = ("polars", "polars-lazy", "ibis-duckdb")


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListCastElements:
    def test_scalar_element_dtype_cast(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"xs": [["1", "2"], None]}, backend_name)
        expr = ma.col("xs").list.cast_items(dtype=ListDtype(D.I64), field_name="xs")
        assert collect_expr(df, expr) == [[1, 2], None]

    def test_scalar_element_conversion_is_executed(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"xs": [[1, None], [2], None]}, backend_name)
        expr = ma.col("xs").list.agg(ma.element().fill_null(0)).list.cast_items(
            dtype=ListDtype(D.I16),
            field_name="xs",
        )
        assert collect_expr(df, expr) == [[1, 0], [2], None]

    def test_nested_collection_dtype_cast(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"xs": [[[{"id": "1"}], [{"id": "2"}]]]}, backend_name)
        dtype = ListDtype(ListDtype(StructDtype((("id", D.I64),))))
        expr = ma.col("xs").list.cast_items(dtype=dtype, field_name="xs")
        assert collect_expr(df, expr) == [[[{"id": 1}], [{"id": 2}]]]

    def test_nested_scalar_conversion_reaches_innermost_elements(
        self, backend_name, backend_factory, collect_expr,
    ):
        df = backend_factory.create({"xs": [[[1, None], [2]], None]}, backend_name)
        inner = ma.element().list.agg(ma.element().fill_null(0)).list.cast_items(
            dtype=ListDtype(D.I16),
            field_name="xs",
        )
        expr = ma.col("xs").list.agg(inner)
        assert collect_expr(df, expr) == [[[1, 0], [2]], None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ("polars", "ibis-duckdb"))
class TestStructCastChildren:
    def test_children_follow_dtype_member_order(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(
            {"p": [{"y": 1, "x": "a"}, None], "v": [10, 20], "w": ["q", "r"]}, backend_name,
        )
        expr = ma.col("p").struct.cast(
            dtype=StructDtype((("y", D.I64), ("x", D.STRING))),
            converted_fields=(("y", ma.col("v")), ("x", ma.col("w"))),
            field_name="p",
        )
        values = collect_expr(df, expr)
        assert values == [{"y": 10, "x": "q"}, None]
        assert list(values[0]) == ["y", "x"]

    def test_reordered_children_are_rebuilt_in_dtype_order(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(
            {"p": [{"y": 1, "x": "a"}, None], "v": [10, 20], "w": ["q", "r"]}, backend_name,
        )
        expr = ma.col("p").struct.cast(
            dtype=StructDtype((("x", D.STRING), ("y", D.I64))),
            converted_fields=(("x", ma.col("w")), ("y", ma.col("v"))),
            field_name="p",
        )
        values = collect_expr(df, expr)
        assert values == [{"x": "q", "y": 10}, None]
        assert list(values[0]) == ["x", "y"]

    def test_unchanged_member_supplied_from_source_is_preserved(
        self, backend_name, backend_factory, collect_expr,
    ):
        df = backend_factory.create(
            {"p": [{"y": 1, "z": "keep"}, None], "v": [10, 20]}, backend_name,
        )
        expr = ma.col("p").struct.cast(
            dtype=StructDtype((("y", D.I64), ("z", D.STRING))),
            converted_fields=(("y", ma.col("v")), ("z", ma.col("p").struct.field("z"))),
            field_name="p",
        )
        assert collect_expr(df, expr) == [{"y": 10, "z": "keep"}, None]

    def test_validity_false_yields_typed_null_without_hidden_child(
        self, backend_name, backend_factory, collect_expr,
    ):
        df = backend_factory.create(
            {"p": [{"id": "1"}, {"id": "bad"}, None], "v": ["1", "bad", "3"]}, backend_name,
        )
        child = ma.col("v").cast(D.I64, failure_behavior="null")
        expr = ma.col("p").struct.cast(
            dtype=StructDtype((("id", D.I64),)),
            converted_fields=(("id", child),),
            converted_validity=child.is_not_null(),
            field_name="p",
        )
        assert collect_expr(df, expr) == [{"id": 1}, None, None]

    def test_zero_children_cast_original_directly(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"p": [{"id": "1"}, None]}, backend_name)
        expr = ma.col("p").struct.cast(dtype=StructDtype((("id", D.I64),)), field_name="p")
        assert collect_expr(df, expr) == [{"id": 1}, None]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
def test_list_empty_and_null_containers_stay_distinct(backend_name, backend_factory, collect_expr):
    df = backend_factory.create({"xs": [["1"], [], None]}, backend_name)
    expr = ma.col("xs").list.cast_items(dtype=ListDtype(D.I64), field_name="xs")
    assert collect_expr(df, expr) == [[1], [], None]


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
        dtype=StructDtype((("id", D.I64),)), field_name="p", failure_behavior=CaseFailureBehaviour.NULL,
    )
    if backend_name in {"polars", "polars-lazy"}:
        assert collect_expr(df, expr) == [None, {"id": 2}]
        return
    with pytest.raises(BackendCapabilityError) as error:
        collect_expr(df, expr)
    assert error.value.function_key is FK_STRUCT.CAST


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("container", ["list", "struct"])
@pytest.mark.parametrize("width", [16, 64])
def test_container_dtype_controls_physical_result(
    backend_name, backend_factory, container, width,
):
    import polars as pl

    values = [[1, None], [], None] if container == "list" else [{"v": 1}, {"v": None}, None]
    if backend_name == "ibis-sqlite":
        with pytest.raises(UnsupportedBackendType):
            backend_factory.create({"value": values}, backend_name)
        return
    source = backend_factory.create({"value": values}, backend_name)
    scalar = D.I16 if width == 16 else D.I64
    native_scalar = pl.Int16 if width == 16 else pl.Int64
    if container == "list":
        expr = ma.col("value").list.cast_items(dtype=ListDtype(scalar), field_name="value")
        expected_type = pl.List(native_scalar)
    else:
        expr = ma.col("value").struct.cast(dtype=StructDtype((("v", scalar),)), field_name="value")
        expected_type = pl.Struct({"v": native_scalar})
    relation = ma.relation(source).select(expr)
    if container == "struct" and backend_name in {"pandas", "narwhals-pandas"}:
        with pytest.raises(BackendCapabilityError, match="cannot preserve null input structs"):
            relation.to_polars()
        return
    result = relation.to_polars()
    assert result.schema["value"] == expected_type
    assert result["value"].to_list() == values


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("route", ["direct", "converted-child", "general-cast"])
@pytest.mark.parametrize("nullable_parent", [False, True])
def test_struct_float32_checks_actual_member_values(
    backend_name, backend_factory, route, nullable_parent, request,
):
    import polars as pl

    if backend_name == "ibis-sqlite":
        with pytest.raises(UnsupportedBackendType):
            backend_factory.create({"p": [{"v": 1.5}]}, backend_name)
        return

    def frame(data):
        # Numeric safety uses structural dtype evidence, not inspection of
        # Python objects stored in an untyped pandas object column.
        if backend_name in {"pandas", "narwhals-pandas"}:
            import narwhals as nw
            import pandas as pd

            native = pl.DataFrame(data).to_arrow().to_pandas(types_mapper=pd.ArrowDtype)
            return nw.from_native(native) if backend_name == "narwhals-pandas" else native
        return backend_factory.create(data, backend_name)

    target = StructDtype((("v", D.FP32),))
    if route == "general-cast":
        expression = ma.col("p").cast(target)
    else:
        children = (("v", ma.col("replacement")),) if route == "converted-child" else ()
        expression = ma.col("p").struct.cast(
            dtype=target, field_name="p", converted_fields=children,
        )
    values = [{"v": 1.5}, None] if nullable_parent else [{"v": 1.5}]
    source = frame({"p": values, "replacement": [1.5] * len(values)})
    if route == "general-cast" and backend_name in {"pandas", "narwhals-pandas"}:
        from pyarrow import ArrowInvalid

        request.applymarker(pytest.mark.xfail(
            strict=True, raises=ArrowInvalid,
            reason="342: native Narwhals pandas typed nested-null broadcast",
        ))
    if backend_name in {"pandas", "narwhals-pandas"} and route != "general-cast":
        with pytest.raises(BackendCapabilityError, match="cannot preserve null input structs"):
            ma.relation(source).select(expression).to_polars()
        return
    result = ma.relation(source).select(expression).to_polars()
    assert result.to_series().to_list() == values
    assert result.to_series().dtype == pl.Struct({"v": pl.Float32})
    source = frame({
        "p": [{"v": 1.5 if route == "converted-child" else 1e100}],
        "replacement": [1e100],
    })
    with pytest.raises(Exception) as raised:
        ma.relation(source).select(expression).to_polars()
    assert not isinstance(raised.value, (BackendCapabilityError, NotImplementedError, AttributeError, TypeError))


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("route", ["direct", "conform"])
def test_zero_member_struct_keeps_parent_null(backend_name, backend_factory, route):
    import polars as pl
    from mountainash.typespec import FieldDefinition, TableSchema

    data = {"value": [{"v": 1}, None]}
    if backend_name == "ibis-sqlite":
        with pytest.raises(UnsupportedBackendType):
            backend_factory.create(data, backend_name)
        return
    relation = ma.relation(backend_factory.create(data, backend_name))
    if route == "direct":
        relation = relation.select(ma.col("value").struct.cast(dtype=StructDtype(()), field_name="value"))
    else:
        relation = relation.conform(TableSchema(fields={"value": FieldDefinition(fields={})}, missing_values=[]))
    if route == "direct" and backend_name in {"pandas", "narwhals-pandas"}:
        with pytest.raises(BackendCapabilityError, match="cannot preserve null input structs"):
            relation.to_polars()
        return
    if backend_name == "ibis-duckdb":
        from duckdb import ParserException

        # DuckDB cannot represent STRUCT(); this is not unknown membership.
        with pytest.raises(ParserException, match="syntax error"):
            relation.to_polars()
        return
    result = relation.to_polars()
    assert result.schema["value"] == pl.Struct({})
    assert result["value"].to_list() == [{}, None]
