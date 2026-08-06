"""Cross-backend gate verification for dt.assume_timezone (honor-or-declare).

assume_timezone is HONORED only on the polars family; ibis and narwhals
silently drop the timezone (return a naive timestamp), so the capability gate
declares them UNSUPPORTED and raises BackendCapabilityError on the real user
path rather than returning silently-wrong data.

Split out of test_datetime_extension_results.py (SP2-B Wave 2.D): the gate is
enriched through the visitor path, not the queryable CapabilityRegistry, so
assert_capability_gated cannot resolve it (capability_gate returns None). Per
the crosswalk Part D fallback (mutation probe fails to redden -> split-out
§4.1.1), the precise `pytest.raises(BackendCapabilityError)` gate assertion is
kept here, isolated from any xfail_divergence so the all-or-nothing census
guard stays satisfied.
"""

from __future__ import annotations

from datetime import datetime

import pytest

import mountainash as ma
from mountainash.core.capabilities import load_all_capability_declarations
from mountainash.core.types import BackendCapabilityError

# Load capability declarations at import so the gate is live under standalone
# collection (mirrors test_datetime_extension_results.py's convention).
load_all_capability_declarations()

TIMESTAMP_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]

_ASSUME_TZ_HONORED = {"polars", "polars-lazy"}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TIMESTAMP_BACKENDS)
class TestDtAssumeTimezone:
    def test_assume_timezone_preserves_hour(
        self, backend_name, backend_factory, collect_expr
    ):
        """Polars: assume UTC then extract hour — same hour as the naive input.

        ibis/narwhals: the gate raises (they silently drop the tz), so the
        expression cannot be compiled at all.
        """
        data = {
            "ts": [
                datetime(2024, 3, 15, 10, 30, 0),
                datetime(2024, 6, 20, 14, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.assume_timezone("UTC").dt.hour()
        if backend_name in _ASSUME_TZ_HONORED:
            actual = collect_expr(df, expr)
            assert actual == [10, 14]
        else:
            with pytest.raises(BackendCapabilityError, match="assume_timezone"):
                collect_expr(df, expr)

    def test_assume_timezone_runs_without_error(
        self, backend_name, backend_factory
    ):
        """Polars runs cleanly; ibis/narwhals raise BackendCapabilityError."""
        data = {
            "ts": [
                datetime(2024, 3, 15, 10, 30, 0),
                datetime(2024, 6, 20, 14, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        build = (
            ma.relation(df)
            .select(ma.col("ts").dt.assume_timezone("UTC").name.alias("tz_ts"))
            .to_dict
        )
        if backend_name in _ASSUME_TZ_HONORED:
            result = build()
            assert len(result["tz_ts"]) == 2
        else:
            with pytest.raises(BackendCapabilityError, match="assume_timezone"):
                build()
