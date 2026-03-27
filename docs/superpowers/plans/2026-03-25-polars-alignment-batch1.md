# Polars Alignment Batch 1: Bug Fixes, Aliases, Arithmetic Essentials

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 2 known bugs, add Polars-compatible naming aliases in extension builders, and wire up arithmetic essentials (abs, sqrt, sign, exp, negate) that already have backend implementations.

**Architecture:** The full pipeline for each operation is: enum value → function mapping definition → API builder method → backend implementations → tests. For the arithmetic essentials, protocols and backends are already implemented — we only need to uncomment enums, add function mappings, and implement API builder methods. Aliases use direct AST construction in extension builders (no `self._api` — `BaseExpressionAPIBuilder` only has `_node`). `clip()` is deferred to a future batch.

**Tech Stack:** Python, pytest, hatch

**Task dependencies:** Task 2 (negate) must complete before Task 3 (aliases), because the `neg` alias depends on negate being wired up.

---

## File Map

**Bug fixes:**
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_comparison.py` (LTEAST typo)
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py` (uncomment negate)
- Modify: `src/mountainash_expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_arithmetic.py` (uncomment negate protocol)
- Modify: `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py` (uncomment negate mapping)
- Modify: `src/mountainash_expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_arithmetic.py` (uncomment negate)
- Modify: `src/mountainash_expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_arithmetic.py` (uncomment negate)
- Modify: `src/mountainash_expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_arithmetic.py` (uncomment negate)

**Aliases:**
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_arithmetic.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_string.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_comparison.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py`
- Modify: `src/mountainash_expressions/core/expression_api/boolean.py` (compose StringAPIBuilder, add comparison extension to imports and _FLAT_NAMESPACES)

**Arithmetic essentials:**
- Modify: `src/mountainash_expressions/core/expression_system/function_keys/enums.py` (uncomment ABS, SIGN, SQRT, EXP)
- Modify: `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py` (add ABS, SIGN, SQRT, EXP mappings)
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py` (implement abs, sqrt, sign, exp builder methods)

**Tests:**
- Create: `tests/cross_backend/test_arithmetic_essentials.py`
- Create: `tests/unit/test_polars_aliases.py`
- Create: `tests/cross_backend/test_negate.py`
- Create: `tests/cross_backend/test_least.py`

---

## Task 1: Fix LTEAST Typo

**Files:**
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_comparison.py:431,455`
- Create: `tests/cross_backend/test_least.py`

- [ ] **Step 1: Write test for least()**

Create `tests/cross_backend/test_least.py`:

```python
"""Cross-backend tests for least() and least_skip_null()."""

