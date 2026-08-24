from __future__ import annotations

from typing import Any

import pytest

from mountainash.core.dtypes import MountainashDtype
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
