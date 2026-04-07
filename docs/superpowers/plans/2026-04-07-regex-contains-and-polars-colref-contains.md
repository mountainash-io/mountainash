# regex_contains + Polars column-reference contains — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `regex_contains` routing through the literal `CONTAINS` function key, and fix Polars `str.contains` with a column-reference pattern so per-row literal contains works natively.

**Architecture:** `regex_contains` is a mountainash API-builder alias. It must route to the existing `FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH` (Substrait `regexp_match_substring`) function key and wrap the result with `.is_not_null()` at the API-builder layer. The `CONTAINS` function key stays literal-only per Substrait spec. For column-reference patterns, the Polars backend is audited against current Polars APIs and switched to the most native path available (preferred: `str.find(...).is_not_null()`; last resort: `str.count_matches(...) > 0`).

**Tech Stack:** Python 3.12, Polars, Ibis, Narwhals, pytest, hatch, uv.

**Spec:** `docs/superpowers/specs/2026-04-07-regex-contains-and-polars-colref-contains-design.md`

---

## Context for the implementer

You are working in `mountainash-expressions`, a three-layer expression system:

1. **Protocol layer** — `src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_string.py` declares the Substrait protocol methods every backend must implement.
2. **API builder layer** — `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py` is the fluent user-facing API. It builds backend-agnostic `ScalarFunctionNode`s keyed on enum members.
3. **Backend layer** — three sibling directories under `src/mountainash/expressions/backends/expression_systems/{polars,ibis,narwhals}/substrait/expsys_{pl,ib,nw}_scalar_string.py` implement each protocol method for that backend.

Function keys are dispatched via `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py` which maps `FKEY_SUBSTRAIT_SCALAR_STRING.*` → Substrait name → protocol method.

**Existing state (verified before writing this plan):**

- `FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH` exists in `enums.py:319` and is wired in `definitions.py:545-550` to protocol method `regexp_match_substring`.
- All three backends already implement `regexp_match_substring`:
  - Polars: `expsys_pl_scalar_string.py:686` uses `input.str.extract(pattern, group_index=0)` which returns matched substring or null.
  - Ibis: `expsys_ib_scalar_string.py:662` uses `input.re_extract(pattern, 0)`.
  - Narwhals: `expsys_nw_scalar_string.py:740`.
- `is_not_null()` is available on `BaseExpressionAPI` via `api_bldr_scalar_comparison.py:297`.
- Current buggy `regex_contains` in `api_bldr_scalar_string.py:1075-1091` emits `FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS` — that is the bug.
- Current Polars `CONTAINS` implementation at `expsys_pl_scalar_string.py:426-430` hardcodes `literal=True`, which is correct per Substrait spec and must NOT be changed.

**Commands you will use repeatedly:**

- Run a single test file: `hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains.py`
- Run a single test: `hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains.py::test_regex_contains_literal_pattern`
- Type check: `hatch run mypy:check`
- Lint: `hatch run ruff:check`

---

## File structure

**Modify:**

- `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py` — rewrite `regex_contains()` body (lines 1075-1091).
- `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py` — `contains()` method (lines 409-430) may switch to `str.find(...).is_not_null()` if investigation confirms colref bug.

**Create:**

- `tests/cross_backend/string/test_regex_contains_refactor.py` — new cross-backend parametrized tests.
- `scripts/debug/polars_contains_colref.py` — throwaway repro (NOT committed; delete after Task 2).

**Possibly update (principles repo, separate commit):**

- `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/e.cross-backend/known-divergences.md` — record Polars `str.contains` colref finding.

---

## Task 1: Failing test for `regex_contains` with literal regex pattern

**Files:**
- Create: `tests/cross_backend/string/test_regex_contains_refactor.py`

- [ ] **Step 1: Check if the test directory exists and find an existing cross-backend string test to mirror its fixture style**

Run:
```bash
ls tests/cross_backend/string/ 2>/dev/null || ls tests/cross_backend/ | head
```

If `tests/cross_backend/string/` does not exist, find the nearest existing cross-backend test with string operations:
```bash
grep -rln "def test_" tests/cross_backend/ | xargs grep -l "regex_contains\|contains" | head -3
```

Read one of those files to understand the parametrization pattern (backend fixture, DataFrame construction, `.compile(df)` usage). You MUST match that style — do not invent a new pattern.

- [ ] **Step 2: Create the new test file**

