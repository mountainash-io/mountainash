"""Cross-backend regression for datetime value-class capability gating (items 63/64).

Encodes the controller Task-5 semantic probe matrix
(`.superpowers/sdd/vc-probe-matrix.md`) as an explicit regression lock — NOT a
re-probe. IANA_TIMEZONE (`assume_timezone`) value-class facts must gate the
declared (op, backend) cells with a clean ``BackendCapabilityError``, while
honored cells compile and evaluate.

Probe matrix (every value in each cell AGREES — no partial/disagree cells, so
there are no xfails here):

  IANA_TIMEZONE :: assume_timezone
    - ibis + both narwhals dialects: SILENTLY-WRONG (drop the tz, return a naive
      timestamp) — DECLARED.
    - polars: honored (attaches the tz).

`is_dst` is a placeholder stub (`lit(False)`) on every backend — its timezone
option is non-functional, so it carries NO value-class fact and stays parked
(see backlog: is_dst-placeholder-implementation). `offset_by` and `strftime`
are honored on every fixture — no facts.

DURATION_MULTIPLIER (integer unit multipliers >= 2, e.g. "2d"/"3h"/"12mo")
facts and this file's former `test_multiplier_gate` regression were RETIRED
by item 74: truncate/round_dt/ceil_dt/floor_dt now redirect through the real
round_temporal/round_calendar implementation instead of a silent-wrong
truncate fallback, so every fixture honors every multiplier value (see
`src/mountainash/expressions/backends/capabilities/datetime/value_classes_ma.py`
module docstring for the re-probed disposition table).
"""
from __future__ import annotations

from datetime import datetime

import pytest

import mountainash as ma
from mountainash.core.capabilities import load_all_capability_declarations
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import CapabilityLevel, ValueClass

# Facts register at import via the shared bootstrap (house convention: mirror
# test_option_fact_integrity / test_capability_integrity). Without this a
# standalone run of this file sees an empty registry and the gate never fires.
load_all_capability_declarations()
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as S,
)

_TS = datetime(2026, 7, 21, 13, 37, 45)

ALL_BACKENDS = ("polars", "ibis-duckdb", "narwhals-polars", "narwhals-pandas")

# --- Probe-derived declaration table (regression lock) --------------------

# (fkey, param, backend, dialect, value_class) tuples that MUST resolve to an
# UNSUPPORTED value-class fact. ibis carries a family-default (dialect=None) AND
# an ibis-duckdb fact; narwhals is per-dialect only.
_TZ = ValueClass.IANA_TIMEZONE

EXPECTED_DECLARED_CLASS_FACTS = [
    # assume_timezone IANA: ibis family default + duckdb; narwhals per-dialect
    *[
        (S.ASSUME_TIMEZONE, "timezone", CONST_BACKEND.IBIS, dialect, _TZ)
        for dialect in (None, "ibis-duckdb")
    ],
    *[
        (S.ASSUME_TIMEZONE, "timezone", CONST_BACKEND.NARWHALS, dialect, _TZ)
        for dialect in ("narwhals-polars", "narwhals-pandas")
    ],
]

_REPRESENTATIVE_VALUE = {
    _TZ: "Australia/Sydney",
}


def test_declared_class_cells_have_facts():
    """Every probe-declared cell resolves to an UNSUPPORTED class fact."""
    for fkey, param, backend, dialect, vc in EXPECTED_DECLARED_CLASS_FACTS:
        fact = CapabilityRegistry.capability_for(
            fkey, param, backend, dialect, option_value=_REPRESENTATIVE_VALUE[vc]
        )
        assert fact is not None, f"missing class fact for {(fkey, param, backend, dialect, vc)}"
        assert fact.level is CapabilityLevel.UNSUPPORTED
        assert fact.value_class is vc


# --- Cross-backend production regression ----------------------------------

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("tz", ["UTC", "Australia/Sydney"])
def test_assume_timezone_gate(backend_factory, collect_expr, backend_name, tz):
    """assume_timezone is honored on polars (tz-aware result) and DECLARED
    unsupported on ibis + both narwhals (silent tz-drop -> clean error)."""
    df = backend_factory.create({"ts": [_TS]}, backend_name)
    expr = ma.col("ts").dt.assume_timezone(tz)
    if backend_name == "polars":
        got = collect_expr(df, expr, alias="r")
        assert got[0].tzinfo is not None
    else:
        with pytest.raises(BackendCapabilityError):
            collect_expr(df, expr, alias="r")
