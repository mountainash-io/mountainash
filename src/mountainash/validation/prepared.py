"""Standalone validation-source preparation (spec section 6, Task 6).

``ValidationRunner.validate_relation()`` used to collapse the (possibly
conform-laden) plan via ``Relation.collect(unwrap=False)`` -- a generic
``NATIVE_COLLECT`` purpose that leaves an Ibis source ``DEFERRED``, so every
per-check executor re-executed the whole query plan from scratch. This
module compiles the relation exactly once and materializes it with the
dedicated ``VALIDATION_SOURCE`` purpose instead, which forces an Ibis table
eager via a single ``.cache()`` call (spec 7.2), owned by the caller's
``MaterializationScope``.

One shared logical-terminal snapshot (Tasks 3/4) is then resolved once with
``StructuredActionConsumer.VALIDATION`` -- every value check, the transported
``required`` interception, identity, and uniqueness read the same decoded
logical values and share the same row ordinals, instead of each re-decoding
structured cells independently.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mountainash.core.errors import BackendConversionError

if TYPE_CHECKING:
    from mountainash.conform.structured_transport import StructuredFieldPlanMap
    from mountainash.relations import Relation
    from mountainash.relations.core.logical_snapshot import (
        LogicalTerminalSnapshot,
        ResolvedLogicalSnapshot,
    )
    from mountainash.relations.core.materialization import (
        MaterializationScope,
        NativeExecutionValue,
    )
    from mountainash.relations.dag.materialization import DAGMaterializationSession

__all__ = [
    "PreparedValidationInput",
    "assert_prepared_identity",
    "prepare_validation_input",
    "prepare_validation_input_from_session",
]


@dataclass(frozen=True)
class PreparedValidationInput:
    """One compiled-once, materialized-once validation source (spec section 6)."""

    relation: "Relation"
    native: "NativeExecutionValue"
    structured_field_plans: "StructuredFieldPlanMap"
    snapshot: "LogicalTerminalSnapshot"
    logical_snapshot: "ResolvedLogicalSnapshot"


def assert_prepared_identity(native: "NativeExecutionValue", value: Any) -> None:
    """Re-verify *value*'s independently detected backend identity matches
    *native*'s recorded ``value_identity``.

    The recorded identity is authoritative -- this independent
    :func:`~mountainash.core.backend_detection.identify_backend_identity`
    re-check is only a consistency assertion, never a second source of
    truth.
    """
    from mountainash.core.backend_detection import identify_backend_identity

    detected = identify_backend_identity(value)
    if detected != native.value_identity:
        raise BackendConversionError(
            "prepared validation input's independently detected backend "
            "identity diverges from its recorded native.value_identity",
            boundary_key=None,
            source_family=str(native.value_identity.family),
            source_dialect=native.value_identity.dialect,
            destination_family=str(detected.family),
            destination_dialect=detected.dialect,
            source_type=type(value).__name__,
            route="assert_prepared_identity",
            reason=(
                "materialize_native()'s recorded value_identity must match "
                "an independent identify_backend_identity() re-check"
            ),
        )


def _resolve_prepared_snapshot(
    native: "NativeExecutionValue",
    structured_field_plans: "StructuredFieldPlanMap",
) -> "tuple[LogicalTerminalSnapshot, ResolvedLogicalSnapshot]":
    """One physical snapshot, resolved once for validation consumers.

    Shared by both producer functions below so a caller never re-derives
    the diagnostic frame via ``diagnostic_polars_view()`` after the
    snapshot exists (spec Task 6 step 4) -- the snapshot IS the one eager
    read; every downstream consumer reads through it.
    """
    from mountainash.conform.structured_transport import StructuredActionConsumer
    from mountainash.relations.core.logical_snapshot import (
        logical_terminal_snapshot,
        resolve_logical_snapshot,
    )

    snapshot = logical_terminal_snapshot(native)
    logical_snapshot = resolve_logical_snapshot(
        snapshot, structured_field_plans, consumer=StructuredActionConsumer.VALIDATION
    )
    return snapshot, logical_snapshot


def prepare_validation_input(
    relation: "Relation | Any",
    *,
    backend: str | None = None,
    scope: "MaterializationScope",
) -> PreparedValidationInput:
    """Compile *relation* once and materialize it with the dedicated
    ``VALIDATION_SOURCE`` purpose (spec section 6).

    An Ibis source is forced eager via exactly one ``.cache()`` call, owned
    by *scope*, so every downstream check executor reuses the same
    materialized result instead of re-executing the whole query plan once
    per check. The resulting logical-terminal snapshot adds exactly one
    ``.to_pyarrow()``/``.to_arrow()`` extraction on top of that same cache
    (Task 6 step 1) -- never a second native execution.
    """
    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.relations import Relation
    from mountainash.relations import relation as as_relation
    from mountainash.relations.core.materialization import (
        MaterializationPurpose,
        materialize_native,
    )

    rel = relation if isinstance(relation, Relation) else as_relation(relation)
    result, visitor = rel._compile_and_execute_with_visitor(backend=backend)
    compiler_identity = BackendIdentity(visitor.backend.backend_type, visitor.backend.dialect)
    native = materialize_native(
        result, compiler_identity, MaterializationPurpose.VALIDATION_SOURCE, scope=scope
    )
    assert_prepared_identity(native, native.value)
    snapshot, logical_snapshot = _resolve_prepared_snapshot(native, visitor.structured_field_plans)
    return PreparedValidationInput(
        relation=as_relation(native.value),
        native=native,
        structured_field_plans=visitor.structured_field_plans,
        snapshot=snapshot,
        logical_snapshot=logical_snapshot,
    )


def prepare_validation_input_from_session(
    session: "DAGMaterializationSession", name: str
) -> PreparedValidationInput:
    """Build a :class:`PreparedValidationInput` for a DAG-registered *name*
    from an already-shared :class:`~mountainash.relations.dag.materialization.DAGMaterializationSession`
    (Task 8, spec section 10/18: "the Unit D node transform hook for
    planned resources").

    Unlike :func:`prepare_validation_input`, this never *compiles* *name*
    itself -- ``session.compile_registered()`` already compiles and
    materializes it (memoized, shared with every other consumer in the
    same session: a dependency, another planned resource's foreign-key
    reference, ...), so multiple validated resources referencing the same
    upstream DAG relation share one compile instead of each re-running
    ``prepare_validation_input()`` independently.

    A Polars/Narwhals DAG-canonical native intentionally stays lazy (spec
    10.2/10.4's documented lazy-when-possible contract, so Polars' own
    optimizer can fuse shared subexpressions); a keyed/row identity check
    and a logical-terminal snapshot both need concrete columns, so
    ``session.validation_native()`` forces exactly one ``.collect()`` on
    top of that shared canonical value the first time *name* is
    validated, memoized per name -- an Ibis DAG-canonical native is
    already forced eager via ``.cache()`` at DAG_CANONICAL compile time
    (spec 10.2) and passes through unchanged.
    """
    from mountainash.relations import relation as as_relation

    native, visitor = session.validation_native(name)
    assert_prepared_identity(native, native.value)
    snapshot, logical_snapshot = _resolve_prepared_snapshot(native, visitor.structured_field_plans)
    return PreparedValidationInput(
        relation=as_relation(native.value),
        native=native,
        structured_field_plans=visitor.structured_field_plans,
        snapshot=snapshot,
        logical_snapshot=logical_snapshot,
    )
