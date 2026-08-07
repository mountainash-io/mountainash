# Expression Coverage

<!-- GENERATED FILE — do not edit by hand. -->
<!-- Regenerate: hatch -e test run python -m mountainash.core.capabilities.render_markdown -->

Declarations: 30 · Facts: 1440 · Registered operations: 324

Legend — cell states:

- `✅` **DECLARED_CLEAN** — at least one capability declaration covers this
  op's (backend, source, domain) and no constraining fact exists for the op.
  Scope of the claim: the probe wave declared the backend×domain surface and
  recorded nothing against this op. Declarations carry no per-op probe
  manifest, so this is domain-wave-level evidence, not proof the specific op was exercised.
- `◐ partial (…)` / `✗ unsupported` / `poly` — **CONSTRAINED**: at least one
  GATE constraint or runtime residue fact applies (counts are distinct
  selector keys, never raw fact counts).
- `—` **UNDECLARED** — no declaration covers the coordinates; absence of
  facts means nothing here.
- Annotations: `↻ routed` (router metadata — handled via an alternate path),
  `⚠ runtime` (materialize-residue failure), `✓ dialect-verified`
  (dialect-scoped EXPR_CAPABLE refinement).
- `fidelity` is None on all EXECUTE facts by registration validation and is
  omitted from detail rows.

## Summary

| Backend | ✅ declared-clean | ◐ constrained | — undeclared |
| --- | --- | --- | --- |
| polars | 75 | 50 | 199 |
| narwhals | 152 | 75 | 97 |
| ibis | 118 | 68 | 138 |

### Fact statistics

| Axis | Breakdown |
| --- | --- |
| Level | expr_capable 155, literal_only 56, polymorphic 9, unsupported 1220 |
| Enforcement | gate 1434, router_metadata 3, materialize_residue 3 |
| Backend | polars 247, narwhals 618, ibis 575 |

`pandas` / `pyarrow` are routed input types (they execute via the narwhals path) and are not independent coverage columns.

### Audited pairs

| Backend | Source | Domain | Probe date | Library versions | Fixtures |
| --- | --- | --- | --- | --- | --- |
| ibis | mountainash | datetime | 2026-07-05 |  |  |
| ibis | mountainash | datetime | 2026-07-24 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| ibis | mountainash | datetime | 2026-07-25 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| ibis | mountainash | relation | 2026-07-05 |  |  |
| ibis | mountainash | set | — | — | — |
| ibis | mountainash | ternary | — | — | — |
| ibis | substrait | arithmetic | 2026-07-21 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| ibis | substrait | datetime | 2026-07-25 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| ibis | substrait | datetime | 2026-07-30 | ibis 12.0.0, narwhals 2.23.0 | polars, ibis-duckdb, ibis-polars, ibis-sqlite, narwhals-polars, narwhals-pandas |
| ibis | substrait | string | 2026-07-05 |  |  |
| ibis | substrait | string | 2026-07-23 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| narwhals | mountainash | datetime | 2026-07-05 |  |  |
| narwhals | mountainash | datetime | 2026-07-24 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| narwhals | mountainash | datetime | 2026-07-25 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| narwhals | mountainash | list | 2026-07-05 |  |  |
| narwhals | mountainash | relation | 2026-07-05 |  |  |
| narwhals | mountainash | set | — | — | — |
| narwhals | mountainash | ternary | — | — | — |
| narwhals | substrait | arithmetic | 2026-07-21 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| narwhals | substrait | datetime | 2026-07-25 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| narwhals | substrait | datetime | 2026-07-30 | ibis 12.0.0, narwhals 2.23.0 | polars, ibis-duckdb, ibis-polars, ibis-sqlite, narwhals-polars, narwhals-pandas |
| narwhals | substrait | string | 2026-07-05 |  |  |
| narwhals | substrait | string | 2026-07-05 | narwhals 2.19.0 |  |
| narwhals | substrait | string | 2026-07-23 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| polars | mountainash | relation | 2026-07-05 |  |  |
| polars | mountainash | set | — | — | — |
| polars | mountainash | ternary | — | — | — |
| polars | substrait | arithmetic | 2026-07-21 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| polars | substrait | string | 2026-07-05 |  | polars |
| polars | substrait | string | 2026-07-23 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |

## Per-family coverage

### `FKEY_MOUNTAINASH_SCALAR_ARITHMETIC` (mountainash / arithmetic)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `FLOOR_DIVIDE` | — | — | — |

### `FKEY_MOUNTAINASH_SCALAR_DATETIME` (mountainash / datetime)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `ADD_DAYS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_HOURS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MICROSECONDS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MILLISECONDS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MINUTES` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MONTHS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_SECONDS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_YEARS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `CEIL` | — | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 2 dialects) | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 1 dialects) |
| `DATE` | — | ✅ | ✅ |
| `DAYS_IN_MONTH` | — | ✅ | ✅ |
| `DIFF_DAYS` | — | ✅ | ✅ |
| `DIFF_HOURS` | — | ✅ | ✅ |
| `DIFF_MILLISECONDS` | — | ✅ | ✅ |
| `DIFF_MINUTES` | — | ✅ | ✅ |
| `DIFF_MONTHS` | — | ✅ | ✅ |
| `DIFF_SECONDS` | — | ✅ | ✅ |
| `DIFF_YEARS` | — | ✅ | ✅ |
| `EXTRACT_DAY` | — | ✅ | ✅ |
| `EXTRACT_DAY_OF_YEAR` | — | ✅ | ✅ |
| `EXTRACT_HOUR` | — | ✅ | ✅ |
| `EXTRACT_ISO_YEAR` | — | ✅ | ✅ |
| `EXTRACT_MICROSECOND` | — | ✅ | ✅ |
| `EXTRACT_MILLISECOND` | — | ✅ | ✅ |
| `EXTRACT_MINUTE` | — | ✅ | ✅ |
| `EXTRACT_MONTH` | — | ✅ | ✅ |
| `EXTRACT_NANOSECOND` | — | ✅ | ✅ |
| `EXTRACT_QUARTER` | — | ✅ | ✅ |
| `EXTRACT_SECOND` | — | ✅ | ✅ |
| `EXTRACT_TIMEZONE_OFFSET` | — | ✅ | ✅ |
| `EXTRACT_UNIX_TIME` | — | ✅ | ✅ |
| `EXTRACT_WEEK` | — | ✅ | ✅ |
| `EXTRACT_WEEKDAY` | — | ✅ | ✅ |
| `EXTRACT_YEAR` | — | ✅ | ✅ |
| `FLOOR` | — | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 2 option-selectors, 1 value-classes, 1 dialects) |
| `IS_DST` | — | ✅ | ✅ |
| `IS_LEAP_YEAR` | — | ✅ | ✅ |
| `MONTH_END` | — | ✅ | ✅ |
| `MONTH_START` | — | ✅ | ✅ |
| `NOW` | — | ✅ | ✅ |
| `OFFSET_BY` | — | ✅ | ✅ |
| `ROUND` | — | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 2 dialects) | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 1 dialects) |
| `TIME` | — | ✅ | ✅ |
| `TODAY` | — | ✅ | ✅ |
| `TOTAL_DAYS` | — | ✅ | ✅ |
| `TOTAL_HOURS` | — | ✅ | ✅ |
| `TOTAL_MICROSECONDS` | — | ✅ | ✅ |
| `TOTAL_MILLISECONDS` | — | ✅ | ✅ |
| `TOTAL_MINUTES` | — | ✅ | ✅ |
| `TOTAL_NANOSECONDS` | — | ✅ | ✅ |
| `TOTAL_SECONDS` | — | ✅ | ✅ |
| `TO_TIMEZONE` | — | ✅ | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 1 dialects) |
| `TRUNCATE` | — | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 2 option-selectors, 1 value-classes, 1 dialects) |

