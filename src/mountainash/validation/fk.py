"""build_fk_checks — the single owner of FK check generation (spec §10).

Canonicalises FK declarations from BOTH sources — dag.constraint_metadata
(the DAG-native field-level store) and spec-supplied TypeSpec.foreign_keys —
into one deduplicated set. Invalid or unresolvable declarations become
CheckSummary(status="error") entries: never raised mid-run, never silently
skipped (closed-by-default-verification). dependency_edges are never read;
constraint_edges alone never create checks (two-edge-graph-model).
"""
from __future__ import annotations

from typing import Any

from mountainash.validation.checks import ForeignKeyRule
from mountainash.validation.result import CheckSummary


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
