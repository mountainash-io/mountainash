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


@pytest.fixture
def _visitor_construction_spy(monkeypatch):
    """Patch UnifiedRelationVisitor.__init__ to record the constructed
    relation_system's (backend_type, dialect) on every construction.
    _compile_with_refs constructs exactly ONE UnifiedRelationVisitor per
    call (the anchor's) -- per-ref swaps (Task 4) mutate
    visitor.backend/.expr_visitor directly and never call __init__ again
    -- so this fires exactly once per test here, BEFORE any native
    dispatch, making it safe even when the actual compile subsequently
    raises (e.g. PolarsRelationSystem rejecting a raw Narwhals frame).

    Patches the CLASS's own __init__ in place (not a module-level name
    rebind), so it is picked up regardless of how dag.py imports the
    name.
    """
    from mountainash.relations.core.unified_visitor import relation_visitor as _rv

    original_init = _rv.UnifiedRelationVisitor.__init__
    constructions: list[dict] = []

    def _spy_init(self, relation_system, *args, **kwargs):
        constructions.append(
            {
                "backend_type": getattr(relation_system, "backend_type", None),
                "dialect": getattr(relation_system, "dialect", "MISSING"),
            }
        )
        return original_init(self, relation_system, *args, **kwargs)

    monkeypatch.setattr(_rv.UnifiedRelationVisitor, "__init__", _spy_init)
    yield constructions


class TestExplicitBackendAnchorCoherence:
    """Round-2 finding: the anchor's OWN (family, dialect) construction had
    the same invalid-hybrid bug the per-ref guard (Task 4) is fixed for --
    an explicit backend= override combined with a dialect string detected
    from a leaf of a DIFFERENT physical family. Covers both branches that
    establish the anchor identity."""

    def test_named_target_branch_never_builds_invalid_hybrid(
        self, _visitor_construction_spy
    ):
        # backend_target_name is not None (collect()'s always-set target).
        dag = RelationDAG()
        dag.add("pandas_only", ma.relation(_nw_pandas({"k": [1]})))
        try:
            dag.collect("pandas_only", backend="polars")
        except Exception:
            pass  # PolarsRelationSystem cannot read a raw Narwhals frame --
            # irrelevant, we assert the identity used to CONSTRUCT the
            # visitor, captured before any read is attempted.

        assert _visitor_construction_spy[0]["backend_type"] == CONST_BACKEND.POLARS
        assert _visitor_construction_spy[0]["dialect"] is None  # never "narwhals-pandas"

    def test_adhoc_node_fallback_branch_never_builds_invalid_hybrid(
        self, _visitor_construction_spy
    ):
        # No refs, no target name (execute() with zero RefRelNode leaves).
        dag = RelationDAG()
        rel = ma.relation(_nw_pandas({"k": [1]})).select("k")
        try:
            dag.execute(rel, backend="polars")
        except Exception:
            pass

        assert _visitor_construction_spy[0]["backend_type"] == CONST_BACKEND.POLARS
        assert _visitor_construction_spy[0]["dialect"] is None  # never "narwhals-pandas"

    def test_no_override_still_resolves_family_and_dialect_from_same_leaf(
        self, _visitor_construction_spy
    ):
        # Non-regression: the no-override path must still detect the
        # anchor's REAL family+dialect together (same leaf) and must
        # actually succeed end-to-end (no mismatch to raise on here).
        dag = RelationDAG()
        rel = ma.relation(_nw_pandas({"k": [1]})).select("k")
        _result, visitor = dag._execute_with_visitor(rel)
        assert visitor.backend.backend_type == CONST_BACKEND.NARWHALS
        assert visitor.backend.dialect == "narwhals-pandas"
        assert _visitor_construction_spy[0]["backend_type"] == CONST_BACKEND.NARWHALS
        assert _visitor_construction_spy[0]["dialect"] == "narwhals-pandas"