import pytest
import mountainash_expressions as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLeast:
    def test_least_two_columns(self, backend_name, backend_factory, select_and_extract):
        """Test least() returns the smaller of two columns."""
        data = {"a": [10, 5, 30], "b": [20, 3, 25]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").least(ma.col("b"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, 3, 25], f"[{backend_name}] got {actual}"

    def test_least_three_columns(self, backend_name, backend_factory, select_and_extract):
        """Test least() with three arguments."""
        data = {"a": [10, 50, 30], "b": [20, 3, 25], "c": [15, 10, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").least(ma.col("b"), ma.col("c"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, 3, 5], f"[{backend_name}] got {actual}"
```

- [ ] **Step 2: Run test to verify it fails with AttributeError**

Run: `hatch run test:test-target tests/cross_backend/test_least.py -v`
Expected: FAIL with `AttributeError: type object 'FKEY_SUBSTRAIT_SCALAR_COMPARISON' has no attribute 'LTEAST'`

- [ ] **Step 3: Fix the typo**

In `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_comparison.py`:

Line 431: Change `FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTEAST` to `FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST`

Line 455: Change `FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTEAST_SKIP_NULL` to `FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST_SKIP_NULL`

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run test:test-target tests/cross_backend/test_least.py -v`
Expected: PASS (all backends have `least` implementations)

- [ ] **Step 5: Commit**

```bash
git add src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_comparison.py tests/cross_backend/test_least.py
git commit -m "fix: correct LTEAST typo to LEAST in comparison builder"
```

---

## Task 2: Wire Up negate() End-to-End

Negate requires uncommenting code in **6 locations**: protocol, API builder, function mapping, and all 3 backends.

**Files:**
- Modify: `src/mountainash_expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_arithmetic.py:61-67`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py:261-278`
- Modify: `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py:335-341`
- Modify: `src/mountainash_expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_arithmetic.py:156-171`
- Modify: `src/mountainash_expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_arithmetic.py:157-172`
- Modify: `src/mountainash_expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_arithmetic.py:158-173`
- Create: `tests/cross_backend/test_negate.py`

- [ ] **Step 1: Write test for negate**

Create `tests/cross_backend/test_negate.py`:

```python
"""Cross-backend tests for negate() and __neg__ operator."""

import pytest
import mountainash_expressions as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNegate:
    def test_negate_method(self, backend_name, backend_factory, select_and_extract):
        """Test negate() method on numeric column."""
        data = {"val": [10, -5, 0, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").negate()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [-10, 5, 0, -3], f"[{backend_name}] got {actual}"

    def test_neg_operator(self, backend_name, backend_factory, select_and_extract):
        """Test Python -expr operator (calls __neg__ -> negate())."""
        data = {"val": [10, -5, 0, 3]}
        df = backend_factory.create(data, backend_name)

        expr = -ma.col("val")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [-10, 5, 0, -3], f"[{backend_name}] got {actual}"

    def test_negate_in_expression(self, backend_name, backend_factory, select_and_extract):
        """Test negate composed with arithmetic."""
        data = {"val": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = (-ma.col("val")).add(100)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [90, 80, 70], f"[{backend_name}] got {actual}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/cross_backend/test_negate.py -v`
Expected: FAIL with `AttributeError` (negate method not found)

- [ ] **Step 3: Uncomment negate in protocol**

In `src/mountainash_expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_arithmetic.py`, uncomment lines 61-67 (the `negate` protocol method). This must be done FIRST because the function mapping definition references `SubstraitScalarArithmeticExpressionSystemProtocol.negate`.

- [ ] **Step 4: Uncomment negate in API builder**

In `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py`, uncomment lines 261-278.

- [ ] **Step 5: Uncomment negate in function mapping definitions**

In `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py`, uncomment lines 335-341.

- [ ] **Step 6: Uncomment negate in all 3 backends**

Uncomment the `negate` method in:
- `src/mountainash_expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_arithmetic.py` (lines 156-171)
- `src/mountainash_expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_arithmetic.py` (lines 157-172)
- `src/mountainash_expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_arithmetic.py` (lines 158-173)

- [ ] **Step 7: Run test to verify it passes**

Run: `hatch run test:test-target tests/cross_backend/test_negate.py -v`
Expected: PASS on all backends

- [ ] **Step 8: Run full test suite to check for regressions**

Run: `hatch run test:test-quick`
Expected: No new failures

- [ ] **Step 9: Commit**

```bash
git add src/mountainash_expressions/core/expression_protocols/expression_systems/substrait/prtcl_expsys_scalar_arithmetic.py \
        src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py \
        src/mountainash_expressions/core/expression_system/function_mapping/definitions.py \
        src/mountainash_expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_arithmetic.py \
        src/mountainash_expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_arithmetic.py \
        src/mountainash_expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_arithmetic.py \
        tests/cross_backend/test_negate.py
git commit -m "fix: wire up negate() end-to-end, fixing broken __neg__ operator"
```

---

## Task 3: Add Polars Naming Aliases in Extension Builders

**Key architectural facts (verified):**
- `BaseExpressionAPIBuilder` has only `_node` (via `__slots__`). No `_api` attribute exists.
- Aliases must use **direct AST node construction** (same pattern as existing builder methods like `floor_divide`).
- `.str` namespace currently uses only `SubstraitScalarStringAPIBuilder`. Must create a composed `StringAPIBuilder` (like `DatetimeAPIBuilder`).
- `MountainAshScalarComparisonAPIBuilder` is not imported or in `_FLAT_NAMESPACES`. Must add it.
- `.dt` and `.name` already compose extension builders — aliases there are simple class-level assignments.
- `neg` alias depends on Task 2 completing first.

**Files:**
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_arithmetic.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_string.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_datetime.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_comparison.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py`
- Modify: `src/mountainash_expressions/core/expression_api/boolean.py` (compose StringAPIBuilder, add MountainAshScalarComparisonAPIBuilder to imports and _FLAT_NAMESPACES)
- Create: `tests/unit/test_polars_aliases.py`

- [ ] **Step 1: Write test for aliases**

Create `tests/unit/test_polars_aliases.py`:

```python
"""Unit tests verifying Polars-compatible aliases resolve to the same methods."""

import mountainash_expressions as ma


class TestArithmeticAliases:
    """Polars-style short names for arithmetic operations."""

    def test_sub_alias(self):
        expr = ma.col("a").sub(ma.col("b"))
        assert expr is not None

    def test_mul_alias(self):
        expr = ma.col("a").mul(ma.col("b"))
        assert expr is not None

    def test_truediv_alias(self):
        expr = ma.col("a").truediv(ma.col("b"))
        assert expr is not None

    def test_floordiv_alias(self):
        expr = ma.col("a").floordiv(ma.col("b"))
        assert expr is not None

    def test_mod_alias(self):
        expr = ma.col("a").mod(ma.col("b"))
        assert expr is not None

    def test_pow_alias(self):
        expr = ma.col("a").pow(ma.col("b"))
        assert expr is not None

    def test_neg_alias(self):
        expr = ma.col("a").neg()
        assert expr is not None


class TestStringAliases:
    """Polars-style names for string operations."""

    def test_to_uppercase(self):
        expr = ma.col("a").str.to_uppercase()
        assert expr is not None

    def test_to_lowercase(self):
        expr = ma.col("a").str.to_lowercase()
        assert expr is not None

    def test_strip_chars(self):
        expr = ma.col("a").str.strip_chars()
        assert expr is not None

    def test_strip_chars_start(self):
        expr = ma.col("a").str.strip_chars_start()
        assert expr is not None

    def test_strip_chars_end(self):
        expr = ma.col("a").str.strip_chars_end()
        assert expr is not None

    def test_len_chars(self):
        expr = ma.col("a").str.len_chars()
        assert expr is not None


class TestDatetimeAliases:
    """Polars-style names for datetime operations."""

    def test_week(self):
        expr = ma.col("a").dt.week()
        assert expr is not None

    def test_weekday(self):
        expr = ma.col("a").dt.weekday()
        assert expr is not None

    def test_ordinal_day(self):
        expr = ma.col("a").dt.ordinal_day()
        assert expr is not None


class TestComparisonAliases:
    """Polars-style names for comparison operations."""

    def test_is_between(self):
        expr = ma.col("a").is_between(1, 10)
        assert expr is not None


class TestNameAliases:
    """Polars-style names for .name operations."""

    def test_to_lowercase(self):
        expr = ma.col("a").name.to_lowercase()
        assert expr is not None

    def test_to_uppercase(self):
        expr = ma.col("a").name.to_uppercase()
        assert expr is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/unit/test_polars_aliases.py -v`
Expected: FAIL — aliases don't exist yet

- [ ] **Step 3: Add arithmetic aliases using direct AST construction**

In `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_arithmetic.py`, after the existing `rfloor_divide` method, add:

```python
    # ========================================
    # Polars-compatible aliases
    # ========================================
    # These use direct AST construction (same pattern as floor_divide).
    # Defined here (not in Substrait builders) because aliases are not
    # part of the Substrait standard.

    def sub(self, other) -> BaseExpressionAPI:
        """Alias for subtract() — Polars compatibility."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def mul(self, other) -> BaseExpressionAPI:
        """Alias for multiply() — Polars compatibility."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def truediv(self, other) -> BaseExpressionAPI:
        """Alias for divide() — Polars compatibility."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    floordiv = floor_divide  # Already in this builder

    def mod(self, other) -> BaseExpressionAPI:
        """Alias for modulus() — Polars compatibility."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def pow(self, other) -> BaseExpressionAPI:
        """Alias for power() — Polars compatibility."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def neg(self) -> BaseExpressionAPI:
        """Alias for negate() — Polars compatibility."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
            arguments=[self._node],
        )
        return self._build(node)
```

Ensure `FKEY_SUBSTRAIT_SCALAR_ARITHMETIC` and `ScalarFunctionNode` are imported at the top of the file. Check existing imports — `floor_divide` already uses these, so they should be present.

- [ ] **Step 4: Create composed StringAPIBuilder and add string aliases**

First, update `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_string.py`. Replace the stub with methods using direct AST construction:

```python
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING
from mountainash_expressions.core.expression_nodes.substrait.exn_scalar_function import ScalarFunctionNode


class MountainAshScalarStringAPIBuilder(BaseExpressionAPIBuilder):
    """Extension API builder for Mountainash string operations.

    Provides Polars-compatible aliases for Substrait-named string methods.
    """

    def to_uppercase(self) -> BaseExpressionAPI:
        """Alias for upper() — Polars compatibility."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER,
            arguments=[self._node],
        )
        return self._build(node)

    def to_lowercase(self) -> BaseExpressionAPI:
        """Alias for lower() — Polars compatibility."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LOWER,
            arguments=[self._node],
        )
        return self._build(node)

    def strip_chars(self, characters=None) -> BaseExpressionAPI:
        """Alias for trim() — Polars compatibility."""
        args = [self._node]
        if characters is not None:
            args.append(self._to_substrait_node(characters))
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.TRIM,
            arguments=args,
        )
        return self._build(node)

    def strip_chars_start(self, characters=None) -> BaseExpressionAPI:
        """Alias for ltrim() — Polars compatibility."""
        args = [self._node]
        if characters is not None:
            args.append(self._to_substrait_node(characters))
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.LTRIM,
            arguments=args,
        )
        return self._build(node)

    def strip_chars_end(self, characters=None) -> BaseExpressionAPI:
        """Alias for rtrim() — Polars compatibility."""
        args = [self._node]
        if characters is not None:
            args.append(self._to_substrait_node(characters))
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.RTRIM,
            arguments=args,
        )
        return self._build(node)

    def len_chars(self) -> BaseExpressionAPI:
        """Alias for char_length() — Polars compatibility."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CHAR_LENGTH,
            arguments=[self._node],
        )
        return self._build(node)
```

Then, in `src/mountainash_expressions/core/expression_api/boolean.py`, create a composed `StringAPIBuilder` (following the `DatetimeAPIBuilder` pattern near line 48-53):

```python
class StringAPIBuilder(
    MountainAshScalarStringAPIBuilder,   # Polars aliases
    SubstraitScalarStringAPIBuilder,      # Substrait methods
):
    """Unified string builder for the .str namespace."""
    pass
```

And update the `str` descriptor (line 124) from:
```python
str = NamespaceDescriptor(SubstraitScalarStringAPIBuilder)
```
to:
```python
str = NamespaceDescriptor(StringAPIBuilder)
```

Add the import for `MountainAshScalarStringAPIBuilder` to the extension imports block.

- [ ] **Step 5: Add comparison extension to _FLAT_NAMESPACES**

In `src/mountainash_expressions/core/expression_api/boolean.py`:

Add `MountainAshScalarComparisonAPIBuilder` to the extension imports block (around line 15-24).

Add it to `_FLAT_NAMESPACES` tuple — insert after `MountainAshScalarBooleanAPIBuilder`:
```python
MountainAshScalarComparisonAPIBuilder,
```

- [ ] **Step 6: Add comparison alias using direct AST construction**

In `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_comparison.py`:

```python
from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON
from mountainash_expressions.core.expression_nodes.substrait.exn_scalar_function import ScalarFunctionNode


class MountainAshScalarComparisonAPIBuilder(BaseExpressionAPIBuilder):
    """Extension API builder for Mountainash comparison operations.

    Provides Polars-compatible aliases.
    """

    def is_between(self, low, high, closed="both") -> BaseExpressionAPI:
        """Alias for between() — Polars compatibility."""
        low_node = self._to_substrait_node(low)
        high_node = self._to_substrait_node(high)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN,
            arguments=[self._node, low_node, high_node],
            options={"closed": closed},
        )
        return self._build(node)
```

- [ ] **Step 7: Add datetime aliases**

In `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_datetime.py`, at the end of the class, add class-level assignments (these work because all methods are in the same class):

```python
    # ========================================
    # Polars-compatible aliases
    # ========================================

    week = week_of_year
    weekday = day_of_week
    ordinal_day = day_of_year
    convert_time_zone = to_timezone
    replace_time_zone = assume_timezone
    epoch = unix_timestamp
```

- [ ] **Step 8: Add name aliases**

In `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py`, at the end of the class:

```python
    # ========================================
    # Polars-compatible aliases
    # ========================================

    to_lowercase = name_to_lower
    to_uppercase = name_to_upper
```

- [ ] **Step 9: Run alias tests**

Run: `hatch run test:test-target tests/unit/test_polars_aliases.py -v`
Expected: PASS

- [ ] **Step 10: Run full test suite**

Run: `hatch run test:test-quick`
Expected: No new failures (especially verify existing `.str` tests still pass after the composition change)

- [ ] **Step 11: Commit**

```bash
git add src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/ \
        src/mountainash_expressions/core/expression_api/boolean.py \
        tests/unit/test_polars_aliases.py
git commit -m "feat: add Polars-compatible naming aliases in extension builders"
```

---

## Task 4: Wire Up Arithmetic Essentials (abs, sqrt, sign, exp)

**Files:**
- Modify: `src/mountainash_expressions/core/expression_system/function_keys/enums.py:166-169`
- Modify: `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py:283-318`
- Create: `tests/cross_backend/test_arithmetic_essentials.py`

Note: Protocol file and backend implementations already exist. Narwhals has `abs()` but `sqrt()`, `exp()`, `sign()` raise `NotImplementedError` — present failures to user per CLAUDE.md test integrity rules.

- [ ] **Step 1: Write tests**

Create `tests/cross_backend/test_arithmetic_essentials.py`:

```python
"""Cross-backend tests for arithmetic essentials: abs, sqrt, sign, exp."""

import math
import pytest
import mountainash_expressions as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAbs:
    def test_abs_positive(self, backend_name, backend_factory, select_and_extract):
        """abs() on positive values returns same values."""
        data = {"val": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [1, 2, 3], f"[{backend_name}] got {actual}"

    def test_abs_negative(self, backend_name, backend_factory, select_and_extract):
        """abs() on negative values returns positive values."""
        data = {"val": [-10, -5, 0, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, 5, 0, 3], f"[{backend_name}] got {actual}"

    def test_abs_floats(self, backend_name, backend_factory, select_and_extract):
        """abs() on floats."""
        data = {"val": [-1.5, 2.5, -3.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        for a, e in zip(actual, [1.5, 2.5, 3.0]):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] {a} != {e}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSqrt:
    def test_sqrt(self, backend_name, backend_factory, select_and_extract):
        """sqrt() on positive values."""
        data = {"val": [1.0, 4.0, 9.0, 16.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sqrt()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        for a, e in zip(actual, [1.0, 2.0, 3.0, 4.0]):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] {a} != {e}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSign:
    def test_sign(self, backend_name, backend_factory, select_and_extract):
        """sign() returns -1, 0, or 1."""
        data = {"val": [-10, 0, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sign()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [-1, 0, 1], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExp:
    def test_exp(self, backend_name, backend_factory, select_and_extract):
        """exp() computes e^x."""
        data = {"val": [0.0, 1.0, 2.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").exp()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        for a, e in zip(actual, [1.0, math.e, math.e**2]):
            assert math.isclose(a, e, abs_tol=1e-6), f"[{backend_name}] {a} != {e}"
```

Note: Tests for sqrt/sign/exp on narwhals will fail with `NotImplementedError`. Per CLAUDE.md, present failures to user rather than pre-marking as xfail. The implementer should run the tests, observe which backends fail, and ask the user how to handle (likely xfail with clear reason).

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target tests/cross_backend/test_arithmetic_essentials.py -v`
Expected: FAIL — builder methods return None (stubs with `...`)

- [ ] **Step 3: Uncomment enum values**

In `src/mountainash_expressions/core/expression_system/function_keys/enums.py`, uncomment lines 166-169:

```python
    ABS = auto()
    SIGN = auto()
    SQRT = auto()
    EXP = auto()
```

Keep `LN` commented — it's handled by the logarithmic builder separately.

- [ ] **Step 4: Add function mapping definitions**

In `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py`, after the POWER entry in the SCALAR_ARITHMETIC_FUNCTIONS list, add:

```python
    ExpressionFunctionDef(
        function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
        substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
        substrait_name="abs",
        protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.abs,
    ),
    ExpressionFunctionDef(
        function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN,
        substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
        substrait_name="sign",
        protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.sign,
    ),
    ExpressionFunctionDef(
        function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
        substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
        substrait_name="sqrt",
        protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.sqrt,
    ),
    ExpressionFunctionDef(
        function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
        substrait_uri=SubstraitExtension.SCALAR_ARITHMETIC,
        substrait_name="exp",
        protocol_method=SubstraitScalarArithmeticExpressionSystemProtocol.exp,
    ),
```

- [ ] **Step 5: Implement API builder methods**

In `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py`, replace the stub methods (lines ~283-318) with real implementations:

```python
    def abs(self, overflow: Any = None) -> BaseExpressionAPI:
        """Calculate the absolute value.

        Substrait: abs
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            arguments=[self._node],
        )
        return self._build(node)

    def sign(self) -> BaseExpressionAPI:
        """Return the sign of the value (-1, 0, or 1).

        Substrait: sign
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN,
            arguments=[self._node],
        )
        return self._build(node)

    def sqrt(self, rounding: Any = None, on_domain_error: Any = None) -> BaseExpressionAPI:
        """Square root of the value.

        Substrait: sqrt
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT,
            arguments=[self._node],
        )
        return self._build(node)

    def exp(self, rounding: Any = None) -> BaseExpressionAPI:
        """The mathematical constant e raised to the power of the value.

        Substrait: exp
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP,
            arguments=[self._node],
        )
        return self._build(node)
```

- [ ] **Step 6: Run tests and handle failures**

Run: `hatch run test:test-target tests/cross_backend/test_arithmetic_essentials.py -v`

Expected: PASS on polars, ibis-polars, ibis-duckdb, ibis-sqlite. Narwhals will fail for sqrt/sign/exp with `NotImplementedError`. Present failures to user and ask whether to xfail.

- [ ] **Step 7: Run full test suite**

Run: `hatch run test:test-quick`
Expected: No new failures beyond the known narwhals limitations

- [ ] **Step 8: Commit**

```bash
git add src/mountainash_expressions/core/expression_system/function_keys/enums.py \
        src/mountainash_expressions/core/expression_system/function_mapping/definitions.py \
        src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py \
        tests/cross_backend/test_arithmetic_essentials.py
git commit -m "feat: wire up arithmetic essentials (abs, sqrt, sign, exp)"
```

---

## Task 5: Final Verification

- [ ] **Step 1: Run full test suite with coverage**

Run: `hatch run test:test`
Expected: All tests pass, no regressions. Coverage should improve on `api_bldr_scalar_arithmetic.py` and `api_bldr_scalar_comparison.py`.

- [ ] **Step 2: Verify the protocol alignment test still passes**

Run: `hatch run test:test-target tests/unit/test_protocol_alignment.py -v`
Expected: PASS — confirms new function mappings align with protocols.

- [ ] **Step 3: Push**

```bash
git push
```
