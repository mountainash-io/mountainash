"""Shared fixtures for argument/option channel tests."""
from __future__ import annotations

from typing import Any

import pytest

from mountainash.core.capabilities.identity import BackendIdentity
from mountainash.core.constants import CONST_BACKEND

ALL_BACKENDS = ["polars", "ibis", "narwhals-polars", "narwhals-pandas"]

MATRIX_IDENTITIES: dict[str, BackendIdentity] = {
    "polars": BackendIdentity(CONST_BACKEND.POLARS, "polars"),
    "ibis": BackendIdentity(CONST_BACKEND.IBIS, "ibis-duckdb"),
    "narwhals-polars": BackendIdentity(CONST_BACKEND.NARWHALS, "narwhals-polars"),
    "narwhals-pandas": BackendIdentity(CONST_BACKEND.NARWHALS, "narwhals-pandas"),
}


def matrix_identity(backend: str) -> BackendIdentity:
    """The authoritative (family, dialect) for an argument-matrix fixture name.

    Conformance-tested against real backend objects in
    test_capability_matrix_expectations.py — keep in sync with make_df().
    """
    return MATRIX_IDENTITIES[backend]


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.argument_types)


def make_df(
    data: dict[str, list[Any]],
    backend: str,
    schema: dict[str, Any] | None = None,
):
    """Materialize a dict of columns into a backend-native DataFrame."""
    import polars as pl
    pdf = pl.DataFrame(data, schema=schema)
    if backend == "polars":
        return pdf
    if backend == "ibis":
        import ibis
        connection = ibis.duckdb.connect()
        return connection.create_table("option_test", pdf, overwrite=True)
    if backend == "ibis-polars":
        import ibis
        connection = ibis.polars.connect()
        return connection.create_table("option_test", pdf, overwrite=True)
    if backend == "narwhals-polars":
        import narwhals as nw
        return nw.from_native(pdf, eager_only=True)
    if backend == "narwhals-pandas":
        import narwhals as nw
        return nw.from_native(pdf.to_pandas(), eager_only=True)
    raise ValueError(f"Unknown backend: {backend}")


@pytest.fixture(params=ALL_BACKENDS)
def backend(request) -> str:
    return request.param