@pytest.fixture
def _dialect_spy_factory(monkeypatch):
    """Patch UnifiedRelationVisitor with a subclass that records, per
    watched node (by identity), the visitor's ``(id(backend),
    backend_type, backend.dialect, id(expr_visitor))`` at ``visit()``
    ENTRY, and whether ``visit()`` COMPLETED without raising. Mirrors
    ``test_key_drift_identity.py``'s ``_spy_visitor_factory`` -- dag.py
    imports ``UnifiedRelationVisitor`` via a local ``from ... import``
    inside ``_compile_with_refs``, re-resolving the module attribute on
    every call, so this monkeypatch is picked up without mutating any
    frozen pydantic ``RelationNode``.

    Returns a callable ``_register(node, label)``; captured state is on
    ``_register.captured`` (``dict[label, {"entry": {...}, "completed":
    bool}]``) after the DAG call under test runs.
    """
    from mountainash.relations.core.unified_visitor import relation_visitor as _rv

    original_cls = _rv.UnifiedRelationVisitor
    captured: dict[str, dict] = {}
    watch: dict[int, str] = {}

    class _SpyVisitor(original_cls):  # type: ignore[misc, valid-type]
        def visit(self, node):
            label = watch.get(id(node))
            if label is not None:
                captured[label] = {
                    "entry": {
                        "backend_id": id(self.backend),
                        "backend_type": getattr(self.backend, "backend_type", None),
                        "backend_dialect": getattr(self.backend, "dialect", "MISSING"),
                        "expr_visitor_id": id(self.expr_visitor),
                    },
                    "completed": False,
                }
            result = super().visit(node)
            if label is not None:
                captured[label]["completed"] = True
            return result

    monkeypatch.setattr(_rv, "UnifiedRelationVisitor", _SpyVisitor)

    def _register(node, label: str) -> None:
        watch[id(node)] = label

    _register.captured = captured  # type: ignore[attr-defined]
    yield _register


class TestPerRefDialectSwapAndRestore:
    """Spy-based identity test (testing plan #4): the anchor ref gets the
    original objects; a same-dialect ref reuses those same objects (by
    id()); a differing-dialect same-family ref gets a new, correctly-
    dialected pair; a subsequent same-dialect ref after a swap restores the
    original objects (catches stale-loop-state bugs); the target sees the
    originals after the loop. Also covers testing plan #2's "both anchor
    directions" requirement with a second, role-reversed test."""

    def test_swap_and_restore_across_three_refs(self, _dialect_spy_factory):
        dag = RelationDAG()
        a_rel = ma.relation(_nw_polars({"k": [1, 2]}))  # anchor: narwhals-polars
        b_rel = ma.relation(_nw_pandas({"k": [1, 2]}))  # differs: narwhals-pandas
        c_rel = ma.relation(_nw_polars({"k": [1, 2]}))  # same as anchor again
        dag.add("a", a_rel)
        dag.add("b", b_rel)
        dag.add("c", c_rel)
        final_rel = dag.ref("a").join(dag.ref("b"), on="k").join(dag.ref("c"), on="k")
        dag.add("final", final_rel)

        _dialect_spy_factory(a_rel._node, "a")
        _dialect_spy_factory(b_rel._node, "b")
        _dialect_spy_factory(c_rel._node, "c")
        _dialect_spy_factory(final_rel._node, "final")

        # narwhals cannot natively join a polars-backed frame against a
        # pandas-backed one -- the join itself is expected to raise once
        # dispatched. "a"/"b"/"c" are each simple standalone reads with no
        # combination attempted on their own, so each must COMPLETE;
        # "final" (the outer join) is watched at visit() entry only.
        try:
            dag.collect("final")
        except Exception:
            pass

        captured = _dialect_spy_factory.captured
        assert set(captured) == {"a", "b", "c", "final"}
        for label in ("a", "b", "c"):
            assert captured[label]["completed"] is True

        anchor_backend_id = captured["a"]["entry"]["backend_id"]
        anchor_expr_id = captured["a"]["entry"]["expr_visitor_id"]
        assert captured["a"]["entry"]["backend_dialect"] == "narwhals-polars"

        assert captured["b"]["entry"]["backend_dialect"] == "narwhals-pandas"
        assert captured["b"]["entry"]["backend_id"] != anchor_backend_id
        assert captured["b"]["entry"]["expr_visitor_id"] != anchor_expr_id

        # Restoration, not a fresh third construction and not b's stale state.
        assert captured["c"]["entry"]["backend_dialect"] == "narwhals-polars"
        assert captured["c"]["entry"]["backend_id"] == anchor_backend_id
        assert captured["c"]["entry"]["expr_visitor_id"] == anchor_expr_id

        assert captured["final"]["entry"]["backend_dialect"] == "narwhals-polars"
        assert captured["final"]["entry"]["backend_id"] == anchor_backend_id
        assert captured["final"]["entry"]["expr_visitor_id"] == anchor_expr_id

    def test_reversed_anchor_direction_pandas_anchor_polars_differs(
        self, _dialect_spy_factory
    ):
        # Testing plan #2: exercise BOTH anchor directions, not only
        # "polars-family dialect anchors, pandas-family dialect differs".
        dag = RelationDAG()
        a_rel = ma.relation(_nw_pandas({"k": [1, 2]}))  # anchor: narwhals-pandas
        b_rel = ma.relation(_nw_polars({"k": [1, 2]}))  # differs: narwhals-polars
        dag.add("a", a_rel)
        dag.add("b", b_rel)
        dag.add("final", dag.ref("a").join(dag.ref("b"), on="k"))

        _dialect_spy_factory(a_rel._node, "a")
        _dialect_spy_factory(b_rel._node, "b")

        try:
            dag.collect("final")
        except Exception:
            pass

        captured = _dialect_spy_factory.captured
        assert captured["a"]["completed"] is True
        assert captured["a"]["entry"]["backend_dialect"] == "narwhals-pandas"

        assert captured["b"]["completed"] is True
        assert captured["b"]["entry"]["backend_dialect"] == "narwhals-polars"
        assert (
            captured["b"]["entry"]["backend_id"] != captured["a"]["entry"]["backend_id"]
        )


