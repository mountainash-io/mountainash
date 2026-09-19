"""Cross-backend results for dt.to_timezone / dt.local_timestamp (item 62 PR-A).

Both were public API-builder methods that raised a bare KeyError at .compile().
See spec 2026-07-28-datetime-missing-ops-design.md Section 2.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
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

# Ibis cannot preserve either operation's composable timezone semantics:
# to_timezone has no engine-level target-zone lowering and local_timestamp
# returns the UTC wall clock. Both backend methods refuse the call.
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
@pytest.mark.parametrize("backend_name", HONORING_BACKENDS)
class TestDtToTimezone:
    def test_converts_preserving_the_instant(
        self, backend_name, backend_factory, collect_expr
    ):
        """The wall clock moves; the instant does not."""
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
@pytest.mark.parametrize("method", ["to_timezone", "local_timestamp"])
class TestTimezoneOpsIbisRefusal:
    def test_raises_capability_error(
        self, method, backend_name, backend_factory, collect_expr
    ):
        """Ibis refuses each operation at its public function boundary."""
        df = backend_factory.create(TZ_DATA, backend_name)
        expr = getattr(ma.col("x").dt, method)(NY)
        with pytest.raises(BackendCapabilityError) as raised:
            collect_expr(df, expr)
        expected_key = (
            FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE
            if method == "to_timezone"
            else FKEY_SUBSTRAIT_SCALAR_DATETIME.LOCAL_TIMESTAMP
        )
        assert raised.value.function_key is expected_key
        assert raised.value.backend == "ibis"
        assert raised.value.limitation is None

