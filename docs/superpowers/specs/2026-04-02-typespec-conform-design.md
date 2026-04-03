# TypeSpec & Conform: Schema Module Redesign

> **For agentic workers:** This spec replaces the existing `schema/` module with two focused modules: `typespec` (metadata) and `conform` (transforms). Read fully before implementing.

**Goal:** Replace the monolithic `schema/` module (which has 27 xfailed tests due to broken backend infrastructure) with two clean modules that separate metadata from transformation, eliminating ~2,800 lines of parallel backend code by compiling transforms to the existing relations/expressions layer.

**Motivation:** The `schema/` module was ported from a separate repository and carries its own backend detection and strategy infrastructure — a parallel system to what expressions/relations already provides. Three of five transform backends are broken (pandas: backend detection fails, pyarrow: wrong import name, ibis: calls nonexistent `ibis.col()`). Rather than fix bugs in a parallel system, we replace it with one that compiles to the proven expressions/relations layer.

---

## Module Structure

```
src/mountainash/
├── typespec/                     # Metadata: what does data look like?
│   ├── __init__.py               # Public API re-exports
│   ├── universal_types.py        # UniversalType enum, normalize_type(), type mappings
│   ├── type_bridge.py            # UniversalType ↔ MountainashDtype mapping
│   ├── spec.py                   # TypeSpec, FieldSpec, FieldConstraints
│   ├── extraction.py             # Extract TypeSpec from DataFrames, dataclasses, Pydantic
│   ├── validation.py             # Validate DataFrames against a TypeSpec
│   ├── converters.py             # UniversalType → backend-specific types
│   ├── custom_types.py           # CustomTypeRegistry, semantic converters
│   └── frictionless.py           # Import/export Frictionless Table Schema format
├── conform/                      # Transforms: make data match a spec
│   ├── __init__.py               # Public API re-exports
│   ├── builder.py                # ConformBuilder — user-facing DSL
│   └── compiler.py               # Compiles TypeSpec → relation/expression plan
├── schema/                       # DELETED entirely (no backward compat shim)
```

---

## TypeSpec Module (`typespec/`)

### Purpose

Describes the *types and structure* of data, independent of any backend. Provides extraction (infer a spec from existing data), validation (check data against a spec), and serialization (Frictionless Table Schema JSON).

### Core Data Classes (`spec.py`)

```python
@dataclass
class FieldConstraints:
    """Constraints for a field (Frictionless Table Schema compliant)."""
    required: bool = False
    unique: bool = False
    minimum: Any | None = None
    maximum: Any | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[Any] | None = None


@dataclass
class FieldSpec:
    """A single field in a TypeSpec."""
    name: str                                    # Target column name
    type: UniversalType = UniversalType.STRING    # Target type
    format: str = "default"                       # Type format (e.g., date format)
    title: str | None = None                      # Human-readable label
    description: str | None = None                # Documentation
    constraints: FieldConstraints | None = None   # Validation constraints
    missing_values: list[str] | None = None       # Values treated as null
    null_fill: Any = None                         # Default value for nulls
    rename_from: str | None = None                # Source column name if different

    @property
    def source_name(self) -> str:
        """The column name to read from the source DataFrame."""
        return self.rename_from or self.name


@dataclass
class TypeSpec:
    """A serializable specification of data types and conformance rules."""
    fields: list[FieldSpec]
    title: str | None = None
    description: str | None = None
    primary_key: str | list[str] | None = None
    missing_values: list[str] | None = None
    keep_only_mapped: bool = False

    @classmethod
    def from_simple_dict(cls, columns: dict[str, str], **metadata) -> TypeSpec:
        """Create from {name: type_string} dict."""
        ...

    @classmethod
    def from_frictionless(cls, data: dict | str | Path) -> TypeSpec:
        """Import from Frictionless Table Schema."""
        from .frictionless import from_frictionless
        return from_frictionless(data)

    def to_frictionless(self) -> dict:
        """Export as Frictionless Table Schema dict."""
        from .frictionless import to_frictionless
        return to_frictionless(self)

    def get_field(self, name: str) -> FieldSpec | None:
        ...

    @property
    def field_names(self) -> list[str]:
        ...
```

**Rename mapping from old classes:**

