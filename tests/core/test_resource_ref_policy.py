# tests/core/test_resource_ref_policy.py
import json, threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import pytest
import mountainash as ma
from mountainash.core.resource_ref import ResourceRef
from mountainash_transport.location import LocationNotAllowed

def _pkg(root, path):
    p = root / "datapackage.json"
    p.write_text(json.dumps({"name": "p", "resources": [{"name": "r", "path": path, "format": "bin"}]}))
    return ma.DataPackage.from_path(p)

@pytest.fixture
def outside(tmp_path):
    d = tmp_path / "outside"; d.mkdir(); (d / "s.bin").write_bytes(b"secret"); return d

@pytest.fixture
def server(outside):
    hits = {"n": 0}
    class H(SimpleHTTPRequestHandler):
        def do_GET(self):
            hits["n"] += 1; super().do_GET()
        def log_message(self, *a): pass
    s = ThreadingHTTPServer(("127.0.0.1", 0), partial(H, directory=str(outside)))
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield s.server_address[1], hits
    s.shutdown()

def test_absolute_outside_rejected(tmp_path, outside):
    root = tmp_path / "root"; root.mkdir()
    with pytest.raises(LocationNotAllowed):
        ResourceRef(_pkg(root, str(outside / "s.bin")).resources[0]).read_bytes()

def test_in_root_relative_reads(tmp_path):
    root = tmp_path / "root"; root.mkdir(); (root / "a.bin").write_bytes(b"ok")
    assert ResourceRef(_pkg(root, "a.bin").resources[0]).read_bytes() == b"ok"

def test_remote_without_allow_rejected_before_request(tmp_path, server):
    port, hits = server
    root = tmp_path / "root"; root.mkdir()
    with pytest.raises(LocationNotAllowed):
        ResourceRef(_pkg(root, f"http://127.0.0.1:{port}/s.bin").resources[0]).read_bytes()
    assert hits["n"] == 0

def test_programmatic_absolute_is_today(outside):
    pkg = ma.DataPackage(name="p", resources=[{"name": "r", "path": str(outside / "s.bin"), "format": "bin"}])
    assert ResourceRef(pkg.resources[0]).read_bytes() == b"secret"
