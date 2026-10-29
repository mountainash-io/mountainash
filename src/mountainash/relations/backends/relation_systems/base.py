"""Shared base for backend relation systems: backend identity + dialect.

Relation limitations are declared in capability modules and enforced
through the capability registry — the
compile-time gate (``_gate_capabilities``) for BUILD facts and
``enrich_materialization`` (registry residue) for MATERIALIZE facts. The
legacy ``KNOWN_REL_LIMITATIONS`` class dict was retired in the spine's
Phase 1.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.core.dtypes.protocols import ResolvedType
    from mountainash.relations.core.execution.location import ExecutionLocation


class BaseRelationSystem:
    """Mixin carrying backend identity for all relation systems."""

    BACKEND_NAME: str = "unknown"

    def __init__(self, dialect: str | None = None) -> None:
        self.dialect = dialect

    def describe_output_schema(
        self, native: Any, *, location: ExecutionLocation,
    ) -> dict[str, ResolvedType]:
        """Output types of a native relation, from its schema adapter's evidence.

        Sufficient where the native carrier's schema is its physical output
        (Polars, Narwhals-wrapped pandas/Arrow/Polars). A backend whose logical
        schema can differ from what its engine produces overrides this.
        """
        from mountainash.typespec.source_shape import extract_source_shapes, shape_type_evidence

        return {
            name: shape_type_evidence(shape)
            for name, shape in extract_source_shapes(native).items()
        }

    def _import_resource(self, arrow: Any, location: Any) -> Any:
        """Import a parsed resource into ``location``, refusing like any transfer.

        The parsed table stands where raw rows do: in-memory Polars. A destination
        that cannot store it raises the shared typed import refusal.
        """
        from mountainash.core.constants import CONST_BACKEND
        from mountainash.core.errors import BackendConversionError
        from mountainash.relations.core.execution.location import ExecutionLocation
        from mountainash.relations.core.execution.transport import import_refusal
        from mountainash.relations.core.materialization import ExecutionForm

        try:
            return self.import_into(arrow, location=location).value
        except (BackendConversionError, ValueError) as exc:
            source = ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.EAGER, "bound")
            raise import_refusal(source, location, exc) from exc

    @staticmethod
    def _cross_join_names(
        left_names: tuple[str, ...], right_names: tuple[str, ...], suffix: str,
    ) -> tuple[str, ...] | None:
        """Left names, then right names, suffixing only those colliding with the left.

        None when the combination yields duplicate output names.
        """
        left = set(left_names)
        names = (*left_names, *(f"{n}{suffix}" if n in left else n for n in right_names))
        return names if len(set(names)) == len(names) else None
