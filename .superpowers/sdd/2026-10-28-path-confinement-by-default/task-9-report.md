# Task 9 report (mountainash)

## Test migrations
None were needed. The full suite was green at HEAD f1e42a23 before any Task 9 change. The listed files already run on the
no-root or tmp_path paths: `test_resource_read_cross_backend.py` (programmatic `DataResource(...)`, `base_uri=tmp_path`),
`test_resource_schema_discovery.py` and `test_empty_resource_collect.py` (programmatic packages, rootless by decision 2),
`test_e2e_real_descriptor.py` (Task 7: `policy=LocationPolicy(root=tmp_path)`). Decode-only tests untouched. No assertion
changed, nothing deleted.

## Docs (commit a87bb6ec)
- CHANGELOG.md: new `## Unreleased` section (Breaking/Added/Fixed) per spec release notes, incl. the Ibis directory limit and unchanged SCHEMA directory limitation.
- docs/reference/datapackage.md: new "Location policy" section (loader/root table, opt-out, allow-list, copy/revalidate, limits).
- docs/reference/resource-read-support-matrix.md: new "Location policy" table (native allow-list, Ibis directory exception, other backends), dependency wiring corrected (transport required, `storage` extra removed, `ibis` includes files).

## Results
- Full suite (no coverage flags): 34968 passed, 160 skipped, 2767 xfailed.
- `hatch run ruff:check`: All checks passed.
- Not run: hatch test env / coverage (Ruling 5), mypy (policy).

## Installed-build smoke (fresh /tmp venv, non-editable; deleted afterwards)
Wheels built from transport-381 / files-381 / this branch (worktrees left clean).
Versions: mountainash 0.1.0, mountainash-transport 0.1.1, mountainash-files 0.1.1, mountainash-settings 0.1.0,
mountainash-auth-client 0.1.0, mountainash-data 0.1.0, ibis-framework 12.0.0, duckdb 1.5.6, polars 2.1.0, narwhals 2.28.0, pyarrow-hotfix 0.7.
- Task 7 file `test_location_policy_reads.py` (11-row case table on polars, narwhals, ibis-duckdb, ibis-polars, plus schema-phase, post-load assignment, opt-out, `%20`, glob-named root, directory cases) copied to /tmp and run against the installed wheels: **77 passed**.
- Extra script output (installed package, loaded from site-packages):
  schema ref outside root: rejected / opt-out schema ref: True / ResourceRef in-root: b'v\n1\n' / ResourceRef outside root: rejected /
  polars and narwhals assigned path outside root: rejected / opt-out ResourceRef outside root: b'S'.

## Concerns
1. `mountainash[ibis]` alone does not make Ibis usable: the first run failed with `No module named pyarrow_hotfix` and a DuckDB converter ImportError until `ibis-framework[duckdb,polars]==12.0.0` was installed explicitly (the extra pins bare `ibis-framework`, no backend extras). Pre-existing, not 381; the smoke installed those extras.
2. Installed env resolved polars 2.1.0 / narwhals 2.28.0 (spec probes were 2.0.0 / 2.27.1); the smoke still passed.
3. Backlog record edit skipped by instruction (controller). PR not opened.

## Fix round 1
Docs only: `policy=` now documented only on from_path/from_json/from_descriptor (datacontract has no override, confines to source parent) in datapackage.md and CHANGELOG; absolute-path claim qualified as "outside the root" in both.
