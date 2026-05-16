from datetime import date
from mountainash.pipelines.core.capabilities import (
    PaginationHint,
    PushableParam,
    PushedParam,
    PushedPredicates,
)
from mountainash.pipelines.integration.pushdown import synthesise_pagination_hint


PUSHABLE_WITH_STOP = (
    PushableParam(column="date", api_param="end", operators=("lt", "lte"), pagination_stop=True),
)

PUSHABLE_WITHOUT_STOP = (
    PushableParam(column="date", api_param="end", operators=("lt", "lte"), pagination_stop=False),
)


def test_pagination_hint_from_stop_date():
    pp = PushedPredicates(
        params={"end": PushedParam(value=date(2026, 4, 1), operator="lt")},
    )
    hint = synthesise_pagination_hint(pp, PUSHABLE_WITH_STOP)
    assert hint is not None
    assert hint.stop_after_date == date(2026, 4, 1)
    assert hint.stop_after_records is None


def test_pagination_hint_from_limit():
    pp = PushedPredicates(limit=50)
    hint = synthesise_pagination_hint(pp, ())
    assert hint is not None
    assert hint.stop_after_records == 50


def test_pagination_hint_from_both():
    pp = PushedPredicates(
        params={"end": PushedParam(value=date(2026, 4, 1), operator="lte")},
        limit=50,
    )
    hint = synthesise_pagination_hint(pp, PUSHABLE_WITH_STOP)
    assert hint.stop_after_date == date(2026, 4, 1)
    assert hint.stop_after_records == 50


def test_no_pagination_hint_when_no_predicates():
    pp = PushedPredicates()
    hint = synthesise_pagination_hint(pp, ())
    assert hint is None


def test_no_pagination_hint_without_pagination_stop_flag():
    pp = PushedPredicates(
        params={"end": PushedParam(value=date(2026, 4, 1), operator="lt")},
    )
    hint = synthesise_pagination_hint(pp, PUSHABLE_WITHOUT_STOP)
    assert hint is None
