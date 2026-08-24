# Task 6 report

Status: complete

## Implemented

- Added `python-dateutil>=2.9,<2.10` without introducing a lockfile.
- Added deterministic temporal parsers for temporal-any, default datetime, XSD duration, and XSD partial-date lexical values. The temporal-any parser preserves exact native types, applies the fixed two-digit year window, rejects unknown timezone tokens, and normalizes aware text to naive UTC.
- Added temporal function keys, registry mappings, API/protocol signatures, and backend implementations across Polars, Narwhals, and Ibis.
- Added `field_name` and `CaseFailureBehaviour` handling to custom `to_date`, `to_datetime`, and `to_time`, including explicit empty-name rejection.
- Added datetime capability declaration modules for default and temporal-any unsupported backend cells plus the XSD declaration module.
- Exported temporal parser symbols from `mountainash.typespec`.
- Added focused temporal parser and custom-temporal API tests.

## Verification

- `hatch run test:test-target-quick tests/typespec/test_temporal.py tests/core/test_signature_conformance.py tests/core/test_capability_declarations.py tests/conform/test_v2_operation_ast.py tests/conform/cross_backend/test_v2_operations.py tests/conform/cross_backend/test_conform_temporal_types.py tests/conform/cross_backend/test_temporal_format.py -k "temporal or datetime or duration or year or time" -v`
  - 648 passed, 2387 deselected, 12 existing deprecation warnings.
- `hatch run python -c "import dateutil; assert dateutil.__version__.startswith('2.9.'); print(dateutil.__version__)"`
  - `2.9.0.post0`.
- `hatch run ruff:check src/mountainash/typespec/temporal.py src/mountainash/expressions src/mountainash/core/capabilities/datetime tests/typespec/test_temporal.py`
  - All checks passed.
- `git diff --check`
  - Passed.

Commit: `feat(conform): add Frictionless temporal operations` (final hash reported with delivery)

## Correction wave

- Enforced XML Schema year/yearMonth lexical grammar, including valid `0000` and invalid plus-prefixed years/`-0000`, ASCII duration digits, and explicit duration guards.
- Restricted default datetime text to the required `T`-separated forms and normalized aware native datetime/time values to UTC-naive values.
- Added partial-date and temporal-any kind validation, exact `parse_datetime_default` wire naming, and diagnostic-only field metadata for new temporal operations.
- Updated backend signatures, custom temporal null-mode capability facts, and temporal AST contract coverage.

Correction verification:

- Final focused Task 6 command: 652 passed, 2387 deselected, 12 existing deprecation warnings.
- Temporal parser tests: 46 passed.
- Temporal signature subset: 59 passed.
- Temporal AST subset: 5 passed.
- Scoped Ruff checks and `git diff --check`: passed.

## Rereview correction wave

- Removed the global visitor option mutation; only custom temporal builders place optional field names in diagnostic metadata.
- Added `parse_datetime_default` protocol/backend dispatch and exact wire mapping.
- Hardened XSD grammar and backend null/throw validation predicates, timezone handling, `-0000` rejection, and non-Polars custom time capability facts.
- Rereview focused gates: 565 passed, 1575 deselected, 12 existing deprecation warnings.
