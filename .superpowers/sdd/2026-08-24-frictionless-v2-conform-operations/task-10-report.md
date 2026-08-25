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

### Controller-context final edge fixes

- `_shape_diff()` now treats an unknown recursive source child as shape drift before applying numeric GEOPOINT compatibility checks, avoiding an `AttributeError` for `SourceShape(None)` coordinate children while preserving the existing unknown top-level drift classification.
- Polars throw-mode GeoJSON parsing now supplies a strict `parse_constant` callback to `json.loads()`, rejecting `NaN`, `Infinity`, and `-Infinity` in the same way as null mode.
- Added regressions for unknown GEOPOINT array/object coordinate children and all three non-finite GeoJSON constants in both throw and null modes.

Targeted verification:

- `hatch run test:pytest -q tests/conform/test_final_branch_review_fixes.py`: **30 passed**.
- `hatch run test:pytest -q tests/conform/cross_backend/test_v2_operations.py -k 'geojson_parse_exceptional_documents_one_per_test or polars_geojson_parse_and_serialize'`: **361 passed, 497 deselected**.
- Changed-source/test Ruff check: **passed**.
- Changed-file `compileall`: **passed**.

## Whole-branch Important repairs

- Repaired complete source-representation dispatch: lexical `LIST` now accepts only string/unknown lexical evidence, native arrays require `ARRAY`, and incompatible list/struct/temporal sources are rejected for scalar, boolean, category, and temporal declarations.
- Preserved `evolve` actions for unknown source evidence and marked drift `applied` only for actions that change values or rows; `evolve` and `freeze` remain non-transforming.
- Routed canonical JSON sources through `PARSE_GEOJSON`, compared GEOPOINT object keys as an unordered exact `lon`/`lat` set, and retained ordered comparison for ordinary structs.
- Replaced Polars geospatial throw callbacks with native validity predicates and data-dependent cast markers.
- Replaced Polars default/XSD temporal callbacks with native parsing, validation, and throw-marker expressions. `PARSE_TEMPORAL_ANY` remains the sole permitted Polars Python parser.
- Removed the Narwhals-pandas categorical row loop and declared the nullable integer categorical cell as an exact capability gate.

Focused verification for this repair commit:

- `tests/conform/test_final_branch_review_fixes.py tests/conform/cross_backend/test_v2_type_actions.py`: **64 passed**.
- `tests/conform/cross_backend/test_temporal_operations.py`: **309 passed**.
- Polars/Narwhals geospatial and categorical matrix selection in `tests/conform/cross_backend/test_v2_operations.py`: **609 passed**.
- Contract/public DAG/list-array/capability selection: **629 passed, 660 deselected**.
- Ruff on all changed production files and focused regressions: **passed**.
- Changed-source/test `compileall`: **passed**.
- Native callback audit: targeted geospatial and categorical implementations contain no `map_elements`/`map_batches`; Polars temporal contains only the permitted `parse_temporal_any` batch parser.

## Pre-PR controller repairs

- Physical native `LIST` sources declared as lexical `LIST` now produce representation drift before field lowering, so configured `evolve`, `discard_value`, `discard_row`, and `freeze` actions reach the emitted field and follow their policy.
- GEOPOINT coordinate-key order is unordered only when the shape comparison is running in GEOPOINT numeric-child context; ordinary `OBJECT` structs with `lon` and `lat` remain ordered.
- The Narwhals categorical capability declarations now emit one `narwhals-lazy` integer gate instead of cloning duplicate facts.

Focused verification:

- `tests/conform/cross_backend/test_v2_type_actions.py tests/core/test_capability_declarations.py tests/core/test_capability_predicate_registry.py`: **51 passed**.
- Categorical capability coverage: **77 passed, 864 deselected**.

## Controller-context final datetime branch fix

- Masked each strict Polars default-datetime parser input with the
  `has_timezone` predicate before parsing, so strict timezone and naive
  branches never evaluate incompatible rows.
- Kept the anchored Frictionless grammar, UTC-naive offset normalization,
  and throw/null strictness unchanged.
- Added a public `DataPackage -> RelationDAG -> collect` regression covering
  mixed naive and offset-bearing valid datetime values.

Verification:

- Red regression before the production change: mixed public DAG input raised
  from the strict timezone parser on the naive row.
- Focused regression after the change: **1 passed, 2 deselected**.
- Final Unit C gate: **4156 passed, 39 skipped, 93 xfailed, 48 warnings**.
- Final public DAG smoke: **3 passed**.

## Release-confirmation source-dispatch repairs

- Plain native ARRAY and OBJECT declarations without child schemas now preserve
  their already-native LIST/STRUCT values instead of emitting bare container
  casts. Parameterized ARRAY declarations still lower child casts.
- UniversalType.ANY now accepts every physical source representation, including
  LIST, STRUCT, and JSON, and passes values through unchanged.
- Temporal source dispatch now uses an exact representation matrix: native
  DATE/TIME/TIMESTAMP values may cast to STRING; matching native temporal
  targets and lexical strings remain valid; only integer canonical sources
  (plus lexical/XSD YEAR forms) feed YEAR; numeric sources cannot feed
  DATE/TIME/DATETIME/DURATION/YEARMONTH.
- Explicitly unknown custom DATE/TIME/DATETIME, temporal-any, and YEAR
  representations raise UnresolvedSourceTypeError under transforming actions,
  while evolve preserves them. Unknown default DATE/TIME/DATETIME, DURATION,
  and YEARMONTH sources retain their lexical dispatch.
- Added focused matrix regressions, including the known-integer YEAR null
  preservation case.

Verification:

- Red source-dispatch regressions: **4 passed, 23 failed** before production
  changes (failures were the expected missing matrix behavior).
- `tests/conform/test_final_branch_review_fixes.py` and
  `tests/conform/cross_backend/test_v2_type_actions.py`: **98 passed**.
- `tests/conform/cross_backend/test_temporal_operations.py`: **309 passed**.
- Changed-source and regression Ruff check: **passed**.

## P1 absent source-shape normalization

- A supplied but incomplete `actual_shapes` map now normalizes missing
  top-level and dotted child lookups to `SourceShape(None)`, preserving the
  distinction between absent evidence and no shape-evidence mode.
- Unknown ANY is now an unresolved source representation under transforming
  actions, while evolve continues to pass it through.
- Added regressions for missing top-level shape entries, missing dotted child
  entries, and evolve handling across ARRAY, OBJECT, ANY, custom DATE, and
  YEAR.

Verification:

- Absent-shape regressions: **6 passed**.
- Full focused Unit C source-dispatch set after amendment: **413 passed**.

## Final-release review repairs

- Opaque `ANY` source shapes now pass through without synthetic unknown drift or unresolved-source errors, including absent shape evidence.
- Concrete physical `STRING` sources normalize configured missing sentinels even when the declared logical type is `ANY`; unknown non-lexical carriers remain untouched.
- Native `DURATION` sources are incompatible with lexical Frictionless `DURATION` and therefore follow the configured data-type action instead of bypassing XSD duration parsing.
- Structural-only type drift retains the configured data-type action in its report with `applied=False`; emitted fields remain free of value-transform actions.

Focused verification:

- `tests/conform/test_final_branch_review_fixes.py tests/conform/cross_backend/test_v2_type_actions.py`: **107 passed**.
- `tests/conform/cross_backend/test_missing_values.py`: **89 passed, 9 warnings**.
