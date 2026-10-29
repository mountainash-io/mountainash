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


def test_ibis_json_fallback_preserves_rows(tmp_path, monkeypatch):
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
    tbl = MountainashIbisExtensionRelationSystem().read_resource(res)
    rows = tbl.to_pyarrow().to_pylist()
    assert calls["n"] == 1                       # went through the fallback
    assert rows == [{"a": 1}, {"a": 2}]


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


def test_referenced_schema_inference_matches_inline_schema(tmp_path):
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ResourceReadRelNode,
    )
    from mountainash.relations.schema_inference import infer_schema
    from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
        _declared_polars_schema,
    )
    from mountainash.typespec.datapackage import DataPackage

    (tmp_path / "schema.json").write_text(
        '{"fields": [{"name": "id", "type": "integer"}]}',
        encoding="utf-8",
    )
    package = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "referenced",
                    "path": "rows.csv",
                    "schema": "schema.json",
                }
            ]
        },
        base_uri=tmp_path,
    )
    referenced = package.resources[0]
    inline = DataResource(
        name="inline",
        path="rows.csv",
        schema={"fields": [{"name": "id", "type": "integer"}]},
    )

    assert _declared_polars_schema(referenced) == {"id": pl.Int64}
    assert _declared_polars_schema(referenced) == _declared_polars_schema(inline)
    assert infer_schema(ResourceReadRelNode(resource=referenced)) == infer_schema(
        ResourceReadRelNode(resource=inline)
    )


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
    return dag.collect(res.name, target=backend)


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
        from mountainash.typespec.spec import FieldDefinition, TableSchema
        from mountainash.typespec.universal_types import UniversalType
        schema = TableSchema(fields={"n": FieldDefinition(type=UniversalType.INTEGER)})
        (tmp_path / "c.csv").write_text("n\n1\n2\n")
        (tmp_path / "j.json").write_text('[{"n": "1"}, {"n": "2"}]')
        csv_res = DataResource(name="c", path=str(tmp_path / "c.csv"), format="csv", schema=schema)
        json_res = DataResource(name="j", path=str(tmp_path / "j.json"), format="json", schema=schema)
        csv_rows = [r["n"] for r in _to_dict_list(_collect_via_dag(csv_res, backend))]
        json_rows = [r["n"] for r in _to_dict_list(_collect_via_dag(json_res, backend))]
        assert csv_rows == json_rows == [1, 2]   # both conformed to INTEGER

    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_empty_frame_typed_parity(self, backend):
        from mountainash.typespec.spec import FieldDefinition, TableSchema
        from mountainash.typespec.universal_types import UniversalType
        factories = {"polars": _get_polars_ext, "narwhals": _get_narwhals_ext,
                     "ibis": _get_ibis_ext}
        ext = factories[backend]()
        spec = TableSchema(fields={"k": FieldDefinition(type=UniversalType.INTEGER)})
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


