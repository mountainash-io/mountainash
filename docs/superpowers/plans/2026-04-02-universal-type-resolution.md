# Universal Type Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a canonical type string registry (`mountainash.core.dtypes`) so that `.cast()` works identically across all backends using universal type names, then split the test file to validate both cast behavior and type resolution.

**Architecture:** New `dtypes.py` module provides `MountainashDtype` enum (16 tier-1 types), `DTYPE_ALIASES` dict (all accepted string variations), and `resolve_dtype()` normalization function. API builder and backend cast methods both call `resolve_dtype()`. Tests split into `test_cast.py` (behavior) and `test_type_resolution.py` (resolution).

**Tech Stack:** Python 3.12, Polars, Narwhals, Ibis, pytest, hatch

**Spec:** `docs/superpowers/specs/2026-04-02-universal-type-resolution-design.md`

---

### Task 1: Create `mountainash.core.dtypes` module with tests

**Files:**
- Create: `src/mountainash/core/dtypes.py`
- Create: `tests/unit/core/test_dtypes.py`

- [ ] **Step 1: Write the failing tests for `MountainashDtype` enum and `resolve_dtype()`**

Create `tests/unit/core/test_dtypes.py`:

```python
"""Unit tests for mountainash.core.dtypes — canonical type resolution."""

import pytest


class TestMountainashDtypeEnum:
    """Test that the enum has all tier-1 types and behaves as str."""

    def test_enum_is_str(self):
        from mountainash.core.dtypes import MountainashDtype
        assert isinstance(MountainashDtype.I64, str)
        assert MountainashDtype.I64 == "i64"

    def test_all_tier1_types_present(self):
        from mountainash.core.dtypes import MountainashDtype
        expected = {
            "bool", "i8", "i16", "i32", "i64",
            "u8", "u16", "u32", "u64",
            "fp32", "fp64", "string", "binary",
            "date", "time", "timestamp",
        }
        actual = {m.value for m in MountainashDtype}
        assert actual == expected

    def test_enum_usable_as_dict_key(self):
        from mountainash.core.dtypes import MountainashDtype
        d = {MountainashDtype.I64: "works"}
        assert d["i64"] == "works"


class TestResolveDtype:
    """Test resolve_dtype() normalizes all input forms to canonical strings."""

    def test_canonical_strings_pass_through(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("i64") == "i64"
        assert resolve_dtype("string") == "string"
        assert resolve_dtype("fp64") == "fp64"
        assert resolve_dtype("bool") == "bool"
        assert resolve_dtype("u32") == "u32"

    def test_polars_capitalized_aliases(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("Int64") == "i64"
        assert resolve_dtype("Float64") == "fp64"
        assert resolve_dtype("Utf8") == "string"
        assert resolve_dtype("String") == "string"
        assert resolve_dtype("Boolean") == "bool"
        assert resolve_dtype("UInt32") == "u32"

    def test_common_lowercase_aliases(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("int64") == "i64"
        assert resolve_dtype("float64") == "fp64"
        assert resolve_dtype("boolean") == "bool"
        assert resolve_dtype("uint8") == "u8"
        assert resolve_dtype("f64") == "fp64"
        assert resolve_dtype("f32") == "fp32"

    def test_python_builtin_types(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(int) == "i64"
        assert resolve_dtype(float) == "fp64"
        assert resolve_dtype(str) == "string"
        assert resolve_dtype(bool) == "bool"

    def test_enum_members(self):
        from mountainash.core.dtypes import MountainashDtype, resolve_dtype
        assert resolve_dtype(MountainashDtype.I64) == "i64"
        assert resolve_dtype(MountainashDtype.STRING) == "string"
        assert resolve_dtype(MountainashDtype.TIMESTAMP) == "timestamp"

    def test_polars_native_types_via_str(self):
        import polars as pl
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(pl.Int64) == "i64"
        assert resolve_dtype(pl.Utf8) == "string"
        assert resolve_dtype(pl.Float64) == "fp64"
        assert resolve_dtype(pl.Boolean) == "bool"
        assert resolve_dtype(pl.UInt16) == "u16"

    def test_narwhals_native_types_via_str(self):
        import narwhals as nw
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(nw.Int64) == "i64"
        assert resolve_dtype(nw.String) == "string"
        assert resolve_dtype(nw.Float64) == "fp64"
        assert resolve_dtype(nw.UInt32) == "u32"

    def test_ibis_native_types_via_str(self):
        import ibis.expr.datatypes as dt
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(dt.int64) == "i64"
        assert resolve_dtype(dt.string) == "string"
        assert resolve_dtype(dt.float64) == "fp64"
        assert resolve_dtype(dt.uint8) == "u8"

    def test_datetime_alias_maps_to_timestamp(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("Datetime") == "timestamp"
        assert resolve_dtype("timestamp") == "timestamp"

    def test_invalid_string_raises_valueerror(self):
        from mountainash.core.dtypes import resolve_dtype
        with pytest.raises(ValueError, match="Unknown dtype"):
            resolve_dtype("foobar")

    def test_empty_string_raises_valueerror(self):
        from mountainash.core.dtypes import resolve_dtype
        with pytest.raises(ValueError, match="Unknown dtype"):
            resolve_dtype("")

    def test_none_raises_valueerror(self):
        from mountainash.core.dtypes import resolve_dtype
        with pytest.raises(ValueError, match="Unknown dtype"):
            resolve_dtype(None)


class TestDtypeAliases:
    """Test that DTYPE_ALIASES covers all expected variations."""

    def test_every_canonical_name_is_in_aliases(self):
        from mountainash.core.dtypes import MountainashDtype, DTYPE_ALIASES
        for member in MountainashDtype:
            assert member.value in DTYPE_ALIASES, f"Canonical name {member.value!r} missing from DTYPE_ALIASES"

    def test_aliases_all_resolve_to_valid_enum(self):
        from mountainash.core.dtypes import MountainashDtype, DTYPE_ALIASES
        for alias, target in DTYPE_ALIASES.items():
            assert isinstance(target, MountainashDtype), f"Alias {alias!r} maps to {target!r}, not a MountainashDtype"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target-quick tests/unit/core/test_dtypes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mountainash.core.dtypes'`

