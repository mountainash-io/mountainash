# PyData Schema Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate pydata from the old `schema/` module to `typespec/` and `conform/`, eliminating SchemaConfig dependency, fixing the CastDataFrame bug, and restructuring egress around the conform compiler and relation API.

**Architecture:** Three phases executed sequentially. Phase 1 adds `custom_cast` to FieldSpec and rewires all ingress handlers to accept TypeSpec. Phase 2 restructures egress to use `compile_conform()` and `ma.relation(df).to_polars()`. Phase 3 deletes `schema/` entirely.

**Tech Stack:** mountainash typespec (TypeSpec, FieldSpec, CustomTypeRegistry), mountainash conform (compile_conform), mountainash relations (relation, to_polars), Polars, Narwhals.

---

## File Structure

**Files to modify:**

| File | Phase | Change |
|------|-------|--------|
| `src/mountainash/typespec/spec.py` | 1 | Add `custom_cast` field to FieldSpec |
| `src/mountainash/typespec/frictionless.py` | 1 | Serialize/deserialize `custom_cast` in x-mountainash |
| `src/mountainash/conform/builder.py` | 1 | Handle custom cast types in `_dict_to_spec()` |
| `src/mountainash/pydata/ingress/custom_type_helpers.py` | 1 | Add standalone `separate_conversions()`, rewrite `apply_hybrid_conversion()` |
| `src/mountainash/pydata/ingress/base_pydata_ingress_handler.py` | 1 | Signature: TypeSpec |
| `src/mountainash/pydata/ingress/pydata_ingress.py` | 1 | Signature: TypeSpec |
| `src/mountainash/pydata/ingress/pydata_ingress_factory.py` | 1 | TYPE_CHECKING import |
| `src/mountainash/pydata/ingress/ingress_from_pydict.py` | 1 | Import + signature + remove init_column_config |
| `src/mountainash/pydata/ingress/ingress_from_pylist.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_dataclass.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_pydantic.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_namedtuple.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_tuple.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_series.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_collection.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_indexed.py` | 1 | Import + signature |
| `src/mountainash/pydata/ingress/ingress_from_default.py` | 1 | Import + signature |
| `tests/pydata/test_hybrid_conversion.py` | 1 | Migrate to TypeSpec |
| `tests/pydata/test_ingress_handlers.py` | 1 | Update any SchemaConfig usage |
| `src/mountainash/pydata/egress/egress_helpers.py` | 2 | Replace SchemaTransformFactory with compile_conform |
| `src/mountainash/pydata/egress/egress_to_pythondata.py` | 2 | Fix CastDataFrame bug, update schema extraction |
| `src/mountainash/pydata/egress/base_egress_strategy.py` | 2 | Update type hints |
| `src/mountainash/pydata/egress/egress_pydata_from_polars.py` | 2 | Update schema-aware methods |
| `tests/pydata/test_egress_all.py` | 2 | Update schema-aware tests |
| `tests/pydata/test_pydata_roundtrips.py` | 2 | Update to TypeSpec |

**Files to delete (Phase 3):**

```
src/mountainash/schema/              (entire directory)
tests/schema/                        (entire directory)
```

---

### Task 1: Add `custom_cast` to FieldSpec + Frictionless round-trip

**Files:**
- Modify: `src/mountainash/typespec/spec.py`
- Modify: `src/mountainash/typespec/frictionless.py`
- Modify: `src/mountainash/conform/builder.py`
- Create: `tests/typespec/test_custom_cast.py`

- [ ] **Step 1: Write failing tests for custom_cast**

Create `tests/typespec/test_custom_cast.py`:

```python
"""Tests for custom_cast field on FieldSpec and Frictionless round-trip."""
from __future__ import annotations

import pytest

from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.frictionless import typespec_to_frictionless, typespec_from_frictionless
from mountainash.conform.builder import ConformBuilder


class TestFieldSpecCustomCast:
    """FieldSpec.custom_cast field behavior."""

    def test_custom_cast_default_none(self):
        field = FieldSpec(name="col")
        assert field.custom_cast is None

    def test_custom_cast_set(self):
        field = FieldSpec(name="amount", custom_cast="safe_float")
        assert field.custom_cast == "safe_float"
        assert field.type == UniversalType.STRING  # default type unchanged


class TestFrictionlessCustomCast:
    """custom_cast round-trips through Frictionless x-mountainash."""

    def test_export_custom_cast(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="amount", type=UniversalType.ANY, custom_cast="safe_float"),
        ])
        exported = typespec_to_frictionless(spec)
        assert exported["fields"][0]["x-mountainash"]["custom_cast"] == "safe_float"

    def test_import_custom_cast(self):
        data = {
            "fields": [{
                "name": "amount",
                "type": "any",
                "x-mountainash": {"custom_cast": "safe_float"},
            }],
        }
        spec = typespec_from_frictionless(data)
        assert spec.fields[0].custom_cast == "safe_float"

    def test_round_trip_custom_cast(self):
        original = TypeSpec(fields=[
            FieldSpec(name="amount", type=UniversalType.ANY, custom_cast="safe_float"),
            FieldSpec(name="id", type=UniversalType.INTEGER),
        ])
        exported = typespec_to_frictionless(original)
        reimported = typespec_from_frictionless(exported)
        assert reimported.fields[0].custom_cast == "safe_float"
        assert reimported.fields[1].custom_cast is None

    def test_no_custom_cast_no_extension(self):
        spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
        exported = typespec_to_frictionless(spec)
        assert "x-mountainash" not in exported["fields"][0]


class TestConformBuilderCustomCast:
    """ConformBuilder._dict_to_spec handles custom cast types."""

    def test_recognized_type_is_standard(self):
        builder = ConformBuilder({"id": {"cast": "integer"}})
        assert builder.spec.fields[0].type == UniversalType.INTEGER
        assert builder.spec.fields[0].custom_cast is None

    def test_unrecognized_type_is_custom(self):
        builder = ConformBuilder({"amount": {"cast": "safe_float"}})
        assert builder.spec.fields[0].type == UniversalType.ANY
        assert builder.spec.fields[0].custom_cast == "safe_float"

    def test_mixed_standard_and_custom(self):
        builder = ConformBuilder({
            "id": {"cast": "integer"},
            "amount": {"cast": "safe_float"},
            "label": {"rename_from": "raw_label"},
        })
        assert builder.spec.fields[0].custom_cast is None
        assert builder.spec.fields[1].custom_cast == "safe_float"
        assert builder.spec.fields[2].custom_cast is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/typespec/test_custom_cast.py -v`
Expected: FAIL — `AttributeError: 'FieldSpec' has no attribute 'custom_cast'`

- [ ] **Step 3: Add `custom_cast` to FieldSpec**

In `src/mountainash/typespec/spec.py`, add `custom_cast` field to the `FieldSpec` dataclass, after `rename_from`:

```python
    rename_from: Optional[str] = None
    custom_cast: Optional[str] = None  # Custom type name (e.g., "safe_float")
```

- [ ] **Step 4: Update Frictionless export to include custom_cast**

In `src/mountainash/typespec/frictionless.py`, in the `typespec_to_frictionless()` function, find the field-level x-mountainash block (around lines 121-128) and add custom_cast:

After `if fspec.null_fill is not None: field_extensions["null_fill"] = fspec.null_fill` add:

```python
        if fspec.custom_cast is not None:
            field_extensions["custom_cast"] = fspec.custom_cast
```

- [ ] **Step 5: Update Frictionless import to read custom_cast**

In `src/mountainash/typespec/frictionless.py`, in the `typespec_from_frictionless()` function, find where `rename_from` and `null_fill` are extracted (around lines 194-197) and add:

```python
        custom_cast: Optional[str] = field_ext.get("custom_cast")
```

Then add `custom_cast=custom_cast` to the `FieldSpec(...)` constructor call.

- [ ] **Step 6: Update ConformBuilder._dict_to_spec to handle custom casts**

In `src/mountainash/conform/builder.py`, read the current `_dict_to_spec()` method and replace its field-building logic. The key change: if `normalize_type(cast_str)` raises an exception, treat the cast as a custom type.

Find the current pattern (which does `normalize_type(config["cast"]) if "cast" in config else UniversalType.ANY`) and replace with:

```python
        cast_str = config.get("cast")
        if cast_str is not None:
            try:
                utype = normalize_type(cast_str)
                custom = None
            except (ValueError, KeyError):
                utype = UniversalType.ANY
                custom = cast_str
        else:
            utype = UniversalType.ANY
            custom = None

        fields.append(FieldSpec(
            name=target_name,
            type=utype,
            custom_cast=custom,
            rename_from=config.get("rename_from"),
            null_fill=config.get("null_fill"),
        ))
```

- [ ] **Step 7: Run tests**

Run: `hatch run test:test-target tests/typespec/test_custom_cast.py -v`
Expected: PASS (all 9 tests)

Also verify existing tests still pass:
Run: `hatch run test:test-target tests/typespec/ tests/conform/ -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/typespec/spec.py src/mountainash/typespec/frictionless.py src/mountainash/conform/builder.py tests/typespec/test_custom_cast.py
git commit -m "feat: add custom_cast field to FieldSpec with Frictionless round-trip"
```

---

### Task 2: Add standalone `separate_conversions()` and rewrite `apply_hybrid_conversion()`

The architectural heart of the ingress pipeline — move three-tier routing from SchemaConfig into a standalone function.

**Files:**
- Modify: `src/mountainash/pydata/ingress/custom_type_helpers.py`
- Modify: `tests/pydata/test_hybrid_conversion.py`

- [ ] **Step 1: Write failing tests for the new separate_conversions()**

Update `tests/pydata/test_hybrid_conversion.py`. Replace the entire file contents. The new tests use `TypeSpec`/`FieldSpec` instead of `SchemaConfig`:

