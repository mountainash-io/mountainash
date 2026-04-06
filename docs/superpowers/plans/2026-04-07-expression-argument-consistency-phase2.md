# Expression Argument Consistency Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all 65 remaining `_extract_literal_value` calls across datetime, name, rounding, logarithmic, null, and window operations — then delete `_extract_literal_value` entirely.

**Architecture:** Three categories of change: (A) move universally-literal params from `arguments` to `options` at the API builder level, (B) pass-through migration for params where some backends accept expressions, (C) remove no-op extractions of params already delivered as raw values via `options`. Final step removes `_extract_literal_value` from all base classes.

**Tech Stack:** Python, pytest, Polars, Ibis, Narwhals

**Spec:** `docs/superpowers/specs/2026-04-07-expression-argument-consistency-phase2-design.md`

---

### Task 1: Category A — Move `round(decimals)` to Options

Move the `decimals` parameter from `arguments` to `options` in the rounding API builder. Update all three backends to receive it as a raw value. Remove `_extract_literal_value` calls.

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_rounding.py:65-91`
- Modify: `src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_rounding.py:41-49`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_rounding.py:49-67`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_rounding.py:50-68`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_rounding.py:54-72`

- [ ] **Step 1: Read all five files to confirm current state**

Read each file at the line ranges above.

- [ ] **Step 2: Update the API builder — move decimals to options**

In `api_bldr_scalar_rounding.py`, replace the `round` method (lines 65-91). The key change: `decimals` goes into `options` instead of being wrapped via `_to_substrait_node` into `arguments`:

```python
def round(
    self,
    decimals: Optional[int] = None,
) -> BaseExpressionAPI:
    """Round values to the specified number of decimal places.

    Substrait: round

    Args:
        decimals: Number of decimal places (literal integer).

    Returns:
        New ExpressionAPI with round node.
    """
    if decimals is None:
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
            arguments=[self._node],
        )
    else:
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
            arguments=[self._node],
            options={"s": decimals},
        )
    return self._build(node)
```

- [ ] **Step 3: Update the protocol — narrow type to `Optional[int]`**

In `prtcl_api_bldr_scalar_rounding.py`, update the `round` signature (lines 41-49):

```python
def round(
    self,
    decimals: Optional[int] = None,
) -> BaseExpressionAPI:
    """Round values to the specified number of decimal places."""
    ...
```

- [ ] **Step 4: Update Polars backend — remove `_extract_literal_value`, receive raw `int`**

In `expsys_pl_scalar_rounding.py`, update the `round` method. The `s` parameter now arrives as a raw `int` via `**options` (not a visited `pl.Expr`). Remove `_extract_literal_value`:

```python
def round(
    self,
    x: PolarsExpr,
    /,
    s: int = 0,
    rounding: Any = None,
) -> PolarsExpr:
    """Round to s decimal places."""
    return x.round(s)
```

- [ ] **Step 5: Update Ibis backend — same pattern**

In `expsys_ib_scalar_rounding.py`:

```python
def round(
    self,
    x: IbisNumericExpr,
    /,
    s: int = 0,
    rounding: Any = None,
) -> IbisNumericExpr:
    """Round to s decimal places."""
    return x.round(s)
```

- [ ] **Step 6: Update Narwhals backend — same pattern**

In `expsys_nw_scalar_rounding.py`:

```python
def round(
    self,
    x: NarwhalsExpr,
    /,
    s: int = 0,
    rounding: Any = None,
) -> NarwhalsExpr:
    """Round to s decimal places."""
    return x.round(s)
```

- [ ] **Step 7: Run existing round tests**

Run: `hatch run test:test-target-quick tests/ -k "round" -v`
Expected: Existing round tests PASS (they use literal integers — unchanged behaviour)

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_rounding.py \
  src/mountainash/expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_rounding.py \
  src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_rounding.py \
  src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_rounding.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_rounding.py
git commit -m "refactor: move round(decimals) from arguments to options

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Category A — Move Name Operations to Options

Move `name`, `prefix`, `suffix` parameters from `arguments` (wrapped in `LiteralNode`) to `options` in the name API builder. Update all three backends.

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py:36-93`
- Modify: `src/mountainash/expressions/core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_name.py:25-68`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_name.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_name.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_name.py`

- [ ] **Step 1: Read all files to confirm current state**

Read each file.

- [ ] **Step 2: Update the API builder — move to options**

