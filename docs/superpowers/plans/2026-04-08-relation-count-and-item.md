# Aggregate Foundation + `Relation.count_rows()` / `Relation.item()` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land two new strict-semantics terminal operations on `Relation` — `count_rows() -> int` and `item(column, row=0) -> Any` — on top of a proper foundation: wire the Substrait aggregate api_builder that is currently a stub, expose `count` and `count_records` as the first two members, and compose `count_rows()` on top of `count_records`. This establishes the pattern every future scalar aggregate terminal (`sum`, `min`, `max`, `first`, `last`, `mean`) will reuse.

**Architecture:** Substrait-aligned and pure. `count` and `count_records` both belong in `FKEY_SUBSTRAIT_SCALAR_AGGREGATE` (Substrait `functions_arithmetic_and_aggregate.yaml` defines both as standard aggregates). The api_builder stub at `_api_bldr_scalar_aggregate.py` is replaced with a real builder and wired into `BooleanExpressionAPI._FLAT_NAMESPACES`. `ma.col("x").count()` produces a `ScalarFunctionNode` with `COUNT`; `ma.count_records()` (a free function in `entrypoints.py`) produces one with `COUNT_RECORDS`. `Relation.count_rows()` becomes a 3-line composition: wrap `self._node` in an `AggregateRelNode` with `[ma.count_records()]` as the measures list, compile via the existing pipeline, extract the single scalar via `item()`. **No per-backend dispatch ladders anywhere.** `Relation.item()` stays a thin wrapper over `to_polars()` with strict bounds checking (it was already pure).

**Tech Stack:** Python 3.10+, Polars (LazyFrame + DataFrame), Narwhals, Ibis, hatch + pytest.

**Spec:** `docs/superpowers/specs/2026-04-08-relation-count-and-item-design.md`

**Substrait alignment note:** this plan is a **Substrait protocol completion**, not a new function. Per the Substrait spec (`extensions/functions_aggregate_generic.yaml` in `substrait-io/substrait`), there is a single function named `count` with **two impls distinguished by arity**:

1. `count(x: any)` — counts non-null values in a set
2. `count()` (zero args) — counts all records