- [ ] **Step 3: Implement `mountainash.core.dtypes`**

Create `src/mountainash/core/dtypes.py`:

```python
"""Canonical mountainash data type definitions.

Provides the single source of truth for type string resolution across all backends.
Every backend dtype map and the API builder normalize through this module.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class MountainashDtype(str, Enum):
    """Canonical mountainash data type identifiers.

    Tier 1: Simple types guaranteed to work across all backends.
    Substrait-aligned naming where applicable, extended with unsigned ints.
    """
    BOOL = "bool"
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    U64 = "u64"
    FP32 = "fp32"
    FP64 = "fp64"
    STRING = "string"
    BINARY = "binary"
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"


# Every accepted string variation mapped to its canonical MountainashDtype.
DTYPE_ALIASES: dict[str, MountainashDtype] = {
    # Canonical names (identity)
    "bool": MountainashDtype.BOOL,
    "i8": MountainashDtype.I8,
    "i16": MountainashDtype.I16,
    "i32": MountainashDtype.I32,
    "i64": MountainashDtype.I64,
    "u8": MountainashDtype.U8,
    "u16": MountainashDtype.U16,
    "u32": MountainashDtype.U32,
    "u64": MountainashDtype.U64,
    "fp32": MountainashDtype.FP32,
    "fp64": MountainashDtype.FP64,
    "string": MountainashDtype.STRING,
    "binary": MountainashDtype.BINARY,
    "date": MountainashDtype.DATE,
    "time": MountainashDtype.TIME,
    "timestamp": MountainashDtype.TIMESTAMP,

    # Substrait alternatives
    "boolean": MountainashDtype.BOOL,

    # Polars/Narwhals capitalized style
    "Boolean": MountainashDtype.BOOL,
    "Int8": MountainashDtype.I8,
    "Int16": MountainashDtype.I16,
    "Int32": MountainashDtype.I32,
    "Int64": MountainashDtype.I64,
    "UInt8": MountainashDtype.U8,
    "UInt16": MountainashDtype.U16,
    "UInt32": MountainashDtype.U32,
    "UInt64": MountainashDtype.U64,
    "Float32": MountainashDtype.FP32,
    "Float64": MountainashDtype.FP64,
    "Utf8": MountainashDtype.STRING,
    "String": MountainashDtype.STRING,
    "Binary": MountainashDtype.BINARY,
    "Date": MountainashDtype.DATE,
    "Time": MountainashDtype.TIME,
    "Datetime": MountainashDtype.TIMESTAMP,

    # Python type str() representations
    "int": MountainashDtype.I64,
    "float": MountainashDtype.FP64,
    "str": MountainashDtype.STRING,

    # Common lowercase aliases
    "int8": MountainashDtype.I8,
    "int16": MountainashDtype.I16,
    "int32": MountainashDtype.I32,
    "int64": MountainashDtype.I64,
    "uint8": MountainashDtype.U8,
    "uint16": MountainashDtype.U16,
    "uint32": MountainashDtype.U32,
    "uint64": MountainashDtype.U64,
    "float32": MountainashDtype.FP32,
    "float64": MountainashDtype.FP64,
    "f32": MountainashDtype.FP32,
    "f64": MountainashDtype.FP64,
}


_PYTHON_TYPE_MAP: dict[type, MountainashDtype] = {
    int: MountainashDtype.I64,
    float: MountainashDtype.FP64,
    str: MountainashDtype.STRING,
    bool: MountainashDtype.BOOL,
}


def resolve_dtype(dtype: Any) -> str:
    """Resolve any dtype specifier to a canonical mountainash type string.

    Accepts:
      - MountainashDtype enum members
      - Python built-in types (int, float, str, bool)
      - Canonical strings ("i64", "string", etc.)
      - Alias strings ("Int64", "Utf8", "int64", etc.)
      - Native backend types (pl.Int64, nw.String, ibis dt) via str() conversion

    Returns:
      Canonical type string (e.g., "i64", "string", "fp64").

    Raises:
      ValueError: If dtype cannot be resolved to a known type.
    """
    if isinstance(dtype, MountainashDtype):
        return dtype.value

    # Check bool before int — bool is a subclass of int in Python
    if isinstance(dtype, type) and dtype in _PYTHON_TYPE_MAP:
        return _PYTHON_TYPE_MAP[dtype].value

    dtype_str = str(dtype)

    if dtype_str in DTYPE_ALIASES:
        return DTYPE_ALIASES[dtype_str].value

    raise ValueError(
        f"Unknown dtype: {dtype!r} (resolved to string {dtype_str!r}). "
        f"Use a canonical type like 'i64', 'string', 'fp64', or a MountainashDtype enum."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `hatch run test:test-target-quick tests/unit/core/test_dtypes.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/core/dtypes.py tests/unit/core/test_dtypes.py
