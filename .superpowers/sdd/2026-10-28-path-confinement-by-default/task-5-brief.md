### Task 5 (files): explicit `FileSpec.policy`

**Files:** Modify `src/mountainash_files/specs/base.py:14-29`, `_operations.py` (`_resolve_profiles`, `_make_facade`, `_read_bytes`, `_write_bytes`, `_with_access`, the `on_source` callbacks in `parse`/`inspect_schema`, `_read_source`, `write`, `copy`, `stream`), `_glob.py:13-42`, `README.md`, `pyproject.toml`/`hatch.toml` (`mountainash-transport>=0.1.1,<0.2`), `__version__.py` (bump to `0.1.1`, the release carrying `FileSpec.policy`). Test: `tests/test_location_policy.py` (new).

**Interfaces:**
- Consumes: transport `LocationPolicy`, `LocationNotAllowed`, `StorageFacade.from_path(..., policy=)`.
- Produces: `FileSpec.policy: LocationPolicy | None = None` (inherited by `FileSourceSpec`/`FileSinkSpec`); `_resolve_profiles(spec) -> tuple[profile, auth, policy]`; `resolve_glob(base, pattern, *, storage_profile=None, auth_profile=None, policy=None)`.

- [ ] **Step 1: Failing tests.**

```python
import pytest
from mountainash_files import FileSinkSpec, FileSourceSpec, copy, inspect_schema, parse, stream, write
from mountainash_transport.location import LocationNotAllowed, LocationPolicy

@pytest.fixture
def env(tmp_path):
    root = tmp_path / "root"; out = tmp_path / "out"; root.mkdir(); out.mkdir()
    (root / "a.csv").write_text("v\n1\n"); (out / "s.csv").write_text("v\n9\n")
    return root, out, LocationPolicy(root=str(root))

def test_parse_inside_root_reads(env):
    root, _, pol = env
    assert parse(FileSourceSpec(path="a.csv", format="csv", policy=pol))[0].data.num_rows == 1

@pytest.mark.parametrize("op", ["parse", "inspect_schema", "stream"])
def test_read_operations_reject_outside(env, op):
    _, out, pol = env
    spec = FileSourceSpec(path=str(out / "s.csv"), format="csv", policy=pol)
    with pytest.raises(LocationNotAllowed):
        r = {"parse": parse, "inspect_schema": inspect_schema, "stream": stream}[op](spec)
        if op == "stream": r.__enter__()

def test_template_expansion_escape_rejected(env):
    _, _, pol = env
    with pytest.raises(LocationNotAllowed):
        parse(FileSourceSpec(path="{p}", format="csv", policy=pol), params={"p": "../out/s.csv"})

def test_glob_reads_only_in_root(env):
    root, out, pol = env
    (root / "link.csv").symlink_to(out / "s.csv")
    with pytest.raises(LocationNotAllowed):
        parse(FileSourceSpec(path=".", glob="*.csv", format="csv", policy=pol))

@pytest.mark.parametrize("mode", ["overwrite", "append"])
def test_write_outside_rejected(env, mode):
    import pyarrow as pa
    _, out, pol = env
    with pytest.raises(LocationNotAllowed):
        write(FileSinkSpec(path=str(out / "w.csv"), format="csv", policy=pol, write_disposition=mode), pa.table({"v": [1]}))

def test_copy_each_endpoint_uses_its_own_policy(env, tmp_path):
    root, out, pol = env
    dst = tmp_path / "dst"; dst.mkdir()
    copy(FileSourceSpec(path="a.csv", policy=pol), FileSinkSpec(path="b.csv", policy=LocationPolicy(root=str(dst))))
    assert (dst / "b.csv").exists()
    with pytest.raises(LocationNotAllowed):
        copy(FileSourceSpec(path="a.csv", policy=pol), FileSinkSpec(path=str(out / "x.csv"), policy=LocationPolicy(root=str(dst))))
    with pytest.raises(LocationNotAllowed):
        copy(FileSourceSpec(path=str(out / "s.csv"), policy=pol), FileSinkSpec(path="c.csv", policy=LocationPolicy(root=str(dst))))

def test_no_policy_is_today(env):
    _, out, _ = env
    assert parse(FileSourceSpec(path=str(out / "s.csv"), format="csv"))[0].data.num_rows == 1

def test_unknown_scheme_rejected_and_redacted(env):
    _, _, pol = env
    with pytest.raises(LocationNotAllowed) as e:
        parse(FileSourceSpec(path="hf://user:secret@h/x.csv", format="csv", policy=pol))
    assert "secret" not in str(e.value)

def test_supplied_profile_permits_its_own_endpoint_only(env, monkeypatch):
    """Decision 3 at the files boundary: a supplied S3 profile with BUCKET permits that bucket only."""
    import io
    from mountainash_transport.storage.facade import facade as facade_mod
    reads = []
    class Conn:
        def connect(self): pass
        def close(self): pass
    class Backend:
        storage_profile = None
        def read_to_bytes(self, path): reads.append(path); return b"v\n1\n"
        def read_to_stream(self, path): reads.append(path); return io.BytesIO(b"v\n1\n")
    monkeypatch.setattr("mountainash_transport.connections.create_connection", lambda *a, **k: Conn())
    monkeypatch.setattr(facade_mod, "get_storage_backend", lambda *a, **k: Backend())
    profile = _s3_profile(bucket="bucket-a")
    pol = LocationPolicy()
    parse(FileSourceSpec(path="s3://bucket-a/a.csv", format="csv", storage_profile=profile, policy=pol))
    with pytest.raises(LocationNotAllowed):
        parse(FileSourceSpec(path="s3://bucket-b/a.csv", format="csv", storage_profile=profile, policy=pol))
    assert reads == ["s3://bucket-a/a.csv"]
```

  `_s3_profile(bucket=...)` builds an `S3StorageProfile` from the same minimal fields Task 4 copies from transport's profile tests. Add it at the top of this file.

  Adjust `write_disposition` values to the sink spec's literal names (see `specs/sink.py`).
- [ ] **Step 2: Run** `hatch run test:test tests/test_location_policy.py` → FAIL.
- [ ] **Step 3: Implement.**
  - Add the field after `transforms`: `policy: LocationPolicy | None = None` (type under `TYPE_CHECKING`).
  - `_resolve_profiles(spec)` returns `(profile, auth, spec.policy)`. Every caller unpacks three values.
  - Every helper that receives `storage_profile, auth_profile` receives `policy` next to them and passes it on.
  - `_make_facade(path, storage_profile, auth_profile, policy)` → `StorageFacade.from_path(path, storage_profile, auth_profile=auth_profile, policy=policy)`.
  - `resolve_glob(..., policy=None)` passes it to its `StorageFacade.from_path`.
  - `copy` resolves `src_*` and `dst_*` triples separately.
  - No contextvar (spec §4). README "Location policy": no confinement without a policy; set one when specs come from untrusted input; examples for `root` and `allowed_remote`.
- [ ] **Step 4: Run** the full files suite → PASS. Existing tests use no policy.
- [ ] **Step 5: Commit** `feat(specs): FileSpec.policy threaded explicitly to every facade (381)`. Open the PR to `develop`, depending on the transport PR.

