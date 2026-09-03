# Expression Coverage — Scoped Deviations

<!-- GENERATED FILE — do not edit by hand. -->
<!-- Regenerate: hatch -e test run python -m mountainash.core.capabilities.render_markdown -->

Scoped deviations — dialect, parameter, option, value-class; function-level coverage and matrices live in [`expression-coverage.md`](expression-coverage.md).

Declarations: 69 · Facts: 1558 · Registered operations: 338 · Implementation records: 1014

Legend — scoped deviations:

- The main doc (`expression-coverage.md`) carries matrices, function-level
  coverage, and the by-exception render map. This doc carries the per-op
  detail for every fact with a dialect, parameter, option, or value-class
  selector. The two are byte-disjoint on detail bodies — every input fact
  appears in exactly one artifact's detail body (§4.5 M-3).
- **Dialect-scoped whole-op facts** (wildcard param + a dialect, no
  option_value or value_class) render FIRST under a `Dialect-scoped
  whole-op` subheading within each (op, backend) section. The main doc's
  matrix cell surfaces the level + dialect via the I-2b suffix
  (e.g. `◐ partial (…) · unsupported on ibis-duckdb`).
- All other scoped facts render with the §4.3 option-collapse rule:
  groups of ≥3 facts sharing every semantic field except `option_value`
  collapse to a single row with the sorted `option_value` list; smaller
  groups render per-fact.
- Annotations seen in the main doc's matrix (`↻ routed`, `⚠ runtime`,
  `✓ dialect-verified: …`) describe the same cells; this doc carries
  the underlying fact rows, not the annotations.
- `fidelity` is None on all EXECUTE facts by registration validation and
  is omitted from detail rows.

## Per-op detail (scoped)

### `PARSE_TOKENS` × ibis (FKEY_MOUNTAINASH_SCALAR_BOOLEAN)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | failure_behavior | — | — | unsupported | gate | build | — | ibis-sqlite cannot enforce throw-on-invalid boolean tokens | — | — | 2026-08-25 | — | — |

### `CAST` × narwhals (FKEY_MOUNTAINASH_SCALAR_CATEGORICAL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-lazy | value_type | — | — | unsupported | gate | build | — | This backend cannot execute CATEGORICAL.CAST for the requested value type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | value_type | — | — | unsupported | gate | build | — | This backend cannot execute CATEGORICAL.CAST for the requested value type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | value_type | — | — | unsupported | gate | build | — | This backend cannot execute CATEGORICAL.CAST for the requested value type and failure behavior | — | — | 2026-08-24 | — | — |

### `CAST` × ibis (FKEY_MOUNTAINASH_SCALAR_CATEGORICAL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | value_type | — | — | unsupported | gate | build | — | This backend cannot execute CATEGORICAL.CAST for the requested value type and failure behavior | — | — | 2026-08-24 | — | — |

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
| narwhals-pandas | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-pandas | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |

### `CEIL` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | unit | 1mo, 1q, 1y, month, quarter, year | — | unsupported | gate | build | — | ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |
| ibis-sqlite | unit | — | duration_multiplier | unsupported | gate | build | — | ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0 | — | — | 2026-08-18 | — | — |
| ibis-sqlite | unit | 1h, 1m, 1ms, 1q, 1s, 1us, hour, microsecond, millisecond, minute, quarter, second | — | unsupported | gate | build | — | ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |

### `FLOOR` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-pandas | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |

### `FLOOR` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | unit | — | duration_multiplier | unsupported | gate | build | — | ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0 | — | — | 2026-08-18 | — | — |
| ibis-sqlite | unit | 1h, 1m, 1ms, 1q, 1s, 1us, hour, microsecond, millisecond, minute, quarter, second | — | unsupported | gate | build | — | ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |

### `IS_DST` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | is_dst is not supported on ibis -- ibis has no DST/timezone-offset primitive to build on (verified 2026-08-16, ibis 12.0.0/duckdb) | — | — | 2026-08-16 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | is_dst is not supported on ibis -- ibis has no DST/timezone-offset primitive to build on (verified 2026-08-16, ibis 12.0.0/duckdb) | — | — | 2026-08-16 | — | — |

### `PARSE_XSD_DURATION` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |
| narwhals-polars | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |

### `PARSE_XSD_DURATION` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |
| ibis-polars | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | ibis-sqlite has no XSD lexical parser; gate before backend dispatch | — | — | 2026-08-21 | — | XSD lexical parser behavior is covered by conform temporal contract tests |

### `PARSE_XSD_PARTIAL_DATE` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |
| narwhals-polars | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |

### `PARSE_XSD_PARTIAL_DATE` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |
| ibis-polars | * | — | — | unsupported | materialize_residue | materialize | — | invalid XSD lexical values are converted to null by the residue policy | — | — | 2026-08-21 | — | — |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | ibis-sqlite has no XSD lexical parser; gate before backend dispatch | — | — | 2026-08-21 | — | XSD lexical parser behavior is covered by conform temporal contract tests |

