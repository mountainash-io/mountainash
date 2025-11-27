# Namespace Refactor: Implementation Plan

## Overview

Migrate from mixin-based `ExpressionBuilder` to descriptor-based namespace architecture.

**Scope:**
- 10 mixin files → ~14 namespace files
- ~113 methods to migrate
- ~2,354 lines of source code
- 703 existing tests (must remain passing)

---

## Phase 1: Infrastructure

**Goal:** Create the foundational classes that all namespaces depend on.

### 1.1 Create Directory Structure

```
src/mountainash_expressions/core/
├── expression_api/
│   ├── __init__.py
│   ├── descriptor.py       # NamespaceDescriptor
│   ├── base.py             # BaseExpressionAPI
│   ├── boolean.py          # BooleanExpressionAPI
│   └── ternary.py          # TernaryExpressionAPI (stub)
└── namespaces/
    ├── __init__.py
    ├── base.py             # BaseNamespace
    ├── comparison/
    │   ├── __init__.py
    │   └── boolean.py      # BooleanComparisonNamespace
    ├── logical/
    │   ├── __init__.py
    │   └── boolean.py      # BooleanLogicalNamespace
    ├── arithmetic.py       # ArithmeticNamespace
    ├── string.py           # StringNamespace
    ├── date.py             # DateNamespace (was TemporalExpressionBuilder)
    ├── name.py             # NameNamespace
    ├── null.py             # NullNamespace
    ├── type.py             # TypeNamespace
    ├── iterable.py         # IterableNamespace
    └── native.py           # NativeNamespace
```

### 1.2 Implement NamespaceDescriptor

**File:** `core/expression_api/descriptor.py`

```python
class NamespaceDescriptor(Generic[T]):
    """Lazily bind namespace class to API instance."""

    def __init__(self, namespace_cls: type[T]) -> None:
        self._namespace_cls = namespace_cls

    def __get__(self, obj, objtype=None) -> T | NamespaceDescriptor[T]:
        if obj is None:
            return self
        return self._namespace_cls(obj)
```

**Tests:**
- [ ] Class access returns descriptor
- [ ] Instance access returns namespace instance
- [ ] Namespace bound to correct API instance

### 1.3 Implement BaseNamespace

**File:** `core/namespaces/base.py`

Key methods:
- `__init__(self, api)` - Store parent API
- `_node` property - Access current node
- `_to_node_or_value(other)` - Convert input to node
- `_coerce_if_needed(node)` - Override for logic coercion
- `_build(node)` - Create new API via `self._api.create(node)`

**Tests:**
- [ ] `_node` returns API's node
- [ ] `_to_node_or_value` handles API, Node, and raw values
- [ ] `_build` preserves concrete API type

### 1.4 Implement BaseExpressionAPI

**File:** `core/expression_api/base.py`

Key components:
- `_FLAT_NAMESPACES: tuple[type[BaseNamespace], ...]` class variable
- `__init__(self, node)` - Store expression node
- `create(cls, node) -> Self` - Factory preserving type
- `__getattr__(name)` - Dispatch to flat namespaces
- `_to_node_or_value(other)` - Convert inputs
- `compile(target)` - Compile to backend

**Tests:**
- [ ] `__getattr__` finds method in first matching namespace
- [ ] `__getattr__` raises `AttributeError` for unknown methods
- [ ] `create()` returns same concrete type
- [ ] `compile()` works with existing visitor factory

### 1.5 Integration Test

Create minimal `BooleanExpressionAPI` with one namespace to verify the dispatch mechanism:

```python
class BooleanExpressionAPI(BaseExpressionAPI):
    _FLAT_NAMESPACES = (BooleanComparisonNamespace,)

# Test: col("a").eq(5) works
```

---

## Phase 2: Namespace Conversion (Flat Namespaces)

**Goal:** Convert mixins to namespaces one at a time, maintaining test compatibility.

### Conversion Pattern

For each mixin method:

```python
# BEFORE (mixin)
def method(self, arg):
    node = SomeExpressionNode(...)
    return ExpressionBuilder(node)  # ❌ Hardcoded

# AFTER (namespace)
def method(self, arg):
    node = SomeExpressionNode(...)
    return self._build(node)  # ✅ Uses factory
```

