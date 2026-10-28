### Task 6 (mountainash): dependency, policy carriage, loaders, base joining, context retention

**Files:**
- Modify: `pyproject.toml` (move `mountainash-transport` to `dependencies` with floor `>=0.1.1,<0.2`, delete the `storage` extra, add `mountainash-files>=0.1.1,<0.2` to `ibis`, and raise every other `mountainash-files` floor in the extras (`files`, `s3`, `gcs`, `azure`, `sftp`) to `>=0.1.1`; update `all`), `hatch.toml` envs that reference the `storage` extra. These floors are the transport/files releases from Tasks 4 and 5; Task 9 qualifies against installed builds of them, not editable worktrees.
- Modify: `typespec/descriptor_context.py` (`DescriptorContext.policy`, `build_descriptor_context(policy=)`, `loader_policy`), `typespec/frictionless_codec.py:420-456` (loaders), `typespec/datapackage.py` (`from_descriptor`/`from_json`/`from_path` gain `policy=`; `DataResource.model_copy`, `DataResource.model_validate`/`model_validate_json` on a bound instance, `DataPackage.model_validate` on a bound instance), `__init__.py:90-143` (`datacontract` passes the root).
- Create: `src/mountainash/core/location.py` with `resource_policy(resource)` and `resolve_resource_location(resource, path) -> str` (base joining).
- Test: `tests/typespec/test_location_policy_context.py` (new).

**Interfaces — Produces:**
```python
# typespec/descriptor_context.py
@dataclass(frozen=True)
class DescriptorContext: base_uri: str | None; resolver: DescriptorResolver; package_sources: tuple[...]; policy: LocationPolicy | None = None
def build_descriptor_context(*, base_uri=None, resolver=None, package_sources=(), policy=None) -> DescriptorContext
def loader_policy(base_uri: str | Path | None, policy: LocationPolicy | None) -> LocationPolicy
# DataPackage.from_path(path, *, resolver=None, policy=None); from_json(text, *, base_uri=None, resolver=None, policy=None); from_descriptor(raw, *, base_uri=None, resolver=None, policy=None)
# core/location.py
def resource_policy(resource) -> LocationPolicy | None                 # active policy or None
def resolve_resource_location(resource, path: str) -> str              # base-joined, not yet confined
```

- [ ] **Step 1: Failing tests.**

```python
import json, os
import pytest
import mountainash as ma
from mountainash.core.location import resolve_resource_location, resource_policy
from mountainash_transport.location import LocationPolicy

def _pkg(root, path):
    p = root / "datapackage.json"
    p.write_text(json.dumps({"name": "p", "resources": [{"name": "r", "path": path}]}))
    return p

def test_from_path_roots_at_descriptor_dir(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"))
    assert os.path.realpath(resource_policy(pkg.resources[0]).root) == os.path.realpath(tmp_path)

def test_allow_list_only_policy_keeps_descriptor_root(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), policy=LocationPolicy(allowed_remote={"https": frozenset()}))
    pol = resource_policy(pkg.resources[0])
    assert os.path.realpath(pol.root) == os.path.realpath(tmp_path) and pol.allowed_remote

def test_from_json_without_base_roots_at_load_time_cwd(tmp_path, monkeypatch):
    a = tmp_path / "a"; b = tmp_path / "b"; a.mkdir(); b.mkdir()
    monkeypatch.chdir(a)
    pkg = ma.DataPackage.from_json(json.dumps({"name": "p", "resources": [{"name": "r", "path": "x.csv"}]}))
    monkeypatch.chdir(b)                                   # a later chdir must not move the root or base
    assert os.path.realpath(resource_policy(pkg.resources[0]).root) == os.path.realpath(a)
    assert resolve_resource_location(pkg.resources[0], "x.csv") == os.path.join(os.path.realpath(a), "x.csv")

@pytest.mark.parametrize("base", ["https://host.example/pkg/", "s3://bucket/pkg/"])
def test_remote_base_grants_no_permission_and_roots_at_cwd(tmp_path, monkeypatch, base):
    monkeypatch.chdir(tmp_path)
    pkg = ma.DataPackage.from_json(json.dumps({"name": "p", "resources": [{"name": "r", "path": "d/a.csv"}]}),
                                   base_uri=base)
    pol = resource_policy(pkg.resources[0])
    assert pol.allowed_remote == {} and os.path.realpath(pol.root) == os.path.realpath(tmp_path)
    assert resolve_resource_location(pkg.resources[0], "d/a.csv") == base + "d/a.csv"

def test_bare_path_joined_literally(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "report%20a.csv"))
    assert resolve_resource_location(pkg.resources[0], "report%20a.csv").endswith("report%20a.csv")

def test_programmatic_package_has_no_policy():
    pkg = ma.DataPackage(name="p", resources=[{"name": "r", "path": "/abs/a.csv"}])
    assert resource_policy(pkg.resources[0]) is None

def test_opt_out_is_inactive(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), policy=LocationPolicy(allow_unconfined=True))
    assert resource_policy(pkg.resources[0]) is None

@pytest.mark.parametrize("op", ["model_copy", "resource_validate", "package_validate"])
def test_policy_survives_copy_and_revalidation(tmp_path, op):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"))
    original = resource_policy(pkg.resources[0])
    r = pkg.resources[0]
    if op == "model_copy": r = r.model_copy(update={"name": "r2"})
    if op == "resource_validate": r = type(r).model_validate(r)
    if op == "package_validate": r = type(pkg).model_validate(pkg).resources[0]
    assert resource_policy(r) == original and resource_policy(r).root is not None

def test_opt_out_still_resolves_relative_to_descriptor(tmp_path, monkeypatch):
    d = tmp_path / "desc"; d.mkdir(); monkeypatch.chdir(tmp_path)
    pkg = ma.DataPackage.from_path(_pkg(d, "a.csv"), policy=LocationPolicy(allow_unconfined=True))
    assert resolve_resource_location(pkg.resources[0], "a.csv") == os.path.join(os.path.realpath(d), "a.csv")

def test_descriptor_round_trip_unchanged(tmp_path):
    p = _pkg(tmp_path, "report%20a.csv")
    assert ma.DataPackage.from_path(p).to_descriptor()["resources"][0]["path"] == "report%20a.csv"
```

