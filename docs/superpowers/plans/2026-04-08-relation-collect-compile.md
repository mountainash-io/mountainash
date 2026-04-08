# Relation `collect()` / `compile()` Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Relation.collect()` always return a materialized backend result (fixing the `rel.collect().collect()` hazard on Polars LazyFrame sources) and add a symmetric `Relation.compile()` that returns the native plan unexecuted.

**Architecture:** Local change to `Relation` public terminals. `compile()` exposes the existing `_compile_and_execute()` return value unchanged. `collect()` calls `compile()` then materializes any Polars LazyFrame via its own `.collect()`. `to_polars()` routes through `collect()` instead of duplicating the materialization guard. No visitor, node, backend, or DAG changes.

**Tech Stack:** Python 3.10+, Polars (lazy + eager), narwhals, Ibis, pytest, hatch.

**Spec:** `docs/superpowers/specs/2026-04-08-relation-collect-compile-design.md`

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `src/mountainash/relations/core/relation_api/relation.py` | `Relation` public terminals | Modify `collect()`, add `compile()`, simplify `to_polars()` |
| `tests/relations/test_terminal_collect_compile.py` | Contract tests for `collect()` / `compile()` across backends | Create |
| `../mountainash-central/01.principles/mountainash-expressions/c.api-design/build-then-collect.md` | API-design principle | Modify — add `compile()`/`collect()` paragraph |

---

## Task 1: Write failing contract test for `collect()` on Polars LazyFrame (the regression guard)

**Files:**
- Create: `tests/relations/test_terminal_collect_compile.py`

- [ ] **Step 1: Create the new test file with the regression-guard test**

```python
"""Cross-backend contract tests for Relation.collect() and Relation.compile().

collect() MUST return a materialized native result for every backend.
compile() MUST return the native plan (lazy where the backend is lazy).
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.relations import relation


def test_collect_polars_lazyframe_returns_dataframe():
    """Regression guard: collect() on a LazyFrame source must NOT return a LazyFrame.

    Before this fix, `rel.collect()` leaked the LazyFrame and callers had to
    do `rel.collect().collect()`. That broke the one-syntax-all-backends promise.
    """
    lf = pl.DataFrame({"x": [1, 2, 3]}).lazy()
    result = relation(lf).collect()
    assert isinstance(result, pl.DataFrame)
    assert not isinstance(result, pl.LazyFrame)
    assert result.to_dicts() == [{"x": 1}, {"x": 2}, {"x": 3}]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `hatch run test:test-target-quick tests/relations/test_terminal_collect_compile.py::test_collect_polars_lazyframe_returns_dataframe`

Expected: FAIL — the assertion `assert isinstance(result, pl.DataFrame)` fails because `result` is a `pl.LazyFrame`.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/relations/test_terminal_collect_compile.py
git commit -m "test(relations): add regression guard for collect() on LazyFrame"
```

---

## Task 2: Implement `compile()` and fix `collect()` to materialize

**Files:**
- Modify: `src/mountainash/relations/core/relation_api/relation.py:381-383` (`collect()`)
- Modify: `src/mountainash/relations/core/relation_api/relation.py:517-528` (`to_polars()`)

- [ ] **Step 1: Replace `collect()` and add `compile()`**

In `src/mountainash/relations/core/relation_api/relation.py`, replace the current `collect()` method (currently at line 381):

```python
    def collect(self) -> Any:
        """Execute the plan and return the native backend result."""
        return self._compile_and_execute()
```

with the following two methods:

```python
    def compile(self) -> Any:
        """Compile to a native backend plan without materializing.

        For lazy backends (Polars ``LazyFrame``, Ibis) this returns the
        unexecuted plan — use it as an escape hatch to interleave native
        ops before calling :meth:`collect`. For eager backends the result
        is already materialized and :meth:`collect` is a no-op over it.

        Symmetric with the expressions-side ``expr.compile(df)``.
        """
        return self._compile_and_execute()

    def collect(self) -> Any:
        """Execute the plan and return a fully materialized native result.

        Always eager: a Polars ``LazyFrame`` source returns a ``DataFrame``,
        an Ibis expression returns an executed result, narwhals returns its
        native frame, and so on. One syntax for all backends.
        """
        from mountainash.core.types import is_polars_lazyframe

        result = self.compile()
        if is_polars_lazyframe(result):
            return result.collect()
        return result
```

