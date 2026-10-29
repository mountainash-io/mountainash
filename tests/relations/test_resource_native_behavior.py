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

def test_schema_inspection_does_not_consume_generator_column():
    import mountainash as ma
    from mountainash.relations.core.errors import IncompleteSchemaError

    iterations = 0

    def values():
        nonlocal iterations
        iterations += 1
        yield 1
        yield 2

    relation = ma.relation({"x": values()})

    relation.schema
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()

    assert iterations == 0




@pytest.mark.parametrize("multiple", [False, True])
def test_declared_python_source_supports_computed_metadata_without_reading_values(multiple):
    from dataclasses import dataclass
    import mountainash as ma
    from mountainash.core.dtypes import MountainashDtype as D

    reads = []

    @dataclass
    class Row:
        n: int

        def __getattribute__(self, name):
            if name == "n":
                reads.append(name)
            return object.__getattribute__(self, name)

    source = [Row(7), Row(8)] if multiple else Row(7)
    relation = ma.relation(source).select((ma.col("n") + 1).alias("next"))
    assert relation.collect_schema() == {"next": D.I64}
    assert reads == []
    assert relation.to_dict() == {"next": [8, 9] if multiple else [8]}
    assert reads


def test_numpy_column_literal_retains_available_native_dtype():
    import numpy as np
    import mountainash as ma
    from mountainash.core.dtypes import MountainashDtype as D

    relation = ma.relation({"n": np.array([2, 7], dtype=np.int64)}).select(
        (ma.col("n") + 1).alias("next")
    )
    assert relation.collect_schema() == {"next": D.I64}
    assert relation.to_dict() == {"next": [3, 8]}