- [ ] **Step 2: Run** `hatch run test:test-target-quick tests/typespec/test_location_policy_context.py` → FAIL.
- [ ] **Step 3: Implement.**
  - **Dependencies.** Update `pyproject.toml`/`hatch.toml` per Global constraints.
  - **`DescriptorContext`.** Add `policy: LocationPolicy | None = None` (import under `TYPE_CHECKING`). `build_descriptor_context(..., policy=None)` stores it.
  - **`loader_policy(base_uri, policy)`:**
    - `declared` = `local_path(str(base_uri))` when the base is local (`identify_scheme in ("", "file")`), else `os.getcwd()`.
    - Return `(policy or LocationPolicy()).with_declared_root(declared)`.
  - **Base URI for loaders without one.** When `base_uri` is `None`, loaders store the captured working directory as the context `base_uri` as well (decision 4, R3-A4). `from_path` already passes the descriptor directory.
  - **Loaders.** `decode_package_descriptor/json/path` take `policy=` and build the context with `policy=loader_policy(base_uri_or_cwd, policy)`. `DataPackage.from_*` forward `policy=`.
  - **Context retention.**
    - `DataResource.model_copy` sets `result._descriptor_context = self._descriptor_context` on the copy.
    - `DataResource.model_validate` / `model_validate_json`: when the input is a `DataResource` instance, keep its `_descriptor_context` instead of `_default_descriptor_context()`.
    - `DataPackage.model_validate` with a `DataPackage` instance: pass the instance's context into `_prepare_package_input` **before** resource finalization, so `_bind_resource` binds to it.
  - **`core/location.py`:**

```python
def resource_policy(resource):
    ctx = getattr(resource, "_descriptor_context", None)
    pol = getattr(ctx, "policy", None)
    return pol if pol is not None and pol.active else None

def resolve_resource_location(resource, path: str) -> str:
    """Join a resource path to its descriptor base (spec §5): bare paths literally, URIs hierarchically.

    Applies whether or not confinement is active: opting out of confinement does not opt out of
    descriptor-relative resolution."""
    import posixpath
    from urllib.parse import urlsplit, urlunsplit
    from mountainash_transport.location import identify_scheme, local_path
    ctx = getattr(resource, "_descriptor_context", None)
    base = getattr(ctx, "base_uri", None)
    if base is None or identify_scheme(path) != "" or os.path.isabs(path):
        return path                                    # programmatic, URI, file: URI, or absolute
    if identify_scheme(base) in ("", "file"):
        return os.path.join(local_path(base), path)    # literal filesystem join, no decoding
    from mountainash.typespec.descriptor_context import _normalize_remote_path   # existing RFC 3986 dot-segment logic
    parts = urlsplit(base)                             # hierarchical join for every registered scheme;
    joined = posixpath.join(parts.path or "/", path)   # urljoin ignores s3/r2/gs/... (not in uses_relative)
    return urlunsplit((parts.scheme, parts.netloc, _normalize_remote_path(joined), "", ""))
```

  - **`datacontract(source)`.** Its package is built through a loader with `base_uri=path.parent`, so it inherits the loader policy. Verify with one assertion in the test file (`resource_policy(...)` root is the source's parent).
- [ ] **Step 4: Run** the new test file plus `tests/typespec` → PASS. Existing descriptor tests are unchanged except those listed in Task 9.
- [ ] **Step 5: Commit** `feat(datapackage)!: loaders carry a LocationPolicy; context survives copy and revalidation (381)`.

