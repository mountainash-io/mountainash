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

from mountainash.core.errors import InvalidOptionValueError

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

# (backend, op) → reason. round/ceil have no native datetime impl on ibis or narwhals
# (the silent truncate-fallback is an anti-pattern); Task 3 declares them UNSUPPORTED so
# the visitor raises a clean BackendCapabilityError. ibis floor was fixed in Task 3
# (floor == truncate; applies the unit-mapping) and is NO LONGER divergent — its removal
# from this map was forced by the strict xfail flipping to XPASS, exactly as intended.
_KNOWN_FALLBACK_DIVERGENCES: dict[tuple[str, str], str] = {
    ("ibis-duckdb", "round"): "ibis has no native datetime round; declared UNSUPPORTED -> BackendCapabilityError (Task 3)",
    ("ibis-duckdb", "ceil"): "ibis has no native datetime ceil; declared UNSUPPORTED -> BackendCapabilityError (Task 3)",
    ("narwhals-polars", "round"): "narwhals has no native datetime round; declared UNSUPPORTED -> BackendCapabilityError (Task 3)",
    ("narwhals-polars", "ceil"): "narwhals has no native datetime ceil; declared UNSUPPORTED -> BackendCapabilityError (Task 3)",
    ("narwhals-pandas", "round"): "narwhals has no native datetime round; declared UNSUPPORTED -> BackendCapabilityError (Task 3)",
    ("narwhals-pandas", "ceil"): "narwhals has no native datetime ceil; declared UNSUPPORTED -> BackendCapabilityError (Task 3)",
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


# --------------------------------------------------------------------------
# Task 2: friendly-word normalization + uniform rejection of bad units
# --------------------------------------------------------------------------


# Friendly aliases -> canonical Polars-style duration forms (single multiplier).
# The api-builder now normalizes friendly -> duration before dispatch, so the
# two spellings must produce identical results on every backend.
_FRIENDLY_TO_DURATION: list[tuple[str, str]] = [
    ("year", "1y"),
    ("month", "1mo"),
    ("day", "1d"),
    ("hour", "1h"),
    ("minute", "1m"),
    ("second", "1s"),
    ("week", "1w"),
]


@pytest.mark.cross_backend
@pytest.mark.parametrize(("friendly", "duration"), _FRIENDLY_TO_DURATION)
def test_friendly_unit_normalizes_to_duration_on_polars(
    friendly: str,
    duration: str,
    backend_factory,
    collect_expr,
) -> None:
    """`truncate(<friendly>)` must produce the same value as `truncate(<duration>)` on polars.

    Task 2 wire-up: friendly words were previously passed straight to the
    backend, so the result depended on the backend (ibis accepted "month"
    natively; polars raised). After normalization, both spellings are the
    same canonical duration string before dispatch.
    """
    df = backend_factory.create(
        {"ts": [datetime(2026, 7, 21, 13, 37, 45)]},
        "polars",
    )

    friendly_result = collect_expr(
        df,
        ma.col("ts").dt.truncate(friendly).name.alias("r"),
        alias="r",
    )
    duration_result = collect_expr(
        df,
        ma.col("ts").dt.truncate(duration).name.alias("r"),
        alias="r",
    )

    assert friendly_result == duration_result, (
        f"friendly {friendly!r} -> {friendly_result!r} should equal "
        f"duration {duration!r} -> {duration_result!r}"
    )


@pytest.mark.cross_backend
@pytest.mark.parametrize("bad", ["fortnight", "13x", "2d", "3h", ""])
def test_invalid_or_multiplier_unit_rejected_uniformly(
    bad: str,
    backend_factory,
) -> None:
    """`truncate(<bad>)` must raise InvalidOptionValueError uniformly.

    Before Task 2:
      - polars passed these through, so `truncate("2d")` and `truncate("3h")`
        returned wrong/silent results (not rejected) — multiplier>1 must
        raise.
      - polars raised an opaque Polars engine error on `"fortnight"` / `"13x"`
        instead of the typed mountainash `InvalidOptionValueError`.
    After Task 2, the api-builder normalizes and validates `unit` against
    `MA_OPTION_DOMAINS[(truncate, unit)]` and raises the typed error.
    """
    df = backend_factory.create(
        {"ts": [datetime(2026, 7, 21, 13, 37, 45)]},
        "polars",
    )

    with pytest.raises(InvalidOptionValueError):
        ma.relation(df).select(ma.col("ts").dt.truncate(bad).name.alias("r")).to_polars()
