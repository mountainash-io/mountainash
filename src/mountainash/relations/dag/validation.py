"""DAG validation types and FK referential integrity checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import polars as pl

    from mountainash.datacontracts.result import ValidationResult
    from mountainash.relations.dag.dag import RelationDAG


@dataclass
class FKViolation:
    """A foreign key referential integrity violation."""

    child_table: str
    parent_table: str
    child_fields: list[str]
    parent_fields: list[str]
    orphan_count: int
    orphan_sample: pl.DataFrame


@dataclass
class DAGValidationResult:
    """Result of a DAG-level validation run."""

    passes: bool
    table_results: dict[str, ValidationResult] = field(default_factory=dict)
    fk_violations: list[FKViolation] = field(default_factory=list)
    message: str | None = None


FK_SAMPLE_SIZE = 10


def validate(
    dag: RelationDAG,
    specs: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> DAGValidationResult:
    """Full validation for a DAG."""
    table_results, cache = _validate_tables(dag, specs, context=context, fast=False)
    fk_violations = _check_all_fks(specs, cache, fast=False)

    passes = all(r.passes for r in table_results.values()) and not fk_violations
    return DAGValidationResult(
        passes=passes,
        table_results=table_results,
        fk_violations=fk_violations,
    )


def validate_quick(
    dag: RelationDAG,
    specs: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> DAGValidationResult:
    """Fast validation for a DAG."""
    table_results, cache = _validate_tables(dag, specs, context=context, fast=True)

    if any(not r.passes for r in table_results.values()):
        return DAGValidationResult(
            passes=False,
            table_results=table_results,
        )

    fk_violations = _check_all_fks(specs, cache, fast=True)

    return DAGValidationResult(
        passes=not fk_violations,
        table_results=table_results,
        fk_violations=fk_violations,
    )


def _validate_tables(
    dag: RelationDAG,
    specs: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
    fast: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Materialize and validate each table. Returns ``(results, cache)``."""
    from mountainash.datacontracts.contract import BaseDataContract
    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.datacontracts.validator import Validator
    from mountainash.typespec.spec import TypeSpec

    table_results: dict[str, Any] = {}
    cache: dict[str, Any] = {}

    for name, spec in specs.items():
        if name not in dag.relations:
            raise KeyError(f"relation {name!r} not in DAG")

        df = _to_validation_polars(dag, name)
        cache[name] = df

        if isinstance(spec, TypeSpec):
            contract = compile_datacontract(spec, name=name)
        elif isinstance(spec, type) and issubclass(spec, BaseDataContract):
            contract = spec
        else:
            raise TypeError(
                f"specs[{name!r}] must be TypeSpec or BaseDataContract subclass, "
                f"got {type(spec).__name__}"
            )

        validator = Validator(name=name, contract=contract)
        result = (
            validator.validate_quick(df, context=context)
            if fast
            else validator.validate(df, context=context)
        )
        table_results[name] = result

        if fast and not result.passes:
            break

    return table_results, cache


def _to_validation_polars(dag: RelationDAG, name: str) -> Any:
    """Materialize a relation for current Polars-only validation semantics."""
    from mountainash.core.types import (
        is_pandas_dataframe,
        is_polars_dataframe,
        is_polars_lazyframe,
    )

    result = dag.collect(name, backend="polars")
    if is_polars_lazyframe(result):
        return result.collect()
    if is_polars_dataframe(result):
        return result

    import polars as pl

    if is_pandas_dataframe(result):
        return pl.from_pandas(result)
    return pl.from_pandas(result.to_pandas())


def _check_all_fks(
    specs: dict[str, Any],
    cache: dict[str, Any],
    *,
    fast: bool = False,
) -> list[FKViolation]:
    """Check FK referential integrity using cached materialized tables."""
    from mountainash.typespec.spec import TypeSpec

    fk_violations: list[FKViolation] = []

    for child_name, spec in specs.items():
        if not isinstance(spec, TypeSpec) or spec.foreign_keys is None:
            continue
        if child_name not in cache:
            continue

        child_df = cache[child_name]

        for fk in spec.foreign_keys:
            parent_name = fk.reference.resource
            if parent_name not in cache:
                continue

            parent_df = cache[parent_name]
            violation = check_fk_integrity(
                child_df=child_df,
                parent_df=parent_df,
                child_table=child_name,
                parent_table=parent_name,
                child_fields=fk.fields,
                parent_fields=fk.reference.fields,
            )
            if violation is not None:
                fk_violations.append(violation)
                if fast:
                    return fk_violations

    return fk_violations


def check_fk_integrity(
    *,
    child_df: pl.DataFrame,
    parent_df: pl.DataFrame,
    child_table: str,
    parent_table: str,
    child_fields: list[str],
    parent_fields: list[str],
) -> FKViolation | None:
    """Check FK referential integrity between two Polars DataFrames.

    Rows where any child FK column is null are excluded (optional relationships).
    Returns an FKViolation if orphaned rows exist, else None.
    """
    non_null_children = child_df.drop_nulls(subset=child_fields)
    if len(non_null_children) == 0:
        return None

    orphans = non_null_children.join(
        parent_df.select(parent_fields).unique(),
        left_on=child_fields,
        right_on=parent_fields,
        how="anti",
    )

    if len(orphans) == 0:
        return None

    return FKViolation(
        child_table=child_table,
        parent_table=parent_table,
        child_fields=child_fields,
        parent_fields=parent_fields,
        orphan_count=len(orphans),
        orphan_sample=orphans.head(FK_SAMPLE_SIZE),
    )
