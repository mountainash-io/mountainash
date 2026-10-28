### Task 1 (transport): `location` module — rules and errors

**Files:**
- Create: `src/mountainash_transport/location.py`
- Create: `src/mountainash_transport/_schemes.py` (stdlib-only scheme registry, moved from `storage/path_helpers/scheme.py`)
- Modify: `src/mountainash_transport/storage/path_helpers/scheme.py` (delete moved contents), `storage/path_helpers/storage_path.py:48-66` (`StoragePath.identify_scheme` delegates), every importer of `SCHEMES`/`_ALIAS_TO_CANONICAL`/`SchemeSpec` (find them with `git grep -n "path_helpers.scheme\|from .scheme import"`)
- Test: `tests/test_location.py`

**Interfaces — Produces:**
```python
# mountainash_transport/location.py
@dataclass(frozen=True)
class LocationPolicy:
    root: str | os.PathLike[str] | None = None
    allowed_remote: Mapping[str, frozenset[str]] = field(default_factory=dict)
    allow_unconfined: bool = False
    @property
    def active(self) -> bool: ...                       # not allow_unconfined
    def with_declared_root(self, declared: str | os.PathLike[str] | None) -> "LocationPolicy": ...
class LocationNotAllowed(StorageError):
    location: str; reason: str
def identify_scheme(location: str) -> str | None: ...   # "" bare, "file", canonical remote, None unknown
def local_path(location: str) -> str: ...
def confine_local(location: str, policy: LocationPolicy | None, *, tree: bool = False) -> str: ...
def allow_remote(scheme: str, host: str, policy: LocationPolicy | None, *, profile_host: str | None = None) -> None: ...
def url_host(location: str) -> str: ...                 # parsed, lowercased, IDNA, userinfo stripped
def require_known_scheme(location: str, policy: LocationPolicy | None) -> str | None: ...  # raises "unknown scheme" under an active policy
```

- [ ] **Step 1: Write the failing tests** (`tests/test_location.py`), one test per spec acceptance-A row:

