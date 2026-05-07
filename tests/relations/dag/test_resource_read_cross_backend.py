"""Backend-parametrized resource-read tests.

Verifies that read_resource on each backend produces correct results
for inline data and local CSV/Parquet files.
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.typespec.datapackage import DataResource


def _get_polars_ext():
    from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
        MountainashPolarsExtensionRelationSystem,
    )
    return MountainashPolarsExtensionRelationSystem()


def _get_narwhals_ext():
    from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
        MountainashNarwhalsExtensionRelationSystem,
    )
    return MountainashNarwhalsExtensionRelationSystem()


def _get_ibis_ext():
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )
    return MountainashIbisExtensionRelationSystem()


def _to_dict_list(native) -> list[dict]:
    """Convert any backend's native result to a list of dicts for assertion."""
    if hasattr(native, "collect"):
        return native.collect().to_dicts()
    if hasattr(native, "to_pandas"):
        return native.to_pandas().to_dict("records")
    if hasattr(native, "execute"):
        return native.execute().to_dict("records")
    raise TypeError(f"Cannot convert {type(native)}")


@pytest.fixture(
    params=["polars", "narwhals", "ibis"],
    ids=["polars", "narwhals", "ibis"],
)
def backend_ext(request):
    factories = {
        "polars": _get_polars_ext,
        "narwhals": _get_narwhals_ext,
        "ibis": _get_ibis_ext,
    }
    return factories[request.param]()


class TestReadResourceInline:
    def test_inline_list_of_dicts(self, backend_ext):
        res = DataResource(name="t", data=[{"a": 1}, {"a": 2}], format="json")
        result = backend_ext.read_resource(res)
        rows = _to_dict_list(result)
        assert [r["a"] for r in rows] == [1, 2]


class TestReadResourceLocalCSV:
    def test_csv_local(self, backend_ext, tmp_path):
        p = tmp_path / "t.csv"
        p.write_text("a,b\n1,2\n3,4\n")
        res = DataResource(name="t", path=str(p), format="csv")
        rows = _to_dict_list(backend_ext.read_resource(res))
        assert len(rows) == 2


class TestReadResourceLocalParquet:
    def test_parquet_local(self, backend_ext, tmp_path):
        p = tmp_path / "t.parquet"
        pl.DataFrame({"x": [10, 20]}).write_parquet(p)
        res = DataResource(name="t", path=str(p), format="parquet")
        rows = _to_dict_list(backend_ext.read_resource(res))
        vals = sorted(r["x"] for r in rows)
        assert vals == [10, 20]
