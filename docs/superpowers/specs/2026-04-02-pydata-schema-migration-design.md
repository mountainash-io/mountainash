# PyData Schema Migration: Rewire to TypeSpec & Conform

> **For agentic workers:** This spec migrates the pydata module from the old `schema/` module to `typespec/` and `conform/`. Three phases: ingress rewire, egress restructure, SchemaConfig deletion.

**Goal:** Eliminate pydata's dependency on the old `schema/` module by migrating ingress to consume `TypeSpec`, restructuring egress around `compile_conform()` and relation API terminals, and deleting `SchemaConfig` and all remaining schema shims.

**Motivation:** The `schema/` module is now a thin shim layer over `typespec/`. Pydata is the sole remaining consumer of `SchemaConfig`, `init_column_config()`, and `SchemaTransformFactory`. Additionally, egress has a pre-existing bug: `CastDataFrame` is imported but was never ported from the old `mountainash-dataframes` repo. This migration eliminates the shim layer, fixes the bug, and simplifies egress by using the relation API.

---

## Current Architecture

### Ingress (Python data → Polars DataFrame)

```
Python data → PydataIngressFactory.get_strategy(data) → Handler.convert(data, column_config)
    → apply_hybrid_conversion(data_dicts, schema_config)  [if config provided]
        → SchemaConfig.separate_conversions()  →  3 tiers:
            TIER 3: Python-only custom (row-by-row at edges)
            TIER 1: Native casts (vectorized in DataFrame)
            TIER 2: Narwhals custom (vectorized expressions)
    → Polars DataFrame
```

**11 ingress handlers** all accept `Optional[SchemaConfig | Dict | str]` and delegate to `apply_hybrid_conversion()` when a config is provided.

### Egress (DataFrame → Python collections)

```
DataFrame → apply_native_conversions_for_egress(df, schema_config)
    → SchemaTransformFactory.get_strategy(df).apply(df, config)  [native tier]
    → CastDataFrame.to_polars_eager(df)  [BUG: class doesn't exist]
    → Polars extraction (.to_dicts(), .iter_rows(), etc.)
    → apply_custom_converters_to_python_data()  [custom tier]
    → Final Python data
```

### Dependencies on schema/

| Import | Files | Status |
|--------|-------|--------|
| `SchemaConfig` | 25+ files | Replace with TypeSpec |
| `init_column_config()` | 11 ingress handlers | Remove — callers pass TypeSpec directly |
| `SchemaConfig.separate_conversions()` | `custom_type_helpers.py` | Move to standalone function |
| `SchemaTransformFactory` | `egress_helpers.py` | Replace with `compile_conform()` |
| `CastDataFrame` | `egress_to_pythondata.py` | Replace with `ma.relation(df).to_polars()` |
| `CustomTypeRegistry` | 3 files | Already in `typespec.custom_types` |
| `normalize_type`, `get_polars_type` | `custom_type_helpers.py` | Already in `typespec.universal_types` |

---

## Phase 1: Ingress Rewire

### Signature Changes

**`BasePydataIngressHandler`:**
```python
# Before:
def convert(cls, data, column_config: Optional[SchemaConfig|Dict|str] = None) -> PolarsFrame

# After:
def convert(cls, data, type_spec: Optional[TypeSpec] = None) -> PolarsFrame
```

**`PydataIngress`:**
```python
# Before:
def convert(cls, data, column_config=None) -> PolarsFrame

# After:
def convert(cls, data, type_spec: Optional[TypeSpec] = None) -> PolarsFrame
```

All 11 handlers updated to match. The `init_column_config()` normalization is removed — callers are responsible for providing a `TypeSpec` (per the design decision to accept TypeSpec only).

### Custom Type Handling in FieldSpec

Custom cast types like "safe_float", "rich_boolean", and "xml_string" are not `UniversalType` enum values — they're strings registered in `CustomTypeRegistry`. In the current `SchemaConfig`, columns carry `{"cast": "safe_float"}` as a raw string.