### `FKEY_MOUNTAINASH_SCALAR_LIST` (mountainash / list)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `AGG` | — | ✅ | — |
| `ALL` | — | ✅ | — |
| `ANY` | — | ✅ | — |
| `ARG_MAX` | — | ✅ | — |
| `ARG_MIN` | — | ✅ | — |
| `CONCAT` | — | ✅ | — |
| `CONTAINS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) ⚠ runtime | — |
| `COUNT_MATCHES` | — | ✅ | — |
| `DIFF` | — | ✅ | — |
| `DROP_NULLS` | — | ✅ | — |
| `EXPLODE` | — | ✅ | — |
| `FILTER` | — | ✅ | — |
| `GATHER` | — | ✅ | — |
| `GATHER_EVERY` | — | ✅ | — |
| `GET` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) ⚠ runtime | — |
| `HEAD` | — | ✅ | — |
| `ITEM` | — | ✅ | — |
| `JOIN` | — | ✅ | — |
| `LEN` | — | ✅ | — |
| `MAX` | — | ✅ | — |
| `MEAN` | — | ✅ | — |
| `MEDIAN` | — | ✅ | — |
| `MIN` | — | ✅ | — |
| `N_UNIQUE` | — | ✅ | — |
| `REVERSE` | — | ✅ | — |
| `SAMPLE` | — | ✅ | — |
| `SET_DIFFERENCE` | — | ✅ | — |
| `SET_INTERSECTION` | — | ✅ | — |
| `SET_SYMMETRIC_DIFFERENCE` | — | ✅ | — |
| `SET_UNION` | — | ✅ | — |
| `SHIFT` | — | ✅ | — |
| `SLICE` | — | ✅ | — |
| `SORT` | — | ✅ | — |
| `STD` | — | ✅ | — |
| `SUM` | — | ✅ | — |
| `TAIL` | — | ✅ | — |
| `TO_ARRAY` | — | ✅ | — |
| `TO_STRUCT` | — | ✅ | — |
| `T_CONTAINS` | — | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) ⚠ runtime | — |
| `UNIQUE` | — | ✅ | — |
| `VAR` | — | ✅ | — |

### `FKEY_MOUNTAINASH_SCALAR_SET` (mountainash / set)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `IS_IN` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `IS_NOT_IN` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |

### `FKEY_MOUNTAINASH_SCALAR_STRING` (mountainash / string)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `DECODE` | — | — | — |
| `ENCODE` | — | — | — |
| `EXTRACT_GROUPS` | — | — | — |
| `JSON_DECODE` | — | — | — |
| `JSON_PATH_MATCH` | — | — | — |
| `REGEX_CONTAINS` | — | — | — |
| `STRIP_SUFFIX` | — | — | — |
| `TO_INTEGER` | — | — | — |
| `TO_TIME` | — | — | — |

### `FKEY_MOUNTAINASH_SCALAR_TERNARY` (mountainash / ternary)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `ALWAYS_FALSE` | ✅ | ✅ | ✅ |
| `ALWAYS_TRUE` | ✅ | ✅ | ✅ |
| `ALWAYS_UNKNOWN` | ✅ | ✅ | ✅ |
| `COLLECT_VALUES` | poly | poly | poly |
| `IS_FALSE` | ✅ | ✅ | ✅ |
| `IS_KNOWN` | ✅ | ✅ | ✅ |
| `IS_TRUE` | ✅ | ✅ | ✅ |
| `IS_UNKNOWN` | ✅ | ✅ | ✅ |
| `MAYBE_FALSE` | ✅ | ✅ | ✅ |
| `MAYBE_TRUE` | ✅ | ✅ | ✅ |
| `TO_TERNARY` | ✅ | ✅ | ✅ |
| `T_AND` | ✅ | ✅ | ✅ |
| `T_EQ` | ✅ | ✅ | ✅ |
| `T_GE` | ✅ | ✅ | ✅ |
| `T_GT` | ✅ | ✅ | ✅ |
| `T_IS_IN` | ✅ | ✅ | ✅ |
| `T_IS_NOT_IN` | ✅ | ✅ | ✅ |
| `T_LE` | ✅ | ✅ | ✅ |
| `T_LT` | ✅ | ✅ | ✅ |
| `T_NE` | ✅ | ✅ | ✅ |
| `T_NOT` | ✅ | ✅ | ✅ |
| `T_OR` | ✅ | ✅ | ✅ |
| `T_XOR` | ✅ | ✅ | ✅ |
| `T_XOR_PARITY` | ✅ | ✅ | ✅ |

### `FKEY_SUBSTRAIT_SCALAR_ARITHMETIC` (substrait / arithmetic)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `ABS` | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 3 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `ACOS` | ◐ partial (2 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `ACOSH` | ◐ partial (2 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) |
| `ADD` | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (2 params, 8 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `ASIN` | ◐ partial (2 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `ASINH` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `ATAN` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `ATAN2` | ◐ partial (2 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) |
| `ATANH` | ◐ partial (2 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) |
| `BITWISE_AND` | ✅ | ✅ | ✅ |
| `BITWISE_NOT` | ✅ | ✅ | ✅ |
| `BITWISE_OR` | ✅ | ✅ | ✅ |
| `BITWISE_XOR` | ✅ | ✅ | ✅ |
| `COS` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `COSH` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `DEGREES` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `DIVIDE` | ◐ partial (4 params, 13 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (4 params, 15 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (4 params, 15 option-selectors, 0 value-classes, 1 dialects) |
| `EXP` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `MODULO` | ◐ partial (3 params, 4 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (3 params, 4 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (3 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `MULTIPLY` | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (2 params, 8 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `NEGATE` | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 3 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `POWER` | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 3 option-selectors, 0 value-classes, 1 dialects) |
| `RADIANS` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `SHIFT_LEFT` | ✅ | ✅ | ✅ |
| `SHIFT_RIGHT` | ✅ | ✅ | ✅ |
| `SHIFT_RIGHT_UNSIGNED` | ✅ | ✅ | ✅ |
| `SIGN` | ✅ | ✅ | ✅ |
| `SIN` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `SINH` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `SQRT` | ◐ partial (2 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `SUBTRACT` | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (2 params, 8 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `TAN` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `TANH` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |

### `FKEY_SUBSTRAIT_SCALAR_DATETIME` (substrait / datetime)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `ADD_INTERVALS` | — | ✅ | ✅ |
| `ASSUME_TIMEZONE` | — | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 2 dialects) | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 1 dialects) |
| `EXTRACT` | — | ✅ | ✅ |
| `EXTRACT_BOOLEAN` | — | ✅ | ✅ |
| `LOCAL_TIMESTAMP` | — | ✅ | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 1 dialects) |
| `STRFTIME` | — | ✅ | ✅ |
| `STRPTIME_DATE` | — | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) |
| `STRPTIME_TIMESTAMP` | — | ✅ | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) |

### `FKEY_SUBSTRAIT_SCALAR_SET` (substrait / set)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `INDEX_IN` | — | — | — |

### `FKEY_SUBSTRAIT_SCALAR_STRING` (substrait / string)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `BIT_LENGTH` | ✅ | ✅ | ✅ |
| `CAPITALIZE` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `CENTER` | ◐ partial (3 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (3 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `CHAR_LENGTH` | ✅ | ✅ | ✅ |
| `CONCAT` | ✅ | ✅ | ✅ |
| `CONCAT_WS` | ✅ | ✅ | ✅ |
| `CONTAINS` | ✅ ✓ dialect-verified: polars | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ✅ ✓ dialect-verified: ibis-duckdb |
| `COUNT_SUBSTRING` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `ENDS_WITH` | ✅ ✓ dialect-verified: polars | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ✅ ✓ dialect-verified: ibis-duckdb |
| `INITCAP` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) |
| `LEFT` | ✅ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✅ |
| `LIKE` | ◐ partial (2 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `LOWER` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `LPAD` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (2 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✅ |
| `LTRIM` | ✅ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `OCTET_LENGTH` | ✅ | ✅ | ✅ |
| `REGEXP_COUNT` | ◐ partial (4 params, 4 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (4 params, 7 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (4 params, 7 option-selectors, 0 value-classes, 1 dialects) |
| `REGEXP_MATCH` | ◐ partial (5 params, 5 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (6 params, 6 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (5 params, 5 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `REGEXP_MATCH_ALL` | ◐ partial (5 params, 5 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (5 params, 8 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (5 params, 8 option-selectors, 0 value-classes, 1 dialects) |
| `REGEXP_REPLACE` | ◐ partial (5 params, 4 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (7 params, 5 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ◐ partial (5 params, 5 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `REGEXP_SPLIT` | ◐ partial (3 params, 3 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (3 params, 3 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (3 params, 3 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `REGEXP_STRPOS` | ◐ partial (5 params, 5 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (5 params, 8 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (5 params, 8 option-selectors, 0 value-classes, 1 dialects) |
| `REPEAT` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✅ | ✅ |
| `REPLACE` | ◐ partial (2 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (3 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `REPLACE_SLICE` | ◐ partial (3 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✅ | ◐ partial (3 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `REVERSE` | ✅ | ✅ | ✅ |
| `RIGHT` | ✅ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✅ |
| `RPAD` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (2 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✅ |
| `RTRIM` | ✅ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `SPLIT` | ✅ | ✅ | ✅ |
| `STARTS_WITH` | ✅ ✓ dialect-verified: polars | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ✅ ✓ dialect-verified: ibis-duckdb |
| `STRPOS` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `SUBSTRING` | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (3 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `SWAPCASE` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) |
| `TITLE` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) |
| `TRIM` | ✅ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `UPPER` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |

### `RKEY_MOUNTAINASH_REL` (mountainash / relation)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `CONFORM` | ✅ | ✅ | ✅ |
| `DROP_NANS` | ✅ | ✅ | ✅ |
| `DROP_NULLS` | ✅ | ✅ | ✅ |
| `EMPTY_FRAME` | ✅ | ✅ | ✅ |
| `EXPLODE` | ✅ | ✅ | ✅ |
| `FETCH_FROM_END` | ✅ | ✅ | ✅ |
| `JOIN_ASOF` | ✅ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✅ |
| `PIVOT` | ✅ | ✅ | ✅ |
| `READ_RESOURCE` | ✅ ↻ routed | ✅ ↻ routed | ✅ ↻ routed |
| `REF` | ✅ | ✅ | ✅ |
| `SAMPLE` | ✅ | ✅ | ✅ |
| `SOURCE` | ✅ | ✅ | ✅ |
| `TOP_K` | ✅ | ✅ | ✅ |
| `UNNEST` | ✅ | ✗ unsupported | ✅ |
| `UNPIVOT` | ✅ | ✅ | ✅ |
| `WITH_ROW_INDEX` | ✅ | ✅ | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) |

### `RKEY_SUBSTRAIT_REL` (mountainash / relation)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `AGGREGATE` | ✅ | ✅ | ✅ |
| `DISTINCT` | ✅ | ✅ | ✅ |
| `FETCH` | ✅ | ✅ | ✅ |
| `FILTER` | ✅ | ✅ | ✅ |
| `JOIN` | ✅ | ✅ | ✅ |
| `PROJECT_DROP` | ✅ | ✅ | ✅ |
| `PROJECT_RENAME` | ✅ | ✅ | ✅ |
| `PROJECT_SELECT` | ✅ | ✅ | ✅ |
| `PROJECT_WITH_COLUMNS` | ✅ | ✅ | ✅ |
| `READ` | ✅ | ✅ | ✅ |
| `SORT` | ✅ | ✅ | ✅ |
| `UNION_ALL` | ✅ | ✅ | ✅ |
| `UNION_DISTINCT` | ✅ | ✅ | ✅ |

## Unmapped families

No declaration domain exists for these enum classes yet; every cell is UNDECLARED. Extending coverage here starts at `classify_domain`/`_DOMAIN_SUFFIXES` (spec §3.2).

- `FKEY_MOUNTAINASH_NAME` (5 ops): `ALIAS`, `NAME_TO_LOWER`, `NAME_TO_UPPER`, `PREFIX`, `SUFFIX`
- `FKEY_MOUNTAINASH_NULL` (3 ops): `FILL_NAN`, `FILL_NULL`, `NULL_IF`
- `FKEY_MOUNTAINASH_SCALAR_AGGREGATE` (1 ops): `COUNT_DISTINCT`
- `FKEY_MOUNTAINASH_SCALAR_BOOLEAN` (1 ops): `XOR_PARITY`
- `FKEY_MOUNTAINASH_SCALAR_COMPARISON` (1 ops): `IS_DUPLICATED`
- `FKEY_MOUNTAINASH_SCALAR_STRUCT` (1 ops): `FIELD`
- `FKEY_MOUNTAINASH_WINDOW` (10 ops): `BACKWARD_FILL`, `CUM_COUNT`, `CUM_MAX`, `CUM_MIN`, `CUM_PROD`, `CUM_SUM`, `DIFF`, `FORWARD_FILL`, `RANK_AVERAGE`, `RANK_MAX`
- `FKEY_SUBSTRAIT_CAST` (1 ops): `CAST`
- `FKEY_SUBSTRAIT_CONDITIONAL` (1 ops): `IF_THEN_ELSE`
- `FKEY_SUBSTRAIT_SCALAR_AGGREGATE` (16 ops): `ANY_VALUE`, `AVG`, `BOOL_AND`, `BOOL_OR`, `CORR`, `COUNT`, `COUNT_RECORDS`, `MAX`, `MEDIAN`, `MIN`, `MODE`, `PRODUCT`, `QUANTILE`, `STD_DEV`, `SUM`, `VARIANCE`
- `FKEY_SUBSTRAIT_SCALAR_BOOLEAN` (5 ops): `AND`, `AND_NOT`, `NOT`, `OR`, `XOR`
- `FKEY_SUBSTRAIT_SCALAR_COMPARISON` (22 ops): `BETWEEN`, `COALESCE`, `EQUAL`, `GREATEST`, `GREATEST_SKIP_NULL`, `GT`, `GTE`, `IS_FALSE`, `IS_FINITE`, `IS_INFINITE`, `IS_NAN`, `IS_NOT_FALSE`, `IS_NOT_NULL`, `IS_NOT_TRUE`, `IS_NULL`, `IS_TRUE`, `LEAST`, `LEAST_SKIP_NULL`, `LT`, `LTE`, `NOT_EQUAL`, `NULL_IF`
- `FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC` (5 ops): `LOG`, `LOG10`, `LOG1P`, `LOG2`, `LOGB`
- `FKEY_SUBSTRAIT_SCALAR_ROUNDING` (3 ops): `CEIL`, `FLOOR`, `ROUND`
- `SUBSTRAIT_ARITHMETIC_WINDOW` (11 ops): `CUME_DIST`, `DENSE_RANK`, `FIRST_VALUE`, `LAG`, `LAST_VALUE`, `LEAD`, `NTH_VALUE`, `NTILE`, `PERCENT_RANK`, `RANK`, `ROW_NUMBER`

## Per-op detail

### `ADD_DAYS` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | days | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_DAYS` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | days | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `ADD_HOURS` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | hours | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_HOURS` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | hours | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `ADD_MICROSECONDS` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | microseconds | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_MICROSECONDS` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | microseconds | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `ADD_MILLISECONDS` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | milliseconds | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_MILLISECONDS` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | milliseconds | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `ADD_MINUTES` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | minutes | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_MINUTES` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | minutes | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `ADD_MONTHS` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | months | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_MONTHS` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | months | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `ADD_SECONDS` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | seconds | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_SECONDS` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | seconds | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `ADD_YEARS` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | years | — | — | literal_only | gate | build | — | Narwhals datetime offset operations require literal integer values | Use a literal integer for the offset amount | NW-DT-01 | 2026-07-05 | — | — |