| Old (schema/) | New (typespec/) |
|---|---|
| `TableSchema` | `TypeSpec` |
| `SchemaField` | `FieldSpec` |
| `FieldConstraints` | `FieldConstraints` (unchanged) |
| `SchemaDiff` | `SpecDiff` |
| `compare_schemas()` | `compare_specs()` |

### Universal Types (`universal_types.py`)

Moved from `schema/config/types.py`. Contains `UniversalType` enum (13 Frictionless-aligned types), `normalize_type()`, `is_safe_cast()`, and all backend type mappings (`UNIVERSAL_TO_POLARS`, `UNIVERSAL_TO_PANDAS`, etc.).

No changes to the type enum or mappings — this is a move, not a rewrite.

### Type Bridge (`type_bridge.py`)

Maps between the two type systems so conform can compile to expressions:

```python
UNIVERSAL_TO_MOUNTAINASH: dict[UniversalType, MountainashDtype] = {
    UniversalType.STRING:   MountainashDtype.STRING,
    UniversalType.INTEGER:  MountainashDtype.I64,
    UniversalType.NUMBER:   MountainashDtype.FP64,
    UniversalType.BOOLEAN:  MountainashDtype.BOOL,
    UniversalType.DATE:     MountainashDtype.DATE,
    UniversalType.TIME:     MountainashDtype.TIME,
    UniversalType.DATETIME: MountainashDtype.TIMESTAMP,
    # DURATION, YEAR, YEARMONTH, ARRAY, OBJECT, ANY — no MountainashDtype equivalent yet
}

def bridge_type(universal: UniversalType) -> MountainashDtype:
    """Convert UniversalType to MountainashDtype for expression compilation.

    Raises ValueError for types without a MountainashDtype equivalent.
    """
    if universal not in UNIVERSAL_TO_MOUNTAINASH:
        raise ValueError(
            f"No MountainashDtype mapping for {universal}. "
            f"Supported: {list(UNIVERSAL_TO_MOUNTAINASH.keys())}"
        )
    return UNIVERSAL_TO_MOUNTAINASH[universal]
```

This is an interim bridge. Future work will unify the type systems.

### Extraction (`extraction.py`)

Moved from `schema/config/extractors.py`. Functions renamed:

| Old | New |
|---|---|
| `from_dataframe()` | `extract_from_dataframe()` |
| `from_dataclass()` | `extract_from_dataclass()` |
| `from_pydantic()` | `extract_from_pydantic()` |

All return `TypeSpec` instead of `TableSchema`. Internal logic unchanged.

### Validation (`validation.py`)

Moved from `schema/config/validators.py`. Functions renamed:

| Old | New |
|---|---|
| `validate_schema_match()` | `validate_match()` |
| `assert_schema_match()` | `assert_match()` |
| `validate_round_trip()` | `validate_round_trip()` (unchanged) |
| `validate_transformation_config()` | removed (transform config no longer exists) |

### Converters (`converters.py`)

Moved from `schema/config/converters.py`. Functions unchanged:

- `to_polars_schema()`, `to_pandas_dtypes()`, `to_arrow_schema()`, `to_ibis_schema()`
- `convert_to_backend()` (dispatch function)

These convert a `TypeSpec` to backend-specific schema objects. Useful for DataFrame creation, not for transforms.

### Custom Types (`custom_types.py`)

Moved from `schema/config/custom_types.py`. `CustomTypeRegistry`, `TypeConverter`, `TypeConverterSpec` unchanged. This is the Layer 2 semantic type system.

### Frictionless Adapter (`frictionless.py`)

**Export:**

```python
def to_frictionless(spec: TypeSpec) -> dict:
    """Convert TypeSpec to Frictionless Table Schema dict.

    Standard Frictionless fields go in their standard locations.
    Mountainash-specific extensions (rename_from, null_fill, keep_only_mapped)
    go in 'x-mountainash' namespaced keys per Frictionless convention.
    """
    result: dict = {"fields": []}
    for field in spec.fields:
        fd: dict = {
            "name": field.name,
            "type": field.type.value,
        }
        if field.format != "default":
            fd["format"] = field.format
        if field.title:
            fd["title"] = field.title
        if field.description:
            fd["description"] = field.description
        if field.constraints:
            fd["constraints"] = _constraints_to_dict(field.constraints)
        if field.missing_values:
            fd["missingValues"] = field.missing_values

        # Mountainash extensions
        ma_ext: dict = {}
        if field.rename_from:
            ma_ext["rename_from"] = field.rename_from
        if field.null_fill is not None:
            ma_ext["null_fill"] = field.null_fill
        if ma_ext:
            fd["x-mountainash"] = ma_ext

        result["fields"].append(fd)

    # Spec-level standard fields
    if spec.title:
        result["title"] = spec.title
    if spec.description:
        result["description"] = spec.description
    if spec.primary_key:
        result["primaryKey"] = spec.primary_key
    if spec.missing_values:
        result["missingValues"] = spec.missing_values

    # Spec-level mountainash extensions
    if spec.keep_only_mapped:
        result.setdefault("x-mountainash", {})["keep_only_mapped"] = True

    return result
```