`FieldSpec.type` is a `UniversalType` enum which cannot represent custom types. To support the three-tier routing, `FieldSpec` gets a new optional field:

```python
@dataclass
class FieldSpec:
    # ... existing fields ...
    custom_cast: str | None = None  # Custom type name (e.g., "safe_float")
```

When `custom_cast` is set, it takes precedence over `type` for the purposes of `separate_conversions()`. The `type` field retains its meaning as the Frictionless-aligned target type for native casts.

The `ConformBuilder._dict_to_spec()` method is updated: if the "cast" value is not a recognized `UniversalType`, it's treated as a custom cast name:

```python
@staticmethod
def _dict_to_spec(columns: dict) -> TypeSpec:
    fields = []
    for target_name, config in columns.items():
        cast_str = config.get("cast")
        try:
            utype = normalize_type(cast_str) if cast_str else UniversalType.ANY
            custom = None
        except (ValueError, KeyError):
            # Not a standard type — treat as custom cast
            utype = UniversalType.ANY
            custom = cast_str
        fields.append(FieldSpec(
            name=target_name,
            type=utype,
            custom_cast=custom,
            rename_from=config.get("rename_from"),
            null_fill=config.get("null_fill"),
        ))
    return TypeSpec(fields=fields)
```

### Standalone `separate_conversions()`

Move the routing logic from `SchemaConfig.separate_conversions()` into `custom_type_helpers.py` as a standalone function:

```python
def separate_conversions(
    spec: TypeSpec,
) -> tuple[dict[str, FieldSpec], dict[str, FieldSpec], dict[str, FieldSpec]]:
    """Route TypeSpec fields into three conversion tiers.

    Checks each field's cast type against CustomTypeRegistry to determine
    whether it should be handled as a native conversion (vectorized DataFrame
    operations), a Narwhals-vectorized custom conversion, or a Python-only
    custom conversion applied at edges.

    Args:
        spec: The TypeSpec defining target column types.

    Returns:
        Tuple of (python_only_custom, narwhals_custom, native_conversions).
        Each is a dict mapping source column name to FieldSpec.
    """
    from mountainash.typespec.custom_types import CustomTypeRegistry

    python_only: dict[str, FieldSpec] = {}
    narwhals: dict[str, FieldSpec] = {}
    native: dict[str, FieldSpec] = {}

    for field in spec.fields:
        # Custom cast takes precedence over standard type
        cast_type = field.custom_cast or (
            field.type.value if field.type != UniversalType.ANY else None
        )

        if cast_type is None:
            # No cast — rename/null_fill only → native tier
            native[field.source_name] = field
            continue

        if CustomTypeRegistry.has_converter(cast_type):
            if CustomTypeRegistry.is_vectorized(cast_type):
                narwhals[field.source_name] = field
            else:
                python_only[field.source_name] = field
        else:
            native[field.source_name] = field

    return python_only, narwhals, native
```

### `apply_hybrid_conversion()`

Updated to accept `TypeSpec`:

```python
def apply_hybrid_conversion(data_dicts: list[dict], spec: TypeSpec) -> pl.DataFrame:
    """Apply three-tier hybrid conversion to Python data.

    Args:
        data_dicts: List of row dicts.
        spec: TypeSpec defining target column types.

    Returns:
        Polars DataFrame with all conversions applied.
    """
    python_only, narwhals_custom, native = separate_conversions(spec)

    # TIER 3: Python-only custom at edges (row-by-row)
    if python_only:
        data_dicts = [apply_custom_converters_to_dict(d, python_only) for d in data_dicts]

    # Create DataFrame
    df = pl.DataFrame(data_dicts, strict=False)

    # TIER 2: Narwhals custom (vectorized expressions)
    if narwhals_custom:
        df = _apply_narwhals_custom_converters(df, narwhals_custom)

    # TIER 1: Native conversions via conform compiler
    if native:
        native_spec = TypeSpec(fields=[f for f in spec.fields if f.source_name in native])
        from mountainash.conform.compiler import compile_conform
        df = compile_conform(native_spec, df)

    return df
```

