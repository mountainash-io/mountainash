# tests/typespec/test_descriptor_reference_policy.py
import json, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import pytest
import mountainash as ma
from mountainash_transport.location import LocationNotAllowed, LocationPolicy

SCHEMA = {"fields": [{"name": "v", "type": "integer"}]}

@pytest.fixture
def layout(tmp_path):
    root = tmp_path / "root"; out = tmp_path / "out"; root.mkdir(); out.mkdir()
    (root / "schema.json").write_text(json.dumps(SCHEMA)); (out / "schema.json").write_text(json.dumps(SCHEMA))
    hits = {"n": 0}
    class H(SimpleHTTPRequestHandler):
        def do_GET(self):
            hits["n"] += 1; super().do_GET()
        def log_message(self, *a): pass
    s = ThreadingHTTPServer(("127.0.0.1", 0), partial(H, directory=str(out)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield root, out, s.server_address[1], hits
    s.shutdown()

def _pkg(root, schema_ref, **kw):
    p = root / "datapackage.json"
    p.write_text(json.dumps({"name": "p", "resources": [{"name": "r", "path": "a.csv", "schema": schema_ref}]}))
    return ma.DataPackage.from_path(p, **kw)

def test_in_root_reference_resolves(layout):
    root, *_ = layout
    assert _pkg(root, "schema.json").resources[0].to_table_schema()

def test_absolute_outside_reference_rejected(layout):
    root, out, *_ = layout
    with pytest.raises(LocationNotAllowed):
        _pkg(root, str(out / "schema.json")).resources[0].to_table_schema()

def test_remote_reference_needs_allow_list(layout):
    root, _, port, hits = layout
    url = f"http://127.0.0.1:{port}/schema.json"
    with pytest.raises(LocationNotAllowed):
        _pkg(root, url).resources[0].to_table_schema()
    assert hits["n"] == 0
    pol = LocationPolicy(allowed_remote={"http": frozenset({"127.0.0.1"})})
    assert _pkg(root, url, policy=pol).resources[0].to_table_schema()

def test_remote_base_relative_reference_needs_allow_list(layout, monkeypatch):
    root, _, port, hits = layout
    monkeypatch.chdir(root)
    raw = {"name": "p", "resources": [{"name": "r", "path": "a.csv", "schema": "schema.json"}]}
    pkg = ma.DataPackage.from_descriptor(raw, base_uri=f"http://127.0.0.1:{port}/")
    with pytest.raises(LocationNotAllowed):
        pkg.resources[0].to_table_schema()
    assert hits["n"] == 0

def test_dotdot_reference_escaping_root_rejected(layout):
    root, *_ = layout
    with pytest.raises(LocationNotAllowed):          # spec: a valid reference that escapes the root
        _pkg(root, "../out/schema.json").resources[0].to_table_schema()

def test_dialect_reference_obeys_policy(layout):
    root, out, port, hits = layout
    (root / "dialect.json").write_text(json.dumps({"delimiter": ";"})); (out / "dialect.json").write_text(json.dumps({"delimiter": ";"}))
    def pkg(ref):
        p = root / "datapackage.json"
        p.write_text(json.dumps({"name": "p", "resources": [{"name": "r", "path": "a.csv", "dialect": ref}]}))
        return ma.DataPackage.from_path(p)
    assert pkg("dialect.json").resources[0].to_dialect()
    with pytest.raises(LocationNotAllowed): pkg(str(out / "dialect.json")).resources[0].to_dialect()
    with pytest.raises(LocationNotAllowed): pkg(f"http://127.0.0.1:{port}/dialect.json").resources[0].to_dialect()
    assert hits["n"] == 0


def test_unknown_scheme_reference_rejected(layout):
    root, *_ = layout
    with pytest.raises(LocationNotAllowed, match="unknown scheme"):
        _pkg(root, "hf://host/schema.json").resources[0].to_table_schema()
