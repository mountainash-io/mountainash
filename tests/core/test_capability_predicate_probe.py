"""Consumer audit for predicate facts (backlog 66b)."""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityRegistry
from mountainash.core.capabilities.schema import (
    CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate,
)
from mountainash.core.constants import CONST_BACKEND


def test_first_predicate_fact_is_the_join_asof_strategy_gate():
    """Invariant flip (item 108): the mechanism now ships with exactly one
    production predicate fact — the ibis-polars join_asof strategy gate."""
    from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_MOUNTAINASH_REL,
    )
    load_all_capability_declarations()
    facts = [f for f in CapabilityRegistry.facts() if f.predicate is not None]
    assert len(facts) == 1
    assert facts[0].operation_key == RKEY_MOUNTAINASH_REL.JOIN_ASOF
    assert facts[0].param == "strategy"
    assert facts[0].dialect == "ibis-polars"


def test_first_predicate_fact_is_compound_cell_safe():
    """The §6 compound-cell probe: gate_params=("tolerance", "strategy") binds
    BOTH params conjunctively into the BoundCall, but the predicate clause only
    inspects `strategy`. A call that also sets `tolerance` must not spuriously
    trigger or suppress the gate — the two gate_params are independent axes."""
    import polars as pl
    import mountainash as ma
    from fixtures.capability_gating import assert_predicate_capability_gated
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_MOUNTAINASH_REL,
    )

    left = pl.DataFrame({"t": [1, 3]})
    right = pl.DataFrame({"t": [2, 4]})

    # backward + tolerance on ibis-polars: NOT gated (predicate only checks strategy).
    import ibis
    con = ibis.polars.connect()
    L = con.create_table("cp_l", left, overwrite=True)
    R = con.create_table("cp_r", right, overwrite=True)
    ma.relation(L).join_asof(R, on="t", strategy="backward", tolerance=1).to_polars()

    # forward + tolerance on ibis-polars: IS gated (strategy predicate fires
    # regardless of the co-bound tolerance value).
    err = assert_predicate_capability_gated(
        lambda: ma.relation(L).join_asof(R, on="t", strategy="forward", tolerance=1).to_polars()
    )
    assert err.function_key == RKEY_MOUNTAINASH_REL.JOIN_ASOF


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