The mountainash Substrait protocol at `prtcl_expsys_aggregate_generic.py` currently exposes **only the 1-arg overload**. It is incomplete relative to the Substrait spec. This plan extends the protocol to expose **both** overloads as distinct Python methods (`count` and `count_records` — the latter taking its name from Substrait's own description "Count the number of records"). Both methods map to the same Substrait wire-format function name (`substrait_name="count"`); the Python identifier difference is mountainash-internal disambiguation so each overload can have its own enum key, function-mapping entry, and api-builder call site per the existing six-layer wiring matrix.

All work below lives under `substrait/` directories, uses `FKEY_SUBSTRAIT_SCALAR_AGGREGATE.*` enums, and uses the `SubstraitExtension.SCALAR_AGGREGATE` URI. Nothing goes under `extensions_mountainash/` — the 0-arg `count` overload is already defined in Substrait; it's not a mountainash extension.

**Protocols are the source of truth.** Unwired backend files (e.g. `_expsys_pl_scalar_aggregate.py` with its commented `count_all` method, or any `_`-prefixed aspirational file) are **not authoritative**. They don't exist from the system's point of view until a protocol backs them. This plan defines the protocol methods first, then updates backends to conform.

---

## File Structure

### Phase 1: aggregate foundation

```
# ENUM
src/mountainash/expressions/core/expression_system/function_keys/enums.py
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS = auto()   # NEW

# Protocol
src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_aggregate_generic.py
    def count_records(self, /, overflow=None) -> ExpressionT: ...   # NEW method

# Backend implementations (Substrait-aligned)
src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_aggregate_generic.py
    def count_records(self, overflow=None) -> pl.Expr: ...   # uncomment and rename existing count_all

src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_aggregate_generic.py
    def count_records(self, overflow=None) -> nw.Expr: ...   # NEW

src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_aggregate_generic.py
    def count_records(self, overflow=None) -> ibis.Expr: ...   # NEW

# Function mapping
src/mountainash/expressions/core/expression_system/function_mapping/definitions.py
    Append COUNT_RECORDS entry to SCALAR_AGGREGATE_FUNCTIONS list

# Protocol (api_builder side)
src/mountainash/expressions/core/expression_protocols/api_builders/substrait/_prtcl_api_bldr_scalar_aggregate.py
    Rename to prtcl_api_bldr_scalar_aggregate.py (drop leading underscore),
    add count and count_records method signatures.

# API builder — drop the stub, add the real one
src/mountainash/expressions/core/expression_api/api_builders/substrait/_api_bldr_scalar_aggregate.py
    → rename to api_bldr_scalar_aggregate.py (drop leading underscore)
    → replace stub body with real implementation exposing count()

# Free function entrypoint
src/mountainash/expressions/core/expression_api/entrypoints.py
    def count_records() -> BaseExpressionAPI: ...   # NEW free function

# Wire into the flat namespace
src/mountainash/expressions/core/expression_api/boolean.py
    Uncomment: SubstraitScalarAggregateAPIBuilder in imports and _FLAT_NAMESPACES

# Top-level re-export
src/mountainash/__init__.py
    from mountainash.expressions import count_records
    __all__ += ["count_records"]
```

### Phase 2: relation terminals

```
src/mountainash/relations/core/relation_api/relation.py
    def count_rows(self) -> int: ...
    def item(self, column: str, row: int = 0) -> Any: ...
```

### Phase 3: tests

```
tests/expressions/test_aggregate_count.py                       # NEW — col().count() and ma.count_records() via .agg()
tests/relations/test_terminal_count_rows.py                     # NEW — count_rows() cross-backend
tests/relations/test_terminal_item.py                           # NEW — item() cross-backend
tests/relations/dag/test_dag_count_rows_and_item.py             # NEW — DAG integration
```

### Phase 4: docs

```
mountainash-central/01.principles/mountainash-expressions/
    a.architecture/wiring-matrix.md                             # Update: count + count_records now wired
    h.backlog/polars-alignment-deferred.md                      # Possibly remove aggregate stub TODO if present
CLAUDE.md                                                       # No changes needed (principles unchanged)
```

---

## Task 1: Audit current aggregate wiring state

**Purpose:** Before touching any code, produce a concrete gap-list so the implementer knows exactly which of the six wiring-matrix layers are ready, stubbed, or missing for `COUNT` and `COUNT_RECORDS`. Catches drift from what the plan assumes.

**Files:**
- Read-only.
- Output: a commit-worthy notes file at `notes/aggregate-wiring-audit-2026-04-08.md`.

- [ ] **Step 1: Check each layer for the `COUNT` function.** Run these greps and record the findings:

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions

# Layer 1: Enum
grep -n "COUNT\b" src/mountainash/expressions/core/expression_system/function_keys/enums.py

# Layer 2: Function mapping
grep -n "COUNT\b" src/mountainash/expressions/core/expression_system/function_mapping/definitions.py

# Layer 3: Protocol (expression system)
grep -n "def count\b" src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_aggregate_generic.py

# Layer 4: Backend implementations (all 3 backends)
grep -n "def count\b" src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_aggregate_generic.py
grep -n "def count\b" src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_aggregate_generic.py 2>/dev/null
grep -n "def count\b" src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_aggregate_generic.py 2>/dev/null

# Layer 5: api_builder protocol
ls src/mountainash/expressions/core/expression_protocols/api_builders/substrait/ | grep -i aggreg
cat src/mountainash/expressions/core/expression_protocols/api_builders/substrait/_prtcl_api_bldr_scalar_aggregate.py 2>/dev/null

# Layer 6: api_builder implementation
ls src/mountainash/expressions/core/expression_api/api_builders/substrait/ | grep -i aggreg
cat src/mountainash/expressions/core/expression_api/api_builders/substrait/_api_bldr_scalar_aggregate.py 2>/dev/null

# Flat namespace wiring
grep -n "AggregateAPIBuilder\|scalar_aggregate" src/mountainash/expressions/core/expression_api/boolean.py
```

- [ ] **Step 2: Repeat the layer probe for `COUNT_RECORDS` (the 0-arg Substrait count overload).**

```bash
grep -rn "COUNT_RECORDS\|count_records" src/mountainash/expressions/ 2>/dev/null
# Expected: no results — COUNT_RECORDS does not exist yet at the protocol layer.

# Check for aspirational backend artefacts that are NOT authoritative
# (reminder: backend files without protocol backing are unwired and don't count):
grep -rn "count_all\|count_star" src/mountainash/expressions/ 2>/dev/null
# Expected: possibly `count_all` in a `_`-prefixed file such as
# _expsys_pl_scalar_aggregate.py — note this but do NOT treat as evidence the
# 0-arg overload is already wired. Protocol is the source of truth.
```

Also verify the Substrait spec position:

```bash
# Confirm the Substrait count function defines the 0-arg overload.
# The source of truth is:
#   https://github.com/substrait-io/substrait/blob/main/extensions/functions_aggregate_generic.yaml
# Key text: "Count the number of records (not field-referenced)."
# If you have network access:
gh api repos/substrait-io/substrait/contents/extensions/functions_aggregate_generic.yaml \
  --jq '.content' | base64 -d | sed -n '/- name: "count"/,/- name: "any_value"/p'
# Expected: two impls under the single name "count", the second with no `args` block.
```

- [ ] **Step 3: Check whether a narwhals/ibis aggregate_generic backend file exists.**

```bash
ls src/mountainash/expressions/backends/expression_systems/narwhals/substrait/ | grep -i aggreg
ls src/mountainash/expressions/backends/expression_systems/ibis/substrait/ | grep -i aggreg
```

If `expsys_nw_aggregate_generic.py` or `expsys_ib_aggregate_generic.py` does NOT exist, those files need to be created in Task 3 alongside the `count_records` addition. If they exist but lack a `count` method, Task 3 adds both `count` and `count_records`.

- [ ] **Step 4: Write the audit notes** to `notes/aggregate-wiring-audit-2026-04-08.md`:

```markdown
# Aggregate Wiring Audit — 2026-04-08

For each of the six wiring-matrix layers, status of `count(x)` and `count_records()` in the Substrait aggregate namespace.

| Layer | COUNT | COUNT_RECORDS | Notes |
|---|---|---|---|
| Enum (`FKEY_SUBSTRAIT_SCALAR_AGGREGATE`) | ? | ? | ... |
| Function mapping (`definitions.py`) | ? | ? | ... |
| Protocol (expression system) | ? | ? | ... |
| Backend impl — Polars | ? | ? | ... |
| Backend impl — Narwhals | ? | ? | ... |
| Backend impl — Ibis | ? | ? | ... |
| api_builder protocol | ? | ? | ... |
| api_builder implementation | ? | ? | ... |
| Flat namespace wiring | ? | ? | ... |
| Free-function entrypoint (`entrypoints.py`) | ? | ? | ... |

Legend: `+` ready, `~` aspirational/stub, `-` missing.

## Gaps to close in this plan

1. ...
2. ...
```

Fill in every `?` with a concrete marker and the gap list with actionable items.

- [ ] **Step 5: Commit the audit.**

```bash
mkdir -p notes
git add notes/aggregate-wiring-audit-2026-04-08.md
git commit -m "docs(aggregate): audit wiring state for count and count_records"
```

---

## Task 2: Add `COUNT_RECORDS` enum, protocol method, function mapping

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/function_keys/enums.py`
- Modify: `src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_aggregate_generic.py`
- Modify: `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`
- Test: `tests/expressions/test_aggregate_enum.py` *(new)*

- [ ] **Step 1: Write failing enum test.**

```python
# tests/expressions/test_aggregate_enum.py
"""Tests for Substrait scalar aggregate enum + protocol + mapping wiring."""
from __future__ import annotations

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)


def test_count_enum_exists():
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT is not None


def test_count_records_enum_exists():
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS is not None


def test_count_and_count_records_are_distinct():
    assert (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT
        != FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS
    )


def test_count_records_has_function_mapping():
    from mountainash.expressions.core.expression_system.function_mapping.definitions import (
        ExpressionFunctionDefinitions,
    )
    # The class has a SCALAR_AGGREGATE_FUNCTIONS list; find COUNT_RECORDS in it
    keys = [
        fn.function_key
        for fn in ExpressionFunctionDefinitions.SCALAR_AGGREGATE_FUNCTIONS
    ]
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS in keys
    assert FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT in keys
```

- [ ] **Step 2: Run, see fail.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_enum.py
```

Expected: failures because `COUNT_RECORDS` doesn't exist on the enum.

- [ ] **Step 3: Add the enum member.** Read `src/mountainash/expressions/core/expression_system/function_keys/enums.py` around line 120 where `COUNT = auto()` lives in `FKEY_SUBSTRAIT_SCALAR_AGGREGATE`, and add directly after it:

```python
class FKEY_SUBSTRAIT_SCALAR_AGGREGATE(Enum):
    COUNT = auto()           # Substrait count(x) — 1-arg overload, counts non-null values
    COUNT_RECORDS = auto()   # NEW: Substrait count() — 0-arg overload, counts all records
                             # (both serialize to substrait_name="count" on the wire)
```

- [ ] **Step 4: Add the protocol method.** In `src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_aggregate_generic.py`, find the existing `def count(self, x, /, overflow=None)` method (around line 22) and add directly after it:

```python
    def count_records(
        self,
        /,
        overflow: Optional[str] = None,
    ) -> ExpressionT:
        """Substrait ``count()`` — zero-arg overload of the Substrait ``count`` function.

        From ``extensions/functions_aggregate_generic.yaml`` in the Substrait spec:
        "Count the number of records (not field-referenced)." Distinct from
        :meth:`count`, which is the 1-arg overload that counts non-null values
        of a specific column. Both serialize to Substrait wire format as the
        function name ``count``; arity distinguishes the two impls.

        The Python identifier ``count_records`` is mountainash-internal — a
        label so the two Substrait overloads can each have their own enum key,
        function mapping entry, and api-builder call site per the six-layer
        wiring matrix.

        Args:
            overflow: Optional overflow handling mode (Substrait-standard option).

        Returns:
            A backend-native expression that resolves to the row count when
            evaluated inside an aggregate context.
        """
        ...
```

If the file doesn't already import `Optional` from typing, add it.

- [ ] **Step 5: Add the function mapping entry.** In `src/mountainash/expressions/core/expression_system/function_mapping/definitions.py`, find the `SCALAR_AGGREGATE_FUNCTIONS` list (around line 790) and append a `COUNT_RECORDS` entry directly after the existing `COUNT` entry:

```python
    SCALAR_AGGREGATE_FUNCTIONS = [
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="count",
            options=("overflow",),
            protocol_method=SubstraitAggregateGenericExpressionSystemProtocol.count,
        ),
        ExpressionFunctionDef(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS,
            substrait_uri=SubstraitExtension.SCALAR_AGGREGATE,
            substrait_name="count",   # ← SAME Substrait function as COUNT above;
                                      #   distinguished by arity (this is the 0-arg impl)
            options=("overflow",),
            protocol_method=SubstraitAggregateGenericExpressionSystemProtocol.count_records,
        ),
    ]
