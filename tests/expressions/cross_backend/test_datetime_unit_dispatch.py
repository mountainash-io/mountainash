"""Cross-backend regression for the dt.{truncate,round,ceil,floor} unit dispatch.

Before the *_dt rename (Task 1), `round`/`ceil`/`floor` on the MA datetime
extension collide in MRO with `round`/`ceil`/`floor` on the Substrait
scalar_rounding extension. The visitor resolves the backend method by
`protocol_method.__name__` and does `getattr(backend, name)`, so the
collision shadows the datetime impl behind the numeric-rounding impl and
calling `col("ts").dt.round("1h")` raises:

    TypeError: ...round() got an unexpected keyword argument 'unit'

This test pins the four `unit`-rounding ops (truncate / round / ceil / floor)
across the canonical 4-fixture cross-backend matrix and asserts that each
reaches its datetime impl and returns the *expected* rounded datetime (not
merely "no raise"). The unit `1h` is portable core (honored uniformly per
the spec).

Per-backend xfails cover the KNOWN pre-existing per-backend fall-back
divergences that are out of scope for Task 1 (the dispatch fix) and will be
declared as CapabilityFacts in Task 3:

  - ibis-duckdb round/ceil/floor: the existing Ibis impl calls
    `x.truncate(unit)` directly without going through the Polars-style
    `1h`→`h` unit translation that `truncate` does. Task 2 normalizes the
    unit format on the visit path.
  - narwhals-{polars,pandas} round/ceil: the existing Narwhals impl falls
    back to `x.dt.truncate(unit)` (no native datetime round/ceil), so
    13:37:45 → 13:00 not 14:00. Task 3 declares this as a
    `declared_unsupported` CapabilityFact.

Truncate passes on all 4 backends pre- and post-fix (it never collided
because no other protocol defines a bare `truncate` method).
"""
from __future__ import annotations

from datetime import datetime

import pytest

import mountainash as ma

# Canonical 4-fixture cross-backend set for datetime `unit` rounding
# (per the spec): polars → polars, ibis → ibis-duckdb, narwhals-polars,
# narwhals-pandas. The `1h` unit is portable core (honored uniformly on
# all four) so the regression is meaningful for each fixture. Backend
# names match the entries in `tests/fixtures/backend_registry.py`
# (e.g. the spec's "ibis" maps to "ibis-duckdb" in the registry).
ALL_BACKENDS_DATETIME_UNIT = (
    "polars",
    "ibis-duckdb",
    "narwhals-polars",
    "narwhals-pandas",
)

# (backend, op) → reason. Pre-existing per-backend fall-back divergences
# unrelated to the Task 1 dispatch fix; declared as CapabilityFacts in Task 3.
_KNOWN_FALLBACK_DIVERGENCES: dict[tuple[str, str], str] = {
    ("ibis-duckdb", "round"): "ibis datetime round falls back to truncate w/o unit-format normalization (Task 2/3)",
    ("ibis-duckdb", "ceil"): "ibis datetime ceil falls back to truncate w/o unit-format normalization (Task 2/3)",
    ("ibis-duckdb", "floor"): "ibis datetime floor falls back to truncate w/o unit-format normalization (Task 2/3)",
    ("narwhals-polars", "round"): "narwhals datetime round falls back to truncate (no native round; Task 3 CapabilityFact)",
    ("narwhals-polars", "ceil"): "narwhals datetime ceil falls back to truncate (no native ceil; Task 3 CapabilityFact)",
    ("narwhals-pandas", "round"): "narwhals datetime round falls back to truncate (no native round; Task 3 CapabilityFact)",
    ("narwhals-pandas", "ceil"): "narwhals datetime ceil falls back to truncate (no native ceil; Task 3 CapabilityFact)",
}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS_DATETIME_UNIT)
class TestDatetimeUnitDispatch:
    """`dt.truncate/round/ceil/floor(unit)` must reach the datetime impl on every backend."""

    @pytest.mark.parametrize(
        ("op", "expected"),
        [
            ("truncate", datetime(2026, 7, 21, 13, 0)),
            ("round", datetime(2026, 7, 21, 14, 0)),  # 13:37 rounds up to 14:00 at 1h
            ("ceil", datetime(2026, 7, 21, 14, 0)),
            ("floor", datetime(2026, 7, 21, 13, 0)),
        ],
    )
    def test_datetime_unit_ops_reach_datetime_impl(
        self,
        backend_name: str,
        backend_factory,
        collect_expr,
        op: str,
        expected: datetime,
        request,
    ) -> None:
        div_key = (backend_name, op)
        if div_key in _KNOWN_FALLBACK_DIVERGENCES:
            # STRICT xfail (not imperative pytest.xfail): the assertion below still
            # RUNS, so when a later task (Task 2 unit-format normalization / Task 3
            # CapabilityFact) fixes a backend, the unexpected pass fails loudly and
            # forces this entry's removal — the deferred work self-announces. Mirrors
            # the plan's Task 3 `request.applymarker(...)` idiom.
            request.applymarker(
                pytest.mark.xfail(strict=True, reason=_KNOWN_FALLBACK_DIVERGENCES[div_key])
            )

        df = backend_factory.create(
            {"ts": [datetime(2026, 7, 21, 13, 37, 45)]},
            backend_name,
        )

        got = collect_expr(
            df,
            getattr(ma.col("ts").dt, op)("1h").name.alias("r"),
            alias="r",
        )

        assert got == [expected], (
            f"[{backend_name}] {op}('1h') on {datetime(2026, 7, 21, 13, 37, 45)} "
            f"expected {[expected]!r}, got {got!r}"
        )
