# `t_is_in` / `t_is_not_in` Accept List-Typed Column Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `t_col(x).t_is_in(col(list_col))` work cross-backend by distinguishing literal-list vs compiled-expression arguments at the Python type level — no new API surface, no dtype introspection.

**Architecture:** The current API builder wraps *every* non-literal `values` argument inside a `LIST` function node, causing Polars to see a nested-list type when the argument is a list column. The fix: in the API builder, only wrap literal Python lists/tuples/sets in `LIST`; pass expression arguments through raw. The visitor then compiles the raw expression normally, and each backend's `t_is_in` receives either a `list` (literal path, today's behavior) or a compiled `Expr` (new list-column path, dispatched via `isinstance` at the Python boundary — no dtype peek needed).

**Tech Stack:** Python 3.12, Polars, Ibis, Narwhals, pytest, hatch.

**Spec:** `docs/superpowers/specs/2026-04-08-ternary-is-in-list-column-design.md`

---

## File Map

| # | File | Responsibility | Action |
|---|---|---|---|
| 1 | `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_ternary.py` | Build-time AST construction for ternary API | Modify `t_is_in`, `t_is_not_in` to skip `LIST` wrapper for single expression args |
| 2 | `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_ternary.py` | Protocol contract for backends | Widen `collection` type hint to `Collection[Any] \| ExpressionT` |
| 3 | `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_ternary.py` | Polars backend impl | Type-dispatch `collection`: list → `is_in`, `pl.Expr` → `list.contains` |
| 4 | `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_ternary.py` | Ibis backend impl | Same dispatch pattern using `ibis.Expr` type check |
| 5 | `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_ternary.py` | Narwhals backend impl | Same dispatch pattern using `nw.Expr` type check |
| 6 | `src/mountainash/expressions/backends/expression_systems/narwhals/base.py` | Narwhals known-limitations registry | Add `T_IS_IN`/`T_IS_NOT_IN` entries for list-column case |
| 7 | `tests/cross_backend/test_ternary_is_in_list_column.py` | New cross-backend test file | Create (all parametrized tests) |

**No changes needed to:**
- `visitor.py` — the existing code path (`self.visit(arg)`) handles a raw `FieldReferenceNode` second arg correctly; only `LIST` nodes trigger the raw-values special case.
- Function mapping definitions (`T_IS_IN` / `T_IS_NOT_IN` identity unchanged).
- Function key enums.

---

## Task 1: Red test — the downstream reproduction

**Files:**
- Create: `tests/cross_backend/test_ternary_is_in_list_column.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/cross_backend/test_ternary_is_in_list_column.py
"""Cross-backend tests: t_is_in / t_is_not_in accept list-typed column argument.

Tracks mountainash-expressions#75. See spec at
docs/superpowers/specs/2026-04-08-ternary-is-in-list-column-design.md
"""
from __future__ import annotations

import pytest

import mountainash.expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTIsInListColumn:

    def test_t_is_in_list_column_happy_path(self, backend_name, backend_factory, collect_expr):
        """Scalar column vs list column: per-row membership."""
        if backend_name == "narwhals-pandas":
            pytest.xfail(
                "narwhals-pandas list ops lag narwhals-polars; "
                "KNOWN_EXPR_LIMITATIONS registers an enriched error"
            )
        data = {
            "ctx": ["AU", "US", "CN"],
            "allowed": [["AU", "NZ"], ["US", "CA"], ["JP", "KR"]],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual == [1, 1, -1], (
            f"[{backend_name}] Expected [1, 1, -1], got {actual}"
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
hatch run test:test-target-quick tests/cross_backend/test_ternary_is_in_list_column.py::TestTIsInListColumn::test_t_is_in_list_column_happy_path -v
```
Expected: **FAIL** on at least `polars` with `TypeError: not yet implemented: Nested object types` (or similar). `narwhals-pandas` should xfail-pass or fail — acceptable either way at this stage.

- [ ] **Step 3: Commit the red test**

