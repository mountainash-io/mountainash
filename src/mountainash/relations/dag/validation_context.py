"""Per-session validation preparation cache (spec section 10, Task 8).

``DAGValidationContext`` sits outside ``ref_resolver`` -- it owns one
``PreparedValidationInput`` (logical-terminal snapshot + resolved logical
columns) per DAG-registered resource name, memoized for the context's
lifetime. Multiple local validation consumers for the same resource (a
keyed-identity check, a value-rule check, a foreign-key check) therefore
share one relation compilation, one canonical native cache entry, one
logical snapshot, and one decoded cell result per declared structured
cell -- instead of each independently calling
:func:`~mountainash.validation.prepared.prepare_validation_input_from_session`
and re-deriving the snapshot.

The underlying :class:`~mountainash.relations.dag.materialization.DAGMaterializationSession`
remains the only owner of the native execution-value cache; this context
never stores or exposes anything beyond the ``PreparedValidationInput``
objects it memoizes.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.relations.dag.materialization import DAGMaterializationSession
    from mountainash.validation.prepared import PreparedValidationInput

__all__ = ["DAGValidationContext"]


class DAGValidationContext:
    """Memoizes one :class:`PreparedValidationInput` per resource name for
    the lifetime of one DAG validation run."""

    def __init__(self, session: "DAGMaterializationSession") -> None:
        self._session = session
        self._prepared: "dict[str, PreparedValidationInput]" = {}

    def prepare(self, name: str) -> "PreparedValidationInput":
        """The resource's prepared validation input, computed once and
        reused by every later caller for the same *name*."""
        if name not in self._prepared:
            from mountainash.validation.prepared import prepare_validation_input_from_session

            self._prepared[name] = prepare_validation_input_from_session(self._session, name)
        return self._prepared[name]
