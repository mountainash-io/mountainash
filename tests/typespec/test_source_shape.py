from __future__ import annotations

from typing import Any

import pytest

from mountainash.core.dtypes import MountainashDtype, NativeDtype, TimeDtype, TypeTarget
from mountainash.typespec.source_shape import SourceShape, extract_source_shapes


def test_source_shape_rejects_children_on_scalar() -> None:
    with pytest.raises(ValueError, match="only LIST can have item_shape"):
        SourceShape(
            MountainashDtype.STRING,
            item_shape=SourceShape(MountainashDtype.I64),
        )


def test_source_shape_rejects_duplicate_struct_fields() -> None:
    child = SourceShape(MountainashDtype.STRING)
    with pytest.raises(ValueError, match="unique"):
        SourceShape(
            MountainashDtype.STRUCT,
            struct_fields=(("id", child), ("id", child)),
        )


def test_source_shape_rejects_mixed_children() -> None:
    with pytest.raises(ValueError):
        SourceShape(
            MountainashDtype.STRUCT,
            item_shape=SourceShape(MountainashDtype.STRING),
            struct_fields=(("value", SourceShape(MountainashDtype.STRING)),),
        )


def test_source_shape_rejects_struct_children_on_non_struct() -> None:
    with pytest.raises(ValueError, match="only STRUCT can have struct_fields"):
        SourceShape(
            MountainashDtype.STRING,
            struct_fields=(("value", SourceShape(MountainashDtype.STRING)),),
        )


def test_source_shape_allows_unknown_leaf() -> None:
    assert SourceShape(None) == SourceShape(canonical_type=None)


@pytest.mark.parametrize(
    ("dtype", "expected_item"),
    [
        ("list", SourceShape(MountainashDtype.I64)),
        ("array", SourceShape(MountainashDtype.FP64)),
    ],
)
def test_polars_list_shape_keeps_child(dtype: str, expected_item: SourceShape) -> None:
    pl = pytest.importorskip("polars")
    native = pl.List(pl.Int64) if dtype == "list" else pl.Array(pl.Float64, shape=(2,))
    frame = pl.DataFrame(schema={"values": native})
    shape = extract_source_shapes(frame)["values"]
    assert shape.canonical_type is MountainashDtype.LIST
    assert shape.item_shape == expected_item


def test_polars_struct_shape_is_recursive() -> None:
    pl = pytest.importorskip("polars")
    dtype = pl.Struct(
        [
            pl.Field("id", pl.Int64),
            pl.Field("labels", pl.List(pl.String)),
            pl.Field("nested", pl.Struct([pl.Field("ok", pl.Boolean)])),
        ]
    )
    shape = extract_source_shapes(pl.DataFrame(schema={"record": dtype}))["record"]
    assert shape == SourceShape(
        MountainashDtype.STRUCT,
        struct_fields=(
            ("id", SourceShape(MountainashDtype.I64)),
            ("labels", SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.STRING))),
            (
                "nested",
                SourceShape(
                    MountainashDtype.STRUCT,
                    struct_fields=(("ok", SourceShape(MountainashDtype.BOOL)),),
                ),
            ),
        ),
    )


def test_unsupported_top_level_carrier_has_qualified_name() -> None:
    class UnsupportedCarrier:
        pass

    with pytest.raises(TypeError, match=r"unsupported schema carrier .*UnsupportedCarrier"):
        extract_source_shapes(UnsupportedCarrier())


def test_pyarrow_list_families_keep_child() -> None:
    pa = pytest.importorskip("pyarrow")
    table = pa.table(
        {
            "list": pa.array([[1], [2]], type=pa.list_(pa.int64())),
            "large": pa.array([[1], [2]], type=pa.large_list(pa.int32())),
            "fixed": pa.array([[1, 2], [3, 4]], type=pa.list_(pa.int16(), 2)),
        }
    )
    shapes = extract_source_shapes(table)
    assert shapes["list"].item_shape == SourceShape(MountainashDtype.I64)
    assert shapes["large"].item_shape == SourceShape(MountainashDtype.I32)
    assert shapes["fixed"].item_shape == SourceShape(MountainashDtype.I16)

    if hasattr(pa, "list_view"):
        views = pa.table(
            {
                "view": pa.array([[1], [2]], type=pa.list_view(pa.int64())),
                "large_view": pa.array([[1], [2]], type=pa.large_list_view(pa.int32())),
            }
        )
        view_shapes = extract_source_shapes(views)
        assert view_shapes["view"].item_shape == SourceShape(MountainashDtype.I64)
        assert view_shapes["large_view"].item_shape == SourceShape(MountainashDtype.I32)



