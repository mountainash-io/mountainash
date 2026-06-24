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


def _build_ibis_sqlite(data: DataDict, table_name: str):
    conn = ibis.sqlite.connect(":memory:")
    return conn.create_table(table_name, data, overwrite=True)


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


# Single chokepoint: every cross-backend test parametrises over ALL_BACKENDS,
# so filtering here scopes the whole matrix with no per-file edits.
ALL_BACKENDS: list[str] = resolve_backend_scope(os.environ.get("MA_BACKEND_SCOPE", "full"))
