"""Logical join results must not change when the execution side changes."""

import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL


@pytest.mark.parametrize("backend_name", list(REGISTRY))
@pytest.mark.parametrize("target", [None, "left", "right"])
@pytest.mark.parametrize("how,expected", [
    ("inner", [(2, "b", 200), (2, "c", 200)]),
    ("left", [(1, "a", None), (2, "b", 200), (2, "c", 200)]),
    ("right", [(2, "b", 200), (2, "c", 200), (3, None, 300)]),
    ("outer", [(1, "a", None), (2, "b", 200), (2, "c", 200), (3, None, 300)]),
    ("semi", [(2, "b"), (2, "c")]),
    ("anti", [(1, "a")]),
])
def test_targeted_join_preserves_duplicate_and_unmatched_rows(backend_name, backend_factory, target, how, expected):
    left, right = backend_factory.create_pair(
        {"id": [1, 2, 2], "left_value": ["a", "b", "c"]},
        {"id": [2, 3], "right_value": [200, 300]}, backend_name,
    )
    rows = ma.relation(left).join(right, on="id", how=how, execute_on=target).to_dicts()
    columns = ("id", "left_value") if how in ("semi", "anti") else (
        "id", "left_value", "right_value"
    )
    assert all(set(row) == set(columns) for row in rows)
    assert sorted((tuple(row[col] for col in columns) for row in rows), key=repr) == sorted(expected, key=repr)


@pytest.mark.parametrize("backend_name", list(REGISTRY))
@pytest.mark.parametrize("target", [None, "left", "right"])
def test_cross_join_keeps_six_distinct_pairs(backend_name, backend_factory, target):
    left, right = backend_factory.create_pair(
        {"left_id": [1, 2, 2], "left_value": ["a", "b", "c"]},
        {"right_id": [2, 3], "right_value": [200, 300]}, backend_name,
    )
    rows = ma.relation(left).cross_join(right, execute_on=target).to_dicts()
    assert sorted(((row["left_value"], row["right_value"]) for row in rows)) == [
        ("a", 200), ("a", 300), ("b", 200), ("b", 300), ("c", 200), ("c", 300),
    ]
    assert all(set(row) == {"left_id", "left_value", "right_id", "right_value"} for row in rows)


@pytest.mark.parametrize("backend_name", list(REGISTRY))
@pytest.mark.parametrize("target", [None, "left", "right"])
def test_separate_keys_and_nondefault_suffix(backend_name, backend_factory, target):
    left, right = backend_factory.create_pair(
        {"left_id": [1, 2, 2], "value": ["a", "b", "c"]},
        {"right_id": [2, 3], "value": ["x", "y"]}, backend_name,
    )
    rows = ma.relation(left).join(
        right, left_on="left_id", right_on="right_id", suffix="_lookup", execute_on=target,
    ).to_dicts()
    assert sorted(
        [{name: row[name] for name in ("left_id", "value", "value_lookup")} for row in rows],
        key=lambda r: r["value"],
    ) == [
        {"left_id": 2, "value": "b", "value_lookup": "x"},
        {"left_id": 2, "value": "c", "value_lookup": "x"},
    ]


@pytest.mark.parametrize("backend_name", list(REGISTRY))
@pytest.mark.parametrize("target", [None, "left", "right"])
@pytest.mark.parametrize("strategy,rates", [
    ("backward", [100, None]), ("forward", [None, 700]), ("nearest", [100, 700]),
])
def test_targeted_grouped_asof_with_tolerance(backend_name, backend_factory, target, strategy, rates):
    left, right = backend_factory.create_pair(
        {"t": [2, 6], "g": ["a", "a"], "event": [10, 20]},
        {"t": [1, 4, 7], "g": ["a", "b", "a"], "rate": [100, 999, 700]}, backend_name,
    )
    if backend_name in {"pandas", "narwhals-pandas", "narwhals-polars", "narwhals-lazy"}:
        with pytest.raises(BackendCapabilityError, match="Narwhals join_asof does not expose a tolerance argument") as caught:
            ma.relation(left).join_asof(right, on="t", by="g", strategy=strategy,
                                           tolerance=2, execute_on=target).to_dicts()
        assert caught.value.function_key is RKEY_MOUNTAINASH_REL.JOIN_ASOF
        assert caught.value.backend == "narwhals"
        return
    if backend_name == "ibis-polars" and strategy != "backward":
        with pytest.raises(BackendCapabilityError, match="Ibis Polars cannot compile forward or nearest asof join emulation") as caught:
            ma.relation(left).join_asof(right, on="t", by="g", strategy=strategy,
                                           tolerance=2, execute_on=target).to_dicts()
        assert caught.value.function_key is RKEY_MOUNTAINASH_REL.JOIN_ASOF
        assert caught.value.backend == "ibis"
        return
    rows = ma.relation(left).join_asof(
        right, on="t", by="g", strategy=strategy, tolerance=2, execute_on=target,
    ).sort("event").to_dicts()
    assert rows == [
        {"t": 2, "g": "a", "event": 10, "rate": rates[0]},
        {"t": 6, "g": "a", "event": 20, "rate": rates[1]},
    ]
