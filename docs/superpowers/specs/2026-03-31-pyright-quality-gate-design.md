# Pyright Quality Gate

**Date:** 2026-03-31
**Status:** Approved
**Goal:** Establish Pyright as a quality gate for the mountainash project — baseline at `basic` mode, triage all errors, fix bugs, and set up a ratchet mechanism to progressively tighten type checking as architectural improvements land.

## Problem

Pyright is now correctly configured against the project's `.venv` (see `python-environment-setup.md` principle). Running it at the default `standard` mode produces 1,169 errors across 401 files. Most of these are not bugs — they are symptoms of architectural patterns that Pyright cannot resolve (dynamic Ibis APIs, broad type aliases, deliberate operator overrides). The real bugs are buried in the noise.

We need to separate signal from noise, fix the real bugs, and create a sustainable workflow for progressive type safety improvement.

## Approach

This spec covers the diagnostic workflow only — not the architectural improvements that fix the root causes. Each architectural improvement (generic protocols, Ibis type refinement, etc.) will be its own spec.

## 1. Pyright Configuration

Update `pyrightconfig.json` to use `basic` mode:

```json
{
  "venvPath": ".",
  "venv": ".venv",
  "typeCheckingMode": "basic"
}
```

`basic` mode enables a focused set of rules: `reportMissingImports`, `reportUndefinedVariable`, `reportGeneralClassIssues`, and a few others. It filters out the structural noise (`reportAttributeAccessIssue`, `reportOperatorIssue`, `reportIncompatibleMethodOverride`) that are symptoms of the type system architecture, not bugs.

## 2. Baseline and Triage

Run Pyright at `basic` to establish the baseline error count. Categorise every error into one of three buckets:

| Bucket | Action | Example |
|--------|--------|---------|
| **Bug** | Fix immediately | `"fom"` typo in schema_utils.py, undefined `SchemaConfig`, missing `Optional` import |
| **Architecture** | Track as future spec topic | Generic protocols, Ibis type aliases, Polars LazyFrame typing |
| **Suppress** | `# pyright: ignore[rule]` with comment | Deliberate `__eq__` override returning non-bool |

### Triage discipline

- **Suppress is the last resort.** Only for things that are genuinely correct as-is and will not be addressed by an architectural improvement.
- If an error *could* be fixed by better types, it goes in the Architecture bucket — do not suppress it, track it.
- Every suppression comment must explain *why* it is correct.

### Triage output

1. A set of bug fixes (committed directly)
2. A list of architectural improvement topics (each becomes a future spec candidate)
3. A small number of targeted suppressions with explanatory comments

After triage, the project should be at **zero errors on `basic`**.

## 3. Ratchet Mechanism

### Hatch script

Add a Pyright check to hatch environments:

```toml
[tool.hatch.envs.pyright]
dependencies = ["pyright"]

[tool.hatch.envs.pyright.scripts]
check = "pyright src/mountainash/"
```

Run via `hatch run pyright:check`. This is the quality gate — run before committing, alongside `hatch run ruff:check` and `hatch run mypy:check`.

### Ratcheting up

As architectural specs land (generic protocols, Ibis type refinement, etc.), errors at `standard` mode decrease. When a category of errors reaches zero, enable that rule explicitly in `pyrightconfig.json`:

```json
{
  "typeCheckingMode": "basic",
  "reportAttributeAccessIssue": true
}
```

This graduates individual rules from `basic` to `standard` incrementally, locking in gains from each architectural improvement. The end state is full `standard` mode with zero errors.

## 4. Architectural Improvement Tracking

The triage phase will surface architectural topics. Based on initial investigation, the known topics are:

| Topic | Estimated error impact | Description |
|-------|----------------------|-------------|
| Generic protocols (`ExpressionT`) | ~150 `reportIncompatibleMethodOverride` + ~170 `reportArgumentType` | Protocols become `Protocol[ExpressionT]`, backends bind concrete types |
| Ibis type refinement | ~460 `reportAttributeAccessIssue` + `reportOperatorIssue` | Replace broad `IbisExpr` alias with domain-specific Ibis types per backend module |
| Polars LazyFrame typing | ~40 errors in Polars backend | Correct expression vs LazyFrame type distinctions |
| Method redeclaration | ~120 `reportRedeclaration` | Protocol method shadowing in datetime backends |
| Auto-gen protocol imports | ~73 `reportMissingImports` | Auto-generated protocol files have broken relative imports and use `SupportedExpressions = Any` |

Each becomes its own spec. Triage may reveal additional topics.

**This spec does NOT include any of these fixes.** It only establishes the baseline, fixes genuine bugs, and sets up the ratchet.

## Files touched

1. **Modified:** `pyrightconfig.json` (add `typeCheckingMode`)
2. **Modified:** `pyproject.toml` (add `[tool.hatch.envs.pyright]`)
3. **Modified:** Various source files (bug fixes found during triage)
4. **New:** Targeted `# pyright: ignore` comments where suppression is appropriate

## Success criteria

- `hatch run pyright:check` passes with zero errors at `basic` mode
- All genuine bugs found during triage are fixed
- Architectural improvement topics are documented
- No suppression without an explanatory comment
