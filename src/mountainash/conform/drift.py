"""Drift report shapes — the pure data returned by conform contract evaluation.

These are frozen dataclasses only: no evaluation logic lives here. A
`ConformDrift` records, per conform node, what diverged between the
declared `TypeSpec` and the actual observed schema, plus the policy
action that was (or would be) applied for each divergence. A
`ConformCollection` wraps the materialised frame alongside the drift
report(s) collected for the plan.

See: item 17-P8 (compatibility predicate), item 48 (conform contract +
drift evaluator).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class TypeDrift:
    """A single source/type divergence with evaluator evidence."""

    name: str
    declared: Any
    actual: Any
    safety: str
    action: str | None = None
    reason: str = "cast_safety"
    source_detail: str | None = None
    requirement: str | None = None
    applied: bool = True

@dataclass(frozen=True)
class ColumnDrift:
    """A single column present/absent relative to the declared spec.

    Used for both `extra_columns` (present in data, not declared) and
    `missing_columns` (declared, not present in data) — the `action`
    vocabulary differs by which list it appears in:
      - extra:   evolve|freeze|discard
      - missing: skip|freeze|null_fill
    """

    name: str
    action: str


@dataclass(frozen=True)
class KeyDrift:
    """A single foreign-key relationship that diverged from its declaration."""

    kind: str  # fk_field_dropped|dangling_reference|fk_type_mismatch
    fields: list[str]
    reference: Optional[str]
    declared: Optional[Any] = None
    actual: Optional[Any] = None
    action: str = "ignore"


@dataclass(frozen=True)
class ConformDrift:
    """Drift report for a single conform node.

    `key_changes` distinguishes two states that are semantically distinct
    and must not be conflated:
      - `None`: key drift was NOT ASSESSED — no DAG/FK context was
        available when this node was compiled (e.g. a bare `Relation`
        with no owning `RelationDAG`, or a resource with no declared
        foreign keys).
      - `[]`: key drift WAS assessed (DAG/FK context was available) and
        no drift was found — i.e. assessed clean.

    `.compatible` only judges ASSESSED dimensions, so both `None` and
    `[]` are treated as "no key drift" for that predicate — the absence
    of assessment is not itself evidence of incompatibility.
    """

    node_id: str
    resource_name: Optional[str]
    spec_name: Optional[str]
    extra_columns: list[ColumnDrift] = field(default_factory=list)
    missing_columns: list[ColumnDrift] = field(default_factory=list)
    type_mismatches: list[TypeDrift] = field(default_factory=list)
    key_changes: Optional[list[KeyDrift]] = None  # None = NOT ASSESSED; [] = assessed clean

    @property
    def compatible(self) -> bool:
        """True iff every ASSESSED dimension is empty (item 17-P8 predicate)."""
        return not (
            self.extra_columns
            or self.missing_columns
            or self.type_mismatches
            or (self.key_changes or [])
        )


@dataclass(frozen=True)
class ConformCollection:
    """Materialised frame plus the drift report(s) collected for the plan."""

    frame: Any
    drifts: list[ConformDrift]
    effective_schema: dict  # ACTUAL post-policy output schema (canonical space)

    @property
    def drift(self) -> ConformDrift:
        """The single drift report, when the plan has exactly one conform node.

        Raises `ValueError` if the plan has zero or more than one conform
        node — use `.drifts` directly in those cases.
        """
        if len(self.drifts) != 1:
            raise ValueError(
                f"plan has {len(self.drifts)} conform nodes; use .drifts"
            )
        return self.drifts[0]
