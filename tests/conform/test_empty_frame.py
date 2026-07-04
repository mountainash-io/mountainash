"""Backend empty_frame(spec) builds a typed-empty frame from a TypeSpec."""
from __future__ import annotations

import polars as pl

from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
    MountainashPolarsExtensionRelationSystem,
)

SPEC = TypeSpec(
    fields=[
        FieldSpec(name="date", type=UniversalType.STRING),
        FieldSpec(name="v", type=UniversalType.INTEGER),
    ],
    primary_key=["date", "v"],
    fields_match="open",
)


def test_polars_empty_frame_typed():
    lf = MountainashPolarsExtensionRelationSystem().empty_frame(SPEC)
    df = lf.collect()
    assert df.shape == (0, 2)
    assert df.columns == ["date", "v"]
    assert df.dtypes == [pl.String, pl.Int64]


def test_ibis_empty_frame_typed():
    import ibis
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )

    t = MountainashIbisExtensionRelationSystem().empty_frame(SPEC)
    df = t.execute()
    assert list(df.columns) == ["date", "v"]
    assert len(df) == 0
    # dtype parity: string-ish and integer-ish (exact ibis/pandas dtype tolerated)
    schema = t.schema()
    assert schema["date"].is_string()
    assert schema["v"].is_integer()


def test_narwhals_empty_frame_typed():
    import narwhals as nw
    from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
        MountainashNarwhalsExtensionRelationSystem,
    )

    lazy = MountainashNarwhalsExtensionRelationSystem().empty_frame(SPEC)
    assert isinstance(lazy, nw.LazyFrame)
    frame = lazy.collect()
    assert list(frame.columns) == ["date", "v"]
    assert frame.shape == (0, 2)
    assert frame.schema["date"] == nw.String
    assert frame.schema["v"] == nw.Int64
