# Fix: `regex_contains` dispatch + Polars column-reference `contains`

**Date:** 2026-04-07
**Status:** Design approved, pending implementation plan
**Related:** Downstream string-match refactor Tasks 6 (CONTAINS) and 7 (REGEX)

## Problem

Two distinct upstream bugs in `mountainash-expressions` surfaced while refactoring string-match rules in a downstream consumer. Both block that refactor from completing cleanly.

### Bug 1 — `regex_contains` is silently literal

`api_bldr_scalar_string.regex_contains()` emits a `ScalarFunctionNode` keyed on
`FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS`
(`src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py:1075-1091`).

The Polars backend implements `CONTAINS` as
`input.str.contains(substring, literal=True)`
(`src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py:426-430`).

Per the Substrait spec, `contains` is literal-only and `regexp_match_substring` is the regex equivalent. The current wiring conflates two different Substrait operations. This violates `substrait-first-design.md`: a mountainash API alias must not change the semantics of a Substrait function key.

Effect: `col("s").regex_contains("^PRE.*")` is evaluated as "does `s` contain the literal string `^PRE.*`" rather than as a regex match.

### Bug 2 — Polars `str.contains` with a column-reference pattern

When `substring` is a `pl.Expr` (column reference) rather than a Python literal, `input.str.contains(expr, literal=True)` does not appear to evaluate per-row. The implementer of an earlier downstream refactor reported silent literal-string behavior and worked around it with `input.str.count_matches(expr) > 0`. This behavior has not been verified in this repo yet.

Effect: literal-contains against a per-row pattern column is either broken or requires a workaround that counts every occurrence instead of short-circuiting.

## Fix

### Fix 1 — Route `regex_contains` through `regexp_match_substring`

- `api_bldr_scalar_string.regex_contains()` emits a `ScalarFunctionNode` keyed on `FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_SUBSTRING` with the pattern as an argument and `case_sensitivity` as an option.
- The backend implementation of `REGEXP_MATCH_SUBSTRING` returns the matched substring (per Substrait spec). `regex_contains` wraps this with `.is_not_null()` at the API-builder level — one line, keeps backends honest to the spec.
- `CONTAINS` backend implementations remain literal-only, matching Substrait exactly.
- Polars backend gains a `regexp_match_substring` implementation using `input.str.extract(pattern, 0)` or equivalent.
- Ibis backend gains a `regexp_match_substring` implementation using `re_search` / `re_extract`.
- Narwhals backend gains a `regexp_match_substring` implementation using `str.contains(..., literal=False)` wrapped to return a matched substring (or a null-indicator proxy, TBD by the Narwhals API surface).

This choice is per `substrait-first-design.md`: prefer expressing mountainash aliases via Substrait primitives over adding extension function keys.

### Fix 2 — Per-row column-reference `contains` on Polars

Task-ordered:

1. **Verify.** Write a throwaway repro at `scripts/debug/polars_contains_colref.py` (not committed) that exercises `pl.col("s").str.contains(pl.col("pat"), literal=True)` on a 3-row frame with varying patterns. Confirm whether the result is row-wise or all-rows-use-first-pattern.
2. **Investigate native paths.** Consult the Polars corpus and current API. Candidates:
   - `str.contains_any([...])` — takes a literal list, not a column. Not applicable.
   - `str.contains` accepting a `pl.Expr` with `broadcast=False` or equivalent in current Polars.
   - `str.find(pl.col("pat")).is_not_null()` — `find` already works per-row (used by `strpos`, line 488), returns null when not found.
3. **Choose implementation**, in order of preference:
   - **Preferred:** native per-row `str.contains` if any path exists.
   - **Fallback:** `input.str.find(substring).is_not_null()` — avoids the `count_matches` overhead.
   - **Last resort:** `input.str.count_matches(substring) > 0`.
4. **Record finding** in `e.cross-backend/known-divergences.md` (principles repo) regardless of outcome, so the next person does not re-litigate this.

The same investigation applies to the regex variant from Fix 1 when the pattern is a column reference.

## Files affected

- `src/mountainash/expressions/core/expression_system/function_keys/enums.py` — confirm `FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_SUBSTRING` exists; add if missing.
- `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py` — rewrite `regex_contains()` to emit `REGEXP_MATCH_SUBSTRING` and wrap with `.is_not_null()`.
- `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py` — implement `regexp_match_substring`; fix per-row column-reference path for `contains` and the regex variant.
- `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py` — implement `regexp_match_substring` via `re_search` / `re_extract`.
- `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py` — implement `regexp_match_substring` via `str.contains(..., literal=False)` or nearest equivalent.
- `tests/cross_backend/` — new parametrized tests (see Testing).
- Principle doc update: `e.cross-backend/known-divergences.md` in the mountainash-central principles repo.

## Testing

New cross-backend parametrized tests (all three backends: Polars, Ibis, Narwhals):

- `test_regex_contains_literal_pattern` — e.g. `col("s").regex_contains("^PRE.*")` against a frame of strings, some matching.
- `test_regex_contains_column_pattern` — pattern drawn from another column, one pattern per row.
- `test_contains_column_pattern` — literal contains, column-reference substring.
- Existing `contains` and `regex_contains` tests must still pass unchanged.

Per `testing-philosophy.md`: no `skip` or `xfail` unless a genuine backend quirk is documented in `known-divergences.md`.

## Out of scope

- Rewriting `regex_match` — it already delegates to `regex_contains` with anchoring, so the fix flows through automatically.
- Touching `like`, `regexp_replace`, `regexp_strpos`, or other regex operations. If they share the same bug class, that is separate work.
- Refactoring the downstream consumer's Tasks 6 and 7 — that happens in the consumer repo once this upstream fix lands.

## Open questions

None — all resolved during brainstorming. Function-key naming settled on option A (route through `REGEXP_MATCH_SUBSTRING`).
