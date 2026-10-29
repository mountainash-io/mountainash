# Upstream Issues Registry

Canonical operational registry of upstream (polars / ibis / narwhals) issues
affecting mountainash. Moved from mountainash-central 2026-07 (capability-spine
Phase 2): code + metadata now land atomically and CI validates the join.

## Join contract (typed, bidirectional)

- Code (`CapabilityFact.upstream_ref` / `DivergenceFact.upstream_ref`, xfail
  helpers) references entries **by `id`** (grammar `PROJ-CAT-NN`).
- This file holds lifecycle only: status, GitHub URL, last_verified.
- CI (`tests/core/test_upstream_registry_join.py`) fails on: a code ref with no
  YAML entry; a YAML entry with neither code references nor a
  zero-reference-allowed status.
- Legacy `xfail_refs` / `known_expr_limitations` heuristic fields are gone —
  do not reintroduce them.

## Tooling

- `python scripts/validate_upstream_registry.py` — schema validation
- `python scripts/audit_upstream_issues.py` — GitHub state sync + discovery