def test_polars_timestamp_shape_retains_parameters_for_extraction():
    pl = pytest.importorskip("polars")
    from mountainash.core.dtypes import TimestampDtype

    shape = extract_source_shapes(
        pl.DataFrame(schema={"at": pl.Datetime("ns", "UTC")})
    )["at"]
    assert shape.detailed_dtype == TimestampDtype(9, True, "UTC")

def test_pyarrow_struct_shape_is_recursive() -> None:
    pa = pytest.importorskip("pyarrow")
    dtype = pa.struct(
        [
            pa.field("id", pa.int64()),
            pa.field("items", pa.list_(pa.string())),
            pa.field("nested", pa.struct([pa.field("ok", pa.bool_())])),
        ]
    )
    shape = extract_source_shapes(pa.table({"record": pa.array([], type=dtype)}))["record"]
    assert shape.struct_fields[0] == ("id", SourceShape(MountainashDtype.I64))
    assert shape.struct_fields[1] == (
        "items",
        SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.STRING)),
    )
    assert shape.struct_fields[2][1].struct_fields == (("ok", SourceShape(MountainashDtype.BOOL)),)


def test_pandas_arrow_lists_are_inspected_from_dtype_only() -> None:
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    dtype = pd.ArrowDtype(__import__("pyarrow").list_(__import__("pyarrow").int64()))
    frame = pd.DataFrame({"values": pd.Series([], dtype=dtype)})
    shape = extract_source_shapes(frame)["values"]
    assert shape == SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))


def test_ibis_non_table_expression_is_unsupported() -> None:
    ibis = pytest.importorskip("ibis")
    with pytest.raises(TypeError, match=r"unsupported schema carrier .*IntegerScalar"):
        extract_source_shapes(ibis.literal(1))


def test_ibis_arrays_and_structs_are_recursive() -> None:
    ibis = pytest.importorskip("ibis")
    dtype = ibis.expr.datatypes.Struct.from_string("struct<id: int64, items: array<int64>>")
    table = ibis.table({"record": dtype}, name="records")
    shape = extract_source_shapes(table)["record"]
    assert shape.canonical_type is MountainashDtype.STRUCT
    assert shape.struct_fields[0] == ("id", SourceShape(MountainashDtype.I64))
    assert shape.struct_fields[1] == (
        "items",
        SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64)),
    )


def test_narwhals_exposes_child_dtypes() -> None:
    nw = pytest.importorskip("narwhals")
    pl = pytest.importorskip("polars")
    frame = nw.from_native(pl.DataFrame(schema={"values": pl.List(pl.Int64)}))
    shape = extract_source_shapes(frame)["values"]
    assert shape == SourceShape(MountainashDtype.LIST, SourceShape(MountainashDtype.I64))


def test_pandas_object_column_is_opaque_without_row_access(monkeypatch: pytest.MonkeyPatch) -> None:
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame({"values": pd.Series([], dtype=object)})

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("row access is forbidden")

    monkeypatch.setattr(pd.DataFrame, "__getitem__", fail)
    monkeypatch.setattr(pd.DataFrame, "iterrows", fail)
    assert extract_source_shapes(frame)["values"] == SourceShape(None)


def test_narwhals_pandas_object_column_is_opaque_without_row_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    nw = pytest.importorskip("narwhals")
    pd = pytest.importorskip("pandas")
    frame = nw.from_native(pd.DataFrame({"values": pd.Series([], dtype=object)}))

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("row access is forbidden")

    monkeypatch.setattr(pd.DataFrame, "__getitem__", fail)
    monkeypatch.setattr(pd.DataFrame, "iterrows", fail)
    assert extract_source_shapes(frame)["values"] == SourceShape(None)


# ---------------------------------------------------------------------------
# Wrapped carriers, lazy carriers and execution placement
# ---------------------------------------------------------------------------


def _arrow_time_frame():
    pd = pytest.importorskip("pandas")
    pa = pytest.importorskip("pyarrow")
    return pd.DataFrame({"t": pd.Series([], dtype=pd.ArrowDtype(pa.time64("us")))})