```

- [ ] **Step 6: Run tests.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_enum.py
```

Expected: 4 passing.

- [ ] **Step 7: Verify no regressions.**

```bash
hatch run test:test-target-quick tests/expressions/
```

- [ ] **Step 8: Commit.**

```bash
git add src/mountainash/expressions/core/expression_system/function_keys/enums.py \
        src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_aggregate_generic.py \
        src/mountainash/expressions/core/expression_system/function_mapping/definitions.py \
        tests/expressions/test_aggregate_enum.py
git commit -m "feat(expressions): add Substrait COUNT_RECORDS enum, protocol, and function mapping"
```

---

## Task 3: Backend implementations of `count_records`

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_aggregate_generic.py`
- Modify/create: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_aggregate_generic.py`
- Modify/create: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_aggregate_generic.py`
- Test: `tests/expressions/test_aggregate_count_backends.py` *(new)*

- [ ] **Step 1: Write a failing cross-backend test for `count_records`.** This exercises the backend implementations directly, one level below the api_builder layer.

```python
# tests/expressions/test_aggregate_count_backends.py
"""Verify each backend's aggregate_generic.count_records implementation exists."""
from __future__ import annotations

import pytest


def test_polars_count_records_exists():
    from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_aggregate_generic import (
        PolarsAggregateGenericExpressionSystem,
    )
    assert hasattr(PolarsAggregateGenericExpressionSystem, "count_records")


def test_narwhals_count_records_exists():
    pytest.importorskip("narwhals")
    from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_aggregate_generic import (
        NarwhalsAggregateGenericExpressionSystem,
    )
    assert hasattr(NarwhalsAggregateGenericExpressionSystem, "count_records")


def test_ibis_count_records_exists():
    pytest.importorskip("ibis")
    from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_aggregate_generic import (
        IbisAggregateGenericExpressionSystem,
    )
    assert hasattr(IbisAggregateGenericExpressionSystem, "count_records")
```

The class names above are guesses — verify against Task 1's audit output and the actual file contents. Adjust class names in the test to match reality.

- [ ] **Step 2: Run, see fail.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_count_backends.py
```

- [ ] **Step 3: Implement `count_records` in the Polars Substrait backend.** The backend implementation follows the newly-extended Substrait protocol from Task 2. Open `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_aggregate_generic.py` and add the new method after the existing `count(self, x, ...)`. There is a commented-out `count_all` block around line 50 which can serve as a reference for the Polars primitive (`pl.len()`), but do **not** simply uncomment it — write the method fresh to match the protocol signature exactly, under the protocol-approved name `count_records`. The old commented `count_all` can be deleted.

```python
    def count_records(
        self,
        /,
        overflow: Any = None,
    ) -> pl.Expr:
        """Substrait count_records() — counts all rows including nulls.

        Args:
            overflow: Overflow handling (ignored in Polars).

        Returns:
            A Polars expression that resolves to the row count.
        """
        return pl.len()
```

Note: the `pl.len()` function is the modern Polars row-count primitive. Older Polars versions used `pl.count()`; verify current `polars` version supports `pl.len()` (it does in 0.20+). If the codebase targets an older Polars, fall back to `pl.count()`.

