"""Input-authoritative dialect gating for the capability gate (item 95).

_gate_capabilities keys its dialect-scoped lookup off the visitor's anchor
dialect, so a GATE fact scoped to an operation's authoritative (left) input
dialect fires against the wrong string. This item resolves the authoritative
input dialect recursively.

Design: mountainash-central
2026-08-14-multi-input-node-anchor-dialect-gating-design.md (Revision 5).
"""
from __future__ import annotations

import narwhals as nw
import pandas as pd
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND, SetType
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)
from mountainash.relations.dag import RelationDAG

import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def _nw_polars(data: dict):
    return nw.from_native(pl.DataFrame(data), eager_only=True)


def _nw_pandas(data: dict):
    return nw.from_native(pd.DataFrame(data), eager_only=True)


@pytest.fixture
def _narwhals_pandas_filter_gate_fact():
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_backend(
            CONST_BACKEND.NARWHALS,
            [
                CapabilityFact(
                    operation_key=RKEY_SUBSTRAIT_REL.FILTER,
                    param=WILDCARD_PARAM,
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=CONST_BACKEND.NARWHALS,
                    dialect="narwhals-pandas",
                    since="2026-08-14",
                    message="test-only BUILD-time gate for narwhals-pandas filter",
                    enforcement=Enforcement.GATE,
                )
            ],
        )
        yield
    finally:
        CapabilityRegistry.restore(snap)


class TestInlineOperandDialectGate:
    def test_filter_gate_fires_on_inline_left_operand_dialect(
        self, _narwhals_pandas_filter_gate_fact
    ):
        # Anchor is narwhals-polars (a_polars is alphabetically first); the
        # Filter is INLINE in the target tree (not a separately-compiled dep),
        # so its gate runs under the anchor pair. Its input is a narwhals-pandas
        # ref, so the gate must fire against narwhals-pandas -- today it uses
        # the anchor (narwhals-polars) and does NOT fire.
        dag = RelationDAG()
        dag.add("a_polars", ma.relation(_nw_polars({"k": [1, 2]})))
        dag.add("z_pandas", ma.relation(_nw_pandas({"k": [1, 2]})))
        dag.add(
            "target",
            dag.ref("z_pandas").filter(ma.col("k") > 0).join(dag.ref("a_polars"), on="k"),
        )
        with pytest.raises(BackendCapabilityError):
            dag.collect("target")


class TestAuthoritativeDialectCases:
    def test_gate_does_not_fire_when_left_matches_anchor(self, _narwhals_pandas_filter_gate_fact):
        dag = RelationDAG()
        dag.add("a_polars", ma.relation(_nw_polars({"k": [1, 2]})))
        dag.add("z_polars2", ma.relation(_nw_polars({"k": [1, 2]})))
        dag.add("target", dag.ref("z_polars2").filter(ma.col("k") > 0).join(dag.ref("a_polars"), on="k"))
        dag.collect("target")   # narwhals-pandas fact must NOT fire

    def test_join_gate_fires_on_left_operand_dialect(self):
        snap = CapabilityRegistry.snapshot()
        try:
            CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, [
                CapabilityFact(
                    operation_key=RKEY_SUBSTRAIT_REL.JOIN, param=WILDCARD_PARAM,
                    level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.NARWHALS,
                    dialect="narwhals-pandas", since="2026-08-14",
                    enforcement=Enforcement.GATE,
                    message="join gate on narwhals-pandas",
                )
            ])
            dag = RelationDAG()
            dag.add("a_polars", ma.relation(_nw_polars({"k": [1, 2]})))
            dag.add("z_pandas", ma.relation(_nw_pandas({"k": [1, 2]})))
            dag.add("target", dag.ref("z_pandas").join(dag.ref("a_polars"), on="k"))
            with pytest.raises(BackendCapabilityError):
                dag.collect("target")
        finally:
            CapabilityRegistry.restore(snap)

    def test_unbound_ibis_input_yields_none(self):
        import ibis
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        from mountainash.relations.core.relation_nodes import ReadRelNode

        class _FakeBackend:
            backend_type = CONST_BACKEND.IBIS
            dialect = "ibis-duckdb"   # anchor has a KNOWN dialect

        ib = ibis.memtable({"k": [1]})   # unbound -> (IBIS, None)
        visitor = UnifiedRelationVisitor(
            _FakeBackend(), expression_visitor=None, identity_resolver=None
        )
        family, dialect = visitor._physical_identity(ReadRelNode(dataframe=ib))
        assert family is CONST_BACKEND.IBIS
        assert dialect is None   # explicitly unknown, NOT the anchor's "ibis-duckdb"

    def test_cycle_protection_returns_unresolved(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            RefRelNode,
        )

        class _FakeBackend:
            backend_type = CONST_BACKEND.NARWHALS
            dialect = "narwhals-pandas"

        nodes = {"a": RefRelNode(name="b"), "b": RefRelNode(name="a")}
        visitor = UnifiedRelationVisitor(
            _FakeBackend(), expression_visitor=None,
            identity_resolver=lambda name: nodes[name],
        )
        family, dialect = visitor._physical_identity(nodes["a"])
        assert family is None and dialect is None   # cycle -> unresolved, no recursion

    def test_empty_set_node_no_indexerror(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            _first_input_node,
        )
        from mountainash.relations.core.relation_nodes import SetRelNode

        node = SetRelNode(inputs=[], set_type=SetType.UNION_ALL)
        assert _first_input_node(node) is None   # no IndexError on inputs[0]
