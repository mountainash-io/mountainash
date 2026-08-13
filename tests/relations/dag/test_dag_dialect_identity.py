"""Per-ref dialect-correct capability enforcement in RelationDAG (item 89).

Bug (pre-fix): ``RelationDAG._compile_with_refs()`` resolved exactly ONE
``(family, dialect)`` identity for an entire compile call, via two
independently-walking resolvers (``_resolve_backend_const`` for family,
``_resolve_dialect_for`` for dialect), reused for EVERY named ref compiled
in the dependency-materialisation loop. A DAG mixing dialects within the
same family (e.g. one ref reads narwhals-pandas, another narwhals-polars)
gated/enriched every dependency against the ANCHOR's dialect, not its own
-- confirmed live: a narwhals-pandas ``string_split`` MATERIALIZE_RESIDUE
fact leaked its raw native TypeError under a narwhals-polars anchor (see
the acceptance test in ``tests/relations/test_rel_limitations.py``).

Fix: one combined per-name identity resolver
(``_resolve_actual_identity_for``), used both to construct the anchor's
own (family, dialect) coherently under an explicit ``backend=`` override,
and to swap ``visitor.backend``/``visitor.expr_visitor`` to each
dependency's OWN identity for the duration of its own
``root.accept(visitor)`` -- mirroring the ``key_context`` per-ref swap
precedent (item 48) in the same loop.

Design: mountainash-central/04.planning/mountainash/superpowers/specs/
2026-08-13-relationdag-per-ref-dialect-gating-design.md (Revision 3).

Narwhals cannot natively combine (join/concat) frames of different
storage engines (verified empirically). Every DAG built here that
combines two differing-dialect refs at a TARGET expects that final
combination to raise -- tests assert on visitor CONSTRUCTION state or a
watched node's own visit() entry/exit, captured before that raise, never
on the full return value.
"""
from __future__ import annotations

import pandas as pd
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.dag import RelationDAG


def _nw_polars(data: dict):
    import narwhals as nw
    return nw.from_native(pl.DataFrame(data), eager_only=True)


def _nw_pandas(data: dict):
    import narwhals as nw
    return nw.from_native(pl.DataFrame(data).to_pandas(), eager_only=True)


def _nw_pyarrow(data: dict):
    import narwhals as nw
    import pyarrow as pa
    return nw.from_native(pa.table(data), eager_only=True)


class TestResolveActualIdentityFor:
    """Direct unit tests of the new combined resolver (Task 2)."""

    def test_pure_source_tree_returns_none_none(self):
        dag = RelationDAG()
        dag.add("src", ma.relation([{"a": 1}, {"a": 2}]))  # SourceRelNode, no ReadRelNode
        assert dag._resolve_actual_identity_for("src") == (None, None)

    def test_readable_leaf_with_unbound_dialect_returns_family_none(self):
        ibis = pytest.importorskip("ibis")
        dag = RelationDAG()
        dag.add("src", ma.relation(ibis.table({"a": "int64"}, name="u")))
        assert dag._resolve_actual_identity_for("src") == (CONST_BACKEND.IBIS, None)

    def test_fully_resolved_leaf(self):
        dag = RelationDAG()
        dag.add("src", ma.relation(pl.DataFrame({"a": [1]})))
        assert dag._resolve_actual_identity_for("src") == (
            CONST_BACKEND.POLARS,
            "polars",
        )

    def test_ignores_explicit_backend_override_entirely(self):
        # The combined resolver reports the ref's TRUE physical identity
        # regardless of any override -- callers apply the override on top.
        dag = RelationDAG()
        dag.add("src", ma.relation(_nw_pandas({"a": [1]})))
        assert dag._resolve_actual_identity_for("src") == (
            CONST_BACKEND.NARWHALS,
            "narwhals-pandas",
        )


class TestResolveActualIdentityForNode:
    """Direct unit tests of the ad-hoc-node sibling resolver (Task 2)."""

    def test_pure_source_node_returns_none_none(self):
        dag = RelationDAG()
        rel = ma.relation([{"a": 1}])
        assert dag._resolve_actual_identity_for_node(rel._node) == (None, None)

    def test_direct_read_node(self):
        dag = RelationDAG()
        rel = ma.relation(pl.DataFrame({"a": [1]}))
        assert dag._resolve_actual_identity_for_node(rel._node) == (
            CONST_BACKEND.POLARS,
            "polars",
        )


class TestResolveBackendConstAndDialectForWrappers:
    """Regression: the thin wrappers preserve their pre-refactor external
    behaviour exactly (explicit override honoured for family; dialect
    always walks regardless of override)."""

    def test_resolve_backend_const_honours_explicit_override(self):
        dag = RelationDAG()
        dag.add("src", ma.relation(_nw_pandas({"a": [1]})))
        assert dag._resolve_backend_const("polars", "src") == CONST_BACKEND.POLARS

    def test_resolve_backend_const_defaults_to_polars_for_pure_source(self):
        dag = RelationDAG()
        dag.add("src", ma.relation([{"a": 1}]))
        assert dag._resolve_backend_const(None, "src") == CONST_BACKEND.POLARS

    def test_resolve_backend_const_detects_when_no_override(self):
        dag = RelationDAG()
        dag.add("src", ma.relation(pl.DataFrame({"a": [1]})))
        assert dag._resolve_backend_const(None, "src") == CONST_BACKEND.POLARS

    def test_resolve_dialect_for_always_walks_regardless_of_override(self):
        dag = RelationDAG()
        dag.add("src", ma.relation(_nw_pandas({"a": [1]})))
        assert dag._resolve_dialect_for("src") == "narwhals-pandas"

    def test_resolve_dialect_for_none_when_no_readable_leaf(self):
        dag = RelationDAG()
        dag.add("src", ma.relation([{"a": 1}]))
        assert dag._resolve_dialect_for("src") is None
