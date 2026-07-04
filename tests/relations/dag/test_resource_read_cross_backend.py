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


# ---------------------------------------------------------------------------
# Cross-backend integration matrix -- through a real RelationDAG.collect()
# ---------------------------------------------------------------------------

_DAG_BACKENDS = ["polars", "narwhals", "ibis"]


def _collect_via_dag(res, backend: str):
    """Read a DataResource through a real one-node RelationDAG on `backend`.
    Exercises the ResourceReadRelNode -> visitor -> conform-after-read path."""
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ResourceReadRelNode,
    )
    dag = RelationDAG()
    dag.add(res.name, Relation(ResourceReadRelNode(resource=res)))
    return dag.collect(res.name, backend=backend)


def _column_names(native) -> list[str]:
    """Backend-native column names (for empty-frame schema assertions)."""
    if hasattr(native, "collect"):          # polars/narwhals lazy
        return list(native.collect().columns)
    if hasattr(native, "columns"):          # ibis Table / polars DataFrame
        return list(native.columns)
    if hasattr(native, "schema"):
        return list(native.schema().names)
    raise TypeError(f"Cannot read columns from {type(native)}")


@pytest.mark.parametrize("backend", _DAG_BACKENDS)
class TestItem32FallbackViaDAG:
    def test_parity_local_csv(self, backend, tmp_path):
        from mountainash.typespec.datapackage import DataResource
        p = tmp_path / "d.csv"; p.write_text("a,b\n1,x\n2,y\n")
        res = DataResource(name="d", path=str(p), format="csv")
        assert _to_dict_list(_collect_via_dag(res, backend)) == \
            [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]

    def test_inline_data(self, backend):
        from mountainash.typespec.datapackage import DataResource
        res = DataResource(name="d", data=[{"a": 1}, {"a": 2}])
        assert [r["a"] for r in _to_dict_list(_collect_via_dag(res, backend))] == [1, 2]

    def test_multipath_csv_promote(self, backend, tmp_path):
        from mountainash.typespec.datapackage import DataResource
        (tmp_path / "a.csv").write_text("x\n1\n")
        (tmp_path / "b.csv").write_text("x\n2\n")
        res = DataResource(name="d",
                           path=[str(tmp_path / "a.csv"), str(tmp_path / "b.csv")],
                           format="csv")
        assert sorted(r["x"] for r in _to_dict_list(_collect_via_dag(res, backend))) == [1, 2]

    def test_mappable_nondefault_dialect_roundtrip(self, backend, tmp_path):
        # delimiter=';' is mappable -> native (kwargs) on Polars/Narwhals,
        # files fallback on Ibis; values identical across all three (§A.6).
        from mountainash.typespec.datapackage import DataResource, TableDialect
        (tmp_path / "d.csv").write_text("a;b\n1;x\n2;y\n")
        res = DataResource(name="d", path=str(tmp_path / "d.csv"), format="csv",
                           dialect=TableDialect(delimiter=";"))
        rows = _to_dict_list(_collect_via_dag(res, backend))
        assert [(r["a"], r["b"]) for r in rows] == [(1, "x"), (2, "y")]

    def test_absence_transitive_during_parse(self, backend, tmp_path, monkeypatch):
        # A transitive dep failing while parse() runs must propagate the typed
        # error through collect() (normalization itself is unit-tested in Task 1).
        import mountainash.relations.backends.relation_systems.resource_files as rf
        from mountainash.relations.dag.errors import MissingFilesDependency
        from mountainash.typespec.datapackage import DataResource

        def boom(_resource):
            raise MissingFilesDependency("needs mountainash[files]")

        monkeypatch.setattr(rf, "parse_resource_to_arrow", boom)
        p = tmp_path / "d.json"; p.write_text('[{"a": 1}]')
        res = DataResource(name="d", path=str(p), format="json")
        with pytest.raises(MissingFilesDependency, match=r"mountainash\[files\]"):
            _collect_via_dag(res, backend)

    def test_parity_local_json_fallback(self, backend, tmp_path):
        from mountainash.typespec.datapackage import DataResource
        p = tmp_path / "d.json"; p.write_text('[{"a": 1}, {"a": 2}]')
        res = DataResource(name="d", path=str(p), format="json")
        assert [r["a"] for r in _to_dict_list(_collect_via_dag(res, backend))] == [1, 2]

    def test_parity_parquet(self, backend, tmp_path):
        import polars as pl
        from mountainash.typespec.datapackage import DataResource
        pl.DataFrame({"x": [1, 2]}).write_parquet(tmp_path / "d.parquet")
        res = DataResource(name="d", path=str(tmp_path / "d.parquet"), format="parquet")
        assert sorted(r["x"] for r in _to_dict_list(_collect_via_dag(res, backend))) == [1, 2]

    def test_multipath_promote(self, backend, tmp_path):
        import polars as pl
        from mountainash.typespec.datapackage import DataResource
        pl.DataFrame({"x": [1]}).write_parquet(tmp_path / "a.parquet")
        pl.DataFrame({"x": [2]}).write_parquet(tmp_path / "b.parquet")
        res = DataResource(name="d",
                           path=[str(tmp_path / "a.parquet"), str(tmp_path / "b.parquet")],
                           format="parquet")
        assert sorted(r["x"] for r in _to_dict_list(_collect_via_dag(res, backend))) == [1, 2]

    def test_gzip_csv_fallback(self, backend, tmp_path):
        import gzip
        from mountainash.typespec.datapackage import DataResource
        (tmp_path / "d.csv.gz").write_bytes(gzip.compress(b"a\n1\n2\n"))
        res = DataResource(name="d", path=str(tmp_path / "d.csv.gz"), format="csv")
        assert [r["a"] for r in _to_dict_list(_collect_via_dag(res, backend))] == [1, 2]

    def test_absence_direct_import(self, backend, tmp_path, monkeypatch):
        import builtins
        from mountainash.relations.dag.errors import MissingFilesDependency
        from mountainash.typespec.datapackage import DataResource
        real_import = builtins.__import__

        def fake(name, *a, **k):
            if name == "mountainash_files" or name.startswith("mountainash_files."):
                raise ImportError("gone")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake)
        p = tmp_path / "d.json"; p.write_text('[{"a": 1}]')  # JSON forces fallback
        res = DataResource(name="d", path=str(p), format="json")
        with pytest.raises(MissingFilesDependency, match=r"mountainash\[files\]"):
            _collect_via_dag(res, backend)


