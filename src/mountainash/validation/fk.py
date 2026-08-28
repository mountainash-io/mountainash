"""build_fk_checks — the single owner of FK check generation (spec §10).

Canonicalises FK declarations from BOTH sources — dag.constraint_metadata
(the DAG-native field-level store) and spec-supplied TypeSpec.foreign_keys —
into one deduplicated set. Invalid or unresolvable declarations become
CheckSummary(status="error") entries: never raised mid-run, never silently
skipped (closed-by-default-verification). dependency_edges are never read;
constraint_edges alone never create checks (two-edge-graph-model).

``_canonical_key_rows()`` (Task 9, spec 15.2) extracts one
:class:`CanonicalKeyRow` per retained row from a prepared validation
input's logical snapshot -- every foreign-key comparison uses
``canonical_value_key()`` over decoded logical values, never a backend
join. A JSON-text/opaque carrier's raw physical bytes can never define
logical equality (whitespace and object-name order differ between
structurally-equal values), so a backend anti-join is not merely
inefficient here, it is incorrect.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from mountainash.validation.checks import ForeignKeyRule
from mountainash.validation.result import CheckSummary

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mountainash.validation.prepared import PreparedValidationInput


@dataclass(frozen=True)
class CanonicalKeyRow:
    """One retained row's composite key, canonicalized for equality.

    ``outcome`` classifies the row before any parent-set comparison:

    - ``"candidate"`` -- every component resolved to a real logical value;
      ``key`` is the canonical tuple used for set membership.
    - ``"excluded_null"`` -- at least one component is logical null. On
      the child side this is SQL MATCH SIMPLE's any-null exclusion (spec
      15.2); on the parent side a null-containing row never contributes a
      target key either way, since no MATCH-SIMPLE-excluded child key
      could ever need to find it.
    - ``"unknown"`` -- at least one component is `INVALID_VALUE` (an
      unresolved `coerce` decode). A child row in this state is neither
      proven to match nor proven to be an orphan; a parent row in this
      state never creates a target key (spec 15.2: "An invalid parent
      component does not create a target key").
    """

    ordinal: int
    key: "tuple[Any, ...] | None"
    outcome: 'Literal["candidate", "excluded_null", "unknown"]'


@dataclass(frozen=True)
class CanonicalKeyRows:
    """Every retained row's :class:`CanonicalKeyRow`, in logical-snapshot order."""

    rows: "tuple[CanonicalKeyRow, ...]"


def _canonical_key_rows(
    prepared: "PreparedValidationInput", fields: "Sequence[str]", *, child: bool
) -> CanonicalKeyRows:
    """Extract one :class:`CanonicalKeyRow` per retained row of *prepared*'s
    logical snapshot for the composite key named by *fields*.

    *child* documents which side of the comparison the caller is building
    -- the classification rule itself (null / invalid / candidate) is the
    same for both sides; interpreting an ``"excluded_null"`` child row
    under `ForeignKeyRule.exclude_null_child` is the caller's job, not
    this function's.
    """
    from mountainash.relations.core.logical_snapshot import logical_column_values
    from mountainash.validation.value import INVALID_VALUE, canonical_value_key

    del child  # documents intent at the call site; the rule below is side-agnostic
    snapshot = prepared.logical_snapshot
    ordinals = snapshot.keep_ordinals
    field_columns = [logical_column_values(snapshot, name) for name in fields]
    rows: "list[CanonicalKeyRow]" = []
    for index, values in enumerate(zip(*field_columns, strict=True)):
        ordinal = ordinals[index]
        if any(value is None for value in values):
            rows.append(CanonicalKeyRow(ordinal=ordinal, key=None, outcome="excluded_null"))
        elif any(value is INVALID_VALUE for value in values):
            rows.append(CanonicalKeyRow(ordinal=ordinal, key=None, outcome="unknown"))
        else:
            key = tuple(canonical_value_key(value) for value in values)
            rows.append(CanonicalKeyRow(ordinal=ordinal, key=key, outcome="candidate"))
    return CanonicalKeyRows(rows=tuple(rows))



def build_standalone_fk_checks(
    plan: Any,
    *,
    resource_name: str,
) -> tuple[ForeignKeyRule, ...]:
    """Build plan-owned self-reference checks without a RelationDAG.

    Cross-resource references need parent materialization and are therefore
    rejected before a standalone runner can read either side.
    """
    from mountainash.relations.dag.errors import RelationDAGRequired

    rules: list[ForeignKeyRule] = []
    for foreign_key in plan.foreign_keys:
        parent = foreign_key.parent_resource or resource_name
        if parent != resource_name:
            raise RelationDAGRequired(
                f"foreign key from {resource_name!r} to {parent!r} requires RelationDAG"
            )
        rules.append(
            ForeignKeyRule(
                id=_fk_check_id(resource_name, parent, list(foreign_key.child_fields)),
                child=resource_name,
                parent=parent,
                child_fields=list(foreign_key.child_fields),
                parent_fields=list(foreign_key.parent_fields),
            )
        )
    return tuple(rules)


def _fk_check_id(child: str, parent: str, child_fields: "list[str]") -> str:
    return f"fk__{child}__{'.'.join(child_fields)}__{parent}"


def _schema_columns(dag: Any, name: str) -> "set[str] | None":
    """Column names for a DAG resource via schema inference, or None when
    inference is unavailable."""
    try:
        return set(dag.schema(name).keys())
    except Exception:  # noqa: BLE001 — inference failure yields no evidence
        return None


def _resource_columns(
    dag: Any, name: str, spec_fields: "dict[str, set[str]]"
) -> "set[str] | None":
    """Best evidence of a resource's columns: spec-declared fields first,
    then DAG schema inference. Returns None only when NEITHER source has
    evidence — only then is field-presence validation deferred to execution,
    where a missing column fails the compiled plan and is captured by the
    runner's isolation guard as status="error" (closed-by-default either way;
    early validation just gives the better message)."""
    declared = spec_fields.get(name)
    if declared:
        return declared
    return _schema_columns(dag, name)


def build_fk_checks(
    dag: Any, specs: "dict[str, Any] | None" = None
) -> "tuple[list[ForeignKeyRule], list[CheckSummary]]":
    specs = specs or {}
    # Spec-declared field names are first-class evidence for declaration
    # validation (they don't depend on DAG schema inference succeeding).
    spec_fields: "dict[str, set[str]]" = {
        name: {f.name for f in spec.fields}
        for name, spec in specs.items()
        if getattr(spec, "fields", None)
    }
    declarations: dict[tuple, dict[str, Any]] = {}

    def _add(child: str, fk: Any) -> None:
        parent = fk.reference.resource or child  # empty/self reference -> child
        decl = {
            "child": child,
            "parent": parent,
            "child_fields": list(fk.fields),
            "parent_fields": list(fk.reference.fields),
        }
        key = (child, parent, tuple(decl["child_fields"]), tuple(decl["parent_fields"]))
        declarations.setdefault(key, decl)

    # Source 1: DAG-native constraint metadata (constraints_for-equivalent walk).
    for (_target, child), fks in dag.constraint_metadata.items():
        for fk in fks:
            _add(child, fk)

    # Source 2: spec-supplied TypeSpec.foreign_keys.
    for child, spec in specs.items():
        for fk in getattr(spec, "foreign_keys", None) or []:
            _add(child, fk)

    rules: list[ForeignKeyRule] = []
    errors: list[CheckSummary] = []
    for decl in declarations.values():
        check_id = _fk_check_id(decl["child"], decl["parent"], decl["child_fields"])
        problem = _validate_declaration(dag, decl, spec_fields)
        if problem is not None:
            errors.append(
                CheckSummary(
                    check_id=check_id,
                    check_kind="foreign_key",
                    status="error",
                    error=problem,
                )
            )
            continue
        rules.append(
            ForeignKeyRule(
                id=check_id,
                child=decl["child"],
                parent=decl["parent"],
                child_fields=decl["child_fields"],
                parent_fields=decl["parent_fields"],
            )
        )
    return rules, errors


def _validate_declaration(
    dag: Any, decl: "dict[str, Any]", spec_fields: "dict[str, set[str]]"
) -> "str | None":
    child, parent = decl["child"], decl["parent"]
    child_fields, parent_fields = decl["child_fields"], decl["parent_fields"]

    if child not in dag.relations:
        return f"child resource {child!r} not in DAG"
    if parent not in dag.relations:
        return f"foreign-key parent {parent!r} not in DAG (unresolvable declaration)"
    if not child_fields or not parent_fields:
        return "FK declaration has empty field list"
    if len(child_fields) != len(parent_fields):
        return (
            f"FK arity mismatch: {len(child_fields)} child fields "
            f"vs {len(parent_fields)} parent fields"
        )

    child_cols = _resource_columns(dag, child, spec_fields)
    if child_cols is not None:
        missing = [f for f in child_fields if f not in child_cols]
        if missing:
            return f"child fields missing from {child!r} schema: {missing}"
    parent_cols = _resource_columns(dag, parent, spec_fields)
    if parent_cols is not None:
        missing = [f for f in parent_fields if f not in parent_cols]
        if missing:
            return f"parent fields missing from {parent!r} schema: {missing}"
    return None