```python
"""Cross-backend tests for regex_contains refactor.

Covers:
- Literal regex pattern (Bug 1: regex_contains was routing through literal CONTAINS)
- Column-reference regex pattern (per-row pattern)
- Column-reference literal contains (Bug 2: Polars str.contains with colref)
"""
from __future__ import annotations

import pytest

import mountainash as ma


# NOTE: replace `backend_df` fixture usage below with whatever fixture the
# existing cross_backend string tests use. If the existing fixture is named
# `df` or `backend` or `polars_df`, adapt accordingly — do NOT introduce a
# new fixture.


def test_regex_contains_literal_pattern(backend_df):
    """regex_contains with a literal regex string must match via regex, not literal."""
    df = backend_df(
        {
            "s": ["PREFIX_a", "PREFIX_b", "other", "PRE_no_suffix", None],
        }
    )
    result = (
        ma.col("s")
        .regex_contains("^PREFIX_.*")
        .compile(df)
    )
    # Materialize to a list of booleans for comparison
    out = df.select(result.alias("m")).to_series().to_list()
    assert out == [True, True, False, False, None]


def test_regex_contains_column_pattern(backend_df):
    """regex_contains with a per-row pattern column."""
    df = backend_df(
        {
            "s": ["abc123", "xyz", "hello world", "foo"],
            "pat": [r"\d+", r"^x", r"\s", r"^bar"],
        }
    )
    result = (
        ma.col("s")
        .regex_contains(ma.col("pat"))
        .compile(df)
    )
    out = df.select(result.alias("m")).to_series().to_list()
    assert out == [True, True, True, False]


def test_contains_column_pattern(backend_df):
    """Literal contains with a per-row pattern column (Bug 2)."""
    df = backend_df(
        {
            "s": ["apple pie", "banana split", "cherry", "date"],
            "needle": ["pie", "split", "XX", "dat"],
        }
    )
    result = (
        ma.col("s")
        .contains(ma.col("needle"))
        .compile(df)
    )
    out = df.select(result.alias("m")).to_series().to_list()
    assert out == [True, True, False, True]
```

**IMPORTANT:** Before saving, replace `backend_df` with the actual cross-backend fixture from existing tests. If the project uses a parametrized `backend` fixture with per-backend DataFrame constructors, adapt the test functions to match. The three test functions and their assertions MUST remain structurally identical.

- [ ] **Step 3: Run tests to verify they fail (Bug 1 and Bug 2 manifest)**

Run:
```bash
hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains_refactor.py -v
```

Expected: `test_regex_contains_literal_pattern` FAILS on Polars with all-False output (because CONTAINS is literal). The other two tests may fail or error — record which.

Capture the actual output before moving on. If `test_regex_contains_literal_pattern` unexpectedly PASSES on all backends, STOP and report back — the bug may already be fixed or the fixture is misconfigured.

- [ ] **Step 4: Commit the failing tests**

```bash
git add tests/cross_backend/string/test_regex_contains_refactor.py
git commit -m "test: add failing tests for regex_contains and colref contains"
```

---

## Task 2: Verify Polars `str.contains` colref behavior with a repro

**Files:**
- Create (not committed): `scripts/debug/polars_contains_colref.py`

- [ ] **Step 1: Write the repro script**

```python
"""Verify whether polars str.contains evaluates a column-reference pattern per-row.

NOT COMMITTED. Delete after use. See spec:
docs/superpowers/specs/2026-04-07-regex-contains-and-polars-colref-contains-design.md
"""
import polars as pl

df = pl.DataFrame(
    {
        "s": ["apple pie", "banana split", "cherry", "date"],
        "needle": ["pie", "split", "XX", "dat"],
    }
)

print("=== Test A: str.contains with colref, literal=True ===")
try:
    out = df.select(pl.col("s").str.contains(pl.col("needle"), literal=True).alias("m"))
    print(out)
except Exception as e:
    print(f"RAISED: {type(e).__name__}: {e}")

print("\n=== Test B: str.contains with colref, literal=False ===")
try:
    out = df.select(pl.col("s").str.contains(pl.col("needle"), literal=False).alias("m"))
    print(out)
except Exception as e:
    print(f"RAISED: {type(e).__name__}: {e}")

print("\n=== Test C: str.find with colref, then is_not_null ===")
try:
    out = df.select(pl.col("s").str.find(pl.col("needle")).is_not_null().alias("m"))
    print(out)
except Exception as e:
    print(f"RAISED: {type(e).__name__}: {e}")

print("\n=== Test D: str.count_matches with colref, > 0 ===")
try:
    out = df.select((pl.col("s").str.count_matches(pl.col("needle")) > 0).alias("m"))
    print(out)
except Exception as e:
    print(f"RAISED: {type(e).__name__}: {e}")

print("\nExpected row-wise result: [True, True, False, True]")
```