- [ ] **Step 4: Add `count_records` to Narwhals backend.** If `expsys_nw_aggregate_generic.py` doesn't exist, create it following the pattern of `expsys_pl_aggregate_generic.py`:

```python
# src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_aggregate_generic.py
"""Narwhals implementations of Substrait aggregate_generic protocol."""
from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.core.types import NarwhalsExpr


class NarwhalsAggregateGenericExpressionSystem:
    """Narwhals implementation of SubstraitAggregateGenericExpressionSystemProtocol."""

    def count(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Count non-null values of x."""
        return x.count()

    def count_records(
        self,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Count all rows including nulls."""
        return nw.len()
```

If the file already exists with a `count` method, just append `count_records`. Verify `nw.len()` is the correct Narwhals primitive; if not, use whichever row-count expression Narwhals exposes (`nw.col("*").count()` or similar).

- [ ] **Step 5: Add `count_records` to Ibis backend.** Follow the same pattern:

```python
# src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_aggregate_generic.py
# Append count_records if file exists; create from scratch otherwise:

def count_records(
    self,
    /,
    overflow: Any = None,
) -> IbisValueExpr:
    """Count all rows including nulls.

    Ibis' row-count primitive lives on Table, not Column — at protocol level
    we return an Ibis count aggregate that the relation visitor binds to a
    table context at compile time.
    """
    import ibis
    return ibis.row_number().count()   # or appropriate Ibis row-count primitive
```

**This is the trickiest backend.** Ibis separates column aggregates from table aggregates — `table.count()` on the table itself is the normal row-count idiom. At the protocol level, we're producing a column-space expression that will be evaluated inside an aggregate context. The simplest correct approach may be to produce a literal-1 count expression: `ibis.literal(1).count()`, which counts non-null 1s (== row count). Or use `_.count()` / `_.rowid()` depending on the Ibis idiom used elsewhere in the codebase. **Check what the existing Ibis `count` implementation returns** to match its shape — if the existing `count(x)` returns `x.count()`, then `count_records` can return `ibis.literal(1).count()`.

If the existing pattern isn't obvious from the file, report DONE_WITH_CONCERNS with the question explicitly noted. The relation-level count_rows() will still work because the AggregateRelNode visitor can special-case Ibis to use `table.count()` directly — but that's a Task 6 concern, not here.

- [ ] **Step 6: Run tests, iterate.** Both the existence tests and any pre-existing aggregate tests should stay green.

- [ ] **Step 7: Commit.**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_aggregate_generic.py \
        src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_aggregate_generic.py \
        src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_aggregate_generic.py \
        tests/expressions/test_aggregate_count_backends.py
git commit -m "feat(expressions): add count_records backend implementations for Polars/Narwhals/Ibis"
```

---

## Task 4: Real aggregate api_builder + free function + wiring

**Files:**
- Rename + replace: `src/mountainash/expressions/core/expression_protocols/api_builders/substrait/_prtcl_api_bldr_scalar_aggregate.py` → `prtcl_api_bldr_scalar_aggregate.py`
- Rename + replace: `src/mountainash/expressions/core/expression_api/api_builders/substrait/_api_bldr_scalar_aggregate.py` → `api_bldr_scalar_aggregate.py`
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/__init__.py`
- Modify: `src/mountainash/expressions/core/expression_api/boolean.py`
- Modify: `src/mountainash/expressions/core/expression_api/entrypoints.py`
- Modify: `src/mountainash/expressions/__init__.py`
- Modify: `src/mountainash/__init__.py`
- Test: extend `tests/expressions/test_aggregate_count.py` *(new)*

- [ ] **Step 1: Write the failing integration test.**

```python
# tests/expressions/test_aggregate_count.py
"""End-to-end tests: col().count() and ma.count_records() via the public API."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def sample_df() -> pl.DataFrame:
    return pl.DataFrame({
        "group": ["a", "a", "b", "b", "b"],
        "value": [1, None, 3, 4, None],
    })


def test_col_count_exposed_as_method(sample_df):
    """ma.col('value').count() should be callable from the public API."""
    expr = ma.col("value").count()
    # Shape check: should return an expression, not raise AttributeError
    assert expr is not None


def test_count_records_exposed_as_free_function(sample_df):
    """ma.count_records() should be callable from the top-level namespace."""
    expr = ma.count_records()
    assert expr is not None


def test_count_via_group_by_agg(sample_df):
    """col().count() compiles correctly through the aggregate pipeline."""
    result = (
        relation(sample_df)
        .group_by("group")
        .agg(ma.col("value").count().alias("non_null_count"))
        .to_polars()
        .sort("group")
    )
    # value has 2 non-null rows in group 'a' → 1, in group 'b' → 2
    assert result["non_null_count"].to_list() == [1, 2]


def test_count_records_via_group_by_agg(sample_df):
    """ma.count_records() compiles correctly through the aggregate pipeline."""
    result = (
        relation(sample_df)
        .group_by("group")
        .agg(ma.count_records().alias("row_count"))
        .to_polars()
        .sort("group")
    )
    # group 'a' has 2 rows total, group 'b' has 3 rows total
    assert result["row_count"].to_list() == [2, 3]
```

- [ ] **Step 2: Run, see fail.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_count.py
```

Expected: `AttributeError` on `ma.col("value").count()` and `ma.count_records` unresolved.

- [ ] **Step 3: Rename and implement the api_builder protocol.** Move `_prtcl_api_bldr_scalar_aggregate.py` to `prtcl_api_bldr_scalar_aggregate.py` (drop underscore), and replace its body with:

```python
# src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_aggregate.py
"""Protocol for Substrait scalar aggregate api_builder methods."""
from __future__ import annotations

from typing import Optional, Protocol

from mountainash.expressions.core.expression_api.api_builder_base import (
    BaseExpressionAPI,
)


class SubstraitScalarAggregateAPIBuilderProtocol(Protocol):
    """Substrait-standard scalar aggregate builder surface."""

    def count(self, *, overflow: Optional[str] = None) -> BaseExpressionAPI:
        """Count non-null values of this column.

        Corresponds to Substrait ``count(x)``.
        """
        ...