### 2.1 BooleanComparisonNamespace

**Source:** `boolean_expression_builder.py` (comparison methods only)
**Target:** `namespaces/comparison/boolean.py`
**Methods:** `eq`, `ne`, `gt`, `lt`, `ge`, `le`, `is_close`, `between`
**Dunder methods:** `__eq__`, `__ne__`, `__gt__`, `__lt__`, `__ge__`, `__le__`

**Protocol:** `BooleanBuilderProtocol` (comparison subset)

### 2.2 BooleanLogicalNamespace

**Source:** `boolean_expression_builder.py` (logical methods only)
**Target:** `namespaces/logical/boolean.py`
**Methods:** `and_`, `or_`, `xor_`, `xor_parity`, `not_`, `is_true`, `is_false`
**Dunder methods:** `__and__`, `__or__`, `__xor__`, `__invert__`

**Special:** Implements `_coerce_if_needed()` for ternary→boolean coercion

### 2.3 BooleanCollectionNamespace

**Source:** `boolean_expression_builder.py` (collection methods)
**Target:** `namespaces/comparison/boolean.py` (or separate file)
**Methods:** `is_in`, `is_not_in`, `always_true`, `always_false`

### 2.4 ArithmeticNamespace

**Source:** `arithmetic_expression_builder.py` (~325 lines, 21 methods)
**Target:** `namespaces/arithmetic.py`
**Methods:** `add`, `sub`, `mul`, `div`, `mod`, `pow`, `floor_div`, `neg`, `abs`, etc.
**Dunder methods:** `__add__`, `__sub__`, `__mul__`, `__truediv__`, etc.

**Note:** Shared across boolean and ternary facades (no logic-specific behavior)

### 2.5 NullNamespace

**Source:** `null_expression_builder.py` (~124 lines, 5 methods)
**Target:** `namespaces/null.py`
**Methods:** `is_null`, `is_not_null`, `fill_null`, `null_if`, `always_null`

### 2.6 TypeNamespace

**Source:** `type_expression_builder.py` (~41 lines, 1 method)
**Target:** `namespaces/type.py`
**Methods:** `cast`

### 2.7 IterableNamespace

**Source:** `iterable_expression_builder.py` (~86 lines, 3 methods)
**Target:** `namespaces/iterable.py`
**Methods:** `coalesce`, `greatest`, `least`

### 2.8 NativeNamespace

**Source:** `native_expression_builder.py` (~48 lines, 1 method)
**Target:** `namespaces/native.py`
**Methods:** `native`

---

## Phase 3: Namespace Conversion (Explicit Namespaces)

**Goal:** Convert remaining mixins to explicit namespace accessors (`.str`, `.dt`, `.name`).

### 3.1 StringNamespace

**Source:** `string_expression_builder.py` (~416 lines, 17 methods)
**Target:** `namespaces/string.py`
**Accessor:** `.str`

**Methods:**
- Case: `upper`, `lower`
- Trim: `strip`, `lstrip`, `rstrip`
- Manipulation: `slice`, `replace`, `concat`, `split`
- Properties: `len`
- Checks: `contains`, `starts_with`, `ends_with`
- Pattern: `like`, `regex_match`, `regex_contains`, `regex_replace`

**Mapping from old names:**
| Old Method | New Method |
|------------|------------|
| `str_upper()` | `.str.upper()` |
| `str_lower()` | `.str.lower()` |
| `str_trim()` | `.str.strip()` |
| `str_contains(x)` | `.str.contains(x)` |
| `pat_like(x)` | `.str.like(x)` |
| `pat_regex_match(x)` | `.str.regex_match(x)` |

### 3.2 DateNamespace (Temporal)

**Source:** `temporal_expression_builder.py` (~567 lines, 26 methods)
**Target:** `namespaces/date.py`
**Accessor:** `.dt`

**Methods:**
- Extract: `year`, `month`, `day`, `hour`, `minute`, `second`, `weekday`
- Manipulation: `add_days`, `add_hours`, `subtract_days`, etc.
- Difference: `diff_days`, `diff_hours`, `diff_minutes`, etc.
- Truncation: `truncate_to_day`, `truncate_to_hour`, etc.

