### Task 7 (mountainash): reader seams — native decision, effective paths, allow-list, fallback

**Files:**
- Modify: `relations/backends/relation_systems/resource_files.py` (add `confined_local_paths`, `escape_duckdb_glob`; `polars_native_scan_supported` applies the policy gate; `_file_source_specs` passes `policy=` and joins paths).
- Modify the readers: Polars `relsys_pl_ext_ma_util.py:148-190`, Narwhals `relsys_nw_ext_ma_util.py:276-335`, Ibis `relsys_ib_ext_ma_util.py:183-250`.
- Test: `tests/relations/dag/cross_backend/test_location_policy_reads.py` (new, cross-backend parametrized per `cross-backend-test-coverage.md`).

**Interfaces:**
- Consumes: Task 6 `resource_policy`, `resolve_resource_location`; transport `confine_local`, `identify_scheme`, `LocationNotAllowed`.
- Produces:
```python
def confined_local_paths(resource, *, tree: bool) -> list[str] | None   # None => not local (fallback); raises LocationNotAllowed
def escape_duckdb_glob(path: str) -> str                               # [ * ? -> [[] [*] [?]
```

- [ ] **Step 1: Failing tests.** Parametrize over targets `"polars"`, `"narwhals"`, `ibis.duckdb.connect()`, `ibis.polars.connect()`. Build packages with `DataPackage.from_path` and collect via `pkg.to_relation_dag().collect("r", target=t)`. Normalize values with the existing `_collect_pl` helper pattern from `test_resource_read_cross_backend.py:54-69`.

```python
CASES = [
  # (id, path-or-builder, policy, expected)  expected: list of values, or "reject"
  ("in_root_glob_named_root", "data/a.csv", None, [99]),
  ("absolute_outside", "{outside}/secret.csv", None, "reject"),
  ("symlink_escape", "data/link.csv", None, "reject"),
  ("dir_with_escaping_entry", "badtree", None, "reject"),
  ("remote_no_allow", "http://127.0.0.1:{port}/secret.csv", None, "reject"),
  ("remote_allowed", "http://127.0.0.1:{port}/secret.csv", "allow-127", [666]),
  ("allow_list_only_keeps_root", "{outside}/secret.csv", "allow-any-http", "reject"),
  ("unknown_scheme", "hf://x/y.csv", None, "reject"),
  ("opt_out", "{outside}/secret.csv", "unconfined", [666]),
  ("remote_base_relative_resource", "<base_uri=http://127.0.0.1:{port}/> secret.csv", None, "reject"),
  ("remote_base_absolute_local", "<base_uri=http://127.0.0.1:{port}/> {outside}/secret.csv", None, "reject"),
]
```

  `<base_uri=...>` rows load with `DataPackage.from_descriptor(raw, base_uri=...)` from a working directory that does not contain `outside`; all other rows use `from_path`. Every rejecting row asserts the loopback server was not hit.

  The fixture builds the root `pkg[12]` with siblings `pkg1`/`pkg2`, `data/link.csv` → outside, a `badtree/` holding an outbound symlink, and a loopback HTTP server serving `outside`. All four targets must give the expected result. Add separate tests:
  - `test_plain_root_directory_reads_natively`: root without glob characters, directory `tree/` with `x.csv` and `sub/y.csv`. Polars, Narwhals and `ibis-duckdb` give `[7, 8]`; `ibis-polars` raises `LocationNotAllowed` (owner-approved exception).
  - `test_glob_named_root_directory_on_ibis_duckdb_rejected`: `LocationNotAllowed`.
  - `test_literal_percent_filename`: files `report%20a.csv` = `[1]` and `report a.csv` = `[2]` → `[1]`, under a policy and under the opt-out.
  - `test_path_assigned_after_load_is_confined`: load an in-root package, then `pkg.resources[0].path = str(outside / "secret.csv")`; collecting raises `LocationNotAllowed` on all targets.
  - `test_opt_out_reads_relative_to_descriptor_not_cwd`: descriptor in `d/` with `a.csv` = `[5]`; working directory elsewhere, containing an `a.csv` = `[6]`; `policy=LocationPolicy(allow_unconfined=True)` → `[5]` on all targets.
  - `test_opt_out_remote_base_relative_resource_takes_fallback`: `from_descriptor(raw, base_uri=f"http://127.0.0.1:{port}/", policy=LocationPolicy(allow_unconfined=True))` with relative `secret.csv` reads `[666]` on all targets, through the files fallback, not a local native scan of `secret.csv`.
  - `test_schema_phase_rejects_outside_and_reads_inside`: use the SCHEMA execution pattern from `tests/relations/test_resource_schema_discovery.py:66-90` (`relation._compile_and_execute_with_visitor(target=..., phase=ExecutionPhase.SCHEMA)`, with `ExecutionPhase` from `relations.core.execution.preparation`). An outside path raises `LocationNotAllowed` on all targets; an in-root path completes. (Declaration-only `infer_schema` never opens the resource, so it cannot test this.)
  - `test_programmatic_absolute_path_is_today`: `DataPackage(...)` with an absolute outside path reads on all targets.

  **Existing limitation, recorded, not changed:** the SCHEMA dispatcher (`relation_mapping/handlers.py:187-202`) sends every Ibis resource through `inspect_resource_schema`, which cannot read a directory. Probed 2026-10-28 on `develop` without any policy: Ibis/DuckDB SCHEMA on a directory resource raises `StorageError: Is a directory`; Polars succeeds. Under a policy the Ibis SCHEMA directory case raises `LocationNotAllowed` instead. Do not add a new SCHEMA route for Ibis directories; note the limitation in `resource-read-support-matrix.md` (Task 9).