### Import Updates

All 11 handlers + base class + factory:

```python
# Before:
from mountainash.schema.config import SchemaConfig, init_column_config

# After:
from mountainash.typespec.spec import TypeSpec
```

### Files Changed (Phase 1)

| File | Change |
|------|--------|
| `ingress/base_pydata_ingress_handler.py` | Signature: `SchemaConfig` → `TypeSpec` |
| `ingress/pydata_ingress.py` | Signature + remove `init_column_config` |
| `ingress/pydata_ingress_factory.py` | TYPE_CHECKING import update |
| `ingress/custom_type_helpers.py` | Add standalone `separate_conversions()`, update `apply_hybrid_conversion()` to accept TypeSpec, update helper functions to work with FieldSpec |
| `ingress/ingress_from_pydict.py` | Import + signature |
| `ingress/ingress_from_pylist.py` | Import + signature |
| `ingress/ingress_from_dataclass.py` | Import + signature |
| `ingress/ingress_from_pydantic.py` | Import + signature |
| `ingress/ingress_from_namedtuple.py` | Import + signature |
| `ingress/ingress_from_tuple.py` | Import + signature |
| `ingress/ingress_from_series.py` | Import + signature |
| `ingress/ingress_from_collection.py` | Import + signature |
| `ingress/ingress_from_indexed.py` | Import + signature |
| `ingress/ingress_from_default.py` | Import + signature |

---

## Phase 2: Egress Restructure

### Replace SchemaTransformFactory with compile_conform

**`egress_helpers.py` — `apply_native_conversions_for_egress()`:**

```python
# Before:
def apply_native_conversions_for_egress(df, schema_config):
    native_config = SchemaConfig(columns=native_only_columns)
    factory = SchemaTransformFactory()
    strategy = factory.get_strategy(df)
    return strategy.apply(df, native_config)

# After:
def apply_conversions_for_egress(
    df, spec: TypeSpec
) -> tuple[pl.DataFrame, dict[str, FieldSpec]]:
    """Apply native + narwhals conversions, return conformed DataFrame and deferred custom specs.

    Args:
        df: Source DataFrame (any backend).
        spec: TypeSpec defining target columns.

    Returns:
        Tuple of (conformed Polars DataFrame, python-only custom FieldSpecs to apply post-extraction).
    """
    python_only, narwhals_custom, native = separate_conversions(spec)

    # Build conform spec for all non-python-only fields
    conform_fields = [f for f in spec.fields if f.source_name not in python_only]
    if conform_fields:
        conform_spec = TypeSpec(fields=conform_fields, keep_only_mapped=spec.keep_only_mapped)
        from mountainash.conform.compiler import compile_conform
        df = compile_conform(conform_spec, df)
    elif not isinstance(df, pl.DataFrame):
        # No conform needed but still need Polars conversion
        import mountainash as ma
        df = ma.relation(df).to_polars()

    return df, python_only
```

### Fix CastDataFrame Bug

**`egress_to_pythondata.py`:**

```python
# Before (11 occurrences, BUG — CastDataFrame doesn't exist):
from mountainash.schema.transform import CastDataFrame
pl_df = CastDataFrame.to_polars_eager(df)

# After:
import mountainash as ma
pl_df = ma.relation(df).to_polars()
```

This fixes the pre-existing import bug and uses the proven relation egress path.

### Egress Helpers — Python Custom Converters

`apply_custom_converters_to_python_data()` stays largely unchanged — it operates on extracted Python data (list of dicts or list of named tuples). The only change is that it accepts `dict[str, FieldSpec]` instead of `dict[str, dict]` for the custom converter specs.

### Schema-Aware Conversions

