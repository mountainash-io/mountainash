### Task 4 (transport): remote providers — S3/SFTP host rules, HTTP send-loop check

**Files:** Modify `storage/facade/facade.py` (`_check`, constructor engine wiring), `_core/http/engine.py:161-170,236-245`, `storage/backends/http/__init__.py:45-54`. Tests: `tests/storage/facade/test_facade_remote_policy.py` (new), `tests/_core/http/test_redirects.py` (add cases).

**Interfaces:**
- Produces: `HttpRequestEngine(client, policy=None, auth_strategy=None, *, location_check: Callable[[str], None] | None = None)`. The HTTP backend constructor accepts `location_check` and passes it to the engine.
- Consumes: Task 3 `_check`, `_profile_host`.

- [ ] **Step 1: Failing tests.**

```python
# test_facade_remote_policy.py
import threading
from functools import partial
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
import pytest
from mountainash_transport import StorageFacade
from mountainash_transport.location import LocationNotAllowed, LocationPolicy

@pytest.fixture
def servers(tmp_path):
    (tmp_path / "s.csv").write_bytes(b"v\n1\n")
    target = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(tmp_path)))
    hits = {"target": 0}
    class H(SimpleHTTPRequestHandler):
        def do_GET(self):
            hits["target"] += 1; super().do_GET()
    target.RequestHandlerClass = partial(H, directory=str(tmp_path))
    tport = target.server_address[1]
    class R(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302); self.send_header("Location", f"http://127.0.0.1:{tport}/s.csv"); self.end_headers()
        def log_message(self, *a): pass
    redirector = ThreadingHTTPServer(("localhost", 0), R)
    for s in (target, redirector): threading.Thread(target=s.serve_forever, daemon=True).start()
    yield tport, redirector.server_address[1], hits
    target.shutdown(); redirector.shutdown()

def test_http_rejected_without_allow_list(servers):
    tport, _, hits = servers
    url = f"http://127.0.0.1:{tport}/s.csv"
    with pytest.raises(LocationNotAllowed): StorageFacade.from_path(url, policy=LocationPolicy()).read(url)
    assert hits["target"] == 0

def test_http_allowed_by_allow_list(servers):
    tport, _, _ = servers
    url = f"http://127.0.0.1:{tport}/s.csv"
    pol = LocationPolicy(allowed_remote={"http": frozenset({"127.0.0.1"})})
    assert StorageFacade.from_path(url, policy=pol).read(url) == b"v\n1\n"

def test_redirect_to_disallowed_host_rejected_before_second_send(servers):
    _, rport, hits = servers
    url = f"http://localhost:{rport}/x"
    pol = LocationPolicy(allowed_remote={"http": frozenset({"localhost"})})
    with pytest.raises(LocationNotAllowed): StorageFacade.from_path(url, policy=pol).read(url)
    assert hits["target"] == 0

def test_http_no_policy_is_today(servers):
    tport, _, _ = servers
    url = f"http://127.0.0.1:{tport}/s.csv"
    assert StorageFacade.from_path(url).read(url) == b"v\n1\n"

@pytest.fixture
def fake_backend(monkeypatch):
    """Record backend calls; no SDK or network. Patches the two seams the facade constructor uses."""
    import io
    from mountainash_transport.storage.facade import facade as facade_mod
    calls = []
    class Conn:
        def connect(self): pass
        def close(self): pass
    class Backend:
        storage_profile = None
        def read_to_bytes(self, path): calls.append(("read", path)); return b"x"
        def read_to_stream(self, path): calls.append(("read", path)); return io.BytesIO(b"x")
        def write_from_bytes(self, path, data, create_parents=True): calls.append(("write", path))
        def write_from_stream(self, path, stream, create_parents=True): calls.append(("write", path))
        def copy(self, src, dst): calls.append(("copy", src, dst))
    monkeypatch.setattr("mountainash_transport.connections.create_connection", lambda *a, **k: Conn())
    monkeypatch.setattr(facade_mod, "get_storage_backend", lambda *a, **k: Backend())
    return calls

def _s3(bucket):
    from mountainash_transport.settings.storage.profiles import S3StorageProfile
    # Construct with the minimal required fields used in tests/settings/storage/profiles (REGION etc.), plus BUCKET.
    return S3StorageProfile(**_S3_MINIMAL, BUCKET=bucket)

def _sftp(host):
    from mountainash_transport.settings.storage.profiles import SFTPStorageProfile
    return SFTPStorageProfile(**_SFTP_MINIMAL, HOST=host)

def test_s3_profile_bucket_permits_own_bucket_only(fake_backend):
    fac = StorageFacade.from_path("s3://bucket-a/k", _s3("bucket-a"), policy=LocationPolicy())
    fac.read("s3://bucket-a/k"); fac.read("bucket-a/k")
    with pytest.raises(LocationNotAllowed): fac.read("s3://bucket-b/k")
    assert [c[1] for c in fake_backend] == ["s3://bucket-a/k", "bucket-a/k"]

def test_s3_profile_without_bucket_permits_any_bucket(fake_backend):
    fac = StorageFacade.from_path("s3://x/k", _s3(None), policy=LocationPolicy())
    fac.read("s3://any-bucket/k")
    assert fake_backend == [("read", "s3://any-bucket/k")]

def test_s3_without_profile_needs_allow_list(fake_backend):
    with pytest.raises(LocationNotAllowed):
        StorageFacade.from_path("s3://b/k", policy=LocationPolicy()).read("s3://b/k")
    assert fake_backend == []

def test_sftp_url_host_must_match_profile(fake_backend):
    fac = StorageFacade.from_path("sftp://host-a/p", _sftp("host-a"), policy=LocationPolicy())
    fac.read("/remote/p")
    with pytest.raises(LocationNotAllowed): fac.read("sftp://host-b/p")

def test_equal_policies_different_s3_profiles_use_stream_branch(fake_backend):
    from mountainash_transport import copy_between
    pol = LocationPolicy()
    src = StorageFacade.from_path("s3://a/k", _s3("a"), policy=pol)
    dst = StorageFacade.from_path("s3://b/k", _s3("b"), policy=pol)
    copy_between("s3://a/k", "s3://b/k", src, dst)
    assert ("copy", "s3://a/k", "s3://b/k") not in fake_backend
    assert ("write", "s3://b/k") in fake_backend

def test_unknown_scheme_rejected_before_provider_detection():
    with pytest.raises(LocationNotAllowed) as e:
        StorageFacade.from_path("hf://user:secret@host/x", policy=LocationPolicy())
    assert "secret" not in str(e.value)

@pytest.mark.parametrize("bucket", ["bucket-a", None])
def test_unknown_scheme_rejected_at_operation_time(fake_backend, bucket):
    fac = StorageFacade.from_path("s3://bucket-a/k", _s3(bucket), policy=LocationPolicy())
    with pytest.raises(LocationNotAllowed) as e: fac.read("hf://user:secret@host/x")
    assert "secret" not in str(e.value) and fake_backend == []
```

  Define `_S3_MINIMAL` and `_SFTP_MINIMAL` at the top of the file with the required fields used by `tests/settings/storage/profiles/test_s3*.py` and `test_sftp*.py`; copy them, don't invent values. If the fake-backend fixture's backend lacks a method the facade's `_require` protocol checks need, add the method, keeping the fake minimal.

  In `tests/_core/http/test_redirects.py`, add two engine-level cases using that file's existing mock-transport setup:

```python
def test_location_check_stops_redirect_before_second_send(...):
    sent = []
    # transport: first URL -> 302 to http://evil.example/x ; record every request in `sent`
    def check(url):
        if "evil.example" in url: raise LocationNotAllowed(url, "remote not allowed")
    engine = HttpRequestEngine(client, location_check=check)
    with pytest.raises(LocationNotAllowed): engine.request("GET", "http://good.example/a")
    assert [str(r.url) for r in sent] == ["http://good.example/a"]

def test_location_check_stops_auth_flow_request_to_other_host(...):
    class Hop(httpx.Auth):
        def auth_flow(self, request):
            response = yield request
            if response.status_code == 401:
                yield httpx.Request("GET", "http://evil.example/token")
    # transport: 401 for good.example ; engine built with auth_strategy/auth that applies Hop (follow the file's Digest test wiring)
    ...same assertion: LocationNotAllowed raised; only the first request was sent.
```

  Fill the `...` with the file's existing client/transport construction (see its Digest-authentication test around lines 206–226); the assertions above are the required ones.

- [ ] **Step 2: Run** both files → FAIL.
- [ ] **Step 3: Implement.**
  - **`_check` starts with `require_known_scheme(path, self._policy)`** for every provider, so an unknown scheme handed to an already-constructed facade is refused with the redacted error before any parser sees it.
  - **`_check` for remote providers:**
    - S3 family: if `self._profile_any`, allowed (any bucket at the supplied profile's endpoint). Otherwise `bucket, _ = parse_s3_path(path)` (existing parser, so bare and schemed forms both work) and `allow_remote(<canonical scheme of provider>, bucket.lower(), self._policy, profile_host=self._profile_host)`.
    - SFTP: if `identify_scheme(path) == "sftp"`, `allow_remote("sftp", url_host(path), …, profile_host=self._profile_host)`. Otherwise (a bare remote path) the target is the profile's own host, so no check is needed.
    - HTTP: `allow_remote(identify_scheme(path), url_host(path), self._policy)`.
    - Return `path` unchanged in all remote cases.
  - **Unknown schemes.** In `from_path`, call `require_known_scheme(path, policy)` **before** `detect_provider_from_path`, so an unknown scheme under a policy raises the redacted `LocationNotAllowed` instead of the existing `ValueError` that echoes the URL. Without a policy, today's `ValueError` is unchanged.
  - **Engine.** Add the `location_check` constructor keyword and store it. At the top of the `while True:` body in `_send_with_redirects`, before `self._client.send(...)`, add `if self._location_check is not None: self._location_check(str(request.url))`.
  - **Wiring.** The HTTP backend constructor gains `location_check=None` and forwards it. The facade passes `location_check=self._check` through `get_storage_backend(..., **backend_kwargs)` when the provider is HTTP and a policy is active. Construct the backend after `_policy` is set; reorder the constructor accordingly. No post-construction attribute patching.
- [ ] **Step 4: Run** the targeted files: `hatch run test:test-target-quick tests/storage/facade tests/_core/http` → PASS.
- [ ] **Step 5: Commit** `feat(facade): remote LocationPolicy for S3/SFTP/HTTP; check every HTTP send incl. redirects (381)`.
- [ ] **Step 6 (transport PR):** README section "Location policy" (the root, `allowed_remote`, profile permission incl. bucketless S3 profiles, `allow_unconfined`, `ROOT_PATH` now confines, `MOUNT_SPEC` removed, DNS-rebinding and managed-OAuth limits from the spec threat model). Bump `__version__` to `0.1.1` (the release carrying `mountainash_transport.location`; files and mountainash floors reference it). Run the full transport suite once (`hatch run test:test`), then open the PR to `develop` with the spec link and acceptance A/B evidence.