In `api_bldr_ext_ma_name.py`, update all three methods. Each currently does:
```python
arguments=[self._node, LiteralNode(value=name)]
```
Change to:
```python
arguments=[self._node], options={"name": name}
```

For `alias` (lines 36-53):
```python
def alias(self, name: str) -> BaseExpressionAPI:
    """Rename the expression output column."""
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
        arguments=[self._node],
        options={"name": name},
    )
    return self._build(node)
```

For `prefix` (lines 55-73):
```python
def prefix(self, prefix: str) -> BaseExpressionAPI:
    """Add a prefix to the column name."""
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_NAME.PREFIX,
        arguments=[self._node],
        options={"prefix": prefix},
    )
    return self._build(node)
```

For `suffix` (lines 75-93):
```python
def suffix(self, suffix: str) -> BaseExpressionAPI:
    """Add a suffix to the column name."""
    node = ScalarFunctionNode(
        function_key=FKEY_MOUNTAINASH_NAME.SUFFIX,
        arguments=[self._node],
        options={"suffix": suffix},
    )
    return self._build(node)
```

- [ ] **Step 3: Update all three backend name implementations**

Each backend's `alias`, `prefix`, `suffix` methods currently extract the literal value. After this change, they receive raw `str` via `**options`. Remove `_extract_literal_value` calls.

For each backend, the methods become:

**Polars** (`expsys_pl_ext_ma_name.py`):
```python
def alias(self, input: PolarsExpr, /, name: str) -> PolarsExpr:
    return input.alias(name)

def prefix(self, input: PolarsExpr, /, prefix: str) -> PolarsExpr:
    return input.name.prefix(prefix)

def suffix(self, input: PolarsExpr, /, suffix: str) -> PolarsExpr:
    return input.name.suffix(suffix)
```

**Ibis** (`expsys_ib_ext_ma_name.py`):
```python
def alias(self, input: IbisExpr, /, name: str) -> IbisExpr:
    return input.name(name)

def prefix(self, input: IbisExpr, /, prefix: str) -> IbisExpr:
    current_name = self._extract_column_name(input) or "col"
    return input.name(prefix + current_name)

def suffix(self, input: IbisExpr, /, suffix: str) -> IbisExpr:
    current_name = self._extract_column_name(input) or "col"
    return input.name(current_name + suffix)
```

**Narwhals** (`expsys_nw_ext_ma_name.py`):
```python
def alias(self, input: NarwhalsExpr, /, name: str) -> NarwhalsExpr:
    return input.alias(name)

def prefix(self, input: NarwhalsExpr, /, prefix: str) -> NarwhalsExpr:
    return input.name.prefix(prefix)

def suffix(self, input: NarwhalsExpr, /, suffix: str) -> NarwhalsExpr:
    return input.name.suffix(suffix)
```

NOTE: Read each backend file first to confirm the exact implementation (especially Ibis which uses `_extract_column_name`). Preserve any logic beyond just the extraction.

- [ ] **Step 4: Run name tests**

Run: `hatch run test:test-target-quick tests/ -k "alias or prefix or suffix or name" -v`
Expected: All existing name tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py \
  src/mountainash/expressions/core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_name.py \
  src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_name.py \
  src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_name.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_name.py
git commit -m "refactor: move name operations (alias/prefix/suffix) from arguments to options

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Category A — Move `nth_value(n)` to Options

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py:225-240`
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py:144-162`

- [ ] **Step 1: Read both files**

- [ ] **Step 2: Update the API builder**

In `api_bldr_window_arithmetic.py`, change `nth_value` (lines 225-240):

```python
def nth_value(self, n: int) -> BaseExpressionAPI:
    """Nth value in the window frame (1-based)."""
    node = WindowFunctionNode(
        function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE,
        arguments=[self._node],
        options={"window_offset": n},
    )
    return self._build(node)
```

- [ ] **Step 3: Update Polars backend**

In `expsys_pl_window_arithmetic.py`, update the `nth_value` method. It currently extracts `window_offset` — now it arrives as raw `int` via options:

```python
def nth_value(self, input: PolarsExpr, /, window_offset: int = 1) -> PolarsExpr:
    """Nth value in the window frame."""
    return input.gather(window_offset - 1)
```

Remove the `_extract_literal_value` call.

- [ ] **Step 4: Run window tests**