- [ ] **Step 2: Run** `hatch run test:test-target-quick tests/relations/dag/cross_backend/test_location_policy_reads.py` → FAIL.
- [ ] **Step 3: Implement.**
  - **`confined_local_paths(resource, *, tree)`.** For each authored path:
    1. `p = resolve_resource_location(resource, raw)`;
    2. `scheme = identify_scheme(p)`; `None` with an active policy → `LocationNotAllowed(raw, "unknown scheme")`;
    3. non-local → return `None`;
    4. otherwise `confine_local(p, policy, tree=tree)`.

    With no active policy, return the base-joined paths: the raw paths for programmatic resources, descriptor-relative paths for loaded ones, including under `allow_unconfined`.
  - **Routing uses the base-resolved path, with or without a policy.** Opting out of confinement must not opt out of descriptor-relative resolution. Each native predicate (`polars_native_scan_supported`, Ibis `_native_scan_for`) classifies `resolve_resource_location(resource, raw)` instead of the authored path: a resolved remote location is never native and takes the existing files fallback; a resolved local one keeps today's native eligibility. Without a policy, the native branch opens `confined_local_paths(resource, tree=False)` with today's reader options (no `glob=False`, no escaping), which gives today's behaviour for programmatic resources.
  - **`polars_native_scan_supported`.** Under an active policy: authored glob characters → `False` (the files fallback confines each match); `confined_local_paths(resource, tree=True) is None` → `False`. The existing checks then run unchanged.
  - **Polars `read_resource`.** Under a policy, the native branch opens `confined_local_paths(resource, tree=True)` with `glob=False` for both `scan_csv` and `scan_parquet`. Compute the paths once in `read_resource` and pass them in; do not run the tree check twice.
  - **Narwhals.** Same, inside the existing `narwhals-polars`/`narwhals-lazy` gate: `nw.scan_*(p, backend="polars", glob=False, ...)`.
  - **Ibis `_native_scan_for`.** Under a policy:
    - `key = location.dialect if location and location.dialect else f"ibis-{con.name}"`;
    - native only if `key == "ibis-duckdb"` and the effective paths are local;
    - a directory whose effective path contains `[`, `*` or `?` is not native.

    The reader opens files escaped with `escape_duckdb_glob` and directories unchanged.
  - **Fallback (`_file_source_specs`, shared by `parse_resource_to_arrow` and `inspect_resource_schema`).**
    - Each entry's base part is base-joined with `resolve_resource_location`.
    - Under an active policy, non-glob entries also get:
      - unknown scheme → `LocationNotAllowed`;
      - local → `confine_local`; if the result is a directory, raise `LocationNotAllowed(raw, "directory resource not supported for this backend under a location policy; use a glob")`.
    - Remote permission is **not** re-evaluated here; `FileSourceSpec(policy=...)` → files → `StorageFacade._check` and the HTTP send hook own it.
    - Pass `FileSourceSpec(path=<base-joined base>, glob=pattern, ..., policy=policy)`. The path is already absolute or a full URI, so files' own root join is a no-op on it.
- [ ] **Step 4: Run** the new file plus `tests/relations/dag` → PASS.
- [ ] **Step 5: Commit** `feat(resources): confine native and fallback resource reads; decision-7 allow-list (381)`.

