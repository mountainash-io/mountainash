"""Consumer audit for predicate facts (backlog 66b)."""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityRegistry
from mountainash.core.capabilities.schema import (
    CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate,
)
from mountainash.core.constants import CONST_BACKEND


def test_no_production_predicate_facts_yet():
    """Invariant: the mechanism ships with zero predicate facts (spec §7 —
    no consumer has arrived). If one lands, it MUST be accompanied by the §6
    compound-cell probe (see plan Task 5 deferred note)."""
    from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
    load_all_capability_declarations()
    facts = [f for f in CapabilityRegistry.facts() if f.predicate is not None]
    assert facts == []


def test_fact_sort_key_is_total_over_predicate_facts():
    """Two predicate facts on the same key differing only in clause content
    must not tie (review finding 8)."""
    from mountainash.core.capabilities.coverage import fact_sort_key

    def _make(value):
        return CapabilityFact(
            operation_key="TRUNCATE", param="unit", level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
            since="2026-08-15",
            predicate=Predicate((Clause("unit", ClauseOp.EQ, value),)),
        )

    assert fact_sort_key(_make("WEEK")) != fact_sort_key(_make("MONTH"))
