"""Resource discovery evidence must describe output without executing the relation."""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import mountainash as ma
from mountainash.core.dtypes import ListDtype, MountainashDtype as D, TimestampDtype
from mountainash.exceptions import IncompleteSchemaError
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
from mountainash.relations.dag.errors import UnsupportedResourceFormat
from mountainash.typespec.datapackage import DataResource


def resource_relation(path, *, format, schema=None):
    return Relation(ResourceReadRelNode(resource=DataResource(
        name="rows", path=str(path), format=format, schema=schema,
    )))


def test_http_parquet_dag_preserves_recursive_types_without_row_loading(tmp_path, monkeypatch):
    path = tmp_path / "rows.parquet"
    pq.write_table(pa.table({
        "id": [1],
        "at": pa.array([0], type=pa.timestamp("us", "UTC")),
        "items": pa.array([[2, 3]], type=pa.list_(pa.int32())),
    }), path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(tmp_path)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        source = resource_relation(f"http://127.0.0.1:{server.server_port}/rows.parquet", format="parquet")
        dag = ma.RelationDAG()
        dag.add("source", source)
        query = dag.ref("source").select(ma.col("id").add(1).alias("next"), "at", "items")
        dag.add("output", query)
        expected = {
            "next": D.I64,
            "at": TimestampDtype(precision=6, timezone_aware=True, timezone="UTC"),
            "items": ListDtype(element=D.I32),
        }
        from mountainash.relations.backends.relation_systems import resource_files

        def forbid_rows(*args, **kwargs):
            raise AssertionError("schema inspection loaded resource rows")

        with monkeypatch.context() as guard:
            guard.setattr(resource_files, "parse_resource_to_arrow", forbid_rows)
            assert dag.schema("output") == expected
            assert query.collect_schema() == expected
            assert query.collect_schema(allow_execution=True) == expected
        assert query.to_dict()["next"] == [2]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("backend", ["polars", "narwhals"])
def test_resource_metadata_composes_with_selected_backend_and_conform(backend, tmp_path, monkeypatch):
    from mountainash.relations.core.execution.preparation import ExecutionPhase
    from mountainash.relations.backends.relation_systems import resource_files

    path = tmp_path / "rows.json"
    path.write_text('[{"id": 7, "amount": "2.5"}]')
    resource = resource_relation(path, format="json", schema={"fields": [
        {"name": "id", "type": "integer"}, {"name": "amount", "type": "number"},
    ]})

    def forbid_rows(*args, **kwargs):
        raise AssertionError("schema compilation loaded resource rows")

    # Resource-only public schema inspection chooses the default backend.
    # Exercise the compiler's existing explicit family selection independently,
    # without introducing a cross-backend row transfer into this schema test.
    with monkeypatch.context() as guard:
        guard.setattr(resource_files, "parse_resource_to_arrow", forbid_rows)
        native, visitor = resource._compile_and_execute_with_visitor(
            backend=backend, phase=ExecutionPhase.SCHEMA,
        )
        try:
            assert ma.relation(native).collect_schema() == {"id": D.I64, "amount": D.FP64}
        finally:
            visitor._execution_session.close(release_owned=True)
    assert ma.relation(resource.collect(backend=backend)).to_dict() == {"id": [7], "amount": [2.5]}


def test_resource_schema_observes_replacement(tmp_path):
    path = tmp_path / "rows.json"
    relation = resource_relation(path, format="json")
    path.write_text('[{"old": 1}]')
    assert relation.collect_schema() == {"old": D.I64}
    path.write_text('[{"new": "x"}]')
    assert relation.collect_schema() == {"new": D.STRING}


@pytest.mark.parametrize("allow_execution", [False, True])
def test_malformed_resource_is_not_an_execution_retry(tmp_path, monkeypatch, allow_execution):
    from mountainash.relations.backends.relation_systems import resource_files

    path = tmp_path / "rows.json"
    path.write_text("{invalid")
    relation = resource_relation(path, format="json")

    def forbid_retry(*args, **kwargs):
        raise AssertionError("malformed discovery was retried by parsing rows")

    monkeypatch.setattr(resource_files, "parse_resource_to_arrow", forbid_retry)
    with pytest.raises(UnsupportedResourceFormat):
        relation.collect_schema(allow_execution=allow_execution)


@pytest.mark.parametrize("discovery", ["bounded", "unsupported"])
@pytest.mark.parametrize("projection", ["none", "late", "late_conform", "resource_exact", "resource_subset"])
def test_plugin_evidence_requires_permission_without_losing_known_fields(tmp_path, monkeypatch, discovery, projection):
    from dataclasses import dataclass
    from typing import ClassVar
    import pyarrow.json as paj
    from mountainash_files import register_format
    from mountainash_files.formats import _registry
    from mountainash_files.formats._types import FormatSpec

    # Isolate registration without clearing plugins owned by another test.
    for name, value in tuple(vars(_registry).items()):
        if name.startswith("_") and isinstance(value, dict):
            monkeypatch.setattr(_registry, name, value.copy())
    monkeypatch.setattr(_registry, "_DISCOVERY_DONE", _registry._DISCOVERY_DONE)

    @dataclass(frozen=True)
    class ObservedSpec(FormatSpec):
        FORMAT: ClassVar[str] = "schema-observation-test"
        SUFFIXES: ClassVar[tuple[str, ...]] = (".observation",)

    def parser(data, spec):
        return paj.read_json(pa.BufferReader(data))

    def inspector(data, spec, *, infer_schema_rows=None):
        prefix = data.splitlines()[0] + b"\n"
        return paj.read_json(pa.BufferReader(prefix)).schema, "bounded"

    register_format(ObservedSpec, parser, schema_inspector=inspector if discovery == "bounded" else None)
    path = tmp_path / "rows.observation"
    path.write_text('{"id":1}\n{"id":2,"late":"value"}\n')
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    declared = None
    if projection.startswith("resource_"):
        fields = [FieldSpec(name="late", type=UniversalType.STRING)]
        if projection == "resource_exact":
            fields.insert(0, FieldSpec(name="id", type=UniversalType.INTEGER))
        declared = TypeSpec(fields=fields, fields_match=projection.removeprefix("resource_"))
    dag = ma.RelationDAG()
    dag.add("source", resource_relation(path, format=ObservedSpec.FORMAT, schema=declared))
    query = dag.ref("source")
    if declared is None:
        assert query.schema == ({"id": D.I64} if discovery == "bounded" else {})
    if projection in {"late", "late_conform"}:
        query = query.select("late")
        if projection == "late_conform":
            query = query.conform(TypeSpec(
                fields=[FieldSpec(name="late", type=UniversalType.STRING)],
                fields_match="open",
            ))
    with pytest.raises(IncompleteSchemaError):
        query.collect_schema()
    retains_id = projection in {"none", "resource_exact"}
    expected = {"id": D.I64, "late": D.STRING} if retains_id else {"late": D.STRING}
    assert query.collect_schema(allow_execution=True) == expected
    expected_rows = {"id": [1, 2], "late": [None, "value"]} if retains_id else {"late": [None, "value"]}
    assert query.to_dict() == expected_rows


def test_empty_file_resource_schema_matches_declared_reconstruction(tmp_path):
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    path = tmp_path / "empty.json"
    path.write_text("[]")
    relation = resource_relation(path, format="json", schema=TypeSpec(
        fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
        fields_match="open",
    ))
    assert relation.collect_schema() == {"id": D.I64}
    assert relation.select("id").collect_schema(allow_execution=True) == {"id": D.I64}
    assert relation.to_dict() == {"id": []}


@pytest.mark.parametrize("allow_execution", [False, True])
def test_complete_discovery_preserves_invalid_projection_error(tmp_path, allow_execution):
    import polars as pl

    path = tmp_path / "rows.json"
    path.write_text('[{"id": 1}]')
    relation = resource_relation(path, format="json").select("absent")
    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        relation.collect_schema(allow_execution=allow_execution)
