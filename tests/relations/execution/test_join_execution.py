"""Public execution placement regressions."""

import pytest
import mountainash as ma

from fixtures.backend_registry import REGISTRY


IBIS = [name for name, spec in REGISTRY.items() if spec.family == "ibis"]


@pytest.mark.parametrize("backend_name", list(REGISTRY))
@pytest.mark.parametrize("target", [None, "left", "right"])
def test_left_join_preserves_logical_rows(backend_name, backend_factory, target):
    left, right = backend_factory.create_pair(
        {"id": [1, 2], "a": [10, 20]}, {"id": [2, 3], "b": [200, 300]}, backend_name,
    )
    rel = ma.relation(left).join(right, on="id", how="left", execute_on=target)
    assert rel.sort("id").to_dicts() == [
        {"id": 1, "a": 10, "b": None}, {"id": 2, "a": 20, "b": 200},
    ]


@pytest.mark.parametrize("source_name", IBIS)
@pytest.mark.parametrize("target_name", IBIS)
def test_right_target_uses_exact_connection(source_name, target_name):
    left = REGISTRY[source_name].build({"id": [1, 2], "a": [10, 20]}, "same")
    right = REGISTRY[target_name].build({"id": [2, 3], "b": [200, 300]}, "same")
    rel = ma.relation(left).join(right, on="id", how="left", execute_on="right")
    native = rel.collect()
    assert native._find_backend(use_default=False) is right._find_backend(use_default=False)
    assert rel.sort("id").to_dicts() == [
        {"id": 1, "a": 10, "b": None}, {"id": 2, "a": 20, "b": 200},
    ]


def test_nested_right_then_left_target_with_parent_filter():
    a = REGISTRY["ibis-duckdb"].build({"id": [1, 2]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    c = REGISTRY["ibis-polars"].build({"id": [2]}, "c")
    rel = ma.relation(a).join(b, on="id", execute_on="right").join(
        c, on="id", execute_on="left",
    ).filter(ma.col("id") > 1)
    native = rel.collect()
    assert native._find_backend(use_default=False) is b._find_backend(use_default=False)
    assert rel.to_dict() == {"id": [2]}


@pytest.mark.parametrize("source_name", IBIS)
@pytest.mark.parametrize("target_name", ["polars", "narwhals-pandas", "narwhals-polars"])
def test_right_eager_target_consumes_ibis_source(source_name, target_name):
    left = REGISTRY[source_name].build({"id": [1, 2], "a": [10, 20]}, "left")
    right = REGISTRY[target_name].build({"id": [2, 3], "b": [200, 300]}, "right")
    rel = ma.relation(left).join(right, on="id", how="left", execute_on="right")
    assert rel.sort("id").to_dicts() == [
        {"id": 1, "a": 10, "b": None}, {"id": 2, "a": 20, "b": 200},
    ]


@pytest.mark.parametrize("source_name", ["polars", "narwhals-pandas", "narwhals-polars"])
@pytest.mark.parametrize("target_name", IBIS)
def test_right_ibis_target_consumes_eager_source(source_name, target_name):
    left = REGISTRY[source_name].build({"id": [1, 2], "a": [10, 20]}, "left")
    right = REGISTRY[target_name].build({"id": [2, 3], "b": [200, 300]}, "right")
    rel = ma.relation(left).join(right, on="id", how="left", execute_on="right")
    result = rel.collect()
    assert result._find_backend(use_default=False) is right._find_backend(use_default=False)
    assert rel.sort("id").to_dicts() == [
        {"id": 1, "a": 10, "b": None}, {"id": 2, "a": 20, "b": 200},
    ]


def test_matching_override_keeps_selected_connection_and_polars_is_only_egress():
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [1]}, "b")
    rel = ma.relation(a).join(b, on="id", execute_on="right")
    native = rel.collect(backend="ibis")
    assert native._find_backend(use_default=False) is b._find_backend(use_default=False)
    assert rel.to_polars().to_dict(as_series=False) == {"id": [1]}


def test_cross_connection_native_result_survives_scope_exit():
    import gc

    a = REGISTRY["ibis-duckdb"].build({"id": [1, 2]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    result = ma.relation(a).join(b, on="id", execute_on="right").collect()
    gc.collect()
    assert ma.relation(result).to_dict() == {"id": [2]}
