"""Closed-by-default alignment: RelationDAG public surface ⇄ RelationDAGProtocol.

Per closed-by-default-verification R1–R3: introspection discovers the class's
public surface — methods AND instance attributes from a constructed instance
(graph state is assigned in __init__, so class-only introspection would miss
exactly the state the protocol exists to guard). Assertions verify every
member is either declared on the protocol or listed in the named delegator
exception set. A future public method without a protocol entry fails here.
"""
from __future__ import annotations

import inspect

from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.protocol import RelationDAGProtocol

# name -> (reason, since). Thin delegators over the helper modules: the
# helpers consume the protocol, so declaring these on it would be circular —
# an alternative DAG implementation gets them for free by satisfying the
# orchestration contract via the same helper functions.
DELEGATOR_EXCEPTIONS: dict[str, tuple[str, str]] = {
    "describe": ("delegates to introspection.describe", "2026-07-04"),
    "to_dot": ("delegates to introspection.to_dot", "2026-07-04"),
    "to_package": ("delegates to packaging.to_package", "2026-07-04"),
    "validate": ("delegates to validation.validate", "2026-07-04"),
    "validate_quick": ("delegates to validation.validate_quick", "2026-07-04"),
}


def _public_class_methods(cls: type) -> set[str]:
    return {
        name
        for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def _dag_public_surface() -> set[str]:
    instance_attrs = {n for n in vars(RelationDAG()) if not n.startswith("_")}
    return instance_attrs | _public_class_methods(RelationDAG)


def _protocol_members() -> set[str]:
    annotations = {
        n
        for n in getattr(RelationDAGProtocol, "__annotations__", {})
        if not n.startswith("_")
    }
    return annotations | _public_class_methods(RelationDAGProtocol)


def test_protocol_covers_public_surface():
    missing = _dag_public_surface() - _protocol_members() - set(DELEGATOR_EXCEPTIONS)
    assert not missing, (
        f"RelationDAG public members absent from RelationDAGProtocol: "
        f"{sorted(missing)}. Add each to the protocol, or (for a thin helper "
        "delegator) to DELEGATOR_EXCEPTIONS with a reason."
    )


def test_protocol_declares_no_phantom_members():
    phantom = _protocol_members() - _dag_public_surface()
    assert not phantom, (
        f"RelationDAGProtocol declares members RelationDAG does not provide: "
        f"{sorted(phantom)}"
    )


def test_delegator_exceptions_are_real_and_not_duplicated():
    surface = _dag_public_surface()
    declared = _protocol_members()
    for name in DELEGATOR_EXCEPTIONS:
        assert name in surface, (
            f"stale exception entry: {name!r} is no longer on RelationDAG"
        )
        assert name not in declared, (
            f"{name!r} is both a protocol member and an exception entry — remove one"
        )


def test_shared_method_signatures_match():
    shared = _public_class_methods(RelationDAG) & _public_class_methods(
        RelationDAGProtocol
    )
    assert shared, "no shared methods found — introspection is broken"
    # Compares (name, kind, default) — a drifted default (e.g. backend=None
    # becoming required) fails here. Annotation equality is deliberately out
    # of scope: under `from __future__ import annotations` the spellings
    # legitimately differ (`Optional[str]` in dag.py vs `str | None` in the
    # protocol) while denoting the same type.
    for name in sorted(shared):
        proto_params = [
            (p.name, p.kind, p.default)
            for p in inspect.signature(
                getattr(RelationDAGProtocol, name)
            ).parameters.values()
        ]
        impl_params = [
            (p.name, p.kind, p.default)
            for p in inspect.signature(getattr(RelationDAG, name)).parameters.values()
        ]
        assert impl_params == proto_params, (
            f"signature drift on {name!r}: protocol {proto_params} vs "
            f"RelationDAG {impl_params}"
        )