- [ ] **Step 2: Simplify `to_polars()` to route through `collect()`**

Replace the current `to_polars()` method (currently at line 517):

```python
    def to_polars(self) -> Any:
        """Execute and return a Polars DataFrame."""
        from mountainash.core.types import is_polars_dataframe, is_polars_lazyframe

        result = self._compile_and_execute()
        if is_polars_dataframe(result):
            return result
        if is_polars_lazyframe(result):
            return result.collect()
        # Fallback for other backends
        import polars as pl
        return pl.from_pandas(result.to_pandas())
```

with:

```python
    def to_polars(self) -> Any:
        """Execute and return a Polars DataFrame."""
        from mountainash.core.types import is_polars_dataframe

        result = self.collect()
        if is_polars_dataframe(result):
            return result
        # Fallback for other backends (Ibis, narwhals, pandas)
        import polars as pl
        return pl.from_pandas(result.to_pandas())
```

- [ ] **Step 3: Run the regression guard test to verify it passes**

Run: `hatch run test:test-target-quick tests/relations/test_terminal_collect_compile.py::test_collect_polars_lazyframe_returns_dataframe`

Expected: PASS.

- [ ] **Step 4: Run the full relations test suite to confirm nothing regressed**

Run: `hatch run test:test-target-quick tests/relations/`

Expected: all tests pass. Pay particular attention to `test_terminal_count_rows.py`, `test_terminal_item.py`, `test_terminal_scalar_aggregates.py` — these route through `to_polars()` and `item()`, which now go via `collect()`.

- [ ] **Step 5: Commit the fix**

```bash
git add src/mountainash/relations/core/relation_api/relation.py
git commit -m "fix(relations): collect() always materializes; add compile()

collect() on a Polars LazyFrame source previously returned the
LazyFrame, forcing callers into rel.collect().collect() — a breakage
of the one-syntax-all-backends contract. collect() now materializes
LazyFrames before returning.

compile() is added as the symmetric escape hatch: returns the native
plan unexecuted, pairing with the expressions-side expr.compile(df).

to_polars() is simplified to route through collect()."
```

---

## Task 3: Expand contract tests across all backends

**Files:**
- Modify: `tests/relations/test_terminal_collect_compile.py`

- [ ] **Step 1: Add the full cross-backend contract test suite**

Append the following to `tests/relations/test_terminal_collect_compile.py` (after the regression-guard test from Task 1):

```python
# ----------------------------------------------------------------------
# collect() — always materialized
# ----------------------------------------------------------------------


def test_collect_polars_eager_returns_dataframe():
    df = pl.DataFrame({"x": [1, 2, 3]})
    result = relation(df).collect()
    assert isinstance(result, pl.DataFrame)
    assert result.to_dicts() == [{"x": 1}, {"x": 2}, {"x": 3}]


def test_collect_narwhals_polars_returns_native():
    pytest.importorskip("narwhals")
    import narwhals as nw

    nw_df = nw.from_native(pl.DataFrame({"x": [1, 2, 3]}), eager_only=True)
    result = relation(nw_df).collect()
    # Must not be a Polars LazyFrame under any circumstances
    assert not isinstance(result, pl.LazyFrame)


def test_collect_narwhals_pandas_returns_native():
    pytest.importorskip("narwhals")
    pytest.importorskip("pandas")
    import narwhals as nw
    import pandas as pd

    nw_df = nw.from_native(pd.DataFrame({"x": [1, 2, 3]}), eager_only=True)
    result = relation(nw_df).collect()
    assert not isinstance(result, pl.LazyFrame)


def test_collect_ibis_returns_materialized():
    pytest.importorskip("ibis")
    import ibis

    t = ibis.memtable({"x": [1, 2, 3]})
    result = relation(t).collect()
    # Ibis backends already return materialized frames from the visitor;
    # the critical invariant is that it is NOT a Polars LazyFrame and
    # NOT an unexecuted ibis.Table.
    assert not isinstance(result, pl.LazyFrame)
    assert not isinstance(result, ibis.Table)


# ----------------------------------------------------------------------
# compile() — native plan, lazy where the backend is lazy
# ----------------------------------------------------------------------


def test_compile_polars_lazyframe_returns_lazyframe():
    """compile() preserves laziness — this is the escape-hatch contract."""
    lf = pl.DataFrame({"x": [1, 2, 3]}).lazy()
    plan = relation(lf).compile()
    assert isinstance(plan, pl.LazyFrame)
    # And it is a real, executable plan
    assert plan.collect().to_dicts() == [{"x": 1}, {"x": 2}, {"x": 3}]


def test_compile_polars_eager_returns_dataframe():
    """Eager source has nothing to defer — compile() returns the DataFrame."""
    df = pl.DataFrame({"x": [1, 2, 3]})
    plan = relation(df).compile()
    assert isinstance(plan, pl.DataFrame)


def test_compile_ibis_returns_unexecuted_table():
    pytest.importorskip("ibis")
    import ibis

    t = ibis.memtable({"x": [1, 2, 3]})
    plan = relation(t).compile()
    assert isinstance(plan, ibis.Table)


# ----------------------------------------------------------------------
# Round-trip: collect() equals manually materialized compile()
# ----------------------------------------------------------------------


def test_collect_equals_manual_compile_then_collect_polars_lazy():
    lf = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]}).lazy()
    rel = relation(lf)

    via_collect = rel.collect()
    via_compile = rel.compile().collect()

    assert via_collect.to_dicts() == via_compile.to_dicts()


def test_collect_equals_compile_polars_eager():
    df = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
    rel = relation(df)

    via_collect = rel.collect()
    via_compile = rel.compile()  # eager — no extra step needed

    assert via_collect.to_dicts() == via_compile.to_dicts()
```

