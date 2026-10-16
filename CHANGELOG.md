# Changelog

## Unreleased — 2026-10-16

### Fixed
- Polars 2 migration (332): replace removed String-to-temporal casts with native planning-time parsing on Polars and Narwhals-on-Polars, including nested List/Array/Struct values. Preserve target units, naive wall-clock versus zoned instant semantics, parent nulls, failure policies and window composition. Declared Date ingress and date-range validation now complete through the repaired cast path. The dependency requires `polars>=2,<3`.
- Polars 2 list-to-struct conversion (332): lower declared upper bounds to explicit field names, preserve explicit-field precedence (including zero fields), ragged padding and the existing null-list-to-null-fields result.
- Polars 2 relation fingerprints (332): use the current seeded hash API while retaining two-lane accumulation, row-order/batch invariance and persisted profile identity. Hash compatibility remains qualified by the recorded Polars version; fingerprints from different Polars versions are not interchangeable.
- Reconcile native Decimal qualification on Polars 2 (332): floor division, modulus and reverse forms now execute on the five Polars-kernel provider identities; power remains unsupported. Regression coverage retains exact values, native zero-divisor errors, signed rounding carry, sufficient integer capacity and resolved-schema consistency instead of pinning incidental output precision. No arithmetic emulation or authored-cast policy change is introduced.
- PostgreSQL dynamic case-insensitive `str.regex_contains()` patterns, including native Ibis expressions, now receive a declared `BackendCapabilityError` on Ibis 12.0.0 / SQLGlot 29.0.1 / PostgreSQL 16.15 (321, IB-STR-16). Native literals and sensitive plain-column matching remain allowed. Trusted, excluded-semantic and unqualified executions retain native lowering; unknown forms are not classified as supported. No SQL rewrite is added, and case-sensitive concatenated patterns remain unresolved.
- PostgreSQL Decimal conversion with `failure_behavior="null"` now raises a declared `BackendCapabilityError` under selected semantics protection on Ibis 12.0.0 / SQLGlot 29.0.1 / PostgreSQL 16.15 (322, IB-CAST-04). This deliberately refuses the mode even for valid/null inputs because native `TryCast` lowers to strict `CAST`. Explicit `failure_behavior="throw"` remains available; conform discard conversions share the gate. Trusted, excluded-semantic and unqualified executions retain native behavior. No SQL workaround is added.

## Unreleased — 2026-10-15

### Fixed
- Narwhals-pandas dynamic `str.regex_contains()` patterns now receive a declared `BackendCapabilityError` under selected protection on Narwhals 2.27.1/pandas 3.0.6 (313). Python-string and expression-literal patterns remain supported; working dynamic patterns on other providers are unchanged. Other dependency versions remain unqualified rather than automatically blocked.
- Ibis 12.0.0 now receives declared, dialect-scoped capability refusals for public Decimal conversion on MySQL, SingleStoreDB and Exasol (missing `RegexReplace`, 323), and regex matching on Exasol (missing `RegexSearch`, 330). Other operations, versions and existing policy presets are unchanged. These gates do not repair translators or deny the databases' native Decimal/regex facilities.
- Narwhals-PyArrow dynamic regex patterns now receive a literal-only capability refusal on Narwhals 2.27.1/PyArrow 26.0.0; string and expression-literal patterns remain allowed. Public Decimal conversion now receives typed adapter-unavailability refusals for Narwhals 2.27.1 with PyArrow 26.0.0 or DuckDB 1.5.6. DuckDB dynamic regex and ordinary conversions are unchanged; other versions remain unqualified. No native-provider implementation or workaround is added (313).

## Unreleased — 2026-10-14

