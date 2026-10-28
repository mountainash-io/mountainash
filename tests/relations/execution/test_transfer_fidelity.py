"""Arrow transfer keeps payload values distinct from transport representations."""

from datetime import date, datetime, timezone
from decimal import Decimal
import math

import ibis
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from fixtures.backend_registry import MATRIX_BACKENDS, REGISTRY
from mountainash.relations.core.errors import UnsupportedRelationTransportError


IBIS = [name for name, spec in REGISTRY.items() if spec.family == "ibis"]


@pytest.mark.parametrize("source_name", IBIS)
@pytest.mark.parametrize("destination_name", IBIS)
def test_null_and_nan_remain_distinct_after_connection_transfer(source_name, destination_name):
    payload = pa.table({
        "id": pa.array([1, 2, 3], type=pa.int64()),
        "measure": pa.array([None, float("nan"), 2.5], type=pa.float64()),
    })
    connection = {
        "ibis-duckdb": ibis.duckdb.connect,
        "ibis-sqlite": lambda: ibis.sqlite.connect(":memory:"),
    }[source_name]()
    source = connection.create_table("source", payload)
    destination = REGISTRY[destination_name].build({"id": [1, 2, 3]}, "destination")
    if source_name == "ibis-sqlite":
        pytest.xfail("SQLite stores IEEE NaN as SQL NULL at native table ingestion; source cannot represent fixture")
    source_rows = ma.relation(source).sort("id").to_dicts()
    assert source_rows[0]["measure"] is None
    assert math.isnan(source_rows[1]["measure"])
    if destination_name == "ibis-sqlite":
        from mountainash.relations.core.errors import UnsupportedRelationTransportError

        with pytest.raises(UnsupportedRelationTransportError) as caught:
            ma.relation(source).join(destination, on="id", execute_on="right").to_dicts()
        assert caught.value.source_dialect == source_name
        assert caught.value.destination_dialect == destination_name
        return
    rows = ma.relation(source).join(destination, on="id", execute_on="right").sort("id").to_dicts()
    assert rows[0] == {"id": 1, "measure": None}
    assert rows[1]["id"] == 2 and math.isnan(rows[1]["measure"])
    assert rows[2] == {"id": 3, "measure": 2.5}


@pytest.mark.parametrize("source_name", IBIS)
@pytest.mark.parametrize("destination_name", IBIS)
def test_typed_empty_result_preserves_schema(source_name, destination_name):
    source = REGISTRY[source_name].build({"id": [1], "payload": ["a"]}, "source")
    destination = REGISTRY[destination_name].build({"id": [2], "rate": [4]}, "destination")
    result = ma.relation(source).join(destination, on="id", execute_on="right")
    assert result.to_dicts() == []
    assert set(result.collect().columns) == {"id", "payload", "rate"}


@pytest.mark.parametrize("destination_name", IBIS)
def test_typed_empty_arrow_source_keeps_field_types(destination_name):
    empty = pa.table({
        "id": pa.array([], type=pa.int64()),
        "amount": pa.array([], type=pa.decimal128(10, 2)),
    })
    source = ibis.duckdb.connect().create_table("source", empty)
    destination = REGISTRY[destination_name].build({"id": [1]}, "destination")
    result = ma.relation(source).join(destination, on="id", execute_on="right")
    native = result.collect()
    assert result.to_dicts() == []
    assert native.schema()["amount"].is_decimal()


@pytest.mark.parametrize("destination_name", ["ibis-duckdb"])
def test_arrow_decimal_temporal_and_structured_payload_survives_transfer(destination_name):
    payload = pa.table({
        "id": pa.array([1, 2], type=pa.int64()),
        "amount": pa.array([Decimal("1.20"), Decimal("999.99")], type=pa.decimal128(10, 2)),
        "day": pa.array([date(2024, 1, 2), date(2024, 1, 3)], type=pa.date32()),
        "instant": pa.array([
            datetime(2024, 1, 2, tzinfo=timezone.utc),
            datetime(2024, 1, 3, tzinfo=timezone.utc),
        ], type=pa.timestamp("us", tz="UTC")),
        "items": pa.array([[1, 2], [3]], type=pa.list_(pa.int64())),
        "detail": pa.array([{"score": 4}, {"score": 5}], type=pa.struct([("score", pa.int64())])),
    })
    source = ibis.duckdb.connect().create_table("source", payload)
    destination = REGISTRY[destination_name].build({"id": [1, 2]}, "destination")
    assert ma.relation(source).sort("id").to_dicts()[0]["amount"] == Decimal("1.20")
    rows = ma.relation(source).join(destination, on="id", execute_on="right").sort("id").to_dicts()
    assert [row["amount"] for row in rows] == [Decimal("1.20"), Decimal("999.99")]
    assert [row["day"] for row in rows] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert [row["instant"] for row in rows] == [
        datetime(2024, 1, 2, tzinfo=timezone.utc),
        datetime(2024, 1, 3, tzinfo=timezone.utc),
    ]
    assert [row["items"] for row in rows] == [[1, 2], [3]]
    assert [row["detail"] for row in rows] == [{"score": 4}, {"score": 5}]