def test_wrapped_pandas_keeps_underlying_precision_with_narwhals_native_evidence() -> None:
    nw = pytest.importorskip("narwhals")
    shape = extract_source_shapes(nw.from_native(_arrow_time_frame()))["t"]
    assert shape.detailed_dtype == TimeDtype(6)
    assert shape.native_dtype is not None
    assert shape.native_dtype.target is TypeTarget.NARWHALS


def test_wrapped_arrow_table_keeps_underlying_precision_with_narwhals_native_evidence() -> None:
    nw = pytest.importorskip("narwhals")
    pa = pytest.importorskip("pyarrow")
    table = pa.table({"t": pa.array([], type=pa.time64("us"))})
    shape = extract_source_shapes(nw.from_native(table))["t"]
    assert shape.detailed_dtype == TimeDtype(6)
    assert shape.native_dtype is not None
    assert shape.native_dtype.target is TypeTarget.NARWHALS


def test_standalone_decode_reports_only_the_evidence_the_schema_contains() -> None:
    nw = pytest.importorskip("narwhals")
    from mountainash.typespec.adapter_registry import get_native_schema_adapter

    adapter = get_native_schema_adapter(TypeTarget.NARWHALS)
    frame = nw.from_native(_arrow_time_frame())
    decoded = adapter.decode_schema(frame.collect_schema())["t"]
    acquired = adapter.extract_schema(frame)["t"]
    assert decoded.detailed_dtype != TimeDtype(6)
    assert acquired.detailed_dtype == TimeDtype(6)


def test_execution_through_narwhals_does_not_change_the_native_schema_target() -> None:
    pd = pytest.importorskip("pandas")
    pytest.importorskip("narwhals")
    frame = pd.DataFrame({"x": [1]})
    placed = extract_source_shapes(frame, target=TypeTarget.NARWHALS)["x"]
    native = extract_source_shapes(frame)["x"]
    assert placed.native_dtype.target is TypeTarget.NARWHALS
    assert native.native_dtype.target is TypeTarget.PANDAS
    assert placed.canonical_type is native.canonical_type is MountainashDtype.I64


@pytest.mark.parametrize("lazy", [False, True])
def test_polars_and_narwhals_lazy_carriers_are_schema_only(lazy: bool) -> None:
    pl = pytest.importorskip("polars")
    nw = pytest.importorskip("narwhals")
    frame = pl.DataFrame(schema={"values": pl.List(pl.Int64)})
    carrier = frame.lazy() if lazy else frame
    assert extract_source_shapes(carrier)["values"].item_shape == SourceShape(MountainashDtype.I64)
    assert extract_source_shapes(nw.from_native(carrier))["values"].item_shape == SourceShape(
        MountainashDtype.I64
    )


def test_arrow_field_qualifiers_are_native_evidence_while_portable_evidence_is_the_type() -> None:
    pa = pytest.importorskip("pyarrow")
    field = pa.field("x", pa.int64(), nullable=False, metadata={"unit": "m"})
    table = pa.table({"x": pa.array([1], pa.int64())}).cast(pa.schema([field]))
    shape = extract_source_shapes(table)["x"]
    assert shape.canonical_type is MountainashDtype.I64
    assert isinstance(shape.native_dtype, NativeDtype)
    assert shape.native_dtype.value.nullable is False
    assert shape.native_dtype.value.metadata == {b"unit": b"m"}


def test_pandas_arrow_backed_dtype_keeps_pandas_native_evidence_over_arrow_detail() -> None:
    pd = pytest.importorskip("pandas")
    shape = extract_source_shapes(_arrow_time_frame())["t"]
    assert shape.detailed_dtype == TimeDtype(6)
    assert shape.native_dtype.target is TypeTarget.PANDAS
    assert isinstance(shape.native_dtype.value, pd.ArrowDtype)


def test_shape_evidence_owns_its_native_payload() -> None:
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame({"c": pd.Series(["a"], dtype=pd.CategoricalDtype(["a", "b"]))})
    shape = extract_source_shapes(frame)["c"]
    assert shape.native_dtype.value is not frame.dtypes["c"]
    assert shape.native_dtype.value == frame.dtypes["c"]


