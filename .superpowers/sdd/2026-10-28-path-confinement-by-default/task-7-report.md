# Task 7 report

## Implemented
- `resource_files.py`: `escape_duckdb_glob`, `confined_local_paths(resource, *, tree)`, `polars_native_scan_paths` (single native decision returning effective paths; `polars_native_scan_supported` wraps it), `_file_source_specs` base-joins, confines non-glob entries (unknown scheme / directory -> LocationNotAllowed), passes `policy=`.
- Polars/Narwhals `read_resource` use the effective paths once (tree walk once), `glob=False` under a policy.
- Ibis `_native_scan_paths` (wrapped by `_native_scan_for`): routes on the descriptor-resolved path; under a policy only `ibis-duckdb` (key = location.dialect or `ibis-{con.name}`), glob-char directories fall back; reader escapes files, leaves directories.
- Existing `test_e2e_real_descriptor.py` tests loaded a descriptor then assigned tmp_path files outside the (cwd) root; now given `LocationPolicy(root=tmp_path)`.

## TDD
RED: `pytest tests/relations/dag/cross_backend/test_location_policy_reads.py` -> 65 failed, 12 passed (e.g. relative paths read from cwd; escapes read).
GREEN: same file -> 77 passed.
Full `pytest tests`: 34954 passed, 2 failed (the e2e descriptor tests above), fixed -> 6 passed.

## Notes / concerns
- Test location: brief's `test_resource_read_cross_backend.py` is at `tests/relations/dag/`; schema test uses string target `"ibis"` with `ibis.options.default_backend` patched (connection targets are not supported by SCHEMA phase).
- "allow-any-http" policy is `allowed_remote={"http": {"127.0.0.1"}}` (no wildcard exists in LocationPolicy).
- Under a policy, effective paths are realpaths passed to readers.

## Fix round 1
"allow-any-http" factory now `LocationPolicy(allowed_remote={"http": frozenset()})` (empty host set = any host); earlier note that a wildcard cannot be expressed was wrong. `allow_list_only_keeps_root` still rejects on all four targets with zero requests. File: 77 passed.