@pytest.mark.parametrize("destination_name", IBIS)
def test_duplicate_keys_and_overlapping_payload_types_are_not_harmonized(destination_name):
    source = REGISTRY["ibis-duckdb"].build(
        {"id": [2, 2], "payload": ["first", "second"]}, "source",
    )
    destination = REGISTRY[destination_name].build(
        {"id": [2], "payload": [100]}, "destination",
    )
    rows = ma.relation(source).join(
        destination, on="id", suffix="_destination", execute_on="right",
    ).to_dicts()
    assert sorted(rows, key=lambda row: row["payload"]) == [
        {"id": 2, "payload": "first", "payload_destination": 100},
        {"id": 2, "payload": "second", "payload_destination": 100},
    ]


@pytest.mark.parametrize("lazy", [False, True])
def test_polars_nan_to_sqlite_rejects_loss_without_changing_source(lazy):
    source = pl.from_arrow(pa.table({
        "id": pa.array([1, 2, 3], type=pa.int64()),
        "measure": pa.array([None, float("nan"), 2.5], type=pa.float64()),
    }))
    if lazy:
        source = source.lazy()
    assert ma.relation(source).sort("id").to_dicts()[0]["measure"] is None
    assert math.isnan(ma.relation(source).sort("id").to_dicts()[1]["measure"])
    target = REGISTRY["ibis-sqlite"].build({"id": [1, 2, 3]}, "target")
    with pytest.raises(UnsupportedRelationTransportError) as caught:
        ma.relation(source).join(target, on="id", execute_on="right").to_dicts()
    assert caught.value.source_family == "polars"
    assert caught.value.destination_dialect == "ibis-sqlite"
    assert caught.value.route == "import_into"
    assert isinstance(caught.value.__cause__, ValueError)
    assert "NaN" in str(caught.value.__cause__)


@pytest.mark.parametrize("shape", ["mapping", "rows", "memory"])
def test_connectionless_ingress_nan_to_sqlite_is_rejected(shape):
    target = REGISTRY["ibis-sqlite"].build({"id": [1, 2]}, "target")
    if shape == "mapping":
        source = {"id": [1, 2], "measure": [None, float("nan")]}
    elif shape == "rows":
        source = [{"id": 1, "measure": None}, {"id": 2, "measure": float("nan")}]
    else:
        source = ibis.memtable(pa.table({
            "id": pa.array([1, 2]),
            "measure": pa.array([None, float("nan")], type=pa.float64()),
        }))
    with pytest.raises(UnsupportedRelationTransportError) as caught:
        ma.relation(target).join(source, on="id").to_dicts()
    assert caught.value.destination_dialect == "ibis-sqlite"
    assert isinstance(caught.value.__cause__, ValueError)
    assert "NaN" in str(caught.value.__cause__)


def test_decimal_to_sqlite_fails_with_typed_context_not_driver_exception():
    source = ibis.duckdb.connect().create_table("source", pa.table({
        "id": pa.array([1], type=pa.int64()),
        "amount": pa.array([Decimal("1.20")], type=pa.decimal128(10, 2)),
    }))
    assert ma.relation(source).to_dicts() == [{"id": 1, "amount": Decimal("1.20")}]
    target = REGISTRY["ibis-sqlite"].build({"id": [1]}, "target")
    with pytest.raises(UnsupportedRelationTransportError) as caught:
        ma.relation(source).join(target, on="id", execute_on="right").to_dicts()
    assert caught.value.source_dialect == "ibis-duckdb"
    assert caught.value.destination_dialect == "ibis-sqlite"
    assert caught.value.route == "import_into"
    assert caught.value.__cause__ is not None
    assert "decimal" in str(caught.value.__cause__).lower()