### `ROUND` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-pandas | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |

### `ROUND` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | unit | 1mo, 1q, 1y, month, quarter, year | — | unsupported | gate | build | — | ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |
| ibis-sqlite | unit | — | duration_multiplier | unsupported | gate | build | — | ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0 | — | — | 2026-08-18 | — | — |
| ibis-sqlite | unit | 1h, 1m, 1ms, 1q, 1s, 1us, hour, microsecond, millisecond, minute, quarter, second | — | unsupported | gate | build | — | ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |

### `TO_TIMEZONE` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | to_timezone is correct only at the materialization boundary -- the target zone lives in the ibis output dtype, not in the engine (SQL is a bare CAST AS TIMESTAMPTZ), so any expression composed on the result raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb) | — | — | 2026-07-29 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | to_timezone is correct only at the materialization boundary -- the target zone lives in the ibis output dtype, not in the engine (SQL is a bare CAST AS TIMESTAMPTZ), so any expression composed on the result raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb) | — | — | 2026-07-29 | — | — |

### `TRUNCATE` × narwhals (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-pandas | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | 1w | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |
| narwhals-polars | unit | week | — | unsupported | gate | build | — | narwhals dt.truncate rejects the week unit '1w' (and its friendly alias 'week') on both dialects | — | — | 2026-08-16 | — | — |

### `TRUNCATE` × ibis (FKEY_MOUNTAINASH_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | unit | — | duration_multiplier | unsupported | gate | build | — | ibis-sqlite has no TimestampBucket compilation rule -- a multiplied MA duration (e.g. dt.truncate('2d')) is unsupported there; verified 2026-08-18, ibis 12.0.0 | — | — | 2026-08-18 | — | — |
| ibis-sqlite | unit | 1h, 1m, 1ms, 1q, 1s, 1us, hour, microsecond, millisecond, minute, quarter, second | — | unsupported | gate | build | — | ibis-sqlite has no TimestampTruncate support for units finer than DAY, and no TimestampBucket compilation rule (blocks multiple>1 bucketing, which quarter needs); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |

### `PARSE_GEOPOINT` × narwhals (FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |
| * | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |
| * | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |

### `PARSE_GEOPOINT` × ibis (FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |
| * | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |
| * | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |
| ibis-sqlite | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |
| ibis-sqlite | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |
| ibis-sqlite | format | — | — | unsupported | gate | build | — | This backend cannot execute the requested geospatial operation cell | — | — | 2026-08-21 | — | — |

### `CAST_ITEMS` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-lazy | failure_behavior | null | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | failure_behavior | throw | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | null | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | throw | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | failure_behavior | null | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |

### `CAST_ITEMS` × ibis (FKEY_MOUNTAINASH_SCALAR_LIST)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | failure_behavior | null | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |
| ibis-polars | failure_behavior | null | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |
| ibis-sqlite | failure_behavior | null | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |
| ibis-sqlite | failure_behavior | throw | — | unsupported | gate | build | — | This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior | — | — | 2026-08-24 | — | — |

### `CONTAINS` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | Narwhals list operations on pandas require PyArrow-backed list columns. | Convert column to PyArrow list or use the Polars backend. | NW-LIST-01 | 2026-07-05 | TypeError | whole-op materialize-time storage residue (narwhals-pandas PyArrow-list requirement); enriched after the visitor, not an arg-type gate |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | item | — | — | literal_only | gate | build | — | Narwhals list.contains() requires a literal item argument, not a column expression | Use a literal value for item or use the Polars/Ibis backend. | NW-LIST-01 | 2026-07-05 | — | — |

### `GET` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-polars | index | — | — | unsupported | materialize_residue | materialize | index < 0 | narwhals list.get() (and list.last(), which calls get(-1)) rejects negative indices on the polars backend. | Use a non-negative index, or the polars/ibis backends. | NW-LIST-04 | 2026-08-01 | ValueError | value-conditioned (negative index) — not a structural param gate |

### `PARSE` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | Narwhals pandas list parsing may raise a TypeError during materialization | — | — | 2026-08-24 | TypeError | — |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-lazy | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | item_type | datetime | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | item_type | time | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | item_type | datetime | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | item_type | time | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | item_type | datetime | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | item_type | time | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |

### `PARSE` × ibis (FKEY_MOUNTAINASH_SCALAR_LIST)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | LIST parsing is covered by conform list contract tests |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| ibis-duckdb | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| ibis-duckdb | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| ibis-duckdb | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| ibis-duckdb | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| ibis-duckdb | item_type | datetime | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |
| ibis-polars | item_type | boolean, date, datetime, integer, number, time | — | unsupported | gate | build | — | This backend cannot execute LIST.PARSE for the requested item type and failure behavior | — | — | 2026-08-24 | — | — |

