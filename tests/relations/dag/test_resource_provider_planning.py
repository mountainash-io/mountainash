from __future__ import annotations

import polars as pl

from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
    MountainashPolarsExtensionRelationSystem,
)
from mountainash.typespec.datapackage import DataResource
from mountainash_files.provider import FileResourceProvider


def test_explicit_file_provider_reads_arrow_then_adapts_to_polars(tmp_path) -> None:
    path = tmp_path / "orders.csv"
    path.write_text("id\n1\n")
    resource = DataResource(name="orders", path=str(path), format="csv")
    out = MountainashPolarsExtensionRelationSystem().read_resource(
        resource,
        provider_binding=FileResourceProvider.default(),
    )
    assert isinstance(out, pl.LazyFrame)
    assert out.collect().to_dicts() == [{"id": 1}]