# --- Location-centred export / import_into --------------------------------
import narwhals as nw
import pandas as pd
from ibis.expr import operations as ops
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import BackendConversionError
from mountainash.relations.core.execution.location import ExecutionLocation
from mountainash.relations.core.materialization import ExecutionForm
from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

ARROW = pa.table({"id": [1, 2, 3], "v": [10.0, None, 30.0]})


def _loc(f, d, form=ExecutionForm.EAGER, b="bound", con=None, tok=None):
    return ExecutionLocation(f, d, form, b, tok, con)


def sys_(f):
    return get_relation_system(f)()


@pytest.mark.parametrize("form, cls", [(ExecutionForm.EAGER, pl.DataFrame), (ExecutionForm.LAZY, pl.LazyFrame)])
def test_polars_import_form(form, cls):
    assert isinstance(sys_(CONST_BACKEND.POLARS).import_into(ARROW, location=_loc(CONST_BACKEND.POLARS, "polars", form)).value, cls)


@pytest.mark.parametrize("dialect, impl, lazy", [
    ("narwhals-pandas", "pandas", False), ("narwhals-polars", "polars", False),
    ("narwhals-pyarrow", "pyarrow", False), ("narwhals-lazy", "polars", True)])
def test_narwhals_import(dialect, impl, lazy):
    out = sys_(CONST_BACKEND.NARWHALS).import_into(ARROW, location=_loc(CONST_BACKEND.NARWHALS, dialect)).value
    assert str(out.implementation).lower().endswith(impl) and isinstance(out, nw.LazyFrame) is lazy


@pytest.mark.parametrize("dialect", ["narwhals-duckdb", "narwhals-dask"])
def test_narwhals_lazy_only_import_refused(dialect):
    with pytest.raises(ValueError, match="lazy-only"):
        sys_(CONST_BACKEND.NARWHALS).import_into(ARROW, location=_loc(CONST_BACKEND.NARWHALS, dialect))


@pytest.mark.parametrize("native", [pd.DataFrame({"id": [1]}), pa.table({"id": [1]})])
def test_narwhals_export_native_carrier(native):
    src = _loc(CONST_BACKEND.NARWHALS, "narwhals-pandas" if isinstance(native, pd.DataFrame) else "narwhals-pyarrow")
    assert sys_(CONST_BACKEND.NARWHALS).export(native, source=src).to_pylist() == [{"id": 1}]


def test_ibis_unowned_import_is_memtable():
    out = sys_(CONST_BACKEND.IBIS).import_into(ARROW, location=_loc(CONST_BACKEND.IBIS, "ibis-duckdb", ExecutionForm.DEFERRED, "memory"))
    assert isinstance(out.value.op(), ops.InMemoryTable) and out.release is None


@pytest.mark.parametrize("connect", [ibis.duckdb.connect, ibis.polars.connect])
def test_ibis_owned_import(connect):
    con = connect()
    out = sys_(CONST_BACKEND.IBIS).import_into(
        ARROW, location=_loc(CONST_BACKEND.IBIS, f"ibis-{con.name}", ExecutionForm.DEFERRED, "bound", con, 0), owned=True)
    assert out.value.get_backend() is con and out.release is not None
    assert out.value.to_pyarrow().to_pylist() == ARROW.to_pylist()


def test_ibis_export_memtable_without_execution(monkeypatch):
    t = ibis.memtable(ARROW)
    monkeypatch.setattr(type(t), "to_pyarrow", lambda *a, **k: pytest.fail("executed"))
    assert sys_(CONST_BACKEND.IBIS).export(t, source=_loc(CONST_BACKEND.IBIS, None, ExecutionForm.DEFERRED, "memory")).equals(ARROW)


def test_ibis_sqlite_import_rejects_nan():
    con = ibis.sqlite.connect()
    with pytest.raises(ValueError, match="NaN"):
        sys_(CONST_BACKEND.IBIS).import_into(pa.table({"x": [1.0, float("nan")]}),
            location=_loc(CONST_BACKEND.IBIS, "ibis-sqlite", ExecutionForm.DEFERRED, "memory", con, 0))


# --- Typed source x destination x value transfer matrix (spec §8, spike J) ---