### `ADD_YEARS` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | years | — | — | literal_only | gate | build | — | Ibis datetime offset operations require literal integer values | Use a literal integer for the offset amount | IB-DT-01 | 2026-07-05 | — | — |

### `CEIL` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | unit | — | duration_multiplier | unsupported | gate | build | — | narwhals has no native datetime round/ceil; a multiplier value silently falls back to truncate and returns a wrong (down-rounded) result | — | — | 2026-07-25 | — | — |
| narwhals-pandas | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | narwhals has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |
| narwhals-polars | unit | — | duration_multiplier | unsupported | gate | build | — | narwhals has no native datetime round/ceil; a multiplier value silently falls back to truncate and returns a wrong (down-rounded) result | — | — | 2026-07-25 | — | — |
| narwhals-polars | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | narwhals has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |

### `CEIL` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| * | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | ibis has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |
| ibis-duckdb | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| ibis-duckdb | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | ibis has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |

### `FLOOR` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | unit | 1w | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |
| narwhals-pandas | unit | week | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |
| narwhals-polars | unit | 1w | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |
| narwhals-polars | unit | week | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |

### `FLOOR` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| * | unit | 1q | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |
| * | unit | quarter | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |
| ibis-duckdb | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| ibis-duckdb | unit | 1q | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |
| ibis-duckdb | unit | quarter | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |

### `ROUND` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | unit | — | duration_multiplier | unsupported | gate | build | — | narwhals has no native datetime round/ceil; a multiplier value silently falls back to truncate and returns a wrong (down-rounded) result | — | — | 2026-07-25 | — | — |
| narwhals-pandas | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | narwhals has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |
| narwhals-polars | unit | — | duration_multiplier | unsupported | gate | build | — | narwhals has no native datetime round/ceil; a multiplier value silently falls back to truncate and returns a wrong (down-rounded) result | — | — | 2026-07-25 | — | — |
| narwhals-polars | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | narwhals has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |

### `ROUND` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| * | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | ibis has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |
| ibis-duckdb | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| ibis-duckdb | unit | 1d, 1h, 1m, 1mo, 1ms, 1q, 1s, 1us, 1w, 1y, day, hour, microsecond, millisecond, minute, month, quarter, second, week, year | — | unsupported | gate | build | — | ibis has no native datetime round/ceil; silently falling back to truncate would return a wrong value | — | — | 2026-07-24 | — | — |

### `TO_TIMEZONE` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | to_timezone is correct only at the materialization boundary -- the target zone lives in the ibis output dtype, not in the engine (SQL is a bare CAST AS TIMESTAMPTZ), so any expression composed on the result raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb) | — | — | 2026-07-29 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | to_timezone is correct only at the materialization boundary -- the target zone lives in the ibis output dtype, not in the engine (SQL is a bare CAST AS TIMESTAMPTZ), so any expression composed on the result raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb) | — | — | 2026-07-29 | — | — |

### `TRUNCATE` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | unit | 1w | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |
| narwhals-pandas | unit | week | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |
| narwhals-polars | unit | 1w | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |
| narwhals-polars | unit | week | — | unsupported | gate | build | — | narwhals truncate rejects the week unit '1w' (and its friendly alias 'week') | — | — | 2026-07-24 | — | — |

### `TRUNCATE` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| * | unit | 1q | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |
| * | unit | quarter | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |
| ibis-duckdb | unit | — | duration_multiplier | unsupported | gate | build | — | ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted | — | — | 2026-07-25 | — | — |
| ibis-duckdb | unit | 1q | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |
| ibis-duckdb | unit | quarter | — | unsupported | gate | build | — | ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter') | — | — | 2026-07-24 | — | — |

### `CONTAINS` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | item | — | — | literal_only | gate | build | — | Narwhals list.contains() requires a literal item argument, not a column expression | Use a literal value for item or use the Polars/Ibis backend. | NW-LIST-01 | 2026-07-05 | — | — |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | Narwhals list operations on pandas require PyArrow-backed list columns. | Convert column to PyArrow list or use the Polars backend. | NW-LIST-01 | 2026-07-05 | TypeError | whole-op materialize-time storage residue (narwhals-pandas PyArrow-list requirement); enriched after the visitor, not an arg-type gate |

### `GET` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-polars | index | — | — | unsupported | materialize_residue | materialize | index < 0 | narwhals list.get() (and list.last(), which calls get(-1)) rejects negative indices on the polars backend. | Use a non-negative index, or the polars/ibis backends. | NW-LIST-04 | 2026-08-01 | ValueError | value-conditioned (negative index) — not a structural param gate |

### `T_CONTAINS` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | item | — | — | literal_only | gate | build | — | Narwhals list.t_contains() requires a literal item argument, not a column expression | Use a literal value for item or use the Polars/Ibis backend. | NW-LIST-01 | 2026-07-05 | — | — |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | Narwhals list operations on pandas require PyArrow-backed list columns. | Convert column to PyArrow list or use the Polars backend. | NW-LIST-01 | 2026-07-05 | TypeError | whole-op materialize-time storage residue (narwhals-pandas PyArrow-list requirement); enriched after the visitor, not an arg-type gate |

### `IS_IN` × polars (FKEY_MOUNTAINASH_SCALAR_SET)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | haystack | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `IS_IN` × narwhals (FKEY_MOUNTAINASH_SCALAR_SET)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | haystack | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `IS_IN` × ibis (FKEY_MOUNTAINASH_SCALAR_SET)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | haystack | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `IS_NOT_IN` × polars (FKEY_MOUNTAINASH_SCALAR_SET)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | haystack | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `IS_NOT_IN` × narwhals (FKEY_MOUNTAINASH_SCALAR_SET)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | haystack | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `IS_NOT_IN` × ibis (FKEY_MOUNTAINASH_SCALAR_SET)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | haystack | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `COLLECT_VALUES` × polars (FKEY_MOUNTAINASH_SCALAR_TERNARY)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `COLLECT_VALUES` × narwhals (FKEY_MOUNTAINASH_SCALAR_TERNARY)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `COLLECT_VALUES` × ibis (FKEY_MOUNTAINASH_SCALAR_TERNARY)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | polymorphic | gate | build | — | literal collections unwrap to raw values; expressions compile through (LIST-wrapper marker) | — | — | 2026-07-05 | — | polymorphic — both paths supported by design |

### `ABS` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `ABS` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `ABS` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |

### `ACOS` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ACOS` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ACOS` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR | — | expr_capable | gate | build | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ACOSH` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ACOSH` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ACOSH` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ADD` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ADD` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ADD` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ASIN` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ASIN` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ASIN` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR | — | expr_capable | gate | build | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ASINH` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ASINH` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ASINH` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATAN` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATAN` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATAN` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATAN2` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATAN2` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATAN2` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATANH` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATANH` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ATANH` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `COS` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `COS` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `COS` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `COSH` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `COSH` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `COSH` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `DEGREES` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `DEGREES` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `DEGREES` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `DIVIDE` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | on_division_by_zero | ERROR, LIMIT, NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_division_by_zero | IEEE | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | on_domain_error | NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `DIVIDE` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | on_division_by_zero | ERROR, IEEE, LIMIT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_division_by_zero | NULL | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NULL | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-pandas | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | on_division_by_zero | ERROR, LIMIT, NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_division_by_zero | IEEE | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-polars | on_domain_error | NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `DIVIDE` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | on_division_by_zero | ERROR, IEEE, LIMIT, NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | ERROR, NAN, NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | on_division_by_zero | ERROR, IEEE, LIMIT, NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR, NAN, NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `EXP` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `EXP` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `EXP` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `MODULO` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | division_type | FLOOR | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | division_type | TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NULL | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `MODULO` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | division_type | FLOOR | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-pandas | division_type | TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NULL | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-pandas | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-polars | division_type | FLOOR | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-polars | division_type | TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NULL | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `MODULO` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | division_type | FLOOR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | division_type | TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | division_type | FLOOR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | division_type | TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | NULL | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |

### `MULTIPLY` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `MULTIPLY` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `MULTIPLY` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `NEGATE` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `NEGATE` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `NEGATE` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |

### `POWER` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |
| polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |
| polars | overflow | SILENT | — | expr_capable | gate | build | — | Explicit SILENT selects the native backend's i64 power wrapping behavior, so it is observably equivalent to omission and cannot discriminate | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `POWER` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SILENT | — | expr_capable | gate | build | — | Explicit SILENT selects the native backend's i64 power wrapping behavior, so it is observably equivalent to omission and cannot discriminate | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SILENT | — | expr_capable | gate | build | — | Explicit SILENT selects the native backend's i64 power wrapping behavior, so it is observably equivalent to omission and cannot discriminate | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |

### `POWER` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait i64 power overflow mode | Pre-check the i64 base and exponent and handle out-of-range powers before calling power() | — | 2026-07-21 | — | — |

