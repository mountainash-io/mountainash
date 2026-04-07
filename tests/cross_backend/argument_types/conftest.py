"""Shared fixtures for argument/option channel tests."""
from __future__ import annotations

from typing import Any

import pytest

ALL_BACKENDS = ["polars", "ibis", "narwhals-polars", "narwhals-pandas"]


def make_df(data: dict[str, list[Any]], backend: str):
    """Materialize a dict of columns into a backend-native DataFrame."""
    import polars as pl
    pdf = pl.DataFrame(data)
    if backend == "polars":
        return pdf
    if backend == "ibis":
        import ibis
        return ibis.memtable(pdf.to_pandas())
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
