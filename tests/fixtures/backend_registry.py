# tests/fixtures/backend_registry.py
"""Centralized backend dispatch for the cross-backend test suite.

Single source of truth — adding a new backend means adding one row to REGISTRY.
The four `backend_*_df` fixtures in tests/conftest.py delegate here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

import os

import ibis
import narwhals as nw
import pandas as pd
import polars as pl


DataDict = dict[str, list[Any]]
Family = Literal["polars-eager", "polars-lazy", "pandas", "narwhals", "ibis"]
Materialization = Literal["eager", "lazy", "deferred"]


@dataclass(frozen=True)
class BackendSpec:
    """Description of one backend variant in the test matrix.

    `build(data, table_name)` returns the backend's native object. Result-helper
    fixtures (get_result, select_and_extract, etc.) branch on `materialization`
    to decide how to unwrap a result.
    """

    name: str
    family: Family
    materialization: Materialization
    build: Callable[[DataDict, str], Any]
    min_versions: dict[str, str] = field(default_factory=dict)
    capabilities: frozenset[str] = field(default_factory=frozenset)
    extra_marks: Callable[[], tuple] | None = None


def _build_polars_eager(data: DataDict, table_name: str) -> pl.DataFrame:
    return pl.DataFrame(data)


def _build_polars_lazy(data: DataDict, table_name: str) -> pl.LazyFrame:
    return pl.DataFrame(data).lazy()


def _build_pandas(data: DataDict, table_name: str) -> pd.DataFrame:
    return pd.DataFrame(data)


def _build_narwhals_polars(data: DataDict, table_name: str):
    return nw.from_native(pl.DataFrame(data))

def _build_narwhals_polars_lazy(data: DataDict, table_name: str):
    return nw.from_native(pl.DataFrame(data).lazy())


def _build_narwhals_pandas(data: DataDict, table_name: str):
    return nw.from_native(pd.DataFrame(data), eager_only=True)


def _build_ibis_polars(data: DataDict, table_name: str):
    conn = ibis.polars.connect()
    return conn.create_table(table_name, pl.DataFrame(data), overwrite=True)


def create_ibis_sqlite_table(conn, name: str, data: DataDict, *, overwrite: bool = True):
    """Create an ibis-sqlite table, safe against null date/timestamp values.

    Single source of truth for every ibis-sqlite table-creation call site in
    the cross-backend test suite (this module, backend_helpers.py, and
    conftest.py's ibis_sqlite_df fixture) -- delegates the NaT-binding
    workaround to mountainash's own production fix (item 112 / IB-DT-19)
    rather than re-registering a second copy of it.
    """
    from mountainash.relations.backends.relation_systems.ibis._sqlite_compat import (
        ensure_sqlite_nat_adapter,
    )
    ensure_sqlite_nat_adapter()
    return conn.create_table(name, data, overwrite=overwrite)


def _build_ibis_sqlite(data: DataDict, table_name: str):
    conn = ibis.sqlite.connect(":memory:")
    return create_ibis_sqlite_table(conn, table_name, data)


def _build_ibis_duckdb(data: DataDict, table_name: str):
    conn = ibis.duckdb.connect()
    return conn.create_table(table_name, data, overwrite=True)


REGISTRY: dict[str, BackendSpec] = {
    "polars":          BackendSpec("polars",          "polars-eager", "eager",    _build_polars_eager),
    "polars-lazy":     BackendSpec("polars-lazy",     "polars-lazy",  "lazy",     _build_polars_lazy),
    "pandas":          BackendSpec("pandas",          "pandas",       "eager",    _build_pandas),
    "narwhals-polars": BackendSpec("narwhals-polars", "narwhals",     "eager",    _build_narwhals_polars),
    "narwhals-pandas": BackendSpec("narwhals-pandas", "narwhals",     "eager",    _build_narwhals_pandas),
    "ibis-duckdb":     BackendSpec("ibis-duckdb",     "ibis",         "deferred", _build_ibis_duckdb),
    "ibis-polars":     BackendSpec("ibis-polars",     "ibis",         "deferred", _build_ibis_polars),
    "ibis-sqlite":     BackendSpec("ibis-sqlite",     "ibis",         "deferred", _build_ibis_sqlite),
    # Legacy alias: "narwhals" resolves to narwhals-polars for pre-existing
    # tests that hardcode this name in their @parametrize lists.
    # "narwhals":        BackendSpec("narwhals",        "narwhals",     "eager",    _build_narwhals_polars),
    "narwhals-lazy":   BackendSpec("narwhals-lazy",   "narwhals",     "lazy",    _build_narwhals_polars_lazy),
}

PR_BACKENDS: list[str] = ["polars", "narwhals-polars", "ibis-duckdb"]


def resolve_backend_scope(scope: str) -> list[str]:
    """Return the backend names active for a scope.

    'pr' → one representative per engine family (fast PR matrix).
    Anything else (incl. 'full' or unset) → the entire registry (fail-safe).
    """
    if scope == "pr":
        return list(PR_BACKENDS)
    return list(REGISTRY)


def active_scope() -> str:
    """The currently-active backend scope (env-driven; CLI mirrors into env)."""
    return os.environ.get("MA_BACKEND_SCOPE", "full")


def deselect_backend_under_scope(backend_name: str | None, scope: str) -> bool:
    """True if a test parametrized with this backend should be DESELECTED.

    Scoping is 'which tests to run', not 'what the registry contains': we keep
    ALL_BACKENDS the full canonical list and instead drop the parametrized cases
    for out-of-scope backends at collection time. Only registered backend names
    are ever deselected — a param value that isn't a backend (or scope != 'pr')
    is always kept (fail-safe: never drop a test we can't positively identify).
    """
    if scope != "pr" or backend_name is None:
        return False
    return backend_name in REGISTRY and backend_name not in PR_BACKENDS


def partition_items_by_scope(items, scope: str):
    """Split collected items into (kept, deselected) for the given scope.

    Reads each item's backend parameter (the cross-backend convention uses
    ``backend_name``; a few use ``backend``). Used by the conftest collection
    hook and mirrored in the pytester attribution test.
    """
    kept, deselected = [], []
    for item in items:
        params = getattr(getattr(item, "callspec", None), "params", {}) or {}
        backend = params.get("backend_name", params.get("backend"))
        (deselected if deselect_backend_under_scope(backend, scope) else kept).append(item)
    return kept, deselected


# ALL_BACKENDS is the full canonical registry list — ALWAYS all 9 backends.
# It is the parametrize source AND what structural tests assert against. Backend
# SCOPING (pr vs full) is applied by DESELECTING out-of-scope parametrized cases
# at collection (see tests/conftest.py::pytest_collection_modifyitems), not by
# shrinking this list.
ALL_BACKENDS: list[str] = list(REGISTRY)