### `RADIANS` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `RADIANS` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `RADIANS` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SIN` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SIN` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SIN` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SINH` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SINH` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SINH` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SQRT` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SQRT` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| narwhals-polars | on_domain_error | NAN | — | expr_capable | gate | build | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The native omission path already has the requested arithmetic semantics, so the explicit option cannot discriminate |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SQRT` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | on_domain_error | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | on_domain_error | ERROR | — | expr_capable | gate | build | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | on_domain_error | NAN | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait arithmetic option semantics | Pre-handle invalid arithmetic inputs and select the requested result before evaluating the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SUBTRACT` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SUBTRACT` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-pandas | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | ERROR | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| narwhals-polars | overflow | SILENT | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `SUBTRACT` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | overflow | ERROR, SATURATE, SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | ERROR | — | expr_capable | gate | build | — | The explicit option selects the native backend's existing behavior, so it is observably equivalent to omission and cannot discriminate | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | The DuckDB omission path raises the exact exception required by the requested ERROR semantics, so the explicit option is equivalent |
| ibis-duckdb | overflow | SATURATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | overflow | SILENT | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait integer overflow mode | Cast operands to a wider integer dtype before the operation | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `TAN` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `TAN` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `TAN` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `TANH` × polars (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `TANH` × narwhals (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| narwhals-polars | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `TANH` × ibis (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |
| ibis-duckdb | rounding | CEILING, FLOOR, TIE_AWAY_FROM_ZERO, TIE_TO_EVEN, TRUNCATE | — | unsupported | gate | build | — | The native backend does not implement the requested Substrait IEEE rounding mode | Evaluate with native rounding, then apply an explicit application-level numeric policy | — | 2026-07-21 | — | — |

### `ASSUME_TIMEZONE` × narwhals (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | timezone | — | iana_timezone | unsupported | gate | build | — | assume_timezone silently drops the timezone (returns a naive timestamp) — the tz argument is ignored; only polars attaches the timezone | — | — | 2026-07-25 | — | — |
| narwhals-polars | timezone | — | iana_timezone | unsupported | gate | build | — | assume_timezone silently drops the timezone (returns a naive timestamp) — the tz argument is ignored; only polars attaches the timezone | — | — | 2026-07-25 | — | — |

### `ASSUME_TIMEZONE` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | assume_timezone silently drops the timezone (returns a naive timestamp) — the tz argument is ignored; only polars attaches the timezone | — | — | 2026-07-25 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | assume_timezone silently drops the timezone (returns a naive timestamp) — the tz argument is ignored; only polars attaches the timezone | — | — | 2026-07-25 | — | — |

### `LOCAL_TIMESTAMP` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | local_timestamp returns the UTC wall clock, not the target-zone wall clock -- ibis has no timezone method and the naive re-cast discards the conversion (verified 2026-07-29, ibis 12.0.0/duckdb: 12:00 instead of 17:30 for Asia/Kolkata) | — | — | 2026-07-29 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | local_timestamp returns the UTC wall clock, not the target-zone wall clock -- ibis has no timezone method and the naive re-cast discards the conversion (verified 2026-07-29, ibis 12.0.0/duckdb: 12:00 instead of 17:30 for Asia/Kolkata) | — | — | 2026-07-29 | — | — |

### `STRPTIME_DATE` × narwhals (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | gate | build | — | narwhals raises NotImplementedError for str.to_date() on the default pandas backend (it would return an object-dtype Series, diverging from the polars API); str.to_datetime() is unaffected and stays supported | — | — | 2026-07-30 | — | whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py |

### `STRPTIME_DATE` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | ibis-sqlite has no compilation rule for StringToDate/StringToTimestamp (OperationNotDefinedError); format-driven parsing is unavailable on this dialect, so it is gated rather than left to fail natively | — | — | 2026-07-30 | — | whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py |

### `STRPTIME_TIMESTAMP` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | ibis-sqlite has no compilation rule for StringToDate/StringToTimestamp (OperationNotDefinedError); format-driven parsing is unavailable on this dialect, so it is gated rather than left to fail natively | — | — | 2026-07-30 | — | whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py |

### `CAPITALIZE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `CAPITALIZE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |
| narwhals-pandas | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |

### `CAPITALIZE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `CENTER` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | character | — | — | literal_only | gate | build | — | Polars str.center() requires a single literal fill character, not a column expression | Use a literal single-character string | PL-STR-03 | 2026-07-05 | — | — |
| * | length | — | — | literal_only | gate | build | — | Polars str.center() requires a literal integer length, not a column expression | Use a literal integer length value | PL-STR-03 | 2026-07-05 | — | — |
| polars | padding | LEFT | — | unsupported | gate | build | — | The native backend does not implement LEFT padding semantics for center | — | — | 2026-07-23 | — | — |
| polars | padding | RIGHT | — | expr_capable | gate | build | — | RIGHT is the builder default, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | RIGHT is the builder default, so the explicit option is observably equivalent to omission and cannot discriminate |

### `CENTER` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |
| narwhals-pandas | padding | LEFT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | padding | RIGHT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | padding | LEFT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | padding | RIGHT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |

### `CENTER` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | character | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | — |
| * | length | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | — |
| * | padding | LEFT | — | unsupported | gate | build | — | The native backend does not implement LEFT padding semantics for center | — | — | 2026-07-23 | — | — |
| ibis-duckdb | padding | LEFT | — | unsupported | gate | build | — | The native backend does not implement LEFT padding semantics for center | — | — | 2026-07-23 | — | — |
| ibis-duckdb | padding | RIGHT | — | expr_capable | gate | build | — | RIGHT is the builder default, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | RIGHT is the builder default, so the explicit option is observably equivalent to omission and cannot discriminate |

### `CONTAINS` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `CONTAINS` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | substring | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-lazy | substring | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | substring | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-01 | 2026-07-05 | — | — |

### `CONTAINS` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `COUNT_SUBSTRING` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `COUNT_SUBSTRING` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `COUNT_SUBSTRING` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `ENDS_WITH` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `ENDS_WITH` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | substring | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-lazy | substring | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | substring | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-01 | 2026-07-05 | — | — |

### `ENDS_WITH` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `INITCAP` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `INITCAP` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-pandas | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `INITCAP` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |
| * | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| * | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |

### `LEFT` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | count | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-06 | 2026-07-05 | — | — |

### `LIKE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | match | — | — | literal_only | gate | build | — | Polars LIKE requires a literal pattern — the SQL-LIKE to regex conversion happens in Python | Use a literal SQL LIKE pattern string | — | 2026-07-05 | — | dynamic arg silently miscompiles: the SQL-LIKE→regex conversion runs on str(Expr), producing a pattern that matches nothing rather than raising — cannot be confirmed by an exception-based probe |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LIKE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | match | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LIKE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LOWER` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LOWER` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-pandas | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LOWER` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LPAD` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Polars str.pad_start() requires a single literal fill character, not a column expression | Use a literal single-character string | PL-STR-03 | 2026-07-05 | — | — |

### `LPAD` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Narwhals str.lpad() requires a single literal fill character, not a column expression | Use a literal single-character string | NW-STR-06 | 2026-07-05 | — | — |
| * | length | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-06 | 2026-07-05 | — | — |

### `LTRIM` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-07 | 2026-07-05 | — | — |

### `LTRIM` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | dynamic arg silently miscompiles via str(Expr) into a no-op char-class, returning the input unchanged rather than raising — cannot be confirmed by an exception-based probe |

### `REGEXP_COUNT` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_COUNT` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |

### `REGEXP_COUNT` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |

### `REGEXP_MATCH` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| polars | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_MATCH` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | group | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | group | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-pandas | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | group | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | group | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-polars | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_MATCH` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_MATCH_ALL` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | group | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | group | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_MATCH_ALL` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | group | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | group | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | group | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | group | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |

### `REGEXP_MATCH_ALL` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | group | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | group | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | group | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | group | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |

### `REGEXP_REPLACE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | pattern | — | — | literal_only | gate | build | — | Polars does not support dynamic column patterns in str.replace_all/str.replace with regex | Use a literal string regex pattern; replacement can be a column reference | PL-STR-02 | 2026-07-05 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_REPLACE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | pattern | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-05 | 2026-07-05 | — | — |
| * | replacement | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-05 | 2026-07-05 | — | — |
| narwhals-lazy | replacement | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-05 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-pandas | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-polars | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| narwhals-polars | replacement | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-05 | 2026-07-05 | — | — |

### `REGEXP_REPLACE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_SPLIT` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |

### `REGEXP_SPLIT` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |

### `REGEXP_SPLIT` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |

### `REGEXP_STRPOS` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| polars | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| polars | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |

### `REGEXP_STRPOS` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | occurrence | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | occurrence | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | occurrence | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | occurrence | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-polars | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |

### `REGEXP_STRPOS` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | occurrence | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | occurrence | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | occurrence | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | occurrence | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |

### `REPEAT` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | count | — | — | literal_only | gate | build | — | Polars str.repeat() requires a literal integer count, not a column expression | Use a literal integer count value | PL-STR-03 | 2026-07-05 | — | — |

### `REPLACE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | substring | — | — | literal_only | gate | build | — | Polars does not support dynamic column patterns in str.replace | Use a literal string substring; replacement can be a column reference | PL-STR-01 | 2026-07-05 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `REPLACE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | replacement | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-03 | 2026-07-05 | — | — |
| * | substring | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-03 | 2026-07-05 | — | — |
| narwhals-lazy | replacement | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-03 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | replacement | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-03 | 2026-07-05 | — | — |

### `REPLACE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `REPLACE_SLICE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | length | — | — | literal_only | gate | build | — | Polars str.replace_slice() requires a literal integer length, not a column expression | Use a literal integer length value | PL-STR-03 | 2026-07-05 | — | — |
| * | replacement | — | — | literal_only | gate | build | — | Polars str.replace_slice() requires a literal replacement string, not a column expression | Use a literal replacement string | — | 2026-07-05 | — | — |
| * | start | — | — | literal_only | gate | build | — | Polars str.replace_slice() requires a literal integer start, not a column expression | Use a literal integer start value | PL-STR-03 | 2026-07-05 | — | — |

### `REPLACE_SLICE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | length | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | — |
| * | replacement | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | — |
| * | start | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | — |

### `RIGHT` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | count | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-06 | 2026-07-05 | — | — |

### `RPAD` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Polars str.pad_end() requires a single literal fill character, not a column expression | Use a literal single-character string | PL-STR-03 | 2026-07-05 | — | — |

### `RPAD` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Narwhals str.rpad() requires a single literal fill character, not a column expression | Use a literal single-character string | NW-STR-06 | 2026-07-05 | — | — |
| * | length | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-06 | 2026-07-05 | — | — |

### `RTRIM` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-07 | 2026-07-05 | — | — |

### `RTRIM` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | dynamic arg silently miscompiles via str(Expr) into a no-op char-class, returning the input unchanged rather than raising — cannot be confirmed by an exception-based probe |

### `STARTS_WITH` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `STARTS_WITH` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | substring | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-lazy | substring | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | substring | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-01 | 2026-07-05 | — | — |

### `STARTS_WITH` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `STRPOS` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `STRPOS` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `STRPOS` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `SUBSTRING` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | negative_start | ERROR | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| polars | negative_start | LEFT_OF_BEGINNING | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| polars | negative_start | WRAP_FROM_END | — | expr_capable | gate | build | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate |

### `SUBSTRING` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | length | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-06 | 2026-07-05 | — | — |
| * | start | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-06 | 2026-07-05 | — | — |
| narwhals-pandas | negative_start | ERROR | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| narwhals-pandas | negative_start | LEFT_OF_BEGINNING | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| narwhals-pandas | negative_start | WRAP_FROM_END | — | expr_capable | gate | build | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | negative_start | ERROR | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| narwhals-polars | negative_start | LEFT_OF_BEGINNING | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| narwhals-polars | negative_start | WRAP_FROM_END | — | expr_capable | gate | build | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate |

### `SUBSTRING` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | negative_start | ERROR | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| * | negative_start | LEFT_OF_BEGINNING | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| ibis-duckdb | negative_start | ERROR | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| ibis-duckdb | negative_start | LEFT_OF_BEGINNING | — | unsupported | gate | build | — | The native backend does not implement non-default negative_start semantics for substring | — | — | 2026-07-23 | — | — |
| ibis-duckdb | negative_start | WRAP_FROM_END | — | expr_capable | gate | build | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits WRAP_FROM_END, so the explicit option is observably equivalent to omission and cannot discriminate |

### `SWAPCASE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `SWAPCASE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |
| narwhals-pandas | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |

### `SWAPCASE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |
| * | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| * | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |

### `TITLE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `TITLE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-pandas | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `TITLE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |
| * | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| * | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |

### `TRIM` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-07 | 2026-07-05 | — | — |

### `TRIM` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | characters | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | dynamic arg silently miscompiles via str(Expr) into a no-op char-class, returning the input unchanged rather than raising — cannot be confirmed by an exception-based probe |

### `UPPER` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `UPPER` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-pandas | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `UPPER` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| ibis-duckdb | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `JOIN_ASOF` × narwhals (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | tolerance | — | — | unsupported | gate | build | tolerance is not None | join_asof(tolerance=...) is not supported by the Narwhals backend | Drop tolerance= or use the Polars backend. | — | 2026-07-05 | — | — |

### `READ_RESOURCE` × polars (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | resource | — | — | unsupported | router_metadata | build | resource.dialect.escape_char is set | CSV dialect field 'escape_char' is not native-safe on this backend's reader — routed to the CsvSpec fallback reader | none needed — mountainash routes automatically | — | 2026-07-05 | — | router, not gate — fallback handles it; behaviour covered by relations resource tests |

### `READ_RESOURCE` × narwhals (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | resource | — | — | unsupported | router_metadata | build | resource.dialect.escape_char is set | CSV dialect field 'escape_char' is not native-safe on this backend's reader — routed to the CsvSpec fallback reader | none needed — mountainash routes automatically | — | 2026-07-05 | — | router, not gate — fallback handles it; behaviour covered by relations resource tests |

### `READ_RESOURCE` × ibis (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | resource | — | — | unsupported | router_metadata | build | resource.dialect.escape_char is set | CSV dialect field 'escape_char' is not native-safe on this backend's reader — routed to the CsvSpec fallback reader | none needed — mountainash routes automatically | — | 2026-07-05 | — | router, not gate — fallback handles it; behaviour covered by relations resource tests |

### `UNNEST` × narwhals (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | unnest() is not supported by the Narwhals backend | Use the Polars backend for unnest. | — | 2026-07-05 | — | — |

### `WITH_ROW_INDEX` × ibis (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | * | — | — | unsupported | gate | build | — | with_row_index lowers to a window function (row_number); the ibis Polars backend has no WindowFunction translation rule. | Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends. | IB-REL-01 | 2026-08-01 | — | relation op-level gap; covered by relation with_row_index cross-backend tests |

## Divergence register

| Id | Kind | Backends | Operations | Summary | Impact | Workaround | Upstream | Since |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IB-AGG-04 | naming | ibis-duckdb, ibis-polars, ibis-sqlite | — | Ibis names un-aliased aggregate measures "Sum(v)" rather than source column "v" | Inferred schemas and Ibis runtime output names can disagree | Always alias aggregate measures when pipelines may execute on Ibis | IB-AGG-04 | 2026-07-05 |
| IB-AGG-05 | semantics | ibis-polars | `PRODUCT` | ibis-polars product() returns None instead of the product (no wired product aggregate on the ibis-polars path) | product() returns None on ibis-polars; polars/narwhals and ibis-duckdb/ibis-sqlite compute it (ibis-duckdb overflows only on a zero factor) | Use a polars or narwhals backend for product aggregates | — | 2026-08-06 |
| IB-AGG-06 | engine_leniency | ibis-polars, ibis-sqlite | — | ibis-polars/ibis-sqlite infer an untyped NullColumn for an all-null input, which has no aggregate method (AttributeError: NullColumn has no 'sum'/'mean'/'std'/'var'/'nunique') | sum/mean/std_dev/variance/n_unique/any_value over an all-null column raise AttributeError on ibis-polars/ibis-sqlite; ibis-duckdb rejects the table outright (IB-REL-06), polars/narwhals compute None | Cast the all-null column to an explicit type first, or use a polars/narwhals backend | — | 2026-08-06 |
| IB-AGG-07 | engine_leniency | ibis-duckdb, ibis-sqlite | `PRODUCT` | product() with a zero factor breaks the log-based product implementation on ibis SQL: ibis-duckdb raises OutOfRangeException, ibis-sqlite returns a wrong value | product() over data containing 0 fails on ibis-duckdb (OutOfRangeException) and diverges on ibis-sqlite; polars/narwhals compute 0 (ibis-polars returns None — IB-AGG-05) | Use a polars or narwhals backend for product() over data that may contain zero | — | 2026-08-06 |
| IB-CAST-01 | precision | ibis-duckdb | `CAST` | DuckDB uses IEEE 754 banker's rounding (half-to-even) casting float to integer | Tests expecting truncation-on-cast produce different results on ibis-duckdb | Explicit floor()/ceil() before cast, or use ibis-sqlite/polars | IB-CAST-01 | 2026-07-05 |
| IB-CAST-03 | engine_leniency | ibis-sqlite | `CAST` | SQLite CAST is lenient, parsing CAST('1x' AS INTEGER) as 1 | Strict casts do not raise for malformed input on ibis-sqlite | Validate malformed input via conform/typespec or use another Ibis backend | IB-CAST-03 | 2026-07-05 |
| IB-CAST-04 | engine_leniency | ibis-sqlite | `CAST` | ibis-sqlite has no SQL compilation rule for TryCast (cast failure_behavior=NULL); the op raises OperationNotDefinedError | ma.col(x).cast(dtype, failure_behavior=NULL) raises on ibis-sqlite; ibis-polars/ibis-duckdb and polars null the invalid rows | Use a polars or ibis-polars/ibis-duckdb backend for null-on-cast-failure semantics | — | 2026-08-06 |
| IB-CMP-01 | engine_leniency | ibis-sqlite | `IS_FINITE`, `IS_INFINITE` | ibis-sqlite has no SQL compilation rule for is_finite/is_infinite; the ops raise OperationNotDefinedError | ma.col(x).is_finite()/is_infinite() raise on ibis-sqlite; polars, pandas, narwhals, and ibis-polars/ibis-duckdb evaluate them | Use is_null/fill checks or a non-sqlite backend for infinity detection | — | 2026-08-06 |
| IB-CTE-01 | semantics | ibis-duckdb, ibis-polars, ibis-sqlite | — | Ibis strips RECURSIVE from generated CTE SQL, turning WITH RECURSIVE into WITH | Recursive CTE SQL cannot be generated through Ibis | — | IB-CTE-01 | 2026-07-05 |
| IB-DT-06 | semantics | ibis-duckdb | `XOR`, `XOR_PARITY` | DuckDB ^ is bitwise on integers, not logical XOR on booleans | Chained boolean parity via xor diverges on ibis-duckdb | polars, narwhals, or ibis-sqlite for boolean parity | IB-DT-06 | 2026-07-05 |
| IB-DT-09 | semantics | ibis-duckdb, ibis-polars, ibis-sqlite | `TODAY`, `NOW` | Ibis today() upcasts date to timestamp on ALL ibis backends; now() compiles to query-time UTC SQL on ibis-duckdb and ibis-sqlite only (ibis-polars evaluates now() like Polars/Narwhals) | today() snapshot type differs on all ibis backends; now() evaluation instant differs on ibis-duckdb/ibis-sqlite (UTC, query-time) | Use Polars or Narwhals for exact date types; account for UTC query-time now() on ibis-duckdb/ibis-sqlite | IB-DT-09 | 2026-07-05 |
| IB-DT-10 | engine_leniency | ibis-polars | `ADD_YEARS`, `ADD_MONTHS`, `OFFSET_BY` | ibis-polars rejects calendar-based interval arithmetic (add_years/add_months/offset by months/years) with a TypeError; only duration-based intervals (days/hours/…) work | dt.add_years()/add_months() and month/year offsets raise TypeError on ibis-polars; ibis-duckdb/ibis-sqlite and polars/narwhals compute them | Use a polars/narwhals backend or ibis-duckdb/ibis-sqlite for calendar-interval arithmetic | — | 2026-08-06 |
| IB-DT-11 | engine_leniency | ibis-polars, ibis-sqlite | `DIFF_DAYS`, `DIFF_HOURS`, `DIFF_MINUTES` | ibis-polars/ibis-sqlite have no TimestampDelta translation for time-unit differences (diff_days/diff_hours/diff_minutes) — OperationNotDefinedError | dt.diff_days()/diff_hours()/diff_minutes() raise on ibis-polars and ibis-sqlite; ibis-duckdb and polars/narwhals compute them | Use ibis-duckdb or a polars/narwhals backend for time-unit differences | — | 2026-08-06 |
| IB-DT-12 | engine_leniency | ibis-sqlite | `TRUNCATE` | ibis-sqlite cannot truncate timestamps to sub-day units (hour) — UnsupportedOperationError | dt.truncate() to hour (and chains ending in a sub-day truncate) raise on ibis-sqlite; other backends compute them | Use a polars/narwhals backend or ibis-duckdb for sub-day truncation | — | 2026-08-06 |
| IB-DT-13 | semantics | ibis-sqlite | — | ibis-sqlite stores datetimes as strings, so sub-day arithmetic and comparisons produce wrong values (negative-hour offsets, month subtraction, within/between-time filters) | sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges (wrong values, not a raise); other backends compute them correctly | Use a polars/narwhals backend or ibis-duckdb for sub-day datetime arithmetic and comparisons | — | 2026-08-06 |
| IB-DT-14 | engine_leniency | ibis-sqlite | `ADD_DAYS`, `ADD_MONTHS`, `MONTH_END`, `DAYS_IN_MONTH`, `OFFSET_BY` | SQLite < 3.46 lacks time-shift modifiers, so calendar arithmetic (add_days/add_months/month_end/days_in_month/combined offsets) is unavailable on ibis-sqlite; SQLite >= 3.46 supports them (environment-conditional — the mark is applied only below 3.46) | calendar/offset arithmetic raises on ibis-sqlite when the linked SQLite is < 3.46; >= 3.46 computes them | Upgrade SQLite to >= 3.46, or use another backend for calendar arithmetic | — | 2026-08-06 |
| IB-DT-15 | semantics | ibis-sqlite | `EXTRACT_MICROSECOND` | ibis-sqlite microsecond extraction returns whole seconds instead of the microsecond component | dt.microsecond() returns the wrong value on ibis-sqlite; other backends return the microsecond component | Use a polars/narwhals backend or ibis-duckdb for microsecond extraction | — | 2026-08-06 |
| IB-DT-16 | semantics | ibis | `EXTRACT_NANOSECOND` | Ibis nanosecond extraction returns 0 — no sub-microsecond precision is retained from Python datetime inputs on any ibis backend | dt.nanosecond() returns 0 on ibis-duckdb/ibis-polars/ibis-sqlite; polars/narwhals retain nanosecond precision | Use a polars/narwhals backend for nanosecond precision | — | 2026-08-06 |
| IB-DT-17 | semantics | ibis-sqlite | `TIME` | ibis-sqlite dt.time() returns a timedelta instead of a time value | dt.time() yields the wrong type on ibis-sqlite; other backends return a time | Use a polars/narwhals backend or ibis-duckdb for dt.time() | — | 2026-08-06 |
| IB-DT-18 | engine_leniency | ibis-polars | `MONTH_END`, `DAYS_IN_MONTH` | ibis-polars cannot compile month_end()/days_in_month(): the interval construction passes months= to duration(), raising TypeError (duration() got an unexpected keyword argument 'months') | ma.col(x).dt.month_end()/days_in_month() raise TypeError on ibis-polars; ibis-duckdb/ibis-sqlite and polars compute them | Use ibis-duckdb/ibis-sqlite or a polars backend for month_end/days_in_month | — | 2026-08-06 |
| IB-LIST-01 | engine_leniency | ibis | `GATHER_EVERY`, `ARG_MIN`, `ARG_MAX`, `N_UNIQUE`, `COUNT_MATCHES`, `DROP_NULLS`, `SET_DIFFERENCE`, `STD`, `VAR`, `SHIFT`, `DIFF`, `REVERSE`, `SLICE`, `HEAD`, `TAIL`, `MEDIAN` | Ibis lacks native array operations for these list ops; the mountainash ibis expression system raises BackendCapabilityError (unenriched) | list.gather_every/arg_min/arg_max/n_unique/count_matches/drop_nulls/set_difference/std/var/shift/diff/reverse/slice/head/tail/median raise on ibis backends | Use a Polars backend for these list operations | — | 2026-08-06 |
| IB-MATH-02 | engine_leniency | ibis-sqlite | `SINH`, `COSH`, `TANH`, `ASINH`, `ACOSH`, `ATANH` | SQLite lacks hyperbolic math functions | sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite | Any backend other than ibis-sqlite | IB-MATH-02 | 2026-07-05 |
| IB-MATH-04 | semantics | ibis-sqlite | `DIVIDE` | SQLite performs integer division for two integer operands | Division expecting float results silently truncates on ibis-sqlite | Cast one operand to float before dividing | IB-MATH-04 | 2026-07-05 |
| IB-MATH-05 | semantics | ibis-sqlite, ibis-duckdb | `MODULO` | SQL modulo takes the sign of the dividend rather than the divisor | Cyclic calculations and hash bucketing with negative dividends diverge | Ensure the dividend is non-negative or normalize with a conditional expression | IB-MATH-05 | 2026-07-05 |
| IB-MATH-06 | engine_leniency | ibis-polars, ibis-duckdb | `SINH`, `COSH`, `TANH`, `ASINH`, `ACOSH`, `ATANH` | ibis-polars and ibis-duckdb lack hyperbolic math functions in the mountainash arithmetic system; these ops raise NotImplementedError (ibis-sqlite is a separate engine limitation, IB-MATH-02) | sinh/cosh/tanh/asinh/acosh/atanh raise on ibis-polars and ibis-duckdb; polars computes them | Use a polars backend for hyperbolic functions | — | 2026-08-06 |
| IB-REL-06 | engine_leniency | ibis-duckdb | — | DuckDB rejects tables containing untyped all-NULL columns | Projections whose column is entirely null raise a type resolution error | cast the null column to an explicit type first | IB-REL-06 | 2026-07-05 |
| IB-REL-07 | engine_leniency | ibis-sqlite | — | ibis-sqlite lacks array/pivot relational translations: drop_nans, unpivot/melt raise OperationNotDefinedError | Relation.drop_nans()/unpivot()/melt() raise on ibis-sqlite; other backends compute them | Use ibis-duckdb or a polars/narwhals backend for these relational ops | — | 2026-08-06 |
| IB-REL-08 | semantics | ibis-duckdb, ibis-sqlite | — | asof join is unreliable on ibis SQL backends: ibis-duckdb returns a wrong (diverging) result and ibis-sqlite raises UnsupportedOperationError | Relation.join_asof() diverges on ibis-duckdb and raises on ibis-sqlite; polars/narwhals compute it correctly | Use a polars or narwhals backend for asof joins | — | 2026-08-06 |
| IB-REL-09 | engine_leniency | ibis-duckdb, ibis-sqlite | — | cross_join with suffix disambiguation fails on ibis SQL backends (ibis-duckdb BinderException, ibis-sqlite OperationalError) — suffixes kwarg incompatibility | Relation.cross_join() raises on ibis-duckdb/ibis-sqlite; polars/narwhals and ibis-polars compute it | Use a polars/narwhals backend or ibis-polars for cross joins | — | 2026-08-06 |
| IB-STR-01 | engine_leniency | ibis-polars | `LIKE` | ibis-polars has no translation rule for SQL LIKE patterns (OperationNotDefinedError) | str LIKE-pattern matching raises on ibis-polars; ibis-duckdb/ibis-sqlite and polars/narwhals handle it | Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend for LIKE patterns | — | 2026-08-06 |
| IB-STR-02 | engine_leniency | ibis-polars | `CONTAINS`, `STARTS_WITH`, `ENDS_WITH` | ibis-polars rejects case-insensitive string matching (contains/starts_with/ends_with with case_sensitive=False) — UnsupportedArgumentError | case-insensitive contains/starts_with/ends_with raise on ibis-polars; other backends compute them | Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend for case-insensitive matching | — | 2026-08-06 |
| IB-TYPE-02 | semantics | ibis-duckdb, ibis-sqlite | `IS_NAN`, `FILL_NAN` | SQL engines treat NaN as NULL; NaN == NaN yields NULL not False | is_nan/fill_nan/NaN comparisons diverge on SQL engines | Use is_null/fill_null on SQL backends | IB-TYPE-02 | 2026-07-05 |
| IB-TYPE-04 | type_inference | ibis-duckdb, ibis-polars, ibis-sqlite | — | Ibis defers type resolution to its backend, unlike eager Polars | Type-sensitive operations and result comparisons can differ despite matching values | — | IB-TYPE-04 | 2026-07-05 |
| IB-WIN-01 | engine_leniency | ibis-polars | `DIFF`, `CUM_SUM`, `CUM_MAX`, `CUM_MIN`, `CUM_COUNT`, `IS_DUPLICATED`, `RANK`, `DENSE_RANK`, `ROW_NUMBER`, `LEAD`, `LAG`, `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE`, `NTILE`, `PERCENT_RANK`, `CUME_DIST` | ibis-polars has no translation rule for any WindowFunction (OperationNotDefinedError): rank/dense_rank/row_number/lead/lag/shift/first_value/last_value/nth_value/ntile/percent_rank/cume_dist/cumulative/diff/is_duplicated | all window ops raise on ibis-polars; ibis-duckdb/ibis-sqlite and polars/narwhals handle them (rank family with 0-based divergence on ibis SQL — see IB-WIN-02) | Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend | — | 2026-08-06 |
| IB-WIN-02 | semantics | ibis-duckdb, ibis-sqlite | `RANK`, `DENSE_RANK`, `ROW_NUMBER` | ibis-duckdb/ibis-sqlite compute rank/dense_rank/row_number as 0-based, while polars/narwhals are 1-based | rank()/dense_rank()/row_number().over() return values one lower on ibis-duckdb/ibis-sqlite; ordering-relative assertions still hold but absolute ranks differ | Add 1 to the result on ibis SQL backends, or use polars/narwhals for 1-based ranks | — | 2026-08-06 |
| IB-WIN-03 | engine_leniency | ibis | `RANK_AVERAGE`, `RANK_MAX` | Ibis raises BackendCapabilityError (unenriched) for rank(method='average'\|'max') — no SQL equivalent | rank(method='average') and rank(method='max') raise on all ibis backends; polars/narwhals compute them | Use rank(method='min'/'dense'/'ordinal') on ibis, or polars/narwhals for average/max | — | 2026-08-06 |
| IB-WIN-04 | engine_leniency | ibis | `CUM_PROD` | Ibis lacks cum_prod as a window function (AttributeError at materialize) | col().cum_prod() raises on all ibis backends; polars and eager narwhals compute it | Use a polars or eager narwhals backend for cumulative product | — | 2026-08-06 |
| MA-AGG-01 | engine_leniency | polars, polars-lazy, pandas, narwhals-polars, narwhals-pandas, narwhals-lazy, ibis-duckdb, ibis-sqlite | `CORR` | corr() Substrait signature is wired only on ibis-polars; every other backend raises (NotImplementedError / UnsupportedOperationError / OperationNotDefinedError) | ma.corr() raises on all backends except ibis-polars | Use ibis-polars for corr(), or compute correlation manually | — | 2026-08-06 |
| MA-CONF-01 | engine_leniency | pandas, narwhals-pandas, ibis-sqlite | — | conform struct dotted-source extraction is unsupported on pandas/narwhals-pandas (TypeError) and ibis-sqlite (UnsupportedBackendType) — no native struct column type | conform() with a dotted struct source path raises on pandas/narwhals-pandas/ibis-sqlite; polars and ibis-duckdb/ibis-polars extract it | Use a polars backend or ibis-duckdb/ibis-polars for struct dotted-source conform | — | 2026-08-06 |
| MA-CONF-02 | engine_leniency | pandas, narwhals, ibis-sqlite | — | conform discard-value/discard-row drift policies are unsupported on pandas/narwhals (unenriched BackendCapabilityError) and ibis-sqlite (OperationNotDefinedError) | conform() discard_value/discard_row policies raise on pandas/narwhals and ibis-sqlite; polars and ibis-duckdb/ibis-polars apply them | Use a polars backend or ibis-duckdb/ibis-polars for discard drift policies | — | 2026-08-06 |
| MA-CONF-03 | engine_leniency | ibis | — | conform multi-transform full pipeline raises IbisTypeError on all ibis backends (deferred type resolution rejects the chained transform) | a full conform multi-transform pipeline raises on ibis-duckdb/ibis-polars/ibis-sqlite; polars/narwhals run it | Use a polars or narwhals backend for full conform transform pipelines | — | 2026-08-06 |
| MA-MATH-01 | precision | polars, narwhals, ibis | — | Intermediate float precision and rounding differ across backends | Exact equality comparisons on float results can fail across backends | Use is_close(precision=...) instead of eq() for float comparisons | MA-MATH-01 | 2026-07-05 |
| MA-MATH-02 | semantics | polars, narwhals, ibis, pandas | — | cbrt() of a negative value returns NaN on every backend (the pow(x, 1/3) implementation is undefined for negatives), instead of the real cube root | ma.col(x).cbrt() on negative inputs yields NaN across all backends; a mathematically-correct negative cube root is not available | Compute sign(x) * abs(x) ** (1/3) manually for negative inputs | — | 2026-08-06 |
| MA-REL-01 | engine_leniency | ibis, narwhals-lazy | — | pivot (long-to-wide) is unsupported on ibis (TypeError) and narwhals-lazy (AttributeError) | Relation.pivot() raises on all ibis backends and narwhals-lazy; polars and eager narwhals compute it | Use a polars or eager narwhals backend for pivot | — | 2026-08-06 |
| MA-REL-02 | semantics | pandas, narwhals-pandas | — | horizontal greatest()/least() produce diverging values on pandas and narwhals-pandas (pandas element-wise max/min semantics differ from polars/ibis) | Relation greatest()/least() diverge on pandas/narwhals-pandas; polars/narwhals-polars and ibis agree | Use a polars or ibis backend for horizontal greatest/least | — | 2026-08-06 |
| MA-STR-01 | engine_leniency | pandas, ibis-polars | `CONTAINS` | str.contains with a columnar (per-row) literal pattern is unsupported on pandas (enriched BackendCapabilityError, not registry-resolvable) and ibis-polars (UnsupportedArgumentError) | col.str.contains(other_col) raises on pandas and ibis-polars; polars and ibis-duckdb/ibis-sqlite compute the per-row substring test | Use a polars or ibis SQL backend for columnar substring patterns | — | 2026-08-06 |
| MA-STR-02 | engine_leniency | pandas, narwhals, ibis-polars | `CENTER` | str.center(width, char) is unsupported on pandas/narwhals (enriched BackendCapabilityError — padding option not honorable) and ibis-polars (UnsupportedArgumentError — columnar length argument) | ma.col(x).str.center(...) raises on pandas, all narwhals backends, and ibis-polars; polars and ibis-duckdb/ibis-sqlite compute it | Use a polars or ibis SQL backend for str.center() | — | 2026-08-06 |
| MA-TERN-01 | engine_leniency | polars, pandas, narwhals-pandas | — | a ternary comparison with a fill_null operand and booleanizer=None raises on polars/polars-lazy (SchemaError: expected Boolean got i64) and pandas/narwhals-pandas (TypeError: Boolean array expected) | t_gt(col.fill_null(0)) with booleanizer=None raises on polars/polars-lazy and pandas/narwhals-pandas; narwhals-polars/narwhals-lazy and ibis compute it | Pass an explicit booleanizer, or use narwhals-polars/ibis backends | — | 2026-08-06 |
| MA-TYPE-01 | type_inference | ibis-duckdb, ibis-polars, ibis-sqlite | — | Typed all-NULL columns lose their declared dtype through to_polars()'s pandas bridge | Ibis-backed materialization reports String or Float64 instead of the declared dtype | Re-cast after materialization or inspect the pre-materialization Ibis schema | MA-TYPE-01 | 2026-07-05 |
| MA-TYPE-02 | semantics | pandas, narwhals-pandas | `CAST` | All-NULL casts to non-nullable numpy int64/bool raise or corrupt nulls | Pandas-backed integer casts raise and boolean casts can map None to False | Use polars, narwhals-polars, narwhals-lazy, or an Ibis backend | MA-TYPE-02 | 2026-07-05 |
| MA-VAL-01 | semantics | pandas, narwhals-pandas | — | pandas/narwhals-pandas have no nullable boolean dtype for comparison results, so a null rule result collapses to False instead of the 'unknown' outcome (mountainash targets plain float64/bool on pandas) | validation outcome-model tests expecting an 'unknown' verdict from a null comparison diverge on pandas/narwhals-pandas | Use a polars, narwhals-polars, or ibis backend for three-way null outcome semantics | — | 2026-08-06 |
| MA-VAL-02 | semantics | ibis-polars, ibis-sqlite | — | ibis-polars/ibis-sqlite infer an untyped NullColumn for an all-null input, so a scalar-aggregate verdict over it diverges from the polars/narwhals result | a ScalarRule verdict over an all-null column diverges on ibis-polars/ibis-sqlite; polars/narwhals compute the 'unknown' verdict (ibis-duckdb rejects the all-null table outright — IB-REL-06) | Use a polars or narwhals backend for scalar verdicts over all-null columns | — | 2026-08-06 |
| MA-WIN-01 | engine_leniency | ibis, narwhals, pandas | `DENSE_RANK`, `ROW_NUMBER` | rank(method='dense'\|'ordinal') is only supported on polars; every other backend raises TypeError | col().rank(method='dense'\|'ordinal') raises TypeError on ibis/narwhals/pandas; only polars/polars-lazy support the method= param for dense/ordinal | Use dense_rank()/row_number() directly, or a polars backend | — | 2026-08-06 |
| MA-WIN-02 | engine_leniency | ibis, narwhals, pandas | `NTILE` | ntile() is unsupported off polars (ibis SignatureValidationError; narwhals/pandas NotImplementedError) | col().ntile(n).over() raises on ibis and narwhals/pandas backends; only polars/polars-lazy compute it | Use a polars backend for ntile() | — | 2026-08-06 |
| MA-WIN-03 | engine_leniency | ibis, narwhals, pandas | — | Applying .over() to a non-window (elementwise/scalar) expression is rejected off polars (ibis IbisTypeError; narwhals/pandas InvalidOperationError) | scalar_expr.over(...) raises on ibis and narwhals/pandas; polars evaluates the windowed scalar | Use a polars backend, or wrap a genuine window function | — | 2026-08-06 |
| NW-AGG-01 | engine_leniency | narwhals-lazy | `MODE`, `ANY_VALUE` | narwhals-lazy rejects mode()/any_value(): order-dependent/length-changing aggregates are not permitted on a LazyFrame (InvalidOperationError) | mode() and any_value() raise on narwhals-lazy; eager narwhals and other backends compute them | Use an eager backend for mode()/any_value() | — | 2026-08-06 |
| NW-CAST-01 | engine_leniency | pandas, narwhals | `CAST` | pandas and narwhals have no cast failure-behavior parameter; cast(failure_behavior=NULL) (try-cast) raises BackendCapabilityError instead of nulling invalid values | ma.col(x).cast(dtype, failure_behavior=NULL) raises on pandas and all narwhals backends; polars and ibis-polars/ibis-duckdb null the invalid rows | Use a polars or ibis-polars/ibis-duckdb backend for null-on-cast-failure semantics | — | 2026-08-06 |
| NW-DT-01 | engine_leniency | pandas, narwhals | `EXTRACT_WEEK` | pandas and narwhals lack ISO week_of_year; the mountainash expression system raises BackendCapabilityError (unenriched) | dt.week_of_year() raises on pandas and all narwhals backends; polars and ibis compute it | Use a polars or ibis backend for ISO week extraction | — | 2026-08-06 |
| NW-DT-02 | engine_leniency | narwhals-pandas | `DATE` | narwhals-pandas dt.date() raises NotImplementedError | dt.date() raises on narwhals-pandas; narwhals-polars, polars and ibis compute it | Use narwhals-polars, polars, or an ibis backend for dt.date() | — | 2026-08-06 |
| NW-DT-03 | engine_leniency | narwhals | `TIME` | Narwhals does not support dt.time() — NotImplementedError on all narwhals backends | dt.time() raises on narwhals-polars/narwhals-pandas/narwhals-lazy; polars and ibis-duckdb/ibis-polars compute it | Use a polars or ibis backend for dt.time() | — | 2026-08-06 |
| NW-DT-04 | engine_leniency | pandas, narwhals-pandas | `DATE` | the default pandas backend and narwhals-pandas do not implement dt.date() extraction; the op raises NotImplementedError (narwhals-polars computes it) | ma.col(x).dt.date() raises on pandas and narwhals-pandas; polars, narwhals-polars, and ibis compute it | Use a polars/narwhals-polars or ibis backend for dt.date() | — | 2026-08-06 |
| NW-DT-05 | engine_leniency | pandas, narwhals | `TIME`, `MONTH_START`, `MONTH_END`, `DAYS_IN_MONTH` | pandas and narwhals do not implement dt.time()/month_start()/month_end()/days_in_month(); these ops raise NotImplementedError | ma.col(x).dt.time()/month_start()/month_end()/days_in_month() raise on pandas and all narwhals backends; polars and ibis compute them | Use a polars or ibis backend for these datetime enrichment ops | — | 2026-08-06 |
| NW-LIST-05 | engine_leniency | narwhals | `GATHER_EVERY`, `ARG_MIN`, `ARG_MAX`, `ALL`, `ANY`, `N_UNIQUE`, `COUNT_MATCHES`, `DROP_NULLS`, `SET_UNION`, `SET_INTERSECTION`, `SET_DIFFERENCE`, `STD`, `VAR`, `SHIFT`, `DIFF`, `CONCAT`, `JOIN`, `REVERSE`, `SLICE`, `HEAD`, `TAIL`, `EXPLODE` | Narwhals lacks native list operations; the mountainash narwhals expression system raises BackendCapabilityError (unenriched) for these list ops | list.gather_every/arg_min/arg_max/all/any/n_unique/count_matches/drop_nulls/set_union/set_intersection/set_difference/std/var/shift/diff/concat/join/reverse/slice/head/tail/explode raise on narwhals backends | Use a Polars or Ibis backend for these list operations | — | 2026-08-06 |
| NW-MATH-01 | engine_leniency | pandas, narwhals | — | pandas and narwhals lack tan(), so cot() (computed as 1/tan) raises NotImplementedError | ma.col(x).cot() raises on pandas and all narwhals backends; polars and ibis compute it | Use a polars or ibis backend for cot() | — | 2026-08-06 |
| NW-MATH-02 | engine_leniency | pandas, narwhals | `SIN`, `COS`, `TAN`, `ASIN`, `ACOS`, `ATAN`, `ATAN2`, `RADIANS`, `DEGREES`, `SINH`, `COSH`, `TANH`, `ASINH`, `ACOSH`, `ATANH` | pandas and narwhals lack native trigonometric, angular-conversion, and hyperbolic math functions; these ops raise NotImplementedError | trig (sin/cos/tan/asin/acos/atan/atan2), angular (radians/degrees), and hyperbolic (sinh/cosh/tanh/asinh/acosh/atanh) raise on pandas and all narwhals backends; polars and ibis (polars/duckdb) compute them | Use a polars or ibis-polars/ibis-duckdb backend for these math functions | — | 2026-08-06 |
| NW-REL-01 | engine_leniency | narwhals-lazy | — | narwhals-lazy with_row_index() requires an explicit order_by= (row order over a LazyFrame is undefined); calling it without one raises TypeError | Relation.with_row_index() raises on narwhals-lazy; eager narwhals/polars and ibis-duckdb/ibis-sqlite assign a 0..N-1 index | Use an eager backend, or pass an explicit order before the lazy row index | — | 2026-08-06 |
| NW-REL-02 | engine_leniency | narwhals | — | Narwhals does not support unnest of a struct column | Relation.unnest() raises on narwhals backends; polars and ibis compute it | Use a polars or ibis backend for unnest | — | 2026-08-06 |
| NW-REL-03 | engine_leniency | narwhals-lazy | — | narwhals-lazy has no sample() on a LazyFrame (AttributeError) | Relation.sample() raises on narwhals-lazy; eager backends sample rows | Use an eager backend for sample() | — | 2026-08-06 |
| NW-STR-14 | semantics | narwhals-pandas | `TITLE`, `INITCAP` | narwhals-pandas title/initcap route to pandas str.title(); its Unicode titlecasing of sharp-S/ligatures differs from polars to_titlecase (e.g. 'ße' -> 'ẞe' vs 'SSe') | title()/initcap() on narwhals-pandas may differ from polars/narwhals-polars on non-ASCII inputs (sharp-S, ligatures); ASCII is identical | Use polars or narwhals-polars where exact polars titlecasing of non-ASCII is required | — | 2026-07-29 |
| NW-STR-15 | semantics | pandas, narwhals | `LTRIM`, `RTRIM` | pandas and narwhals lack directional trimming: ltrim/rtrim and strip_chars_start/end strip BOTH sides (only strip_chars is native), so leading/trailing-only requests over-strip | ltrim/rtrim and str.strip_chars_start()/strip_chars_end() strip both sides on pandas/narwhals; polars and ibis strip only the requested side | Use a polars or ibis backend for directional trimming | — | 2026-08-06 |
| NW-STR-17 | engine_leniency | pandas, narwhals | `REPEAT` | str.repeat(n) is unsupported on pandas and narwhals (BackendCapabilityError); no repeat translation is wired for these backends | ma.col(x).str.repeat(n) raises on pandas and all narwhals backends; polars and ibis compute it | Use a polars or ibis backend for str.repeat() | — | 2026-08-06 |
| NW-STR-18 | semantics | pandas, narwhals | `REPLACE_SLICE` | str.replace_slice(start, length, replacement) is a silent no-op on pandas and narwhals: the slice arguments never reach the backend so the string is returned unchanged instead of having the slice replaced | ma.col(x).str.replace_slice(...) returns the input unchanged on pandas and all narwhals backends; polars and ibis replace the intended slice | Use a polars or ibis backend for str.replace_slice() | — | 2026-08-06 |
| NW-WIN-01 | engine_leniency | narwhals-lazy | `DIFF`, `CUM_SUM`, `CUM_MAX`, `CUM_MIN`, `CUM_COUNT`, `CUM_PROD`, `LEAD`, `LAG`, `FIRST_VALUE`, `LAST_VALUE` | narwhals-lazy rejects order-dependent window expressions (diff/cumulative/lead/lag/shift/first_value/last_value) on a LazyFrame (InvalidOperationError) | order-dependent window ops (diff/cum_*/lead/lag/shift/first_value/last_value) raise on narwhals-lazy; eager narwhals and polars compute them | Use an eager backend, or establish an explicit order before the lazy diff | — | 2026-08-06 |
| NW-WIN-02 | engine_leniency | narwhals, pandas | `PERCENT_RANK`, `CUME_DIST`, `NTH_VALUE`, `DIFF` | narwhals backends raise NotImplementedError for percent_rank()/cume_dist()/nth_value() and diff(n>1) | percent_rank/cume_dist/nth_value and multi-step diff raise on narwhals/pandas; ibis-duckdb/sqlite compute them (polars too, except nth_value — see PL-WIN-01) | Use a polars or ibis SQL backend for these window ops | — | 2026-08-06 |
| PL-LIST-01 | engine_leniency | polars, polars-lazy | `EXPLODE` | Polars expression-level list.explode() in a multi-column select raises ShapeError: the exploded column's row count diverges from un-exploded siblings | col('arr').list.explode() projected alongside a non-exploded sibling column raises polars.exceptions.ShapeError on eager and lazy Polars | Explode without a mismatched sibling column, or use an Ibis backend | — | 2026-08-06 |
| PL-WIN-01 | engine_leniency | polars, polars-lazy | `NTH_VALUE` | polars nth_value().over() raises ShapeError: the window expression length does not match the group | col().nth_value(n).over() raises on eager and lazy Polars; only ibis-duckdb/ibis-sqlite compute nth_value | Use an ibis-duckdb/ibis-sqlite backend for nth_value() | — | 2026-08-06 |

## Known gaps

None recorded.

## Retirement changelog

None recorded.