```bash
git add tests/cross_backend/test_ternary_is_in_list_column.py
git commit -m "test(ternary): add failing cross-backend test for t_is_in on list column

Ref mountainash-expressions#75"
```

---

## Task 2: API builder — stop wrapping single expressions in LIST

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_ternary.py:191-233`

- [ ] **Step 1: Read the current implementation**

Look at lines 191–233. Current `t_is_in` unconditionally wraps `value_nodes` inside a `LIST` ScalarFunctionNode even when `values` is a single expression (producing `LIST[col_ref]`, which the visitor then compiles to a Python list containing a `pl.Expr`).

- [ ] **Step 2: Replace `t_is_in` with the new implementation**

Replace the method body (currently lines 191–211) with:

```python
    def t_is_in(
        self,
        values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary membership check. Returns -1/0/1.

        `values` may be a Python list/tuple/set (literal collection, baked in
        at build time) or a single expression. When the expression resolves to
        a list-typed column at compile time, each backend compiles the operation
        as per-row `list.contains(element)`; scalar expressions keep today's
        `element == value` semantics.
        """
        left_unknown = getattr(self._node, "unknown_values", None)
        options = {"unknown_values": frozenset(left_unknown)} if left_unknown else {}

        if isinstance(values, (list, tuple, set)):
            # Literal path — wrap in LIST node; visitor will extract raw values.
            collection_arg: "ExpressionNode" = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST,
                arguments=[LiteralNode(value=v) for v in values],
            )
        else:
            # Expression path — pass through raw. Visitor compiles normally;
            # the backend distinguishes list-literal vs compiled-Expr arguments
            # via `isinstance` at its own boundary.
            collection_arg = self._to_substrait_node(values)

        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN,
            arguments=[self._node, collection_arg],
            options=options,
        )
        return self._build(node)
```

- [ ] **Step 3: Replace `t_is_not_in` with the mirror**

Replace lines 213–233 with:

```python
    def t_is_not_in(
        self,
        values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Ternary non-membership check. Returns -1/0/1.

        Mirror of `t_is_in`. See its docstring for `values` semantics.
        """
        left_unknown = getattr(self._node, "unknown_values", None)
        options = {"unknown_values": frozenset(left_unknown)} if left_unknown else {}

        if isinstance(values, (list, tuple, set)):
            collection_arg: "ExpressionNode" = ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST,
                arguments=[LiteralNode(value=v) for v in values],
            )
        else:
            collection_arg = self._to_substrait_node(values)

        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_NOT_IN,
            arguments=[self._node, collection_arg],
            options=options,
        )
        return self._build(node)
```

- [ ] **Step 4: Run the red test — still fails, but now inside the backend, not the builder**

Run:
```bash
hatch run test:test-target-quick tests/cross_backend/test_ternary_is_in_list_column.py::TestTIsInListColumn::test_t_is_in_list_column_happy_path -v
```
Expected: **FAIL** — but the error now surfaces from inside each backend's `t_is_in` method (receiving a `pl.Expr` / `ibis.Expr` / `nw.Expr` in place of a Python list). The Polars error typically becomes a `.is_in()` type error or nested-object error. This confirms the AST change took effect.

- [ ] **Step 5: Run the existing ternary test suite — no regressions**

Run:
```bash
hatch run test:test-target-quick tests/cross_backend/test_ternary.py tests/cross_backend/test_ternary_auto_booleanize.py tests/cross_backend/test_t_col.py -v
```
Expected: **PASS** — literal-list path still works on every backend because we still wrap `list`/`tuple`/`set` in a `LIST` node.

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_ternary.py
git commit -m "refactor(ternary): pass expression args through without LIST wrapper

For t_is_in/t_is_not_in, only wrap literal Python collections in the
LIST AST node. Expression arguments flow through raw so backends can
type-dispatch list-literal vs compiled-Expr at their own boundary."
```

---

## Task 3: Protocol — widen `collection` type hint

**Files:**
- Modify: `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_ternary.py:93-109`

