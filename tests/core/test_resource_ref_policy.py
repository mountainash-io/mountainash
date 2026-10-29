# tests/core/test_resource_ref_policy.py
import json, threading
from http.server import BaseHTTPRequestHandler
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import pytest
import mountainash as ma
from mountainash.core.resource_ref import ResourceRef
from mountainash_transport.location import POLICY_UNSET, LocationNotAllowed, LocationPolicy

def _pkg(root, path, *, policy=POLICY_UNSET):
    p = root / "datapackage.json"
    p.write_text(json.dumps({"name": "p", "resources": [{"name": "r", "path": path, "format": "bin"}]}))
    return ma.DataPackage.from_path(p, policy=policy)

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
        ResourceRef(_pkg(root, str(outside / "s.bin"), policy=LocationPolicy()).resources[0]).read_bytes()

def test_in_root_relative_reads(tmp_path):
    root = tmp_path / "root"; root.mkdir(); (root / "a.bin").write_bytes(b"ok")
    assert ResourceRef(_pkg(root, "a.bin").resources[0]).read_bytes() == b"ok"

def test_remote_without_allow_rejected_before_request(tmp_path, server):
    port, hits = server
    root = tmp_path / "root"; root.mkdir()
    with pytest.raises(LocationNotAllowed):
        ResourceRef(_pkg(root, f"http://127.0.0.1:{port}/s.bin", policy=LocationPolicy()).resources[0]).read_bytes()
    assert hits["n"] == 0

def test_programmatic_absolute_is_today(outside):
    pkg = ma.DataPackage(name="p", resources=[{"name": "r", "path": str(outside / "s.bin"), "format": "bin"}])
    assert ResourceRef(pkg.resources[0]).read_bytes() == b"secret"


def test_unknown_scheme_rejected_under_policy(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    with pytest.raises(LocationNotAllowed, match="unknown scheme"):
        ResourceRef(_pkg(root, "hf://host/data.bin", policy=LocationPolicy()).resources[0]).read_bytes()


# --- bound storage binding: profile headers/policy reach the byte read ------------------

_BODIES = {"alpha": b"alpha-bytes", "beta": b"beta-bytes"}


@pytest.fixture
def token_server():
    """Loopback server whose bytes depend on a profile header or bearer credential."""
    seen: list = []

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            token = self.headers.get("X-Token") or self.headers.get("Authorization", "").removeprefix("Bearer ")
            seen.append(token)
            body = _BODIES.get(token)
            self.send_response(200 if body is not None else 403)
            self.end_headers()
            self.wfile.write(body or b"denied")

        def log_message(self, *a):
            pass

    s = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield s.server_address[1], seen
    s.shutdown()
    s.server_close()


def _http_profile(token, **extra):
    from mountainash_transport.settings.storage.profiles import HTTPStorageProfile

    return HTTPStorageProfile(HEADERS={"X-Token": token}, **extra)


def _remote_pkg(port, **load):
    raw = {"name": "p", "resources": [{"name": "r", "path": f"http://127.0.0.1:{port}/x.bin", "format": "bin"}]}
    return ma.DataPackage.from_descriptor(raw, **load)


def test_bound_profile_headers_select_remote_bytes(token_server):
    port, seen = token_server
    pkg = _remote_pkg(port)
    alpha = pkg.with_storage(_http_profile("alpha"))
    beta = pkg.with_storage(_http_profile("beta"))
    assert ResourceRef(alpha.resources[0]).read_bytes() == b"alpha-bytes"
    assert ResourceRef(beta.resources[0]).read_bytes() == b"beta-bytes"
    assert seen == ["alpha", "beta"]


def test_inherited_profile_denial_versus_explicit_none(token_server):
    port, seen = token_server
    profile = _http_profile("alpha", LOCATION_POLICY={})
    inherited = _remote_pkg(port).with_storage(profile)
    with pytest.raises(LocationNotAllowed):
        ResourceRef(inherited.resources[0]).read_bytes()
    assert seen == []
    explicit_off = _remote_pkg(port, policy=None).with_storage(profile)
    assert ResourceRef(explicit_off.resources[0]).read_bytes() == b"alpha-bytes"


def test_local_reads_never_construct_a_remote_client(tmp_path, monkeypatch):
    from mountainash_transport.storage.facade.facade import StorageFacade

    (tmp_path / "a.bin").write_bytes(b"local")

    def forbidden(cls, *args, **kwargs):
        raise AssertionError("local read constructed a storage facade")

    monkeypatch.setattr(StorageFacade, "from_path", classmethod(forbidden))
    raw = {"name": "p", "resources": [{"name": "r", "path": "a.bin", "format": "bin"}]}
    pkg = ma.DataPackage.from_descriptor(raw, base_uri=str(tmp_path)).with_storage(_http_profile("alpha"))
    assert ResourceRef(pkg.resources[0]).read_bytes() == b"local"
    absolute = ma.DataPackage(name="p", resources=[
        {"name": "r", "path": str(tmp_path / "a.bin"), "format": "bin"},
    ]).with_storage(_http_profile("alpha"))
    assert ResourceRef(absolute.resources[0]).read_bytes() == b"local"


@pytest.mark.parametrize("token", ["alpha", "unknown"], ids=["success", "http-error"])
def test_read_bytes_closes_its_owned_facade(token_server, monkeypatch, token):
    from mountainash_transport.storage.facade.facade import StorageFacade
    from mountainash_transport import PermissionDeniedError

    port, _ = token_server
    closes: list = []
    original = StorageFacade.close

    def counting_close(self):
        closes.append(self)
        return original(self)

    monkeypatch.setattr(StorageFacade, "close", counting_close)
    pkg = _remote_pkg(port).with_storage(_http_profile(token))
    if token == "alpha":
        assert ResourceRef(pkg.resources[0]).read_bytes() == b"alpha-bytes"
    else:
        with pytest.raises(PermissionDeniedError):
            ResourceRef(pkg.resources[0]).read_bytes()
    assert len(closes) == 1 and closes[0]._closed


def test_named_auth_and_explicit_replacement_choose_actual_bytes(token_server, tmp_path, monkeypatch):
    from mountainash_auth_client import NoAuthProfile, TokenAuthProfile
    from mountainash_transport import PermissionDeniedError

    config = tmp_path / "profiles.yaml"
    config.write_text("""
storage_profiles:
  http-store:
    provider: http
    auth:
      mode: token
      parameters:
        TOKEN: alpha
""")
    monkeypatch.setenv("MOUNTAINASH_PROFILES_CONFIG", str(config))
    port, seen = token_server
    original = _remote_pkg(port)
    named = original.with_storage("http-store")
    replaced = original.with_storage("http-store", auth_profile=TokenAuthProfile(TOKEN="beta"))
    noauth = original.with_storage("http-store", auth_profile=NoAuthProfile())
    assert ResourceRef(named.resources[0]).read_bytes() == b"alpha-bytes"
    assert ResourceRef(replaced.resources[0]).read_bytes() == b"beta-bytes"
    with pytest.raises(PermissionDeniedError):
        ResourceRef(noauth.resources[0]).read_bytes()
    assert seen == ["alpha", "beta", ""]
    assert named.to_descriptor() == replaced.to_descriptor() == original.to_descriptor()
