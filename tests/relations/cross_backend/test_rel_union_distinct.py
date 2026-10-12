"""Public union value, precision and timezone behavior."""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from itertools import permutations

import ibis
import narwhals as nw
import pyarrow as pa
from fixtures.backend_registry import ALL_BACKENDS, create_ibis_sqlite_table
from fixtures.call_expectations import expect_call_failure

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.errors import InvalidOptionValueError
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
from mountainash.relations.core.relation_api.relation import concat


def _frames(backend):
    a = pl.DataFrame({"x": [1, 2]})
    b = pl.DataFrame({"x": [2, 3]})
    if backend == "polars":
        return a, b
    if backend == "narwhals":
        import narwhals as nw
        return nw.from_native(a, eager_only=True), nw.from_native(b, eager_only=True)
    if backend == "ibis":
        import ibis
        connection = ibis.duckdb.connect()
        return (connection.create_table("first_input", a.to_arrow()),
                connection.create_table("second_input", b.to_arrow()))
    raise AssertionError(backend)


@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_concat_distinct_deduplicates(backend):
    a, b = _frames(backend)
    rel = concat([ma.relation(a), ma.relation(b)], distinct=True)
    out = rel.to_polars()
    assert sorted(out["x"].to_list()) == [1, 2, 3]


@pytest.mark.parametrize("backend", ["polars", "narwhals", "ibis"])
def test_concat_default_keeps_duplicates(backend):
    a, b = _frames(backend)
    rel = concat([ma.relation(a), ma.relation(b)])
    out = rel.to_polars()
    assert sorted(out["x"].to_list()) == [1, 2, 2, 3]


@contextmanager
def _timestamp_inputs(backend_name, specifications):
    """Build declared timestamp carriers without rounding through datetime."""
    connection = None
    if backend_name.startswith("ibis-"):
        connection = getattr(ibis, backend_name.removeprefix("ibis-")).connect()
    try:
        parts = []
        for index, columns in enumerate(specifications):
            table = pa.table({
                name: pa.array(values, type=pa.timestamp(unit, tz=zone))
                for name, (unit, zone, values) in columns.items()
            })
            if connection is not None:
                if backend_name == "ibis-sqlite":
                    native = create_ibis_sqlite_table(connection, f"input_{index}", table)
                else:
                    native = connection.create_table(f"input_{index}", table)
            else:
                native = table.to_pandas() if "pandas" in backend_name else pl.from_arrow(table)
                if backend_name in {"polars-lazy", "narwhals-lazy"}:
                    native = native.lazy()
                if backend_name.startswith("narwhals-"):
                    native = nw.from_native(native)
            parts.append(ma.relation(native))
        yield parts
    finally:
        if connection is not None:
            connection.disconnect()


def _epoch_values(result, *, unit="ns", zone=None, column="t"):
    assert result.schema.field(column).type.tz == zone
    return result.column(column).cast(pa.timestamp(unit, tz=zone)).cast(pa.int64()).to_pylist()


# SQLite retains native concat; lossless reconciliation is explicitly unsupported.
@pytest.mark.parametrize("backend_name", [b for b in ALL_BACKENDS if b != "ibis-sqlite"])
@pytest.mark.parametrize("distinct", [False, True])
def test_concat_precision_is_order_independent(backend_name, distinct):
    specifications = [
        {"t": ("ms", None, [123])},
        {"t": ("us", None, [123456])},
        {"t": ("ns", None, [123456789])},
    ]
    with _timestamp_inputs(backend_name, specifications) as parts:
        for order in permutations(parts):
            for inputs in (order, (ma.concat(order[:2], distinct=distinct), order[2])):
                result = ma.concat(inputs, distinct=distinct).to_pyarrow()
                assert sorted(_epoch_values(result)) == [123000000, 123456000, 123456789]


@pytest.mark.parametrize("backend_name", [b for b in ALL_BACKENDS if b != "ibis-sqlite"])
@pytest.mark.parametrize("distinct", [False, True])
def test_concat_aware_literal_preserves_microseconds(backend_name, distinct):
    value = datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=timezone.utc)
    with _timestamp_inputs(backend_name, [{"t": ("us", "UTC", [1767225600123456])}]) as parts:
        literal = parts[0].select(ma.lit(value).alias("t"))
        result = ma.concat([parts[0], literal], distinct=distinct).to_pyarrow()
        assert _epoch_values(result, unit="us", zone="UTC") == (
            [1767225600123456] if distinct else [1767225600123456] * 2
        )