class TestExplicitBackendPerRefNeverBuildsInvalidHybrid:
    """Round-1 finding (per-ref level, distinct from Task 3's anchor-level
    fix): an explicit backend= compile call must not construct an invalid
    hybrid for a NON-anchor ref whose OWN physical family differs from the
    override. Item 92 changed the resolution: a BARE foreign ref is now
    compiled in its OWN family (then coerced to the override family), so the
    ref's visit entry observes its own family, never an invalid hybrid."""

    def test_pandas_ref_under_explicit_polars_backend_with_polars_anchor(
        self, _dialect_spy_factory
    ):
        dag = RelationDAG()
        polars_anchor_rel = ma.relation(pl.DataFrame({"k": [1]}))
        pandas_rel = ma.relation(_nw_pandas({"k": [1]}))
        dag.add("a_polars_anchor", polars_anchor_rel)  # alphabetically first -> anchor
        dag.add("b_pandas_ref", pandas_rel)
        dag.add(
            "final",
            dag.ref("a_polars_anchor").join(dag.ref("b_pandas_ref"), on="k"),
        )
        _dialect_spy_factory(pandas_rel._node, "pandas_ref")

        # Item 92: the bare narwhals-pandas ref is compiled in its own family
        # (narwhals) and coerced to the explicit polars override -- so its
        # visit entry observes narwhals, not the invalid polars hybrid.
        result = dag.collect("final", backend="polars")
        assert result is not None

        captured = _dialect_spy_factory.captured["pandas_ref"]["entry"]
        assert captured["backend_type"] == CONST_BACKEND.NARWHALS
        assert captured["backend_dialect"] == "narwhals-pandas"


class TestSameFamilyUnboundDialectRefGetsNoneNotAnchorsDialect:
    """Testing plan #6: a same-family ref with a genuinely unbound dialect
    (an untyped Ibis table) must get dialect=None explicitly, never the
    anchor's specific known dialect -- and must itself complete without
    error (only the target's own bound-vs-unbound-connection join may
    fail, not the ref's own trivial "read this unbound table" compile)."""

    def test_unbound_ibis_table_ref_gets_none(self, _dialect_spy_factory):
        ibis = pytest.importorskip("ibis")
        con = ibis.duckdb.connect()
        bound_table = con.create_table("t", pd.DataFrame({"k": [1]}))
        anchor_rel = ma.relation(bound_table)  # ibis-duckdb, KNOWN dialect
        unbound_rel = ma.relation(ibis.table({"k": "int64"}, name="u"))  # dialect=None
        dag = RelationDAG()
        dag.add("a_anchor", anchor_rel)  # alphabetically first -> anchor
        dag.add("b_unbound", unbound_rel)
        dag.add(
            "final", dag.ref("a_anchor").join(dag.ref("b_unbound"), on="k")
        )
        _dialect_spy_factory(unbound_rel._node, "unbound")

        try:
            dag.collect("final")
        except Exception:
            pass  # the TARGET's own join across an unrelated ibis
            # connection may fail; the REF's own compile (just wrapping
            # the unbound table, a lazy no-op) must not.

        captured = _dialect_spy_factory.captured["unbound"]
        assert captured["completed"] is True
        assert captured["entry"]["backend_type"] == CONST_BACKEND.IBIS
        assert captured["entry"]["backend_dialect"] is None


@pytest.fixture
def _narwhals_pandas_filter_gate_fact():
    """Register an isolated, dialect-scoped BUILD-time GATE fact: filter()
    is UNSUPPORTED on narwhals-pandas specifically (not a real production
    limitation -- test-only, to deterministically exercise the per-ref
    GATE path without depending on any real backend quirk or native
    exception)."""
    from mountainash.core.capabilities import (
        CapabilityFact,
        CapabilityLevel,
        CapabilityRegistry,
        Enforcement,
        WILDCARD_PARAM,
    )
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_SUBSTRAIT_REL,
    )

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
                    message="test-only BUILD-time gate for narwhals-pandas filter",
                    enforcement=Enforcement.GATE,
                    since="2026-08-13",
                )
            ],
        )
        yield
    finally:
        CapabilityRegistry.restore(snap)