- [ ] **Step 2: Run the repro**

Run:
```bash
uv run python scripts/debug/polars_contains_colref.py
```

Record the output of all four tests. You are looking for:
- Which methods return `[True, True, False, True]` (correct per-row behavior)?
- Which methods return something else (silent wrong behavior) or raise (loud failure)?

- [ ] **Step 3: Choose the Polars implementation path**

Based on the repro, pick in this order of preference:

1. **If Test A or Test B returns correct per-row results** → keep native `str.contains` with the appropriate `literal` flag. The bug was misdiagnosed.
2. **Else if Test C returns correct per-row results** → use `input.str.find(substring).is_not_null()` as the new Polars `contains` implementation. This is the preferred fallback because `find` is already used by `strpos` (line 488) and is lightweight.
3. **Else if Test D returns correct per-row results** → use `input.str.count_matches(substring) > 0` as a last resort.

Write your decision into a comment at the top of Task 4 before starting it. If NONE of the four tests produce correct per-row output, STOP and report back — this indicates a deeper Polars regression.

- [ ] **Step 4: Delete the repro script**

```bash
rm scripts/debug/polars_contains_colref.py
```

Do not commit anything in this task.

---

## Task 3: Fix `regex_contains` routing

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py:1075-1091`

- [ ] **Step 1: Replace the `regex_contains` method body**

Current code (lines 1075-1091):

```python
    def regex_contains(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Check if string contains a match for regex pattern.

        Uses regexp_match_substring under the hood — a non-null result means the pattern matched.
        """
        # Delegate to contains with the pattern — backends handle regex in contains
        pattern_node = self._to_substrait_node(pattern)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            arguments=[self._node, pattern_node],
            options={"case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE"},
        )
        return self._build(node)
```

Replace with:

```python
    def regex_contains(
        self,
        pattern: Union[BaseExpressionAPI, "ExpressionNode", Any],
        case_sensitive: bool = True,
    ) -> BaseExpressionAPI:
        """Check if string contains a match for a regex pattern.

        Routes through REGEXP_MATCH (Substrait regexp_match_substring) and
        checks that the matched substring is non-null. This keeps CONTAINS
        literal per Substrait spec and lets regex_contains reuse the existing
        regex backend implementations.
        """
        pattern_node = self._to_substrait_node(pattern)
        match_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            arguments=[self._node, pattern_node],
            options={
                "case_sensitivity": "CASE_SENSITIVE" if case_sensitive else "CASE_INSENSITIVE",
            },
        )
        return self._build(match_node).is_not_null()
```

- [ ] **Step 2: Run the regex_contains tests**

```bash
hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains_refactor.py::test_regex_contains_literal_pattern -v
hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains_refactor.py::test_regex_contains_column_pattern -v
```

Expected: `test_regex_contains_literal_pattern` PASSES on all three backends. `test_regex_contains_column_pattern` may still fail on Polars if the Polars `regexp_match_substring` implementation (`input.str.extract(pattern, group_index=0)`) has the same colref bug as `str.contains`. If so, note it and proceed — Task 5 will address it.

- [ ] **Step 3: Run the full existing regex_contains / regex_match test suite to catch regressions**

```bash
hatch run test:test-target-quick tests/ -v -k "regex_contains or regex_match"
```

Expected: no regressions. Any previously passing test must still pass. If a test fails because it was asserting the old literal-matching bug, STOP and report back — do NOT modify the existing test.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py
git commit -m "fix: route regex_contains through REGEXP_MATCH, not literal CONTAINS

regex_contains was emitting FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, which
the Polars backend implements with literal=True per Substrait spec. This
caused regex patterns to be matched literally. Route regex_contains
through REGEXP_MATCH (regexp_match_substring) instead and wrap with
.is_not_null() at the API-builder layer."
```

---

## Task 4: Fix Polars `contains` with column-reference pattern

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py:409-430`

> **Implementation path chosen in Task 2 Step 3:** _[fill in with the concrete choice before editing]_

- [ ] **Step 1: Check the current `contains` implementation to decide if a change is needed**

If Task 2 revealed that native `str.contains(..., literal=True)` with a colref DOES work correctly per-row, skip Steps 2-3 of this task and go straight to Step 4 — no code change is needed and the existing implementation is correct.

Otherwise, continue.

- [ ] **Step 2: Replace the `contains` method body**

Current code (lines 409-430):

```python
    def contains(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Whether the input string contains the substring.

        Args:
            input: String expression.
            substring: Substring to search for (expression or literal).
            case_sensitivity: Case sensitivity option.

        Returns:
            Boolean expression.
        """
        return self._call_with_expr_support(
            lambda: input.str.contains(substring, literal=True),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )
```

Replace with ONE of the following based on the Task 2 decision:

**Option 2a (preferred — `str.find(...).is_not_null()`):**

```python
    def contains(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Whether the input string contains the substring (literal match).

        Uses str.find(...).is_not_null() because Polars str.contains does not
        evaluate a column-reference pattern per-row (confirmed via repro
        2026-04-07). str.find works per-row and returns null when absent,
        giving us boolean per-row literal-contains semantics without the
        overhead of str.count_matches.
        """
        return self._call_with_expr_support(
            lambda: input.str.find(substring, literal=True).is_not_null(),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )
```

**Option 2b (last resort — `str.count_matches(...) > 0`):**

```python
    def contains(
        self,
        input: PolarsExpr,
        /,
        substring: PolarsExpr,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Whether the input string contains the substring (literal match).

        Uses str.count_matches(...) > 0 because neither str.contains nor
        str.find accept a column-reference pattern per-row in this Polars
        version (confirmed via repro 2026-04-07). Tracked in
        known-divergences.md.
        """
        return self._call_with_expr_support(
            lambda: input.str.count_matches(substring, literal=True) > 0,
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            substring=substring,
        )
```

Paste only the chosen option. Do not leave both in the file.

- [ ] **Step 3: Run the contains colref test**

```bash
hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains_refactor.py::test_contains_column_pattern -v
```

Expected: PASS on all three backends (Ibis and Narwhals were never buggy, only Polars).

- [ ] **Step 4: Run the full contains test suite to catch regressions**

```bash
hatch run test:test-target-quick tests/ -v -k "contains and not regex"
```

Expected: no regressions.

- [ ] **Step 5: Commit (only if code changed in Step 2)**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py
git commit -m "fix(polars): per-row contains with column-reference pattern

Polars str.contains does not evaluate a column-reference pattern per-row
with literal=True. Switch to [str.find(...).is_not_null() | str.count_matches(...) > 0]
so literal contains works when the needle is drawn from another column."
```

---

## Task 5: Fix Polars `regexp_match_substring` with column-reference pattern (if Task 3 Step 2 revealed it)

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py:686-714`

- [ ] **Step 1: Re-run `test_regex_contains_column_pattern`**

```bash
hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains_refactor.py::test_regex_contains_column_pattern -v
```

If this PASSES on Polars already after Task 3, SKIP this entire task and go straight to Task 6.

If it FAILS on Polars only, continue.

- [ ] **Step 2: Write a small repro for `str.extract` with colref**

```bash
uv run python -c "
import polars as pl
df = pl.DataFrame({'s': ['abc123', 'xyz', 'hello world', 'foo'], 'pat': [r'\d+', r'^x', r'\s', r'^bar']})
try:
    print(df.select(pl.col('s').str.extract(pl.col('pat'), 0).alias('m')))
except Exception as e:
    print(f'RAISED: {type(e).__name__}: {e}')
"
```

Record whether `str.extract` handles a column-reference pattern per-row.

- [ ] **Step 3: Based on the repro, pick an implementation**

- If `str.extract` works per-row: no change needed. Investigate why the test is still failing — might be a null-propagation issue in `.is_not_null()` wrapping. Report back.
- If `str.extract` does NOT work per-row, replace the `regexp_match_substring` method at lines 686-714 with:

```python
    def regexp_match_substring(
        self,
        input: PolarsExpr,
        pattern: PolarsExpr,
        /,
        position: PolarsExpr = None,
        occurrence: PolarsExpr = None,
        group: PolarsExpr = None,
        case_sensitivity: Any = None,
        multiline: Any = None,
        dotall: Any = None,
    ) -> PolarsExpr:
        """Extract substring matching regex pattern.

        Uses map_elements for per-row column-reference patterns because
        Polars str.extract does not evaluate the pattern per-row (confirmed
        via repro 2026-04-07). For literal-pattern cases this still
        short-circuits via the scalar fast path inside _call_with_expr_support.

        Args:
            input: String expression.
            pattern: Regex pattern.
            position: Starting position (ignored in basic impl).
            occurrence: Which occurrence (ignored in basic impl).
            group: Capture group number.
            case_sensitivity: Case sensitivity option.
            multiline: Multiline mode.
            dotall: Dotall mode.

        Returns:
            Matched substring or null.
        """
        import re

        group_index = 0 if group is None else (group if isinstance(group, int) else 0)

        def _extract_row(row: dict[str, Any]) -> str | None:
            s = row["s"]
            p = row["p"]
            if s is None or p is None:
                return None
            m = re.search(p, s)
            if m is None:
                return None
            return m.group(group_index)

        return self._call_with_expr_support(
            lambda: pl.struct([input.alias("s"), pattern.alias("p")]).map_elements(
                _extract_row, return_dtype=pl.String
            ),
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH,
            pattern=pattern,
        )
```

- [ ] **Step 4: Run regex_contains tests**

```bash
hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains_refactor.py -v
```

Expected: all three tests PASS on all three backends.

- [ ] **Step 5: Run the full regex test suite**

```bash
hatch run test:test-target-quick tests/ -v -k "regex"
```

Expected: no regressions.

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py
git commit -m "fix(polars): per-row regexp_match_substring with colref pattern

Polars str.extract does not evaluate a column-reference regex pattern
per-row. Fall back to a struct + map_elements path using the stdlib re
module so regex_contains and friends work with a pattern drawn from
another column."
```

---

## Task 6: Type-check and lint

- [ ] **Step 1: Run mypy**

```bash
hatch run mypy:check
```

Expected: no new errors. If there are pre-existing errors in unrelated files, ignore them. If there are new errors in files you modified, fix them.

- [ ] **Step 2: Run ruff**

```bash
hatch run ruff:check src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_string.py src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py tests/cross_backend/string/test_regex_contains_refactor.py
```

Expected: clean. Auto-fix with `hatch run ruff:fix <same files>` if needed.

- [ ] **Step 3: Commit any lint/type fixes**

```bash
git add -u
git commit -m "style: lint and type fixes for regex_contains refactor" || echo "no changes"
```

---

## Task 7: Run the full test suite

- [ ] **Step 1: Full suite**

```bash
hatch run test:test
```

Expected: all tests pass. Coverage should not drop below its previous level. Any failure that is NOT one of the tests you modified indicates a regression — investigate and fix before moving on.

- [ ] **Step 2: Commit coverage updates if any**

Nothing to commit here normally. Skip if `git status` is clean.

---

## Task 8: Record finding in known-divergences.md (principles repo)

**Files:**
- Modify: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/e.cross-backend/known-divergences.md`

- [ ] **Step 1: Check whether known-divergences.md exists**

```bash
ls /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/e.cross-backend/known-divergences.md
```

If it does not exist, skip this task — it is out of scope for this plan to create the file.

- [ ] **Step 2: Add a new entry**

Append (or insert in the appropriate section) the following entry:

```markdown
### Polars `str.contains` / `str.extract` with column-reference patterns

**Confirmed:** 2026-04-07 (repro at commit [fill in commit hash from Task 4])

**Behavior:** `pl.col("s").str.contains(pl.col("pat"))` and `pl.col("s").str.extract(pl.col("pat"), 0)` do NOT evaluate the pattern per-row. [Exact behavior: record what the repro showed — silently literal? raises? returns wrong shape?]

**Mountainash workaround:** `contains()` uses `str.find(...).is_not_null()`; `regexp_match_substring()` uses `pl.struct([...]).map_elements(...)` with stdlib `re`. See `expsys_pl_scalar_string.py::contains` and `::regexp_match_substring`.

**Ibis and Narwhals:** Not affected — both handle column-reference patterns natively.
```

Fill in the bracketed sections with the actual behavior observed in Task 2 and the commit hash from Task 4.

- [ ] **Step 3: Commit in the principles repo**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expressions/e.cross-backend/known-divergences.md
git commit -m "docs(known-divergences): polars str.contains colref pattern

Record the Polars str.contains / str.extract limitation with
column-reference patterns and the mountainash-expressions workaround."
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions
```

---

## Task 9: Final verification

- [ ] **Step 1: Re-run the new test file one more time**

```bash
hatch run test:test-target-quick tests/cross_backend/string/test_regex_contains_refactor.py -v
```

Expected: 3 tests × 3 backends = 9 test invocations (or however the parametrization produces them), all PASS.

- [ ] **Step 2: Confirm `git status` is clean**

```bash
git status
```

Expected: working tree clean. The spec, the plan, and all implementation commits should be on `develop`.

- [ ] **Step 3: Print summary**

Print a short summary to the terminal describing:
- Which Polars path was chosen in Task 4 (Option 2a or 2b, or "no change needed")
- Whether Task 5 was executed or skipped
- Whether Task 8 (known-divergences) was executed or skipped
- Commit hashes of the fix commits

This is the handoff signal back to the user.