**Mapping from old names:**
| Old Method | New Method |
|------------|------------|
| `dt_year()` | `.dt.year()` |
| `dt_add_days(n)` | `.dt.add_days(n)` |
| `dt_diff_hours(other)` | `.dt.diff_hours(other)` |

### 3.3 NameNamespace

**Source:** `name_expression_builder.py` (~128 lines, 5 methods)
**Target:** `namespaces/name.py`
**Accessor:** `.name`

**Methods:** `alias`, `prefix`, `suffix`, `to_upper`, `to_lower`

---

## Phase 4: Facade Assembly

### 4.1 BooleanExpressionAPI

**File:** `core/expression_api/boolean.py`

```python
class BooleanExpressionAPI(BaseExpressionAPI):
    _FLAT_NAMESPACES = (
        BooleanComparisonNamespace,
        BooleanLogicalNamespace,
        ArithmeticNamespace,
        NullNamespace,
        TypeNamespace,
        IterableNamespace,
        NativeNamespace,
    )

    str = NamespaceDescriptor(StringNamespace)
    dt = NamespaceDescriptor(DateNamespace)
    name = NamespaceDescriptor(NameNamespace)
```

### 4.2 TernaryExpressionAPI (Stub)

**File:** `core/expression_api/ternary.py`

```python
class TernaryExpressionAPI(BaseExpressionAPI):
    """Stub for future ternary logic implementation."""

    _FLAT_NAMESPACES = (
        # TernaryComparisonNamespace,  # Future
        # TernaryLogicalNamespace,     # Future
        ArithmeticNamespace,
        NullNamespace,
        TypeNamespace,
        IterableNamespace,
        NativeNamespace,
    )

    str = NamespaceDescriptor(StringNamespace)
    dt = NamespaceDescriptor(DateNamespace)
    name = NamespaceDescriptor(NameNamespace)
```

### 4.3 Update Factory Functions

**File:** `api/__init__.py`

```python
def col(name: str, logic: Literal["boolean", "ternary"] = "boolean") -> BaseExpressionAPI:
    """Create column reference."""
    from ..core.expression_nodes import ColumnExpressionNode
    from ..core.expression_api import BooleanExpressionAPI, TernaryExpressionAPI

    node = ColumnExpressionNode(name)
    if logic == "ternary":
        return TernaryExpressionAPI(node)
    return BooleanExpressionAPI(node)

def lit(value: Any, logic: Literal["boolean", "ternary"] = "boolean") -> BaseExpressionAPI:
    """Create literal value."""
    from ..core.expression_nodes import LiteralExpressionNode
    from ..core.expression_api import BooleanExpressionAPI, TernaryExpressionAPI

    node = LiteralExpressionNode(value)
    if logic == "ternary":
        return TernaryExpressionAPI(node)
    return BooleanExpressionAPI(node)

# Convenience aliases
def tcol(name: str) -> TernaryExpressionAPI:
    """Create ternary logic column reference."""
    return col(name, logic="ternary")

def tlit(value: Any) -> TernaryExpressionAPI:
    """Create ternary logic literal."""
    return lit(value, logic="ternary")
```

---

## Phase 5: Backwards Compatibility Layer

### 5.1 Flat Method Aliases on StringNamespace

For gradual migration, support both styles:

```python
# Old style (flat on API)
col("name").str_upper()

# New style (explicit namespace)
col("name").str.upper()
```

**Option A:** Keep flat methods as aliases
```python
class BooleanExpressionAPI(BaseExpressionAPI):
    def str_upper(self) -> Self:
        return self.str.upper()
```

**Option B:** Add `StringFlatNamespace` to `_FLAT_NAMESPACES` with old method names

**Recommendation:** Option B with deprecation warnings, remove in next major version.

### 5.2 Deprecate Old ExpressionBuilder

```python
# api/expression_builder.py
import warnings

class ExpressionBuilder(BooleanExpressionAPI):
    """Deprecated: Use BooleanExpressionAPI instead."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "ExpressionBuilder is deprecated. Use BooleanExpressionAPI instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
```

---

## Phase 6: Testing & Validation

### 6.1 Unit Tests for Infrastructure