git commit -m "feat: add mountainash.core.dtypes canonical type resolution module"
```

---

### Task 2: Update API builder to use `resolve_dtype()`

**Files:**
- Modify: `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_cast.py`

- [ ] **Step 1: Run existing cast tests to confirm green baseline**

Run: `hatch run test:test-target-quick tests/cross_backend/test_type.py -v`
Expected: 129 passed, 3 xfailed (the baseline we confirmed earlier)

- [ ] **Step 2: Update the API builder**

In `src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_cast.py`, replace the ad-hoc normalization (lines 59-69):

Replace:

```python
        # Normalize dtype to string representation
        if isinstance(dtype, type):
            type_map = {
                int: "i64",
                float: "f64",
                str: "string",
                bool: "bool",
            }
            target_type = type_map.get(dtype, str(dtype))
        else:
            target_type = str(dtype)
```

With:

```python
        from mountainash.core.dtypes import resolve_dtype
        target_type = resolve_dtype(dtype)
```

- [ ] **Step 3: Run existing tests to verify no regression**

Run: `hatch run test:test-target-quick tests/cross_backend/test_type.py -v`
Expected: Same results as step 1 (129 passed, 3 xfailed)

Also run the unit tests: `hatch run test:test-target-quick tests/unit/core/test_dtypes.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/core/expression_api/api_builders/substrait/api_bldr_cast.py
git commit -m "refactor: use resolve_dtype() in cast API builder"
```

---

### Task 3: Add missing entries to backend dtype maps and add `resolve_dtype()` normalization

**Files:**
- Modify: `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_cast.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_cast.py`
- Modify: `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_cast.py`

- [ ] **Step 1: Update Polars backend dtype map**

In `expsys_pl_cast.py`, add the missing entries to `_POLARS_DTYPE_MAP`:

```python
    # Unsigned integers
    "u8": pl.UInt8,
    "u16": pl.UInt16,
    "u32": pl.UInt32,
    "u64": pl.UInt64,
    "UInt8": pl.UInt8,
    "UInt16": pl.UInt16,
    "UInt32": pl.UInt32,
    "UInt64": pl.UInt64,
    "uint8": pl.UInt8,
    "uint16": pl.UInt16,
    "uint32": pl.UInt32,
    "uint64": pl.UInt64,
    # Missing canonical names
    "binary": pl.Binary,
    "Binary": pl.Binary,
    "time": pl.Time,
    "Time": pl.Time,
    "timestamp": pl.Datetime,
```

Then update the `cast()` method to add `resolve_dtype()` normalization at the top, before the isinstance checks:

```python
    def cast(self, x: PolarsExpr, /, dtype: Any) -> PolarsExpr:
        # Try canonical resolution first
        try:
            from mountainash.core.dtypes import resolve_dtype
            dtype = resolve_dtype(dtype)
        except ValueError:
            pass  # Fall through to backend-specific handling

        # If already a Polars dtype, use directly
        if isinstance(dtype, pl.DataType) or (isinstance(dtype, type) and issubclass(dtype, pl.DataType)):
            return x.cast(dtype)
        # ... rest unchanged