### Changed
- Raised the Narwhals minimum to 2.27.1 so pandas-backed string casts preserve nulls instead of converting them to text (#391); no local workaround or runtime gate is added.
- Removed the transit policy registry, call wrappers, tracing API, AST census and inventory generator (248, first deletion slice). Native operations, conversion routes, outputs, placement, ownership and real conversion errors are unchanged; the wrapper's pandas-result rejection and trace records are retired. Upstream-internal pandas, native pandas execution and requested pandas output remain supported. Conversion simplification and validation/materialization work in 248/249 remain open.
- Simplified Polars output and operand conversion by delegating recognized pandas, Arrow and Ibis imports to the native Polars constructor. Native Polars passthrough, Narwhals conversion, lazy execution and existing conversion errors remain unchanged; pandas inputs and requested pandas outputs remain supported.
- Raised the pandas minimum to 3.0.0 so typed-null String columns retain their string type on Arrow export (#392). Pandas 2.x is no longer supported; the Arrow minimum is unchanged. Native interval-construction tests retain version-aware applicability for #386, separate from expression compilation.

### Fixed
- Install the existing pinned `pytest-mock` test dependency in the CI Hatch environment so migrated ownership, extraction and reuse tests can resolve their `mocker` fixture.
- Remove the logical-snapshot test's blanket `to_pandas()` prohibition; retain owned-copy/extraction counts and assert exact snapshot values across Ibis backends.
- Materialization residue checks now inspect Arrow scalar values rather than scalar-object truthiness, preventing false/null markers from rejecting valid results on PyArrow 16 while retaining true-marker rejection.
- Removed the obsolete egress-factory test requiring pandas input rejection: pandas is registered, and the test depended on incidental version-specific type detection rather than a supported rejection contract.

## Unreleased — 2026-10-13

### Added
- Cross-backend declared-Decimal arithmetic coverage (288): direct native arithmetic is separated from explicitly authored Float64 computation and final Decimal conversion, including operand forms, reductions, rounding modes, nonfinite values and capacity boundaries. Existing Decimal cast/product refusals and native extraction defects remain visible; no automatic widening or numerical policy is introduced.

### Fixed
- `dt.to_timezone()` now uses native Ibis timestamp casts instead of refusing every Ibis call (310), retaining the declared timestamp scale. DuckDB and Polars return the requested timezone; SQLite supports UTC and already-matching no-op casts. Dialect-specific precision and composed-expression behavior remain native, documented divergences rather than conversion gates.
- Removed a redundant tier marker from the direct-Decimal aggregate tests so CI's single-tier collection guard passes; inherited cross-backend coverage is unchanged.
- Composed window expressions now inherit their enclosing `.over()` context, allowing `pct_change(...).over(...)` to compile its nested lag without applying a second native window. Existing backend window limitations remain.
- `factorial()` now reports its existing unsupported status explicitly instead of returning `None` from an unfinished builder.
- Generated datacontract checks now accept valid native Polars arrays, including empty arrays and optional nulls (backlog 290). The logical snapshot boundary unwraps array cells before validation without a JSON round-trip; required and nested constraints remain enforced.
- Flat dataclass source declarations now survive relation schema inference, allowing conformance and structured joins without caller-side materialization (backlog 289). Single instances and homogeneous lists use metadata only, with no row scan; mixed-class schema completeness is not guaranteed.
- ASOF schema inference and transport lineage now omit merged right-side `on`/`by` keys, so `select(*joined.columns)` and subsequent joins no longer reference phantom columns (backlog 255). Pandas-backed nearest ASOF preserves left-column order; matching, tie selection and row ordering are unchanged.
- Projection schema inference now preserves source types through field aliases and name-only selectors, and reports `UNKNOWN` for computed outputs instead of retaining a replaced column's stale type (backlog 303, #376). Decimal conform introspection accepts unknown evidence without weakening concrete conversion or terminal validation.
- Ibis-DuckDB fingerprint batches now safely conform to the compiled result's declared Arrow schema, fixing Decimal arithmetic schema mismatches (backlog 304). Typed-empty results and reader/transaction ownership are preserved. Overflow and fractional-digit loss raise; authors remain responsible for explicit Decimal widening.
- Flat dataclass and Pydantic ingress now uses declared scalar source types during construction, preserving late non-null values and typed all-null columns (backlog 302). Nullable Pydantic annotations resolve to their value type without changing whether the field is required.
- PyData ingress accepts keyword-only `source_spec` and `inline_conform`. Explicit source declarations override model annotations; unrefined `ANY` falls through to existing evidence. Target `type_spec` remains separate, target conversion defaults to enabled, and undeclared row inference remains bounded to 100 rows with no extra scan or retry.
- Conversion-boundary CI checks now enforce policy against the live AST census rather than a copied source-fingerprint snapshot. Unwrapped/unknown boundaries and prohibited transit remain rejected; the inventory CLI remains available for audit reports.

## Unreleased — 2026-10-12

### Fixed
- `ma.concat()` now widens top-level timestamp precision before native unions on Polars, Narwhals and Ibis-DuckDB/Ibis-Polars, fixing UTC column/literal schema mismatches without fractional loss (#369). Optional `timezone="..."` normalizes all-aware columns to an explicit IANA target before union/distinct; naive and mixed-awareness columns are not localized. SQLite retains native default concat and reports `BackendCapabilityError` for explicit aware normalization; lossless SQLite reconciliation remains unsupported.
- `str.regex_contains()` now accepts literal expressions and per-row/computed patterns through the public expression API (#364), preserving conditional projection names without native wrappers. Dynamic patterns execute on Polars, Narwhals-Polars, Ibis-DuckDB and Ibis-SQLite; Narwhals-pandas/PyArrow and Ibis-Polars retain native restrictions. Literal patterns and `regex_match` remain supported. Opaque native-expression metadata is unchanged; the ignored `case_sensitive=False` option remains separately tracked in backlog 297.
- `str.regex_contains()` and its literal-only `str.regex_match()` wrapper now honor `case_sensitive=False` using native regex flags (backlog 297). Explicit inline flags retain their native meaning; default behavior, dynamic-pattern restrictions, Unicode rules and null handling remain backend-native.
- `str.regex_contains()` now accepts literal expressions and per-row/computed patterns through the public expression API (#364), preserving conditional projection names without native wrappers. Dynamic patterns execute on Polars, Narwhals-Polars, Ibis-DuckDB and Ibis-SQLite; Narwhals-pandas/PyArrow and Ibis-Polars retain native restrictions. Literal patterns and `regex_match` remain supported. Opaque native-expression metadata is unchanged.
- `Relation.with_row_index()` now exposes its native ordinal dtype and column placement during schema introspection, including DAG references (#366). Unresolved references expose the ordinal with `UNKNOWN` dtype without requiring execution; native execution and collision behavior are unchanged.
- Row-index documentation and cross-backend assertions now distinguish native frame positions from SQL's unspecified row order and row-to-ordinal assignment. Ordinals are not persistent identity, and unresolved metadata does not certify complete source fields or native column order.
- Whole-row `Relation.unique()` now preserves inferred input field names, order and types, including empty inputs and downstream joins (#365). Keyed DISTINCT and execution behavior are unchanged.

## Unreleased — 2026-10-11

### Added
- Top-level decimal conversion through `Relation.conform()` with explicit `FieldSpec.rounding`, persisted as `x-mountainash.rounding` beside dtype (280). Reuses the native decimal cast and existing coerce/discard policies, preserves exact output/inferred types, and applies existing numeric-text preparation and null filling on conversion. Matching decimals remain unchanged, including nulls; evolve/freeze and missing-column policies are unchanged. Existing precision, backend and rounding limits still apply.

### Changed
- The Ibis extra now requires Ibis 12+ and SQLGlot `>=29.0.1,<30.18.0`, matching mountainash-data. SQLGlot 30.22.0 still fails Ibis 12 table deletion; the existing ceiling remains necessary.
- Local/CI analytical rehearsal pins are Ibis 12.0.0, SQLGlot 30.17.0 and DuckDB 1.5.6. DuckDB test environments no longer impose `<1.3`; their floor is 1.5.6.
- Backward ASOF on Ibis-DuckDB permits any right row tied at the nearest eligible key; last-input-row selection is not portable. The duplicate-right regression accepts either valid complete output on DuckDB and retains exact last-row assertions on other backends. No runtime planner override or xfail is used.

### Fixed
- The `ibis` extra now declares `mountainash-data>=0.1.0,<0.2`, required by the existing SQL transaction/owned-copy integration (261). Base installations remain Data-free; development/CI source constraints and release import checks include the dependency. Public-extra installation still requires sibling publication.
- Ibis semi/anti joins between identical or structurally equal relations no longer raise `IbisInputError` (258).
- Narwhals semi/anti joins using `left_on`/`right_on` preserve the left-only output without projecting absent or duplicate right columns (258).
- Ibis dialects and all Narwhals variants (including pandas DataFrames routed through Narwhals) now reject product aggregates with `BackendCapabilityError`; Polars product behavior is unchanged. Retired the Ibis `EXP(SUM(LN(x)))` workaround recommendation and historical product-divergence examples (239).
- Cross-backend tests import exceptions from DuckDB's public API rather than the removed `duckdb.duckdb` module, allowing collection on current DuckDB releases.
- The compound eligibility regression explicitly sorts its output instead of expecting an incidental DuckDB filter-order failure; eligible-row assertions remain unchanged.

## Unreleased — 2026-10-10

### Added
- `ma.DecimalDtype(precision, scale)`, an exact decimal descriptor, with `.cast(DecimalDtype(...), rounding=...)` for native conversion on Polars, Polars-lazy, Ibis-DuckDB and Ibis-Polars, and `ma.lit(value, dtype=...)` for typed literals. `rounding=` takes `"half_to_even"`, `"half_away_from_zero"` or `"to_zero"` and is required for decimal targets. The value is rounded once, from the text as written, by the engine's own text-to-decimal cast, so the result does not depend on the target precision (`"1.2451"` gives `1.25` at both `(10,2)` and `(16,2)`). Exponent text is passed to the engine, not interpreted by mountainash. Integer-part overflow always raises; invalid text raises or becomes null per `failure_behavior`. The Narwhals-based backends and SQLite refuse with a declared `BackendCapabilityError` (Narwhals #3698/#3702). Cast targets are limited to precision 16 (declarations allow up to 38) because Polars' own `Decimal.round` aborts the process when a carry exceeds the type's width. Known limits, all documented and each covered by a strict test: `to_zero` on the Ibis backends is exact only within `17 - p` digits past the scale (a value that already fits the target is never changed); DuckDB mis-rounds exponent text below the last place and cannot parse some exponent text at scale 12 or more under the two half modes; and an exact tie written with an exponent follows the engine's own tie rule. Text is classified as a number by its shape, so a finite number too large for any float raises under both failure behaviours. See [Exact decimals](docs/website/features-technical/typespec-conform.md#exact-decimals) (241).
- `FieldSpec.dtype` declares a field's exact decimal. It persists under `x-mountainash.dtype` (including inside object and array-item fields), lowers to each backend's native decimal, is extracted from native decimal columns with precision and scale kept, and is compared by `compare_specs`. A malformed `x-mountainash.dtype` raises `InvalidDtypeDeclaration` on load.
- `conform()` verifies a declared decimal field and never converts it: a matching column passes unchanged (previously a decimal column raised during conform), and any other type follows the `data_type` policy, with `coerce`/`discard_*` raising `DecimalConversionRequiredError`. A missing declared decimal column under `null_fill` becomes a typed decimal null (241).

### Changed
- Native decimal columns now extract as `NUMBER` fields carrying `dtype` instead of raising `UnknownDtypeError`, and relation schema inference reports them as `DecimalDtype`. `.cast` is now provided by a Mountainash extension builder that builds the unchanged Substrait cast for every non-decimal target.

## Unreleased — 2026-10-09

### Added
- `Relation.fingerprint(keys=..., columns=..., batch_size=5000)` for scoped, runtime-versioned per-column drift fingerprints on Polars and Ibis-DuckDB. Includes exact row counts and typed compatibility descriptors; PostgreSQL is deferred pending reader lifecycle fixes. See [Selective fingerprints](docs/guides/selective-fingerprints.md).

## Unreleased — 2026-10-08

### Added
- Owned `Relation.snapshot()` and `ma.materialization_scope()` with checkpoint policy, detach, and sequential batch capture (257). See [Owned snapshots](docs/guides/owned-snapshots.md) for supported routes, lifetime, and SQL preparation limits.

### Fixed
- Repeated Ibis DAG, validation, logical-terminal, and transport materialization now observes fresh source values while earlier results remain alive (257).
- Ibis `collect()` documentation now describes deferred pass-through behavior.

## Unreleased — 2026-10-01

### Changed
- `Relation.conform()` and `Validator` now own the declarations they acquire. Editing a TypeSpec, contract override, contract `Config` or contract class after building a conform relation or `Validator` no longer changes that consumer; construct a new one to use the edit. Compiled validation checks isolate expression argument, option, conditional and window containers while native values and callbacks stay uncopied. Errors from a contract's `to_typespec()`/`to_checks()` now surface when the `Validator` is constructed.
- Grouped and global aggregates now enforce backend-independent scalar names for keys and measures, including direct AST and DAG plans. Nested aliases and name transformations are retained; literal-first reductions use `literal`. Ibis-generated names are replaced; use explicit aliases to retain a chosen historical name.
- Aggregate keys and measures share one collision namespace. Repeated reducers of one column and key/measure collisions require distinct aliases. Complete aggregate schemas raise when native/selector output names or cardinality are unavailable, without gating otherwise supported metadata-free collection.
- Aggregate key types follow ordinary source fields through name-only wrappers rather than matching the output name to an unrelated source column. Computed keys and measures remain `UNKNOWN`.
- DAG descriptor export omits unavailable optional schema by default, but raises `MissingResourceSchema` if doing so would discard declared foreign keys. Strict export rejects incomplete schemas; malformed-plan and duplicate-name errors still propagate.
- Relation `select` and `with_columns` now assign backend-independent names to resolvable single-output Mountainash expressions. On Ibis, `.with_columns(ma.col("n").fill_null(0))` replaces `n` instead of adding a generated `Coalesce(...)` column; use `.alias("filled_n")` to add a column while retaining `n`.
- Membership projections inherit the needle's name: `.with_columns(ma.col("n").is_in([2, 4]))` now replaces `n` rather than adding the historical `literal` output. Use `.alias("is_member")` for a separate result.
- Duplicate resolved projection outputs raise a build-time `ValueError`, including on Narwhals-pandas, which previously retained the last expression. Incomplete projection schemas now raise explicitly, and metadata lineage fails when output names cannot be mapped safely. Native aliases do not prove single-output cardinality.
- See [Projection and aggregate output names](docs/guides/projection-naming.md) for requires-alias operations and compatibility boundaries. Standalone compilation, selector support, DISTINCT routing and literal-only select row counts are unchanged; no backend parity is claimed for empty-name materialization.
- Keyed joins now produce one output contract on every backend: all left columns, then all right columns, and `.columns`, collected data and structured-field lineage agree. `left_on`/`right_on` joins keep the right key (Polars and Narwhals previously dropped it for some join types); pass `coalesce=True` to merge the keys into the left key column (for right/outer joins its value is `coalesce(left, right)`). `on=` joins still merge by default; `coalesce=False` keeps `<key>_right`.
- Narwhals right joins now suffix right-side name clashes (previously the left side); Polars right `on=` joins use the left-then-right column order.
- A right column whose suffixed name is already taken becomes `<name><suffix>_1` (then `_2`, …) with a `UserWarning` at execution, instead of a backend error. Nested joins on the same fields therefore yield `w_right`, `w_right_1`, ….
- `.columns` names raw Python data passed to `join()` (a dict of columns or a list of row dicts); dtypes are reported as unknown until execution.
- With `coalesce=True`, a merged key whose two sides have different dtypes reports an unknown dtype in `.schema`, matching projection inference for `coalesce`.

### Fixed
- Value checks, including `TYPE_FORMAT`, now construct Boolean failure masks for empty input instead of reporting a `Null`-typed filter-predicate error. Existing conformance/backend limitations and nonempty/null behavior are unchanged.
- Row-dict data converted to Arrow (raw join/union operands on Ibis, transport preflight, JSON record resources) keeps keys that first appear after the first row; previously Arrow's first-row inference silently dropped them.

## Unreleased — 2026-09-29

### Changed
- Capability information and policy declarations now require explicit applicability; declaration-derived `since` is removed. Explicit unbounded scope remains valid.
- Capability version constraints use standard PEP 440 specifiers and public packaging range APIs (`packaging>=26.3`), replacing raw endpoint and numeric-release matching. Prerelease, local-version and policy-overlap semantics follow packaging.
- Existing capability JSON and Markdown reports include authored applicability. Missing runtime observations remain permissive; test-owned checks reject missing required observations in controlled verification.

## Unreleased — 2026-09-22

### Added
- Version-aware capability applicability: authored finite unions of environment regions with PEP 440 package/interpreter ordering, numeric-release engine ordering, and opaque exact equality; matching is three-valued (applicable / not applicable / indeterminate), and explicitly unconstrained declarations match without acquiring version coordinates.
- Optional stable `variant` qualifier on capability declaration keys with full-identity exact lookup; same-key variants coexist without overwrite, unqualified lookup never falls back to a variant, and declaration history preserves narrowing, splits and merges as immutable captures.
- Shared `CapabilityIssueClass` taxonomy on descriptive information and executable policy rules; information labels are never copied into executable classification.
- Execution policies `CapabilityPolicy.checked()`, `native_debugging()`, and `trusted()` with the request-local `capability_policy()` scope. Runtime consumers — gates, immediate and materialization error enrichment, and result protection — are selected via policy demand; the frozen execution context threads compile → visitor → backend systems, DAG execution freezes the policy at public collect/execute, and validation freezes it at validate entry.
- Opt-in coverage diagnostics exposing applicability and policy selection per record: render CLI `--environment`/`--policy` views with `--output`, and `build_coverage_report(environment=..., policy=...)`. Default coverage artifacts remain unchanged.

### Changed
- Optional protection and enrichment actions run only when the active policy demands them. Trusted execution does not disable required backend conversion, ordinary argument validation, or explicitly requested conformance; unknown version coordinates neither manufacture a policy outcome nor certify support, and native construction observations are never attributed to later Mountainash execution.

## Unreleased — 2026-09-19

### Changed
- Separate descriptive capability information from explicit concrete-dialect protection policies; family descriptions compose with their original identity and provenance, without executable inheritance.
- Move required argument preparation, validation and intrinsic backend refusals into backend implementations, independent of catalogue descriptions and optional protections.
- Publish information and policy atomically; reject ambiguous competing policies instead of resolving them through specificity or registration order.
- Extract capability-owned scenarios and observer bindings into ordinary tests, remove their production schemas and the unused routing-metadata accessor, and migrate coverage/divergence/drift reports to descriptive information and separately owned examples.

### Fixed
- Keep coverage-report source provenance as SHA-256 digests rather than repeatedly embedding complete source files; immutable source captures remain unchanged.

## Unreleased — 2026-09-17

### Changed
- Capability declarations now author semantics only; publication derives current source locations from validated ownership and collection position while retaining immutable source captures.
- Remove the authored `CapabilityAssertion.origins`, `DivergenceManifestation.origins`/`legacy_refs`, `CapabilitySegment.evidence_refs`, and `VerificationBinding.legacy_sites` constructor fields, with no compatibility aliases.
- Remove `LocalOrigin`, `ProbeEvidence` (including its public capability re-export), `AuthoringBundle`, and the packaged retired-declaration archive. Historical sources remain in Git; live probes and genuine evidence/change capture remain supported.
- Remove the coverage report's `bundles` input/field, JSON `historical_bundles` and its stamp count, segment JSON `evidence_refs`, and historical-wave Markdown output. Existing current-data reports remain available; the new auditing/report-to-site integration is separate backlog work.
- Replace the global divergence list and ID-selected test expectations with physically scoped manifestations and exact target/scenario observer bindings. Upstream issue IDs remain explicit metadata joins only.
- Classify operational expectations only during the selected test call; fixture setup, teardown, and unrelated exception failures remain visible.
- Retain independent native construction and selected materialization observations with source, fixture, layer, stage, and environment coordinates; reject reattachment to changed claim payloads.

## Unreleased — 2026-09-15

### Changed
- Upgrade Ruff to 0.16.8, preserving exact-type capability validation and runtime protocol annotation resolution while clearing source lint findings.
- Require Python 3.12 or later and align optional files dependencies with the supported 26.8 release line.
- Restrict source distributions to portable build inputs.
- Replace the legacy release upload path with isolated candidate verification and separately approved PyPI Trusted Publishing of the exact verified artifacts.
- Retain failed candidates for independent same-artifact ARM64 verification without weakening full public-extra or publication gates.
- Run distribution checks automatically only for PRs targeting `main`; retain manually dispatched checks on `develop` without granting publication authority.

### Added
- Installed wheel/sdist and advertised-extra verification, source-provenance checks, Python-policy enforcement, and retained failed verification evidence.
- Documented installed-artifact hello world and explicit unpublished/publication-gated status.
- Add distinct external native-construction targets to the capability schema, with import-safe Ibis DuckDB/SQLite callable authorities, exact dialect qualification, and a dedicated `native_input` declaration home. Construction observations cannot be attributed to later Mountainash execution; divergence classifications and runtime gates are unchanged.

### Fixed
- Restore capability registration for the Substrait rounding family through its explicit `rounding` domain, including option gates and gate-disabled native probes.
- Narrow `IB-DT-09` to non-local `now()` snapshots on Ibis DuckDB/SQLite; retain passing native-Date `today()` coverage and make the remaining expected failures deterministic with a restored, fixed non-UTC test timezone.
- Stabilize the old-log cleanup regression with a fixed same-day cutoff, preventing midnight-dependent SQLite XPASSes while retaining the strict `IB-DT-13` expectation and original result assertions.
- Remove the optional pytest-mock fixture dependency from both fixed-clock log-filtering tests so they execute in the CI test environment.

## Unreleased — 2026-09-14

### Added
- Scalar and fluent `value_kind`, `boolean_value`, and `text_value` primitives for original-domain classification and explicit Boolean/text projection, including heterogeneous object columns.
- Metadata-only, input-scoped compilation for type-sensitive expressions across standalone, relation, conform, and DAG execution. Schema-specialized native expressions must be recompiled for a different input representation.

### Changed
- Require Ibis 11.0.0 or newer.
- Honor explicit `LiteralNode.dtype` during native literal lowering, preserving typed nulls.
- Prepare capability operand-name indexes, operation/backend predicate buckets, and canonical reporting views once per registry publication instead of rediscovering them during scalar compilation.
- Capability registration and initial loading now publish whole batches atomically: a failure retains the previous data, and failed loads keep rethrowing the original exception. Registration rejects mutable payloads, unsupported dataclass subclasses, and noncanonical Enum value domains.
- Registry snapshots are opaque tokens. Recursive public mutations and first-load queries are rejected; each accessor reads one immutable generation, without compilation-wide transactions or cached input descriptors.

These primitives support consumer-owned normalization and whole-input validity checks; they do not implement Rules policy or change ternary semantics.
