"""Location confinement at the resource-reader seams, across all four targets."""
from __future__ import annotations

import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import ibis
import polars as pl
import pytest
from mountainash_transport.location import LocationNotAllowed, LocationPolicy

from mountainash.relations.core.execution.preparation import ExecutionPhase
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
from mountainash.typespec.datapackage import DataPackage, DataResource

TARGETS = ["polars", "narwhals", "ibis-duckdb", "ibis-polars"]


def _target(name):
    if name == "ibis-duckdb":
        return ibis.duckdb.connect()
    if name == "ibis-polars":
        return ibis.polars.connect()
    return name


@pytest.fixture(params=TARGETS)
def target_name(request):
    return request.param


def _values(native) -> list:
    if hasattr(native, "to_pyarrow") and not hasattr(native, "collect"):
        return sorted(pl.from_arrow(native.to_pyarrow())["v"].to_list())
    if hasattr(native, "collect"):
        native = native.collect()
    if hasattr(native, "to_native"):
        native = native.to_native()
    if isinstance(native, pl.DataFrame):
        return sorted(native["v"].to_list())
    return sorted(pl.from_arrow(native.to_arrow())["v"].to_list())


class _Handler(SimpleHTTPRequestHandler):
    hits: list = []

    def do_GET(self):
        type(self).hits.append(self.path)
        super().do_GET()

    def log_message(self, *a):
        pass


