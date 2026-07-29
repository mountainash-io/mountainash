"""Cross-backend results for dt.to_timezone / dt.local_timestamp (item 62 PR-A).

Both were public API-builder methods that raised a bare KeyError at .compile().
See spec 2026-07-28-datetime-missing-ops-design.md Section 2.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import mountainash as ma
from mountainash.core.capabilities import load_all_capability_declarations
from mountainash.core.types import BackendCapabilityError

load_all_capability_declarations()

TEMPORAL_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]

# ibis honors neither op composably on any dialect -- declared UNSUPPORTED in
# Task 4. Until that task lands these fail; from Task 4 on they raise
# BackendCapabilityError and are covered by TestTimezoneOpsIbisGate instead.
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

        assert [v.replace(tzinfo=None) for v in actual] == [
            datetime(2024, 1, 15, 7, 0),
            datetime(2024, 7, 15, 8, 0),
        ]
        # EST in January, EDT in July -- proves DST is honored, not a fixed shift.
        assert [v.utcoffset() for v in actual] == [
            timedelta(hours=-5),
            timedelta(hours=-4),
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

        assert [v.replace(tzinfo=None) for v in actual] == [
            datetime(2024, 1, 15, 7, 0),
            datetime(2024, 7, 15, 8, 0),
        ]
        assert all(v.tzinfo is None for v in actual)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
@pytest.mark.parametrize("method", ["to_timezone", "local_timestamp"])
class TestTimezoneOpsIbisGate:
    def test_raises_capability_error(
        self, method, backend_name, backend_factory, collect_expr
    ):
        """ibis honors neither op composably; the gate raises before dispatch.

        to_timezone is correct at the materialization boundary ONLY -- the
        target zone lives in the ibis output dtype, not in the engine, so any
        expression composed on the result raises UnsupportedOperationError.
        local_timestamp is outright wrong (UTC wall clock). Probed on all
        three dialects; ibis-sqlite refuses the cast outright. See spec
        Section 2.3.1.
        """
        df = backend_factory.create(TZ_DATA, backend_name)
        expr = getattr(ma.col("x").dt, method)(NY)
        with pytest.raises(BackendCapabilityError, match="timezone"):
            collect_expr(df, expr)

