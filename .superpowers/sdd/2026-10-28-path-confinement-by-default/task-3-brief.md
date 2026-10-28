### Task 3 (transport): facade enforcement for local storage, `ROOT_PATH`, copy rules, `MOUNT_SPEC` removal

**Files:**
- Modify: `storage/facade/facade.py` (`__init__`, `for_local`, `from_path`, every path-taking method), `storage/facade/cross_backend.py:16-40`, `settings/storage/profiles/local_storage_profile.py` (remove `MOUNT_SPEC`, its docs and `get_connection_url` branch; `CREATE_PATH` creates `ROOT_PATH`).
- Tests: `tests/storage/facade/test_facade_location_policy.py` (new); update `tests/settings/storage/profiles/test_local_settings.py` and `tests/settings/test_loader.py:278-301` (delete the `MOUNT_SPEC` cases; obsolete).

**Interfaces:**
- Consumes: Task 1 API.
- Produces:
  - `StorageFacade(provider_type, storage_profile=None, *, auth_profile=None, oauth_provider=None, token_store=None, policy: LocationPolicy | None = None)`; the same `policy=` keyword on `from_path` and `for_local`.
  - Private `StorageFacade._check(path: str) -> str`, which returns the path the backend must use.
  - Attributes `_policy`, `_profile_host`.

- [ ] **Step 1: Failing tests** (`test_facade_location_policy.py`):

```python
import pytest
from mountainash_transport import StorageFacade, copy_between
from mountainash_transport.location import LocationNotAllowed, LocationPolicy
from mountainash_transport.settings.storage.profiles import LocalStorageProfile

@pytest.fixture
def dirs(tmp_path):
    a = tmp_path / "a"; b = tmp_path / "b"; out = tmp_path / "out"
    for d in (a, b, out): d.mkdir()
    (a / "f.csv").write_bytes(b"1"); (out / "victim").write_bytes(b"keep")
    return a, b, out

def local(root): return StorageFacade.for_local(policy=LocationPolicy(root=str(root)))

def local_profile(**kw):
    return LocalStorageProfile(PROVIDER_TYPE=CONST_STORAGE_PROVIDER_TYPE.LOCAL, auth=NoAuthProfile(), **kw)

def test_root_path_profile_confines(dirs):
    a, _, out = dirs
    fac = StorageFacade("local", LocalStorageProfile(ROOT_PATH=str(a)))
    assert fac.read("f.csv") == b"1"
    for call in (lambda: fac.read(str(out / "victim")), lambda: fac.write("../out/x", b"z"),
                 lambda: fac.mkdir("../out/d"), lambda: fac.delete(str(out / "victim")),
                 lambda: fac.exists(str(out / "victim")), lambda: fac.list_dir(str(out))):
        with pytest.raises(LocationNotAllowed): call()

def test_root_path_kept_when_caller_adds_only_allow_list(dirs):
    a, _, out = dirs
    fac = StorageFacade("local", LocalStorageProfile(ROOT_PATH=str(a)),
                        policy=LocationPolicy(allowed_remote={"https": frozenset()}))
    with pytest.raises(LocationNotAllowed): fac.read(str(out / "victim"))

def test_no_policy_is_today(dirs):
    _, _, out = dirs
    assert StorageFacade.for_local().read(str(out / "victim")) == b"keep"

def test_copy_into_dir_with_outbound_symlink_rejected(dirs):
    a, _, out = dirs
    (a / "dst").mkdir(); (a / "dst" / "f.csv").symlink_to(out / "victim")
    with pytest.raises(LocationNotAllowed): local(a).copy("f.csv", "dst")
    assert (out / "victim").read_bytes() == b"keep"

def test_copy_into_dir_where_derived_name_is_dir_rejected(dirs):
    a, _, out = dirs
    (a / "dst" / "f.csv").mkdir(parents=True); (a / "dst" / "f.csv" / "f.csv").symlink_to(out / "victim")
    with pytest.raises(LocationNotAllowed): local(a).copy("f.csv", "dst")
    assert (out / "victim").read_bytes() == b"keep"

def test_copy_between_two_roots_relative_endpoints(dirs):
    a, b, _ = dirs
    copy_between("f.csv", "g.csv", local(a), local(b))
    assert (b / "g.csv").read_bytes() == b"1"

@pytest.mark.parametrize("layout", ["symlink_at_derived_name", "dir_at_derived_name"])
def test_copy_between_shortcut_applies_final_destination_rule(dirs, layout):
    a, _, out = dirs
    if layout == "symlink_at_derived_name":
        (a / "dst").mkdir(); (a / "dst" / "f.csv").symlink_to(out / "victim")
    else:
        (a / "dst" / "f.csv").mkdir(parents=True); (a / "dst" / "f.csv" / "f.csv").symlink_to(out / "victim")
    same = LocationPolicy(root=str(a))
    with pytest.raises(LocationNotAllowed):
        copy_between("f.csv", "dst", StorageFacade.for_local(policy=same), StorageFacade.for_local(policy=same))
    assert (out / "victim").read_bytes() == b"keep"

def test_mount_spec_removed():
    assert "MOUNT_SPEC" not in {f.name for f in LOCAL_SPEC.fields}
    assert "mount_spec" not in local_profile(ROOT_PATH="/tmp/x").to_handler_kwargs()

def test_create_path_creates_root(tmp_path):
    root = tmp_path / "new-root"
    StorageFacade(CONST_STORAGE_PROVIDER_TYPE.LOCAL, local_profile(ROOT_PATH=str(root), CREATE_PATH=True))
    assert root.is_dir()
```

  Imports to add at the top of the file: `from mountainash_auth_client import NoAuthProfile`, `from mountainash_transport._core.constants import CONST_STORAGE_PROVIDER_TYPE`, `from mountainash_transport.settings.storage.profiles import LOCAL_SPEC`. In the tests above, build every profile with `local_profile(...)` and every facade with `StorageFacade(CONST_STORAGE_PROVIDER_TYPE.LOCAL, local_profile(ROOT_PATH=...), ...)`. If `LOCAL_SPEC` exposes its fields under another attribute name, use that name; the assertion is that the spec no longer declares `MOUNT_SPEC`.

