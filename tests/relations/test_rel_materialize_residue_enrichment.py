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


class TestDeadDeclarationEnforcement:
    def test_handler_routed_residue_fact_requires_wraps_native_call(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_MOUNTAINASH_REL,
        )
        snap = CapabilityRegistry.snapshot()
        try:
            with pytest.raises(ValueError, match="wraps_native_call"):
                CapabilityRegistry.register_backend(
                    CONST_BACKEND.NARWHALS,
                    [
                        CapabilityFact(
                            operation_key=RKEY_MOUNTAINASH_REL.REF,
                            param="*",
                            level=CapabilityLevel.UNSUPPORTED,
                            backend=CONST_BACKEND.NARWHALS,
                            enforcement=Enforcement.MATERIALIZE_RESIDUE,
                            boundary=Boundary.MATERIALIZE,
                            native_errors=(TypeError,),
                            since="2026-08-14",
                        )
                    ],
                )
        finally:
            CapabilityRegistry.restore(snap)


class TestHandlerPathAndBoundaries:
    def test_handler_join_residue_fires(self, monkeypatch):
        from mountainash.relations.backends.relation_systems.narwhals.substrait.relsys_nw_join import (
            SubstraitNarwhalsJoinRelationSystem,
        )
        snap = CapabilityRegistry.snapshot()
        try:
            CapabilityRegistry.register_backend(
                CONST_BACKEND.NARWHALS,
                [
                    CapabilityFact(
                        operation_key=RKEY_SUBSTRAIT_REL.JOIN, param="*",
                        level=CapabilityLevel.UNSUPPORTED,
                        backend=CONST_BACKEND.NARWHALS, dialect="narwhals-pandas",
                        enforcement=Enforcement.MATERIALIZE_RESIDUE,
                        boundary=Boundary.MATERIALIZE, native_errors=(TypeError,),
                        message="join residue fired (test)",
                        since="2026-08-14",
                    )
                ],
            )
            def _boom(self, *a, **k):
                raise TypeError("forced join failure")
            monkeypatch.setattr(SubstraitNarwhalsJoinRelationSystem, "join", _boom)
            nw_df = nw.from_native(pd.DataFrame({"id": [1]}), eager_only=True)
            with pytest.raises(BackendCapabilityError, match="join residue fired"):
                ma.relation(nw_df).join(ma.relation(nw_df), on="id").to_polars()
        finally:
            CapabilityRegistry.restore(snap)

    def test_child_visit_error_not_narrowed(self, monkeypatch):
        from mountainash.relations.core.unified_visitor import relation_visitor as rv
        snap = CapabilityRegistry.snapshot()
        try:
            CapabilityRegistry.register_backend(
                CONST_BACKEND.NARWHALS,
                [
                    CapabilityFact(
                        operation_key=RKEY_SUBSTRAIT_REL.JOIN, param="*",
                        level=CapabilityLevel.UNSUPPORTED,
                        backend=CONST_BACKEND.NARWHALS, dialect="narwhals-pandas",
                        enforcement=Enforcement.MATERIALIZE_RESIDUE,
                        boundary=Boundary.MATERIALIZE, native_errors=(TypeError,),
                        message="join residue fired (test)",
                        since="2026-08-14",
                    )
                ],
            )
            # Force the RIGHT-side child visit/coercion to raise BEFORE the
            # join's native call -- the join's (JOIN, *) fact must NOT enrich
            # this child-visit error (children compile outside the wrap).
            monkeypatch.setattr(
                rv.UnifiedRelationVisitor,
                "_visit_and_coerce_right",
                lambda self, right, left: (_ for _ in ()).throw(TypeError("child visit failure")),
            )
            nw_df = nw.from_native(pd.DataFrame({"id": [1]}), eager_only=True)
            with pytest.raises(TypeError, match="child visit failure"):
                ma.relation(nw_df).join(ma.relation(nw_df), on="id").to_polars()
        finally:
            CapabilityRegistry.restore(snap)