```

- [ ] **Step 2: Update Narwhals backend dtype map**

In `expsys_nw_cast.py`, add the missing entries to `_NARWHALS_DTYPE_MAP`:

```python
    # Missing canonical names
    "timestamp": nw.Datetime,
    "time": nw.Time,
    "Time": nw.Time,
    "binary": nw.String,  # Narwhals has no Binary type for cast — fall through if needed
    # Unsigned integers
    "u8": nw.UInt8,
    "u16": nw.UInt16,
    "u32": nw.UInt32,
    "u64": nw.UInt64,
    "UInt8": nw.UInt8,
    "UInt16": nw.UInt16,
    "UInt32": nw.UInt32,
    "UInt64": nw.UInt64,
    "uint8": nw.UInt8,
    "uint16": nw.UInt16,
    "uint32": nw.UInt32,
    "uint64": nw.UInt64,
```

**Important:** Before adding `"binary"`, check if Narwhals supports Binary:

```bash
hatch run test:python -c "import narwhals as nw; print(hasattr(nw, 'Binary'))"
```

If `True`, map `"binary": nw.Binary`. If `False`, omit the `"binary"` entry — the fallback will handle it.

Then add `resolve_dtype()` normalization to the `cast()` method (same pattern as Polars above):

```python
    def cast(self, x: NarwhalsExpr, /, dtype: Any) -> NarwhalsExpr:
        # Try canonical resolution first
        try:
            from mountainash.core.dtypes import resolve_dtype
            dtype = resolve_dtype(dtype)
        except ValueError:
            pass  # Fall through to backend-specific handling

        # If already a Narwhals dtype, use directly
        if hasattr(nw, "DType") and isinstance(dtype, nw.DType):
            return x.cast(dtype)
        # ... rest unchanged
```

- [ ] **Step 3: Update Ibis backend dtype map**

In `expsys_ib_cast.py`, add the missing entries to `_IBIS_DTYPE_MAP`:

```python
    # Unsigned integers
    "u8": "uint8",
    "u16": "uint16",
    "u32": "uint32",
    "u64": "uint64",
    "UInt8": "uint8",
    "UInt16": "uint16",
    "UInt32": "uint32",
    "UInt64": "uint64",
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "uint64": "uint64",
    # Missing canonical names
    "binary": "binary",
    "Binary": "binary",
    "time": "time",
    "Time": "time",
```

Then add `resolve_dtype()` normalization to the `cast()` method:

```python
    def cast(self, x: IbisValueExpr, /, dtype: Any) -> IbisValueExpr:
        # Try canonical resolution first
        try:
            from mountainash.core.dtypes import resolve_dtype
            dtype = resolve_dtype(dtype)
        except ValueError:
            pass  # Fall through to backend-specific handling

        # If already an Ibis DataType, use directly
        if isinstance(dtype, dt.DataType):
            return x.cast(dtype)
        # ... rest unchanged
```

- [ ] **Step 4: Run existing tests to verify no regression**

Run: `hatch run test:test-target-quick tests/cross_backend/test_type.py -v`
Expected: Same baseline (129 passed, 3 xfailed)

Run: `hatch run test:test-target-quick tests/unit/core/test_dtypes.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_cast.py \
        src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_cast.py \
        src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_cast.py
git commit -m "feat: align backend dtype maps with canonical types and add resolve_dtype() normalization"
```

---

### Task 4: Add `select_and_collect()` to shared backend helpers

**Files:**
- Modify: `tests/fixtures/backend_helpers.py`

- [ ] **Step 1: Add `select_and_collect()` function**

Add this as a module-level function at the end of `tests/fixtures/backend_helpers.py` (after the `BackendDataFrameFactory` class):

```python
def select_and_collect(
    df: Any, backend_expr: Any, column_alias: str, backend_name: str
) -> List:
    """Select an expression and extract values as a Python list.

    Uses PyArrow for Ibis backends to avoid pandas NaN/null conflation.

    Args:
        df: DataFrame from any backend
        backend_expr: Compiled backend expression
        column_alias: Name for the result column
        backend_name: Backend identifier

    Returns:
        List of column values
    """
    if backend_name.startswith("ibis-"):
        result = df.select(backend_expr.name(column_alias))
        return result.to_pyarrow()[column_alias].to_pylist()
    else:
        result = df.select(backend_expr.alias(column_alias))
        return result[column_alias].to_list()
```

- [ ] **Step 2: Verify import works**

Run: `hatch run test:python -c "from fixtures.backend_helpers import select_and_collect; print('OK')"`

(Run from the `tests/` directory, or adjust PYTHONPATH.)

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/backend_helpers.py
git commit -m "feat: add select_and_collect() with PyArrow extraction for Ibis"
```

---

### Task 5: Create `test_cast.py` — cast behavior tests

