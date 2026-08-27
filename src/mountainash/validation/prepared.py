"""Standalone validation-source preparation (spec section 6, Task 6).

``ValidationRunner.validate_relation()`` used to collapse the (possibly
conform-laden) plan via ``Relation.collect(unwrap=False)`` -- a generic
``NATIVE_COLLECT`` purpose that leaves an Ibis source ``DEFERRED``, so every
per-check executor re-executed the whole query plan from scratch. This
module compiles the relation exactly once and materializes it with the
dedicated ``VALIDATION_SOURCE`` purpose instead, which forces an Ibis table
eager via a single ``.cache()`` call (spec 7.2), owned by the caller's
``MaterializationScope``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mountainash.core.errors import BackendConversionError

if TYPE_CHECKING:
    from mountainash.relations import Relation
    from mountainash.relations.core.materialization import (
        DiagnosticFrameView,
        MaterializationScope,
        NativeExecutionValue,
    )

__all__ = [
    "PreparedValidationInput",
    "assert_prepared_identity",
    "prepare_validation_input",
]


@dataclass(frozen=True)
class PreparedValidationInput:
    """One compiled-once, materialized-once validation source (spec section 6)."""

    relation: "Relation"
    native: "NativeExecutionValue"
    diagnostic_source: "DiagnosticFrameView | None" = None


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
    per check.
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
    return PreparedValidationInput(relation=as_relation(native.value), native=native)