Run: `hatch run test:test-target-quick tests/ -k "nth_value or window" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_window_arithmetic.py \
  src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_window_arithmetic.py
git commit -m "refactor: move nth_value(n) from arguments to options

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Category B — Migrate Logarithmic `log(base)` Pass-Through

`log(base)` correctly belongs in `arguments` since Polars and Ibis accept Expr. Remove `_extract_literal_value`, wrap with `_call_with_expr_support`.

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_logarithmic.py:91-118`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_logarithmic.py:92-119`

- [ ] **Step 1: Read both files**

- [ ] **Step 2: Update Polars `logb`**

Remove `_extract_literal_value` call (line 114), wrap with `_call_with_expr_support`:

```python
def logb(self, x: PolarsExpr, /, base: PolarsExpr, rounding: Any = None,
         on_domain_error: Any = None, on_log_zero: Any = None) -> PolarsExpr:
    """Logarithm with custom base."""
    return self._call_with_expr_support(
        lambda: x.log(base),
        function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB,
        base=base,
    )
```

Add the function key import if not present:
```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC,
)
```

- [ ] **Step 3: Update Ibis `logb`**

Same pattern:
```python
def logb(self, x: IbisNumericExpr, /, base: IbisNumericExpr, rounding: Any = None,
         on_domain_error: Any = None, on_log_zero: Any = None) -> IbisNumericExpr:
    """Logarithm with custom base."""
    return self._call_with_expr_support(
        lambda: x.log(base),
        function_key=FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB,
        base=base,
    )
```

- [ ] **Step 4: Run log tests**

Run: `hatch run test:test-target-quick tests/ -k "log" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_logarithmic.py \
  src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_logarithmic.py
git commit -m "feat: migrate log(base) to pass-through expressions

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Category B — Migrate Datetime Offset Operations + Registry

The 8 datetime offset operations (`add_years` through `add_microseconds`) correctly belong in `arguments` since Polars accepts Expr. Apply Phase 1 pattern across all three backends. Add limitation registry entries for Ibis and Narwhals.

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/base.py` (add registry entries)
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/base.py` (add registry entries)

- [ ] **Step 1: Add Ibis limitation registry entries**

In `ibis/base.py`, add imports and registry entries. The Ibis `KNOWN_EXPR_LIMITATIONS` is currently empty (inherits from base). Add:

```python
from mountainash.core.types import KnownLimitation
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)
```

Then add class variable:

```python
_IB_DATETIME_OFFSET_LITERAL_ONLY = KnownLimitation(
    message="Ibis datetime offset operations require literal integer values",
    native_errors=(TypeError,),
    workaround="Use a literal integer for the offset amount",
)

KNOWN_EXPR_LIMITATIONS: dict[tuple[Any, str], KnownLimitation] = {
    (FK_DT.ADD_YEARS, "years"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MONTHS, "months"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_DAYS, "days"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_HOURS, "hours"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MINUTES, "minutes"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_SECONDS, "seconds"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MILLISECONDS, "milliseconds"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MICROSECONDS, "microseconds"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
}
```

- [ ] **Step 2: Add Narwhals limitation registry entries**

In `narwhals/base.py`, add to the existing `KNOWN_EXPR_LIMITATIONS` dict. Import `FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT` at the top alongside the existing `FK_STR` import:

```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)
```

Add a shared limitation and extend the dict:

```python
_NW_DATETIME_OFFSET_LITERAL_ONLY = KnownLimitation(
    message="Narwhals datetime offset operations require literal integer values",
    native_errors=(TypeError,),
    workaround="Use a literal integer for the offset amount",
)
```

Add to `KNOWN_EXPR_LIMITATIONS`:
```python
    (FK_DT.ADD_YEARS, "years"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MONTHS, "months"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_DAYS, "days"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_HOURS, "hours"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MINUTES, "minutes"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_SECONDS, "seconds"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MILLISECONDS, "milliseconds"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MICROSECONDS, "microseconds"): _NW_DATETIME_OFFSET_LITERAL_ONLY,
```

- [ ] **Step 3: Migrate Polars datetime offset methods**

In `expsys_pl_ext_ma_scalar_datetime.py`, find ALL 8 `add_*` methods that call `_extract_literal_value`. Remove the extraction, pass through directly, wrap with `_call_with_expr_support`.

Add function key import:
```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
)
```

Pattern for each (using `add_years` as example):
```python
def add_years(self, x: PolarsExpr, years: PolarsExpr, /) -> PolarsExpr:
    return self._call_with_expr_support(
        lambda: x + pl.duration(years=years),  # or whatever the current implementation does
        function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS,
        years=years,
    )
```

