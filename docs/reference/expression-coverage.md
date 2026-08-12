# Expression Coverage

<!-- GENERATED FILE — do not edit by hand. -->
<!-- Regenerate: hatch -e test run python -m mountainash.core.capabilities.render_markdown -->

Declarations: 39 · Facts: 1509 · Registered operations: 324 · Implementation records: 972

Scoped deviations (dialect/param/option/value-class) live in [`expression-coverage-scoped.md`](expression-coverage-scoped.md).

Parquet recipe: flatten `families[].ops[].cells` from [`expression-coverage.json`](expression-coverage.json) into rows, then `pl.DataFrame(rows).write_parquet(...)`.

Legend — cell states (by exception):

- `✓` **default-capable** — implemented and clean, no constraining fact. The
  presumption; the majority; not a gap. Routed / dialect-verified annotations
  still append (`✓ ↻ routed`, `✓ ✓ dialect-verified: …`).
- `✓ audited` — same as above, strengthened by a probe wave covering this
  op's (backend, source, domain). **Scope of the claim:** the probe wave
  declared the backend×domain surface and recorded nothing against this op.
  Declarations carry no per-op probe manifest, so this is
  domain-wave-level evidence, not proof the specific op was exercised.
- `✓ᴴ` **implemented via handler** — same as `✓` / `✓ audited`, but reached
  through the visitor's `handler` dispatch path rather than a concrete
  protocol-method override on the backend leaf class (spec §3.6). The `ᴴ`
  superscript marks the dispatch shape, not a coverage grade.
- `◐ partial (…)` / `✗ unsupported` / `poly` — **CONSTRAINED**: at least one
  GATE constraint or runtime residue fact applies (counts are distinct
  selector keys, never raw fact counts).
- `—` **NOT_IMPLEMENTED** — the protocol-method override is absent (or only a
  bare `…` stub on the `*Protocol` carrier) and the cell has no facts and
  no declaration. The only true blank.
- `⚠ contradiction` — `NOT_IMPLEMENTED` AND the cell carries facts, a routed
  or refinement entry, or an applicable declaration. Catalog and registry
  disagree; the suite-level `contradictions == 0` invariant guards this.
- `?` **UNKNOWN** — the registry has no definition for the op, or the
  definition carries neither `protocol_method` nor `handler`. The `audited`
  flag is stored on these cells but is **not rendered on `?` cells** —
  audited is stored but not rendered on `?` cells (the field is not dead
  state; the badge is suppressed because the registry's view of the op is
  too thin to anchor a claim).
- Annotations: `↻ routed` (router metadata — handled via an alternate path),
  `⚠ runtime` (materialize-residue failure), `✓ dialect-verified`
  (dialect-scoped EXPR_CAPABLE refinement).
- `fidelity` is None on all EXECUTE facts by registration validation and is
  omitted from detail rows.

## Summary

### Per-backend counts

| Backend | default_capable | audited_clean | constrained | NOT_IMPLEMENTED | UNKNOWN | ops_total |
| --- | --- | --- | --- | --- | --- | --- |
| polars | 199 | 75 | 50 | 0 | 0 | 324 |
| narwhals | 97 | 151 | 76 | 0 | 0 | 324 |
| ibis | 138 | 114 | 72 | 0 | 0 | 324 |

contradictions: 0
audited_unknown: 0

### Fact statistics