class TestPerRefBuildTimeGateFiresOnNonAnchorRefsOwnDialect:
    """Testing plan #1/#5's missing half: item 89's fix covers BUILD-time
    GATE facts too, not just MATERIALIZE_RESIDUE -- a dialect-scoped GATE
    fact on the NON-anchor ref's own dialect must fire during that ref's
    own compile, even though the anchor's dialect differs. GATE facts
    fire before any native call, so this test is fully deterministic --
    no native-exception timing/flakiness concern."""

    def test_gate_fires_on_non_anchor_pandas_ref_filter(
        self, _narwhals_pandas_filter_gate_fact
    ):
        dag = RelationDAG()
        anchor_rel = ma.relation(_nw_polars({"k": [1, 2]}))  # anchor: narwhals-polars
        pandas_rel = ma.relation(_nw_pandas({"k": [1, 2]})).filter(ma.col("k") > 0)
        dag.add("a_anchor", anchor_rel)
        dag.add("b_pandas_filtered", pandas_rel)
        dag.add(
            "final", dag.ref("a_anchor").join(dag.ref("b_pandas_filtered"), on="k")
        )
        with pytest.raises(BackendCapabilityError):
            dag.collect("final")


class TestExecuteAdhocTreeCombiningDirectNodeWithDifferingDialectRef:
    """Testing plan #7: an ad-hoc execute() tree combining a direct
    ReadRelNode (not registered in the DAG) with TWO named RefRelNodes of
    differing dialects must gate/enrich the NON-anchor ref against its OWN
    dialect. Two refs are required: with only one ref, that ref trivially
    IS the anchor (sorted(all_refs)[0] picks the sole ref), which proves
    nothing about per-ref switching."""

    def test_execute_direct_node_plus_two_refs_of_differing_dialects(
        self, _dialect_spy_factory
    ):
        dag = RelationDAG()
        anchor_rel = ma.relation(_nw_polars({"k": [1]}))  # a_anchor_ref: alphabetically first -> anchor
        diff_rel = ma.relation(_nw_pandas({"k": [1]}))  # b_diff_ref: differs from anchor
        dag.add("a_anchor_ref", anchor_rel)
        dag.add("b_diff_ref", diff_rel)
        direct_node_rel = ma.relation(_nw_polars({"k": [1]}))  # NOT registered in the dag
        adhoc = (
            direct_node_rel.join(dag.ref("a_anchor_ref"), on="k").join(
                dag.ref("b_diff_ref"), on="k"
            )
        )
        _dialect_spy_factory(anchor_rel._node, "anchor_ref")
        _dialect_spy_factory(diff_rel._node, "diff_ref")

        try:
            dag.execute(adhoc)
        except Exception:
            pass  # cross-storage narwhals join raises natively once the
            # target combines them; irrelevant -- both named refs must
            # complete their OWN compile first.

        captured = _dialect_spy_factory.captured
        assert captured["anchor_ref"]["completed"] is True
        assert captured["anchor_ref"]["entry"]["backend_dialect"] == "narwhals-polars"

        assert captured["diff_ref"]["completed"] is True
        assert captured["diff_ref"]["entry"]["backend_dialect"] == "narwhals-pandas"
        assert (
            captured["diff_ref"]["entry"]["backend_id"]
            != captured["anchor_ref"]["entry"]["backend_id"]
        )


class TestUnknownDialectStringRefNotSilentlyInherited:
    """Testing plan #8: a ref whose detected dialect is outside
    KNOWN_DIALECTS (narwhals-pyarrow) must not error and must not silently
    inherit the anchor's dialect. Asserts the ref's own compile actually
    COMPLETED (not merely that some assertion survives a broad except
    Exception around the whole call) -- only the TARGET's own cross-
    storage join may legitimately fail."""

    def test_pyarrow_backed_ref_keeps_its_own_unknown_dialect_string(
        self, _dialect_spy_factory
    ):
        pytest.importorskip("pyarrow")
        dag = RelationDAG()
        anchor_rel = ma.relation(_nw_polars({"k": [1]}))
        pyarrow_rel = ma.relation(_nw_pyarrow({"k": [1]}))
        dag.add("a_anchor", anchor_rel)
        dag.add("b_pyarrow", pyarrow_rel)
        dag.add("final", dag.ref("a_anchor").join(dag.ref("b_pyarrow"), on="k"))
        _dialect_spy_factory(pyarrow_rel._node, "pyarrow_ref")

        try:
            dag.collect("final")
        except Exception:
            pass  # the TARGET's own cross-storage join is expected to
            # fail; the REF's own compile (a trivial standalone read)
            # must not.

        captured = _dialect_spy_factory.captured["pyarrow_ref"]
        assert captured["completed"] is True
        assert captured["entry"]["backend_dialect"] == "narwhals-pyarrow"
        assert captured["entry"]["backend_dialect"] != "narwhals-polars"  # not inherited