### `T_CONTAINS` × narwhals (FKEY_MOUNTAINASH_SCALAR_LIST)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | Narwhals list operations on pandas require PyArrow-backed list columns. | Convert column to PyArrow list or use the Polars backend. | NW-LIST-01 | 2026-07-05 | TypeError | whole-op materialize-time storage residue (narwhals-pandas PyArrow-list requirement); enriched after the visitor, not an arg-type gate |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | item | — | — | literal_only | gate | build | — | Narwhals list.t_contains() requires a literal item argument, not a column expression | Use a literal value for item or use the Polars/Ibis backend. | NW-LIST-01 | 2026-07-05 | — | — |

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

### `TO_TIME` × narwhals (FKEY_MOUNTAINASH_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | failure_behavior | null | — | unsupported | gate | build | — | null-on-invalid custom time parsing is supported only by Polars | — | — | 2026-08-21 | — | — |

### `TO_TIME` × ibis (FKEY_MOUNTAINASH_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | failure_behavior | null | — | unsupported | gate | build | — | null-on-invalid custom time parsing is supported only by Polars | — | — | 2026-08-21 | — | — |

### `CAST` × narwhals (FKEY_MOUNTAINASH_SCALAR_STRUCT)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-lazy | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-lazy | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-pandas | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| narwhals-polars | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |

### `CAST` × ibis (FKEY_MOUNTAINASH_SCALAR_STRUCT)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-duckdb | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| ibis-polars | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| ibis-sqlite | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |
| ibis-sqlite | failure_behavior | — | — | unsupported | gate | build | — | This backend cannot execute STRUCT.CAST for the requested failure behavior | — | — | 2026-08-24 | — | — |

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

### `EXTRACT` × polars (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | component | MONDAY_WEEK, PICOSECOND, SUNDAY_WEEK, TIMEZONE_OFFSET, US_WEEK, US_YEAR | — | unsupported | gate | build | — | the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py) | — | — | 2026-08-15 | — | — |

### `EXTRACT` × narwhals (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | component | ISO_WEEK, ISO_YEAR, MONDAY_WEEK, PICOSECOND, SUNDAY_WEEK, TIMEZONE_OFFSET, UNIX_TIME, US_WEEK, US_YEAR | — | unsupported | gate | build | — | the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py) | — | — | 2026-08-15 | — | — |
| narwhals-polars | component | ISO_WEEK, ISO_YEAR, MONDAY_WEEK, PICOSECOND, SUNDAY_WEEK, TIMEZONE_OFFSET, UNIX_TIME, US_WEEK, US_YEAR | — | unsupported | gate | build | — | the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py) | — | — | 2026-08-15 | — | — |

### `EXTRACT` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | component | MONDAY_WEEK, NANOSECOND, PICOSECOND, SUNDAY_WEEK, TIMEZONE_OFFSET, US_WEEK, US_YEAR | — | unsupported | gate | build | — | the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py) | — | — | 2026-08-15 | — | — |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | ibis has no timezone primitives; extract/extract_boolean's timezone option is silently ignored (the local component is read from the stored value, not the target zone) -- see capabilities/datetime/extract.py | — | — | 2026-08-15 | — | — |
| ibis-duckdb | component | MONDAY_WEEK, NANOSECOND, PICOSECOND, SUNDAY_WEEK, TIMEZONE_OFFSET, US_WEEK, US_YEAR | — | unsupported | gate | build | — | the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py) | — | — | 2026-08-15 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | ibis has no timezone primitives; extract/extract_boolean's timezone option is silently ignored (the local component is read from the stored value, not the target zone) -- see capabilities/datetime/extract.py | — | — | 2026-08-15 | — | — |

### `EXTRACT_BOOLEAN` × polars (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | component | IS_DST | — | unsupported | gate | build | — | extract_boolean(IS_DST) is a placeholder (constant False) on all backends; deferred to backlog item 65 (is-dst-placeholder-implementation) | — | — | 2026-08-15 | — | — |

### `EXTRACT_BOOLEAN` × narwhals (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | component | IS_DST | — | unsupported | gate | build | — | extract_boolean(IS_DST) is a placeholder (constant False) on all backends; deferred to backlog item 65 (is-dst-placeholder-implementation) | — | — | 2026-08-15 | — | — |
| narwhals-polars | component | IS_DST | — | unsupported | gate | build | — | extract_boolean(IS_DST) is a placeholder (constant False) on all backends; deferred to backlog item 65 (is-dst-placeholder-implementation) | — | — | 2026-08-15 | — | — |

