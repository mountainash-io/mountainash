### Task 8 (mountainash): `ResourceRef`, descriptor references, one resolver, `core/io`

**Files:**
- Modify: `core/resource_ref.py:38-50`, `core/io.py` (`is_remote` uses `mountainash_transport.location.identify_scheme`, fallback list deleted; `facade_read_bytes(path, policy=None)`), `typespec/descriptor_context.py` (merge `LocalDescriptorResolver`/`StorageDescriptorResolver` into one default resolver; `resolve()` receives the context policy; delete `_local_path_from_uri` in favour of transport `local_path`; replace `DescriptorReferenceSchemeDenied` with `LocationNotAllowed`), `typespec/frictionless_resolution.py:78-125` (pass `context.policy`), `typespec/errors.py` (remove `DescriptorReferenceSchemeDenied`), `typespec/__init__.py:72,165` (exports), `docs/reference/datapackage.md:247-270`, `docs/website/features-technical/typespec-conform.md:608-617` (correct the inaccurate facade claim and the `from_descriptor("datapackage.json")` example).
- Tests: `tests/core/test_resource_ref_policy.py`, `tests/typespec/test_descriptor_reference_policy.py` (new); migrate `tests/typespec/test_descriptor_context.py:227-264` (resolver tests) and `tests/core/test_io.py:11-77`.

**Interfaces:**
- Produces: `facade_read_bytes(path: str, policy: LocationPolicy | None = None) -> bytes`.
- `DescriptorResolver.resolve(reference, *, base_uri, expected_kind, policy=None)`. Custom resolvers are caller code; they receive `policy` and may ignore it (threat model).

- [ ] **Step 1: Failing tests.**

```python
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
```

```python
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
```

  Migrate `tests/typespec/test_descriptor_context.py:227-264`, which constructs `StorageDescriptorResolver(allowed_schemes=...)`, to `policy=LocationPolicy(allowed_remote={<scheme>: frozenset()})` on the loader, keeping each test's assertion. Migrate `tests/core/test_io.py:11-30` (remote classification) unchanged except for deleting the fallback-prefix cases, which are obsolete with the list removed.
- [ ] **Step 2: Run** both files → FAIL.
- [ ] **Step 3: Implement.**
  - **`ResourceRef.read_bytes`.**
    1. `p = resolve_resource_location(resource, path)`; `pol = resource_policy(resource)`.
    2. Local: `confine_local(p, pol)`, then `Path(...).read_bytes()`.
    3. Remote: `facade_read_bytes(p, pol)`, which calls `StorageFacade.from_path(p, policy=pol).read(p)`.
  - **Resolver.**
    - One `DefaultDescriptorResolver`. `normalize_document_uri` is kept as the join step with its existing errors.
    - A local result goes through `confine_local(local_path(normalized), policy)` and `read_bytes`.
    - A remote result goes through `facade_read_bytes(normalized, policy)`.
    - With `policy` `None` (programmatic, no base), today's behaviour: local reads allowed, and **remote denied as today** (the old default resolver denied non-file schemes). Keep that denial as `LocationNotAllowed(reference, "remote not allowed")`.
  - Delete `StorageDescriptorResolver`, `LocalDescriptorResolver` and `_local_path_from_uri`. Update exports, docs and tests.
- [ ] **Step 4: Run** `tests/core tests/typespec` → PASS.
- [ ] **Step 5: Commit** `feat(typespec)!: references and ResourceRef obey LocationPolicy; one descriptor resolver (381)`.