IMPORTANT: Read the current implementation of each method to understand the exact Polars API calls used (e.g., `pl.duration`, `timedelta`, `offset_by`). Preserve the implementation logic — only remove `_extract_literal_value` and wrap with `_call_with_expr_support`.

- [ ] **Step 4: Migrate Ibis datetime offset methods**

Same 8 methods in `expsys_ib_ext_ma_scalar_datetime.py`. Use `_extract_literal_if_possible` since Ibis requires literal ints for `ibis.interval()`:

```python
def add_years(self, x: IbisExpr, years: IbisExpr, /) -> IbisExpr:
    years_val = self._extract_literal_if_possible(years)
    return self._call_with_expr_support(
        lambda: x + ibis.interval(years=years_val),
        function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS,
        years=years,
    )
```

- [ ] **Step 5: Migrate Narwhals datetime offset methods**

Same 8 methods in `expsys_nw_ext_ma_scalar_datetime.py`. Use `_extract_literal_if_possible`:

```python
def add_years(self, x: NarwhalsExpr, years: NarwhalsExpr, /) -> NarwhalsExpr:
    years_val = self._extract_literal_if_possible(years)
    return self._call_with_expr_support(
        lambda: ...,  # preserve current implementation
        function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS,
        years=years,
    )
```

- [ ] **Step 6: Run datetime tests**

Run: `hatch run test:test-target-quick tests/ -k "datetime or temporal or add_year or add_day" -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/ibis/base.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/base.py
git commit -m "feat: migrate datetime offset operations to pass-through with registries

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Category B — Migrate Narwhals Null Operations

Remove `_extract_literal_value` from `fill_null`, `null_if`, `fill_nan` in Narwhals null backend. Narwhals accepts Expr for these — no registry entry needed.

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_null.py`

- [ ] **Step 1: Read the file**

Read `expsys_nw_ext_ma_null.py` to see current implementations.

- [ ] **Step 2: Migrate all three methods**

Remove `_extract_literal_value` calls. Narwhals `fill_null` and `fill_nan` accept expressions natively, so just pass through:

```python
def fill_null(self, input: NarwhalsExpr, /, replacement: NarwhalsExpr) -> NarwhalsExpr:
    return input.fill_null(replacement)

def null_if(self, input: NarwhalsExpr, /, condition: NarwhalsExpr) -> NarwhalsExpr:
    # Read current implementation to understand the logic
    ...

def fill_nan(self, input: NarwhalsExpr, /, replacement: NarwhalsExpr) -> NarwhalsExpr:
    return input.fill_null(replacement)  # or whatever current impl does
```

Read the file first — preserve the implementation logic.

- [ ] **Step 3: Run null tests**

Run: `hatch run test:test-target-quick tests/ -k "null or coalesce or fill" -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_null.py
git commit -m "feat: migrate Narwhals null operations to pass-through expressions

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Category C — Remove No-Op Datetime Extractions

Remove all `_extract_literal_value` calls on parameters that are already delivered as raw values via `options` (unit, timezone, format, offset, rounding). These calls are no-ops — they extract a raw string to a raw string.

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_datetime.py` (2 calls: rounding, unit)
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_datetime.py` (1 call: unit)
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_datetime.py` (1 call: unit)
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py` (remaining unit/timezone/format/offset calls)
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_datetime.py` (remaining unit calls)
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py` (remaining unit calls)

- [ ] **Step 1: Find all remaining `_extract_literal_value` calls in datetime files**

Run:
```bash
grep -n "_extract_literal_value" src/mountainash/expressions/backends/expression_systems/*/substrait/expsys_*_scalar_datetime.py src/mountainash/expressions/backends/expression_systems/*/extensions_mountainash/expsys_*_ext_ma_scalar_datetime.py
```

- [ ] **Step 2: Remove each no-op extraction**

For each call like:
```python
unit_val = self._extract_literal_value(unit)
```

Simply use `unit` directly (it's already a raw string from `**options`):
```python
# Remove: unit_val = self._extract_literal_value(unit)
# Use 'unit' directly in the subsequent code
```

This is a mechanical find-and-replace. For each method:
1. Remove the `_extract_literal_value` line
2. Replace `unit_val` with `unit` (or `timezone_val` with `timezone`, etc.) in subsequent code

- [ ] **Step 3: Run datetime tests**

Run: `hatch run test:test-target-quick tests/ -k "datetime or temporal" -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_datetime.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_datetime.py
git commit -m "refactor: remove no-op _extract_literal_value from datetime options params

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Add Expression Argument Type Tests for Non-String Operations