**Files:**
- Create: `tests/cross_backend/test_cast.py`

This is the current `test_type.py` content rewritten to use canonical type strings and the shared helper. No `get_*_dtype()` helpers. Every `select_and_extract()` replaced with `select_and_collect()` imported from `fixtures.backend_helpers`.

- [ ] **Step 1: Create `tests/cross_backend/test_cast.py`**

```python
"""Cross-backend tests for cast operation behavior.

Validates that type casting produces correct values consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).

Uses canonical mountainash type strings ("i64", "string", "fp64", etc.)
instead of backend-specific types.
"""

import pytest
import math
import mountainash.expressions as ma

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fixtures.backend_helpers import select_and_collect


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


# =============================================================================
# Cast to Integer
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToInteger:
    """Test casting to integer types."""

    def test_cast_float_to_int(self, backend_name, backend_factory):
        """Test casting float values to int (truncates toward zero)."""
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "DuckDB uses banker's rounding for float-to-int cast, not truncation. "
                "This is inherent DuckDB behavior: 2.9 → 3 (rounded) instead of 2 (truncated)."
            )

        data = {"value": [1.1, 2.9, 3.5, -1.7, -2.3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("i64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [1, 2, 3, -1, -2]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_string_to_int(self, backend_name, backend_factory):
        """Test casting string numeric values to int."""
        data = {"value": ["10", "20", "30", "40", "50"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("i64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [10, 20, 30, 40, 50]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_bool_to_int(self, backend_name, backend_factory):
        """Test casting boolean to int (True=1, False=0)."""
        data = {"flag": [True, False, True, False, True]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("flag").cast("i64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [1, 0, 1, 0, 1]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_int64_to_int32(self, backend_name, backend_factory):
        """Test casting between integer types."""
        data = {"value": [100, 200, 300]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("i32")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [100, 200, 300]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Cast to Float
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToFloat:
    """Test casting to float types."""

    def test_cast_int_to_float(self, backend_name, backend_factory):
        """Test casting integer values to float."""
        data = {"value": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("fp64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_string_to_float(self, backend_name, backend_factory):
        """Test casting string numeric values to float."""
        data = {"value": ["1.5", "2.5", "3.5"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("fp64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [1.5, 2.5, 3.5]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_bool_to_float(self, backend_name, backend_factory):
        """Test casting boolean to float (True=1.0, False=0.0)."""
        data = {"flag": [True, False, True]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("flag").cast("fp64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [1.0, 0.0, 1.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Cast to String
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToString:
    """Test casting to string type."""

    def test_cast_int_to_string(self, backend_name, backend_factory):
        """Test casting integer to string."""
        data = {"value": [1, 2, 3, 100, 999]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("string")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = ["1", "2", "3", "100", "999"]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_float_to_string(self, backend_name, backend_factory):
        """Test casting float to string."""
        data = {"value": [1.5, 2.0, 3.75]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("string")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        assert "1" in values[0] and "5" in values[0], f"[{backend_name}] Expected '1.5', got {values[0]}"

    def test_cast_bool_to_string(self, backend_name, backend_factory):
        """Test casting boolean to string."""
        data = {"flag": [True, False, True]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("flag").cast("string")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        assert values[0] != values[1], f"[{backend_name}] True and False should differ: {values}"


# =============================================================================
# Cast to Boolean
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastToBoolean:
    """Test casting to boolean type."""

    def test_cast_int_to_bool(self, backend_name, backend_factory):
        """Test casting integer to boolean (0=False, nonzero=True)."""
        data = {"value": [0, 1, 2, -1, 0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("bool")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [False, True, True, True, False]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_float_to_bool(self, backend_name, backend_factory):
        """Test casting float to boolean (0.0=False, nonzero=True)."""
        data = {"value": [0.0, 1.0, 0.5, -0.5, 0.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("bool")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [False, True, True, True, False]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Cast with Nulls
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastWithNulls:
    """Test casting with null values."""

    def test_cast_with_null_int_to_float(self, backend_name, backend_factory):
        """Test that nulls are preserved when casting int to float."""
        data = {"value": [1, None, 3, None, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("fp64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        assert values[0] == 1.0, f"[{backend_name}] First value: {values[0]}"
        assert values[2] == 3.0, f"[{backend_name}] Third value: {values[2]}"
        assert values[4] == 5.0, f"[{backend_name}] Fifth value: {values[4]}"

        assert values[1] is None or (isinstance(values[1], float) and math.isnan(values[1])), \
            f"[{backend_name}] Second value should be null: {values[1]}"
        assert values[3] is None or (isinstance(values[3], float) and math.isnan(values[3])), \
            f"[{backend_name}] Fourth value should be null: {values[3]}"

    def test_cast_with_null_float_to_string(self, backend_name, backend_factory):
        """Test that nulls are preserved when casting float to string."""
        if backend_name == "pandas":
            pytest.xfail(
                "Pandas converts null float to the string 'nan' instead of preserving None. "
                "This is inherent Pandas behavior when casting nullable floats to strings."
            )

        data = {"value": [1.5, None, 3.5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("string")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        assert isinstance(values[0], str), f"[{backend_name}] First should be string: {values[0]}"
        assert isinstance(values[2], str), f"[{backend_name}] Third should be string: {values[2]}"
        assert values[1] is None, f"[{backend_name}] Second value should be null: {values[1]}"


# =============================================================================
# Cast in Expressions
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastInExpressions:
    """Test using cast within larger expressions."""

    def test_cast_then_arithmetic(self, backend_name, backend_factory):
        """Test casting then performing arithmetic."""
        data = {"value": ["10", "20", "30"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("i64") * 2
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [20, 40, 60]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_then_comparison(self, backend_name, backend_factory):
        """Test casting then performing comparison."""
        data = {"value": ["5", "15", "25"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("i64").gt(10)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [False, True, True]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_arithmetic_then_cast(self, backend_name, backend_factory):
        """Test arithmetic then casting result."""
        data = {"a": [10, 20, 30], "b": [3, 3, 3]}
        df = backend_factory.create(data, backend_name)

        expr = (ma.col("a") + ma.col("b")).cast("string")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = ["13", "23", "33"]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_with_alias(self, backend_name, backend_factory):
        """Test casting combined with alias."""
        data = {"price": [100, 200, 300]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").cast("fp64").name.alias("price_float")
        backend_expr = expr.compile(df)

        if backend_name.startswith("ibis-"):
            result = df.select(backend_expr)
            values = result.to_pyarrow()["price_float"].to_pylist()
        else:
            result = df.select(backend_expr)
            values = result["price_float"].to_list()

        expected = [100.0, 200.0, 300.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCastEdgeCases:
    """Test edge cases for cast operations."""

    def test_cast_same_type(self, backend_name, backend_factory):
        """Test casting to the same type (should be no-op)."""
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("i64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [1, 2, 3]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_negative_float_to_int(self, backend_name, backend_factory):
        """Test casting negative floats to int (truncation behavior)."""
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "DuckDB uses banker's rounding for float-to-int cast, not truncation. "
                "This is inherent DuckDB behavior: -1.9 → -2 (rounded) instead of -1 (truncated)."
            )

        data = {"value": [-1.9, -2.1, -3.5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("i64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [-1, -2, -3]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"

    def test_cast_zero_values(self, backend_name, backend_factory):
        """Test casting zero values."""
        data = {"value": [0, 0, 0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("string")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        assert len(values) == 3, f"[{backend_name}] Expected 3 values"
        for v in values:
            assert "0" in v, f"[{backend_name}] Expected '0' in {v}"

    def test_cast_large_int_to_float(self, backend_name, backend_factory):
        """Test casting large integers to float (precision check)."""
        data = {"value": [1000000, 2000000, 3000000]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast("fp64")
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        expected = [1000000.0, 2000000.0, 3000000.0]
        assert values == expected, f"[{backend_name}] Expected {expected}, got {values}"
```

