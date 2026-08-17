"""Cross-backend results for dt.is_dst (item 65).

Was a public API-builder method returning a non-functional placeholder
(constant False on all backends). See spec 2026-08-15-is-dst-real-implementation-design.md.
"""

from __future__ import annotations

from datetime import datetime, timezone

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

# ibis has no timezone/DST primitive at all -- declared UNSUPPORTED.
HONORING_BACKENDS = [b for b in TEMPORAL_BACKENDS if not b.startswith("ibis")]
IBIS_BACKENDS = [b for b in TEMPORAL_BACKENDS if b.startswith("ibis")]

NY = "America/New_York"
SYDNEY = "Australia/Sydney"

# 12:00 UTC in January and July. America/New_York: EST (UTC-5) in January,
# EDT (UTC-4, DST) in July. Australia/Sydney is the southern-hemisphere
# mirror: AEST (standard) in July, AEDT (DST) in January.
DST_DATA = {
    "x": [
        datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
    ]
}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HONORING_BACKENDS)
class TestIsDstNorthernHemisphere:
    def test_dst_in_summer_not_in_winter(
        self, backend_name, backend_factory, collect_expr
    ):
        df = backend_factory.create(DST_DATA, backend_name)
        actual = collect_expr(df, ma.col("x").dt.is_dst(NY))
        assert actual == [False, True]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HONORING_BACKENDS)
class TestIsDstSouthernHemisphere:
    def test_dst_in_january_not_in_july(
        self, backend_name, backend_factory, collect_expr
    ):
        df = backend_factory.create(DST_DATA, backend_name)
        actual = collect_expr(df, ma.col("x").dt.is_dst(SYDNEY))
        assert actual == [True, False]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
class TestIsDstIbisGate:
    def test_raises_capability_error(
        self, backend_name, backend_factory, collect_expr
    ):
        """Ibis has no timezone/DST primitive; the gate raises before dispatch."""
        df = backend_factory.create(DST_DATA, backend_name)
        expr = ma.col("x").dt.is_dst(NY)
        with pytest.raises(BackendCapabilityError, match="is_dst"):
            collect_expr(df, expr)