@pytest.fixture
def world(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.csv").write_text("v\n666\n")
    top = tmp_path / "top"
    root = top / "pkg[12]"
    (top / "pkg1").mkdir(parents=True)
    (top / "pkg2").mkdir()
    (root / "data").mkdir(parents=True)
    (root / "data" / "a.csv").write_text("v\n99\n")
    os.symlink(outside / "secret.csv", root / "data" / "link.csv")
    (root / "badtree").mkdir()
    (root / "badtree" / "ok.csv").write_text("v\n1\n")
    os.symlink(outside / "secret.csv", root / "badtree" / "leak.csv")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    hits: list = []
    handler = type("H", (_Handler,), {"hits": hits})
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(outside)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield {
            "tmp": tmp_path, "outside": outside, "root": root, "elsewhere": elsewhere,
            "port": server.server_port, "hits": hits,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _descriptor(path, fmt="csv"):
    return {"name": "pkg", "resources": [{
        "name": "r", "path": path, "format": fmt,
        "schema": {"fields": [{"name": "v", "type": "integer"}]},
    }]}


def _load_path(directory, descriptor, policy=None):
    (directory).mkdir(parents=True, exist_ok=True)
    (directory / "datapackage.json").write_text(json.dumps(descriptor))
    return DataPackage.from_path(directory / "datapackage.json", policy=policy)


def _collect(pkg, name):
    return _values(pkg.to_relation_dag().collect("r", target=_target(name)))


POLICIES = {
    None: None,
    "allow-127": lambda: LocationPolicy(allowed_remote={"http": frozenset({"127.0.0.1"})}),
    "allow-any-http": lambda: LocationPolicy(allowed_remote={"http": frozenset({"127.0.0.1"})}),
    "unconfined": lambda: LocationPolicy(allow_unconfined=True),
}

CASES = [
    ("in_root_glob_named_root", "data/a.csv", None, [99]),
    ("absolute_outside", "{outside}/secret.csv", None, "reject"),
    ("symlink_escape", "data/link.csv", None, "reject"),
    ("dir_with_escaping_entry", "badtree", None, "reject"),
    ("remote_no_allow", "http://127.0.0.1:{port}/secret.csv", None, "reject"),
    ("remote_allowed", "http://127.0.0.1:{port}/secret.csv", "allow-127", [666]),
    ("allow_list_only_keeps_root", "{outside}/secret.csv", "allow-any-http", "reject"),
    ("unknown_scheme", "hf://x/y.csv", None, "reject"),
    ("opt_out", "{outside}/secret.csv", "unconfined", [666]),
    ("remote_base_relative_resource", "<base_uri=http://127.0.0.1:{port}/> secret.csv", None, "reject"),
    ("remote_base_absolute_local", "<base_uri=http://127.0.0.1:{port}/> {outside}/secret.csv", None, "reject"),
]


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_read_confinement(case, target_name, world, monkeypatch):
    _id, spec, pol_key, expected = case
    factory = POLICIES[pol_key]
    policy = factory() if factory else None
    base = None
    if spec.startswith("<base_uri="):
        base, spec = spec[len("<base_uri="):].split("> ", 1)
        base = base.format(**world)
    path = spec.format(outside=world["outside"], port=world["port"])
    if base is not None:
        monkeypatch.chdir(world["elsewhere"])
        pkg = DataPackage.from_descriptor(_descriptor(path), base_uri=base, policy=policy)
    else:
        pkg = _load_path(world["root"], _descriptor(path), policy)
    if expected == "reject":
        with pytest.raises(LocationNotAllowed):
            _collect(pkg, target_name)
        assert world["hits"] == []
    else:
        assert _collect(pkg, target_name) == expected


def test_plain_root_directory_reads_natively(target_name, tmp_path):
    root = tmp_path / "plainroot"
    (root / "tree" / "sub").mkdir(parents=True)
    (root / "tree" / "x.csv").write_text("v\n7\n")
    (root / "tree" / "sub" / "y.csv").write_text("v\n8\n")
    pkg = _load_path(root, _descriptor("tree"))
    if target_name == "ibis-polars":
        with pytest.raises(LocationNotAllowed):
            _collect(pkg, target_name)
    else:
        assert _collect(pkg, target_name) == [7, 8]


def test_glob_named_root_directory_on_ibis_duckdb_rejected(world):
    (world["root"] / "tree").mkdir()
    (world["root"] / "tree" / "x.csv").write_text("v\n7\n")
    pkg = _load_path(world["root"], _descriptor("tree"))
    with pytest.raises(LocationNotAllowed):
        _collect(pkg, "ibis-duckdb")


@pytest.mark.parametrize("opt_out", [False, True], ids=["policy", "opt-out"])
def test_literal_percent_filename(target_name, tmp_path, opt_out):
    root = tmp_path / "pct"
    root.mkdir()
    (root / "report%20a.csv").write_text("v\n1\n")
    (root / "report a.csv").write_text("v\n2\n")
    policy = LocationPolicy(allow_unconfined=True) if opt_out else None
    pkg = _load_path(root, _descriptor("report%20a.csv"), policy)
    assert _collect(pkg, target_name) == [1]


def test_path_assigned_after_load_is_confined(target_name, world):
    pkg = _load_path(world["root"], _descriptor("data/a.csv"))
    assert _collect(pkg, target_name) == [99]
    pkg.resources[0].path = str(world["outside"] / "secret.csv")
    with pytest.raises(LocationNotAllowed):
        _collect(pkg, target_name)


def test_opt_out_reads_relative_to_descriptor_not_cwd(target_name, tmp_path, monkeypatch):
    d = tmp_path / "d"
    d.mkdir()
    (d / "a.csv").write_text("v\n5\n")
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    (cwd / "a.csv").write_text("v\n6\n")
    pkg = _load_path(d, _descriptor("a.csv"), LocationPolicy(allow_unconfined=True))
    monkeypatch.chdir(cwd)
    assert _collect(pkg, target_name) == [5]


def test_opt_out_remote_base_relative_resource_takes_fallback(target_name, world, monkeypatch):
    monkeypatch.chdir(world["elsewhere"])
    (world["elsewhere"] / "secret.csv").write_text("v\n1\n")
    pkg = DataPackage.from_descriptor(
        _descriptor("secret.csv"),
        base_uri=f"http://127.0.0.1:{world['port']}/",
        policy=LocationPolicy(allow_unconfined=True),
    )
    assert _collect(pkg, target_name) == [666]


def _schema_relation(resource):
    return Relation(ResourceReadRelNode(resource=resource))


def test_schema_phase_rejects_outside_and_reads_inside(target_name, world, monkeypatch):
    # SCHEMA execution takes a backend name; an Ibis flavour is the default backend.
    if target_name.startswith("ibis-"):
        monkeypatch.setattr(ibis.options, "default_backend", getattr(ibis, target_name[5:]).connect())
    target = "ibis" if target_name.startswith("ibis-") else target_name
    inside = _load_path(world["root"], _descriptor("data/a.csv"))
    outside = _load_path(world["root"] / "o", _descriptor(str(world["outside"] / "secret.csv")))
    _native, visitor = _schema_relation(inside.resources[0])._compile_and_execute_with_visitor(
        target=target, phase=ExecutionPhase.SCHEMA)
    visitor._execution_session.close(release_owned=True)
    with pytest.raises(LocationNotAllowed):
        _schema_relation(outside.resources[0])._compile_and_execute_with_visitor(
            target=target, phase=ExecutionPhase.SCHEMA)


def test_programmatic_absolute_path_is_today(target_name, world):
    res = DataResource(name="r", path=str(world["outside"] / "secret.csv"), format="csv")
    pkg = DataPackage(name="pkg", resources=[res])
    assert _collect(pkg, target_name) == [666]