- [ ] **Step 2: Run the new test file**

Run: `hatch run test:test-target-quick tests/cross_backend/test_cast.py -v`
Expected: 129 passed, 3 xfailed (same behavior as old test_type.py)

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_cast.py
git commit -m "feat: add test_cast.py with canonical type strings"
```

---

### Task 6: Create `test_type_resolution.py` — type resolution tests

**Files:**
- Create: `tests/cross_backend/test_type_resolution.py`

- [ ] **Step 1: Create `tests/cross_backend/test_type_resolution.py`**

```python
"""Cross-backend tests for type resolution.

Validates that the dtype system correctly resolves different type specifiers
(canonical strings, aliases, native types, Python types, enum members)
across all backends.
"""

import pytest
import mountainash.expressions as ma
from mountainash.core.dtypes import MountainashDtype, resolve_dtype

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fixtures.backend_helpers import select_and_collect


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

# Canonical types that can be tested with simple int data (cast from int)
INT_CASTABLE_TYPES = [
    ("i8", [1, 2, 3]),
    ("i16", [1, 2, 3]),
    ("i32", [1, 2, 3]),
    ("i64", [1, 2, 3]),
    ("u8", [1, 2, 3]),
    ("u16", [1, 2, 3]),
    ("u32", [1, 2, 3]),
    ("u64", [1, 2, 3]),
    ("fp32", [1, 2, 3]),
    ("fp64", [1, 2, 3]),
    ("bool", [0, 1, 0]),
    ("string", [1, 2, 3]),
]


