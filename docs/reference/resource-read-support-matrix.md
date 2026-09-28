# Resource-read support matrix

How each relation backend reads a `DataResource`, and how it degrades when the
optional `files` extra is absent. Native local scans stay lazy; the
`mountainash-files` fallback is eager (full Arrow materialization).

## Explicit provider bindings

`ResourceReadRelNode.provider_binding` is runtime-only and excluded from descriptor
serialization. An explicit provider instance or entry-point key plans and materializes
one portable Arrow table, then the Polars, Narwhals, or Ibis reader adapts that same
table to its native relation type. Provider packages are local sibling dependencies;
they are not registry-distributed requirements.

| Resource kind | Polars | Narwhals | Ibis | `files` extra absent |
|---|---|---|---|---|
| inline (`.data`) | PydataIngress | PydataIngress | PydataIngress | works (no files dep) |
| local CSV/Parquet, default dialect | native `scan_*` | native `scan_*` | native `con.read_*` | works (native) |
| local CSV, native-safe non-default dialect (delimiter/header/quote/null) | native (kwargs) | native (kwargs) | files fallback | `MissingFilesDependency` (Ibis) |
| local CSV, `escape_char` dialect (mappable, not native-representable) | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| any CSV, UNmappable dialect field | `UnsupportedResourceFormat` | `UnsupportedResourceFormat` | `UnsupportedResourceFormat` | same (fail-closed is pure) |
| local JSON | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| plain multi-path (concrete local CSV/Parquet) | native `scan_*` concat | native `scan_*` concat | native `con.read_*` | works (native) |
| glob *pattern* | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| gzip / zip archive | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| remote (any format) | files fallback | files fallback | files fallback | `MissingFilesDependency` |

## Dialect fidelity

`TableDialect` maps onto `CsvSpec` (mountainash-files ≥26.7.1):
`delimiter`, `header`, `quote_char`, `escape_char`, `null_sequence`. These are
the **CsvSpec-mappable** (seam-supported) fields. Within them there is a stricter
**native-representable** subset — `delimiter`, `header`, `quote_char`,
`null_sequence` — that a native `pl.scan_csv` can express via kwargs. A
native-safe non-default dialect (e.g. `delimiter=";"`) is honoured natively with
kwargs on Polars/Narwhals (stays lazy) and via the `CsvSpec` fallback on Ibis —
identical values across backends.

`escape_char` is CsvSpec-mappable but **not** native-representable — `pl.scan_csv`
has no escape parameter — so an escape-bearing dialect routes to the `CsvSpec`
fallback on **all three** backends (where it is honoured correctly), never read
natively-and-wrong on Polars/Narwhals while Ibis reads it right
(`consistency-guarantees`).

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

## Dependency wiring

`mountainash-files` is the opt-in `files` extra; descriptor storage helpers use
the `storage` extra. Development test environments select sibling checkouts.
Installed-artifact verification instead selects exact files, transport,
settings and auth-client wheels, without the retired secrets distribution.

For the settings 0.1 migration rehearsal, files `>=26.8.0,<27` and transport
`>=26.7.0,<27` are provisional ranges. Those version numbers alone do not
identify the migrated candidates: use the hash-qualified artifact handoff in
the M4b execution receipt. Before publication, dependency floors must advance
to the migrated published releases. Downstream merge/publication remains on
hold until settings 0.1.0 is published.

Authenticated remote resource reads remain deferred under spec §E of
`2026-07-04-dag-hardening-pr3-readers-item32-design.md`. The existing resource
reader does not expose storage/auth profile or selected-store parameters.