```python
"""Tests for three-tier hybrid conversion pipeline.

Tests the ingress hybrid strategy that splits conversions into:
- TIER 3: Python-only custom (row-by-row at edges)
- TIER 2: Narwhals custom (vectorized expressions)
- TIER 1: Native casts (vectorized in DataFrame via conform compiler)
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.ingress.custom_type_helpers import (
    apply_custom_converters_to_dict,
    apply_custom_converters_to_dicts,
    apply_hybrid_conversion,
    apply_native_conversions_to_dataframe,
    _apply_narwhals_custom_converters,
    separate_conversions,
)
from mountainash.typespec.custom_types import _register_standard_converters
from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType


@pytest.fixture(autouse=True)
def ensure_standard_converters():
    """Ensure standard converters (safe_float, etc.) are registered."""
    _register_standard_converters()


# =============================================================================
# separate_conversions() — routing logic
# =============================================================================

class TestSeparateConversions:
    """separate_conversions() routes FieldSpecs into three tiers."""

    def test_native_integer(self):
        spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
        python_only, narwhals, native = separate_conversions(spec)
        assert "id" in native
        assert len(python_only) == 0
        assert len(narwhals) == 0

    def test_custom_safe_float_is_narwhals(self):
        spec = TypeSpec(fields=[FieldSpec(name="amount", custom_cast="safe_float")])
        python_only, narwhals, native = separate_conversions(spec)
        assert "amount" in narwhals
        assert len(python_only) == 0
        assert len(native) == 0

    def test_no_cast_is_native(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="new_name", type=UniversalType.ANY, rename_from="old_name"),
        ])
        python_only, narwhals, native = separate_conversions(spec)
        assert "old_name" in native
        assert len(python_only) == 0
        assert len(narwhals) == 0

    def test_mixed_routing(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="amount", custom_cast="safe_float"),
            FieldSpec(name="label", type=UniversalType.ANY, rename_from="raw_label"),
        ])
        python_only, narwhals, native = separate_conversions(spec)
        assert "id" in native
        assert "amount" in narwhals
        assert "raw_label" in native
        assert len(python_only) == 0


# =============================================================================
# TIER 3: Python-only custom converters
# =============================================================================

class TestTier3PythonEdge:
    """apply_custom_converters_to_dict/dicts — Python layer conversions."""

    def test_single_dict_safe_float(self):
        custom = {"amount": FieldSpec(name="amount", custom_cast="safe_float")}
        result = apply_custom_converters_to_dict(
            {"amount": "123.45", "name": "test"},
            custom,
        )
        assert isinstance(result["amount"], float)
        assert result["amount"] == pytest.approx(123.45)
        assert result["name"] == "test"

    def test_list_of_dicts(self):
        custom = {"amount": FieldSpec(name="amount", custom_cast="safe_float")}
        data = [
            {"amount": "1.5", "name": "a"},
            {"amount": "2.5", "name": "b"},
        ]
        result = apply_custom_converters_to_dicts(data, custom)
        assert result[0]["amount"] == pytest.approx(1.5)
        assert result[1]["amount"] == pytest.approx(2.5)

    def test_empty_conversions_passthrough(self):
        data = [{"x": 1}]
        result = apply_custom_converters_to_dicts(data, {})
        assert result == [{"x": 1}]

    def test_none_value_safe_float(self):
        custom = {"amount": FieldSpec(name="amount", custom_cast="safe_float")}
        result = apply_custom_converters_to_dict({"amount": None}, custom)
        assert result["amount"] is None


# =============================================================================
# TIER 1: Native DataFrame conversions
# =============================================================================

class TestTier1NativeDataFrame:
    """apply_native_conversions_to_dataframe — vectorized casts."""

    def test_integer_cast(self):
        df = pl.DataFrame({"id": ["1", "2", "3"]})
        native = {"id": FieldSpec(name="id", type=UniversalType.INTEGER)}
        result = apply_native_conversions_to_dataframe(df, native)
        assert result["id"].dtype == pl.Int64

    def test_empty_conversions_passthrough(self):
        df = pl.DataFrame({"x": [1, 2]})
        result = apply_native_conversions_to_dataframe(df, {})
        assert result["x"].to_list() == [1, 2]


# =============================================================================
# TIER 2: Narwhals vectorized custom converters
# =============================================================================

class TestTier2NarwhalsVectorized:
    """_apply_narwhals_custom_converters — vectorized custom conversions."""

    def test_safe_float_vectorized(self):
        df = pl.DataFrame({"amount": ["1.5", "2.5", "bad", None]})
        narwhals_custom = {"amount": FieldSpec(name="amount", custom_cast="safe_float")}
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        vals = result["amount"].to_list()
        assert vals[0] == pytest.approx(1.5)
        assert vals[1] == pytest.approx(2.5)
        assert vals[3] is None


# =============================================================================
# End-to-end hybrid conversion
# =============================================================================

class TestHybridEndToEnd:
    """apply_hybrid_conversion — full three-tier pipeline."""

    def test_native_only(self):
        spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
        result = apply_hybrid_conversion(
            [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            spec,
        )
        assert isinstance(result, pl.DataFrame)
        assert result["id"].dtype == pl.Int64

    def test_no_spec_creates_dataframe(self):
        result = apply_hybrid_conversion(
            [{"x": 1}, {"x": 2}],
            None,
        )
        assert isinstance(result, pl.DataFrame)
        assert result["x"].to_list() == [1, 2]

    def test_safe_float_end_to_end(self):
        spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="amount", custom_cast="safe_float"),
        ])
        result = apply_hybrid_conversion(
            [{"id": "1", "amount": "9.99"}, {"id": "2", "amount": "bad"}],
            spec,
        )
        assert result["id"].dtype == pl.Int64
        assert result["amount"][0] == pytest.approx(9.99)

    def test_tier_assignment(self):
        """safe_float routes to narwhals tier, integer routes to native."""
        spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="amount", custom_cast="safe_float"),
        ])
        python_only, narwhals, native = separate_conversions(spec)
        assert "amount" in narwhals
        assert "id" in native
        assert len(python_only) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `hatch run test:test-target tests/pydata/test_hybrid_conversion.py -v`
Expected: FAIL — `ImportError: cannot import name 'separate_conversions'`

- [ ] **Step 3: Implement separate_conversions() and rewrite custom_type_helpers.py**

Read `src/mountainash/pydata/ingress/custom_type_helpers.py` fully, then rewrite it. The key changes:

1. **Replace imports**: Remove `SchemaConfig` imports, add `TypeSpec`, `FieldSpec`, `UniversalType` imports
2. **Add `separate_conversions(spec: TypeSpec)`**: standalone function (from spec)
3. **Update `apply_custom_converters_to_dict()`**: Accept `dict[str, FieldSpec]` instead of `dict[str, dict]`. Extract `cast_type` from `field_spec.custom_cast` instead of `spec["cast"]`.
4. **Update `apply_custom_converters_to_dicts()`**: Same — accept FieldSpec dict
5. **Update `apply_native_conversions_to_dataframe()`**: Accept `dict[str, FieldSpec]` instead of `dict[str, dict]`. Use conform compiler instead of SchemaConfig.apply(). Extract cast type from `field_spec.type.value`.
6. **Update `_apply_narwhals_custom_converters()`**: Accept `dict[str, FieldSpec]`. Extract cast_type from `field_spec.custom_cast`. Extract target_name from `field_spec.name`.
7. **Rewrite `apply_hybrid_conversion()`**: Accept `Optional[TypeSpec]` instead of `Optional[SchemaConfig]`. Call standalone `separate_conversions()`. Use FieldSpec-based helper functions.

The implementation for each function follows the same pattern: where the old code accessed `spec["cast"]`, the new code accesses `field_spec.custom_cast` or `field_spec.type.value`. Where the old code used `spec.get("rename", col)`, the new code uses `field_spec.name`.

- [ ] **Step 4: Run hybrid conversion tests**

Run: `hatch run test:test-target tests/pydata/test_hybrid_conversion.py -v`
Expected: PASS

- [ ] **Step 5: Run all pydata tests to check for regressions**

Run: `hatch run test:test-target tests/pydata/ -v`
Expected: PASS (or identify failures to fix in next step)

- [ ] **Step 6: Commit**

```bash
git add src/mountainash/pydata/ingress/custom_type_helpers.py tests/pydata/test_hybrid_conversion.py
git commit -m "feat: add standalone separate_conversions() and rewrite hybrid pipeline for TypeSpec"
```

---

### Task 3: Rewire all ingress handlers and entry points to TypeSpec

Mechanical migration — change signatures and imports in 13 files.

**Files:**
- Modify: `src/mountainash/pydata/ingress/base_pydata_ingress_handler.py`
- Modify: `src/mountainash/pydata/ingress/pydata_ingress.py`
- Modify: `src/mountainash/pydata/ingress/pydata_ingress_factory.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_pydict.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_pylist.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_dataclass.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_pydantic.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_namedtuple.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_tuple.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_series.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_collection.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_indexed.py`
- Modify: `src/mountainash/pydata/ingress/ingress_from_default.py`
- Modify: `tests/pydata/test_ingress_handlers.py` (if it uses SchemaConfig)

- [ ] **Step 1: Update base handler signature**

In `src/mountainash/pydata/ingress/base_pydata_ingress_handler.py`:

Replace the `column_config` parameter:
```python
# Before:
from mountainash.schema.config import SchemaConfig

