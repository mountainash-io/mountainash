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
    """Convert any backend's native result to a list of dicts for assertion.

    Handles both Polars LazyFrame (.collect() -> pl.DataFrame, has .to_dicts())
    and Narwhals LazyFrame (.collect() -> nw.DataFrame, which has no .to_dicts()
    of its own -- unwrap via .to_native() to reach the underlying pl.DataFrame).
    """
    if hasattr(native, "collect"):
        native = native.collect()
    if hasattr(native, "to_native"):
        native = native.to_native()
    if hasattr(native, "to_dicts"):
        return native.to_dicts()
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


def test_polars_json_uses_files_fallback(tmp_path, monkeypatch):
    import mountainash.relations.backends.relation_systems.resource_files as rf
    from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
        MountainashPolarsExtensionRelationSystem,
    )
    calls = {"n": 0}
    real = rf.parse_resource_to_arrow

    def spy(resource):
        calls["n"] += 1
        return real(resource)

    monkeypatch.setattr(rf, "parse_resource_to_arrow", spy)
    p = tmp_path / "d.json"; p.write_text('[{"a": 1, "b": "x"}]')
    from mountainash.typespec.datapackage import DataResource
    res = DataResource(name="d", path=str(p), format="json")
    out = MountainashPolarsExtensionRelationSystem().read_resource(res).collect()
    assert calls["n"] == 1                       # JSON has no lazy scan -> fallback
    assert out.to_dicts() == [{"a": 1, "b": "x"}]


def test_narwhals_local_csv_returns_lazyframe(tmp_path):
    import narwhals as nw
    from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
        MountainashNarwhalsExtensionRelationSystem,
    )
    p = tmp_path / "d.csv"; p.write_text("a,b\n1,x\n2,y\n")
    res = DataResource(name="d", path=str(p), format="csv")
    out = MountainashNarwhalsExtensionRelationSystem().read_resource(res)
    assert isinstance(out, nw.LazyFrame)
    assert nw.to_native(out.collect()).to_dicts() == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_narwhals_native_semicolon_dialect(tmp_path):
    """Non-default mappable dialect (delimiter=';') must forward through
    nw.scan_csv(..., backend="polars") on the native local-CSV path."""
    import narwhals as nw
    from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
        MountainashNarwhalsExtensionRelationSystem,
    )
    from mountainash.typespec.datapackage import TableDialect
    p = tmp_path / "d.csv"; p.write_text("a;b\n1;x\n2;y\n")
    res = DataResource(name="d", path=str(p), format="csv", dialect=TableDialect(delimiter=";"))
    out = MountainashNarwhalsExtensionRelationSystem().read_resource(res)
    assert isinstance(out, nw.LazyFrame)
    assert nw.to_native(out.collect()).to_dicts() == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_ibis_json_fallback_no_pandas(tmp_path, monkeypatch):
    import sys
    import mountainash.relations.backends.relation_systems.resource_files as rf
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )
    from mountainash.typespec.datapackage import DataResource
    # Local JSON MUST route to the files fallback (spec §A.6), not con.read_json.
    calls = {"n": 0}
    real = rf.parse_resource_to_arrow
    monkeypatch.setattr(rf, "parse_resource_to_arrow",
                        lambda r: (calls.__setitem__("n", calls["n"] + 1), real(r))[1])
    p = tmp_path / "d.json"; p.write_text('[{"a": 1}, {"a": 2}]')
    res = DataResource(name="d", path=str(p), format="json")
    sys.modules.pop("pandas", None)
    tbl = MountainashIbisExtensionRelationSystem().read_resource(res)
    rows = tbl.to_pyarrow().to_pylist()
    assert calls["n"] == 1                       # went through the fallback
    assert rows == [{"a": 1}, {"a": 2}]
    assert "pandas" not in sys.modules           # Arrow-only coercion
