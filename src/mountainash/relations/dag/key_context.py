"""KeyDriftContext — DAG-provided FK context threaded into the conform visitor.

This is a `+1` optional visitor parameter, analogous to ``ref_resolver``
(see `a.architecture/dag/relation-dag-orchestrator.md`: the DAG stays a
thin orchestrator; the visitor stays the single compiler). It is
constructed per ``RelationDAG.collect()``/``execute()`` call (and
re-pointed per compiled dependency via ``dataclasses.replace``) and
passed into ``UnifiedRelationVisitor`` so ``apply_conform`` can evaluate
declared foreign-key constraints against the conformed output (item 48,
`keys` dimension, PR-D).

A bare ``Relation.conform()`` call with no owning ``RelationDAG`` never
constructs this — ``UnifiedRelationVisitor.key_context`` stays ``None``
and ``ConformDrift.key_changes`` stays ``None`` (not assessed, per the
None-vs-``[]`` distinction documented on ``ConformDrift``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.relations.schema_inference import SchemaTypeStatus
    from mountainash.typespec.spec import ForeignKey


@dataclass(frozen=True)
class KeyDriftContext:
    """DAG-provided FK context for the conform visitor.

    Attributes:
        resource_name: The name of the DAG relation *currently being
            compiled* — the fallback "child" identity used when
            ``apply_conform``'s own ``resource_name`` argument is ``None``
            (a bare ``.conform()`` call with no owning
            ``ResourceReadRelNode``). The DAG re-points this per node via
            ``dataclasses.replace`` in its dependency loop (see
            ``RelationDAG._compile_with_refs``), so each dependency's key
            assessment runs against its OWN constraints, never the
            collect-target's. For a ``ResourceReadRelNode`` conform, the
            call-site ``resource_name`` (the Frictionless resource's own
            name) is used instead — see
            ``UnifiedRelationVisitor.apply_conform``.
        constraints_for: ``RelationDAG.constraints_for`` bound method —
            all foreign keys declared with a given name as the child
            side (item 46(c) ``constraint_metadata``).
        schema_of: ``RelationDAG.schema`` bound method — the ref-resolved
            inferred schema for a named relation, used to resolve a FK's
            reference-side fields/dtypes. Raises ``KeyError`` for an
            unknown name, which callers translate into a
            ``dangling_reference`` finding.
    """

    resource_name: str
    constraints_for: "Callable[[str], list[ForeignKey]]"
    schema_of: "Callable[[str], dict[str, MountainashDtype | SchemaTypeStatus]]"
