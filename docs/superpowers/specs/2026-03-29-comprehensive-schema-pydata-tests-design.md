# Comprehensive Schema & PyData Test Suites — Design Spec

**Roadmap items:** #13 (Layer 5.1) and #14 (Layer 5.2)
**Branch:** `feature/substrait_alignment`
**Date:** 2026-03-29

## Goal

Bring the schema and pydata modules from smoke-test-only coverage to comprehensive test suites. Schema currently has 10 smoke tests + 16 SchemaBuilder tests. PyData has 4 smoke tests. Both modules have ~10k lines of production code with zero coverage of core logic paths.

## Scope

One spec, two implementation phases:
1. **Phase 1: Schema tests** — SchemaConfig, UniversalType mappings, transforms (full matrix across 5 backends), extractors, validators, converters, custom types, round-trips
2. **Phase 2: PyData tests** — all 10 ingress handlers, factory dispatch, all 17 egress methods, egress factory, hybrid conversion strategy, round-trips

Each phase produces independently committable and reviewable test suites.

---

## Phase 1: Schema Tests

### File Organization

```
tests/schema/
├── test_schema_smoke.py          # Existing (10 tests) — unchanged
├── conftest.py                   # Shared fixtures: sample DataFrames (all backends), sample schemas
├── test_schema_config.py         # SchemaConfig API surface
├── test_universal_types.py       # UniversalType enum, normalize_type, mappings, safe casts
├── test_schema_transforms.py     # Full matrix: transform type x universal type x backend
├── test_schema_extractors.py     # Extract from DataFrame (all backends), dataclass, Pydantic
├── test_schema_validators.py     # validate_round_trip, validate_schema_match, validate_transformation_config
├── test_schema_converters.py     # to_polars_schema, to_pandas_dtypes, to_arrow_schema, to_ibis_schema
├── test_custom_types.py          # Registry CRUD + all 4 built-in converters (Python + Narwhals)
└── test_schema_roundtrips.py     # extract->apply, from_schemas->apply, predict->validate
```

### test_schema_config.py — SchemaConfig API

**Creation:**
- `SchemaConfig(columns={...})` with rename, cast, null_fill, default specs
- `SchemaConfig.from_dict()` — 3 input formats: full format, columns-only, simple rename mapping
- `SchemaConfig.from_json()` — full schema JSON and simple format JSON
- `SchemaConfig.from_schemas(source, target)` — auto-generates column mappings via fuzzy string matching; verify `fuzzy_match_threshold` parameter, `auto_cast`, `keep_unmapped_source`

**Serialization:**
- `to_dict()` → `from_dict()` round-trip preserves all config
- `to_json()` → `from_json()` round-trip preserves all config

**Configuration options:**
- `keep_only_mapped=True` drops unmapped columns; `False` keeps them
- `strict=True` raises on missing columns; `False` skips them

**Prediction and validation:**
- `predict_output_schema(input_schema)` returns correct schema for various configs
- `validate_against_schemas(check_source, check_target)` — compatible schemas pass, incompatible fail
- `validate_against_dataframe(df, mode='source')` and `mode='target'` — returns ValidationResult with correct issues

**Conversion separation:**
- `separate_conversions()` returns three dicts: `python_only_custom`, `narwhals_custom`, `native_conversions`
- Verify each conversion lands in the correct tier based on CustomTypeRegistry state

**Helper functions:**
- `init_column_config()` normalizes various input formats to SchemaConfig
- `create_rename_config(mapping, keep_only_mapped)` creates rename-only config
- `create_cast_config(casting, keep_only_mapped)` creates cast-only config
- `apply_column_config(df, config)` delegates to CastSchemaFactory correctly

### test_universal_types.py — Type System

**Enum completeness:**
- All expected UniversalType members exist: STRING, INTEGER, NUMBER, BOOLEAN, DATE, TIME, DATETIME, DURATION, YEAR, YEARMONTH, ARRAY, OBJECT, ANY

**normalize_type() — parametrized by source format:**
- Python types: `int` → "integer", `float` → "number", `str` → "string", `bool` → "boolean", `datetime.date` → "date", `datetime.datetime` → "datetime"
- String names: "string" → "string", "integer" → "integer", etc. (identity)
- Polars types: `pl.Utf8` → "string", `pl.Int64` → "integer", `pl.Float64` → "number", `pl.Boolean` → "boolean", `pl.Date` → "date", `pl.Datetime` → "datetime", `pl.Duration` → "duration"
- Pandas dtypes: "object" → "string", "int64" → "integer", "float64" → "number", etc.
- Arrow types: `pa.string()` → "string", `pa.int64()` → "integer", etc.
- Ibis types: ibis string type representations → universal types

