from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass(frozen=True)
class ParamSpec:
    """Declares one parameter a pipeline step accepts."""
    name: str
    type: type
    required: bool = True
    default: Any = None


# ---------------------------------------------------------------------------
# Stubs retained for backward compatibility — will be removed in Tasks 2–5
# when step.py, executor.py, integration/, and orchestration/ are migrated.
# ---------------------------------------------------------------------------

Operator = Literal["gt", "gte", "lt", "lte", "eq"]


@dataclass(frozen=True)
class PushableParam:
    column: str
    api_param: str
    operators: tuple[Operator, ...] = ("gt", "gte", "lt", "lte", "eq")
    format: str | None = None
    pagination_stop: bool = False


@dataclass(frozen=True)
class PushedParam:
    value: Any
    operator: Operator
    format: str | None = None


@dataclass(frozen=True)
class LimitCapability:
    max_limit: int | None = None
    supported_sort_columns: list[str] | None = None
    supported_sort_directions: list[str] | None = None


@dataclass(frozen=True)
class FieldSelectionCapability:
    available_fields: list[str] = field(default_factory=list)
    always_included: list[str] | None = None


@dataclass(frozen=True)
class PaginationCapability:
    strategy: str = "cursor"
    max_page_size: int | None = None
    supports_early_termination: bool = True


@dataclass(frozen=True)
class StepCapabilities:
    pushable_params: tuple[PushableParam, ...] = ()
    limit: LimitCapability | None = None
    field_selection: FieldSelectionCapability | None = None
    pagination: PaginationCapability | None = None


@dataclass(frozen=True)
class PaginationHint:
    stop_after_records: int | None = None
    stop_after_date: Any = None


@dataclass(frozen=True)
class PushedPredicates:
    params: dict[str, PushedParam] = field(default_factory=dict)
    limit: int | None = None
    selected_fields: list[str] | None = None
    pagination_hint: PaginationHint | None = None


@dataclass(frozen=True)
class ResolvedPredicates:
    params: dict[str, PushedParam] = field(default_factory=dict)
    limit: int | None = None
    selected_fields: list[str] | None = None
    pagination_hint: PaginationHint | None = None
    resolution_timestamp: datetime = field(default_factory=datetime.now)
