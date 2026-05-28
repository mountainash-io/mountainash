# Known Divergences — Reading the Catalog

The full catalog lives in [`docs/known-divergences.md`](../known-divergences.md). It is **auto-generated** from a YAML registry by `scripts/generate_divergences_catalog.py`. Do not edit it by hand — your changes will be overwritten.

This guide explains what the catalog contains, how to use it, and how to file new entries.

## What's in the catalog

Each entry documents one place where a backend's behaviour intentionally diverges from mountainash's logical contract. Entries are categorised:

- **String Operations** — pad/trim/replace/regex/repeat behaviour
- **Datetime Operations** — interval semantics, parameter-width restrictions, SQLite type gaps
- **Math Operations** — overflow, NaN, integer division, modulo sign, precision
- **Type System** — cast/coerce surprises, inference gaps
- **Relational Operations** — join semantics, sort/fetch edge cases
- **Aggregate Operations** — null handling, dispersion, weighted aggregates
- **Window Operations** — `.over()` frame bounds, cumulative semantics, rank variants
- **List Operations** — set ops on lists, diff/shift, explode/concat
- **Cast Semantics** — string ↔ number ↔ datetime coercion differences
- **Interval Operations** — calendar vs duration intervals
- **Recursive CTEs** — backends without recursive query support
- **Internal Wiring Gaps** — places where the AST has a slot but no backend implements it yet

Total: 94 entries as of the last regeneration (2026-05-17).

## How an entry is structured

Each entry has:

| Field | Meaning |
|-------|---------|
| **ID** | Stable identifier. Prefix encodes the backend group: `IB-` Ibis, `NW-` Narwhals, `PL-` Polars. Suffix is the category (`STR`, `DT`, `MATH`, …). |
| **Summary** | One-line description of the divergence. |
| **Backends** | Specific backends affected. `ibis-duckdb`, `ibis-polars`, `ibis-sqlite`, `narwhals-pandas`, `narwhals-polars`, `polars`. |
| **Root Cause** | One of: `upstream_bug`, `upstream_feature_gap`, `parameter_width`, `by_design`. |
| **Workaround** | What mountainash does in practice: `Strict xfail` (the test fails on that backend by design), `Enhanced error message` (the call raises with guidance), or `Accepted (documented)` (no workaround; behaviour is documented). |
| **Status** | `Open`, `Investigating`, `Needs Filing`, `By Design`, `Closed`. |

## Root-cause taxonomy

| Code | When to use it |
|------|----------------|
| `upstream_bug` | The upstream library does something we think is incorrect; we expect them to fix it. |
| `upstream_feature_gap` | The upstream library doesn't yet support the operation; we'd accept their implementation when shipped. |
| `parameter_width` | The upstream library only accepts a narrower argument shape than mountainash's protocol (typically: literal where we'd allow an expression). The KNOWN_EXPR_LIMITATIONS registry hooks here so we can emit a better error. |
| `by_design` | The upstream library deliberately diverges and we are accepting it (e.g. SQLite has no datetime type — that's never going to change). |

## How an entry maps to test code

Most entries correspond to a `pytest.mark.xfail(..., strict=True, reason="…")` somewhere under `tests/`. The reason string usually quotes the divergence ID. Search for the ID:

```bash
rg "IB-STR-04" tests/
```

For `parameter_width` entries, the corresponding `KNOWN_EXPR_LIMITATIONS` registry entry lives under `src/mountainash/expressions/.../known_limitations.py` (or the relations equivalent). The runtime uses this to upgrade the raw upstream error into a friendlier mountainash error.

For `by_design` entries, there is no `xfail` — the behaviour is documented and tests assert it works the divergent way.

## How to file a new entry

1. Discover the divergence (usually a test failure or a user bug report).
2. Identify the root cause and which backend(s) are affected.
3. Pick the next free ID in the relevant category.
4. Add it to the YAML registry under `scripts/upstream_issues/` (or the local registry that the generator reads — check `generate_divergences_catalog.py` for the input path).
5. Add a strict `xfail` (or `KNOWN_EXPR_LIMITATIONS` entry) in the test that references the ID in its `reason=`.
6. Regenerate the catalog:

   ```bash
   python scripts/generate_divergences_catalog.py
   ```

7. If the divergence is `upstream_bug` or `upstream_feature_gap`, file an issue upstream and link it in the registry entry.

## How to close an entry

When the upstream fix lands:

1. Remove the `xfail` (the test should now pass).
2. Update the registry entry to `status: Closed` with the date and the upstream commit/PR link.
3. Regenerate the catalog.
4. Optionally run the upstream-fix-monitoring audit:

   ```bash
   python scripts/audit_upstream_issues.py --report-file scripts/outputs/reconciliation-report.md
   ```

   This cross-references xfails with registry entries and surfaces drift.

Principle: `e.cross-backend/upstream-fix-monitoring.md`.

## Maintenance commands

```bash
# Regenerate catalog
python scripts/generate_divergences_catalog.py

# Validate registry schema
python scripts/validate_upstream_registry.py

# Full audit (local + GitHub upstream issue cross-check)
python scripts/audit_upstream_issues.py --report-file scripts/outputs/reconciliation-report.md

# Local cross-reference only (no GitHub network calls)
python scripts/audit_upstream_issues.py --skip-github

# Drift-guard xfail report
python scripts/report_drift_guards.py
python scripts/report_drift_guards.py --report-file scripts/outputs/drift-guards-report.md
```

## CI behaviour

The strict-xfail policy means: an `xfail` test that **passes** fails the build. This is intentional — when an upstream fix lands, we want to know immediately so we can:

1. Close the divergence entry.
2. Remove the xfail.
3. Possibly remove the registry entry from `KNOWN_EXPR_LIMITATIONS` if applicable.

If you ever see a strict-xfail surprise failure, check the corresponding catalog entry first — the upstream fix has probably shipped.

## What's *not* in the catalog

- **Bugs in mountainash itself.** Those are GitHub issues, not divergences.
- **Performance differences between backends.** Only correctness divergences are tracked.
- **Mountainash extension ops not yet implemented on a backend.** Those are `Internal Wiring Gaps` — already a category, but reserve it for slots in the AST that have a protocol method and no implementation, not for "we haven't designed the op yet."

## Related documents

- The catalog itself: [../known-divergences.md](../known-divergences.md)
- Backend architecture: [backend-architecture.md](backend-architecture.md)
- Principles: `e.cross-backend/known-divergences.md`, `e.cross-backend/upstream-fix-monitoring.md`, `e.cross-backend/consistency-guarantees.md`
