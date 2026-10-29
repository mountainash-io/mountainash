# Resource-read support matrix

How each relation backend reads a `DataResource`. Eligible CSV/Parquet reads use
native engines automatically; the `mountainash-files` fallback materializes Arrow.
Item 387 remains **blocked** on non-range HTTP preservation (`PL-REL-01`, backlog 393).
Passing range-capable HTTP and S3 cases does not qualify that missing case.

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
| local CSV, native-safe non-default dialect (delimiter/header/quote/null) | native (kwargs) | native on Polars-backed targets | DuckDB native; other engines retain fallback | works on native routes |
| local CSV, `escape_char` dialect (mappable, not native-representable) | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| any CSV, UNmappable dialect field | `UnsupportedResourceFormat` | `UnsupportedResourceFormat` | `UnsupportedResourceFormat` | same (fail-closed is pure) |
| local JSON | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| plain multi-path (concrete CSV/Parquet) | native concat when access is representable | same on Polars-backed targets | native when representable | works on native routes |
| glob *pattern* | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| gzip / zip archive | files fallback | files fallback | files fallback | `MissingFilesDependency` |
| unconfined S3 CSV/Parquet, bound static credentials and representable options | native | native on Polars-backed targets | DuckDB native; other engines fallback | works on native routes |
| unconfined anonymous HTTP(S) CSV/Parquet, range-capable source | native | native on Polars-backed targets | DuckDB native; other engines fallback | works on native routes |
| HTTP without Range support | currently fails: `PL-REL-01` | same on Polars-backed targets | existing native/fallback reads work | qualification blocker, not a supported refusal |
| active remote confinement, authenticated HTTP, other remote formats/auth/options | files fallback | files fallback | files fallback | `MissingFilesDependency` |

Narwhals pandas/PyArrow and other non-Polars targets retain their existing fallback
and import behavior. No format-specific speed threshold chooses the route.

## Location policy

Confinement is off by default. Enable it with a profile's `LOCATION_POLICY` or
an explicit loader/binding `policy=`; see [datapackage](datapackage.md#location-policy).
Under an active policy transport decides the location and native readers stay within
the qualified local allow-list. Other reads use the files fallback. With no policy,
or with `LocationPolicy(allow_unconfined=True)`, the table above applies.

| Resource kind | Polars / Narwhals (`narwhals-polars`, `narwhals-lazy`) | Ibis on DuckDB | Other Ibis backends |
|---|---|---|---|
| local file | native `scan_*`, effective path, `glob=False` | native `read_*`, `[` `*` `?` escaped | files fallback → memtable |
| local directory (tree-checked) | native, `glob=False`; Polars expands it | native only if path has none of `[` `*` `?`; otherwise `LocationNotAllowed` | `LocationNotAllowed` (use a glob) |
| glob pattern, archive, JSON | files fallback | files fallback | files fallback |
| remote | policy permission required; files fallback | same | same |
| unknown scheme | `LocationNotAllowed` | `LocationNotAllowed` | `LocationNotAllowed` |

Ibis directory reads under a policy are narrower than today (owner-approved 2026-10-27):
the memtable route cannot read a bare directory. The existing Ibis `SCHEMA` directory
limitation is unchanged and adds no new route. Native Windows drive and UNC handling is
specified but not CI-verified. No new confined-remote native route is introduced.

## Dialect fidelity

`TableDialect` maps onto `CsvSpec` (mountainash-files ≥26.7.1):
`delimiter`, `header`, `quote_char`, `escape_char`, `null_sequence`. These are
the **CsvSpec-mappable** (seam-supported) fields. Within them there is a stricter
**native-representable** subset — `delimiter`, `header`, `quote_char`,
`null_sequence` — that native readers can express via kwargs. Polars/Narwhals
accept one-byte delimiters; DuckDB accepts up to four bytes. Longer delimiters and
other unrepresentable values retain the existing fallback. Headerless CSV columns
use `field1`, `field2`, … consistently with the files reader. DuckDB also honors
representable non-default dialects; other Ibis engines retain their existing rules.

`escape_char` is CsvSpec-mappable but **not** native-representable — `pl.scan_csv`
has no escape parameter — so an escape-bearing dialect routes to the `CsvSpec`
fallback on **all three** backends (where it is honoured correctly), never read
natively-and-wrong on Polars/Narwhals while Ibis reads it right
(`consistency-guarantees`).

Fields outside the existing `CsvSpec` mapping raise `UnsupportedResourceFormat`
before routing. Mappable but non-native dialect options retain the files parser;
native selection must not silently drop them.

## Laziness

Polars scans and `narwhals-lazy` retain downstream projection/filter pushdown.
`narwhals-polars` remains eager: it reads before downstream operations, so native
selection does not imply reduced transfer. DuckDB collection can return a deferred
Ibis table bound to the selected connection. Fallback routes materialize the whole
file into Arrow first; a subsequent lazy wrapper is not a lazy scan.

### Native access and DuckDB setup

Static S3 credentials are supplied explicitly, including an empty session token so
unrelated ambient credentials cannot contaminate them. Absent auth and
`NoAuthProfile` retain transport's ambient-credential behavior; neither means
unsigned S3 access. Session/role/profile-chain credentials remain with transport.

Representable endpoint, region and addressing options are translated by Mountainash,
not by transport. Explicit timeout, header, redirect or TLS options without a
faithful engine representation select fallback before reading. Actual native
authentication, network and parse errors propagate; there is no second-route retry.
The live S3 qualification used two RustFS stores, not AWS/R2/B2/GCS/Azure services;
those services have not been live-qualified by this change.

DuckDB setup uses temporary scoped secrets on the actual selected database. An
incompatible or caller-owned overlapping secret selects fallback without replacing
it. Successful setup survives loader/visitor return and another connection closing.
Borrowed connections and caller settings are not closed or rewritten.

Explanation/eligibility may resolve descriptor metadata and inspect engine state,
but do not open resource data or create setup. Compile raises the existing
`CompileRequiresExecutionError` when new setup is needed; execution installs it,
and subsequent compilation may reuse compatible setup. Schema inspection retains
its existing metadata probes.

**Additional qualification blocker:** if a shared database gains conflicting setup
after preparation, a native resource can switch to an unowned fallback and lose the
selected connection. Compile can also perform the eager read instead of rejecting
it first. Sequential conflict/lifetime witnesses do not cover this case. Transfer
ownership must remain in preparation; a compilation-time replanning patch was
removed rather than changing that contract without approval.

## Dependency wiring

`mountainash-files` is the opt-in `files` extra (also included in the `ibis` extra);
`mountainash-transport` is a required dependency and the `storage` extra is removed.
Development test environments select sibling checkouts.
Installed-artifact verification instead selects exact files, transport,
settings and auth-client wheels, without the retired secrets distribution.

For the settings 0.1 migration rehearsal, files `>=26.8.0,<27` and transport
`>=26.7.0,<27` are provisional ranges. Those version numbers alone do not
identify the migrated candidates: use the hash-qualified artifact handoff in
the M4b execution receipt. Before publication, dependency floors must advance
to the migrated published releases. Downstream merge/publication remains on
hold until settings 0.1.0 is published.

Resources and packages accept trusted runtime access through
`with_storage(storage_profile, auth_profile=..., policy=...)`. The files fallback,
byte reads, schema inspection and matching-provider descriptor references use that
binding. Profiles and credentials are not serialized into descriptors.
