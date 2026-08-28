"""Structural behavior tests for standalone validation-source preparation
(Task 6, spec section 6). The user-confirmed semantic failures (Ibis null
outcomes going through a pandas round-trip) are covered by
``tests/validation/cross_backend/test_runner_semantics.py`` and are not
rerun here solely to reconfirm them.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.errors import BackendConversionError
from mountainash.relations.core.materialization import (
    ExecutionForm,
    MaterializationScope,
    NativeExecutionValue,
)
from mountainash.validation.prepared import (
    PreparedValidationInput,
    assert_prepared_identity,
    prepare_validation_input,
)

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_prepare_validation_input_uses_one_native_ibis_cache(
    backend_name, backend_factory, monkeypatch
):
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    cache_calls = 0
    original = type(table).cache

    def counted_cache(self):
        nonlocal cache_calls
        cache_calls += 1
        return original(self)

    monkeypatch.setattr(type(table), "cache", counted_cache)
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(ma.relation(table), scope=scope)
        assert prepared.native.value_identity.dialect == backend_name
        assert cache_calls == 1


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_prepare_validation_input_snapshot_uses_one_arrow_extraction(
    backend_name, backend_factory, monkeypatch
):
    """Spec Task 6 step 1: one cache(), one Arrow extraction for the shared
    physical snapshot -- never a per-check re-execution."""
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    to_pyarrow_calls = 0
    original_to_pyarrow = None

    original_cache = type(table).cache

    def spy_cache(self):
        cached = original_cache(self)
        nonlocal original_to_pyarrow
        original_to_pyarrow = type(cached).to_pyarrow

        def spy_to_pyarrow(inner_self, *a, **kw):
            nonlocal to_pyarrow_calls
            to_pyarrow_calls += 1
            return original_to_pyarrow(inner_self, *a, **kw)

        monkeypatch.setattr(type(cached), "to_pyarrow", spy_to_pyarrow)
        return cached

    monkeypatch.setattr(type(table), "cache", spy_cache)
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(ma.relation(table), scope=scope)
        assert to_pyarrow_calls == 1
        assert prepared.snapshot.columns["age"].to_pylist() == [30, -1, None]
        assert prepared.logical_snapshot.logical_columns["age"] is prepared.snapshot.columns["age"]



def test_prepared_identity_mismatch_raises_backend_conversion_error():
    import pandas as pd

    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.core.constants import CONST_BACKEND

    identity = BackendIdentity(CONST_BACKEND.IBIS, "ibis-duckdb")
    native = NativeExecutionValue(
        value=object(),
        compiler_identity=identity,
        value_identity=identity,
        form=ExecutionForm.DEFERRED,
    )
    with pytest.raises(BackendConversionError):
        assert_prepared_identity(native, pd.DataFrame({"x": [1]}))


def test_prepared_identity_match_is_silent():
    import polars as pl

    df = pl.DataFrame({"x": [1, 2]})
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(ma.relation(df), scope=scope)
        assert_prepared_identity(prepared.native, prepared.native.value)


def test_prepare_validation_input_returns_frozen_dataclass_shape():
    import polars as pl

    df = pl.DataFrame({"x": [1]})
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(ma.relation(df), scope=scope)
        assert isinstance(prepared, PreparedValidationInput)
        assert prepared.snapshot.columns["x"].to_list() == [1]
        assert prepared.logical_snapshot.logical_columns["x"] is prepared.snapshot.columns["x"]
        assert prepared.structured_field_plans == {}
        with pytest.raises(Exception, match="frozen|cannot assign"):
            prepared.native = None  # type: ignore[misc]


def test_prepared_relation_collects_same_rows():
    import polars as pl

    df = pl.DataFrame({"x": [1, 2, 3]})
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(ma.relation(df), scope=scope)
        assert prepared.relation.to_polars().to_dict(as_series=False) == {"x": [1, 2, 3]}
