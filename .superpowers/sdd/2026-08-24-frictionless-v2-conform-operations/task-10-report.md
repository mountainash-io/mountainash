# Task 10 report

## Status

Repository-local Task 10 closeout is complete. Commit: `95b0f974` (`feat(conform): complete Frictionless v2 conform operations`).

## Implemented

- Added `tests/relations/dag/test_v2_conform_e2e.py` with public `DataPackage.from_descriptor -> to_relation_dag(overrides=...) -> collect` evidence covering:
  - lexical LIST and native ARRAY values;
  - nested OBJECT and arrays of structs;
  - default, array, and object GEOPOINT formats;
  - lexical GEOJSON and TOPOJSON plus native GeoJSON serialization;
  - default datetime, XSD duration, partial dates, and `format="any"` datetime;
  - null preservation, public column shape, marker-column removal, and exact capability-fact attachment.
- Updated `DataPackage.to_relation_dag()` so in-memory overrides with a declared schema run through the same conform path as resource reads.
- Closed protocol/function/API wiring tests for Frictionless temporal operations, boolean token parsing, list GET/TO_ARRAY, conditional expressions, and geospatial protocol registration. Added the concise `parse_default`/`parse_datetime_default` alias rule to the wiring audit.
- Added a capability declaration-to-registry set-closure test for unsupported and materialization-residue facts.
- Added a set-parametrized data-type action evaluator closure test.
- Updated `docs/reference/datapackage.md` with observed DAG override, conform, list/array/object/geospatial/JSON/temporal, null, marker, and capability-error behavior.

## Verification evidence

- Focused Unit C gate command from Task 10: **4145 passed, 39 skipped, 93 xfailed, 49 warnings**.
- Final standalone public smoke command: **2 passed, 1 warning**.
- Ruff changed-scope command: **passed**.
- `git diff --check`: **passed**.
- `hatch run mypy:check`: fails on the repository baseline surface with 95 errors, consisting of missing third-party stubs/untyped optional dependencies and the pre-existing duplicate test-module discovery (`conform.cross_backend.test_v2_operations` vs `tests.conform.cross_backend.test_v2_operations`). No Task 10 implementation error was reported by the targeted runtime or Ruff gates.

## Deliberately left for Terra

- No pull request was created or pushed.
- `mountainash-central` was not modified. Central documentation/backlog records remain post-PR work for Terra after final whole-branch Sol review.
- No central merge or Unit C merged status is claimed.

## Review fixes

- Native GEOJSON/TOPOJSON struct carriers now lower through `serialize_geojson` before the public conform path rejects incompatible source shapes.
- The exact capability assertion now exercises `DataPackage -> RelationDAG -> conform -> collect` with a Narwhals carrier and asserts identity with the declared predicate fact.
- Replaced the declaration/registry tautology with an exhaustive Unit C unsupported/materialization-residue matrix closure derived from declared facts; each selector invokes `violations_for`, `capability_for`, or `residue_for` and asserts the scoped winning fact.
- Review-fix focused gates: **897 passed, 5 warnings**; Ruff passed; `git diff --check` passed.

## P2 matrix closure

- Exhaustive matrix selector regression: **1 passed**.

- Capability declaration plus public smoke focused gate after P2: **11 passed, 1 warning**.

## Final branch review fixes

- Unknown lexical LIST and default GEOPOINT sources now dispatch their lexical parsers; native and shape-dependent unknown forms remain unresolved.
- Incompatible concrete source shapes now apply `data_type` actions before source errors: evolve passes through, discard actions emit typed nulls, discard-row adds the post-missing row filter, and coerce raises `IncompatibleSourceTypeError`.
- Plain native ARRAY/OBJECT shapes are unconstrained; geospatial coordinate children accept every numeric canonical dtype; categorical declared output retains its base scalar type.
- Polars default datetime parsing now uses the anchored Frictionless grammar and normalizes offsets to UTC-naive values.
- Native Polars GeoJSON/TopoJSON serialization preserves top-level nulls.
- Integer YEAR values normalize sign-safely to four-digit lexical values before XSD partial-date validation; XSD duration validation accepts valid hour/minute-only forms.
- Coerce XSD operations retain throw behavior. Residue markers are compiled only for active matching non-null-to-null capability facts.
- Supported throw-mode conform materialization failures now wrap as `ConformTransformError` with active eligible diagnostics; unrelated failures remain raw.
- Added focused direct, relation, and public DAG regressions, including pandas/Narwhals-pandas unknown lexical dispatch, action materialization, shape wildcards, numeric GEOPOINT drift, category inference, datetime grammar/UTC normalization, YEAR normalization, GeoJSON null preservation, residue gating, and transform-error attribution.

### Final-fix verification

- `tests/conform/test_final_branch_review_fixes.py`: **22 passed**.
- Public DAG plus Polars geospatial smoke: **4 passed**.
- Polars GEOPOINT matrix: **56 passed**.
- Changed implementation and final-fix regression Ruff scope: **passed**.
- `compileall` over `src/mountainash` and changed tests: **passed**.
