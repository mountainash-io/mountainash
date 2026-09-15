# Changelog

## Unreleased — 2026-09-15

### Changed
- Require Python 3.12 or later and align optional files dependencies with the supported 26.8 release line.
- Restrict source distributions to portable build inputs.
- Replace the legacy release upload path with isolated candidate verification and separately approved PyPI Trusted Publishing of the exact verified artifacts.

### Added
- Installed wheel/sdist and advertised-extra verification, source-provenance checks, Python-policy enforcement, and retained failed verification evidence.
- Documented installed-artifact hello world and explicit unpublished/publication-gated status.

## Unreleased — 2026-09-14

### Added
- Scalar and fluent `value_kind`, `boolean_value`, and `text_value` primitives for original-domain classification and explicit Boolean/text projection, including heterogeneous object columns.
- Metadata-only, input-scoped compilation for type-sensitive expressions across standalone, relation, conform, and DAG execution. Schema-specialized native expressions must be recompiled for a different input representation.

### Changed
- Require Ibis 11.0.0 or newer.
- Honor explicit `LiteralNode.dtype` during native literal lowering, preserving typed nulls.

These primitives support consumer-owned normalization and whole-input validity checks; they do not implement Rules policy or change ternary semantics.