def convert(cls, data: Any, /, column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None) -> PolarsFrame:

# After:
from mountainash.typespec.spec import TypeSpec

def convert(cls, data: Any, /, type_spec: Optional[TypeSpec] = None) -> PolarsFrame:
```

- [ ] **Step 2: Update PydataIngress entry point**

In `src/mountainash/pydata/ingress/pydata_ingress.py`:

Replace imports and signature:
```python
# Before:
def convert(cls, data: Any, /, column_config: Optional[Union["SchemaConfig", Dict[str, Any], str]] = None) -> PolarsFrame:
    strategy = PydataIngressFactory.get_strategy(data)
    return strategy.convert(data, column_config=column_config)

# After:
def convert(cls, data: Any, /, type_spec: Optional["TypeSpec"] = None) -> PolarsFrame:
    strategy = PydataIngressFactory.get_strategy(data)
    return strategy.convert(data, type_spec=type_spec)
```

- [ ] **Step 3: Update pydata_ingress_factory.py TYPE_CHECKING import**

Replace `SchemaConfig` TYPE_CHECKING import with `TypeSpec`.

- [ ] **Step 4: Update all 11 ingress handlers**

Each handler follows the same pattern. Read each file, then apply these changes:

**For each handler** (`ingress_from_pydict.py`, `ingress_from_pylist.py`, etc.):

1. Replace import:
```python
# Before:
from mountainash.schema.config import SchemaConfig, init_column_config
# After:
from mountainash.typespec.spec import TypeSpec
```

2. Replace signature:
```python
# Before:
def convert(cls, data: Any, /, column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None) -> PolarsFrame:
# After:
def convert(cls, data: Any, /, type_spec: Optional[TypeSpec] = None) -> PolarsFrame:
```

3. Replace body logic:
```python
# Before:
if column_config is not None:
    from .custom_type_helpers import apply_hybrid_conversion
    column_transforms: SchemaConfig = init_column_config(column_config)
    # ... convert to data_dicts ...
    df = apply_hybrid_conversion(data_dicts, column_transforms)

