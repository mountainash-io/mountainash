from datetime import date, datetime

from mountainash.pipelines.core.capabilities import (
    FieldSelectionCapability,
    LimitCapability,
    PaginationCapability,
    PaginationHint,
    PushableParam,
    PushedParam,
    PushedPredicates,
    ResolvedPredicates,
    StepCapabilities,
)


def test_step_capabilities_defaults():
    caps = StepCapabilities()
    assert caps.pushable_params == ()
    assert caps.limit is None
    assert caps.field_selection is None
    assert caps.pagination is None


def test_pushable_param():
    p = PushableParam(column="date", api_param="start", operators=("gt", "gte"), format="iso_datetime")
    assert p.column == "date"
    assert p.api_param == "start"
    assert p.operators == ("gt", "gte")
    assert p.format == "iso_datetime"
    assert p.pagination_stop is False


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
    assert pp.params == {}
    assert pp.limit is None
    assert pp.selected_fields is None
    assert pp.pagination_hint is None


def test_pushed_predicates_with_values():
    pp = PushedPredicates(
        params={
            "start": PushedParam(value=date(2026, 1, 1), operator="gte", format="iso_datetime"),
            "end": PushedParam(value=date(2026, 4, 1), operator="lte", format="iso_datetime_eod"),
        },
        limit=50,
        selected_fields=["id", "date", "value"],
        pagination_hint=PaginationHint(stop_after_records=50, stop_after_date=date(2026, 4, 1)),
    )
    assert pp.params["start"].value == date(2026, 1, 1)
    assert pp.pagination_hint.stop_after_records == 50


def test_resolved_predicates():
    rp = ResolvedPredicates(
        params={"start": PushedParam(value=date(2026, 1, 1), operator="gte")},
        resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0),
    )
    assert rp.params["start"].value == date(2026, 1, 1)
    assert rp.resolution_timestamp.year == 2026


def test_capabilities_are_frozen():
    p = PushableParam(column="date", api_param="start")
    try:
        p.column = "other"
        assert False, "Should raise"
    except AttributeError:
        pass
