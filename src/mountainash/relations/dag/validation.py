"""DAG validation — delegates to the mountainash.validation runner (spec §10).

FK check generation has exactly one owner: validation.fk.build_fk_checks
(dag.constraint_metadata + spec-supplied TypeSpec.foreign_keys, deduplicated;
invalid declarations surface as status="error" check summaries). Relations
compile per the requested backend through dag.collect — no forced Polars
materialisation. dependency_edges are never read as FK metadata;
constraint_edges alone never create FK checks (two-edge-graph-model).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.validation.result import DAGValidationResult

if TYPE_CHECKING:
    from mountainash.relations.dag.dag import RelationDAG

__all__ = ["DAGValidationResult", "validate", "validate_quick"]


def validate(
    dag: "RelationDAG",
    specs: "dict[str, Any]",
    *,
    context: "dict[str, Any] | None" = None,
    backend: str | None = None,
    failure_sample: int | None = None,
) -> DAGValidationResult:
    """Full validation — all per-resource checks, then all FK checks."""
    return _run(
        dag, specs, context=context, backend=backend,
        fail_fast=False, failure_sample=failure_sample,
    )


def validate_quick(
    dag: "RelationDAG",
    specs: "dict[str, Any]",
    *,
    context: "dict[str, Any] | None" = None,
    backend: str | None = None,
    failure_sample: int | None = None,
) -> DAGValidationResult:
    """Fast validation — same runner, fail_fast=True. Identical shapes."""
    return _run(
        dag, specs, context=context, backend=backend,
        fail_fast=True, failure_sample=failure_sample,
    )


def _run(
    dag: "RelationDAG",
    specs: "dict[str, Any]",
    *,
    context: "dict[str, Any] | None",
    backend: str | None,
    fail_fast: bool,
    failure_sample: int | None,
) -> DAGValidationResult:
    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.datacontracts.contract import BaseDataContract
    from mountainash.typespec.spec import TypeSpec
    from mountainash.validation.fk import build_fk_checks
    from mountainash.validation.identity import resolve_identity
    from mountainash.validation.runner import ValidationRunner

    checks_by_resource: dict[str, list[Any]] = {}
    identity_by_resource: dict[str, Any] = {}
    fk_specs: dict[str, TypeSpec] = {}

    for name, spec in specs.items():
        if name not in dag.relations:
            raise KeyError(f"relation {name!r} not in DAG")
        if isinstance(spec, TypeSpec):
            checks = compile_datacontract(spec)
            spec_for_identity = spec
            natural_key = None
        elif isinstance(spec, type) and issubclass(spec, BaseDataContract):
            checks = spec.to_checks()
            spec_for_identity = spec.to_typespec()
            natural_key = getattr(spec.Config, "natural_key", None)
        else:
            raise TypeError(
                f"specs[{name!r}] must be TypeSpec or BaseDataContract subclass, "
                f"got {type(spec).__name__}"
            )
        checks_by_resource[name] = checks
        fk_specs[name] = spec_for_identity
        identity_by_resource[name] = resolve_identity(
            natural_key=natural_key, spec=spec_for_identity
        )

    fk_rules, fk_errors = build_fk_checks(dag, fk_specs)
    for rule in fk_rules:
        checks_by_resource.setdefault(rule.child, []).append(rule)

    return ValidationRunner().validate_dag(
        dag,
        checks_by_resource,
        identity_by_resource=identity_by_resource,
        context=context,
        fail_fast=fail_fast,
        failure_sample=failure_sample,
        backend=backend,
        fk_error_summaries=fk_errors,
    )