_CASES = {
    "int_null": pa.array([1, None, 3], pa.int64()),
    "float_null": pa.array([1.5, None], pa.float64()),
    "float_nan": pa.array([1.5, float("nan")], pa.float64()),
    "string_empty": pa.array(["a", None, ""], pa.string()),
    "bool_null": pa.array([True, None, False], pa.bool_()),
    "date": pa.array([date(2020, 1, 1), None], pa.date32()),
    "ts_us": pa.array([datetime(2020, 1, 1, 12, 0, 0, 123456), None], pa.timestamp("us")),
    "ts_tz": pa.array([datetime(2020, 1, 1, 12, tzinfo=timezone.utc), None], pa.timestamp("us", "UTC")),
    "decimal": pa.array([Decimal("1.10"), None], pa.decimal128(10, 2)),
    "decimal_all_null": pa.array([None, None], pa.decimal128(10, 2)),
    "list": pa.array([[1, 2], None, []], pa.list_(pa.int64())),
    "empty": pa.array([], pa.int64()),
}
_DESTS = {
    "polars": lambda: "polars",
    "narwhals-polars": lambda: "narwhals-polars",
    "narwhals-pandas": lambda: "narwhals-pandas",
    "narwhals-pyarrow": lambda: "narwhals-pyarrow",
    "narwhals-lazy": lambda: "narwhals-lazy",
    "ibis-duckdb": ibis.duckdb.connect,
    "ibis-sqlite": ibis.sqlite.connect,
    "ibis-polars": ibis.polars.connect,
}
# Spike J: the only source representation limits observed.
_SOURCE_LIMITS = {
    ("ibis-sqlite", c): "SQLite source cannot hold this value domain (spike J)"
    for c in ("float_nan", "decimal", "decimal_all_null", "list")
}
# Typed refusal asserted (SQLite storage checks), any source. A collect to an
# SQLite connection is an owned create_table copy, which also refuses an
# all-null decimal column (backlog 336); the memtable path still stores it.
_REFUSED = {("*", "ibis-sqlite", c) for c in ("float_nan", "decimal", "decimal_all_null", "list")}
# Destination representation limits. Imports into pandas use Narwhals' own
# NumPy-backed conversion (owner decision 2026-10-28), so values from a
# non-pandas source lose these distinctions; pandas sources move natively.
_PANDAS_LIMITS = {
    "int_null": "pandas NumPy import: integer column with nulls becomes float",
    "float_nan": "pandas NumPy import: NaN and null both become NaN",
    "decimal": "pandas NumPy import: decimals become Python objects",
    "decimal_all_null": "pandas NumPy import: decimals become Python objects",
}
_PANDAS_SOURCES = {"pandas", "narwhals-pandas"}


def _matrix_cells():
    for s in MATRIX_BACKENDS:
        for d in _DESTS:
            for c in _CASES:
                reason = _SOURCE_LIMITS.get((s, c))
                if reason is None and d == "narwhals-pandas" and s not in _PANDAS_SOURCES:
                    reason = _PANDAS_LIMITS.get(c)
                marks = pytest.mark.xfail(strict=True, reason=reason) if reason else ()
                yield pytest.param(s, d, c, id=f"{s}__{d}__{c}", marks=marks)


def test_matrix_destinations_cover_known_dialects():
    """Every known local/in-process dialect is a matrix destination; the rest
    are named with the reason they are covered elsewhere."""
    from mountainash.core.capabilities.identity import KNOWN_DIALECTS
    from mountainash.core.constants import CONST_BACKEND

    elsewhere = {
        "narwhals-duckdb": "lazy-only: refusal tested by test_lazy_only_narwhals_destinations_refused",
        "narwhals-dask": "lazy-only: refusal tested by test_lazy_only_narwhals_destinations_refused",
        "ibis-postgres": "needs a server",
        "ibis-mysql": "needs a server",
        "ibis-singlestoredb": "needs a server",
        "ibis-exasol": "needs a server",
    }
    known = set().union(*(KNOWN_DIALECTS[f] for f in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS)))
    assert known == set(_DESTS) | set(elsewhere)


@pytest.mark.cross_backend
@pytest.mark.parametrize("src, dst, case", list(_matrix_cells()))
def test_transfer_matrix(src, dst, case):
    from polars.testing import assert_series_equal

    arr = _CASES[case]
    table = pa.table({"k": pa.array(range(len(arr)), pa.int64()), "c": arr})
    expected = pl.from_arrow(table)["c"]
    source = MATRIX_BACKENDS[src].build_typed(table, "t")
    held = pl.from_arrow(ma.relation(source).to_pyarrow()).sort("k")["c"]
    assert_series_equal(held, expected)  # the source holds the case
    rel = ma.relation(source)
    if ("*", dst, case) in _REFUSED or (src, dst, case) in _REFUSED:
        with pytest.raises(UnsupportedRelationTransportError):
            rel.collect(target=_DESTS[dst]())
        return
    out = ma.relation(rel.collect(target=_DESTS[dst]())).to_polars()
    assert out.columns == ["k", "c"] and out.height == table.num_rows
    assert_series_equal(out.sort("k")["c"], expected, check_dtypes=True)


