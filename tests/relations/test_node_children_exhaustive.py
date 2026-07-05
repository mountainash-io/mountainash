"""Closed-by-default exhaustiveness test for RelationNode.children().

The base ``children()`` scans a fixed attribute set (``RELATION_CHILD_ATTRS``).
A future node whose child relation lives under a differently-named field would
silently drop dependency edges in DAG traversal. This test discovers every
concrete RelationNode subclass and fails on any child-bearing field the scan
would miss, unless the class overrides ``children()`` itself
(closed-by-default-verification R1: introspection discovers, assertions verify).
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import types
from typing import Any, Union, get_args, get_origin

import mountainash.relations.core.relation_nodes as _nodes_pkg
from mountainash.relations.core.relation_nodes.reln_base import (
    RELATION_CHILD_ATTRS,
    RelationNode,
)


def _import_all_node_modules() -> None:
    """Import every module under relation_nodes so __subclasses__ discovery is
    complete. The package __init__ re-export lists are deliberately NOT
    trusted: a future node module missing from an __init__ must still be
    discovered (closed-by-default R1)."""
    for mod in pkgutil.walk_packages(
        _nodes_pkg.__path__, prefix=_nodes_pkg.__name__ + "."
    ):
        importlib.import_module(mod.name)
    # Walk the pipelines bridge module so its concrete RelationNode subclasses
    # enter __subclasses__ discovery.
    import contextlib
    with contextlib.suppress(ModuleNotFoundError):
        importlib.import_module("mountainash.pipelines.integration.relation")


def _all_concrete_node_classes() -> set[type[RelationNode]]:
    _import_all_node_modules()
    seen: set[type[RelationNode]] = set()

    def walk(cls: type[RelationNode]) -> None:
        for sub in cls.__subclasses__():
            if sub not in seen:
                seen.add(sub)
                walk(sub)

    walk(RelationNode)
    return {c for c in seen if not inspect.isabstract(c)}


def _involves_relation_node(annotation: object) -> bool:
    """True when the annotation is/contains RelationNode — direct,
    Optional[...], list/tuple/set element, or union member."""
    if isinstance(annotation, type):
        return issubclass(annotation, RelationNode)
    origin = get_origin(annotation)
    if origin in (list, tuple, set, frozenset):
        return any(_involves_relation_node(a) for a in get_args(annotation))
    if origin is Union or isinstance(annotation, types.UnionType):
        return any(
            _involves_relation_node(a)
            for a in get_args(annotation)
            if a is not type(None)
        )
    return False


# Named exemptions: child-bearing fields typed `Any` that are known-safe because
# they use a scanned name. A NEW Any-typed field on a concrete node that is NOT
# scanned must be added here explicitly (closed-by-default).
ANY_TYPED_CHILD_EXEMPTIONS: set[str] = {
    "ParamsRelNode.input",
    "ConformRelNode.spec",    # TypeSpec, not a relation node
    "FilterRelNode.predicate",  # Expression, not a relation node
    "JoinRelNode.tolerance",    # Literal value, not a relation node
    "PipelineStepRelNode.pipeline",  # Pipeline config, not a relation node
    "ReadRelNode.dataframe",    # DataFrame, not a relation node
    "SourceRelNode.data",       # Generic data, not a relation node
}


def _any_typed_failures(cls: type[RelationNode]) -> list[str]:
    """Return actionable failure strings for Any-typed fields on `cls` that are
    neither a scanned child-attr name nor explicitly exempted."""
    out: list[str] = []
    for name, field in cls.model_fields.items():
        if field.annotation is not Any:
            continue
        qualified = f"{cls.__name__}.{name}"
        if name in RELATION_CHILD_ATTRS or qualified in ANY_TYPED_CHILD_EXEMPTIONS:
            continue
        out.append(f"{qualified} (Any-typed; scanned-name-or-exempt required)")
    return out


def test_discovery_finds_both_node_packages():
    names = {c.__name__ for c in _all_concrete_node_classes()}
    # Canary classes — one per package — prove the module walk and the
    # subclass discovery actually worked (guards against a silently-empty sweep).
    assert "ProjectRelNode" in names          # relations/core substrait node
    assert "RefRelNode" in names              # relations/core extension node
    # Pipelines bridge canary: the pipelines import is wrapped in
    # suppress(ModuleNotFoundError), so a future rename/move would silently
    # degrade the walk to zero pipeline nodes and the Any-guard sweep would pass
    # vacuously. Assert a real pipelines node is discovered so that regresses LOUDLY.
    assert "PipelineStepRelNode" in names


def test_every_child_field_is_scanned_or_children_overridden():
    failures: list[str] = []
    for cls in sorted(_all_concrete_node_classes(), key=lambda c: c.__name__):
        if cls.children is not RelationNode.children:
            # An override takes responsibility for its own child enumeration.
            continue
        # Pydantic v2 resolves postponed (string) annotations at model-class
        # creation, so field.annotation is already the concrete type object —
        # equivalent to typing.get_type_hints output, without its
        # namespace-resolution pitfalls on Pydantic models.
        child_fields = {
            name
            for name, field in cls.model_fields.items()
            if _involves_relation_node(field.annotation)
        }
        unscanned = child_fields - set(RELATION_CHILD_ATTRS)
        for field_name in sorted(unscanned):
            failures.append(f"{cls.__name__}.{field_name}")
        failures.extend(_any_typed_failures(cls))
    assert not failures, (
        "Child-bearing relation-node fields invisible to the base children() "
        f"scan {RELATION_CHILD_ATTRS}: {failures}. Fix by renaming the field "
        "to a scanned name, extending RELATION_CHILD_ATTRS in reln_base.py "
        "(and children()), or overriding children() on the node class."
    )


def test_any_guard_flags_unexempted_any_child():
    """Construct a concrete node with an unexempted Any-typed field and assert
    the guard reports it. Without the guard this blind spot is silent."""
    from mountainash.relations.core.relation_nodes.reln_base import RelationNode

    class _RogueNode(RelationNode):
        # A child-bearing field typed Any, NOT a scanned name, NOT exempted.
        sidecar: Any = None

    failures = _any_typed_failures(_RogueNode)
    assert any("sidecar" in f for f in failures)


def test_any_guard_passes_scanned_or_exempt():
    from mountainash.relations.core.relation_nodes.reln_base import RelationNode

    class _OkNode(RelationNode):
        input: Any = None             # scanned child-attr name -> allowed

    assert _any_typed_failures(_OkNode) == []