- [ ] **Step 1: Update the protocol signatures**

Replace the `t_is_in` and `t_is_not_in` method stubs (lines 93–109) with:

```python
    def t_is_in(
        self,
        element: ExpressionT,
        collection: Collection[Any] | ExpressionT,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary membership test - returns -1/0/1.

        `collection` is either a Python collection of literal values (the
        historical literal-list path) or a backend expression (new: per-row
        list-column membership). Backends dispatch on the Python type.
        """
        ...

    def t_is_not_in(
        self,
        element: ExpressionT,
        collection: Collection[Any] | ExpressionT,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary non-membership test - returns -1/0/1.

        See `t_is_in` for `collection` semantics.
        """
        ...
```

- [ ] **Step 2: Run type-check on the protocol file**

Run:
```bash
hatch run mypy:check src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_ternary.py 2>&1 | tail -20
```
Expected: no new errors introduced by the edit.

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_ternary.py
git commit -m "refactor(ternary): widen t_is_in protocol collection type to allow expression"
```

---

## Task 4: Polars backend — type-dispatch on `collection`

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_ternary.py:196-232`

- [ ] **Step 1: Update `t_is_in`**

Replace the method (lines 196–213) with:

```python
    def t_is_in(
        self,
        element: PolarsExpr,
        collection: Collection[Any] | pl.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary membership test - returns -1/0/1.

        `collection` is either a Python list/tuple/set (literal path) or a
        Polars expression resolving to a list-typed column (per-row path).
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, pl.Expr):
            # Expression path: assume list-typed column. If it isn't, Polars
            # raises at collect time with its own clear error.
            membership = collection.list.contains(element)
        else:
            membership = element.is_in(collection)

        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(membership)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )
```

- [ ] **Step 2: Update `t_is_not_in`**

Replace the method (lines 215–232) with:

```python
    def t_is_not_in(
        self,
        element: PolarsExpr,
        collection: Collection[Any] | pl.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary non-membership test - returns -1/0/1.

        Mirror of `t_is_in`. See its docstring.
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, pl.Expr):
            membership = collection.list.contains(element)
        else:
            membership = element.is_in(collection)

        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(~membership)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )
```

- [ ] **Step 3: Run the red test — should pass on Polars**

Run:
```bash
hatch run test:test-target-quick "tests/cross_backend/test_ternary_is_in_list_column.py::TestTIsInListColumn::test_t_is_in_list_column_happy_path[polars]" -v
```
Expected: **PASS** on `polars`.

- [ ] **Step 4: Run all existing Polars ternary tests — no regressions**

Run:
```bash
hatch run test:test-target-quick "tests/cross_backend/test_ternary.py" "tests/cross_backend/test_ternary_auto_booleanize.py" "tests/cross_backend/test_t_col.py" -k polars -v
```
Expected: **PASS** on every selected test.

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_ternary.py
git commit -m "feat(ternary-polars): support list-column arg in t_is_in/t_is_not_in

Type-dispatch on collection at the Python boundary: Python list keeps
today's element.is_in(literals) path; pl.Expr triggers per-row
list.contains(element)."
```

---

## Task 5: Ibis backend — type-dispatch on `collection`

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_ternary.py:194-222`

- [ ] **Step 1: Update `t_is_in`**

Replace the method (lines 194–207) with:

```python
    def t_is_in(
        self,
        element: IbisValueExpr,
        collection: Collection[Any] | Any,   # "Any" covers ibis Expr subtypes
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary membership test - returns -1/0/1.

        `collection` is either a Python collection (literal path) or an Ibis
        array/list-valued expression (per-row path).
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, ibis.expr.types.Expr):
            # Array-column path: Ibis `array.contains(element)`.
            membership = collection.contains(element)
        else:
            membership = element.isin(collection)

        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(membership, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))
        )
```

- [ ] **Step 2: Update `t_is_not_in`**

Replace the method (lines 209–222) with:

```python
    def t_is_not_in(
        self,
        element: IbisValueExpr,
        collection: Collection[Any] | Any,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary non-membership test - returns -1/0/1.

        Mirror of `t_is_in`.
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, ibis.expr.types.Expr):
            membership = collection.contains(element)
        else:
            membership = element.isin(collection)

        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(~membership, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))
        )
```

- [ ] **Step 3: Run the red test on every Ibis backend**

Run:
```bash
hatch run test:test-target-quick "tests/cross_backend/test_ternary_is_in_list_column.py::TestTIsInListColumn::test_t_is_in_list_column_happy_path" -k "ibis" -v
```
Expected: **PASS** on `ibis-duckdb`, `ibis-sqlite`, `ibis-polars`.

Note: if `ibis-sqlite` fails because SQLite has no native array type, accept it as a known divergence and mark it `xfail` in Task 7's test expansion rather than forcing it here. Keep the test running against the other two.

- [ ] **Step 4: Run existing Ibis ternary tests**

Run:
```bash
hatch run test:test-target-quick "tests/cross_backend/test_ternary.py" "tests/cross_backend/test_t_col.py" -k "ibis" -v
```
Expected: **PASS** — no regressions on literal-list path.

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_ternary.py
git commit -m "feat(ternary-ibis): support array-column arg in t_is_in/t_is_not_in

Ibis carries types natively; when collection is an ibis Expr, use
collection.contains(element) for per-row array membership."
```

---

## Task 6: Narwhals backend — type-dispatch + KNOWN_EXPR_LIMITATIONS

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_ternary.py:197-233`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/base.py` (add two registry rows)

- [ ] **Step 1: Update narwhals `t_is_in`**

Replace the method (lines 197–214) with:

```python
    def t_is_in(
        self,
        element: NarwhalsExpr,
        collection: Collection[Any] | nw.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary membership test - returns -1/0/1.

        `collection` is a Python collection (literal path) or a narwhals
        expression resolving to a list-typed column (per-row path).
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, nw.Expr):
            membership = collection.list.contains(element)
        else:
            membership = element.is_in(collection)

        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(membership)
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )
```

- [ ] **Step 2: Update narwhals `t_is_not_in`**

Replace the method (lines 216–233) with:

```python
    def t_is_not_in(
        self,
        element: NarwhalsExpr,
        collection: Collection[Any] | nw.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary non-membership test - returns -1/0/1.

        Mirror of `t_is_in`.
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, nw.Expr):
            membership = collection.list.contains(element)
        else:
            membership = element.is_in(collection)

        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(~membership)
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )
```

- [ ] **Step 3: Register narwhals-pandas limitation**

Open `src/mountainash/expressions/backends/expression_systems/narwhals/base.py`. Near the existing `KNOWN_EXPR_LIMITATIONS` block (search for `_NW_STRING_LITERAL_ONLY`), add immediately above the `KNOWN_EXPR_LIMITATIONS` dict literal:

```python
    _NW_LIST_CONTAINS_LIMITED = KnownLimitation(
        message=(
            "narwhals does not support list-column membership on all native "
            "backends (narwhals-pandas in particular). Use polars or an ibis "
            "backend, or pass a literal list/tuple/set as the t_is_in argument."
        ),
        spec_ref="e.cross-backend/known-divergences.md",
        workaround="Use a literal collection, the polars backend, or an ibis backend",
    )
```

Then add these two rows to the `KNOWN_EXPR_LIMITATIONS` dict literal (after the existing ternary-related entries, or alphabetically near other `FK_MA_*` keys):

```python
        (FK_MA_TERN.T_IS_IN,     "collection"): _NW_LIST_CONTAINS_LIMITED,
        (FK_MA_TERN.T_IS_NOT_IN, "collection"): _NW_LIST_CONTAINS_LIMITED,