**Forward mappings:**
- `get_polars_type(universal_type)` for all UniversalType values → correct Polars dtype
- `get_arrow_type(universal_type)` for all UniversalType values → correct Arrow type
- `get_universal_to_backend_mapping(backend)` for each backend returns complete dict

**Reverse mappings:**
- `get_backend_to_universal_mapping(backend)` for each backend returns complete dict
- `POLARS_TO_UNIVERSAL`, `PANDAS_TO_UNIVERSAL`, `ARROW_TO_UNIVERSAL`, `IBIS_TO_UNIVERSAL`, `PYTHON_TO_UNIVERSAL` cover all common types

**Safe cast checking:**
- `is_safe_cast(from_type, to_type)` returns True for safe pairs (integer→number, string→string)
- Returns False for unsafe pairs (string→integer, date→boolean)
- `SAFE_CASTS` and `UNSAFE_CASTS` sets are disjoint

### test_schema_transforms.py — Full Matrix

**Parametrized test:** `transform_type` x `universal_type` x `backend`

**Transform types (4):**
- `cast` — change column type (e.g., string "30" → integer 30)
- `rename` — change column name (source_name → target_name)
- `null_fill` — replace nulls with a default value
- `default` — provide value when column is missing entirely

**Universal types (10):**
STRING, INTEGER, NUMBER, BOOLEAN, DATE, DATETIME, TIME, DURATION, ARRAY, OBJECT

**Backends (5):**
Polars, Pandas, Ibis, PyArrow, Narwhals

**Total: 4 x 10 x 5 = 200 parametrized cases**

Each test:
1. Creates a source DataFrame in the target backend with appropriate test data
2. Builds a SchemaConfig with the transform
3. Calls `config.apply(df)`
4. Verifies the output has the correct column name, type, and values

**xfail markers** for known backend limitations:
- PyArrow DURATION cast (if unsupported)
- Ibis ARRAY/OBJECT types (limited support)
- Any other backend-specific gaps discovered during implementation

**Additional non-parametrized tests:**
- Multi-column transforms (cast + rename + null_fill in one config)
- Operation ordering: verify null_fill happens before cast, rename is last
- `keep_only_mapped=True` drops extra columns
- `strict=True` raises for missing source columns

### test_schema_extractors.py — Schema Extraction

**DataFrame extraction (parametrized by backend):**
- Polars, Pandas, PyArrow, Ibis, Narwhals DataFrames with mixed types (int, float, string, date, boolean)
- `extract_schema_from_dataframe(df)` returns TableSchema with correct field names and types
- `preserve_backend_types=True` populates `backend_type` field on each SchemaField
- `from_dataframe(df)` (the extractors.py function) matches `extract_schema_from_dataframe()` output

**Dataclass extraction:**
- Simple dataclass with basic types (str, int, float, bool)
- Dataclass with Optional fields — `preserve_optional` flag
- Dataclass with datetime fields
- `extract_schema_from_dataclass()` caching: same class returns same result

**Pydantic extraction:**
- Pydantic v2 model with basic types
- Model with Optional fields
- Model with constrained types (e.g., `Field(ge=0)`)
- `extract_schema_from_pydantic()` caching

**Fuzzy matching:**
- `build_schema_config_with_fuzzy_matching(source, target)` — near-match column names (e.g., "full_name" ↔ "fullname") produce correct rename mappings
- `fuzzy_match_threshold` parameter: high threshold misses fuzzy matches, low threshold catches them

### test_schema_validators.py — Validation

**validate_round_trip():**
- Matching output schema → `(True, [])`
- Wrong column type in output → `(False, [error_msg])`
- Missing column in output → `(False, [error_msg])`
- `tolerance` parameter: float differences within tolerance pass, outside fail

**assert_round_trip():**
- Passes when valid, raises `SchemaValidationError` when invalid

**validate_schema_match():**
- DataFrame matching expected schema → `(True, [])`
- `strict=True`: extra columns in DataFrame → fail; `strict=False`: extra columns OK
- Missing columns → fail in both modes
- Wrong types → fail

**assert_schema_match():**
- Passes when valid, raises `SchemaValidationError` when invalid