@pytest.mark.parametrize("backend_name", [b for b in ALL_BACKENDS if b != "ibis-sqlite"])
@pytest.mark.parametrize("empty_values", [[], [None]])
@pytest.mark.parametrize("distinct", [False, True])
def test_concat_empty_and_null_declared_precision(backend_name, empty_values, distinct):
    with _timestamp_inputs(backend_name, [
        {"t": ("ns", None, empty_values)},
        {"t": ("us", None, [123456])},
    ]) as parts:
        result = ma.concat(parts, distinct=distinct).to_pyarrow()
        assert result.schema.field("t").type.unit == "ns"
        assert Counter(_epoch_values(result)) == Counter([*empty_values, 123456000])


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("distinct", [False, True])
def test_concat_matching_timestamp_schemas_remain_native(backend_name, distinct):
    with _timestamp_inputs(backend_name, [
        {"t": ("us", None, [123456, 654321])},
        {"t": ("us", None, [123456])},
    ]) as parts:
        result = ma.concat(parts, distinct=distinct).to_pyarrow()
        assert sorted(_epoch_values(result, unit="us")) == (
            [123456, 654321] if distinct else [123456, 123456, 654321]
        )


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("distinct", [False, True])
def test_concat_timezone_normalizes_each_column_before_distinct(backend_name, distinct):
    with _timestamp_inputs(backend_name, [
        {"t": ("us", "UTC", [1767225600123456]), "u": ("ms", "Europe/Paris", [654])},
        {"t": ("us", "America/New_York", [1767225600123456]), "u": ("us", "Asia/Tokyo", [654000])},
    ]) as parts:
        parts = [part.with_columns(ma.lit(7).alias("tag")) for part in parts]
        with expect_call_failure(
            when=backend_name == "ibis-sqlite", errors=(BackendCapabilityError,),
            reason="Item 294: SQLite aware normalization unsupported (298–300).",
        ):
            result = (
                ma.concat(parts, distinct=distinct, timezone="UTC")
                .filter(ma.col("tag").eq(7)).sort("t").to_pyarrow()
            )
            count = 1 if distinct else 2
            assert _epoch_values(result, unit="us", zone="UTC") == [1767225600123456] * count
            assert _epoch_values(result, unit="us", zone="UTC", column="u") == [654000] * count
            assert result.column("tag").to_pylist() == [7] * count


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("values", [[], [None], [1793511000123456, 1793514600123456, None]])
def test_concat_single_target_preserves_fold_null_and_empty(backend_name, values):
    with _timestamp_inputs(backend_name, [{"t": ("us", "UTC", values)}]) as parts:
        with expect_call_failure(
            when=backend_name == "ibis-sqlite", errors=(BackendCapabilityError,),
            reason="Item 294: SQLite target timezone unsupported (300).",
        ):
            result = ma.concat(parts, timezone="America/New_York").to_pyarrow()
            assert _epoch_values(result, unit="us", zone="America/New_York") == values


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_concat_timezone_does_not_localize_naive_columns(backend_name):
    first_unit, first_value = ("us", 123000) if backend_name == "ibis-sqlite" else ("ms", 123)
    with _timestamp_inputs(backend_name, [
        {"t": (first_unit, None, [first_value])},
        {"t": ("us", None, [123456])},
    ]) as parts:
        result = ma.concat(parts, timezone="America/New_York").to_pyarrow()
        assert sorted(_epoch_values(result, unit="us")) == [123000, 123456]


@pytest.mark.parametrize("backend_name", ["pandas", "narwhals-pandas"])
@pytest.mark.parametrize("target", [None, "UTC"])
def test_concat_mixed_awareness_retains_native_object_values(backend_name, target):
    naive = datetime(1970, 1, 1, 0, 0, 0, 123456)
    aware = naive.replace(tzinfo=timezone.utc)
    with _timestamp_inputs(backend_name, [
        {"t": ("us", None, [123456])},
        {"t": ("us", "UTC", [123456])},
    ]) as parts:
        result = ma.concat(parts, timezone=target).collect()
        assert result["t"].tolist() == [naive, aware]
        assert result["t"].dtype == object


@pytest.mark.parametrize("distinct", [False, True])
def test_concat_sqlite_normalization_has_typed_operation_error(distinct):
    with _timestamp_inputs("ibis-sqlite", [{"t": ("us", "UTC", [123456])}]) as parts:
        with pytest.raises(BackendCapabilityError) as caught:
            ma.concat(parts, distinct=distinct, timezone="UTC").collect()
        assert caught.value.function_key is (
            RKEY_SUBSTRAIT_REL.UNION_DISTINCT if distinct else RKEY_SUBSTRAIT_REL.UNION_ALL
        )


@pytest.mark.parametrize("target,error", [
    ("Not/AZone", InvalidOptionValueError), ("", InvalidOptionValueError),
    (3, InvalidOptionValueError), (ma.col("t"), TypeError),
])
def test_concat_rejects_invalid_timezone(target, error):
    with pytest.raises(error):
        ma.concat([ma.relation(pl.DataFrame({"x": [1]}))], timezone=target)
