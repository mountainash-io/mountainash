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




class CountingResolver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.documents = {
            "schema.json": {
                "fields": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "string"},
                ]
            },
            "dialect.json": {"delimiter": ";"},
        }

    def resolve(self, reference, *, base_uri, expected_kind):
        self.calls.append((reference, expected_kind))
        return self.documents[reference]

def _get_ibis_ext():
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )
    return MountainashIbisExtensionRelationSystem()


def _collect_pl(native) -> pl.DataFrame:
    """Normalise any backend's read_resource result to a pl.DataFrame so its
    schema/dtypes can be asserted uniformly. For Ibis this goes through
    to_pyarrow(), proving the declared dtype survived the Arrow/memtable
    boundary (not just the in-Polars cast)."""
    if hasattr(native, "to_pyarrow") and not hasattr(native, "collect"):  # ibis Table
        return pl.from_arrow(native.to_pyarrow())
    if hasattr(native, "collect"):
        native = native.collect()
    if hasattr(native, "to_native"):  # narwhals -> pl.DataFrame
        native = native.to_native()
    if isinstance(native, pl.DataFrame):
        return native
    if hasattr(native, "to_arrow"):
        return pl.from_arrow(native.to_arrow())
    raise TypeError(f"Cannot normalise {type(native)}")


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

    def spy(resource, *, dialect):
        calls["n"] += 1
        return real(resource, dialect=dialect)
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
                        lambda r, *, dialect: (
                            calls.__setitem__("n", calls["n"] + 1),
                            real(r, dialect=dialect),
                        )[1])
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

@pytest.mark.parametrize("backend", _DAG_BACKENDS)
def test_referenced_schema_and_dialect_resolve_once_per_backend(backend, tmp_path):
    from mountainash.typespec.datapackage import DataPackage
    from mountainash.typespec.descriptor_context import DescriptorKind

    path = tmp_path / "rows.csv"
    path.write_text("id;name\n1;alice\n2;bob\n")
    resolver = CountingResolver()
    package = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "rows",
                    "path": "rows.csv",
                    "format": "csv",
                    "schema": "schema.json",
                    "dialect": "dialect.json",
                }
            ]
        },
        base_uri=tmp_path,
        resolver=resolver,
    )
    resource = package.resources[0]
    resource.path = str(path)

    rows = _to_dict_list(_collect_via_dag(resource, backend))

    assert rows == [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
    assert [kind for _, kind in resolver.calls] == [
        DescriptorKind.DIALECT,
        DescriptorKind.SCHEMA,
    ]
    assert resource.table_schema == "schema.json"
    assert resource.dialect == "dialect.json"



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

    def test_escape_char_dialect_parity(self, backend, tmp_path):
        # escape_char is CsvSpec-mappable but has NO correct native pl.scan_csv
        # target, so ALL three backends route it to the files fallback (which
        # honours it via CsvSpec.escape_char) -> identical, CORRECT values. Before
        # the native-safe split, Polars/Narwhals read it natively-and-wrong
        # (escape_char->eol_char) while Ibis read it right -> divergence
        # (consistency-guarantees, ENFORCED).
        from mountainash.typespec.datapackage import DataResource, TableDialect
        # note field is a quoted value with an escaped quote: "a\"b" -> a"b
        (tmp_path / "d.csv").write_text('name,note\n1,"a\\"b"\n')
        res = DataResource(name="d", path=str(tmp_path / "d.csv"), format="csv",
                           dialect=TableDialect(escape_char="\\"))
        rows = _to_dict_list(_collect_via_dag(res, backend))
        assert [(r["name"], r["note"]) for r in rows] == [(1, 'a"b')]

    def test_absence_transitive_during_parse(self, backend, tmp_path, monkeypatch):
        # A transitive dep failing while parse() runs must propagate the typed
        # error through collect() (normalization itself is unit-tested in Task 1).
        import mountainash.relations.backends.relation_systems.resource_files as rf
        from mountainash.relations.dag.errors import MissingFilesDependency
        from mountainash.typespec.datapackage import DataResource


        def boom(_resource, *, dialect):
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
                            lambda r, *, dialect: (
                                calls.__setitem__("n", calls["n"] + 1),
                                real(r, dialect=dialect),
                            )[1])
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
                            lambda r, *, dialect: (
                                calls.__setitem__("n", calls["n"] + 1),
                                real(r, dialect=dialect),
                            )[1])
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
        def fake_parse(resource, *, dialect):
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


# ---------------------------------------------------------------------------
# Item 53 — inline reads honor the declared schema (typed-null dtype loss)
# ---------------------------------------------------------------------------