| Axis | Breakdown |
| --- | --- |
| Level | expr_capable 149, literal_only 65, polymorphic 9, unsupported 1286 |
| Enforcement | gate 1503, router_metadata 3, materialize_residue 3 |
| Backend | polars 258, narwhals 642, ibis 609 |

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
| ibis | substrait | string | 2026-08-12 | ibis 12.0.0 | ibis-sqlite, ibis-duckdb |
| ibis | substrait | string | 2026-08-12 | ibis 12.0.0, narwhals 2.24.0 | polars, ibis-duckdb, ibis-polars, ibis-sqlite, narwhals-polars, narwhals-pandas |
| ibis | substrait | string | 2026-08-12 | ibis 12.0.0, polars 1.43.2 | ibis-polars |
| ibis | substrait | string | 2026-08-12 | ibis 12.0.0, polars 1.43.2 | ibis-polars, ibis-duckdb, ibis-sqlite |
| ibis | substrait | string | 2026-08-13 | ibis 12.0.0, polars 1.43.2, narwhals 2.24.0 | ibis-duckdb, ibis-polars, ibis-sqlite, narwhals-polars, narwhals-pandas |
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
| narwhals | substrait | string | 2026-08-12 | ibis 12.0.0, narwhals 2.24.0 | polars, ibis-duckdb, ibis-polars, ibis-sqlite, narwhals-polars, narwhals-pandas |
| narwhals | substrait | string | 2026-08-13 | ibis 12.0.0, polars 1.43.2, narwhals 2.24.0 | ibis-duckdb, ibis-polars, ibis-sqlite, narwhals-polars, narwhals-pandas |
| polars | mountainash | relation | 2026-07-05 |  |  |
| polars | mountainash | set | — | — | — |
| polars | mountainash | ternary | — | — | — |
| polars | substrait | arithmetic | 2026-07-21 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| polars | substrait | string | 2026-07-05 |  | polars |
| polars | substrait | string | 2026-07-23 |  | polars, ibis-duckdb, narwhals-polars, narwhals-pandas |
| polars | substrait | string | 2026-08-12 | ibis 12.0.0, narwhals 2.24.0 | polars, ibis-duckdb, ibis-polars, ibis-sqlite, narwhals-polars, narwhals-pandas |
| polars | substrait | string | 2026-08-13 | polars 1.43.2 | polars |

## Per-family coverage

### `FKEY_MOUNTAINASH_SCALAR_ARITHMETIC` (mountainash / arithmetic)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `FLOOR_DIVIDE` | ✓ | ✓ | ✓ |

### `FKEY_MOUNTAINASH_SCALAR_DATETIME` (mountainash / datetime)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `ADD_DAYS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_HOURS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MICROSECONDS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MILLISECONDS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MINUTES` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_MONTHS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_SECONDS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `ADD_YEARS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `CEIL` | ✓ | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 2 dialects) | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 1 dialects) |
| `DATE` | ✓ | ✓ audited | ✓ audited |
| `DAYS_IN_MONTH` | ✓ | ✓ audited | ✓ audited |
| `DIFF_DAYS` | ✓ | ✓ audited | ✓ audited |
| `DIFF_HOURS` | ✓ | ✓ audited | ✓ audited |
| `DIFF_MILLISECONDS` | ✓ | ✓ audited | ✓ audited |
| `DIFF_MINUTES` | ✓ | ✓ audited | ✓ audited |
| `DIFF_MONTHS` | ✓ | ✓ audited | ✓ audited |
| `DIFF_SECONDS` | ✓ | ✓ audited | ✓ audited |
| `DIFF_YEARS` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_DAY` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_DAY_OF_YEAR` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_HOUR` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_ISO_YEAR` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_MICROSECOND` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_MILLISECOND` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_MINUTE` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_MONTH` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_NANOSECOND` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_QUARTER` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_SECOND` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_TIMEZONE_OFFSET` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_UNIX_TIME` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_WEEK` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_WEEKDAY` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_YEAR` | ✓ | ✓ audited | ✓ audited |
| `FLOOR` | ✓ | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 2 option-selectors, 1 value-classes, 1 dialects) |
| `IS_DST` | ✓ | ✓ audited | ✓ audited |
| `IS_LEAP_YEAR` | ✓ | ✓ audited | ✓ audited |
| `MONTH_END` | ✓ | ✓ audited | ✓ audited |
| `MONTH_START` | ✓ | ✓ audited | ✓ audited |
| `NOW` | ✓ | ✓ audited | ✓ audited |
| `OFFSET_BY` | ✓ | ✓ audited | ✓ audited |
| `ROUND` | ✓ | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 2 dialects) | ◐ partial (1 params, 20 option-selectors, 1 value-classes, 1 dialects) |
| `TIME` | ✓ | ✓ audited | ✓ audited |
| `TODAY` | ✓ | ✓ audited | ✓ audited |
| `TOTAL_DAYS` | ✓ | ✓ audited | ✓ audited |
| `TOTAL_HOURS` | ✓ | ✓ audited | ✓ audited |
| `TOTAL_MICROSECONDS` | ✓ | ✓ audited | ✓ audited |
| `TOTAL_MILLISECONDS` | ✓ | ✓ audited | ✓ audited |
| `TOTAL_MINUTES` | ✓ | ✓ audited | ✓ audited |
| `TOTAL_NANOSECONDS` | ✓ | ✓ audited | ✓ audited |
| `TOTAL_SECONDS` | ✓ | ✓ audited | ✓ audited |
| `TO_TIMEZONE` | ✓ | ✓ audited | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 1 dialects) |
| `TRUNCATE` | ✓ | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 2 option-selectors, 1 value-classes, 1 dialects) |