### `EXTRACT_BOOLEAN` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | component | IS_DST | — | unsupported | gate | build | — | extract_boolean(IS_DST) is a placeholder (constant False) on all backends; deferred to backlog item 65 (is-dst-placeholder-implementation) | — | — | 2026-08-15 | — | — |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | ibis has no timezone primitives; extract/extract_boolean's timezone option is silently ignored (the local component is read from the stored value, not the target zone) -- see capabilities/datetime/extract.py | — | — | 2026-08-15 | — | — |
| ibis-duckdb | component | IS_DST | — | unsupported | gate | build | — | extract_boolean(IS_DST) is a placeholder (constant False) on all backends; deferred to backlog item 65 (is-dst-placeholder-implementation) | — | — | 2026-08-15 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | ibis has no timezone primitives; extract/extract_boolean's timezone option is silently ignored (the local component is read from the stored value, not the target zone) -- see capabilities/datetime/extract.py | — | — | 2026-08-15 | — | — |

### `LOCAL_TIMESTAMP` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | local_timestamp returns the UTC wall clock, not the target-zone wall clock -- ibis has no timezone method and the naive re-cast discards the conversion (verified 2026-07-29, ibis 12.0.0/duckdb: 12:00 instead of 17:30 for Asia/Kolkata) | — | — | 2026-07-29 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | local_timestamp returns the UTC wall clock, not the target-zone wall clock -- ibis has no timezone method and the naive re-cast discards the conversion (verified 2026-07-29, ibis 12.0.0/duckdb: 12:00 instead of 17:30 for Asia/Kolkata) | — | — | 2026-07-29 | — | — |

### `ROUND_CALENDAR` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | unit | MONTH | — | unsupported | gate | build | — | ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- CEIL/ROUND_TIE_DOWN/ROUND_TIE_UP cannot compute the next calendar boundary; verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |
| ibis-polars | unit | YEAR | — | unsupported | gate | build | — | ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- CEIL/ROUND_TIE_DOWN/ROUND_TIE_UP cannot compute the next calendar boundary; verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |
| ibis-sqlite | multiple | 3 | — | unsupported | gate | build | — | ibis-sqlite has no TimestampBucket compilation rule -- multiple > 1 is unsupported for every unit; verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |
| ibis-sqlite | unit | HOUR, MICROSECOND, MILLISECOND, MINUTE, SECOND | — | unsupported | gate | build | — | ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |

### `ROUND_TEMPORAL` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | multiple | 2 | — | unsupported | gate | build | — | ibis-sqlite has no TimestampBucket compilation rule -- multiple > 1 is unsupported for every unit; verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |
| ibis-sqlite | unit | HOUR, MICROSECOND, MILLISECOND, MINUTE, SECOND | — | unsupported | gate | build | — | ibis-sqlite TimestampTruncate has no support for units finer than DAY (HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND); verified 2026-08-16, ibis 12.0.0 | — | — | 2026-08-16 | — | — |

### `STRPTIME_DATE` × narwhals (FKEY_SUBSTRAIT_SCALAR_DATETIME)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | gate | build | — | narwhals raises NotImplementedError for str.to_date() on the default pandas backend (it would return an object-dtype Series, diverging from the polars API); str.to_datetime() is unaffected and stays supported | — | — | 2026-07-30 | — | whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | failure_behavior | null | — | unsupported | gate | build | — | null-on-invalid custom temporal parsing is supported only by Polars | — | — | 2026-08-21 | — | — |

### `STRPTIME_DATE` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | ibis-sqlite has no compilation rule for StringToDate/StringToTimestamp (OperationNotDefinedError); format-driven parsing is unavailable on this dialect, so it is gated rather than left to fail natively | — | — | 2026-07-30 | — | whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | failure_behavior | null | — | unsupported | gate | build | — | null-on-invalid custom temporal parsing is supported only by Polars | — | — | 2026-08-21 | — | — |

### `STRPTIME_TIMESTAMP` × narwhals (FKEY_SUBSTRAIT_SCALAR_DATETIME)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | failure_behavior | null | — | unsupported | gate | build | — | null-on-invalid custom temporal parsing is supported only by Polars | — | — | 2026-08-21 | — | — |