**Import:**

```python
def from_frictionless(data: dict | str | Path) -> TypeSpec:
    """Create TypeSpec from Frictionless Table Schema.

    Args:
        data: Dict, JSON string, or path to .json file.

    Recognizes standard Frictionless fields and x-mountainash extensions.
    Unknown extensions are silently ignored.
    """
    if isinstance(data, (str, Path)):
        data = _load_json(data)

    fields = []
    for fd in data.get("fields", []):
        ma_ext = fd.get("x-mountainash", {})
        fields.append(FieldSpec(
            name=fd["name"],
            type=normalize_type(fd.get("type", "string")),
            format=fd.get("format", "default"),
            title=fd.get("title"),
            description=fd.get("description"),
            constraints=_parse_constraints(fd.get("constraints")),
            missing_values=fd.get("missingValues"),
            rename_from=ma_ext.get("rename_from"),
            null_fill=ma_ext.get("null_fill"),
        ))

    spec_ext = data.get("x-mountainash", {})
    return TypeSpec(
        fields=fields,
        title=data.get("title"),
        description=data.get("description"),
        primary_key=data.get("primaryKey"),
        missing_values=data.get("missingValues"),
        keep_only_mapped=spec_ext.get("keep_only_mapped", False),
    )
```

---

## Conform Module (`conform/`)

### Purpose

Takes a `TypeSpec` and applies it to a DataFrame by compiling to mountainash relation/expression operations. Replaces the entire `schema/transform/` directory (~1,400 lines of backend strategies) with relation compilation (~100 lines).

### ConformBuilder (`builder.py`)

```python
class ConformBuilder:
    """Build-then-apply conformance of DataFrames to a TypeSpec.

    Follows the mountainash build-then-X pattern:
    - Build phase: construct from dict, TypeSpec, or Frictionless JSON
    - Apply phase: .apply(df) compiles to relations and executes

    Examples:
        # From dict (target-oriented keys)
        conform = ConformBuilder({
            "user_id": {"rename_from": "raw_id", "cast": "integer"},
            "email":   {"cast": "string", "null_fill": "unknown"},
        })
        result = conform.apply(df)

        # From TypeSpec
        conform = ConformBuilder(spec)
        result = conform.apply(df)

        # From Frictionless JSON file
        conform = ConformBuilder.from_frictionless("schema.json")
        result = conform.apply(df)
    """

    def __init__(self, source: dict | TypeSpec):
        if isinstance(source, dict):
            self._spec = self._dict_to_spec(source)
        else:
            self._spec = source

    @classmethod
    def from_frictionless(cls, data: dict | str | Path) -> ConformBuilder:
        return cls(TypeSpec.from_frictionless(data))

    @property
    def spec(self) -> TypeSpec:
        return self._spec

    def to_frictionless(self) -> dict:
        return self._spec.to_frictionless()

    def apply(self, df) -> Any:
        """Compile conformance to relations and execute."""
        from .compiler import compile_conform
        return compile_conform(self._spec, df)

    def validate(self, df) -> ValidationResult:
        """Check df against spec without transforming."""
        from mountainash.typespec.validation import validate_match
        from mountainash.typespec.extraction import extract_from_dataframe
        actual = extract_from_dataframe(df)
        return validate_match(actual, self._spec)

    @staticmethod
    def _dict_to_spec(columns: dict) -> TypeSpec:
        """Convert target-oriented dict to TypeSpec.

        Dict format (target column names as keys):
            {
                "user_id": {"rename_from": "raw_id", "cast": "integer"},
                "email":   {"cast": "string", "null_fill": "unknown"},
            }

        The "cast" key in the dict maps to FieldSpec.type (UniversalType).
        "cast" is used in the dict API because it describes the user's intent
        (cast this column), while .type describes the spec's state (target type).
        """
        fields = []
        for target_name, config in columns.items():
            fields.append(FieldSpec(
                name=target_name,
                type=normalize_type(config["cast"]) if "cast" in config else UniversalType.ANY,
                rename_from=config.get("rename_from"),
                null_fill=config.get("null_fill"),
            ))
        return TypeSpec(fields=fields)
```

