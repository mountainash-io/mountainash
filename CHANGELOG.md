# Changelog

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
