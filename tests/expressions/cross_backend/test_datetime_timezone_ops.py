"""Public native timezone conversion and independent local-timestamp support."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from ibis.common.exceptions import UnsupportedOperationError
from fixtures.call_expectations import expect_call_failure

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)

TEMPORAL_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
    "narwhals-lazy",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]

# local_timestamp remains independently unsupported on Ibis.
HONORING_BACKENDS = [b for b in TEMPORAL_BACKENDS if not b.startswith("ibis")]
IBIS_BACKENDS = [b for b in TEMPORAL_BACKENDS if b.startswith("ibis")]

NY = "America/New_York"

# 12:00 UTC in January (America/New_York = UTC-5, EST) and July (UTC-4, EDT).
# The seasonal pair is required: it is the only thing distinguishing a real
# conversion from a fixed-offset shift.
TZ_DATA = {
    "x": [
        datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc),
        datetime(2024, 7, 15, 12, 0, tzinfo=timezone.utc),
        None,
    ]
}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtToTimezone:
    def test_converts_preserving_the_instant(
        self, backend_name, backend_factory, collect_expr
    ):
        """The wall clock moves; the instant does not."""
        if backend_name == "ibis-sqlite":
            df = backend_factory.create(TZ_DATA, backend_name)
            with pytest.raises(UnsupportedOperationError):
                collect_expr(df, ma.col("x").dt.to_timezone(NY))
            return
        df = backend_factory.create(TZ_DATA, backend_name)
        actual = collect_expr(df, ma.col("x").dt.to_timezone(NY))

        assert [None if v is None else v.replace(tzinfo=None) for v in actual] == [
            datetime(2024, 1, 15, 7, 0),
            datetime(2024, 7, 15, 8, 0),
            None,
        ]
        # EST in January, EDT in July -- proves DST is honored, not a fixed shift.
        assert [None if v is None else v.utcoffset() for v in actual] == [
            timedelta(hours=-5),
            timedelta(hours=-4),
            None,
        ]

    def test_utc_conversion_preserves_fold_instants_and_null(
        self, backend_name, backend_factory, collect_expr
    ):
        values = [
            datetime(2026, 11, 1, 5, 30, 0, 123456, tzinfo=timezone.utc),
            datetime(2026, 11, 1, 6, 30, 0, 123456, tzinfo=timezone.utc),
            None,
        ]
        df = backend_factory.create({"x": values}, backend_name)
        actual = collect_expr(df, ma.col("x").dt.to_timezone("UTC"))
        assert actual == values

    def test_same_zone_literal_is_not_refused(
        self, backend_name, backend_factory, collect_expr
    ):
        value = datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=ZoneInfo(NY))
        df = backend_factory.create({"id": [1]}, backend_name)
        with expect_call_failure(
            when=backend_name == "narwhals-pandas",
            reason="Narwhals pandas datetime dtype recognition excludes timezone underscores",
            errors=(AttributeError,),
        ):
            actual = collect_expr(df, ma.lit(value).dt.to_timezone(NY))
            assert [v.astimezone(timezone.utc) for v in actual] == [
                datetime(2026, 1, 1, 5, 0, 0, 123456, tzinfo=timezone.utc)
            ]
            assert actual[0].utcoffset() == timedelta(hours=-5)

    def test_utc_literal_conversion_uses_native_precision(
        self, backend_name, backend_factory, collect_expr
    ):
        value = datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=ZoneInfo(NY))
        df = backend_factory.create({"id": [1]}, backend_name)
        with expect_call_failure(
            when=backend_name == "narwhals-pandas",
            reason="Narwhals pandas datetime dtype recognition excludes timezone underscores",
            errors=(AttributeError,),
        ):
            actual = collect_expr(df, ma.lit(value).dt.to_timezone("UTC"))
            # SQLite formats actual timestamp casts at millisecond precision.
            microsecond = 123000 if backend_name == "ibis-sqlite" else 123456
            assert actual == [
                datetime(2026, 1, 1, 5, 0, 0, microsecond, tzinfo=timezone.utc)
            ]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HONORING_BACKENDS)
class TestDtLocalTimestamp:
    def test_converts_then_drops_the_zone(
        self, backend_name, backend_factory, collect_expr
    ):
        """Same conversion as to_timezone, then the zone is stripped."""
        df = backend_factory.create(TZ_DATA, backend_name)
        actual = collect_expr(df, ma.col("x").dt.local_timestamp(NY))

        assert [None if v is None else v.replace(tzinfo=None) for v in actual] == [
            datetime(2024, 1, 15, 7, 0),
            datetime(2024, 7, 15, 8, 0),
            None,
        ]
        assert all(v is None or v.tzinfo is None for v in actual)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
class TestLocalTimestampIbisRefusal:
    def test_raises_capability_error(
        self, backend_name, backend_factory, collect_expr
    ):
        df = backend_factory.create(TZ_DATA, backend_name)
        with pytest.raises(BackendCapabilityError) as raised:
            collect_expr(df, ma.col("x").dt.local_timestamp(NY))
        assert raised.value.function_key is FKEY_SUBSTRAIT_SCALAR_DATETIME.LOCAL_TIMESTAMP
        assert raised.value.backend == "ibis"



@pytest.mark.cross_backend
@pytest.mark.parametrize("dialect", ["duckdb", "polars"])
def test_ibis_conversion_preserves_native_timestamp_scale(dialect):
    """Exercise Ibis timestamp metadata without Python datetime's ns truncation.

    SQLite's millisecond cast behavior is covered by the literal test above.
    """
    import ibis
    import pyarrow as pa

    values = [1793511000123456789, 1793514600123456789, None]
    connection = getattr(ibis, dialect).connect()
    try:
        source = connection.create_table(
            "timezone_precision",
            pa.table({"ts": pa.array(values, type=pa.timestamp("ns", tz="UTC"))}),
        )
        before = ma.relation(source).to_pyarrow().column("ts")
        after = ma.relation(source).select(
            ma.col("ts").dt.to_timezone(NY).alias("ts")
        ).to_pyarrow().column("ts")
        # DuckDB ingests aware timestamps at us; Polars retains ns.
        assert after.type == pa.timestamp(before.type.unit, tz=NY)
        assert after.cast(pa.int64()).to_pylist() == before.cast(pa.int64()).to_pylist()
    finally:
        connection.disconnect()
