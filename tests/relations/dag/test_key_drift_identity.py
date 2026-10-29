"""Key-drift identity split: ad-hoc execute() must not inherit a dependency's
key identity (misattribution bugfix), while named dependencies still get
their own key contexts. dag-hardening PR-2 Sec 2.2.

Bug (pre-fix): ``_compile_with_refs`` gated the TARGET's ``KeyDriftContext``
on ``backend_target_name``, and ``execute()`` passes
``backend_target_name = sorted(all_refs)[0]`` (the alphabetically-first
dependency name) purely for backend detection. So an ad-hoc ``execute()``
over a tree referencing a constrained dependency got its target key-context
identity set to that DEPENDENCY's name -- the ad-hoc target's conform node
was key-assessed against the dependency's FK constraints.

Fix: split ``backend_target_name`` (backend detection only) from
``key_target_name`` (key-context identity only). ``execute()`` passes
``key_target_name=None`` so the ad-hoc target is never assessed;
``_collect_with_visitor`` passes ``key_target_name=name`` so
``collect()``/``collect_with_drift()`` keep correct target assessment.

Observable strategy: monkeypatch the ``UnifiedRelationVisitor`` name inside
``mountainash.relations.core.unified_visitor.relation_visitor`` with a
subclass that records ``self.key_context`` at the moment ``visit()`` is
called for a specific node instance (identity match). ``dag.py`` imports
``UnifiedRelationVisitor`` via a local ``from ... import`` inside
``_compile_with_refs``, so it re-resolves the module attribute on every
call and picks up the monkeypatched subclass. This avoids mutating frozen
pydantic ``RelationNode`` instances (``model_config = ConfigDict(frozen=True)``
on ``RelationNode`` forbids instance attribute assignment, including
rebinding ``accept``) while still observing the exact visitor state at
the exact moment the target/dependency node is compiled -- a determinstic,
white-box observable of the code path under test.
"""
from __future__ import annotations

from typing import Any

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.typespec.spec import ForeignKey, ForeignKeyReference


def _fk(fields, resource, ref_fields):
    return ForeignKey(
        fields=list(fields),
        reference=ForeignKeyReference(resource=resource, fields=list(ref_fields)),
    )


@pytest.fixture
def _spy_visitor_factory(monkeypatch):
    """Patch UnifiedRelationVisitor with a subclass that records
    ``self.key_context`` (by node identity) at the moment ``visit()`` is
    invoked, then restores the original class after the test.

    Returns a ``captured`` dict the test can inspect after calling
    ``dag.execute(...)`` / ``dag.collect(...)``.
    """
    from mountainash.relations.core.unified_visitor import relation_visitor as _rv

    original_cls = _rv.UnifiedRelationVisitor
    captured: dict[str, Any] = {}
    watch: dict[int, str] = {}

    class _SpyVisitor(original_cls):  # type: ignore[misc, valid-type]
        def visit(self, node):
            label = watch.get(id(node))
            if label is not None:
                captured[label] = self.key_context
            return super().visit(node)

    monkeypatch.setattr(_rv, "UnifiedRelationVisitor", _SpyVisitor)

    def _register(node, label: str) -> None:
        watch[id(node)] = label

    _register.captured = captured  # type: ignore[attr-defined]
    yield _register


def _dag_with_constrained_dependency():
    """'orders' carries a declared FK to 'customers'."""
    dag = RelationDAG()
    dag.add("customers", ma.relation(pl.DataFrame({"cid": [1, 2], "name": ["a", "b"]})))
    dag.add("orders", ma.relation(pl.DataFrame({"oid": [10, 11], "cid": [1, 2]})))
    dag.add_constraint("orders", _fk(["cid"], "customers", ["cid"]))
    return dag


def test_adhoc_execute_target_has_no_key_context(_spy_visitor_factory):
    """Misattribution regression: an ad-hoc execute() target must be
    compiled with key_context is None, never inheriting the alphabetically-
    first dependency's identity (here: 'orders', chosen by
    sorted(all_refs)[0] purely for backend detection).

    Pre-fix: fails -- captured["target"].resource_name == "orders".
    Post-fix: passes -- captured["target"] is None.
    """
    dag = _dag_with_constrained_dependency()
    adhoc = dag.ref("orders").filter(ma.col("oid").gt(0))
    register = _spy_visitor_factory
    register(adhoc._node, "target")

    dag.execute(adhoc)

    captured = register.captured
    assert "target" in captured, "spy never observed the target node being compiled"
    assert captured["target"] is None


def test_adhoc_execute_dependency_still_gets_own_key_context(_spy_visitor_factory):
    """Companion non-regression check: splitting backend detection from key
    identity must NOT disable per-dependency key assessment under an ad-hoc
    execute() -- 'orders' (the dependency) is still compiled with its OWN
    KeyDriftContext(resource_name='orders'), independent of the (now-None)
    target identity.
    """
    dag = _dag_with_constrained_dependency()
    adhoc = dag.ref("orders").filter(ma.col("oid").gt(0))
    register = _spy_visitor_factory
    register(dag.relations["orders"]._node, "dependency")

    dag.execute(adhoc)

    captured = register.captured
    assert "dependency" in captured, "spy never observed the dependency node being compiled"
    dep_ctx = captured["dependency"]
    assert dep_ctx is not None
    assert dep_ctx.resource_name == "orders"


def test_collect_target_key_context_unaffected_by_split(_spy_visitor_factory):
    """collect()/collect_with_drift() must keep correct TARGET key
    assessment after the split -- _collect_with_visitor passes
    key_target_name=name explicitly.
    """
    dag = _dag_with_constrained_dependency()
    register = _spy_visitor_factory
    register(dag.relations["orders"]._node, "target")

    dag.collect("orders")

    captured = register.captured
    assert "target" in captured
    assert captured["target"] is not None
    assert captured["target"].resource_name == "orders"
