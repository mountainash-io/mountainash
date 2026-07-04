# Resource-read support matrix

How each relation backend reads a `DataResource`, and how it degrades when the
optional `files` extra is absent. Native local scans stay lazy; the
`mountainash-files` fallback is eager (full Arrow materialization).

| Resource kind | Polars | Narwhals | Ibis | `files` extra absent |
|---|---|---|---|---|
| inline (`.data`) | PydataIngress | PydataIngress | PydataIngress | works (no files dep) |
| local CSV/Parquet, default dialect | native `scan_*` | native `scan_*` | native `con.read_*` | works (native) |
| local CSV, mappable non-default dialect | native (kwargs) | native (kwargs) | files fallback | `MissingFilesDependency` (Ibis) |
| any CSV, UNmappable dialect field | `UnsupportedResourceFormat` | `UnsupportedResourceFormat` | `UnsupportedResourceFormat` | same (fail-closed is pure) |
| local JSON | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| plain multi-path (concrete local CSV/Parquet) | native `scan_*` concat | native `scan_*` concat | native `con.read_*` | works (native) |
| glob *pattern* | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| gzip / zip archive | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| remote (any format) | files fallback | files fallback | files fallback | `MissingFilesDependency` |

## Dialect fidelity

`TableDialect` maps onto `CsvSpec` (mountainash-files ≥26.7.1):
`delimiter`, `header`, `quote_char`, `escape_char`, `null_sequence`. A
**mappable** non-default dialect (e.g. `delimiter=";"`) is honoured natively
with kwargs on Polars/Narwhals (stays lazy) and via the `CsvSpec` fallback on
Ibis — identical values across backends.

Any other set dialect field (`double_quote`, `skip_initial_space`,
`comment_char`, `line_terminator`, `header_rows`, `header_join`,
`case_sensitive_header`) is **fail-closed UNIFORMLY on every backend**: a
single pure `ensure_dialect_supported()` check runs before routing, so such a
field raises `UnsupportedResourceFormat` naming it on Polars/Narwhals/Ibis
alike — never read natively on one backend while raising on another
(`consistency-guarantees`). The supported-dialect surface is the cross-backend
intersection = what `CsvSpec` can carry. `csvddf_version` is metadata and is
ignored.

## Laziness

Only inline and native local CSV/Parquet scans are genuinely lazy. Every
fallback-routed read materializes the whole file into an in-memory `pa.Table`
first; the resulting `.lazy()` / `memtable` wrapper is lazy-typed over
already-read bytes, not a lazy scan.

## Dependency wiring (deferred to release)

On `develop`, `mountainash-files` is the opt-in `files` extra provisioned via
sibling path pins in the test envs. Production tiering (core vs `files` extra),
authenticated remote reads, and the monorepo-index publish are deferred — see
spec §E of `2026-07-04-dag-hardening-pr3-readers-item32-design.md`.