class TestDialectFallback:
    @pytest.mark.parametrize("backend", _DAG_BACKENDS)
    def test_comment_dialect_field_routes_to_consistent_fallback(self, backend, tmp_path):
        from mountainash.typespec.datapackage import DataResource, TableDialect

        p = tmp_path / "d.csv"
        p.write_text("# metadata\na\n1\n")
        res = DataResource(
            name="d",
            path=str(p),
            format="csv",
            dialect=TableDialect(comment_char="#"),
        )

        assert _to_dict_list(_collect_via_dag(res, backend)) == [{"a": 1}]


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
        from mountainash.typespec.frictionless import table_schema_from_frictionless
        spec = table_schema_from_frictionless(
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


@pytest.mark.parametrize("data", [
    [{"a": 1}, {"a": 2, "b": "x"}],
    [{"a": 1, "b": None}, {"a": 2, "b": "x"}],
])
def test_json_records_payload_keeps_keys_first_seen_after_row_one(data):
    """JSON record payloads become Arrow with every key any record carries."""
    from mountainash.relations.backends.relation_systems.resource_files import _part_data_to_arrow

    table = _part_data_to_arrow(data, "d")
    assert table.column_names == ["a", "b"]
    assert table.to_pylist() == [{"a": 1, "b": None}, {"a": 2, "b": "x"}]


@pytest.mark.parametrize("format", ["csv", "parquet"])
def test_schema_inspection_uses_native_resource_metadata(tmp_path, monkeypatch, format):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    import mountainash.relations.backends.relation_systems.resource_files as rf
    from mountainash.typespec.spec import FieldDefinition, TableSchema
    from mountainash.typespec.universal_types import UniversalType

    paths = [tmp_path / f"rows-{index}.{format}" for index in (1, 2)]
    for index, path in enumerate(paths, start=1):
        if format == "csv":
            path.write_text(f"actual,value\n{index},x\n")
        else:
            pl.DataFrame({"actual": [index], "value": ["x"]}).write_parquet(path)
    open_spec = TableSchema(
        fields={"actual": FieldDefinition(type=UniversalType.INTEGER)},
        fields_match="open",
    )
    resource = DataResource(name="rows", path=[str(path) for path in paths], format=format, schema=open_spec)
    relation = Relation(ResourceReadRelNode(resource=resource))
    reads = []
    real_read = rf.parse_resource_to_arrow

    def count_fallback(resource, *, dialect):
        reads.append(resource.name)
        return real_read(resource, dialect=dialect)

    monkeypatch.setattr(rf, "parse_resource_to_arrow", count_fallback)

    assert list(relation.collect_schema()) == ["actual", "value"]
    assert relation.collect_schema(allow_execution=True) == relation.collect_schema()
    assert reads == []

    closed_spec = TableSchema(
        fields={"actual": FieldDefinition(type=UniversalType.INTEGER)},
        fields_match="subset",
    )
    closed = Relation(ResourceReadRelNode(
        resource=DataResource(
            name="closed",
            path=[str(path) for path in paths],
            format=format,
            schema=closed_spec,
        ),
    ))
    assert list(closed.collect_schema()) == ["actual"]
    assert reads == []



def test_resource_schema_preserves_missing_and_access_errors(tmp_path, monkeypatch):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode

    missing = DataResource(
        name="missing",
        path=str(tmp_path / "missing.csv"),
        format="csv",
    )
    with pytest.raises(FileNotFoundError):
        Relation(ResourceReadRelNode(resource=missing)).collect_schema()

    path = tmp_path / "protected.csv"
    path.write_text("a\n1\n")
    protected = DataResource(name="protected", path=str(path), format="csv")

    def deny_read(*args, **kwargs):
        raise PermissionError("access denied")

    monkeypatch.setattr(pl, "scan_csv", deny_read)
    with pytest.raises(PermissionError, match="access denied"):
        Relation(ResourceReadRelNode(resource=protected)).collect_schema()



@pytest.mark.parametrize(
    "route",
    ["json", "gzip_csv", "glob_csv", "escaped_csv", "remote_csv"],
)
def test_file_resource_schema_discovery_precedes_execution(
    tmp_path, monkeypatch, request, route,
):
    import gzip

    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    import mountainash.relations.backends.relation_systems.resource_files as rf
    from mountainash.typespec.datapackage import TableDialect

    dialect = None
    if route == "json":
        path, fmt = tmp_path / "rows.json", "json"
        path.write_text('[{"actual": 1}]')
    elif route == "gzip_csv":
        path, fmt = tmp_path / "rows.csv.gz", "csv"
        path.write_bytes(gzip.compress(b"actual\n1\n"))
    elif route == "glob_csv":
        path, fmt = tmp_path / "part-*.csv", "csv"
        (tmp_path / "part-1.csv").write_text("actual\n1\n")
    elif route == "escaped_csv":
        path, fmt = tmp_path / "rows.csv", "csv"
        path.write_text('actual\n1\n')
        dialect = TableDialect(escape_char="\\")
    else:
        (tmp_path / "rows.csv").write_text("actual\n1\n")
        path, fmt = request.getfixturevalue("schema_resource_http_url"), "csv"

    relation = Relation(ResourceReadRelNode(
        resource=DataResource(
            name="rows",
            path=str(path),
            format=fmt,
            dialect=dialect,
        ),
    ))
    reads = []
    real_read = rf.parse_resource_to_arrow

    def count_fallback(resource, *, dialect):
        reads.append(resource.name)
        return real_read(resource, dialect=dialect)

    monkeypatch.setattr(rf, "parse_resource_to_arrow", count_fallback)

    from mountainash.core.dtypes import MountainashDtype as D

    assert relation.schema == {"actual": D.I64}
    assert relation.collect_schema() == {"actual": D.I64}
    assert relation.collect_schema(allow_execution=True) == {"actual": D.I64}
    assert reads == []
    assert relation.to_dict() == {"actual": [1]}


def test_native_semicolon_dialect_schema_inference_stays_lazy(tmp_path, monkeypatch):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    import mountainash.relations.backends.relation_systems.resource_files as rf
    from mountainash.typespec.datapackage import TableDialect

    path = tmp_path / "rows.csv"
    path.write_text("actual;value\n1;x\n")
    relation = Relation(ResourceReadRelNode(resource=DataResource(
        name="rows",
        path=str(path),
        format="csv",
        dialect=TableDialect(delimiter=";"),
    )))

    def eager_read(*args, **kwargs):
        raise AssertionError("native schema planning used the eager reader")

    monkeypatch.setattr(rf, "parse_resource_to_arrow", eager_read)
    assert list(relation.collect_schema()) == ["actual", "value"]
    assert relation.collect_schema(allow_execution=True) == relation.collect_schema()


@pytest.fixture(params=["polars", "narwhals", "ibis"])
def _family_system(request):
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

    return get_relation_system(CONST_BACKEND(request.param))()


def test_native_scan_eligible_false_for_inline(_family_system):
    resource = DataResource(name="d", data=[{"a": 1}])
    assert _family_system.native_scan_eligible(resource) is False


def test_native_scan_eligible_true_for_local_csv(_family_system, tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("a,b\n1,2\n")
    resource = DataResource(name="d", path=str(path), format="csv")
    assert _family_system.native_scan_eligible(resource) is True



# --- resource reads bind to the resolved location ---------------------------
import ibis
from mountainash import DataPackage


def _pkg(tmp_path, kind):
    fields = '[{"name":"id","type":"integer"},{"name":"amount","type":"integer"}]'
    if kind == "inline":
        body = '{"name":"orders","type":"table","data":[{"id":1,"amount":10},{"id":2,"amount":20}],"schema":{"fields":%s}}' % fields
    elif kind == "json":
        (tmp_path / "orders.json").write_text('[{"id":1,"amount":10},{"id":2,"amount":20}]')
        body = '{"name":"orders","path":"%s","type":"table","format":"json","schema":{"fields":%s}}' % (tmp_path / "orders.json", fields)
    else:
        (tmp_path / "orders.csv").write_text("id,amount\n1,10\n2,20\n")
        body = '{"name":"orders","path":"%s","type":"table","schema":{"fields":%s}}' % (tmp_path / "orders.csv", fields)
    (tmp_path / "datapackage.json").write_text('{"resources":[%s]}' % body)
    return DataPackage.from_path(tmp_path / "datapackage.json")


EXPECTED = [{"id": 1, "amount": 10}, {"id": 2, "amount": 20}]


@pytest.mark.parametrize("kind", ["csv", "inline", "json"])
def test_resource_on_target_connection(tmp_path, kind):
    B = ibis.duckdb.connect()
    out = _pkg(tmp_path, kind).to_relation_dag().collect("orders", target=B)
    assert out.get_backend() is B and out.to_polars().to_dicts() == EXPECTED


@pytest.mark.parametrize("kind", ["csv", "inline"])
def test_resource_narwhals_pandas(tmp_path, kind):
    out = _pkg(tmp_path, kind).to_relation_dag().collect("orders", target="narwhals-pandas")
    assert str(out.implementation).lower().endswith("pandas")
    assert out.to_dict(as_series=False) == {"id": [1, 2], "amount": [10, 20]}


# --- review fixes: referenced resources, unary chains, narwhals form/predicate ---
def _count_owned(B):
    return [t for t in B.list_tables() if t.startswith("ma_owned_")]


@pytest.mark.parametrize("kind", ["csv", "inline", "json"])
def test_referenced_resource_on_target_connection(tmp_path, kind):
    B = ibis.duckdb.connect()
    dag = _pkg(tmp_path, kind).to_relation_dag()
    dag.add("alias", dag.ref("orders"))
    out = dag.collect("alias", target=B)
    assert out.get_backend() is B and out.to_polars().to_dicts() == EXPECTED


@pytest.mark.parametrize("kind", ["csv", "inline"])
def test_referenced_resource_narwhals_pandas(tmp_path, kind):
    dag = _pkg(tmp_path, kind).to_relation_dag()
    dag.add("alias", dag.ref("orders"))
    out = dag.collect("alias", target="narwhals-pandas")
    assert str(out.implementation).lower().endswith("pandas")
    assert out.to_dict(as_series=False) == {"id": [1, 2], "amount": [10, 20]}


@pytest.mark.parametrize("kind", ["inline", "json", "csv"])
def test_resource_unary_chain_on_target_connection(tmp_path, kind):
    B = ibis.duckdb.connect()
    dag = _pkg(tmp_path, kind).to_relation_dag()
    out = dag.ref("orders").sort("id").head(1).collect(target=B)
    assert out.get_backend() is B and out.to_polars().to_dicts() == EXPECTED[:1]
    if kind != "csv":
        assert len(_count_owned(B)) == 1


def test_resource_csv_joins_eager_narwhals_polars(tmp_path):
    import narwhals as nw
    dag = _pkg(tmp_path, "csv").to_relation_dag()
    left = nw.from_native(pl.DataFrame({"id": [1, 2], "tag": ["a", "b"]}))
    dag.source("left", left)
    dag.add("j", dag.ref("left").join(dag.ref("orders"), on="id"))
    out = dag.collect("j", target="narwhals-polars")
    assert sorted(out.to_dict(as_series=False)["amount"]) == [10, 20]


def test_narwhals_predicate_and_reader_agree_on_location(tmp_path):
    from mountainash.relations.core.execution.location import ExecutionLocation
    from mountainash.relations.core.materialization import ExecutionForm
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
    ext = get_relation_system(CONST_BACKEND.NARWHALS)()
    resource = DataResource(name="o", path=str(tmp_path / "o.csv"), format="csv", type="table")
    (tmp_path / "o.csv").write_text("id,amount\n1,10\n")
    pandas_loc = ExecutionLocation(CONST_BACKEND.NARWHALS, "narwhals-pandas", ExecutionForm.EAGER, "bound")
    polars_loc = ExecutionLocation(CONST_BACKEND.NARWHALS, "narwhals-polars", ExecutionForm.EAGER, "bound")
    assert ext.native_scan_eligible(resource, location=pandas_loc) is False
    assert ext.native_scan_eligible(resource, location=polars_loc) is True
    assert ext.native_scan_eligible(resource) is True
    out = ext.read_resource(resource, location=pandas_loc)
    assert str(out.implementation).lower().endswith("pandas")
    from mountainash.core.lowering_reuse import DEFERRED_ONLY
    assert ext._resource_lowering is not DEFERRED_ONLY
    eager = ext.read_resource(resource, location=polars_loc)
    assert type(eager).__name__ == "DataFrame"


def test_schema_of_eager_narwhals_join_never_collects_scan(tmp_path, monkeypatch):
    import narwhals as nw
    dag = _pkg(tmp_path, "csv").to_relation_dag()
    dag.source("left", nw.from_native(pl.DataFrame({"id": [1, 2], "tag": ["a", "b"]})))
    dag.add("j", dag.ref("left").join(dag.ref("orders"), on="id"))
    collected = []
    real = nw.LazyFrame.collect
    monkeypatch.setattr(nw.LazyFrame, "collect", lambda self, *a, **k: (r := real(self, *a, **k), collected.append(len(r)))[0])
    schema = dag.ref("j").collect_schema()
    assert set(schema) == {"id", "tag", "amount"}
    assert all(n == 0 for n in collected)  # type-only: never a row


@pytest.mark.parametrize("target", ["polars", "narwhals-polars", "narwhals-lazy", "ibis-duckdb"])
@pytest.mark.parametrize("fmt,delimiter,header", [
    ("csv", ",", True), ("csv", ";", True), ("csv", ";", False), ("parquet", None, True),
])
def test_anonymous_http_native_without_files_import(
    target, fmt, delimiter, header, tmp_path, schema_resource_http_url, monkeypatch,
):
    import mountainash as ma
    from mountainash.relations.backends.relation_systems import resource_files

    source = pl.DataFrame({
        "id": [11, 12], "value": [-2147483649, 4294967297], "label": ["a,b", None],
    })
    path = tmp_path / f"rows.{fmt}"
    if fmt == "csv":
        source.write_csv(path, separator=delimiter, null_value="NULL", include_header=header)
    else:
        source.write_parquet(path)

    def no_materializing_reader(*args, **kwargs):
        raise AssertionError("native read must not materialize through mountainash-files")

    monkeypatch.setattr(resource_files, "parse_resource_to_arrow", no_materializing_reader)
    url = schema_resource_http_url.rsplit("/", 1)[0] + "/" + path.name
    dialect = {"delimiter": delimiter, "nullSequence": "NULL", "header": header} if fmt == "csv" else None
    resource = ma.DataResource(name="rows", path=url, format=fmt, dialect=dialect)
    connection = None
    if target == "ibis-duckdb":
        import ibis

        connection = ibis.duckdb.connect()
    try:
        result = ma.ResourceRef(resource).relation().collect(target=connection or target)
        frame = _collect_pl(result)
        names = ["id", "value", "label"] if header else ["field1", "field2", "field3"]
        assert frame.to_dicts() == [
            dict(zip(names, [11, -2147483649, "a,b"])),
            dict(zip(names, [12, 4294967297, None])),
        ]
        assert frame.schema == dict(zip(names, [pl.Int64, pl.Int64, pl.String]))
    finally:
        if connection is not None:
            connection.disconnect()


@pytest.mark.parametrize("target", ["polars", "narwhals-polars", "narwhals-lazy", "ibis-duckdb"])
@pytest.mark.parametrize("shape", ["int64", "int8", "nested-missing"])
def test_remote_parquet_list_promotes_null_schema(
    target, shape, tmp_path, schema_resource_http_url,
):
    import mountainash as ma

    if shape == "nested-missing":
        first = pl.DataFrame({"record": [{"value": None}], "items": [[None]], "first": ["a"]})
        second = pl.DataFrame(
            {"record": [{"value": 7}], "items": [[7]], "second": ["b"]},
            schema={"record": pl.Struct({"value": pl.Int8}), "items": pl.List(pl.Int8), "second": pl.String},
        )
        expected = [
            {"record": {"value": None}, "items": [None], "first": "a", "second": None},
            {"record": {"value": 7}, "items": [7], "first": None, "second": "b"},
        ]
        schema = {"record": pl.Struct({"value": pl.Int8}), "items": pl.List(pl.Int8),
                  "first": pl.String, "second": pl.String}
    else:
        value, dtype = (2**40, pl.Int64) if shape == "int64" else (7, pl.Int8)
        first = pl.DataFrame({"v": [None]})
        second = pl.DataFrame({"v": [value]}, schema={"v": dtype})
        expected, schema = [{"v": None}, {"v": value}], {"v": dtype}
    first.write_parquet(tmp_path / "null.parquet")
    second.write_parquet(tmp_path / "integer.parquet")
    base = schema_resource_http_url.rsplit("/", 1)[0]
    resource = ma.DataResource(name="rows", format="parquet",
                               path=[f"{base}/null.parquet", f"{base}/integer.parquet"])
    connection = None
    if target == "ibis-duckdb":
        import ibis

        connection = ibis.duckdb.connect()
    try:
        frame = _collect_pl(ma.ResourceRef(resource).relation().collect(target=connection or target))
        assert frame.to_dicts() == expected
        assert frame.schema == schema
    finally:
        if connection is not None:
            connection.disconnect()


@pytest.mark.parametrize("target", ["polars", "narwhals-polars", "narwhals-lazy", "ibis-duckdb"])
def test_remote_csv_multibyte_delimiter_retains_fallback(
    target, tmp_path, schema_resource_http_url,
):
    import mountainash as ma

    (tmp_path / "rows.csv").write_text("id|||||label\n11|||||first\n12|||||second\n")
    resource = ma.DataResource(name="rows", path=schema_resource_http_url, format="csv",
                               dialect={"delimiter": "|||||"})
    connection = None
    if target == "ibis-duckdb":
        import ibis

        connection = ibis.duckdb.connect()
    try:
        frame = _collect_pl(ma.ResourceRef(resource).relation().collect(target=connection or target))
        assert frame.to_dicts() == [{"id": 11, "label": "first"}, {"id": 12, "label": "second"}]
    finally:
        if connection is not None:
            connection.disconnect()


def test_csv_default_delimiter_is_not_autodetected(backend_ext, tmp_path):
    path = tmp_path / "rows.csv"
    path.write_text("left;right\nnorth;south\n")
    resource = DataResource(name="rows", path=str(path), format="csv")
    assert _to_dict_list(backend_ext.read_resource(resource)) == [{"left;right": "north;south"}]
