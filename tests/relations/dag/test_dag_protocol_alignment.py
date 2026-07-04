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


def _public_class_members(cls: type) -> set[str]:
    """Public surface: plain functions AND property/classmethod/staticmethod
    descriptors (which escape inspect.isfunction / vars(instance)).

    Walks the MRO's raw ``__dict__`` so descriptors are seen unresolved: on a
    classmethod, ``inspect.getmembers(cls)`` returns the *bound* method (whose
    type is not ``classmethod``) and would miss it, and ``getmembers_static``
    is 3.11+ while this package supports 3.10 — the MRO/``vars`` walk is
    version-independent and preserves the descriptor objects."""
    names: set[str] = set()
    for klass in cls.__mro__:
        if klass is object:
            continue
        for name, member in vars(klass).items():
            if name.startswith("_"):
                continue
            if inspect.isfunction(member) or isinstance(
                member, (property, classmethod, staticmethod)
            ):
                names.add(name)
    return names


def _dag_public_surface() -> set[str]:
    instance_attrs = {n for n in vars(RelationDAG()) if not n.startswith("_")}
    return instance_attrs | _public_class_members(RelationDAG)


def _protocol_members() -> set[str]:
    annotations = {
        n
        for n in getattr(RelationDAGProtocol, "__annotations__", {})
        if not n.startswith("_")
    }
    return annotations | _public_class_members(RelationDAGProtocol)


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


def test_discovery_catches_property_and_classmethod():
    """A public property/classmethod on the surface class MUST be discovered.
    Without the fix these descriptors are invisible (regression guard)."""
    class _Probe:
        @property
        def visible_prop(self):        # public -> must be seen
            return 1

        @classmethod
        def visible_cm(cls):           # public -> must be seen
            return 2

        def _hidden(self):             # underscore -> must be ignored
            return 3

    surface = _public_class_members(_Probe)
    assert "visible_prop" in surface
    assert "visible_cm" in surface
    assert "_hidden" not in surface


def test_alignment_would_flag_protocol_absent_public_property():
    """If a public property exists on RelationDAG but not the protocol, the
    surface diff must be non-empty (the sweep would fail). Proven on a probe
    subclass so the real classes stay clean."""
    class _DAGWithExtra(RelationDAG):
        @property
        def rogue(self):
            return object()

    dag_surface = _public_class_members(_DAGWithExtra)
    protocol_surface = _public_class_members(RelationDAGProtocol)
    assert "rogue" in dag_surface - protocol_surface


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