`egress_to_pythondata.py` methods `_to_list_of_dataclasses()` and `_to_list_of_pydantic()` currently use `extract_schema_from_dataframe()` and `build_schema_config_with_fuzzy_matching()` to auto-derive schemas. These update to use `typespec.extraction.extract_from_dataframe()` and work with `TypeSpec` instead of `SchemaConfig`.

### Files Changed (Phase 2)

| File | Change |
|------|--------|
| `egress/egress_helpers.py` | Replace SchemaTransformFactory with compile_conform, accept TypeSpec |
| `egress/egress_to_pythondata.py` | Replace CastDataFrame with `ma.relation(df).to_polars()`, update schema extraction to typespec |
| `egress/egress_pydata_from_polars.py` | Update schema-aware methods to use TypeSpec |
| `egress/base_egress_strategy.py` | Update type hints from SchemaConfig to TypeSpec |

---

## Phase 3: Delete SchemaConfig and Remaining Shims

### Files to Delete

```
src/mountainash/schema/config/schema_config.py    (~1,000 lines)
src/mountainash/schema/config/__init__.py          (shim)
src/mountainash/schema/config/types.py             (shim → typespec.universal_types)
src/mountainash/schema/config/universal_schema.py  (shim → typespec.spec)
src/mountainash/schema/config/extractors.py        (shim → typespec.extraction)
src/mountainash/schema/config/validators.py        (shim → typespec.validation)
src/mountainash/schema/config/converters.py        (shim → typespec.converters)
src/mountainash/schema/config/custom_types.py      (shim → typespec.custom_types)
src/mountainash/schema/__init__.py                 (empty shell)
tests/schema/                                      (entire directory)
```

**Total deleted:** ~2,500 lines of schema code + ~1,800 lines of schema tests.

### Verification

After deletion:
- `grep -r "mountainash.schema" src/ tests/` returns zero hits
- Full test suite passes (4,300+ tests)
- Pydata tests pass (101+)
- Conform tests pass (80+)
- TypeSpec tests pass (300+)

---

## Test Plan

### Phase 1 Tests

Existing pydata tests should pass with minimal changes:
- `test_hybrid_conversion.py` — update imports, use TypeSpec instead of SchemaConfig
- `test_ingress_factory.py` — no change (tests detection, not conversion)
- `test_ingress_handlers.py` — update any tests that pass SchemaConfig

### Phase 2 Tests

- `test_egress_all.py` — update any schema-aware egress tests
- `test_egress_factory.py` — no change (tests detection)
- `test_pydata_roundtrips.py` — update to use TypeSpec

### Phase 3 Tests

- Delete `tests/schema/` entirely
- Verify `tests/typespec/` and `tests/conform/` cover all moved functionality

---

## Frictionless Serialization of Custom Casts

The `custom_cast` field on FieldSpec serializes to/from `x-mountainash` in Frictionless JSON, alongside `rename_from` and `null_fill`:

```json
{
    "name": "amount",
    "type": "any",
    "x-mountainash": {
        "custom_cast": "safe_float"
    }
}
```

The `frictionless.py` adapter needs a minor update to handle this new field.

---

## Deferred Work

- **Egress relation terminals:** Currently extraction stays as Polars operations (`.to_dicts()`, `.iter_rows()`). A future pass could replace these with relation API terminals (`.to_dicts()`, `.to_tuples()`) for consistency, but the Polars operations are already efficient.
- **Narwhals custom converters as mountainash expressions:** The narwhals-vectorized tier could potentially be folded into the conform compiler, eliminating the separate narwhals step. Deferred until the custom type system is reviewed.
- **Type system unification:** Merge `UniversalType` and `MountainashDtype` (deferred from typespec design).
- **`to_native()` relation terminal:** Return DataFrame in original backend type from conform compiler.

---

## Dependencies

- `mountainash.typespec` — TypeSpec, FieldSpec, UniversalType, CustomTypeRegistry, extraction
- `mountainash.conform` — compile_conform(), ConformBuilder
- `mountainash.relations` — relation(), .to_polars() (for CastDataFrame replacement)
- No new external dependencies