# =============================================================================
# Canonical Type Strings
# =============================================================================

@pytest.mark.cross_backend
class TestCanonicalTypeStrings:
    """Every tier-1 canonical string works on every backend."""

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    @pytest.mark.parametrize("dtype,input_data", INT_CASTABLE_TYPES,
                             ids=[t[0] for t in INT_CASTABLE_TYPES])
    def test_canonical_type_accepted(self, backend_name, backend_factory, dtype, input_data):
        """Cast with a canonical type string does not raise."""
        data = {"value": input_data}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(dtype)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)

        assert len(values) == len(input_data), (
            f"[{backend_name}] cast to {dtype!r}: expected {len(input_data)} values, got {len(values)}"
        )


# =============================================================================
# Type Aliases
# =============================================================================

@pytest.mark.cross_backend
class TestTypeAliases:
    """Common aliases resolve to the same result as their canonical form."""

    ALIAS_PAIRS = [
        ("boolean", "bool"),
        ("int64", "i64"),
        ("int32", "i32"),
        ("float64", "fp64"),
        ("float32", "fp32"),
        ("Int64", "i64"),
        ("Float64", "fp64"),
        ("Utf8", "string"),
        ("String", "string"),
        ("Boolean", "bool"),
        ("Datetime", "timestamp"),
        ("f64", "fp64"),
        ("f32", "fp32"),
        ("UInt32", "u32"),
        ("uint16", "u16"),
    ]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    @pytest.mark.parametrize("alias,canonical", ALIAS_PAIRS,
                             ids=[f"{a}->{c}" for a, c in ALIAS_PAIRS])
    def test_alias_produces_same_result_as_canonical(
        self, backend_name, backend_factory, alias, canonical
    ):
        """An alias and its canonical form produce identical results."""
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr_alias = ma.col("value").cast(alias)
        expr_canonical = ma.col("value").cast(canonical)

        values_alias = select_and_collect(df, expr_alias.compile(df), "r1", backend_name)
        values_canonical = select_and_collect(df, expr_canonical.compile(df), "r2", backend_name)

        assert values_alias == values_canonical, (
            f"[{backend_name}] alias {alias!r} produced {values_alias}, "
            f"canonical {canonical!r} produced {values_canonical}"
        )


# =============================================================================
# Native Types — Own Backend
# =============================================================================

@pytest.mark.cross_backend
class TestNativeTypesOwnBackend:
    """Native backend types work when passed to their own backend."""

    def test_polars_native_on_polars(self, backend_factory):
        """pl.Int64 works on Polars backend."""
        import polars as pl
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "polars")

        expr = ma.col("value").cast(pl.Int64)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "polars")
        assert values == [1, 2, 3]

    def test_polars_utf8_on_polars(self, backend_factory):
        """pl.Utf8 works on Polars backend."""
        import polars as pl
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "polars")

        expr = ma.col("value").cast(pl.Utf8)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "polars")
        assert values == ["1", "2", "3"]

    def test_narwhals_native_on_narwhals(self, backend_factory):
        """nw.Int64 works on Narwhals backend."""
        import narwhals as nw
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "narwhals")

        expr = ma.col("value").cast(nw.Int64)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "narwhals")
        assert values == [1, 2, 3]

    def test_narwhals_string_on_narwhals(self, backend_factory):
        """nw.String works on Narwhals backend."""
        import narwhals as nw
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "narwhals")

        expr = ma.col("value").cast(nw.String)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "narwhals")
        assert values == ["1", "2", "3"]

    def test_ibis_native_on_ibis_duckdb(self, backend_factory):
        """ibis.expr.datatypes.int64 works on Ibis-DuckDB backend."""
        import ibis.expr.datatypes as dt
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "ibis-duckdb")

        expr = ma.col("value").cast(dt.int64)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "ibis-duckdb")
        assert values == [1, 2, 3]


# =============================================================================
# Native Types — Cross Backend
# =============================================================================

