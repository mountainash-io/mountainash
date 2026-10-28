# Task 1 report (transport: location module)
Implemented: `location.py` (brief code verbatim, plus type annotations on with_declared_root/allow_remote), `_schemes.py` (git mv of path_helpers/scheme.py, contents verbatim), `StoragePath.identify_scheme` delegates to `location.identify_scheme`. Importers updated (storage_path, s3, backend_detection, test_scheme, test_registry_completeness). `path_helpers/scheme.py` deleted; `SchemeSpec`/`SCHEMES` removed from `path_helpers/__init__` exports (no alias). AGENTS.md line updated.
Tests: tests/test_location.py = brief tests verbatim (added `require_known_scheme` to its import line, which the brief omitted but uses).
RED: `hatch run test:test-target-quick tests/test_location.py` -> ModuleNotFoundError: mountainash_transport.location.
GREEN: same + tests/storage/path_helpers registry protocols -> 302 passed. Full `hatch run test:test-quick` -> 1774 passed, 1 skipped.
Self-review: diff read; no mypy run (policy). Stdlib-only import test left to Task 2.
Concerns: docs-site/profile JSON still mention path_helpers.scheme (generated docs, left). `storage_path` imports `location` which imports `_core.exceptions`; fine.

## Fix round 1
- P1: `_redact` is urllib-free (strips through last `@` in authority; never raises). New `_split`/`url_host` translate urlsplit ValueError to `LocationNotAllowed(..., "invalid location")` raised outside the except block (`__cause__` None, suppress_context True, no chain secret). Covers identify_scheme, local_path, confine_local, require_known_scheme, url_host.
- P2: one `_norm_host` (IDNA + lowercase) applied to requested host, `profile_host`, every allow-list entry; reused by `url_host`. Un-encodable hosts -> "invalid location".
- Tests added to tests/test_location.py (malformed credential authority x5 callables, constructor redaction, unicode/punycode/mixed-case via allow-list and profile_host).
- `hatch run test:test-target-quick tests/test_location.py tests/storage/path_helpers tests/storage/registry tests/storage/protocols` -> 309 passed.

## Fix round 2
`_redact` now mirrors urllib: strips leading/trailing C0+space, removes \t\r\n, finds authority after first `//` to first `/?#`, drops through last `@`. Parser-free, never raises. Tests: scheme-relative, newline-split, tab-in-scheme, leading-space; assert no secret via direct construction and identify_scheme/url_host/require_known_scheme, `__cause__` None. Focused set: 313 passed.

## Fix round 3
Test-only: split into constructor-redaction test (4 forms) and malformed-form test requiring `pytest.raises(LocationNotAllowed)` on identify_scheme/url_host/require_known_scheme, asserting no secret, `__cause__` and `__context__` None. test_location.py: 37 passed; full `hatch run test:test-quick`: 1791 passed, 1 skipped.
