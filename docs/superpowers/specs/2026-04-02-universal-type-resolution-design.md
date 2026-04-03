# Universal Type Resolution Design

**Date:** 2026-04-02
**Status:** Approved
**Scope:** `mountainash.core.dtypes`, backend dtype map alignment, test split

## Problem

The cast system has no single source of truth for type strings. Each backend independently maintains a dtype mapping dictionary with ad-hoc overlap. Cross-backend tests use per-backend dtype helpers (`get_string_dtype()`, `get_int32_dtype()`) that resolve backend-native types — defeating the purpose of a universal expression language. The test extraction helper also routes through pandas, which conflates null and NaN.

### Current State

- **API builder** (`api_bldr_cast.py`): Normalizes Python types (`int` → `"i64"`) then calls `str(dtype)` on everything else. Stores result in `CastNode.target_type` as a string.
- **Backend maps**: Three independent dictionaries (`_POLARS_DTYPE_MAP`, `_IBIS_DTYPE_MAP`, `_NARWHALS_DTYPE_MAP`) with overlapping but inconsistent keys.
- **Gaps**: Narwhals missing `"timestamp"`. No unsigned int canonical names. No validation of unrecognized strings.
- **Tests**: `test_type.py` uses 6 backend-specific dtype helpers where universal strings would work directly.

### Cross-Library Type Alignment Matrix

| Type | Substrait | Polars | Narwhals | Ibis | Canonical |
|------|-----------|--------|----------|------|-----------|
| Boolean | `boolean` | `Boolean` | `Boolean` | `Boolean` | `bool` |
| Int8 | `i8` | `Int8` | `Int8` | `Int8` | `i8` |
| Int16 | `i16` | `Int16` | `Int16` | `Int16` | `i16` |
| Int32 | `i32` | `Int32` | `Int32` | `Int32` | `i32` |
| Int64 | `i64` | `Int64` | `Int64` | `Int64` | `i64` |
| UInt8 | — | `UInt8` | `UInt8` | `UInt8` | `u8` |
| UInt16 | — | `UInt16` | `UInt16` | `UInt16` | `u16` |
| UInt32 | — | `UInt32` | `UInt32` | `UInt32` | `u32` |
| UInt64 | — | `UInt64` | `UInt64` | `UInt64` | `u64` |
| Float32 | `fp32` | `Float32` | `Float32` | `Float32` | `fp32` |
| Float64 | `fp64` | `Float64` | `Float64` | `Float64` | `fp64` |
| String | `string` | `String` / `Utf8` | `String` | `String` | `string` |
| Binary | `binary` | `Binary` | `Binary` | `Binary` | `binary` |
| Date | `date` | `Date` | `Date` | `Date` | `date` |
| Time | `time` | `Time` | `Time` | `Time` | `time` |
| Timestamp | `timestamp` | `Datetime` | `Datetime` | `Timestamp` | `timestamp` |

**Tier 2 (out of scope, documented for future):**

| Type | Substrait | Polars | Narwhals | Ibis | Notes |
|------|-----------|--------|----------|------|-------|
| Decimal | `DECIMAL<P,S>` | `Decimal` | `Decimal` | `Decimal` | Parameterized |
| Duration | `INTERVAL_DAY<P>` | `Duration` | `Duration` | `Interval` | Naming divergence + parameterized |
| Timestamp_tz | `timestamp_tz` | `Datetime(tz=)` | `Datetime(tz=)` | `Timestamp(tz=)` | Parameterized |
| List | `LIST<T>` | `List` | `List` | `Array` | Parameterized |
| Struct | `STRUCT<...>` | `Struct` | `Struct` | `Struct` | Parameterized |
| Map | `MAP<K,V>` | — | — | `Map` | Parameterized, not in Polars/Narwhals |
| Int128 | — | `Int128` | `Int128` | — | Not in Substrait or Ibis |
| UInt128 | — | `UInt128` | `UInt128` | — | Not in Substrait or Ibis |
| Float16 | — | `Float16` | — | `Float16` | Not in Narwhals |

## Design

### 1. New Module: `mountainash.core.dtypes`

**File:** `src/mountainash/core/dtypes.py`

Three components:

#### 1a. `MountainashDtype` Enum

```python
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
```

Inherits from `str` so `MountainashDtype.STRING == "string"` — works directly in `.cast()` calls without API changes.

#### 1b. `DTYPE_ALIASES` Registry

A flat dict mapping every accepted string variation to its canonical `MountainashDtype`:

```python
DTYPE_ALIASES: dict[str, MountainashDtype] = {
    # Canonical names (identity mappings)
    "bool": MountainashDtype.BOOL,
    "i8": MountainashDtype.I8,
    # ... all 16 canonical names

    # Substrait alternatives
    "boolean": MountainashDtype.BOOL,
    "fp32": MountainashDtype.FP32,

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
    "timestamp": MountainashDtype.TIMESTAMP,
    "date": MountainashDtype.DATE,
    "time": MountainashDtype.TIME,
    "string": MountainashDtype.STRING,
    "binary": MountainashDtype.BINARY,
}
```

#### 1c. `resolve_dtype()` Function

```python
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
      Canonical type string (e.g., "i64", "string", "fp64")

    Raises:
      ValueError: If dtype cannot be resolved to a known type
    """
    # Already a MountainashDtype
    if isinstance(dtype, MountainashDtype):
        return dtype.value

    # Python built-in type
    if isinstance(dtype, type) and dtype in _PYTHON_TYPE_MAP:
        return _PYTHON_TYPE_MAP[dtype].value

    # Convert to string for lookup
    dtype_str = str(dtype)

    # Look up in alias registry
    if dtype_str in DTYPE_ALIASES:
        return DTYPE_ALIASES[dtype_str].value

    raise ValueError(
        f"Unknown dtype: {dtype!r} (resolved to string {dtype_str!r}). "
        f"Use a canonical type like 'i64', 'string', 'fp64', or a MountainashDtype enum."
    )
```