### `STRPTIME_TIMESTAMP` × ibis (FKEY_SUBSTRAIT_SCALAR_DATETIME)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | ibis-sqlite has no compilation rule for StringToDate/StringToTimestamp (OperationNotDefinedError); format-driven parsing is unavailable on this dialect, so it is gated rather than left to fail natively | — | — | 2026-07-30 | — | whole-op gate on a WILDCARD_PARAM fact; cannot be keyed on an OpSpec param (OpSpecs are indexed by concrete argument name) — verified by the dedicated cross-backend gate tests in test_datetime_strptime_format.py |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | failure_behavior | null | — | unsupported | gate | build | — | null-on-invalid custom temporal parsing is supported only by Polars | — | — | 2026-08-21 | — | — |
| * | timezone | — | iana_timezone | unsupported | gate | build | — | strptime_timestamp silently drops the timezone (returns a naive timestamp) on ibis -- ibis has no timezone primitives, matching assume_timezone/to_timezone/local_timestamp/extract.timezone | — | — | 2026-08-15 | — | — |
| ibis-duckdb | timezone | — | iana_timezone | unsupported | gate | build | — | strptime_timestamp silently drops the timezone (returns a naive timestamp) on ibis -- ibis has no timezone primitives, matching assume_timezone/to_timezone/local_timestamp/extract.timezone | — | — | 2026-08-15 | — | — |

### `CAPITALIZE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The native backend does not implement ASCII_ONLY char_set semantics for this Substrait case operation | — | — | 2026-07-23 | — | — |
| polars | char_set | UTF8 | — | expr_capable | gate | build | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits UTF8, so the explicit option is observably equivalent to omission and cannot discriminate |

### `CAPITALIZE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
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
| narwhals-pandas | padding | LEFT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | padding | RIGHT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | padding | LEFT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | padding | RIGHT | — | unsupported | gate | build | — | center is a no-op on this backend, so padding cannot be honored | — | — | 2026-07-23 | — | — |