**validate_transformation_config():**
- Valid config with matching source/target schemas → `(True, [])`
- Config references columns not in source schema → `(False, [errors])`
- Config casts to incompatible types → `(False, [errors])`

### test_schema_converters.py — Backend Conversion

**Parametrized by backend:**
- `to_polars_schema(schema)` — returns dict mapping field names to Polars dtypes
- `to_pandas_dtypes(schema)` — returns dict mapping field names to Pandas dtype strings
- `to_arrow_schema(schema)` — returns `pa.Schema` with correct types
- `to_ibis_schema(schema)` — returns dict mapping field names to Ibis type strings

**For each converter:**
- All UniversalType values produce a valid backend type
- Backend type preservation: if SchemaField has `backend_type`, use it over universal mapping

**Generic dispatcher:**
- `convert_to_backend(schema, "polars")` routes to `to_polars_schema()`
- Same for all other backends

### test_custom_types.py — Custom Type Registry

**Registry CRUD:**
- `register(name, target_type, python_converter, narwhals_converter)` — registers successfully
- `has_converter(name)` returns True after register, False after unregister
- `get_spec(name)` returns correct `TypeConverterSpec`
- `list_converters()` returns dict of all registered converters
- `unregister(name)` removes converter
- `clear()` removes all converters
- `is_native_type(name)` returns True for standard types, False for custom

**Built-in converters — Python path (4 converters):**
- `safe_float`: `"3.14"` → 3.14, `"NaN"` → None, `"Inf"` → None, `""` → None
- `safe_int`: `"42"` → 42, `"NaN"` → None, `3.7` → 3 (truncation)
- `xml_string`: `"<tag>"` → `"&lt;tag&gt;"`, `"&"` → `"&amp;"`
- `rich_boolean`: `"yes"` → True, `"no"` → False, `"1"` → True, `"0"` → False, `"true"` → True

**Built-in converters — Narwhals path (vectorized):**
- Same logical results as Python path but applied to a Polars DataFrame column
- `is_vectorized(name)` returns True for all 4 built-ins
- `get_narwhals_converter(name)` returns callable that produces Narwhals expressions

**User-defined converter:**
- Register a custom converter (Python-only, no Narwhals)
- `is_vectorized()` returns False
- Apply via `CustomTypeRegistry.convert(value, name)`
- Unregister and verify it's gone

**Teardown:** Every test class/function that modifies the registry calls `CustomTypeRegistry.clear()` in teardown, then re-registers built-ins (or uses a fixture that saves/restores state).

### test_schema_roundtrips.py — Schema Round-Trips

- Extract schema from Polars DataFrame → apply extracted schema to a compatible DataFrame with string columns → verify types match original
- `from_schemas(source, target)` → `apply()` → extracted output schema matches target
- `predict_output_schema()` → `apply()` → `extract_schema_from_dataframe(result)` matches prediction
- Extract from dataclass → apply to DataFrame with matching column names → verify types

---

## Phase 2: PyData Tests

### File Organization

```
tests/pydata/
├── test_pydata_smoke.py          # Existing (4 tests) — unchanged
├── conftest.py                   # Shared fixtures: sample dataclasses, Pydantic models, named tuples, test data
├── test_ingress_factory.py       # Format detection for all 10+ types + edge cases
├── test_ingress_handlers.py      # All 10 handlers: convert + column_config
├── test_egress_all.py            # All 17 egress methods from EgressFromPolars
├── test_egress_factory.py        # Factory dispatch for all DataFrame backends
├── test_hybrid_conversion.py     # Three-tier strategy components
└── test_pydata_roundtrips.py     # ingress->egress round-trips for each format
```

### conftest.py — Shared Fixtures

```python
@dataclass
class SamplePerson:
    name: str
    age: int
    score: float

class SamplePersonModel(BaseModel):  # Pydantic
    name: str
    age: int
    score: float

SampleRow = namedtuple("SampleRow", ["name", "age", "score"])

SAMPLE_DICTS = [
    {"name": "Alice", "age": 30, "score": 1.5},
    {"name": "Bob", "age": 25, "score": 2.0},
    {"name": "Charlie", "age": 35, "score": 3.0},
]

SAMPLE_DICT_OF_LISTS = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [30, 25, 35],
    "score": [1.5, 2.0, 3.0],
}
```

Fixtures provide these in various forms (dataclass instances, Pydantic instances, named tuples, plain tuples, indexed data, etc.) for reuse across test files.