### `FKEY_MOUNTAINASH_SCALAR_LIST` (mountainash / list)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `AGG` | ✓ | ✓ audited | ✓ |
| `ALL` | ✓ | ✓ audited | ✓ |
| `ANY` | ✓ | ✓ audited | ✓ |
| `ARG_MAX` | ✓ | ✓ audited | ✓ |
| `ARG_MIN` | ✓ | ✓ audited | ✓ |
| `CONCAT` | ✓ | ✓ audited | ✓ |
| `CONTAINS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) ⚠ runtime | ✓ |
| `COUNT_MATCHES` | ✓ | ✓ audited | ✓ |
| `DIFF` | ✓ | ✓ audited | ✓ |
| `DROP_NULLS` | ✓ | ✓ audited | ✓ |
| `EXPLODE` | ✓ | ✓ audited | ✓ |
| `FILTER` | ✓ | ✓ audited | ✓ |
| `GATHER` | ✓ | ✓ audited | ✓ |
| `GATHER_EVERY` | ✓ | ✓ audited | ✓ |
| `GET` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) ⚠ runtime | ✓ |
| `HEAD` | ✓ | ✓ audited | ✓ |
| `ITEM` | ✓ | ✓ audited | ✓ |
| `JOIN` | ✓ | ✓ audited | ✓ |
| `LEN` | ✓ | ✓ audited | ✓ |
| `MAX` | ✓ | ✓ audited | ✓ |
| `MEAN` | ✓ | ✓ audited | ✓ |
| `MEDIAN` | ✓ | ✓ audited | ✓ |
| `MIN` | ✓ | ✓ audited | ✓ |
| `N_UNIQUE` | ✓ | ✓ audited | ✓ |
| `REVERSE` | ✓ | ✓ audited | ✓ |
| `SAMPLE` | ✓ | ✓ audited | ✓ |
| `SET_DIFFERENCE` | ✓ | ✓ audited | ✓ |
| `SET_INTERSECTION` | ✓ | ✓ audited | ✓ |
| `SET_SYMMETRIC_DIFFERENCE` | ✓ | ✓ audited | ✓ |
| `SET_UNION` | ✓ | ✓ audited | ✓ |
| `SHIFT` | ✓ | ✓ audited | ✓ |
| `SLICE` | ✓ | ✓ audited | ✓ |
| `SORT` | ✓ | ✓ audited | ✓ |
| `STD` | ✓ | ✓ audited | ✓ |
| `SUM` | ✓ | ✓ audited | ✓ |
| `TAIL` | ✓ | ✓ audited | ✓ |
| `TO_ARRAY` | ✓ | ✓ audited | ✓ |
| `TO_STRUCT` | ✓ | ✓ audited | ✓ |
| `T_CONTAINS` | ✓ | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) ⚠ runtime | ✓ |
| `UNIQUE` | ✓ | ✓ audited | ✓ |
| `VAR` | ✓ | ✓ audited | ✓ |

### `FKEY_MOUNTAINASH_SCALAR_SET` (mountainash / set)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `IS_IN` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `IS_NOT_IN` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |

### `FKEY_MOUNTAINASH_SCALAR_STRING` (mountainash / string)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `DECODE` | ✓ | ✓ | ✓ |
| `ENCODE` | ✓ | ✓ | ✓ |
| `EXTRACT_GROUPS` | ✓ | ✓ | ✓ |
| `JSON_DECODE` | ✓ | ✓ | ✓ |
| `JSON_PATH_MATCH` | ✓ | ✓ | ✓ |
| `REGEX_CONTAINS` | ✓ | ✓ | ✓ |
| `STRIP_SUFFIX` | ✓ | ✓ | ✓ |
| `TO_INTEGER` | ✓ | ✓ | ✓ |
| `TO_TIME` | ✓ | ✓ | ✓ |

### `FKEY_MOUNTAINASH_SCALAR_TERNARY` (mountainash / ternary)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `ALWAYS_FALSE` | ✓ audited | ✓ audited | ✓ audited |
| `ALWAYS_TRUE` | ✓ audited | ✓ audited | ✓ audited |
| `ALWAYS_UNKNOWN` | ✓ audited | ✓ audited | ✓ audited |
| `COLLECT_VALUES` | poly | poly | poly |
| `IS_FALSE` | ✓ audited | ✓ audited | ✓ audited |
| `IS_KNOWN` | ✓ audited | ✓ audited | ✓ audited |
| `IS_TRUE` | ✓ audited | ✓ audited | ✓ audited |
| `IS_UNKNOWN` | ✓ audited | ✓ audited | ✓ audited |
| `MAYBE_FALSE` | ✓ audited | ✓ audited | ✓ audited |
| `MAYBE_TRUE` | ✓ audited | ✓ audited | ✓ audited |
| `TO_TERNARY` | ✓ audited | ✓ audited | ✓ audited |
| `T_AND` | ✓ audited | ✓ audited | ✓ audited |
| `T_EQ` | ✓ audited | ✓ audited | ✓ audited |
| `T_GE` | ✓ audited | ✓ audited | ✓ audited |
| `T_GT` | ✓ audited | ✓ audited | ✓ audited |
| `T_IS_IN` | ✓ audited | ✓ audited | ✓ audited |
| `T_IS_NOT_IN` | ✓ audited | ✓ audited | ✓ audited |
| `T_LE` | ✓ audited | ✓ audited | ✓ audited |
| `T_LT` | ✓ audited | ✓ audited | ✓ audited |
| `T_NE` | ✓ audited | ✓ audited | ✓ audited |
| `T_NOT` | ✓ audited | ✓ audited | ✓ audited |
| `T_OR` | ✓ audited | ✓ audited | ✓ audited |
| `T_XOR` | ✓ audited | ✓ audited | ✓ audited |
| `T_XOR_PARITY` | ✓ audited | ✓ audited | ✓ audited |

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
| `BITWISE_AND` | ✓ audited | ✓ audited | ✓ audited |
| `BITWISE_NOT` | ✓ audited | ✓ audited | ✓ audited |
| `BITWISE_OR` | ✓ audited | ✓ audited | ✓ audited |
| `BITWISE_XOR` | ✓ audited | ✓ audited | ✓ audited |
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
| `SHIFT_LEFT` | ✓ audited | ✓ audited | ✓ audited |
| `SHIFT_RIGHT` | ✓ audited | ✓ audited | ✓ audited |
| `SHIFT_RIGHT_UNSIGNED` | ✓ audited | ✓ audited | ✓ audited |
| `SIGN` | ✓ audited | ✓ audited | ✓ audited |
| `SIN` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `SINH` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `SQRT` | ◐ partial (2 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `SUBTRACT` | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 7 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (2 params, 8 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `TAN` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |
| `TANH` | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 5 option-selectors, 0 value-classes, 1 dialects) |

### `FKEY_SUBSTRAIT_SCALAR_DATETIME` (substrait / datetime)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `ADD_INTERVALS` | ✓ | ✓ audited | ✓ audited |
| `ASSUME_TIMEZONE` | ✓ | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 2 dialects) | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 1 dialects) |
| `EXTRACT` | ✓ | ✓ audited | ✓ audited |
| `EXTRACT_BOOLEAN` | ✓ | ✓ audited | ✓ audited |
| `LOCAL_TIMESTAMP` | ✓ | ✓ audited | ◐ partial (1 params, 0 option-selectors, 1 value-classes, 1 dialects) |
| `STRFTIME` | ✓ | ✓ audited | ✓ audited |
| `STRPTIME_DATE` | ✓ | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) · unsupported on narwhals-pandas | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) · unsupported on ibis-sqlite |
| `STRPTIME_TIMESTAMP` | ✓ | ✓ audited | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) · unsupported on ibis-sqlite |

### `FKEY_SUBSTRAIT_SCALAR_SET` (substrait / set)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `INDEX_IN` | ✓ | ✓ | ✓ |

### `FKEY_SUBSTRAIT_SCALAR_STRING` (substrait / string)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `BIT_LENGTH` | ✓ audited | ✓ audited | ✓ audited |
| `CAPITALIZE` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `CENTER` | ◐ partial (3 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (3 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `CHAR_LENGTH` | ✓ audited | ✓ audited | ✓ audited |
| `CONCAT` | ✓ audited | ✓ audited | ✓ audited |
| `CONCAT_WS` | ✓ audited | ✓ audited | ✓ audited |
| `CONTAINS` | ✓ audited ✓ dialect-verified: polars | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: ibis-duckdb |
| `COUNT_SUBSTRING` | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (2 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: ibis-duckdb |
| `ENDS_WITH` | ✓ audited ✓ dialect-verified: polars | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: ibis-duckdb |
| `INITCAP` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) |
| `LEFT` | ✓ audited | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✓ audited |
| `LIKE` | ◐ partial (2 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (2 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) · unsupported on ibis-polars ✓ dialect-verified: ibis-duckdb |
| `LOWER` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `LPAD` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (2 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✓ audited |
| `LTRIM` | ✓ audited | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `OCTET_LENGTH` | ✓ audited | ✓ audited | ✓ audited |
| `REGEXP_COUNT` | ◐ partial (4 params, 5 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (4 params, 8 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (4 params, 8 option-selectors, 0 value-classes, 1 dialects) |
| `REGEXP_MATCH` | ◐ partial (5 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (6 params, 7 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (6 params, 6 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: ibis-duckdb |
| `REGEXP_MATCH_ALL` | ◐ partial (5 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (5 params, 9 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (5 params, 9 option-selectors, 0 value-classes, 1 dialects) |
| `REGEXP_REPLACE` | ◐ partial (5 params, 5 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (7 params, 6 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ◐ partial (6 params, 6 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: ibis-duckdb |
| `REGEXP_SPLIT` | ◐ partial (4 params, 4 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ✗ unsupported + ◐ partial (3 params, 7 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (4 params, 4 option-selectors, 0 value-classes, 3 dialects) · unsupported on ibis-sqlite ✓ dialect-verified: ibis-duckdb |
| `REGEXP_STRPOS` | ◐ partial (5 params, 6 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (5 params, 9 option-selectors, 0 value-classes, 2 dialects) | ◐ partial (5 params, 9 option-selectors, 0 value-classes, 1 dialects) |
| `REPEAT` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✓ audited | ✓ audited |
| `REPLACE` | ◐ partial (2 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (3 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ◐ partial (2 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: ibis-duckdb |
| `REPLACE_SLICE` | ◐ partial (3 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✓ audited | ◐ partial (3 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `REVERSE` | ✓ audited | ✓ audited | ✓ audited |
| `RIGHT` | ✓ audited | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✓ audited |
| `RPAD` | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (2 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✓ audited |
| `RTRIM` | ✓ audited | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `SPLIT` | ✓ audited | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) · unsupported on narwhals-pandas | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 1 dialects) |
| `STARTS_WITH` | ✓ audited ✓ dialect-verified: polars | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) ✓ dialect-verified: narwhals-lazy, narwhals-pandas, narwhals-polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: ibis-duckdb |
| `STRPOS` | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `SUBSTRING` | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (3 params, 2 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |
| `SWAPCASE` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 2 dialects) | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) |
| `TITLE` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ✗ unsupported + ◐ partial (1 params, 2 option-selectors, 0 value-classes, 1 dialects) |
| `TRIM` | ✓ audited | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) |
| `UPPER` | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 2 dialects) ✓ dialect-verified: narwhals-pandas, narwhals-polars | ◐ partial (1 params, 1 option-selectors, 0 value-classes, 1 dialects) ✓ dialect-verified: ibis-duckdb |

### `RKEY_MOUNTAINASH_REL` (mountainash / relation)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `CONFORM` | ✓ᴴ audited | ✓ᴴ audited | ✓ᴴ audited |
| `DROP_NANS` | ✓ audited | ✓ audited | ✓ audited |
| `DROP_NULLS` | ✓ audited | ✓ audited | ✓ audited |
| `EMPTY_FRAME` | ✓ audited | ✓ audited | ✓ audited |
| `EXPLODE` | ✓ audited | ✓ audited | ✓ audited |
| `FETCH_FROM_END` | ✓ audited | ✓ audited | ✓ audited |
| `JOIN_ASOF` | ✓ audited | ◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects) | ✓ audited |
| `PIVOT` | ✓ audited | ✓ audited | ✓ audited |
| `READ_RESOURCE` | ✓ audited ↻ routed | ✓ audited ↻ routed | ✓ audited ↻ routed |
| `REF` | ✓ᴴ audited | ✓ᴴ audited | ✓ᴴ audited |
| `SAMPLE` | ✓ audited | ✓ audited | ✓ audited |
| `SOURCE` | ✓ᴴ audited | ✓ᴴ audited | ✓ᴴ audited |
| `TOP_K` | ✓ audited | ✓ audited | ✓ audited |
| `UNNEST` | ✓ audited | ✗ unsupported | ✓ audited |
| `UNPIVOT` | ✓ audited | ✓ audited | ✓ audited |
| `WITH_ROW_INDEX` | ✓ audited | ✓ audited | ◐ partial (0 params, 0 option-selectors, 0 value-classes, 1 dialects) · unsupported on ibis-polars |

### `RKEY_SUBSTRAIT_REL` (mountainash / relation)

| Operation | polars | narwhals | ibis |
| --- | --- | --- | --- |
| `AGGREGATE` | ✓ audited | ✓ audited | ✓ audited |
| `DISTINCT` | ✓ audited | ✓ audited | ✓ audited |
| `FETCH` | ✓ audited | ✓ audited | ✓ audited |
| `FILTER` | ✓ audited | ✓ audited | ✓ audited |
| `JOIN` | ✓ audited | ✓ audited | ✓ audited |
| `PROJECT_DROP` | ✓ audited | ✓ audited | ✓ audited |
| `PROJECT_RENAME` | ✓ audited | ✓ audited | ✓ audited |
| `PROJECT_SELECT` | ✓ audited | ✓ audited | ✓ audited |
| `PROJECT_WITH_COLUMNS` | ✓ audited | ✓ audited | ✓ audited |
| `READ` | ✓ audited | ✓ audited | ✓ audited |
| `SORT` | ✓ audited | ✓ audited | ✓ audited |
| `UNION_ALL` | ✓ audited | ✓ audited | ✓ audited |
| `UNION_DISTINCT` | ✓ audited | ✓ audited | ✓ audited |

## Unmapped families

No declaration domain exists for these enum classes yet; no audit applies (every cell carries only the implementation axis). Extending coverage here starts at `classify_domain`/`_DOMAIN_SUFFIXES` (spec §3.2).

- `FKEY_MOUNTAINASH_NAME` (5 ops — all implemented on 3/3 backends): `ALIAS`, `NAME_TO_LOWER`, `NAME_TO_UPPER`, `PREFIX`, `SUFFIX`
- `FKEY_MOUNTAINASH_NULL` (3 ops — all implemented on 3/3 backends): `FILL_NAN`, `FILL_NULL`, `NULL_IF`
- `FKEY_MOUNTAINASH_SCALAR_AGGREGATE` (1 ops — all implemented on 3/3 backends): `COUNT_DISTINCT`
- `FKEY_MOUNTAINASH_SCALAR_BOOLEAN` (1 ops — all implemented on 3/3 backends): `XOR_PARITY`
- `FKEY_MOUNTAINASH_SCALAR_COMPARISON` (1 ops — all implemented on 3/3 backends): `IS_DUPLICATED`
- `FKEY_MOUNTAINASH_SCALAR_STRUCT` (1 ops — all implemented on 3/3 backends): `FIELD`
- `FKEY_MOUNTAINASH_WINDOW` (10 ops — all implemented on 3/3 backends): `BACKWARD_FILL`, `CUM_COUNT`, `CUM_MAX`, `CUM_MIN`, `CUM_PROD`, `CUM_SUM`, `DIFF`, `FORWARD_FILL`, `RANK_AVERAGE`, `RANK_MAX`
- `FKEY_SUBSTRAIT_CAST` (1 ops — all implemented on 3/3 backends): `CAST`
- `FKEY_SUBSTRAIT_CONDITIONAL` (1 ops — all implemented on 3/3 backends): `IF_THEN_ELSE`
- `FKEY_SUBSTRAIT_SCALAR_AGGREGATE` (16 ops — all implemented on 3/3 backends): `ANY_VALUE`, `AVG`, `BOOL_AND`, `BOOL_OR`, `CORR`, `COUNT`, `COUNT_RECORDS`, `MAX`, `MEDIAN`, `MIN`, `MODE`, `PRODUCT`, `QUANTILE`, `STD_DEV`, `SUM`, `VARIANCE`
- `FKEY_SUBSTRAIT_SCALAR_BOOLEAN` (5 ops — all implemented on 3/3 backends): `AND`, `AND_NOT`, `NOT`, `OR`, `XOR`
- `FKEY_SUBSTRAIT_SCALAR_COMPARISON` (22 ops — all implemented on 3/3 backends): `BETWEEN`, `COALESCE`, `EQUAL`, `GREATEST`, `GREATEST_SKIP_NULL`, `GT`, `GTE`, `IS_FALSE`, `IS_FINITE`, `IS_INFINITE`, `IS_NAN`, `IS_NOT_FALSE`, `IS_NOT_NULL`, `IS_NOT_TRUE`, `IS_NULL`, `IS_TRUE`, `LEAST`, `LEAST_SKIP_NULL`, `LT`, `LTE`, `NOT_EQUAL`, `NULL_IF`
- `FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC` (5 ops — all implemented on 3/3 backends): `LOG`, `LOG10`, `LOG1P`, `LOG2`, `LOGB`
- `FKEY_SUBSTRAIT_SCALAR_ROUNDING` (3 ops — all implemented on 3/3 backends): `CEIL`, `FLOOR`, `ROUND`
- `SUBSTRAIT_ARITHMETIC_WINDOW` (11 ops — all implemented on 3/3 backends): `CUME_DIST`, `DENSE_RANK`, `FIRST_VALUE`, `LAG`, `LAST_VALUE`, `LEAD`, `NTH_VALUE`, `NTILE`, `PERCENT_RANK`, `RANK`, `ROW_NUMBER`

## Per-op detail

Cells whose facts are all scoped (dialect / parameter / option / value-class) have no section here — see [`expression-coverage-scoped.md`](expression-coverage-scoped.md) for the scoped detail. `refinements` (EXPR_CAPABLE + dialect) are scoped by construction; `dialect-scoped whole-op` facts appear under that doc's `Dialect-scoped whole-op` subheading.

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

### `CAPITALIZE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |

### `CENTER` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |

### `INITCAP` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |

### `REGEXP_SPLIT` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | Narwhals has no regex-split primitive at the pinned version -- ExprStringNamespace.split(by) is literal-substring-only, no other method performs regex splitting on any narwhals dialect | Use a Polars or ibis-duckdb/ibis-polars(literal) backend for regex split | NW-STR-20 | 2026-08-13 | — | whole-op gate on a family-wide WILDCARD_PARAM fact; no OpSpec exists since narwhals genuinely has no candidate method to probe -- verified by a dedicated native-API-surface self-healing probe (not a re-invocation of the mountainash wrapper's own hard-coded raise) |

### `SWAPCASE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |

### `SWAPCASE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |

### `TITLE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | This string operation has no correct native implementation on this backend at the pinned floor; it is gated to fail loudly rather than return wrong data | — | — | 2026-07-23 | — | whole-op gate; verified by the dedicated op-level probe suite (test_op_level_gate_probes.py), which cannot be keyed on an OpSpec param |

### `UNNEST` × narwhals (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | * | — | — | unsupported | gate | build | — | unnest() is not supported by the Narwhals backend | Use the Polars backend for unnest. | — | 2026-07-05 | — | — |

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
| MA-STR-03 | engine_leniency | polars | `REGEXP_SPLIT` | regexp_string_split on an empty or zero-width-capable regex pattern diverges from the ibis-duckdb oracle — Polars has no native regex-split primitive, so mountainash falls back to a Python re.finditer-based split, which consolidates zero-width matches differently than DuckDB's regex engine | regexp_string_split('') or a zero-width-capable pattern like 'a*' returns extra leading/trailing empty-string elements on polars that ibis-duckdb's native re_split does not produce; ordinary (non-degenerate) patterns are unaffected | Use an ibis-duckdb backend for regexp_string_split with an empty or zero-width-capable pattern | MA-STR-03 | 2026-08-13 |
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
| NW-STR-19 | semantics | pandas, narwhals-pandas | `CONTAINS`, `STARTS_WITH`, `ENDS_WITH` | contains()/starts_with()/ends_with() on a null INPUT row (not a null search operand) returns False on pandas/narwhals-pandas instead of propagating null: plain-numpy-backed pandas boolean columns have no null representation, and forcing one via nw.when/then/otherwise produces an object-dtype column of Python bool objects, which breaks `~` elsewhere (bitwise-NOT on bool is not logical negation) | a null row in the searched column silently yields False rather than null on pandas/narwhals-pandas for contains/starts_with/ends_with; every other backend (polars, ibis, narwhals-polars, narwhals-lazy) propagates null correctly | Use a polars, narwhals-polars, narwhals-lazy, or ibis backend where a null row must propagate through contains/starts_with/ends_with | — | 2026-08-12 |
| NW-WIN-01 | engine_leniency | narwhals-lazy | `DIFF`, `CUM_SUM`, `CUM_MAX`, `CUM_MIN`, `CUM_COUNT`, `CUM_PROD`, `LEAD`, `LAG`, `FIRST_VALUE`, `LAST_VALUE` | narwhals-lazy rejects order-dependent window expressions (diff/cumulative/lead/lag/shift/first_value/last_value) on a LazyFrame (InvalidOperationError) | order-dependent window ops (diff/cum_*/lead/lag/shift/first_value/last_value) raise on narwhals-lazy; eager narwhals and polars compute them | Use an eager backend, or establish an explicit order before the lazy diff | — | 2026-08-06 |
| NW-WIN-02 | engine_leniency | narwhals, pandas | `PERCENT_RANK`, `CUME_DIST`, `NTH_VALUE`, `DIFF` | narwhals backends raise NotImplementedError for percent_rank()/cume_dist()/nth_value() and diff(n>1) | percent_rank/cume_dist/nth_value and multi-step diff raise on narwhals/pandas; ibis-duckdb/sqlite compute them (polars too, except nth_value — see PL-WIN-01) | Use a polars or ibis SQL backend for these window ops | — | 2026-08-06 |
| PL-LIST-01 | engine_leniency | polars, polars-lazy | `EXPLODE` | Polars expression-level list.explode() in a multi-column select raises ShapeError: the exploded column's row count diverges from un-exploded siblings | col('arr').list.explode() projected alongside a non-exploded sibling column raises polars.exceptions.ShapeError on eager and lazy Polars | Explode without a mismatched sibling column, or use an Ibis backend | — | 2026-08-06 |
| PL-WIN-01 | engine_leniency | polars, polars-lazy | `NTH_VALUE` | polars nth_value().over() raises ShapeError: the window expression length does not match the group | col().nth_value(n).over() raises on eager and lazy Polars; only ibis-duckdb/ibis-sqlite compute nth_value | Use an ibis-duckdb/ibis-sqlite backend for nth_value() | — | 2026-08-06 |

## Known gaps

None recorded.

## Retirement changelog

None recorded.