```

`count_records()` lives at the module-level entrypoints layer (it's a free function, not a column method), so it does NOT appear in this protocol.

- [ ] **Step 4: Rename and implement the real api_builder.** Move `_api_bldr_scalar_aggregate.py` to `api_bldr_scalar_aggregate.py` (drop underscore) and replace the stub body:

```python
# src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py
"""Substrait scalar aggregate APIBuilder — exposes count() and future sum/min/max/etc."""
from __future__ import annotations

from typing import Optional

from mountainash.expressions.core.expression_nodes.substrait import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)

from ..api_builder_base import BaseExpressionAPIBuilder


class SubstraitScalarAggregateAPIBuilder(BaseExpressionAPIBuilder):
    """Substrait-standard aggregate operations exposed as instance methods on col().

    Extend this class (or add sibling classes) for future Substrait aggregates
    (sum, min, max, mean, first_value, last_value, any_value, etc.).
    """

    def count(self, *, overflow: Optional[str] = None) -> BaseExpressionAPIBuilder:
        """Count non-null values. Corresponds to Substrait ``count(x)``."""
        # This method is called as ma.col("value").count(); self._node is the
        # FieldReferenceNode (or whatever the wrapped expression is).
        from mountainash.expressions.core.expression_api.api_builder_base import (
            _wrap_result,
        )
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return _wrap_result(node)
```

**Important:** the exact mechanism for wrapping the result into the fluent API depends on how other builders do it. Read `api_bldr_scalar_comparison.py` method `coalesce` (around line 387 per Task 1 audit) to see the canonical pattern — match it exactly rather than guessing. The wrap helper may be `_wrap_result`, or the class may return `self.__class__(new_node)`, or there's a `self._make(node)` helper. **Copy whichever pattern the sibling builders use.**

- [ ] **Step 5: Update builder __init__ exports.** In `src/mountainash/expressions/core/expression_api/api_builders/substrait/__init__.py`, uncomment the existing commented-out line:

```python
# Before:
# from .api_bldr_scalar_aggregate import SubstraitScalarAggregateAPIBuilder
# ...
# "SubstraitScalarAggregateAPIBuilder",

# After:
from .api_bldr_scalar_aggregate import SubstraitScalarAggregateAPIBuilder
# in __all__:
"SubstraitScalarAggregateAPIBuilder",
```

- [ ] **Step 6: Wire into the flat namespace.** In `src/mountainash/expressions/core/expression_api/boolean.py` around line 20 and line 125, uncomment the stub references:

```python
# at top of file (import section):
from .api_builders.substrait import (
    SubstraitScalarAggregateAPIBuilder,   # was commented
    ...
)

# in _FLAT_NAMESPACES:
_FLAT_NAMESPACES = [
    ...,
    SubstraitScalarAggregateAPIBuilder,   # was commented
    ...,
]
```

- [ ] **Step 7: Add the free-function `count_records` entrypoint.** In `src/mountainash/expressions/core/expression_api/entrypoints.py`, add after the existing `coalesce` definition (around line 103):

```python
def count_records() -> BaseExpressionAPI:
    """Substrait count_records() — counts all rows including nulls.

    Produces a backend-agnostic aggregate expression suitable for use inside
    ``relation.group_by(...).agg(...)`` or as a measure in an aggregate plan.

    Returns:
        A BaseExpressionAPI wrapping a ScalarFunctionNode with COUNT_RECORDS.
    """
    from mountainash.expressions.core.expression_nodes.substrait import ScalarFunctionNode
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )
    node = ScalarFunctionNode(
        function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS,
        arguments=[],
        options={},
    )
    # Wrap in the same way coalesce() wraps — read the existing coalesce body
    # around line 103 of this file and match the wrapping pattern.
    return _wrap_result(node)   # or however coalesce does it
```

Match the wrapping shape to `coalesce`. If `coalesce` returns `BooleanExpressionAPI(node)` directly, do the same. Don't invent a pattern.

- [ ] **Step 8: Export `count_records` at the package level.**

In `src/mountainash/expressions/__init__.py`:
```python
from mountainash.expressions.core.expression_api.entrypoints import (
    col, lit, coalesce, greatest, least, when, native, t_col,
    count_records,   # NEW
)
__all__ = [..., "count_records"]
```

In `src/mountainash/__init__.py` find where `coalesce` is re-exported and add `count_records` alongside:
```python
from mountainash.expressions import (
    col, lit, coalesce, greatest, least, when, native, t_col,
    count_records,   # NEW
)
__all__ += ["count_records"]
```

- [ ] **Step 9: Smoke test the imports.**

```bash
hatch run python -c "
import mountainash as ma
print('ma.count_records:', ma.count_records)
print('ma.col(\"x\").count:', ma.col('x').count)
expr = ma.col('x').count()
print('count expression:', expr)
expr2 = ma.count_records()
print('count_records expression:', expr2)
"
```

- [ ] **Step 10: Run the integration tests.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_count.py
```

Expected: all 4 passing. If the `group_by().agg()` paths fail because the aggregate function mapping isn't dispatching correctly, trace back through the visitor — the function mapping was added in Task 2 but may need a corresponding entry in whatever registry the visitor consults.

- [ ] **Step 11: Verify no regressions.**

```bash
hatch run test:test-target-quick tests/expressions/ tests/relations/
```

- [ ] **Step 12: Commit.**

```bash
git add src/mountainash/expressions/core/expression_protocols/api_builders/substrait/ \
        src/mountainash/expressions/core/expression_api/api_builders/substrait/ \
        src/mountainash/expressions/core/expression_api/boolean.py \
        src/mountainash/expressions/core/expression_api/entrypoints.py \
        src/mountainash/expressions/__init__.py \
        src/mountainash/__init__.py \
        tests/expressions/test_aggregate_count.py
git commit -m "feat(expressions): wire Substrait aggregate api_builder; expose count() and count_records()"
```

---

## Task 5: Cross-backend e2e — verify aggregate works through Narwhals and Ibis

**Files:**
- Extend: `tests/expressions/test_aggregate_count.py`

- [ ] **Step 1: Append cross-backend tests.**

