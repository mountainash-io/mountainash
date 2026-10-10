# Changelog

## Unreleased — 2026-10-10

### Added
- `ma.DecimalDtype(precision, scale)`, an exact decimal descriptor, with `.cast(DecimalDtype(...), rounding=...)` for native conversion on Polars, Polars-lazy, Ibis-DuckDB and Ibis-Polars with identical results, and `ma.lit(value, dtype=...)` for typed literals. `rounding=` takes `"half_to_even"`, `"half_away_from_zero"` or `"to_zero"` and is required for decimal targets. Integer-part overflow always raises; invalid text raises or becomes null per `failure_behavior`. The Narwhals-based backends and SQLite refuse with a declared `BackendCapabilityError` (Narwhals #3698/#3702). See [Exact decimals](docs/website/features-technical/typespec-conform.md#exact-decimals) for the three documented edge-case limits (241).
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