class TestInlineReadSchemaFidelity:
    """Item 53: inline reads restore the declared dtype of null-inferred columns."""

    def test_any_all_null_becomes_string(self, backend_ext):
        res = DataResource(
            name="t", format="json",
            data={"id": [1], "note": [None]},
            schema={"fields": [
                {"name": "id", "type": "integer"},
                {"name": "note", "type": "any"},
            ]},
        )
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["note"] == pl.String
        assert df.schema["id"] == pl.Int64

    def test_backend_type_unparameterized_honored(self, backend_ext):
        res = DataResource(
            name="t", format="json",
            data={"ts": [None]},
            schema={"fields": [
                {"name": "ts", "type": "any",
                 "x-mountainash": {"backend_type": "Datetime"}},
            ]},
        )
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["ts"] == pl.Datetime

    def test_concrete_types_all_null(self, backend_ext):
        res = DataResource(
            name="t", format="json",
            data={"i": [None], "b": [None], "d": [None]},
            schema={"fields": [
                {"name": "i", "type": "integer"},
                {"name": "b", "type": "boolean"},
                {"name": "d", "type": "date"},
            ]},
        )
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["i"] == pl.Int64
        assert df.schema["b"] == pl.Boolean
        assert df.schema["d"] == pl.Date

    def test_table_schema_as_typespec_object(self, backend_ext):
        from mountainash.typespec.frictionless import typespec_from_frictionless
        spec = typespec_from_frictionless(
            {"fields": [{"name": "note", "type": "any"}]}
        )
        res = DataResource(name="t", format="json", data={"note": [None]}, schema=spec)
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["note"] == pl.String

    def test_typed_non_null_column_untouched(self, backend_ext):
        # Null-only policy: a typed column is never recast, even if its
        # inferred dtype diverges from the schema (schema says string, data
        # is int -> stays Int64).
        res = DataResource(
            name="t", format="json",
            data={"x": [1, 2]},
            schema={"fields": [{"name": "x", "type": "string"}]},
        )
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["x"] == pl.Int64

    def test_no_table_schema_is_noop(self, backend_ext):
        res = DataResource(name="t", format="json", data={"note": [None]})
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["note"] == pl.Null  # unchanged pre-fix behaviour

    def test_rename_from_does_not_null_column(self, backend_ext):
        # Data already renamed to the output name; schema carries rename_from.
        # to_polars_schema keys on output name, so the dtype still applies and
        # no all-null renamed column appears (the backlog caveat, proven moot).
        res = DataResource(
            name="t", format="json",
            data={"provider_id": [1], "note": [None]},
            schema={"fields": [
                {"name": "provider_id", "type": "integer",
                 "x-mountainash": {"rename_from": "id"}},
                {"name": "note", "type": "any"},
            ]},
        )
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.columns == ["provider_id", "note"]
        assert df.schema["provider_id"] == pl.Int64
        assert df.schema["note"] == pl.String

    def test_zero_row_column_completed(self, backend_ext):
        res = DataResource(
            name="t", format="json",
            data={"note": []},
            schema={"fields": [{"name": "note", "type": "any"}]},
        )
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["note"] == pl.String
        assert df.height == 0


class TestInlineReadParameterizedBackendType:
    """Parameterized backend_type fidelity on the inline-read path (item 54).

    These flipped from item 53's deferred behaviour ("falls to String") in
    PR-1 of item 54: a tz-aware Datetime string now parses to a real
    parameterized dtype instead of degrading to ANY -> String."""

    def test_parameterized_backend_type_produces_real_dtype(self, backend_ext):
        # tz-aware Datetime string contains '(' — previously parse_type_string
        # returned None -> ANY -> String; item 54 now reconstructs the real
        # parameterized dtype.
        res = DataResource(
            name="t", format="json",
            data={"ts": [None]},
            schema={"fields": [
                {"name": "ts", "type": "any",
                 "x-mountainash": {"backend_type": "Datetime(time_zone='UTC')"}},
            ]},
        )
        df = _collect_pl(backend_ext.read_resource(res))
        assert df.schema["ts"] == pl.Datetime(time_zone="UTC")


class TestInlineReadCastError:
    def test_cast_failure_raises_typed_error(self):
        from mountainash.relations.dag.errors import ResourceSchemaCastError

        ext = _get_polars_ext()
        # A null-inferred column always casts cleanly (Null -> anything), so the
        # cast-failure branch cannot be reached with real data. Force it by
        # monkeypatching pl.DataFrame.cast to assert the error TYPE/shape.
        res = DataResource(
            name="bad", format="json",
            data={"note": [None]},
            schema={"fields": [{"name": "note", "type": "any"}]},
        )
        orig = pl.DataFrame.cast

        def boom(self, *a, **k):
            raise pl.exceptions.InvalidOperationError("forced")

        pl.DataFrame.cast = boom
        try:
            with pytest.raises(ResourceSchemaCastError) as ei:
                ext.read_resource(res)
        finally:
            pl.DataFrame.cast = orig
        assert ei.value.resource == "bad"
        assert "note" in ei.value.casts


class TestInlineReadRoundTrip:
    def test_datapackage_dag_collect_preserves_all_null_dtype(self):
        from mountainash.typespec.datapackage import DataPackage

        pkg = DataPackage(resources=[
            DataResource(
                name="sleep", type="table", format="json",
                data={"id": [1], "reason": [None]},
                schema={"fields": [
                    {"name": "id", "type": "integer"},
                    {"name": "reason", "type": "any"},
                ]},
            ),
        ])
        dag = pkg.to_relation_dag()
        result = dag.collect("sleep")
        df = result.collect() if hasattr(result, "collect") else result
        assert df.schema["reason"] == pl.String