@pytest.mark.cross_backend
class TestNativeTypesCrossBackend:
    """Native types from one backend resolve via str() on another backend.

    This works because str(pl.Int64) → "Int64" → alias → "i64",
    str(nw.String) → "String" → alias → "string", etc.
    """

    def test_polars_int64_on_ibis(self, backend_factory):
        """pl.Int64 works on Ibis because str(pl.Int64) → 'Int64' → alias."""
        import polars as pl
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "ibis-duckdb")

        expr = ma.col("value").cast(pl.Int64)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "ibis-duckdb")
        assert values == [1, 2, 3]

    def test_polars_utf8_on_narwhals(self, backend_factory):
        """pl.Utf8 works on Narwhals because str(pl.Utf8) → 'Utf8' → alias."""
        import polars as pl
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "narwhals")

        expr = ma.col("value").cast(pl.Utf8)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "narwhals")
        assert values == ["1", "2", "3"]

    def test_narwhals_string_on_polars(self, backend_factory):
        """nw.String works on Polars because str(nw.String) → 'String' → alias."""
        import narwhals as nw
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "polars")

        expr = ma.col("value").cast(nw.String)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "polars")
        assert values == ["1", "2", "3"]

    def test_narwhals_int64_on_ibis(self, backend_factory):
        """nw.Int64 works on Ibis because str(nw.Int64) → 'Int64' → alias."""
        import narwhals as nw
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, "ibis-duckdb")

        expr = ma.col("value").cast(nw.Int64)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "ibis-duckdb")
        assert values == [1, 2, 3]

    def test_polars_uint16_on_ibis(self, backend_factory):
        """pl.UInt16 works on Ibis because str(pl.UInt16) → 'UInt16' → alias."""
        import polars as pl
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, "ibis-polars")

        expr = ma.col("value").cast(pl.UInt16)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", "ibis-polars")
        assert values == [1, 2, 3]


# =============================================================================
# Invalid Type Strings
# =============================================================================

@pytest.mark.cross_backend
class TestInvalidTypeStrings:
    """Invalid type strings raise ValueError at build time."""

    @pytest.mark.parametrize("bad_dtype", [
        "foobar",
        "",
        "int999",
        "FLOAT",
        "INTEGER",
    ])
    def test_invalid_string_raises(self, bad_dtype):
        """Unrecognized type strings raise ValueError in cast()."""
        with pytest.raises(ValueError, match="Unknown dtype"):
            ma.col("value").cast(bad_dtype)

    def test_none_raises(self):
        """None as dtype raises ValueError."""
        with pytest.raises(ValueError, match="Unknown dtype"):
            ma.col("value").cast(None)


# =============================================================================
# Python Built-in Types
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestPythonBuiltinTypes:
    """Python built-in types (int, float, str, bool) work in cast()."""

    def test_cast_with_python_int(self, backend_name, backend_factory):
        data = {"value": [1.5, 2.5, 3.5]}
        df = backend_factory.create(data, backend_name)

        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB uses banker's rounding for float-to-int cast.")

        expr = ma.col("value").cast(int)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == [1, 2, 3]

    def test_cast_with_python_float(self, backend_name, backend_factory):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(float)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == [1.0, 2.0, 3.0]

    def test_cast_with_python_str(self, backend_name, backend_factory):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(str)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == ["1", "2", "3"]

    def test_cast_with_python_bool(self, backend_name, backend_factory):
        data = {"value": [0, 1, 0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(bool)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == [False, True, False]


# =============================================================================
# MountainashDtype Enum
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMountainashDtypeEnum:
    """MountainashDtype enum members work directly in cast()."""

    def test_cast_with_enum_i64(self, backend_name, backend_factory):
        data = {"value": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, backend_name)

        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB uses banker's rounding for float-to-int cast.")

        expr = ma.col("value").cast(MountainashDtype.I64)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == [1, 2, 3]

    def test_cast_with_enum_string(self, backend_name, backend_factory):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(MountainashDtype.STRING)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == ["1", "2", "3"]

    def test_cast_with_enum_fp64(self, backend_name, backend_factory):
        data = {"value": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(MountainashDtype.FP64)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == [1.0, 2.0, 3.0]

    def test_cast_with_enum_bool(self, backend_name, backend_factory):
        data = {"value": [0, 1, 0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(MountainashDtype.BOOL)
        backend_expr = expr.compile(df)
        values = select_and_collect(df, backend_expr, "result", backend_name)
        assert values == [False, True, False]
```

- [ ] **Step 2: Run the new test file**

Run: `hatch run test:test-target-quick tests/cross_backend/test_type_resolution.py -v`
Expected: All PASS (with xfails for DuckDB rounding)

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/test_type_resolution.py
git commit -m "feat: add test_type_resolution.py for canonical type system validation"
```

---

### Task 7: Delete old `test_type.py` and verify full suite

**Files:**
- Delete: `tests/cross_backend/test_type.py`

- [ ] **Step 1: Run both new test files to confirm they cover everything**

Run: `hatch run test:test-target-quick tests/cross_backend/test_cast.py tests/cross_backend/test_type_resolution.py -v`
Expected: All passing (with expected xfails)

- [ ] **Step 2: Delete old test file**

```bash
git rm tests/cross_backend/test_type.py
```

- [ ] **Step 3: Run full test suite to check for no regressions**

Run: `hatch run test:test-quick`
Expected: Full suite passes. Any test that imported from `test_type.py` will fail — check for that.

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: remove test_type.py, replaced by test_cast.py and test_type_resolution.py"
```