### `CENTER` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | character | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | dynamic arg silently miscompiles: str(Expr) bakes the unresolved expression's Python repr into the output as a literal string rather than raising — cannot be confirmed by an exception-based probe |
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
| ibis-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | ibis-polars has no compilation rule for StringTranslate (OperationNotDefinedError); the ASCII-only fold CASE_INSENSITIVE_ASCII needs for contains/starts_with/ends_with is unavailable on this dialect, unlike ibis-duckdb/ibis-sqlite which both support .translate() | — | — | 2026-08-12 | — | — |
| ibis-sqlite | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | ibis-sqlite's native LOWER()/UPPER() are ASCII-only (no ICU extension loaded); CASE_INSENSITIVE's Unicode-aware-lowercasing contract (e.g. Kelvin Sign U+212A -> 'k') is unavailable on this dialect alone in the Ibis family — gated unconditionally for every ibis-sqlite connection and every input (including purely-ASCII input, which SQLite's native LOWER() handles correctly, and any caller-supplied connection with a custom Unicode-aware LOWER()/UPPER() override loaded onto it) because the capability fact is keyed on (backend, dialect), a static identity, with no visibility into a specific connection's actual loaded extensions or a specific call's runtime string content | Use CASE_INSENSITIVE_ASCII instead if ASCII-only folding is sufficient (genuinely honored on ibis-sqlite via native translate()); otherwise Unicode-normalize both operands in Python (e.g. str.lower()) and reissue the comparison as CASE_SENSITIVE (NOT CASE_INSENSITIVE — this dialect-scoped gate is unconditional and still rejects CASE_INSENSITIVE even after preprocessing), or run this expression against a different Ibis dialect (ibis-duckdb) instead of ibis-sqlite | — | 2026-08-12 | — | — |

### `COUNT_SUBSTRING` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `COUNT_SUBSTRING` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | substring | — | — | literal_only | gate | build | — | Narwhals str.replace_all()'s pattern argument does not accept a column expression on any dialect (pandas or polars-backed) -- count_substring's fold is built on replace_all, unlike sibling search-operand params that are pandas-only restricted. | Use a literal string value instead of a column reference | NW-STR-03 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `COUNT_SUBSTRING` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-polars | substring | — | — | literal_only | gate | build | — | ibis-polars compiles this to Polars' native str.replace()/str.replace_all(), which does not support a dynamic (column-valued) pattern argument (tracked upstream as PL-STR-01/PL-STR-02 for the raw polars backend; see backlog item 81) | Use a literal string pattern instead of a column reference | PL-STR-01 | 2026-08-12 | — | — |

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
| ibis-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | ibis-polars has no compilation rule for StringTranslate (OperationNotDefinedError); the ASCII-only fold CASE_INSENSITIVE_ASCII needs for contains/starts_with/ends_with is unavailable on this dialect, unlike ibis-duckdb/ibis-sqlite which both support .translate() | — | — | 2026-08-12 | — | — |
| ibis-sqlite | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | ibis-sqlite's native LOWER()/UPPER() are ASCII-only (no ICU extension loaded); CASE_INSENSITIVE's Unicode-aware-lowercasing contract (e.g. Kelvin Sign U+212A -> 'k') is unavailable on this dialect alone in the Ibis family — gated unconditionally for every ibis-sqlite connection and every input (including purely-ASCII input, which SQLite's native LOWER() handles correctly, and any caller-supplied connection with a custom Unicode-aware LOWER()/UPPER() override loaded onto it) because the capability fact is keyed on (backend, dialect), a static identity, with no visibility into a specific connection's actual loaded extensions or a specific call's runtime string content | Use CASE_INSENSITIVE_ASCII instead if ASCII-only folding is sufficient (genuinely honored on ibis-sqlite via native translate()); otherwise Unicode-normalize both operands in Python (e.g. str.lower()) and reissue the comparison as CASE_SENSITIVE (NOT CASE_INSENSITIVE — this dialect-scoped gate is unconditional and still rejects CASE_INSENSITIVE even after preprocessing), or run this expression against a different Ibis dialect (ibis-duckdb) instead of ibis-sqlite | — | 2026-08-12 | — | — |

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
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LIKE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | match | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-01 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `LIKE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | * | — | — | unsupported | gate | build | — | ibis-polars has no compilation rule for StringSQLLike (OperationNotDefinedError) for any pattern, literal or dynamic; ibis-duckdb/ibis-sqlite both translate LIKE to native SQL correctly | Use ibis-duckdb/ibis-sqlite or a polars/narwhals backend for LIKE patterns | IB-STR-06 | 2026-08-12 | — | whole-op gate on a dialect-scoped WILDCARD_PARAM fact; cannot be keyed on an OpSpec param — verified by the dedicated cross-backend gate test in test_pattern.py (TestLikeIbisPolarsGate) and the native-bypass self-healing probe in test_op_level_gate_probes.py (test_like_ibis_polars_native_still_broken) |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
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
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| narwhals-pandas | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| * | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-polars | pattern | — | — | literal_only | gate | build | — | ibis-polars compiles this to Polars' native columnar-argument path, which raises Ibis's own UnsupportedArgumentError for a dynamic (column-valued) argument; a literal value works fine | Use a literal string pattern/separator instead of a column reference | IB-STR-09 | 2026-08-12 | — | — |

### `REGEXP_MATCH_ALL` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| * | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| * | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | occurrence | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | occurrence | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-duckdb | position | — | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | value-agnostic companion to the representative-value positional fact; the value-scoped disposition probe drives the native-path check |
| ibis-duckdb | position | 2 | — | unsupported | gate | build | — | The native backend does not honor the regexp position/occurrence/group option; it is silently ignored rather than applied | — | — | 2026-07-23 | — | — |
| ibis-polars | pattern | — | — | literal_only | gate | build | — | ibis-polars compiles this to Polars' native str.replace()/str.replace_all(), which does not support a dynamic (column-valued) pattern argument (tracked upstream as PL-STR-01/PL-STR-02 for the raw polars backend; see backlog item 81) | Use a literal string pattern instead of a column reference | PL-STR-02 | 2026-08-12 | — | — |

### `REGEXP_SPLIT` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | pattern | — | — | literal_only | gate | build | — | Polars regexp_string_split requires a literal pattern -- the map_elements fallback binds pattern as a Python closure value, not a column expression | Use a literal string regex pattern | PL-STR-04 | 2026-08-13 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |

### `REGEXP_SPLIT` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_DISABLED | — | unsupported | gate | build | — | The underlying regexp operation is unavailable on this dialect, so its option value cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |

### `REGEXP_SPLIT` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-sqlite | * | — | — | unsupported | gate | build | — | ibis-sqlite has no compilation rule for RegexSplit (OperationNotDefinedError) for any pattern, literal or dynamic; ibis-duckdb translates it to native SQL correctly and ibis-polars supports a literal pattern | Use ibis-duckdb, ibis-polars with a literal pattern, or a Polars backend for regex split | IB-STR-12 | 2026-08-13 | — | whole-op gate on a dialect-scoped WILDCARD_PARAM fact; cannot be keyed on an OpSpec param -- verified by a dedicated cross-backend gate test plus the native-bypass self-healing probe in test_op_level_gate_probes.py, mirroring item 83's TestLikeIbisPolarsGate / test_like_ibis_polars_native_still_broken |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| * | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| * | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | dotall | DOTALL_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-duckdb | multiline | MULTILINE_DISABLED | — | expr_capable | gate | build | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits this regexp flag value, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-duckdb | multiline | MULTILINE_ENABLED | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| ibis-polars | pattern | — | — | literal_only | gate | build | — | ibis-polars compiles regexp_string_split to Polars' native re_split, which raises Ibis's own IbisError for a dynamic (column-valued) pattern; a literal pattern works fine | Use a literal string pattern instead of a column reference | IB-STR-13 | 2026-08-13 | — | — |

### `REGEXP_STRPOS` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's non-default Substrait semantics | — | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement this regexp flag's CASE_INSENSITIVE_ASCII Substrait semantics | — | — | 2026-08-12 | — | — |
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
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `REPLACE` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | replacement | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-03 | 2026-07-05 | — | — |
| * | substring | — | — | literal_only | gate | build | — | Narwhals string methods require literal values, not column references, on the pandas backend. The polars-backed narwhals path supports expression arguments for several methods (declared as dialect-scoped EXPR_CAPABLE refinements below). | Use a literal string value instead of a column reference | NW-STR-03 | 2026-07-05 | — | — |
| narwhals-lazy | replacement | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-03 | 2026-07-05 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | replacement | — | — | expr_capable | gate | build | — | fixed upstream on the polars-backed narwhals path | — | NW-STR-03 | 2026-07-05 | — | — |

### `REPLACE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| ibis-polars | substring | — | — | literal_only | gate | build | — | ibis-polars compiles this to Polars' native str.replace()/str.replace_all(), which does not support a dynamic (column-valued) pattern argument (tracked upstream as PL-STR-01/PL-STR-02 for the raw polars backend; see backlog item 81) | Use a literal string pattern instead of a column reference | PL-STR-02 | 2026-08-12 | — | — |

### `REPLACE_SLICE` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | length | — | — | literal_only | gate | build | — | Polars str.replace_slice() requires a literal integer length, not a column expression | Use a literal integer length value | PL-STR-03 | 2026-07-05 | — | — |
| * | replacement | — | — | literal_only | gate | build | — | Polars str.replace_slice() requires a literal replacement string, not a column expression | Use a literal replacement string | — | 2026-07-05 | — | dynamic arg silently miscompiles: str(Expr) bakes the unresolved expression's Python repr into the output as a literal string rather than raising — cannot be confirmed by an exception-based probe |
| * | start | — | — | literal_only | gate | build | — | Polars str.replace_slice() requires a literal integer start, not a column expression | Use a literal integer start value | PL-STR-03 | 2026-07-05 | — | — |

### `REPLACE_SLICE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | length | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | — |
| * | replacement | — | — | literal_only | gate | build | — | Ibis has no native equivalent; mountainash composes this operation from literal parameters — dynamic column parameters are unsupported | Use a literal value, or the polars backend | — | 2026-07-05 | — | dynamic arg silently miscompiles: str(Expr) bakes the unresolved expression's Python repr into the output as a literal string rather than raising — cannot be confirmed by an exception-based probe |
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

### `SPLIT` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | * | — | — | unsupported | materialize_residue | materialize | — | narwhals-pandas' str.split() requires a pyarrow-backed pandas series (raises TypeError: 'This operation requires a pyarrow-backed series') against the plain numpy-backed storage most pandas DataFrames use; a pyarrow-backed pandas DataFrame (e.g. via .convert_dtypes(dtype_backend='pyarrow')) works correctly, as does narwhals-polars for any storage | Use a pyarrow-backed pandas DataFrame, narwhals-polars, Polars, or Ibis for string_split | NW-STR-22 | 2026-08-13 | TypeError | whole-op materialize-time storage residue (narwhals-pandas pyarrow-backed-series requirement) -- storage-dependent, not an intrinsic dialect-wide gap: a pyarrow-backed pandas DataFrame genuinely works, so this cannot be a build-time GATE (mirrors NW-LIST-01's identical pyarrow-storage-dependent CONTAINS/T_CONTAINS pattern) |

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | separator | — | — | literal_only | gate | build | — | Narwhals str.split() requires a literal separator string, not an Expr -- raises TypeError even for an Expr-wrapped literal | Use a literal separator string | NW-STR-21 | 2026-08-13 | — | — |

### `SPLIT` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | separator | — | — | literal_only | gate | build | — | ibis-polars compiles this to Polars' native columnar-argument path, which raises Ibis's own UnsupportedArgumentError for a dynamic (column-valued) argument; a literal value works fine | Use a literal string pattern/separator instead of a column reference | IB-STR-10 | 2026-08-12 | — | — |

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
| ibis-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | ibis-polars has no compilation rule for StringTranslate (OperationNotDefinedError); the ASCII-only fold CASE_INSENSITIVE_ASCII needs for contains/starts_with/ends_with is unavailable on this dialect, unlike ibis-duckdb/ibis-sqlite which both support .translate() | — | — | 2026-08-12 | — | — |
| ibis-sqlite | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | ibis-sqlite's native LOWER()/UPPER() are ASCII-only (no ICU extension loaded); CASE_INSENSITIVE's Unicode-aware-lowercasing contract (e.g. Kelvin Sign U+212A -> 'k') is unavailable on this dialect alone in the Ibis family — gated unconditionally for every ibis-sqlite connection and every input (including purely-ASCII input, which SQLite's native LOWER() handles correctly, and any caller-supplied connection with a custom Unicode-aware LOWER()/UPPER() override loaded onto it) because the capability fact is keyed on (backend, dialect), a static identity, with no visibility into a specific connection's actual loaded extensions or a specific call's runtime string content | Use CASE_INSENSITIVE_ASCII instead if ASCII-only folding is sufficient (genuinely honored on ibis-sqlite via native translate()); otherwise Unicode-normalize both operands in Python (e.g. str.lower()) and reissue the comparison as CASE_SENSITIVE (NOT CASE_INSENSITIVE — this dialect-scoped gate is unconditional and still rejects CASE_INSENSITIVE even after preprocessing), or run this expression against a different Ibis dialect (ibis-duckdb) instead of ibis-sqlite | — | 2026-08-12 | — | — |

### `STRPOS` × polars (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `STRPOS` × narwhals (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-pandas | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-pandas | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| narwhals-polars | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| narwhals-polars | case_sensitivity | CASE_SENSITIVE | — | expr_capable | gate | build | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate | — | — | 2026-07-23 | — | The builder default emits CASE_SENSITIVE, so the explicit option is observably equivalent to omission and cannot discriminate |

### `STRPOS` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| * | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE semantics for this Substrait string operation | Lowercase the input and search operand explicitly before applying the case-sensitive operation | — | 2026-07-23 | — | — |
| ibis-duckdb | case_sensitivity | CASE_INSENSITIVE_ASCII | — | unsupported | gate | build | — | The native backend does not implement CASE_INSENSITIVE_ASCII semantics for this Substrait string operation (same disposition as CASE_INSENSITIVE — neither case-fold value is wired here) | Fold the input and search operand to ASCII lowercase explicitly before applying the case-sensitive operation | — | 2026-08-12 | — | — |
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
| narwhals-pandas | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-pandas | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | ASCII_ONLY | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |
| narwhals-polars | char_set | UTF8 | — | unsupported | gate | build | — | The underlying case operation is unimplemented/incorrect on this backend (no-op or missing method), so char_set cannot be honored | — | — | 2026-07-23 | — | — |

### `SWAPCASE` × ibis (FKEY_SUBSTRAIT_SCALAR_STRING)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
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

### `JOIN_ASOF` × ibis (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | strategy | — | — | unsupported | gate | build | — | join_asof forward/nearest lowers to a non-equality candidate join; the ibis Polars backend rejects non-equality join predicates (TypeError: Only equality join predicates supported with pandas). | Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends. | IB-REL-15 | 2026-08-18 | — | — |

### `READ_RESOURCE` × polars (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | resource | — | — | unsupported | router_metadata | build | resource.dialect.comment_char is set or resource.dialect.comment_rows is set or resource.dialect.double_quote is set or resource.dialect.escape_char is set or resource.dialect.header_join is set or resource.dialect.header_rows is set or resource.dialect.line_terminator is set or resource.dialect.skip_initial_space is set | CSV dialect fields require the portable provider fallback reader | none needed — mountainash routes automatically | — | 2026-08-30 | — | router, not gate — fallback handles it; behaviour covered by relations resource tests |

### `READ_RESOURCE` × narwhals (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | resource | — | — | unsupported | router_metadata | build | resource.dialect.comment_char is set or resource.dialect.comment_rows is set or resource.dialect.double_quote is set or resource.dialect.escape_char is set or resource.dialect.header_join is set or resource.dialect.header_rows is set or resource.dialect.line_terminator is set or resource.dialect.skip_initial_space is set | CSV dialect fields require the portable provider fallback reader | none needed — mountainash routes automatically | — | 2026-08-30 | — | router, not gate — fallback handles it; behaviour covered by relations resource tests |

### `READ_RESOURCE` × ibis (RKEY_MOUNTAINASH_REL)

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| * | resource | — | — | unsupported | router_metadata | build | resource.dialect.comment_char is set or resource.dialect.comment_rows is set or resource.dialect.delimiter is non-default or resource.dialect.double_quote is set or resource.dialect.escape_char is set or resource.dialect.header is false or resource.dialect.header_join is set or resource.dialect.header_rows is set or resource.dialect.line_terminator is set or resource.dialect.null_sequence is set or resource.dialect.quote_char is set or resource.dialect.skip_initial_space is set | CSV dialect fields require the portable provider fallback reader | none needed — mountainash routes automatically | — | 2026-08-30 | — | router, not gate — fallback handles it; behaviour covered by relations resource tests |

### `WITH_ROW_INDEX` × ibis (RKEY_MOUNTAINASH_REL)

#### Dialect-scoped whole-op

| Dialect | Param | Option values | Value class | Level | Enforcement | Boundary | Condition | Message | Workaround | Upstream | Since | Native errors | Probe-exempt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ibis-polars | * | — | — | unsupported | gate | build | — | with_row_index lowers to a window function (row_number); the ibis Polars backend has no WindowFunction translation rule. | Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends. | IB-REL-01 | 2026-08-01 | — | relation op-level gap; covered by relation with_row_index cross-backend tests |

