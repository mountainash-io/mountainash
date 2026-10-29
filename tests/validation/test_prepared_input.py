"""Structural behavior tests for standalone validation-source preparation
(Task 6, spec section 6). The user-confirmed semantic failures (Ibis null
outcomes going through a pandas round-trip) are covered by
``tests/validation/cross_backend/test_runner_semantics.py`` and are not
rerun here solely to reconfirm them.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
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


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-sqlite"])
def test_prepare_validation_input_uses_one_native_ibis_cache(
    backend_name, backend_factory, mocker
):
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    from mountainash.relations.core import owned_copy

    copies = mocker.spy(owned_copy, "owned_ibis_table")
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(
            ma.relation(table), scope=scope,
            execution_context=_new_execution_context(table, policy=CapabilityPolicy.trusted()),
        )
        assert prepared.native.value_identity.dialect == backend_name
        assert copies.call_count == 1


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-sqlite"])
def test_prepare_validation_input_snapshot_uses_one_arrow_extraction(
    backend_name, backend_factory, mocker
):
    """Spec Task 6 step 1: one cache(), one Arrow extraction for the shared
    physical snapshot -- never a per-check re-execution."""
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    exports = mocker.spy(type(table), "to_pyarrow")
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(
            ma.relation(table), scope=scope,
            execution_context=_new_execution_context(table, policy=CapabilityPolicy.trusted()),
        )
        assert exports.call_count == 1
        assert prepared.snapshot.columns["age"].to_pylist() == [30, -1, None]
        assert prepared.logical_snapshot.logical_columns["age"] is prepared.snapshot.columns["age"]



def test_prepared_identity_mismatch_raises_backend_conversion_error():
    import pandas as pd

    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
    from mountainash.core.constants import CONST_BACKEND

    identity = BackendIdentity(CONST_BACKEND.IBIS, "ibis-duckdb")
    context = _new_execution_context(
        None, family_override=CONST_BACKEND.IBIS, policy=CapabilityPolicy.trusted(),
    )
    native = NativeExecutionValue(
        value=object(),
        compiler_identity=identity,
        value_identity=identity,
        form=ExecutionForm.DEFERRED,
        target=context.target,
    )
    with pytest.raises(BackendConversionError):
        assert_prepared_identity(native, pd.DataFrame({"x": [1]}))


def test_prepared_identity_match_is_silent():
    import polars as pl

    df = pl.DataFrame({"x": [1, 2]})
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(
            ma.relation(df), scope=scope,
            execution_context=_new_execution_context(df, policy=CapabilityPolicy.trusted()),
        )
        assert_prepared_identity(prepared.native, prepared.native.value)


def test_prepare_validation_input_returns_frozen_dataclass_shape():
    import polars as pl

    df = pl.DataFrame({"x": [1]})
    with MaterializationScope() as scope:
        prepared = prepare_validation_input(
            ma.relation(df), scope=scope,
            execution_context=_new_execution_context(df, policy=CapabilityPolicy.trusted()),
        )
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
        prepared = prepare_validation_input(
            ma.relation(df), scope=scope,
            execution_context=_new_execution_context(df, policy=CapabilityPolicy.trusted()),
        )
        assert prepared.relation.to_polars().to_dict(as_series=False) == {"x": [1, 2, 3]}
