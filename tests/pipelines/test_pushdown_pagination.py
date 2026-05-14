from datetime import date
from mountainash.pipelines.core.capabilities import PaginationHint, PushedPredicates
from mountainash.pipelines.integration.pushdown import synthesise_pagination_hint


def test_pagination_hint_from_date_end():
    pp = PushedPredicates(date_end=date(2026, 4, 1))
    hint = synthesise_pagination_hint(pp)
    assert hint is not None
    assert hint.stop_after_date == date(2026, 4, 1)
    assert hint.stop_after_records is None


def test_pagination_hint_from_limit():
    pp = PushedPredicates(limit=50)
    hint = synthesise_pagination_hint(pp)
    assert hint is not None
    assert hint.stop_after_records == 50


def test_pagination_hint_from_both():
    pp = PushedPredicates(date_end=date(2026, 4, 1), limit=50)
    hint = synthesise_pagination_hint(pp)
    assert hint.stop_after_date == date(2026, 4, 1)
    assert hint.stop_after_records == 50


def test_no_pagination_hint_when_no_predicates():
    pp = PushedPredicates()
    hint = synthesise_pagination_hint(pp)
    assert hint is None