- [ ] **Step 2: Run** `hatch run test:test-target-quick tests/storage/facade/test_facade_location_policy.py` → FAIL.
- [ ] **Step 3: Implement.**
  - **Constructor.** After the backend is created:
    - `declared = storage_profile.ROOT_PATH` when the provider is LOCAL and `ROOT_PATH` is set. If `CREATE_PATH`, call `os.makedirs(declared, exist_ok=True)`.
    - `self._policy = (policy or LocationPolicy()).with_declared_root(declared) if declared else policy`.
    - Profile permission (decision 3), from a **caller-supplied** profile only (the HTTP default profile the facade creates grants nothing):
      - SFTP: `self._profile_host = storage_profile.HOST`; `self._profile_any = False`.
      - S3 family: if `storage_profile.BUCKET` is set, `self._profile_host = BUCKET`, `self._profile_any = False`; if `BUCKET` is `None`, `self._profile_host = None`, `self._profile_any = True` (any bucket at the profile's endpoint, spec §3).
      - Otherwise `self._profile_host = None`, `self._profile_any = False`.
  - **`_check(path)`:**
    - LOCAL → `confine_local(path, self._policy)`.
    - Remote providers → see Task 4.
    - Returns the path the backend must use.
  - **Call sites.** Call `path = self._check(path)` at the top of `read_stream`, `write`, `write_stream`, `list_objects`, `delete`, `exists`, `metadata`, `get_size`, `list_dir`, `mkdir` and `rmdir`. `read` delegates to `read_stream`; check there once.
  - **`copy(source, destination)`:**
    - `src = self._check(source)`; `dst = self._check(destination)`.
    - If LOCAL and `os.path.isdir(dst)`: `final = self._check(os.path.join(dst, os.path.basename(src)))`. If `os.path.isdir(final)`, raise `LocationNotAllowed(destination, "copy destination is a directory")`. Pass `final`.
    - Otherwise pass `dst`.
  - **`copy_between`.** Take the same-backend shortcut only when `source_facade._policy == destination_facade._policy` **and** both facades hold the same profile object (`is`). Otherwise use the existing stream branch, where each facade checks its own endpoint. Profiles carry their own permissions, so equal policies with different profiles are not equivalent.
  - **Local profile.** Remove `MOUNT_SPEC` from `LOCAL_SPEC`, the type stub, `get_connection_url` and `to_handler_kwargs`. Update `docs`/README where they describe mounting. Delete the obsolete loader/profile tests for `MOUNT_SPEC`.
- [ ] **Step 4: Run** `hatch run test:test-target-quick tests/storage tests/settings` → PASS. Existing tmp_path backend tests use no policy and must be unchanged.
- [ ] **Step 5: Commit** `feat(facade)!: enforce LocationPolicy for local storage; ROOT_PATH confines; remove MOUNT_SPEC (381)`.

