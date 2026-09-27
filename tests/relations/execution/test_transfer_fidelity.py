"""Arrow transfer keeps payload values distinct from transport representations."""

from datetime import date, datetime, timezone
from decimal import Decimal
import math

import ibis
import pyarrow as pa
import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY


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
        "ibis-polars": ibis.polars.connect,
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


@pytest.mark.parametrize("destination_name", ["ibis-duckdb", "ibis-polars"])
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