**Files:**
- Create: `tests/cross_backend/test_expression_argument_types_nonstring.py`

- [ ] **Step 1: Create the test file**

```python
"""Cross-backend tests for expression argument types in non-string operations.

Tests that non-string operations handle argument types consistently.
Category A params (round decimals, names) are now options and only accept literals.
Category B params (log base, datetime offsets, fill_null) accept expressions where the backend supports it.
"""

import pytest
import mountainash as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


# =============================================================================
# Rounding — decimals is now an option (always literal)
# =============================================================================


@pytest.mark.cross_backend
class TestRoundArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_round_literal_decimals(self, backend_name, backend_factory, collect_expr):
        data = {"val": [3.14159, 2.71828]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").round(2)
        actual = collect_expr(df, expr)
        assert actual == [3.14, 2.72], f"[{backend_name}] got {actual}"


# =============================================================================
# Logarithmic — base is an argument (Polars + Ibis accept Expr)
# =============================================================================


@pytest.mark.cross_backend
class TestLogArgTypes:

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals log not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals log not implemented")),
    ])
    def test_log_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"val": [100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").log(10.0)
        actual = collect_expr(df, expr)
        assert abs(actual[0] - 2.0) < 0.01, f"[{backend_name}] got {actual}"
        assert abs(actual[1] - 3.0) < 0.01, f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals log not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals log not implemented")),
    ])
    def test_log_column_reference_base(self, backend_name, backend_factory, collect_expr):
        data = {"val": [100.0, 1000.0], "base": [10.0, 10.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").log(ma.col("base"))
        actual = collect_expr(df, expr)
        assert abs(actual[0] - 2.0) < 0.01, f"[{backend_name}] got {actual}"
        assert abs(actual[1] - 3.0) < 0.01, f"[{backend_name}] got {actual}"


# =============================================================================
# Datetime offsets — Polars accepts Expr, Ibis/Narwhals require literal
# =============================================================================


@pytest.mark.cross_backend
class TestDatetimeOffsetArgTypes:

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="datetime offset limited")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="datetime offset limited")),
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis datetime offset limited")),
        pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
            strict=True, reason="ibis datetime offset limited")),
        pytest.param("ibis-sqlite", marks=pytest.mark.xfail(
            strict=True, reason="ibis datetime offset limited")),
    ])
    def test_add_days_column_reference(self, backend_name, backend_factory, collect_expr):
        from datetime import datetime
        data = {
            "dt": [datetime(2024, 1, 15), datetime(2024, 6, 20)],
            "days": [5, 10],
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("dt").dt.add_days(ma.col("days"))
        actual = collect_expr(df, expr)
        assert actual[0].day == 20, f"[{backend_name}] got {actual}"
        assert actual[1].day == 30, f"[{backend_name}] got {actual}"
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target-quick tests/cross_backend/test_expression_argument_types_nonstring.py -v`
Expected: Tests PASS or strict XFAIL as documented

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_expression_argument_types_nonstring.py
git commit -m "test: add expression argument type tests for non-string operations

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Remove `_extract_literal_value` from All Base Classes

The final step — all callers are migrated. Remove the deprecated method entirely.

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/base.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/base.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/base.py`

- [ ] **Step 1: Verify no remaining callers**

Run:
```bash
grep -r "_extract_literal_value" src/mountainash/expressions/backends/ --include="*.py" | grep -v "base.py" | grep -v "__pycache__"
```
Expected: Zero results (all callers migrated in Tasks 1-7)

- [ ] **Step 2: Remove from Polars base**

In `polars/base.py`, delete the entire `_extract_literal_value` method (the one with the `.. deprecated::` docstring).

- [ ] **Step 3: Remove from Ibis base**

In `ibis/base.py`, delete the entire `_extract_literal_value` method.

- [ ] **Step 4: Remove from Narwhals base**

In `narwhals/base.py`, delete the entire `_extract_literal_value` method.

- [ ] **Step 5: Run full test suite**

Run: `hatch run test:test-quick`
Expected: All tests PASS (no callers remain)

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/base.py \
  src/mountainash/expressions/backends/expression_systems/ibis/base.py \
  src/mountainash/expressions/backends/expression_systems/narwhals/base.py
git commit -m "refactor: remove deprecated _extract_literal_value from all backends

All callers migrated to _extract_literal_if_possible + _call_with_expr_support
or moved to options. See expression argument consistency Phase 1 & 2 specs.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```
