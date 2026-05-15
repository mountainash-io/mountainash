from datetime import date, datetime

from mountainash.pipelines.core.capabilities import (
    DateRangeCapability,
    FieldSelectionCapability,
    LimitCapability,
    PaginationCapability,
    PaginationHint,
    PushedPredicates,
    ResolvedPredicates,
    StepCapabilities,
)


def test_step_capabilities_defaults():
    caps = StepCapabilities()
    assert caps.date_range is None
    assert caps.limit is None
    assert caps.field_selection is None
    assert caps.pagination is None


def test_date_range_capability():
    cap = DateRangeCapability(column="date")
    assert cap.column == "date"
    assert cap.granularity == "day"
    assert cap.supports_open_start is True
    assert cap.supports_open_end is True
    assert cap.timezone == "UTC"


def test_limit_capability_with_sort():
    cap = LimitCapability(
        max_limit=100,
        supported_sort_columns=["date", "created_at"],
        supported_sort_directions=["asc", "desc"],
    )
    assert cap.max_limit == 100
    assert "date" in cap.supported_sort_columns


def test_field_selection_capability():
    cap = FieldSelectionCapability(
        available_fields=["id", "name", "date"],
        always_included=["id"],
    )
    assert len(cap.available_fields) == 3
    assert cap.always_included == ["id"]


def test_pagination_capability():
    cap = PaginationCapability(strategy="cursor", max_page_size=200, supports_early_termination=True)
    assert cap.strategy == "cursor"


def test_pushed_predicates_defaults():
    pp = PushedPredicates()
    assert pp.date_start is None
    assert pp.date_end is None
    assert pp.limit is None
    assert pp.selected_fields is None
    assert pp.pagination_hint is None


def test_pushed_predicates_with_values():
    pp = PushedPredicates(
        date_start=date(2026, 1, 1),
        date_end=date(2026, 4, 1),
        limit=50,
        selected_fields=["id", "date", "value"],
        pagination_hint=PaginationHint(stop_after_records=50, stop_after_date=date(2026, 4, 1)),
    )
    assert pp.date_start == date(2026, 1, 1)
    assert pp.pagination_hint.stop_after_records == 50


def test_resolved_predicates():
    rp = ResolvedPredicates(
        date_start=date(2026, 1, 1),
        resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0),
    )
    assert rp.date_start == date(2026, 1, 1)
    assert rp.resolution_timestamp.year == 2026


def test_capabilities_are_frozen():
    cap = DateRangeCapability(column="date")
    try:
        cap.column = "other"
        assert False, "Should raise"
    except AttributeError:
        pass