```

At the top of the file, ensure this import exists (add if missing):

```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_MA_TERN,
)
```

- [ ] **Step 4: Run the red test on narwhals backends**

Run:
```bash
hatch run test:test-target-quick "tests/cross_backend/test_ternary_is_in_list_column.py::TestTIsInListColumn::test_t_is_in_list_column_happy_path" -k "narwhals" -v
```
Expected: **PASS** on `narwhals-polars`; **XFAIL** on `narwhals-pandas`.

- [ ] **Step 5: Run existing narwhals ternary tests — no regressions**

Run:
```bash
hatch run test:test-target-quick "tests/cross_backend/test_ternary.py" "tests/cross_backend/test_t_col.py" -k "narwhals" -v
```
Expected: **PASS**.

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_ternary.py src/mountainash/expressions/backends/expression_systems/narwhals/base.py
git commit -m "feat(ternary-narwhals): support list-column arg + register nw-pandas gap

narwhals-polars supports collection.list.contains; narwhals-pandas
does not, so register KNOWN_EXPR_LIMITATIONS for both T_IS_IN and
T_IS_NOT_IN so users get an enriched error with spec guidance."
```

---

## Task 7: Expand cross-backend test coverage

**Files:**
- Modify: `tests/cross_backend/test_ternary_is_in_list_column.py`

- [ ] **Step 1: Add null-row test**

Append to the `TestTIsInListColumn` class:

```python
    def test_t_is_in_null_list_row_is_unknown(self, backend_name, backend_factory, collect_expr):
        """Row where the list column is null → ternary UNKNOWN (0)."""
        if backend_name == "narwhals-pandas":
            pytest.xfail("narwhals-pandas list-column gap")
        data = {
            "ctx": ["AU", "US"],
            "allowed": [["AU", "NZ"], None],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual[0] == 1, f"[{backend_name}] row 0 expected 1, got {actual[0]!r}"
        assert actual[1] == 0, f"[{backend_name}] row 1 expected 0 (UNKNOWN), got {actual[1]!r}"
```

- [ ] **Step 2: Add sentinel-scalar test**

Append:

```python
    def test_t_is_in_sentinel_ctx_is_unknown(self, backend_name, backend_factory, collect_expr):
        """When ctx matches an unknown_values sentinel, result is UNKNOWN."""
        if backend_name == "narwhals-pandas":
            pytest.xfail("narwhals-pandas list-column gap")
        data = {
            "ctx": ["AU", "<NA>", "US"],
            "allowed": [["AU"], ["AU"], ["AU"]],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx", unknown={"<NA>"}).t_is_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual == [1, 0, -1], (
            f"[{backend_name}] Expected [1, 0, -1], got {actual}"
        )
```

- [ ] **Step 3: Add `t_is_not_in` mirror test**

Append:

```python
    def test_t_is_not_in_list_column(self, backend_name, backend_factory, collect_expr):
        """Mirror of happy path for t_is_not_in."""
        if backend_name == "narwhals-pandas":
            pytest.xfail("narwhals-pandas list-column gap")
        data = {
            "ctx": ["AU", "US", "CN"],
            "allowed": [["AU", "NZ"], ["US", "CA"], ["JP", "KR"]],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_not_in(ma.col("allowed"))
        actual = collect_expr(df, expr)
        assert actual == [-1, -1, 1], (
            f"[{backend_name}] Expected [-1, -1, 1], got {actual}"
        )
```

- [ ] **Step 4: Add literal-list regression test**

Append:

```python
    def test_t_is_in_literal_list_still_works(self, backend_name, backend_factory, collect_expr):
        """Regression guard: literal-list path unchanged by this refactor."""
        data = {"ctx": ["AU", "US", "CN"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("ctx").t_is_in(["AU", "US"])
        actual = collect_expr(df, expr)
        assert actual == [1, 1, -1], (
            f"[{backend_name}] Expected [1, 1, -1], got {actual}"
        )
```

- [ ] **Step 5: Run the full new test module**

Run:
```bash
hatch run test:test-target-quick tests/cross_backend/test_ternary_is_in_list_column.py -v
```
Expected: every test passes on `polars`, `pandas` (via direct polars read), `narwhals-polars`, `ibis-polars`, `ibis-duckdb`, `ibis-sqlite`; `narwhals-pandas` xfails on the four list-column tests; literal-list regression passes on every backend including `narwhals-pandas`.

