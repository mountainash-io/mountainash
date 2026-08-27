"""Native collection, Ibis cache, lifetime, and egress behavior for
`mountainash.relations.core.materialization`.
"""
from __future__ import annotations

import pytest

from mountainash.core.backend_detection import identify_backend_identity
from mountainash.relations.core.materialization import (
    DiagnosticFrameView,
    ExecutionForm,
    MaterializationPurpose,
    MaterializationScope,
    diagnostic_polars_view,
    materialize_native,
)


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_validation_materialization_caches_ibis_without_changing_identity(
    backend_name, backend_factory
):
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    identity = identify_backend_identity(table)
    with MaterializationScope() as scope:
        native = materialize_native(
            table,
            identity,
            MaterializationPurpose.VALIDATION_SOURCE,
            scope=scope,
        )
        assert identify_backend_identity(native.value) == identity
        assert native.form is ExecutionForm.DEFERRED
        assert native.value.to_pyarrow()["age"].to_pylist() == [30, -1, None]


def test_materialization_scope_releases_owned_callbacks_once():
    releases = []
    scope = MaterializationScope()
    scope.own(lambda: releases.append("released"))
    scope.close()
    scope.close()
    assert releases == ["released"]


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_repeated_ibis_cache_lifetime_releases_after_use(backend_name, backend_factory):
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    identity = identify_backend_identity(table)
    for _ in range(5):
        with MaterializationScope() as scope:
            native = materialize_native(
                table,
                identity,
                MaterializationPurpose.VALIDATION_SOURCE,
                scope=scope,
            )
            result = native.value.mutate(ok=native.value.age >= 0)
            assert result.to_pyarrow()["ok"].to_pylist() == [True, False, None]


@pytest.mark.parametrize("backend_name", ["polars", "narwhals"])
def test_ordinary_collect_purpose_returns_eager_native(backend_name, backend_factory):
    df = backend_factory.create({"x": [1, 2, 3]}, backend_name)
    identity = identify_backend_identity(df)
    native = materialize_native(df, identity, MaterializationPurpose.NATIVE_COLLECT)
    assert native.form is ExecutionForm.EAGER
    assert native.compiler_identity == identity


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_ordinary_native_collect_purpose_leaves_ibis_table_uncached(
    backend_name, backend_factory
):
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    identity = identify_backend_identity(table)
    native = materialize_native(table, identity, MaterializationPurpose.NATIVE_COLLECT)
    assert native.value is table
    assert native.form is ExecutionForm.DEFERRED


def test_materialization_scope_rejects_new_ownership_after_close():
    from mountainash.relations.core.errors import MaterializationScopeClosedError

    scope = MaterializationScope()
    scope.close()
    with pytest.raises(MaterializationScopeClosedError):
        scope.own(lambda: None)


def test_diagnostic_polars_view_from_polars_eager_native():
    import polars as pl

    df = pl.DataFrame({"x": [1, 2, 3]})
    identity = identify_backend_identity(df)
    native = materialize_native(df, identity, MaterializationPurpose.DIAGNOSTIC_VIEW)
    view = diagnostic_polars_view(native)
    assert isinstance(view, DiagnosticFrameView)
    assert view.frame.to_dict(as_series=False) == {"x": [1, 2, 3]}


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_diagnostic_polars_view_from_ibis_uses_arrow_not_pandas(
    backend_name, backend_factory, monkeypatch
):
    table = backend_factory.create({"age": [30, -1, None]}, backend_name)
    identity = identify_backend_identity(table)
    native = materialize_native(table, identity, MaterializationPurpose.DIAGNOSTIC_VIEW)

    def _boom(*args, **kwargs):
        raise AssertionError("to_pandas() must not be called for a diagnostic view")

    monkeypatch.setattr(type(native.value), "to_pandas", _boom, raising=False)
    view = diagnostic_polars_view(native)
    assert view.frame["age"].to_list() == [30, -1, None]
