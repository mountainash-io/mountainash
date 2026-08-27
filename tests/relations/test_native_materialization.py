"""Native collection, Ibis cache, lifetime, and egress behavior for
`mountainash.relations.core.materialization`.
"""
from __future__ import annotations

import datetime as _dt

import pytest

import mountainash as ma
from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.types import is_ibis_table
from mountainash.relations.core.materialization import (
    DiagnosticFrameView,
    ExecutionForm,
    MaterializationPurpose,
    MaterializationScope,
    diagnostic_polars_view,
    materialize_native,
)
from mountainash.relations.core.relation_api.relation import Relation


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


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_collect_retains_ibis_table_and_dialect(backend_name, backend_factory):
    table = backend_factory.create({"d": [_dt.date(2024, 1, 2), None]}, backend_name)
    result = ma.relation(table).collect(unwrap=False)
    assert is_ibis_table(result)
    assert identify_backend_identity(result).dialect == backend_name


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_to_pandas_does_not_call_to_polars(backend_name, backend_factory, monkeypatch):
    relation = ma.relation(backend_factory.create({"x": [1, None]}, backend_name))
    monkeypatch.setattr(Relation, "to_polars", lambda self: pytest.fail("Polars transit"))
    result = relation.to_pandas()
    assert result["x"].tolist()[0] == 1


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars"])
def test_ibis_to_polars_egress_never_constructs_pandas(
    backend_name, backend_factory, monkeypatch
):
    """Mountainash's own to_polars() route never constructs pandas.

    ibis-sqlite excluded: ibis's SQLite backend uses pandas as an internal
    implementation detail of its own ``to_pyarrow_batches()``
    (``ibis.formats.pandas.SQLitePandasData.convert_table()``), outside
    Mountainash's call site and outside this policy's control. The dtype
    fidelity that matters -- Arrow preserving `date32` -- is still verified
    for ibis-sqlite by `test_ibis_egress_prefers_arrow_over_pandas`.
    """
    import pandas as pd
    import polars as pl

    table = backend_factory.create({"d": [_dt.date(2024, 1, 2), None]}, backend_name)

    def _tripwire(self, *args, **kwargs):
        pytest.fail("pandas.DataFrame constructed during Ibis-to-Polars egress")

    monkeypatch.setattr(pd.DataFrame, "__init__", _tripwire)
    result = ma.relation(table).to_polars()
    assert isinstance(result, pl.DataFrame)
    assert result["d"].dtype == pl.Date
