"""Native scalar terminals and schema inspection across supported representations."""
from __future__ import annotations

import narwhals as nw
import pandas as pd
import polars as pl
import pytest

from mountainash.typespec.source_shape import extract_source_shapes


def test_ibis_fetch_from_end_preserves_rows():
    import ibis
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )

    con = ibis.duckdb.connect()
    try:
        table = con.create_table("t", {"x": list(range(10))}, overwrite=True)
        result = MountainashIbisExtensionRelationSystem().fetch_from_end(table, 3)
        assert result.count().execute() == 3
        assert result.to_pyarrow()["x"].to_pylist() == [7, 8, 9]
    finally:
        con.disconnect()


@pytest.mark.parametrize("constructor", [pl.DataFrame, pd.DataFrame], ids=["polars", "pandas"])
def test_narwhals_schema_preserves_column_names(constructor):
    frame = nw.from_native(constructor({"a": [1], "b": ["x"]}))
    shapes = extract_source_shapes(frame)
    assert set(shapes) == {"a", "b"}
