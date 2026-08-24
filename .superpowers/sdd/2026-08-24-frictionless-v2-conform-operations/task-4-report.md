# Task 4 report

## Status

Implemented the Task 4 list, categorical, and struct operation slices.

## Red/green evidence

- Red gate: `tests/conform/test_v2_operation_ast.py` and `tests/conform/cross_backend/test_v2_operations.py` were absent; the required command failed during collection with file-not-found.
- Green operation tests: `hatch run test:test-target-quick tests/conform/test_v2_operation_ast.py tests/conform/cross_backend/test_v2_operations.py -q` — **11 passed**.
- Scoped Ruff: `hatch run ruff:check src/mountainash/expressions src/mountainash/core/capabilities tests/conform/test_v2_operation_ast.py` — **all checks passed**.
- `git diff --check` passed.
- A focused wiring run reached 2,341 passing tests; four existing test-harness cases remain unrelated to this slice (conditional AST parking, GET/TO_ARRAY argument overrides, and aggregate protocol registry coverage).

## Delivered wiring

- Added `LIST.PARSE`, `LIST.CAST_ITEMS`, `CATEGORICAL.CAST`, and `STRUCT.CAST` enum keys, exact mappings, protocols, API builders, package exports, and all three backend families.
- Added `.str.parse_list()`, `.list.cast_items()`, `.cat.cast()`, `.struct.cast()` and `Domain.CATEGORICAL` / `Domain.STRUCT`.
- Added raw-option validation, diagnostic metadata separation, recursive `FieldSpec` option handling, complete-list null behavior, base-scalar categorical behavior, and capability declarations for the Task 4 matrix.
- Registered divergence `MA-CAT-01`.
- Added AST and cross-backend tests.
## Commit

`3f1ee462` — `feat(conform): add list category and struct operations`

## Concerns

- Ibis execution backends were not materialized locally because the environment lacks the optional `duckdb` package. Ibis expression compilation and capability gating were smoke-tested.
## Review-fix evidence

- Review-fix operation/capability tests: `25 passed`.
- API reachability and protocol alignment: `423 passed, 39 skipped, 37 xfailed`.
- Scoped Ruff and source compilation both pass.
- Review fixes are in amend commit `3f1ee462` after the follow-up changes.
## Re-review fix evidence

- Boolean throw mode now raises on invalid list tokens; null mode nulls the complete list.
- Recursive nested list/struct null-mode casts are atomic on newly-null non-null leaves.
- ALL_BACKENDS AST reachability and expanded invalid-option/recursive-serialization tests pass.
- Conditioned capability facts retain failure behavior selectors and values; ibis-sqlite categorical integer has one applicable fact.

## Round 4/5 residual-fix evidence

- Conditioned `LIST.PARSE` null limitations retain exact `param="failure_behavior"` / `option_value="null"` selectors while remaining predicate-gated; unsupported null facts are emitted only for item types supported in throw mode, and unsupported-in-both cells collapse to one wildcard gate. Duplicate SQLite categorical limitation was removed.
- Narwhals-pandas list parsing residue is now a materialization-scoped wildcard `UNSUPPORTED` fact. Narwhals and Ibis boolean parsers use only `true/True/TRUE/1` and `false/False/FALSE/0`; Polars mixed-case tokens remain rejected.
- Expanded AST validation covers every structural option shape, recursive list/struct `FieldSpec` serialization, and backend/native-node exclusion. Expanded cross-backend coverage executes all `ALL_BACKENDS` string-list materializations, exact SQLite gates, Polars/Narwhals/Ibis boolean paths, nested atomic null-mode casts, and conditioned selector gates.
- Focused operation suites: `41 passed`.
- Capability/declaration/divergence suites: `40 passed`.
- Scoped Ruff, `git diff --check`: passed.
- Final selected gate: `458 passed, 39 skipped, 37 xfailed`; Ruff and compileall pass.
