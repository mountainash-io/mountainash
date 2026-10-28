# tests/pipelines/core/test_values.py
import pytest, pyarrow as pa, polars as pl
from mountainash.pipelines.core.values import (Coverage, Identity, SourceState, Value, ValueKind, SourceResult, Attempt, Record, Status)
from mountainash.pipelines.errors import UnhashableIdentityInput


@pytest.mark.parametrize("payload,kind", [
    ([{"a": 1}, {"a": 2}], ValueKind.RECORDS), ({"a": [1, 2]}, ValueKind.RECORDS), ({}, ValueKind.RECORDS),
    (pa.table({"a": [1]}), ValueKind.TABULAR), ("polars", ValueKind.OPAQUE), (object(), ValueKind.OPAQUE),
])
def test_value_of_kinds(payload, kind):
    assert Value.of(payload, Identity.of("x")).kind is kind


def test_value_of_backend_frames_detect_location(backend_name, backend_df):
    v = Value.of(backend_df, Identity.of("x"))
    assert v.kind is ValueKind.TABULAR and v.location is not None and v.location.family is not None
    assert v.record_count() == 5          # sample_data has 5 rows


def test_record_count_rules():
    assert Value.of({"a": [], "b": []}, Identity.of("x")).record_count() == 0
    assert Value.of({"a": [1, 2]}, Identity.of("x")).record_count() == 2
    assert Value.of(object(), Identity.of("x")).record_count() is None
    lf = pl.DataFrame({"a": [1, 2, 3]}).lazy()
    assert Value.of(lf, Identity.of("x")).record_count() == 3


def test_identity_stable_and_refuses_unserialisable():
    a = Identity.of("k", "1", {"p": 1}, {"up": Identity.of("u")})
    assert a == Identity.of("k", "1", {"p": 1}, {"up": Identity.of("u")})
    assert a != Identity.of("k", "2", {"p": 1}, {"up": Identity.of("u")})
    with pytest.raises(UnhashableIdentityInput):
        Identity.of(object())


def test_source_state_advance_table():
    s = SourceState(None, frozenset(), frozenset())
    partial = s.advance(Coverage.source({"A", "B"}, {"B"}, {"A"}), next_cursor="B")
    assert partial == SourceState(None, frozenset({"A"}), frozenset({"B"}))
    done = partial.advance(Coverage.source({"A", "C"}, {"A", "C"}, set()), next_cursor="C")
    assert done == SourceState("C", frozenset(), frozenset())


def test_identity_distinguishes_mapping_from_pairs_and_is_restart_stable():
    assert Identity.of({"p": {"a": 1}}) != Identity.of({"p": (("a", 1),)})            # F5 collision
    assert Identity.of(frozenset({1, "A"})) == Identity.of(frozenset({"A", 1}))        # heterogeneous set, no ordering
    import datetime, decimal
    assert Identity.of(datetime.date(2026, 1, 1), decimal.Decimal("1.10")).digest == "a3c18432aad55f8f04aae2a3c758abd5"  # restart-stability pin


def test_value_of_narwhals_pandas_named_index_is_tabular():      # Review Focus #1
    import narwhals as nw, pandas as pd
    df = pd.DataFrame({"a": [1, 2]}, index=pd.Index(["x", "y"], name="k"))
    v = Value.of(nw.from_native(df), Identity.of("x"))
    assert v.kind is ValueKind.TABULAR and v.record_count() == 2 and v.location.dialect == "narwhals-pandas"


def test_coverage_partial_marker_is_incomplete():
    m = Coverage.partial_marker()
    assert not m.complete and not m.failed
    assert Coverage.source({"A"}, {"A"}, set()).complete


def test_attempt_replace_and_commit():
    st = SourceState(None, frozenset(), frozenset())
    v = Value.of([{"p": "A"}], Identity.of("i"), Coverage.source({"A"}, {"A"}, set()))
    att = Attempt(st, Identity.of("i"), Record(Identity.of("i"), Status.COMPLETE, None, v.coverage, v), next_cursor="A")
    assert att.commit() == SourceState("A", frozenset(), frozenset())
    v2 = Value.of([], Identity.of("i"), Coverage.source({"A"}, set(), {"A"}))
    att2 = att.replace(SourceResult(v2, None))
    assert att2.identity == att.identity and att2.record.status is Status.PARTIAL and att2.next_cursor is None
