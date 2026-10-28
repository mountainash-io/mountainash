# Final fix report
Each fix: regression test written, RED confirmed against pre-fix source, GREEN after.

1. transport facade.py: policy composed first; ROOT_PATH created only if policy inactive, profile root is effective root, or confine_local passes. Test `test_create_path_not_created_outside_caller_root` (+inside-root positive). RED: `assert not True`; GREEN.
2. transport: `read_stream` runs `_check(path)` before `_resolve_pipeline` (authored path still used for suffixes). Test `test_denied_credential_url_with_gpg_suffix_does_not_leak` RED: ValueError leaking path with `secret`. Files: `_no_transforms` defers ValueError from inference to the byte path (policy-checked facade). Test `test_denied_credential_gpg_url_redacted_before_inference[parse|inspect_schema|stream]`; RED on inspect_schema (ValueError leak), GREEN.
3. transport `_check`: inactive policy returns before require_known_scheme/URL parsing; `copy` derived-destination rejection gated on active policy. Tests `test_malformed_url_not_policy_error_when_inactive`, `test_copy_into_dir_derived_dir_not_policy_error_when_inactive` (None + allow_unconfined). RED: policy error raised; GREEN.
4. mountainash `loader_policy`: relative explicit local root made absolute (os.path.abspath, load-time cwd). Test `test_relative_explicit_root_without_base_anchored_once` via ResourceRef.read_bytes. RED: b'wrong' == b'right' failure; GREEN.
5. mountainash: `_ensure_storage_facade` removed (sole caller `facade_read_bytes`); obsolete missing-package test removed.
6. files: `s3` extra floor raised to >=0.1.1,<0.2 (others already were).

Commands: transport `hatch run test:test-target-quick tests/storage/facade/test_facade_location_policy.py`; files `.hatch/test-py3.12/bin/python -m pytest tests/test_location_policy.py -q`; mountainash `pytest tests/typespec/test_location_policy_context.py -q`.
Suites: transport full 1826 passed/1 skipped; files full 584 passed; mountainash tests/core tests/typespec tests/relations/dag 8832 passed, 46 skipped, 254 xfailed.
Commits: transport 0661f49; files b0f0387; mountainash (see git log -1 on feature branch).

## Second fix round

- **R1 (transport facade)**: CREATE_PATH now computes `target = declared if abs else os.path.join(os.getcwd(), declared)` (no `..` collapse), confines that exact path when a caller root is supplied, and `makedirs(target)`. RED: `test_create_path_relative_root_created_nowhere_outside_caller_root` → `assert not (work/'outside').exists()` failed. GREEN after fix.
- **R2 (transport facade)**: `_check` returns path unchanged under an inactive policy (all providers); `from_path` runs `require_known_scheme` only under an active policy, otherwise `urlparse` (pre-381 ValueError). RED: identity test `'/x' == 'file:///x'` failed; malformed URL raised LocationNotAllowed. GREEN after fix. Command: `hatch run test:test-target-quick tests/storage/facade/test_facade_location_policy.py`.
- **R3 (mountainash)**: `loader_policy` anchors relative root with `os.path.join(os.getcwd(), root)`. RED: `test_relative_root_with_symlink_dotdot_not_collapsed` → LocationNotAllowed (outside root). GREEN after fix; `data/data/a.csv` test still passes.
- Full runs: transport 1831 passed/1 skipped; mountainash tests/core+typespec+relations/dag 8833 passed, 46 skipped, 254 xfailed; files 584 passed.

## Second fix round — addendum

- `location._split`/`identify_scheme`/`local_path` now let urlsplit's `ValueError` propagate (pre-381). New `_sanitized` wrapper translates to `LocationNotAllowed(..., "invalid location") from None` only in `require_known_scheme` (active policy) and `confine_local` (active root); `url_host`/`allow_remote` unchanged (enforcement). Removed the `urlparse` workaround in `from_path`.
- Tests: new facade tests (policy-free `StoragePath.identify_scheme`/`detect_provider_from_path('https://[bad')` → ValueError; active-policy sanitized, no secret). `tests/test_location.py` policy-free `identify_scheme`/`local_path` malformed cases dropped from no-leak parametrizations; active-policy cases kept.
- Runs: transport 1829 passed/1 skipped; mountainash tests/core+relations/dag 7375 passed, 46 skipped, 249 xfailed.

## Second fix round — addendum 2

- `core.location.resolve_resource_location` now calls `require_known_scheme(path, policy)` first when the resource carries an active policy (sanitized `LocationNotAllowed`); inactive/programmatic unchanged (urllib `ValueError` from `is_remote` as before). Other classification sites receive already-vetted strings via this resolver.
- Tests (tests/typespec/test_location_policy_context.py): loaded credential-bearing malformed path via `ResourceRef.read_bytes()` and collect on polars/ibis → `LocationNotAllowed`, no `secret`, no cause/context; programmatic → `ValueError`. RED (3 ValueErrors with secret) with src stashed; GREEN after.
- Run: tests/core tests/typespec tests/relations/dag: 8837 passed, 46 skipped, 254 xfailed.
