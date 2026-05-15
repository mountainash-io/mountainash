from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class DateRangeCapability:
    column: str
    granularity: str = "day"
    supports_open_start: bool = True
    supports_open_end: bool = True
    timezone: str = "UTC"


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
    date_range: DateRangeCapability | None = None
    limit: LimitCapability | None = None
    field_selection: FieldSelectionCapability | None = None
    pagination: PaginationCapability | None = None


@dataclass(frozen=True)
class PaginationHint:
    stop_after_records: int | None = None
    stop_after_date: date | datetime | None = None


@dataclass(frozen=True)
class PushedPredicates:
    date_start: date | datetime | None = None
    date_end: date | datetime | None = None
    limit: int | None = None
    selected_fields: list[str] | None = None
    pagination_hint: PaginationHint | None = None


@dataclass(frozen=True)
class ResolvedPredicates:
    date_start: date | datetime | None = None
    date_end: date | datetime | None = None
    limit: int | None = None
    selected_fields: list[str] | None = None
    pagination_hint: PaginationHint | None = None
    resolution_timestamp: datetime = field(default_factory=datetime.now)
