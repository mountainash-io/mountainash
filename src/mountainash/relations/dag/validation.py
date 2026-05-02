"""DAG validation types and FK referential integrity checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

    from mountainash.datacontracts.result import ValidationResult


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