### Compiler (`compiler.py`)

```python
def compile_conform(spec: TypeSpec, df) -> Any:
    """Compile a TypeSpec conformance plan to relation operations and execute.

    Builds a relation plan that:
    1. Reads from the source DataFrame
    2. For each field: rename (via alias), null_fill (via coalesce), cast
    3. Selects mapped columns (+ unmapped if keep_only_mapped is False)
    4. Executes via .to_native() to return same-type DataFrame

    Args:
        spec: The TypeSpec defining target structure
        df: Source DataFrame (any supported backend)

    Returns:
        Transformed DataFrame (same backend type as input)
    """
    import mountainash as ma
    from .type_bridge import bridge_type

    r = ma.relation(df)
    source_columns = r.columns  # Column names in source df

    mapped_exprs = []
    mapped_names = set()

    for field in spec.fields:
        source_name = field.source_name
        mapped_names.add(source_name)

        expr = ma.col(source_name)

        # Null fill (before cast — fill with compatible value first)
        if field.null_fill is not None:
            expr = ma.coalesce(expr, ma.lit(field.null_fill))

        # Cast (via type bridge: UniversalType → MountainashDtype)
        if field.type and field.type != UniversalType.ANY:
            dtype = bridge_type(field.type)
            expr = expr.cast(dtype)

        # Rename (alias to target name)
        expr = expr.name.alias(field.name)
        mapped_exprs.append(expr)

    # Handle unmapped columns
    if not spec.keep_only_mapped:
        for col in source_columns:
            if col not in mapped_names:
                mapped_exprs.append(ma.col(col))

    return r.select(*mapped_exprs).to_polars()
```

**Note:** The relation API currently has `to_polars()`, `to_pandas()`, `to_dict()` etc. but no `to_native()` that returns the original backend type. For the initial implementation, `to_polars()` is the safest default (Polars is the hub for null-safe extraction). A `to_native()` terminal that auto-detects and returns the original backend type is deferred work — it would be a useful addition to the relations API but is not blocking for conform.

---

## Public API Entry Points

In `src/mountainash/__init__.py`:

```python
from mountainash.typespec.spec import TypeSpec
from mountainash.conform.builder import ConformBuilder

def typespec(columns: dict[str, str], **metadata) -> TypeSpec:
    """Create a TypeSpec from a simple {name: type_string} dict."""
    return TypeSpec.from_simple_dict(columns, **metadata)

def conform(source: dict | TypeSpec) -> ConformBuilder:
    """Create a ConformBuilder from a dict or TypeSpec."""
    return ConformBuilder(source)
```

Usage:
```python
import mountainash as ma

# Quick typespec
spec = ma.typespec({"user_id": "integer", "email": "string"})

# Conform with full options
result = ma.conform({
    "user_id": {"rename_from": "raw_id", "cast": "integer"},
    "email":   {"cast": "string", "null_fill": "unknown"},
}).apply(df)

# From Frictionless file
result = ma.conform(ma.TypeSpec.from_frictionless("schema.json")).apply(df)
```

---

## What Gets Deleted

