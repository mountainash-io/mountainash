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