```python
import os, subprocess, sys
import pytest
from mountainash_transport.location import (
    LocationNotAllowed, LocationPolicy, allow_remote, confine_local, identify_scheme, local_path, url_host,
)

@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "root"; (root / "d").mkdir(parents=True); (root / "d" / "a.csv").write_text("v\n1\n")
    out = tmp_path / "out"; out.mkdir(); (out / "s.csv").write_text("v\n9\n")
    (root / "link.csv").symlink_to(out / "s.csv")
    (root / "dlink").symlink_to(root / "d")
    return root, out

def P(root, **kw): return LocationPolicy(root=str(root), **kw)

def test_in_root_relative_returns_effective_absolute(tree):
    root, _ = tree
    assert confine_local("d/a.csv", P(root)) == os.path.realpath(root / "d" / "a.csv")

@pytest.mark.parametrize("loc", ["../out/s.csv", "d/../../out/s.csv"])
def test_dotdot_escape_rejected(tree, loc):
    root, _ = tree
    with pytest.raises(LocationNotAllowed) as e: confine_local(loc, P(root))
    assert e.value.reason == "outside root"

def test_absolute_outside_rejected(tree):
    root, out = tree
    with pytest.raises(LocationNotAllowed): confine_local(str(out / "s.csv"), P(root))

def test_symlink_escape_rejected(tree):
    root, _ = tree
    with pytest.raises(LocationNotAllowed): confine_local("link.csv", P(root))

def test_link_dotdot_resolving_inside_allowed(tree):
    root, _ = tree
    assert confine_local("dlink/../d/a.csv", P(root)).endswith(os.path.join("d", "a.csv"))

def test_missing_write_target_under_root_allowed_and_escape_rejected(tree):
    root, _ = tree
    assert confine_local("new/x.csv", P(root)) == os.path.join(os.path.realpath(root), "new", "x.csv")
    with pytest.raises(LocationNotAllowed): confine_local("new/../../x.csv", P(root))

def test_file_uri_decoded_once(tree):
    root, _ = tree
    good = (root / "d" / "a.csv").as_uri()
    assert confine_local(good, P(root)) == os.path.realpath(root / "d" / "a.csv")
    with pytest.raises(LocationNotAllowed): confine_local(f"file://evilhost{root}/d/a.csv", P(root))
    with pytest.raises(LocationNotAllowed): confine_local(f"{root.as_uri()}/%2e%2e/out/s.csv", P(root))

def test_bare_percent_is_literal(tree):
    root, _ = tree
    assert confine_local("%2e%2e/x.csv", P(root)).endswith("%2e%2e/x.csv")

def test_root_with_glob_characters(tmp_path):
    root = tmp_path / "pkg[12]"; root.mkdir(); (root / "a.csv").write_text("x")
    assert confine_local("a.csv", P(root)) == os.path.realpath(root / "a.csv")

def test_tree_check_rejects_escaping_entry(tree):
    root, out = tree
    (root / "d" / "bad.csv").symlink_to(out / "s.csv")
    with pytest.raises(LocationNotAllowed) as e: confine_local("d", P(root), tree=True)
    assert e.value.reason == "directory entry outside root"
    assert confine_local("d", P(root)) == os.path.realpath(root / "d")   # tree=False: directory checked as itself

def test_tree_check_survives_symlink_loop(tree):
    root, _ = tree
    (root / "d" / "loop").symlink_to(root / "d")
    assert confine_local("d", P(root), tree=True)

def test_unknown_scheme():
    assert identify_scheme("hf://x/y") is None
    assert identify_scheme("S3://b/k") == "s3" and identify_scheme("/a") == "" and identify_scheme("file:///a") == "file"
    with pytest.raises(LocationNotAllowed) as e: require_known_scheme("hf://user:secret@h/x", LocationPolicy())
    assert e.value.reason == "unknown scheme" and "secret" not in str(e.value)
    assert require_known_scheme("hf://x/y", None) is None          # no policy: caller's existing handling applies

def test_dot_in_missing_remainder_is_harmless(tree):
    root, _ = tree
    assert confine_local("new/.", P(root)) == os.path.join(os.path.realpath(root), "new")

def test_allow_remote_rules():
    pol = LocationPolicy(allowed_remote={"https": frozenset({"data.example.com"}), "s3": frozenset()})
    allow_remote("https", "data.example.com", pol)
    allow_remote("s3", "any-bucket", pol)
    with pytest.raises(LocationNotAllowed) as e: allow_remote("https", "evil.example", pol)
    assert e.value.reason == "remote not allowed"
    allow_remote("sftp", "host-a", LocationPolicy(), profile_host="HOST-A")
    with pytest.raises(LocationNotAllowed) as e: allow_remote("sftp", "host-b", LocationPolicy(), profile_host="host-a")
    assert e.value.reason == "profile host mismatch"

def test_url_host_parsing():
    assert url_host("http://allowed@evil.example/x") == "evil.example"
    assert url_host("https://DATA.Example.COM/x") == "data.example.com"
    assert url_host("https://bücher.example/x") == "xn--bcher-kva.example"

@pytest.mark.parametrize("pol", [None, LocationPolicy(root="/nonexistent", allow_unconfined=True)])
def test_inactive_policy_is_today(pol, tree):
    _, out = tree
    assert confine_local(str(out / "s.csv"), pol) == str(out / "s.csv")
    assert confine_local("rel.csv", pol) == "rel.csv"
    allow_remote("https", "anything", pol)

def test_with_declared_root_composition():
    assert LocationPolicy().with_declared_root("/r").root == "/r"
    assert LocationPolicy(root="/x").with_declared_root("/r").root == "/x"
    p = LocationPolicy(allowed_remote={"https": frozenset()}).with_declared_root("/r")
    assert p.root == "/r" and p.allowed_remote

def test_error_redacts_userinfo_and_names_location():
    e = LocationNotAllowed("https://user:secret@h.example/p", "remote not allowed")
    assert "secret" not in str(e) and "h.example/p" in str(e) and e.reason == "remote not allowed"

```

  The stdlib-only import assertion belongs to Task 2, which makes package initialization lazy (it cannot pass while `__init__` is eager).

- [ ] **Step 2: Run, expect failure.** `hatch run test:test-target-quick tests/test_location.py` → ImportError for `mountainash_transport.location`.

- [ ] **Step 3: Implement.**
  - Move `SchemeSpec`, `SCHEMES` and `_ALIAS_TO_CANONICAL` verbatim into `_schemes.py`. Its imports must be `dataclasses` and `mountainash_transport._core.constants` only.
  - Update every importer to `mountainash_transport._schemes` and delete the moved definitions from `path_helpers/scheme.py`. If that file becomes empty, delete it and its export. No re-export alias.
  - `StoragePath.identify_scheme(path)` returns `location.identify_scheme(str(path)) if path else ""`.
  - Write `location.py`:

```python
"""Storage-location confinement policy (stdlib only)."""
from __future__ import annotations
import os
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from urllib.parse import unquote, urlsplit
from mountainash_transport._core.exceptions import StorageError
from mountainash_transport._schemes import SCHEMES, _ALIAS_TO_CANONICAL

@dataclass(frozen=True)
class LocationPolicy:
    root: str | os.PathLike[str] | None = None
    allowed_remote: Mapping[str, frozenset[str]] = field(default_factory=dict)
    allow_unconfined: bool = False
    @property
    def active(self) -> bool:
        return not self.allow_unconfined
    def with_declared_root(self, declared):
        return self if self.root is not None or declared is None else replace(self, root=declared)

class LocationNotAllowed(StorageError):
    def __init__(self, location: str, reason: str) -> None:
        self.location = _redact(location); self.reason = reason
        super().__init__(f"location not allowed: {self.location} ({reason})")

def _redact(location: str) -> str:
    parts = urlsplit(location)
    if "@" not in parts.netloc:
        return location
    return parts._replace(netloc=parts.netloc.rsplit("@", 1)[1]).geturl()

def identify_scheme(location: str) -> str | None:
    if os.name == "nt" and len(location) > 2 and location[1] == ":" and location[2] in "\\/":
        return ""                                   # drive path (spec §1 rule 3; not CI-verified)
    if os.name == "nt" and location.startswith("\\\\"):
        return ""                                   # UNC
    scheme = urlsplit(location).scheme.lower()
    if not scheme:
        return ""
    if scheme == "file":
        return "file"
    canonical = _ALIAS_TO_CANONICAL.get(scheme, scheme)
    return canonical if canonical in SCHEMES else None

def local_path(location: str) -> str:
    if identify_scheme(location) != "file":
        return location
    parts = urlsplit(location)
    if parts.netloc not in ("", "localhost") or parts.query or parts.fragment:
        raise LocationNotAllowed(location, "invalid file URI")
    path = unquote(parts.path)
    if not os.path.isabs(path):
        raise LocationNotAllowed(location, "invalid file URI")
    return path

def url_host(location: str) -> str:
    host = urlsplit(location).hostname or ""
    return host.encode("idna").decode("ascii").lower() if host else ""

def require_known_scheme(location: str, policy: LocationPolicy | None) -> str | None:
    scheme = identify_scheme(location)
    if scheme is None and policy is not None and policy.active:
        raise LocationNotAllowed(location, "unknown scheme")
    return scheme

def _resolve(path: str) -> str:
    if os.path.lexists(path):
        return os.path.realpath(path)
    head, tail = os.path.split(path)
    if head == path:
        return path
    if tail == ".":
        return _resolve(head)
    if tail == "..":
        raise LocationNotAllowed(path, "outside root")
    return os.path.join(_resolve(head), tail)

def confine_local(location: str, policy: LocationPolicy | None, *, tree: bool = False) -> str:
    path = local_path(location)
    if policy is None or not policy.active or policy.root is None:
        return path
    root = os.path.realpath(policy.root)
    effective = _resolve(os.path.join(root, path))
    if not Path(effective).is_relative_to(root):
        raise LocationNotAllowed(location, "outside root")
    if tree and os.path.isdir(effective):
        _check_tree(effective, root)
    return effective

def _check_tree(top: str, root: str) -> None:
    seen: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(top, followlinks=True):
        real = os.path.realpath(dirpath)
        if real in seen:
            dirnames[:] = []; continue
        seen.add(real)
        for name in (*dirnames, *filenames):
            entry = os.path.join(dirpath, name)
            if not Path(os.path.realpath(entry)).is_relative_to(root):
                raise LocationNotAllowed(entry, "directory entry outside root")

def allow_remote(scheme, host, policy, *, profile_host=None):
    if policy is None or not policy.active:
        return
    if profile_host is not None:
        if host == profile_host.lower():
            return
        reason = "profile host mismatch"
    else:
        reason = "remote not allowed"
    allowed = policy.allowed_remote.get(scheme)
    if allowed is not None and (not allowed or host in allowed):
        return
    raise LocationNotAllowed(f"{scheme}://{host}", reason)
```

  `test_missing_write_target_under_root_allowed_and_escape_rejected` needs `..` inside a missing remainder to be rejected. `_resolve` handles that by rejecting `..`/`.` tails while recursing up to the first existing ancestor.

- [ ] **Step 4: Run** `hatch run test:test-target-quick tests/test_location.py tests/storage/path_helpers tests/storage/registry` → PASS. Existing scheme and registry tests must stay green.
- [ ] **Step 5: Commit** `feat(location): stdlib-only LocationPolicy and confinement rules (381)`.