class TestReaderTimingAndSchema:
    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_native_local_does_not_call_parse(self, backend, tmp_path, monkeypatch):
        import mountainash.relations.backends.relation_systems.resource_files as rf
        from mountainash.typespec.datapackage import DataResource
        calls = {"n": 0}
        real = rf.parse_resource_to_arrow
        monkeypatch.setattr(rf, "parse_resource_to_arrow",
                            lambda r: (calls.__setitem__("n", calls["n"] + 1), real(r))[1])
        p = tmp_path / "d.csv"; p.write_text("a\n1\n")
        res = DataResource(name="d", path=str(p), format="csv")
        _to_dict_list(_collect_via_dag(res, backend))
        assert calls["n"] == 0            # native local scan stays lazy

    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_fallback_calls_parse_once(self, backend, tmp_path, monkeypatch):
        import mountainash.relations.backends.relation_systems.resource_files as rf
        from mountainash.typespec.datapackage import DataResource
        calls = {"n": 0}
        real = rf.parse_resource_to_arrow
        monkeypatch.setattr(rf, "parse_resource_to_arrow",
                            lambda r: (calls.__setitem__("n", calls["n"] + 1), real(r))[1])
        p = tmp_path / "d.json"; p.write_text('[{"a": 1}]')
        res = DataResource(name="d", path=str(p), format="json")
        _to_dict_list(_collect_via_dag(res, backend))
        assert calls["n"] == 1            # eager fallback, exactly one parse

    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_schema_bearing_conform_parity_native_vs_fallback(self, backend, tmp_path):
        # Same declared schema on a native-path (CSV) and a fallback-path (JSON)
        # resource -> identical typed output (conform casts both).
        from mountainash.typespec.datapackage import DataResource
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import UniversalType
        schema = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])
        (tmp_path / "c.csv").write_text("n\n1\n2\n")
        (tmp_path / "j.json").write_text('[{"n": "1"}, {"n": "2"}]')
        csv_res = DataResource(name="c", path=str(tmp_path / "c.csv"), format="csv", schema=schema)
        json_res = DataResource(name="j", path=str(tmp_path / "j.json"), format="json", schema=schema)
        csv_rows = [r["n"] for r in _to_dict_list(_collect_via_dag(csv_res, backend))]
        json_rows = [r["n"] for r in _to_dict_list(_collect_via_dag(json_res, backend))]
        assert csv_rows == json_rows == [1, 2]   # both conformed to INTEGER

    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_empty_frame_typed_parity(self, backend):
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import UniversalType
        factories = {"polars": _get_polars_ext, "narwhals": _get_narwhals_ext,
                     "ibis": _get_ibis_ext}
        ext = factories[backend]()
        spec = TypeSpec(fields=[FieldSpec(name="k", type=UniversalType.INTEGER)])
        empty = ext.empty_frame(spec)
        assert _to_dict_list(empty) == []        # zero rows
        assert _column_names(empty) == ["k"]     # typed schema present, not just empty

    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_remote_routes_to_fallback(self, backend, tmp_path, monkeypatch):
        # We own routing + coercion; parse()'s remote fetch is mountainash-files'
        # tested concern -> stub parse_resource_to_arrow, assert remote -> fallback.
        import pyarrow as pa
        import mountainash.relations.backends.relation_systems.resource_files as rf
        from mountainash.typespec.datapackage import DataResource
        called = {"n": 0}

        def fake_parse(resource):
            called["n"] += 1
            return pa.table({"a": [1, 2]})

        monkeypatch.setattr(rf, "parse_resource_to_arrow", fake_parse)
        res = DataResource(name="d", path="s3://bucket/d.csv", format="csv")
        rows = _to_dict_list(_collect_via_dag(res, backend))
        assert called["n"] == 1
        assert [r["a"] for r in rows] == [1, 2]


class TestDialectFailClosed:
    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_unmappable_dialect_field_raises(self, backend, tmp_path):
        from mountainash.relations.dag.errors import UnsupportedResourceFormat
        from mountainash.typespec.datapackage import DataResource, TableDialect
        p = tmp_path / "d.csv"; p.write_text("a\n1\n")
        # comment_char has no CsvSpec target -> fail-closed UNIFORMLY: Polars/
        # Narwhals raise at ensure_dialect_supported (before the native scan),
        # Ibis raises inside the fallback's _csv_spec_from_dialect. All three
        # raise -- never read-on-Polars / raise-on-Ibis (consistency-guarantees).
        res = DataResource(name="d", path=str(p), format="csv",
                           dialect=TableDialect(comment_char="#"))
        with pytest.raises(UnsupportedResourceFormat, match="comment_char"):
            _to_dict_list(_collect_via_dag(res, backend))