### test_ingress_factory.py — Format Detection

**`_get_strategy_key()` correctly identifies each format:**
- Single dataclass instance → DATACLASS
- Single Pydantic model instance → PYDANTIC
- Dict of lists → PYDICT
- List of dicts → PYLIST
- Single named tuple → NAMEDTUPLE
- Single plain tuple → TUPLE
- Dict of Polars Series → SERIES_DICT
- Dict of Pandas Series → SERIES_DICT
- Indexed data (dict of key → list of rows) → INDEXED_DATA
- List/set/frozenset of scalars → COLLECTION
- List of dataclass instances → DATACLASS
- List of Pydantic instances → PYDANTIC
- List of named tuples → NAMEDTUPLE
- List of plain tuples → TUPLE

**Edge cases:**
- Empty list → verify behavior (UNKNOWN or specific fallback)
- Empty dict → verify behavior
- Single-item list of dicts → PYLIST
- Nested dicts (not indexed) → verify correct classification
- None → verify behavior
- Unrecognized type (e.g., a custom object) → UNKNOWN

**`get_strategy()` returns correct handler class for each format constant.**

### test_ingress_handlers.py — All 10 Handlers

Each handler tested with:
1. **Basic conversion** — standard data → Polars DataFrame with correct shape, columns, values
2. **Multiple rows** — verify all rows present
3. **Null/None handling** — None values in source → null in DataFrame
4. **With column_config** — SchemaConfig applied during conversion (rename, cast, null_fill)

**Handler-specific tests:**

| Handler | Additional Tests |
|---------|-----------------|
| `DataframeFromPylist` | Missing keys in some dicts (ragged rows), column ordering |
| `DataframeFromPydict` | Verify column order matches dict key order |
| `DataframeFromDataclass` | Single instance wraps to 1-row DataFrame; list of instances |
| `DataframeFromPydantic` | Single instance wraps; nested model fields |
| `DataframeFromNamedTuple` | Field names become column names; single + list |
| `DataframeFromTuple` | With `column_names` parameter; without (auto-generated names) |
| `DataframeFromIndexedData` | `index_column_names` parameter; multi-key index |
| `DataframeFromSeriesDict` | Polars Series dict + Pandas Series dict |
| `IngressFromCollection` | `column_name` parameter; default column name; set/frozenset (unordered) |
| `DataframeFromDefault` | Polars DataFrame passthrough; other types Polars can handle |

### test_egress_all.py — All 17 Egress Methods

Test data: a Polars DataFrame with mixed types (int, float, string, date, datetime, null).

**DataFrame conversions:**
- `_to_pandas(df)` → Pandas DataFrame with correct dtypes and values
- `_to_polars(df)` → Polars DataFrame (identity); `_to_polars(df, as_lazy=True)` → LazyFrame
- `_to_narwhals(df)` → Narwhals DataFrame; with `as_lazy` parameter
- `_to_pyarrow(df)` → PyArrow Table with correct schema

**Python data conversions:**
- `_to_dictionary_of_lists(df)` → `{"col": [val1, val2, ...]}` for each column
- `_to_list_of_dictionaries(df)` → `[{"col": val, ...}, ...]` for each row
- `_to_list_of_tuples(df)` → list of tuples, one per row, values in column order

**Series conversions:**
- `_to_dictionary_of_series_polars(df)` → dict of Polars Series, one per column
- `_to_dictionary_of_series_pandas(df)` → dict of Pandas Series, one per column

**Named tuple conversions:**
- `_to_list_of_named_tuples(df)` → named tuples with field names matching columns
- `_to_list_of_typed_named_tuples(df)` → typed named tuples; `preserve_dates=False` converts dates to strings; `preserve_dates=True` keeps date objects

**Indexed conversions (single + composite key):**
- `_to_index_of_dictionaries(df, index_fields=["name"])` → `{"Alice": [{...}], "Bob": [{...}]}`
- `_to_index_of_tuples(df, index_fields)` → indexed tuples
- `_to_index_of_named_tuples(df, index_fields)` → indexed named tuples
- `_to_index_of_typed_named_tuples(df, index_fields)` → indexed typed named tuples
- Composite key: `index_fields=["name", "age"]` → tuple keys