| Path | Lines | Reason |
|---|---|---|
| `schema/transform/cast_schema_factory.py` | 70 | Replaced by relation compilation |
| `schema/transform/cast_schema_polars.py` | 344 | Replaced by relation compilation |
| `schema/transform/cast_schema_pandas.py` | 241 | Replaced by relation compilation |
| `schema/transform/cast_schema_narwhals.py` | 279 | Replaced by relation compilation |
| `schema/transform/cast_schema_ibis.py` | 308 | Replaced by relation compilation |
| `schema/transform/cast_schema_pyarrow.py` | 61 | Replaced by relation compilation |
| `schema/transform/base_schema_transform_strategy.py` | 197 | Replaced by relation compilation |
| `schema/transform/__init__.py` | 42 | Replaced by relation compilation |
| `schema/config/schema_config.py` | 1,000 | Split into typespec/spec.py + conform/builder.py |
| `schema/schema_builder.py` | 179 | Replaced by conform/builder.py |
| `schema/__init__.py` | 87 | Replaced by typespec/ and conform/ __init__.py |
| `schema/config/__init__.py` | 147 | Replaced by typespec/__init__.py |
| `schema/column_mapper/__init__.py` | ~20 | Placeholder module, never implemented |
| **Total deleted** | **~2,975** | |

---

## Test Plan

### New test structure

```
tests/
├── typespec/
│   ├── test_universal_types.py     # Moved from tests/schema/
│   ├── test_spec.py                # TypeSpec/FieldSpec (renamed from test_schema_config.py)
│   ├── test_extraction.py          # Moved from tests/schema/test_schema_extractors.py
│   ├── test_validation.py          # Moved from tests/schema/test_schema_validators.py
│   ├── test_converters.py          # Moved from tests/schema/test_schema_converters.py
│   ├── test_custom_types.py        # Moved from tests/schema/test_custom_types.py
│   ├── test_type_bridge.py         # NEW: UniversalType ↔ MountainashDtype mapping
│   └── test_frictionless.py        # NEW: Frictionless import/export round-trips
├── conform/
│   ├── test_conform_transforms.py  # Replaces test_schema_transforms.py — cross-backend parametrized
│   ├── test_conform_builder.py     # ConformBuilder dict parsing, API surface
│   └── test_conform_compiler.py    # Compiler internals
├── schema/                         # DELETED
```

### Expected xfail reduction

Current: 27 xfailed tests (18 broken backends, 7 backend-specific, 2 type limitations).

After: The 25 backend-related xfails disappear because conform compiles to relations, which already work across all 6 backends. Only the 2 string→boolean cast limitations remain (Polars/Narwhals cannot cast Utf8View → Boolean), and these are expression-layer limitations, not conform bugs.

### Cross-backend conform tests

```python
ALL_BACKENDS = [
    "polars", "pandas", "narwhals",
    "ibis-polars", "ibis-duckdb", "ibis-sqlite",
]

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestConformCast:
    def test_cast_integer(self, backend_name, backend_factory):
        df = backend_factory.create({"val": ["1", "2", "3"]}, backend_name)
        result = ma.conform({"val": {"cast": "integer"}}).apply(df)
        actual = ma.relation(result).select("val").to_dict()["val"]
        assert actual == [1, 2, 3]
```

### Frictionless round-trip tests

```python
def test_frictionless_round_trip():
    spec = TypeSpec(fields=[
        FieldSpec(name="id", type=UniversalType.INTEGER, rename_from="raw_id"),
        FieldSpec(name="email", type=UniversalType.STRING, null_fill="unknown"),
    ], keep_only_mapped=True)

    exported = spec.to_frictionless()
    reimported = TypeSpec.from_frictionless(exported)

    assert reimported.fields[0].name == "id"
    assert reimported.fields[0].rename_from == "raw_id"
    assert reimported.fields[1].null_fill == "unknown"
    assert reimported.keep_only_mapped is True
```

---

## Deferred Work

- **Type system unification:** Merge `UniversalType` and `MountainashDtype` into a single type enum. The `type_bridge.py` interim mapping makes this a clean future task.
- **Additional import/export adapters:** dbt semantic layer, Great Expectations, Pydantic model → TypeSpec. Each is a function returning `TypeSpec`, following the `frictionless.py` pattern.
- **Constraint-based validation expressions:** Compile `FieldConstraints` (min, max, pattern, enum) to mountainash filter expressions for data quality checks.
- **`to_native()` relation terminal:** Add a relation terminal that returns the DataFrame in its original backend type, so `conform.apply(polars_df)` returns a Polars DataFrame, not always Polars. For now, `to_polars()` is the default.

---

## Dependencies

- `mountainash.expressions` — expression building (col, lit, coalesce, cast)
- `mountainash.relations` — relation compilation (relation, select, to_native)
- `mountainash.core.dtypes` — MountainashDtype enum (via type_bridge)
- No new external dependencies
