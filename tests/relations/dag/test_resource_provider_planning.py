from __future__ import annotations

import narwhals as nw
import polars as pl

from mountainash.core.transit import BoundaryKey, capture_conversion_trace
from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
    MountainashIbisExtensionRelationSystem,
)
from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
    MountainashNarwhalsExtensionRelationSystem,
)
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


def test_explicit_file_provider_reads_arrow_then_adapts_to_ibis(tmp_path) -> None:
    import ibis.expr.types as ir

    path = tmp_path / "orders.csv"
    path.write_text("id\n1\n")
    resource = DataResource(name="orders", path=str(path), format="csv")
    with capture_conversion_trace() as trace:
        out = MountainashIbisExtensionRelationSystem().read_resource(
            resource,
            provider_binding=FileResourceProvider.default(),
        )
    assert isinstance(out, ir.Table)
    assert out.to_pyarrow().to_pylist() == [{"id": 1}]
    assert [record.boundary_key for record in trace.records] == [
        BoundaryKey.IBIS_CONSTRUCTOR_ADAPTER
    ]


def test_explicit_file_provider_reads_arrow_then_adapts_to_narwhals(tmp_path) -> None:
    path = tmp_path / "orders.csv"
    path.write_text("id\n1\n")
    resource = DataResource(name="orders", path=str(path), format="csv")
    with capture_conversion_trace() as trace:
        out = MountainashNarwhalsExtensionRelationSystem().read_resource(
            resource,
            provider_binding=FileResourceProvider.default(),
        )
    assert isinstance(out, nw.LazyFrame)
    assert nw.to_native(out.collect()).to_dicts() == [{"id": 1}]
    assert [record.boundary_key for record in trace.records] == [
        BoundaryKey.NARWHALS_NATIVE_WRAP
    ]