# After:
if type_spec is not None:
    from .custom_type_helpers import apply_hybrid_conversion
    # ... convert to data_dicts ...
    df = apply_hybrid_conversion(data_dicts, type_spec)
```

The `init_column_config()` call is removed entirely — callers pass TypeSpec directly.

- [ ] **Step 5: Update test_ingress_handlers.py if needed**

Read `tests/pydata/test_ingress_handlers.py` and check if any tests pass `column_config=SchemaConfig(...)`. If so, update them to pass `type_spec=TypeSpec(...)`.

If tests only call `PydataIngress.convert(data)` without a config (most likely), no changes needed.

- [ ] **Step 6: Run all pydata tests**

Run: `hatch run test:test-target tests/pydata/ -v`
Expected: ALL PASS

- [ ] **Step 7: Verify no remaining schema imports in ingress**

Run: `grep -r "mountainash.schema" src/mountainash/pydata/ingress/ --include="*.py"`
Expected: Zero hits

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/pydata/ingress/ tests/pydata/
git commit -m "refactor: rewire all ingress handlers from SchemaConfig to TypeSpec"
```

---

### Task 4: Restructure egress — replace SchemaTransformFactory and fix CastDataFrame

**Files:**
- Modify: `src/mountainash/pydata/egress/egress_helpers.py`
- Modify: `src/mountainash/pydata/egress/egress_to_pythondata.py`
- Modify: `src/mountainash/pydata/egress/base_egress_strategy.py`
- Modify: `src/mountainash/pydata/egress/egress_pydata_from_polars.py`
- Modify: `tests/pydata/test_egress_all.py` (if SchemaConfig used)
- Modify: `tests/pydata/test_pydata_roundtrips.py` (if SchemaConfig used)

- [ ] **Step 1: Rewrite egress_helpers.py**

Read `src/mountainash/pydata/egress/egress_helpers.py` fully, then apply these changes:

1. **Replace imports**:
```python
# Remove:
from mountainash.schema.config import SchemaConfig
from mountainash.schema.transform import SchemaTransformFactory

# Add:
from mountainash.typespec.spec import TypeSpec, FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.pydata.ingress.custom_type_helpers import separate_conversions
```

2. **Rewrite `apply_native_conversions_for_egress()`** to accept TypeSpec and use compile_conform:
```python
def apply_native_conversions_for_egress(
    df: Any,
    spec: TypeSpec,
) -> tuple[Any, dict[str, FieldSpec]]:
    """Apply native + narwhals conversions, return conformed DataFrame and deferred custom specs."""
    import polars as pl

    python_only, narwhals_custom, native = separate_conversions(spec)

    conform_fields = [f for f in spec.fields if f.source_name not in python_only]
    if conform_fields:
        conform_spec = TypeSpec(fields=conform_fields, keep_only_mapped=spec.keep_only_mapped)
        from mountainash.conform.compiler import compile_conform
        df = compile_conform(conform_spec, df)
    elif not isinstance(df, pl.DataFrame):
        import mountainash as ma
        df = ma.relation(df).to_polars()

    return df, python_only
```

3. **Update `apply_custom_converters_to_python_data()`** to accept `dict[str, FieldSpec]` for custom converters instead of using SchemaConfig.

4. **Update `apply_hybrid_egress_conversion()`** to accept TypeSpec.

5. **Update `_apply_custom_to_dicts()` and `_apply_custom_to_namedtuples()`** to work with FieldSpec (extract `custom_cast` and `name` from FieldSpec instead of dict `"cast"` and `"rename"` keys).

- [ ] **Step 2: Fix CastDataFrame bug in egress_to_pythondata.py**