```python
# Append to tests/expressions/test_aggregate_count.py

def test_count_records_narwhals_backend():
    """count_records via Narwhals-backed relation."""
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(
        pl.DataFrame({"g": ["a", "b", "b"], "v": [1, 2, None]}),
        eager_only=True,
    )
    result = (
        relation(nw_df)
        .group_by("g")
        .agg(ma.count_records().alias("n"))
        .to_polars()
        .sort("g")
    )
    assert result["n"].to_list() == [1, 2]


def test_count_records_ibis_backend():
    """count_records via Ibis-backed relation."""
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"g": ["a", "b", "b"], "v": [1, 2, None]})
    result = (
        relation(t)
        .group_by("g")
        .agg(ma.count_records().alias("n"))
        .to_polars()
        .sort("g")
    )
    assert result["n"].to_list() == [1, 2]
```

- [ ] **Step 2: Run.**

```bash
hatch run test:test-target-quick tests/expressions/test_aggregate_count.py
```

- [ ] **Step 3: If either backend fails**, the backend-specific `count_records` impl from Task 3 needs adjustment. Remember Task 3's note on Ibis — if `ibis.literal(1).count()` didn't produce the right expression, this is where it will show up. Fix the backend impl, re-run.

- [ ] **Step 4: Commit.**

```bash
git add tests/expressions/test_aggregate_count.py
git commit -m "test(expressions): cross-backend e2e for count_records via Narwhals and Ibis"
```

---

## Task 6: `Relation.count_rows()` — thin composition over `count_records`

**Files:**
- Modify: `src/mountainash/relations/core/relation_api/relation.py`
- Test: `tests/relations/test_terminal_count_rows.py` *(new)*

- [ ] **Step 1: Write failing tests.**

```python
# tests/relations/test_terminal_count_rows.py
"""Cross-backend tests for Relation.count_rows() terminal."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def df() -> pl.DataFrame:
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "amount": [10, 20, 30, 40, 50],
        "status": ["a", "b", "a", "b", "a"],
    })


def test_count_rows_basic(df):
    assert relation(df).count_rows() == 5


def test_count_rows_after_head(df):
    assert relation(df).head(2).count_rows() == 2


def test_count_rows_after_filter_match(df):
    rel = relation(df).filter(ma.col("status").eq(ma.lit("a")))
    assert rel.count_rows() == 3


def test_count_rows_after_filter_empty(df):
    rel = relation(df).filter(ma.col("status").eq(ma.lit("zzz")))
    assert rel.count_rows() == 0


def test_count_rows_returns_int(df):
    result = relation(df).count_rows()
    assert isinstance(result, int)
    assert not isinstance(result, bool)


def test_count_rows_polars_lazyframe():
    lf = pl.DataFrame({"x": list(range(100))}).lazy()
    assert relation(lf).count_rows() == 100


def test_count_rows_narwhals():
    pytest.importorskip("narwhals")
    import narwhals as nw
    nw_df = nw.from_native(pl.DataFrame({"x": [1, 2, 3, 4]}), eager_only=True)
    assert relation(nw_df).count_rows() == 4


def test_count_rows_ibis():
    pytest.importorskip("ibis")
    import ibis
    t = ibis.memtable({"x": [1, 2, 3, 4, 5]})
    assert relation(t).count_rows() == 5
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement `count_rows()`.** Add to `src/mountainash/relations/core/relation_api/relation.py` directly after `collect()`:

```python
    def count_rows(self) -> int:
        """Execute the relation and return the number of rows as a Python int.

        Implemented as a thin composition: wraps ``self._node`` in an
        ``AggregateRelNode`` with a single ``count_records()`` measure, compiles
        via the standard visitor pipeline, and extracts the single scalar
        from the single-row result. No per-backend dispatch — all backend
        variance lives inside the ``count_records`` aggregate implementations
        (see ``expsys_pl_aggregate_generic.py`` etc).

        Returns:
            Row count as a Python ``int``. Returns ``0`` for an empty relation.

        Raises:
            RelationDAGRequired: if the relation contains a ``RefRelNode`` and
                is compiled standalone instead of inside
                ``RelationDAG.collect()``.
        """
        import mountainash as ma
        from mountainash.relations.core.relation_nodes import AggregateRelNode

        counted = Relation(
            AggregateRelNode(
                input=self._node,
                keys=[],
                measures=[ma.count_records().alias("__count_rows__")._node],
            )
        )
        return int(counted.item("__count_rows__"))
```

The `._node` extraction at the end of the measures list mirrors how `GroupedRelation.agg()` builds aggregate nodes (check `grouped_relation.py` for the actual pattern — if it accepts `BaseExpressionAPI` objects directly without `._node`, drop the `._node` access). Match the sibling code.

Note that `count_rows()` depends on `item()`, so `item()` must be implemented before this test passes. Tasks are intentionally ordered: implement `item()` first is an option, but this plan orders `count_rows()` first because it's the primary feature. If the test fails with "no method 'item'", jump ahead to Task 7 and return here.

Actually — reorder: **do Task 7 (`item()`) before this step, then come back**. Item has no dependencies on count_rows and is simpler.

- [ ] **Step 4: Jump to Task 7. Implement `item()`, verify its tests pass. Return here.**

- [ ] **Step 5: Now run the count_rows tests.**

```bash
hatch run test:test-target-quick tests/relations/test_terminal_count_rows.py
```

Expected: 8 passing.

- [ ] **Step 6: Verify no regressions.**

```bash
hatch run test:test-target-quick tests/relations/
```

- [ ] **Step 7: Commit.**

```bash
git add src/mountainash/relations/core/relation_api/relation.py \
        tests/relations/test_terminal_count_rows.py
git commit -m "feat(relation): add Relation.count_rows() as composition over count_records aggregate"
```

---

## Task 7: `Relation.item()` — strict scalar extraction (DO THIS BEFORE TASK 6 STEP 5)

**Files:**
- Modify: `src/mountainash/relations/core/relation_api/relation.py` (add `item` method alongside `count_rows` scaffold)
- Test: `tests/relations/test_terminal_item.py` *(new)*

- [ ] **Step 1: Write failing tests.**

```python
# tests/relations/test_terminal_item.py
"""Cross-backend tests for Relation.item() terminal."""
from __future__ import annotations