If `ibis-sqlite` fails the list-column tests (SQLite has no array type), add `if backend_name == "ibis-sqlite": pytest.xfail("SQLite has no native array type")` to the affected tests, and note it in the commit message.

- [ ] **Step 6: Commit**

```bash
git add tests/cross_backend/test_ternary_is_in_list_column.py
git commit -m "test(ternary): add null-row, sentinel, t_is_not_in, and regression tests"
```

---

## Task 8: Full-suite verification

- [ ] **Step 1: Run the entire expressions + relations + cross-backend suite**

Run:
```bash
hatch run test:test-target-quick tests/expressions/ tests/relations/ tests/cross_backend/ 2>&1 | tail -40
```
Expected: green summary with the same `xfailed` / `xpassed` counts as `develop` baseline **plus** the new xfails from this change (`narwhals-pandas` on four tests, possibly `ibis-sqlite` on four tests). No new `failed`.

- [ ] **Step 2: Run ruff**

Run:
```bash
hatch run ruff:check src/mountainash/expressions/ tests/cross_backend/test_ternary_is_in_list_column.py
```
Expected: zero new issues. If import-ordering or type-hint-style nits appear, `hatch run ruff:fix` on the same paths and re-commit.

- [ ] **Step 3: Run mypy on touched files**

Run:
```bash
hatch run mypy:check src/mountainash/expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_ternary.py src/mountainash/expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_ternary.py src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_ternary.py src/mountainash/expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_ternary.py 2>&1 | tail -20
```
Expected: no new errors attributable to this change (pre-existing unrelated errors are acceptable).

- [ ] **Step 4: Final commit if any lint/type fixes were needed**

```bash
git add -u
git commit -m "chore(ternary): ruff/mypy cleanup for t_is_in list-column change" || echo "nothing to commit"
```

---

## Notes for the implementer

- **Why no visitor change is needed.** The unified visitor (`src/mountainash/expressions/core/unified_visitor/visitor.py:308`) only applies raw-value extraction to function keys in `_raw_value_functions` — which includes `FKEY_MOUNTAINASH_SCALAR_TERNARY.LIST` but not `T_IS_IN` itself. For the literal path, the `LIST` node still triggers raw extraction → Python list reaches the backend. For the expression path, the raw `FieldReferenceNode` is visited via the normal `self.visit(arg)` branch → compiled `Expr` reaches the backend. Both cases flow through the existing visitor code unchanged.

- **Why `isinstance` dispatch is safe.** Polars, Ibis, and Narwhals all have a single backend-native expression type (`pl.Expr`, `ibis.expr.types.Expr`, `nw.Expr`). A Python `list`/`tuple`/`set` can never be an instance of those types, so the branch is unambiguous. No dtype introspection. No schema peek.

- **Why the API builder keeps the `LIST` wrapper for literal collections.** The existing visitor machinery (`_raw_value_functions` + `collect_values`) expects `LIST(LiteralNode, ...)` as the marker for "unwrap these as raw Python values". Stripping the wrapper for literals too would require rewriting the visitor. YAGNI — the wrapper is harmless.

- **If `ibis-sqlite` can't compile `array.contains`.** SQLite has no native array type; Ibis may refuse to compile the operation at all. If the test fails there, add a targeted `xfail` inside each list-column test (`if backend_name == "ibis-sqlite"`) with a "SQLite has no native array type" reason. Do not register it in `KNOWN_EXPR_LIMITATIONS` — the Ibis backend class is shared across all Ibis engines, so a registry entry would spuriously trigger on DuckDB too.

- **Downstream follow-up.** After this lands, the `mountainash-utils-rules` repo can drop its `ma.native(pl.col(...).list.contains(...))` workarounds in `_compile_set_membership` / `_compile_set_exclusion` and flip its strict xfails. That work is a separate PR in a separate repo — out of scope for this plan.