**Typed output conversions:**
- `_to_list_of_dataclasses(df, SamplePerson)` → list of dataclass instances with correct field values
- `_to_list_of_dataclasses(df, ..., schema_config=config)` → with column mapping
- `_to_list_of_dataclasses(df, ..., auto_derive_schema=True, fuzzy_match_threshold=0.6)` → fuzzy column matching
- `_to_list_of_dataclasses(df, ..., apply_defaults=True)` → missing columns use dataclass defaults
- `_to_list_of_pydantic(df, SamplePersonModel)` → list of Pydantic model instances (via model_validate)
- `_to_list_of_pydantic(df, ..., schema_config=config)` → with column mapping

### test_egress_factory.py — Factory Dispatch

**All input DataFrame types route to EgressPydataFromPolars:**
- Polars DataFrame → EgressPydataFromPolars
- Polars LazyFrame → EgressPydataFromPolars
- Pandas DataFrame → EgressPydataFromPolars
- PyArrow Table → EgressPydataFromPolars
- Ibis Table → EgressPydataFromPolars
- Narwhals DataFrame (eager) → EgressPydataFromPolars
- Narwhals DataFrame (lazy) → EgressPydataFromPolars

Each test verifies the factory returns the correct strategy class and that conversion to at least one output format (e.g., list of dicts) produces correct results.

### test_hybrid_conversion.py — Three-Tier Strategy

**Tier 3 — Python edge converters:**
- `apply_custom_converters_to_dict(data_dict, custom_conversions)` — applies Python-only converters to a single dict
- `apply_custom_converters_to_dicts(data_dicts, custom_conversions)` — applies to list of dicts
- Verify custom converter functions are called with correct values

**Tier 1 — Native DataFrame converters:**
- `apply_native_conversions_to_dataframe(df, native_conversions)` — applies cast, rename, null_fill as Polars expressions
- With and without schema_config parameter

**Tier 2 — Narwhals vectorized converters:**
- `_apply_narwhals_custom_converters(df, narwhals_custom)` — applies vectorized Narwhals expressions to DataFrame columns

**End-to-end hybrid:**
- `apply_hybrid_conversion(data_dicts, schema_config)` with a SchemaConfig that has:
  - One python_only_custom column (e.g., safe_float)
  - One narwhals_custom column (e.g., xml_string with Narwhals impl)
  - One native column (e.g., integer cast)
- Verify all three tiers applied correctly in final DataFrame

**Tier assignment verification:**
- `SchemaConfig.separate_conversions()` with mixed custom/native types → verify each conversion lands in the correct tier

### test_pydata_roundtrips.py — Ingress/Egress Round-Trips

Each test: create Python data → ingress to DataFrame → egress back to same format → verify values match.

- **dict-of-lists:** `{"a": [1,2], "b": ["x","y"]}` → DataFrame → `_to_dictionary_of_lists()` → matches original
- **list-of-dicts:** `[{"a": 1, "b": "x"}, ...]` → DataFrame → `_to_list_of_dictionaries()` → matches original
- **dataclass instances:** `[SamplePerson(...), ...]` → DataFrame → `_to_list_of_dataclasses(SamplePerson)` → field values match
- **Pydantic instances:** `[SamplePersonModel(...), ...]` → DataFrame → `_to_list_of_pydantic(SamplePersonModel)` → field values match
- **named tuples:** `[SampleRow(...), ...]` → DataFrame → `_to_list_of_named_tuples()` → field values match
- **plain tuples:** `[(1, "x"), ...]` → DataFrame → `_to_list_of_tuples()` → values match (column names lost, values preserved)
- **indexed data:** `{"key": [{"a": 1}]}` → DataFrame → `_to_index_of_dictionaries(index_fields)` → structure matches
- **collection:** `[1, 2, 3]` → DataFrame → column `.to_list()` → matches original

---

## Testing Approach

**Parametrization:** The full transform matrix (200 cases) uses `@pytest.mark.parametrize` with `pytest.param(..., marks=pytest.mark.xfail(reason="..."))` for known backend limitations. Consistent with the expression test suite pattern.

**No skips:** xfail for known issues, per the project's testing-philosophy principle. All backends are installed.

**Backend availability:** Polars, Pandas, Narwhals, PyArrow, Ibis (local fork) — all available, all tested.

**Custom type test isolation:** Tests that modify `CustomTypeRegistry` save state in setup and restore in teardown via a fixture.

**Estimated test counts:**
- Phase 1 (Schema): ~300-350 tests
- Phase 2 (PyData): ~150-200 tests
- Total: ~450-550 new tests