### 2. Backend Dtype Map Alignment

Each backend's cast implementation gets two changes:

**a. Add missing entries to each backend's `_*_DTYPE_MAP`:**
- All backends: ensure all 16 canonical strings are present as keys
- All backends: ensure `u8`–`u64` unsigned types are present
- Narwhals: add `"timestamp"` → `nw.Datetime`

**b. Add normalization step to each backend's `cast()` method:**

```python
def cast(self, x, /, dtype):
    # Try resolve through canonical registry first
    try:
        from mountainash.core.dtypes import resolve_dtype
        dtype = resolve_dtype(dtype)
    except ValueError:
        pass  # Fall through to backend-specific handling

    # Existing isinstance checks and map lookup...
```

This means any alias automatically works on any backend. The `try/except` preserves backward compatibility for two cases: (1) backend-native types that `resolve_dtype()` doesn't recognize (e.g., a parameterized `pl.Datetime("us", "UTC")`), and (2) tier 2 type strings that backends may handle natively but aren't in the canonical registry yet. In both cases, the existing isinstance checks and fallback `x.cast(dtype)` handle the type. The API builder (section 3) does NOT use try/except — it raises `ValueError` for unrecognized types at build time, which is the intended validation point.

### 3. API Builder Update

Replace the ad-hoc normalization in `api_bldr_cast.py`:

```python
# Before (current):
if isinstance(dtype, type):
    type_map = {int: "i64", float: "f64", str: "string", bool: "bool"}
    target_type = type_map.get(dtype, str(dtype))
else:
    target_type = str(dtype)

# After:
from mountainash.core.dtypes import resolve_dtype
target_type = resolve_dtype(dtype)
```

This is a strict improvement: same behavior for known types, clear error for unknown types instead of silent `str()` passthrough.

### 4. Test File Split

#### 4a. `tests/cross_backend/test_cast.py` — Cast Behavior

Tests that cast produces correct values. Uses only canonical type strings.

**Test classes:**
- `TestCastToInteger` — float→int truncation, string→int, negative floats (existing)
- `TestCastToFloat` — int→float, string→float, precision (existing)
- `TestCastToString` — int→string, float→string, bool→string (existing)
- `TestCastToBoolean` — int→bool, string→bool (existing)
- `TestCastWithNulls` — null preservation across all cast types (existing)
- `TestCastInExpressions` — cast chained with arithmetic, comparisons, aliases (existing)
- `TestCastEdgeCases` — same-type cast, zero values, large ints (existing)

All `get_*_dtype(backend_name)` calls replaced with inline canonical strings: `"i64"`, `"string"`, `"fp64"`, `"bool"`.

#### 4b. `tests/cross_backend/test_type_resolution.py` — Type Resolution

Tests that the dtype system accepts and resolves different type specifiers correctly.

**Test classes:**

- `TestCanonicalTypeStrings` — every tier 1 canonical string works on every backend. Parametrized: 16 types × 6 backends = 96 test cases. Each test creates data, casts to the target type, verifies no error and result has expected type characteristics.

- `TestTypeAliases` — common aliases resolve correctly. Tests `"boolean"` → same as `"bool"`, `"int64"` → same as `"i64"`, `"Utf8"` → same as `"string"`, `"Datetime"` → same as `"timestamp"`, etc.

- `TestNativeTypesOwnBackend` — passing backend-native types to their own backend:
  - `pl.Int64` on Polars backend
  - `nw.String` on Narwhals backend
  - `ibis.expr.datatypes.string` on Ibis backends

- `TestNativeTypesCrossBackend` — passing native types from one backend to another. These go through `str()` → `resolve_dtype()`. Tests that `pl.Int64` works on Ibis (because `str(pl.Int64)` → `"Int64"` → alias → `"i64"`). Tests cases where this works and verifies the error message where it doesn't.

- `TestInvalidTypeStrings` — garbage strings (`"foobar"`, `""`, `"int999"`), verifies `ValueError` with helpful message.

- `TestPythonBuiltinTypes` — `int`, `float`, `str`, `bool` as Python types passed directly to `.cast()`.

- `TestMountainashDtypeEnum` — using `MountainashDtype.I64`, `MountainashDtype.STRING`, etc. directly in `.cast()` calls.

### 5. Shared Test Utility

**Location:** `tests/fixtures/backend_helpers.py`

Move and rename the extraction helper:

```python
def select_and_collect(df, backend_expr, column_alias, backend_name) -> list:
    """Select an expression and extract values as a Python list.

    Uses PyArrow for Ibis backends to avoid pandas NaN/null conflation.
    """
    if backend_name.startswith("ibis-"):
        result = df.select(backend_expr.name(column_alias))
        return result.to_pyarrow()[column_alias].to_pylist()
    else:
        result = df.select(backend_expr.alias(column_alias))
        return result[column_alias].to_list()
```

Both new test files import from this shared location. The current `test_type.py` is deleted.

## Out of Scope

- Tier 2 parameterized types (`decimal<P,S>`, `duration`, `timestamp_tz`, `list<T>`, `struct<...>`)
- Replacing backend dtype maps entirely with a generated-from-registry approach
- Changes to CastNode or visitor
- Changes to schema module cast handling
- `Int128`, `UInt128`, `Float16` (insufficient cross-backend support)