def test_acquisition_preserves_column_order() -> None:
    pl = pytest.importorskip("polars")
    frame = pl.DataFrame(schema={"b": pl.Int8, "a": pl.String, "c": pl.Boolean})
    assert list(extract_source_shapes(frame)) == ["b", "a", "c"]


@pytest.mark.parametrize("lazy", [False, True])
def test_wrapped_polars_keeps_underlying_precision_with_narwhals_native_evidence(lazy: bool) -> None:
    nw = pytest.importorskip("narwhals")
    pl = pytest.importorskip("polars")
    from mountainash.typespec.adapter_registry import get_native_schema_adapter

    frame = pl.DataFrame(schema={"t": pl.Time})
    carrier = nw.from_native(frame.lazy() if lazy else frame)
    adapter = get_native_schema_adapter(TypeTarget.NARWHALS)
    acquired = adapter.extract_schema(carrier)["t"]
    assert acquired.detailed_dtype == TimeDtype(9)
    assert acquired.native_dtype.target is TypeTarget.NARWHALS
    # Narwhals' own schema carries no Time precision to decode.
    assert adapter.decode_schema(carrier.collect_schema())["t"].detailed_dtype != TimeDtype(9)


def test_wrapped_native_evidence_is_narwhals_at_every_level_without_carrier_overrides() -> None:
    nw = pytest.importorskip("narwhals")
    pa = pytest.importorskip("pyarrow")
    storage = pa.large_list(pa.struct([("a", pa.int64())]))
    table = pa.table({"v": pa.array([[{"a": 1}]], storage)})
    shape = extract_source_shapes(nw.from_native(table))["v"]
    member = shape.item_shape.struct_fields[0][1]
    assert shape.native_dtype.target is TypeTarget.NARWHALS
    assert member.native_dtype.target is TypeTarget.NARWHALS
    # large_list is Arrow storage detail, not an override a Narwhals target could honour.
    assert shape.detailed_dtype.native is None


def test_arrow_backed_pandas_nested_evidence_is_pandas_evidence_that_lowers_back() -> None:
    pd = pytest.importorskip("pandas")
    pa = pytest.importorskip("pyarrow")
    from mountainash.core.dtypes import registry

    storage = pa.list_(pa.large_string())
    shape = extract_source_shapes(pd.DataFrame({"v": pd.Series([], dtype=pd.ArrowDtype(storage))}))["v"]
    assert shape.item_shape.native_dtype == NativeDtype(
        value=pd.ArrowDtype(pa.large_string()), target=TypeTarget.PANDAS,
    )
    assert registry.to_native_schema(shape.detailed_dtype, TypeTarget.PANDAS) == pd.ArrowDtype(storage)


def test_arrow_backed_pandas_native_only_type_is_pandas_evidence() -> None:
    pd = pytest.importorskip("pandas")
    pa = pytest.importorskip("pyarrow")
    storage = pa.dictionary(pa.int32(), pa.string())
    shape = extract_source_shapes(pd.DataFrame({"c": pd.Series([], dtype=pd.ArrowDtype(storage))}))["c"]
    assert shape.detailed_dtype == NativeDtype(value=pd.ArrowDtype(storage), target=TypeTarget.PANDAS)


@pytest.mark.parametrize("carrier", ["pyarrow", "pandas"])
def test_wrapped_native_storage_leaves_do_not_become_foreign_overrides(carrier):
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa
    from mountainash.core.dtypes import ListDtype, MountainashDtype, SchemaTypeStatus
    from mountainash.typespec.converters import resolve_field_type
    from mountainash.typespec.spec import FieldDefinition
    from mountainash.core.dtypes import registry

    storage = pa.list_(pa.large_string())
    source = (
        pa.Table.from_arrays([pa.array([], type=storage)], names=["values"])
        if carrier == "pyarrow"
        else pd.DataFrame({"values": pd.Series([], dtype=pd.ArrowDtype(storage))})
    )
    shape = extract_source_shapes(nw.from_native(source))["values"]
    authored = FieldDefinition(dtype=ListDtype(SchemaTypeStatus.UNKNOWN))
    effective = resolve_field_type(authored, source=shape, target=TypeTarget.NARWHALS, path=("values",))
    assert effective == ListDtype(MountainashDtype.STRING)
    assert registry.to_native_schema(effective, TypeTarget.NARWHALS) == nw.List(nw.String)
    assert authored.dtype.element is SchemaTypeStatus.UNKNOWN