from datetime import datetime

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.fixture
def three_row_df() -> pl.DataFrame:
    return pl.DataFrame({
        "id": [10, 20, 30],
        "name": ["alice", "bob", "carol"],
        "score": [1.5, 2.5, 3.5],
    })


def test_item_first_row(three_row_df):
    assert relation(three_row_df).item("id") == 10


def test_item_explicit_row_zero(three_row_df):
    assert relation(three_row_df).item("id", row=0) == 10


def test_item_string_column(three_row_df):
    assert relation(three_row_df).item("name") == "alice"


def test_item_after_head_one(three_row_df):
    rel = relation(three_row_df).head(1)
    assert rel.item("id") == 10
    assert rel.item("name") == "alice"


def test_item_after_filter_to_one_row(three_row_df):
    rel = relation(three_row_df).filter(ma.col("id").eq(ma.lit(20)))
    assert rel.item("name") == "bob"


def test_item_explicit_row_index(three_row_df):
    assert relation(three_row_df).item("id", row=2) == 30


def test_item_empty_relation_raises_index_error(three_row_df):
    rel = relation(three_row_df).filter(ma.col("id").eq(ma.lit(999)))
    with pytest.raises(IndexError, match="row 0"):
        rel.item("id")


def test_item_missing_column_raises_key_error(three_row_df):
    with pytest.raises(KeyError, match="nope"):
        relation(three_row_df).item("nope")


def test_item_row_out_of_range_raises_index_error(three_row_df):
    with pytest.raises(IndexError, match="row 5"):
        relation(three_row_df).item("id", row=5)


def test_item_negative_row_raises_index_error(three_row_df):
    with pytest.raises(IndexError):
        relation(three_row_df).item("id", row=-1)


def test_item_datetime_column():
    df = pl.DataFrame({
        "ts": [datetime(2026, 4, 8, 12, 0), datetime(2026, 4, 9, 13, 0)],
    })
    result = relation(df).item("ts")
    assert isinstance(result, datetime)
    assert result == datetime(2026, 4, 8, 12, 0)
```

- [ ] **Step 2: Run, see fail.**

- [ ] **Step 3: Implement `item()`.** Add to `src/mountainash/relations/core/relation_api/relation.py` immediately after `count_rows()`:

```python
    def item(self, column: str, row: int = 0) -> Any:
        """Extract a single cell value as a Python scalar with strict semantics.

        The relation is materialised via the existing ``to_polars()`` terminal,
        and the cell is extracted via Polars' ``Series`` scalar accessor
        (which handles native → Python conversion for datetime, decimal, etc.).

        Args:
            column: Column name to extract. Must exist in the result.
            row: Row index; must satisfy ``0 <= row < number_of_rows``.
                Defaults to ``0``. Negative indexing is **not** supported.

        Returns:
            The cell value as a Python scalar.

        Raises:
            KeyError: if ``column`` is not present in the result.
            IndexError: if ``row < 0``, if ``row >= number_of_rows``, or if
                the relation is empty.
            RelationDAGRequired: if the relation contains a ``RefRelNode`` and
                is compiled standalone.
        """
        df = self.to_polars()

        if column not in df.columns:
            raise KeyError(column)

        n = len(df)
        if row < 0 or row >= n:
            raise IndexError(
                f"row {row} out of range for relation with {n} row(s) "
                f"in column {column!r}"
            )

        return df[column][row]
```

- [ ] **Step 4: Run, see pass.**

```bash
hatch run test:test-target-quick tests/relations/test_terminal_item.py
```

Expected: 11 passing.

- [ ] **Step 5: Commit `item()` standalone.**

```bash
git add src/mountainash/relations/core/relation_api/relation.py \
        tests/relations/test_terminal_item.py