- [ ] **Step 2: Run the expanded suite**

Run: `hatch run test:test-target-quick tests/relations/test_terminal_collect_compile.py`

Expected: all tests pass across Polars eager, Polars lazy, narwhals-polars, narwhals-pandas, and Ibis.

- [ ] **Step 3: Commit the test expansion**

```bash
git add tests/relations/test_terminal_collect_compile.py
git commit -m "test(relations): cross-backend contract for collect()/compile()"
```

---

## Task 4: Update the `build-then-collect` principle

**Files:**
- Modify: `../mountainash-central/01.principles/mountainash-expressions/c.api-design/build-then-collect.md`

- [ ] **Step 1: Read the current principle document**

Read `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expressions/c.api-design/build-then-collect.md` to find the best location for the new paragraph — look for the section that enumerates terminal methods (`to_polars`, `to_pandas`, `collect`, etc.) or the closest equivalent.

- [ ] **Step 2: Add the `compile()` / `collect()` paragraph**

Insert the following paragraph near where the terminal methods are described (or append as a new `### collect() vs compile()` subsection if no clear insertion point exists):

```markdown
### `collect()` vs `compile()`

The relations API exposes a symmetric pair of terminals that mirror the
expressions-side `build-then-compile` principle:

- **`rel.collect()`** — fully materialized native result. Always eager.
  A Polars `LazyFrame` source returns a `DataFrame`, Ibis returns an
  executed frame, narwhals returns its native eager frame. This is the
  default "give me the data" terminal and is guaranteed consistent across
  every registered backend.
- **`rel.compile()`** — native backend plan, lazy where the backend is
  lazy. Returns a `pl.LazyFrame` for lazy Polars sources, an unexecuted
  `ibis.Table` for Ibis, and the native frame for eager backends. Use it
  as an escape hatch when you need to interleave backend-specific ops
  before materializing.

Never call `rel.collect().collect()` — if you find yourself reaching for
that, you want `rel.compile().collect()` (escape hatch) or just
`rel.collect()` (the common case).
```

- [ ] **Step 3: Commit the principle update**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expressions/c.api-design/build-then-collect.md
git commit -m "docs(principles): document relation collect()/compile() pair"
cd -
```

(Push to central is out of scope — batch it with the next central push.)

---

## Task 5: Final full-suite verification

**Files:** none

- [ ] **Step 1: Run the full test suite (no coverage, for speed)**

Run: `hatch run test:test-quick`

Expected: all tests pass. The change is local to `Relation` terminals; no other subsystem should be affected.

- [ ] **Step 2: Run pyright on the modified file**

Run: `hatch run mypy:check` (or rely on the editor LSP diagnostics on `relation.py`).

Expected: no new errors introduced by the change. The only touch is `relation.py`, which already imported the relevant type guards lazily inside each method.

- [ ] **Step 3: If everything passes, the implementation is complete.**

No further commit needed — all commits were made per-task.
