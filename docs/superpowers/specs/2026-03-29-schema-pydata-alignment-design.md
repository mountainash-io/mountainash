# Schema & PyData Alignment Design

**Status:** APPROVED
**Created:** 2026-03-29

## Goal

Align the schema and pydata modules with the build-then-execute paradigm used by expressions and relations. Two public entry points: `ma.relation()` (extended to accept Python data and emit Python data) and `ma.schema()` (deferred schema definition, extraction, validation, transformation).

## Design Decisions

1. **Build-then-execute pattern** — schema and pydata get deferred plan objects that execute at terminal methods, matching expressions (`.compile()`) and relations (`.collect()`).
2. **`ma.source()` / `ma.sink()` folded into `ma.relation()`** — no separate public entry points. `ma.relation()` becomes the universal data pipeline that accepts anything (DataFrames, Python data, future: files/URIs) and outputs anything (DataFrames, Python data, future: external writes). Source and sink are internal dispatch mechanisms.
3. **`ma.schema()` stays separate** — schema has capabilities that don't fit in relation: extraction, validation, reusable definitions. It's a distinct concept.
4. **Wrap existing internals** — the new API is a thin layer over existing factories, strategies, and handlers. No restructuring of existing code. Internal refactoring deferred to a future item if/when needed.
5. **TDD for the new API surface** — tests exercise the public API, which also validates the underlying machinery.

## Public API

### `ma.relation()` — Extended

Accepts Python data in addition to DataFrames. Detection is eager (lightweight type check). Conversion is deferred until a terminal method is called.

```python
# Existing — DataFrame input
ma.relation(df).filter(ma.col("x").gt(5)).collect()

# NEW — Python data input (source dispatch)
ma.relation([{"a": 1, "b": 2}, {"a": 3, "b": 4}]).filter(...).collect()
ma.relation(my_dataclasses).sort("name").to_polars()

# NEW — Python data output (sink terminals)
ma.relation(df).to_dicts()                    # → list[dict]
ma.relation(df).to_tuples()                   # → list[tuple]
ma.relation(df).to_dataclasses(MyDC)          # → list[MyDC]
ma.relation(df).to_pydantic(MyModel)          # → list[MyModel]

# Full pipeline: Python → transform → Python
ma.relation(my_dicts).filter(...).sort("x").to_dicts()
```

### `ma.schema()` — New

Deferred schema definition with terminal methods for transformation, extraction, and validation.

```python
# Define schema transform plan
# Format mirrors existing SchemaConfig columns dict
s = ma.schema({
    "age": {"cast": "integer"},
    "name": {"rename": "full_name", "cast": "string"},
    "score": {"cast": "float", "null_fill": 0.0},
})

# Inspect (deferred — no execution yet)
s.columns          # ['age', 'name', 'score']
s.transforms       # summary of planned transforms

# Terminal: apply to a DataFrame
result_df = s.apply(df)
result_df = s.apply(df, strict=True)

# Extract schema from existing data
s = ma.schema.extract(df)             # from DataFrame
s = ma.schema.extract(MyModel)        # from Pydantic model
s = ma.schema.extract(MyDataclass)    # from dataclass

# Validate conformance
report = ma.schema(spec).validate(df)
report.is_valid    # bool
report.issues      # list of ValidationIssue
```

## Architecture

### Source Dispatch (inside `ma.relation()`)

`ma.relation()` currently only accepts DataFrames. We extend it to detect input type:

- **DataFrame** → existing `ReadRelNode` path (unchanged)
- **Python data** → `SourceRelNode` (new relation node). Holds a reference to the Python data and the auto-detected format (`CONST_PYTHON_DATAFORMAT`). At execution time, the relation visitor calls `PydataIngressFactory` to materialize the data into a DataFrame, then proceeds with the plan tree.

Detection is eager (runs at `ma.relation()` call time — lightweight type check using existing `PydataIngressFactory._get_strategy_key()` logic). The actual data conversion is deferred until a terminal method triggers the visitor.

```
ma.relation(my_dicts)       →  SourceRelNode(data=my_dicts, format=PYLIST)
  .filter(...)              →  FilterRelNode(input=SourceRelNode, ...)
  .collect()                →  visitor walks tree:
                                 1. visit_source_rel → PydataIngressFactory → DataFrame
                                 2. visit_filter_rel → backend.filter(df, predicate)
                                 3. return result
```

### Sink Dispatch (relation terminal methods)

New terminal methods on `RelationAPI` that:

1. Execute the relation plan (call `.collect()` or equivalent internally)
2. Pass the result DataFrame to existing egress machinery (`DataFrameEgressFactory` → `EgressPydataFromPolars`)
3. Return Python data

These are thin methods — 3-5 lines each, delegating to existing egress code.

```python
# In RelationAPI
def to_dicts(self) -> list[dict]:
    df = self._execute()  # collect the plan
    factory = DataFrameEgressFactory(df)
    return factory.to_list_of_dictionaries()

def to_dataclasses(self, cls):
    df = self._execute()
    factory = DataFrameEgressFactory(df)
    return factory._to_list_of_dataclasses(cls)
```

### Schema Builder

`SchemaBuilder` — new class that wraps existing internals:

- Holds a schema specification (column definitions with cast, rename, null_fill, defaults — same keys as `SchemaConfig`)
- `.apply(df)` constructs a `SchemaConfig` from the spec, uses `CastSchemaFactory` to get the right backend strategy, executes the transform
- `.extract()` delegates to existing `extractors.py`
- `.validate()` delegates to existing `validators.py`

```
ma.schema({...})          →  SchemaBuilder(spec={...})     (deferred)
  .apply(df)              →  SchemaConfig(spec) + CastSchemaFactory(df)
                              → backend strategy → transformed df

ma.schema.extract(df)     →  extractors.extract_schema(df) → SchemaBuilder
ma.schema(spec).validate(df) → validators.validate(df, spec) → ValidationResult
```

### Relation Integration with Schema

Schema transforms can be applied within a relation pipeline:

```python
schema = ma.schema({"age": {"type": "integer"}})
ma.relation(df).apply_schema(schema).filter(...).collect()
```

This adds an `ApplySchemaRelNode` (extension node) to the plan tree. The visitor delegates to `SchemaBuilder.apply()` at execution time.

## New Files

| File | Class | Role |
|------|-------|------|
| `relations/core/relation_nodes/mountainash_extensions/reln_ext_source.py` | `SourceRelNode` | Holds Python data + detected format |
| `relations/backends/.../relsys_*_source.py` (per backend) | Source visitor method | Calls `PydataIngressFactory`, returns DataFrame |
| `relations/core/relation_api/relation_api.py` (modify) | Sink terminal methods | `.to_dicts()`, `.to_dataclasses()`, etc. |
| `schema/schema_builder.py` | `SchemaBuilder` | Deferred schema API |
| `__init__.py` (modify) | `ma.schema` entry point | Re-export SchemaBuilder |

## Existing Code — Unchanged

All existing pydata and schema internals remain as-is:

- `pydata/ingress/` — 9 handlers + factory (execution layer for source)
- `pydata/egress/` — egress strategies + factory (execution layer for sink)
- `schema/config/` — SchemaConfig, types, extractors, converters, validators
- `schema/transform/` — CastSchemaFactory + 5 backend strategies

The new API wraps these; it does not replace them.

## Future Notes

- **Internal refactoring** — file renaming (standard prefixes), Protocol extraction from ABCs, breaking up large files (1001-line SchemaConfig, 907-line custom_types) — deferred until there's a concrete need
- **File/URI sources** — `ma.relation("file.csv")` can be added later by extending `SourceRelNode` detection
- **Database sources** — `ma.relation(db_connection)` same extension path
- **External writes** — `ma.relation(df).write("s3://...")` future terminal

## Testing Strategy

TDD for the new API surface. Tests exercise the public API which validates the underlying machinery.

### Schema tests (~12 tests)

- **Definition + apply:** cast, rename, null_fill, multi-transform, strict/lenient modes
- **Extract:** from Polars, Pandas, dataclass, Pydantic
- **Validate:** conforming (is_valid=True), non-conforming (returns issues)

### Source tests via relation (~8 tests)

- **Python data → relation → collect:** list of dicts, dict of lists, dataclasses, Pydantic models
- **Plan introspection:** detected format accessible on SourceRelNode
- **Source + transforms:** filter, sort chained after source

### Sink tests via relation terminals (~6 tests)

- **DataFrame → Python data:** to_dicts, to_tuples, to_dataclasses, to_pydantic

### Round-trip tests (~4 tests)

- **Python → transform → Python:** full pipeline through source, relation ops, and sink terminals
- **Cross-backend:** parametrized where applicable (Polars, Narwhals, Ibis)

### Total: ~30 tests

Cross-backend parametrized where applicable.