@pytest.mark.parametrize("dst", ["narwhals-duckdb", "narwhals-dask"])
def test_lazy_only_narwhals_destinations_refused(dst):
    with pytest.raises(UnsupportedRelationTransportError):
        ma.relation(ibis.duckdb.connect().create_table("t", {"k": [1]})).collect(target=dst)


@pytest.mark.parametrize("src", list(MATRIX_BACKENDS))
def test_to_pyarrow_nested_types_match_across_backends(src):
    """Same logical nested type -> same Arrow type string (offset width aside),
    whatever the engine names its list children (DuckDB uses ``l``). PyArrow's
    ``==`` ignores child names, so compare the type strings."""
    table = pa.table({
        "k": pa.array([0, 1], pa.int64()),
        "tags": pa.array([["a"], []], pa.list_(pa.string())),
        "s": pa.array([{"q": [1]}, None], pa.struct([("q", pa.list_(pa.int64()))])),
    })
    if src == "ibis-sqlite":
        pytest.xfail("SQLite source cannot hold nested types (spike J)")
    out = ma.relation(MATRIX_BACKENDS[src].build_typed(table, "t")).to_pyarrow()
    def logical(dtype):
        return str(dtype).replace("large_", "")

    assert logical(out.schema.field("tags").type) == "list<item: string>"
    assert logical(out.schema.field("s").type) == "struct<q: list<item: int64>>"


# --- Imports into pandas mix with the caller's pandas frames (review 2026-10-28) ---

def _ts_frame(**extra):
    import pandas as pd

    return pd.DataFrame({"k": [datetime(2024, 1, 1), None], **extra})


def test_union_with_imported_operand_leaves_caller_frame_unchanged():
    import narwhals as nw

    original = _ts_frame(v=[0, 1])
    other = pl.DataFrame({"k": [datetime(2024, 1, 1), None], "v": [2, 3]})
    rel = ma.concat([ma.relation(nw.from_native(original, eager_only=True)), ma.relation(other)])
    first = rel.to_pandas()
    assert original["k"].isna().tolist() == [False, True]
    assert first["k"].isna().sum() == 2
    assert rel.to_pandas()["k"].isna().sum() == 2


def test_timestamp_join_with_imported_operand():
    import narwhals as nw

    left = ma.relation(nw.from_native(_ts_frame(v=[0, 1]), eager_only=True))
    right = pl.DataFrame({"k": [datetime(2024, 1, 1), None], "w": [0, 1]})
    out = left.join(right, on="k", how="inner").to_pandas()
    assert out[["v", "w"]].values.tolist() == [[0, 0]]


def test_join_asof_mismatched_key_types_are_not_coerced():
    import narwhals as nw
    import pandas as pd

    left = ma.relation(nw.from_native(pd.DataFrame({"k": [1, 2]}), eager_only=True))
    right = nw.from_native(pd.DataFrame({"k": [1.9], "p": [99]}), eager_only=True)
    with pytest.raises(Exception, match="incompatible merge keys|must be the same type"):
        left.join_asof(right, on="k", strategy="backward").to_pandas()


def test_to_pandas_keeps_polars_dates_as_datetime64():
    out = ma.relation(pl.DataFrame({"d": [date(2024, 1, 1)]})).to_pandas()
    assert str(out["d"].dtype).startswith("datetime64")
    assert out["d"].dt.year.tolist() == [2024]


def test_resource_import_refusal_is_typed_with_limitation():
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
    from mountainash.relations.core.execution.location import ExecutionLocation
    from mountainash.relations.core.materialization import ExecutionForm

    resource = ma.DataResource(name="r", data=[{"l": [1, 2]}])
    con = ibis.sqlite.connect()
    location = ExecutionLocation(CONST_BACKEND.IBIS, "ibis-sqlite", ExecutionForm.DEFERRED, "bound", 0, con)
    with pytest.raises(UnsupportedRelationTransportError) as caught:
        get_relation_system(CONST_BACKEND.IBIS)().read_resource(resource, location=location)
    assert caught.value.limitation is not None
