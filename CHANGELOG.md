# Changelog

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