Read `src/mountainash/pydata/egress/egress_to_pythondata.py` fully, then:

1. **Remove broken import**:
```python
# Remove:
from mountainash.schema.transform import CastDataFrame
```

2. **Replace all 11 `CastDataFrame.to_polars_eager(df)` calls** with:
```python
import mountainash as ma
pl_df = ma.relation(df).to_polars()
```

3. **Update schema extraction imports**:
```python
# Before:
from mountainash.schema.config import (
    SchemaConfig,
    extract_schema_from_dataframe,
    extract_schema_from_dataclass,
    build_schema_config_with_fuzzy_matching,
    extract_schema_from_pydantic
)

# After:
from mountainash.typespec.extraction import (
    extract_from_dataframe,
    extract_from_dataclass,
    extract_from_pydantic,
)
```

4. **Update `_to_list_of_dataclasses()` and `_to_list_of_pydantic()`** to use TypeSpec instead of SchemaConfig for schema derivation.

- [ ] **Step 3: Update base_egress_strategy.py type hints**

Read `src/mountainash/pydata/egress/base_egress_strategy.py` and replace any `SchemaConfig` type hints with `TypeSpec`.

- [ ] **Step 4: Update egress_pydata_from_polars.py if needed**

Read `src/mountainash/pydata/egress/egress_pydata_from_polars.py` and update any SchemaConfig references.

- [ ] **Step 5: Update egress tests**

Read `tests/pydata/test_egress_all.py` and `tests/pydata/test_pydata_roundtrips.py`. Update any SchemaConfig usage to TypeSpec.

- [ ] **Step 6: Run all pydata tests**

Run: `hatch run test:test-target tests/pydata/ -v`
Expected: ALL PASS

- [ ] **Step 7: Verify no remaining schema imports in egress**

Run: `grep -r "mountainash.schema" src/mountainash/pydata/egress/ --include="*.py"`
Expected: Zero hits

- [ ] **Step 8: Commit**

```bash
git add src/mountainash/pydata/egress/ tests/pydata/
git commit -m "refactor: restructure egress — replace SchemaTransformFactory with compile_conform, fix CastDataFrame bug"
```

---

### Task 5: Delete schema/ module and tests

**Files:**
- Delete: `src/mountainash/schema/` (entire directory)
- Delete: `tests/schema/` (entire directory)

- [ ] **Step 1: Verify no remaining schema imports anywhere**

Run: `grep -r "mountainash\.schema" src/ tests/ --include="*.py" | grep -v __pycache__`

Expected: Zero hits. If any remain, fix them before proceeding.

- [ ] **Step 2: Delete schema module and tests**

```bash
rm -rf src/mountainash/schema/
rm -rf tests/schema/
```

- [ ] **Step 3: Run full test suite**

Run: `hatch run test:test-quick`
Expected: ALL PASS (4,300+ tests, 0 failures)

- [ ] **Step 4: Verify schema is gone**

```bash
find src/mountainash/schema -name "*.py" 2>/dev/null | wc -l
# Expected: 0

find tests/schema -name "*.py" 2>/dev/null | wc -l
# Expected: 0
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: delete schema/ module — fully replaced by typespec/ and conform/"
```

---

### Task 6: Full test suite verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `hatch run test:test`
Expected: ALL PASS

- [ ] **Step 2: Run pydata tests specifically**

Run: `hatch run test:test-target tests/pydata/ -v`
Expected: ALL PASS (101+)

- [ ] **Step 3: Run typespec tests**

Run: `hatch run test:test-target tests/typespec/ -v`
Expected: ALL PASS (300+)

- [ ] **Step 4: Run conform tests**

Run: `hatch run test:test-target tests/conform/ -v`
Expected: ALL PASS (80+)

- [ ] **Step 5: Run integration tests**

Run: `hatch run test:test-target tests/integration/ -v`
Expected: ALL PASS

- [ ] **Step 6: Final grep for any schema references**

Run: `grep -r "mountainash\.schema\|SchemaConfig\|SchemaTransformFactory\|CastDataFrame\|init_column_config" src/ tests/ --include="*.py" | grep -v __pycache__`
Expected: Zero hits (or only in comments/docs)