- [ ] `test_descriptor.py` - Descriptor binding behavior
- [ ] `test_base_namespace.py` - Base namespace methods
- [ ] `test_base_api.py` - `__getattr__` dispatch, `create()` factory
- [ ] `test_coercion.py` - Ternary→boolean coercion

### 6.2 Unit Tests for Each Namespace

One test file per namespace:
- [ ] `test_comparison_namespace.py`
- [ ] `test_logical_namespace.py`
- [ ] `test_arithmetic_namespace.py`
- [ ] `test_string_namespace.py`
- [ ] `test_date_namespace.py`
- [ ] `test_name_namespace.py`
- [ ] `test_null_namespace.py`
- [ ] `test_type_namespace.py`
- [ ] `test_iterable_namespace.py`
- [ ] `test_native_namespace.py`

### 6.3 Integration Tests

- [ ] Cross-namespace chaining: `col("x").str.upper().name.alias("X").eq("HELLO")`
- [ ] Type preservation: `TernaryExpressionAPI` methods return `TernaryExpressionAPI`
- [ ] Compile works: `col("a").gt(5).compile(polars_df)` produces valid `pl.Expr`

### 6.4 Regression Tests

**All 703 existing tests must pass.**

Run after each phase:
```bash
hatch run test:test
```

---

## Phase 7: Cleanup

### 7.1 Move Old Mixins to `_deprecated/`

```
src/mountainash_expressions/core/expression_builders/
├── _deprecated/
│   ├── boolean_expression_builder.py
│   ├── arithmetic_expression_builder.py
│   └── ...
├── __init__.py  # Re-export from new location
└── base_expression_builder.py  # Keep (may still be useful)
```

### 7.2 Update CLAUDE.md

Document new architecture:
- Namespace structure
- How to add new operations
- How `__getattr__` dispatch works

### 7.3 Update Package Exports

```python
# mountainash_expressions/__init__.py
from .core.expression_api import (
    BaseExpressionAPI,
    BooleanExpressionAPI,
    TernaryExpressionAPI,
)
from .api import col, lit, tcol, tlit, filter, select, with_columns
```

---

## Execution Order

### Batch 1: Infrastructure (Phase 1)
1. Create directory structure
2. Implement `NamespaceDescriptor`
3. Implement `BaseNamespace`
4. Implement `BaseExpressionAPI`
5. Write infrastructure tests
6. **Checkpoint:** Basic dispatch works

### Batch 2: Core Flat Namespaces (Phase 2.1-2.4)
1. `BooleanComparisonNamespace`
2. `BooleanLogicalNamespace`
3. `ArithmeticNamespace`
4. Wire into `BooleanExpressionAPI`
5. **Checkpoint:** `col("a").eq(5).and_(col("b").gt(3))` works

### Batch 3: Supporting Flat Namespaces (Phase 2.5-2.8)
1. `NullNamespace`
2. `TypeNamespace`
3. `IterableNamespace`
4. `NativeNamespace`
5. **Checkpoint:** All flat methods work

### Batch 4: Explicit Namespaces (Phase 3)
1. `StringNamespace` + `.str` descriptor
2. `DateNamespace` + `.dt` descriptor
3. `NameNamespace` + `.name` descriptor
4. **Checkpoint:** `col("x").str.upper()` works

### Batch 5: Factory & Compat (Phases 4-5)
1. Update `col()`, `lit()` factories
2. Add `tcol()`, `tlit()` aliases
3. Add backwards compatibility layer
4. Deprecate old `ExpressionBuilder`
5. **Checkpoint:** All 703 tests pass

### Batch 6: Cleanup (Phases 6-7)
1. Move old code to `_deprecated/`
2. Update documentation
3. Final test run
4. **Checkpoint:** Ready for merge

---

## Risk Mitigation

### Risk 1: Import Cycles

**Mitigation:** Heavy use of `TYPE_CHECKING` guards. Namespace imports API type only for hints, never at runtime.

### Risk 2: Breaking Existing Tests

**Mitigation:**
- Keep old `ExpressionBuilder` as alias to `BooleanExpressionAPI`
- Run full test suite after each batch
- Don't delete old code until all tests pass

### Risk 3: IDE Autocomplete Breaks