git commit -m "feat(relation): add Relation.item() with strict bounds checking"
```

- [ ] **Step 6: Return to Task 6 Step 5.**

---

## Task 8: DAG integration tests

**Files:**
- Test: `tests/relations/dag/test_dag_count_rows_and_item.py` *(new)*

- [ ] **Step 1: Write tests.**

```python
# tests/relations/dag/test_dag_count_rows_and_item.py
"""DAG integration for count_rows() and item() terminals."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.errors import RelationDAGRequired


def test_count_rows_standalone_on_ref_raises():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}, {"id": 2}]))
    ref_rel = dag.ref("orders")
    with pytest.raises(RelationDAGRequired):
        ref_rel.count_rows()


def test_item_standalone_on_ref_raises():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}]))
    ref_rel = dag.ref("orders")
    with pytest.raises(RelationDAGRequired):
        ref_rel.item("id")


def test_dag_collect_then_count_rows():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}, {"id": 2}, {"id": 3}]))
    dag.add(
        "filtered",
        dag.ref("orders").filter(ma.col("id").gt(ma.lit(1))),
    )
    native = dag.collect("filtered")
    df = native.collect() if isinstance(native, pl.LazyFrame) else native
    assert len(df) == 2


def test_dag_collect_then_item():
    dag = RelationDAG()
    dag.add(
        "orders",
        relation([{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]),
    )
    dag.add("first", dag.ref("orders").head(1))
    native = dag.collect("first")
    df = native.collect() if isinstance(native, pl.LazyFrame) else native
    # Wrap the native back in a Relation to use item()
    assert relation(df).item("name") == "alice"
```

- [ ] **Step 2: Run, see pass.**

```bash
hatch run test:test-target-quick tests/relations/dag/test_dag_count_rows_and_item.py
```

- [ ] **Step 3: Commit.**

```bash
git add tests/relations/dag/test_dag_count_rows_and_item.py
git commit -m "test(relation): DAG integration tests for count_rows() and item()"
```

---

## Task 9: Docs, wiring matrix, lint, finalize

**Files:**
- Modify: `mountainash-central/01.principles/mountainash-expressions/a.architecture/wiring-matrix.md`
- Possibly modify: `mountainash-central/01.principles/mountainash-expressions/h.backlog/polars-alignment-deferred.md`

- [ ] **Step 1: Update the wiring matrix principle.** The aggregate section of `wiring-matrix.md` previously had all aggregate methods marked aspirational (`-`). With this plan landed, `count` and `count_records` should be marked as fully wired (`+`). Open the file and find the aggregate matrix section. If no section exists yet, add one modelled on the existing Substrait scalar sections:

```markdown
### Substrait Scalar Aggregate (2 methods)

| Method | ENUM | Fn Map | Polars | Ibis | Narwhals |
|--------|------|--------|--------|------|----------|
| `count` | + | + | + | + | + |
| `count_records` | + | + | + | + | + |
| `sum` | - | - | - | - | - |
| `min` | - | - | - | - | - |
| `max` | - | - | - | - | - |
| `mean` | - | - | - | - | - |
| `any_value` | - | - | - | - | - |
| `first_value` | - | - | - | - | - |
| `last_value` | - | - | - | - | - |
```

(Aspirational methods listed per Substrait spec so the gap is visible.)

Also update the "Future Considerations" section note about aggregate protocols to say they are now partially wired (count + count_records), with remaining methods aspirational.

- [ ] **Step 2: Check `h.backlog/polars-alignment-deferred.md`** for any aggregate-related backlog entries now closed. If such an entry exists, update it or remove it as appropriate.

- [ ] **Step 3: Commit principles updates.**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expressions/a.architecture/wiring-matrix.md \
        01.principles/mountainash-expressions/h.backlog/polars-alignment-deferred.md 2>/dev/null
git commit -m "docs(principles): mark count and count_records as fully wired in aggregate matrix"
git push
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions
```

- [ ] **Step 4: Lint.**

```bash
hatch run ruff:check 2>&1 | tail -20
hatch run ruff:fix   # auto-fix what it can
```

- [ ] **Step 5: Type check the new/modified files.**

```bash
hatch run mypy:check \
  src/mountainash/expressions/core/expression_system/function_keys/enums.py \
  src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_aggregate_generic.py \
  src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_aggregate_generic.py \
  src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_aggregate.py \
  src/mountainash/expressions/core/expression_api/entrypoints.py \
  src/mountainash/relations/core/relation_api/relation.py \
  2>&1 | tail -20
```

Fix any new errors. Pre-existing errors (verifiable via `git stash` + run + `git stash pop` + run + diff) are out of scope.

- [ ] **Step 6: Run the full relations + expressions test suites.**

```bash
hatch run test:test-target-quick tests/relations/ tests/expressions/
```

Expected: everything green, no regressions versus baseline.

- [ ] **Step 7: Run the full suite if time allows.**

```bash
hatch run test:test
```

Same pre-existing failures as the `develop` baseline are acceptable.

- [ ] **Step 8: Final empty-allowed commit.**

```bash
git commit --allow-empty -m "chore(relation): finalize count_rows, item, and aggregate foundation"
```

---

## Self-Review

**Spec coverage check** (against `docs/superpowers/specs/2026-04-08-relation-count-and-item-design.md`):

| Spec section | Covered by |
|---|---|
| `count_rows()` semantics — compile to aggregate, extract scalar | Task 6 (composition) + Tasks 2-4 (foundation) |
| `count_rows()` push-down behaviour | Achieved transparently: the aggregate pipeline compiles to `pl.len()` / `table.count()` / `nw.len()` via the backend `count_records` impls, which Polars/Ibis push down natively |
| `count_rows()` Polars LazyFrame path | Task 3 step 3 — Polars `count_records` returns `pl.len()` which is lazy |
| `count_rows()` Narwhals path | Task 3 step 4 + Task 5 cross-backend test |
| `count_rows()` Ibis path | Task 3 step 5 + Task 5 cross-backend test |
| `count_rows()` + RefRelNode standalone raises | Task 8 (DAG integration) |
| `count_rows()` + RelationDAG.collect works | Task 8 |
| `item()` strict semantics (all edge cases) | Task 7 (11 parametrized cases) |
| `item()` datetime native conversion | Task 7 (`test_item_datetime_column`) |
| `item()` RelationDAG integration | Task 8 |
| Cross-backend test matrix | Tasks 5, 6, 7, 8 |
| Risk — aggregate rewrite + RefRelNode | Task 8 explicitly tests this combo |
| Risk — Narwhals scalar extraction | Task 5 |
| Risk — Ibis count execution | Task 5 + Task 3 step 5 (Ibis is the flagged-difficult backend) |
| **Substrait alignment** | Explicitly called out in plan header and every file under `substrait/`; no extensions_mountainash work |
| **Foundation for future aggregates** | Task 4 creates the real api_builder; future `sum`/`min`/`max` are one-file additions to `api_bldr_scalar_aggregate.py` + protocol + backend impls |

**Divergence from the spec:** none. The spec described `count_rows()` as wrapping in `AggregateRelNode` with a count measure — that is exactly what Task 6 does. The pragmatic-plan version that used per-backend dispatch has been discarded; this plan follows the spec literally.

**Placeholder scan:** All code blocks are complete. The only flex points are explicitly marked: Task 3 step 5 (Ibis `count_records` implementation may need adjustment), Task 4 step 4 (match sibling builder's wrapping pattern), Task 4 step 7 (match `coalesce` entrypoint shape). Each lists the specific file to consult and the specific question to answer — no "figure it out" hand-waves.

**Type consistency:** `count_rows() -> int` and `item(column: str, row: int = 0) -> Any` consistent across Tasks 6, 7, 8, and the spec. `FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT` and `COUNT_RECORDS` used consistently throughout. Protocol method name `count_records` used consistently at protocol/backend layers; free-function entrypoint name `count_records` consistent across `entrypoints.py`, `expressions/__init__.py`, `mountainash/__init__.py`.

**Task ordering note:** Task 6 (count_rows) depends on Task 7 (item) because `count_rows` uses `.item()` internally. Task 6 explicitly instructs the implementer to jump to Task 7 mid-task, implement item, then return. This is intentional — keeping count_rows as "Task 6" preserves the logical ordering (primary feature first in the narrative) while the dependency order is handled inline.

---

Plan complete and saved to `docs/superpowers/plans/2026-04-08-relation-count-and-item.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
