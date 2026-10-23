"""Backend empty_frame(spec) builds a typed-empty frame from a TypeSpec."""
from __future__ import annotations

import polars as pl

from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
    MountainashPolarsExtensionRelationSystem,
)

SPEC = TableSchema(
    fields={"list": FieldDefinition(type = UniversalType.LIST, item_type="integer"),
        "point": FieldDefinition(type = UniversalType.GEOPOINT, format="array"),
        "geometry": FieldDefinition(type = UniversalType.GEOJSON),
        "duration": FieldDefinition(type = UniversalType.DURATION),
        "year": FieldDefinition(type = UniversalType.YEAR),
        "yearmonth": FieldDefinition(type = UniversalType.YEARMONTH),}
)


def test_polars_empty_frame_typed():
    lf = MountainashPolarsExtensionRelationSystem().empty_frame(SPEC)
    df = lf.collect()
    assert df.shape == (0, 6)
    assert df.columns == ["list", "point", "geometry", "duration", "year", "yearmonth"]
    assert df.schema["list"] == pl.List(pl.Int64)
    assert df.schema["point"].base_type() is pl.List
    for name in ("geometry", "duration", "year", "yearmonth"):
        assert df.schema[name] == pl.String

def test_ibis_empty_frame_typed():
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )

    t = MountainashIbisExtensionRelationSystem().empty_frame(SPEC)
    df = t.execute()
    assert list(df.columns) == ["list", "point", "geometry", "duration", "year", "yearmonth"]
    assert len(df) == 0
    schema = t.schema()
    assert schema["list"].is_array()
    assert schema["point"].is_array()
    for name in ("geometry", "duration", "year", "yearmonth"):
        assert schema[name].is_string()

def test_narwhals_empty_frame_typed():
    import narwhals as nw
    from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
        MountainashNarwhalsExtensionRelationSystem,
    )

    lazy = MountainashNarwhalsExtensionRelationSystem().empty_frame(SPEC)
    assert isinstance(lazy, nw.LazyFrame)
    frame = lazy.collect()
    assert list(frame.columns) == ["list", "point", "geometry", "duration", "year", "yearmonth"]
    assert frame.shape == (0, 6)
    assert frame.schema["list"] == nw.List(nw.Int64)
    assert frame.schema["point"] == nw.List
    for name in ("geometry", "duration", "year", "yearmonth"):
        assert frame.schema[name] == nw.String
