"""Relation-subsystem MATERIALIZE_RESIDUE enrichment (item 98).

The per-op narrowing is dead: _dispatch passes prefer_operation_keys=frozenset()
for handler ops and expression FKEYs (never an RKEY) for declarative ops, so a
dialect-scoped relation residue fact can never fire. This item carries the op's
RKEY into the filter and threads the authoritative dialect into
enrich_materialization.

Design: mountainash-central
2026-08-14-relation-materialize-residue-enrichment-design.md
(Revision 6, 6 GLM-5.2 adversarial review rounds -- SOUND_WITH_CONCERNS).
"""
from __future__ import annotations

import pandas as pd
import narwhals as nw
import pytest

import mountainash as ma
from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)
from mountainash.relations.backends.relation_systems.narwhals.substrait.relsys_nw_set import (
    SubstraitNarwhalsSetRelationSystem,
)

import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


class TestDeclarativeUnionResidueFires:
    def test_union_all_residue_fact_enriches_forced_native_error(self, monkeypatch):
        snap = CapabilityRegistry.snapshot()
        try:
            CapabilityRegistry.register_backend(
                CONST_BACKEND.NARWHALS,
                [
                    CapabilityFact(
                        operation_key=RKEY_SUBSTRAIT_REL.UNION_ALL,
                        param="*",
                        level=CapabilityLevel.UNSUPPORTED,
                        backend=CONST_BACKEND.NARWHALS,
                        dialect="narwhals-pandas",
                        enforcement=Enforcement.MATERIALIZE_RESIDUE,
                        boundary=Boundary.MATERIALIZE,
                        native_errors=(TypeError,),
                        message="union_all residue fired (test)",
                        since="2026-08-14",
                    )
                ],
            )

            def _boom(self, relations):
                raise TypeError("forced union_all failure")

            monkeypatch.setattr(
                SubstraitNarwhalsSetRelationSystem, "union_all", _boom
            )

            nw_df = nw.from_native(pd.DataFrame({"a": [1]}), eager_only=True)
            with pytest.raises(BackendCapabilityError, match="union_all residue fired"):
                ma.concat([ma.relation(nw_df), ma.relation(nw_df)]).to_polars()
        finally:
            CapabilityRegistry.restore(snap)