**Mitigation:**
- Add `py.typed` marker
- Consider type stubs for `__getattr__` methods
- Document that explicit namespaces (`.str.`, `.dt.`) have full autocomplete

### Risk 4: Performance Regression

**Mitigation:**
- Namespace creation is cheap (just stores reference)
- Profile if concerned
- Can add `__slots__` to namespaces if needed
- Can cache namespace instances per API instance if hot path

---

## Success Criteria

1. ✅ All 703 existing tests pass
2. ✅ `BooleanExpressionAPI` works identically to old `ExpressionBuilder`
3. ✅ New explicit namespaces (`.str`, `.dt`, `.name`) work
4. ✅ Type preservation: `TernaryExpressionAPI.eq()` returns `TernaryExpressionAPI`
5. ✅ Coercion: Ternary nodes wrapped in `IS_TRUE` when used in boolean context
6. ✅ No import cycles at runtime
7. ✅ Documentation updated

---

## Estimated Effort

| Phase | Effort | Notes |
|-------|--------|-------|
| Phase 1: Infrastructure | 2-3 hours | Core plumbing |
| Phase 2: Flat Namespaces | 4-6 hours | 8 namespaces, mostly mechanical |
| Phase 3: Explicit Namespaces | 3-4 hours | 3 namespaces, larger files |
| Phase 4: Facade Assembly | 1-2 hours | Wiring |
| Phase 5: Backwards Compat | 1-2 hours | Aliases, deprecation |
| Phase 6: Testing | 2-3 hours | New tests |
| Phase 7: Cleanup | 1-2 hours | Documentation, moves |
| **Total** | **14-22 hours** | |

---

## Appendix: Method Inventory

### Flat Namespace Methods (accessed without prefix)

| Namespace | Methods | Count |
|-----------|---------|-------|
| BooleanComparison | eq, ne, gt, lt, ge, le, is_close, between | 8 |
| BooleanLogical | and_, or_, xor_, xor_parity, not_, is_true, is_false | 7 |
| BooleanCollection | is_in, is_not_in, always_true, always_false | 4 |
| Arithmetic | add, sub, mul, div, mod, pow, floor_div, neg, abs, round, ceil, floor, sqrt, exp, log, log10, sin, cos, tan, asin, acos, atan | 21 |
| Null | is_null, is_not_null, fill_null, null_if, always_null | 5 |
| Type | cast | 1 |
| Iterable | coalesce, greatest, least | 3 |
| Native | native | 1 |
| **Total** | | **50** |

### Explicit Namespace Methods (accessed with prefix)

| Namespace | Accessor | Methods | Count |
|-----------|----------|---------|-------|
| String | `.str` | upper, lower, strip, lstrip, rstrip, slice, replace, concat, split, len, contains, starts_with, ends_with, like, regex_match, regex_contains, regex_replace | 17 |
| Date | `.dt` | year, month, day, hour, minute, second, weekday, add_days, add_hours, add_minutes, add_seconds, subtract_days, subtract_hours, diff_days, diff_hours, diff_minutes, diff_seconds, truncate_to_day, truncate_to_hour, truncate_to_minute, truncate_to_second, date, time, timestamp | 26 |
| Name | `.name` | alias, prefix, suffix, to_upper, to_lower | 5 |
| **Total** | | | **48** |

### Dunder Methods (delegated to named methods)

| Dunder | Delegates To |
|--------|--------------|
| `__eq__` | `eq` |
| `__ne__` | `ne` |
| `__gt__` | `gt` |
| `__lt__` | `lt` |
| `__ge__` | `ge` |
| `__le__` | `le` |
| `__and__` | `and_` |
| `__or__` | `or_` |
| `__xor__` | `xor_` |
| `__invert__` | `not_` |
| `__add__` | `add` |
| `__sub__` | `sub` |
| `__mul__` | `mul` |
| `__truediv__` | `div` |
| `__floordiv__` | `floor_div` |
| `__mod__` | `mod` |
| `__pow__` | `pow` |
| `__neg__` | `neg` |
| `__abs__` | `abs` |
| `__radd__` | `add` (reversed) |
| `__rsub__` | `sub` (reversed) |
| `__rmul__` | `mul` (reversed) |
| `__rtruediv__` | `div` (reversed) |
