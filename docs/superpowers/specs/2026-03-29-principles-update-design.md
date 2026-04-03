# Principles Update for Schema/PyData Alignment — Design Spec

**Date:** 2026-03-29
**Branch:** `feature/substrait_alignment`

## Goal

Update the principles repository to reflect the schema/pydata alignment work (Layer 4.4) and comprehensive test suites (Layers 5.1, 5.2). One new principle document, four existing document updates, one index update.

## Scope

All changes are in: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/`

---

## 1. New: `c.api-design/build-then-apply.md`

**Status:** ENFORCED

**Content:**

SchemaBuilder implements the build-then-execute pattern for schema operations. This parallels build-then-compile (expressions) and build-then-collect (relations) — same deferred pattern, different terminal verb.

**Build phase** — `ma.schema({...})` returns a SchemaBuilder holding the spec. No execution, no backend detection. The spec uses target-oriented keys: each key is the desired output column name. The optional `"rename"` value names the source column in the input DataFrame.

```python
s = ma.schema({
    "age": {"cast": "integer"},
    "name": {"rename": "full_name"},
    "score": {"null_fill": 0.0},
})
```

**Execute phase** — `.apply(df)` constructs a SchemaConfig, translates target-oriented keys to source-oriented keys (SchemaConfig's convention), detects the backend via CastSchemaFactory, and transforms.

**Other terminals:**
- `.extract(source)` — classmethod, extracts schema from DataFrame, dataclass, or Pydantic model. Returns a SchemaBuilder.
- `.validate(df)` — checks DataFrame conformance against the schema spec. Returns a ValidationResult.

**Key convention — target-oriented vs source-oriented:**
- SchemaBuilder: `{"target_name": {"rename": "source_name", "cast": "integer"}}`
- SchemaConfig: `{"source_name": {"rename": "target_name", "cast": "integer"}}`
- `_to_schema_config_columns()` translates between conventions.

**Pattern comparison:**

| Module | Build | Terminal | Deferred Until |
|--------|-------|----------|----------------|
| Expressions | `ma.col("x").gt(5)` | `.compile(df)` | Backend detection + native expression |
| Relations | `ma.relation(df).filter(...)` | `.collect()` / `.to_polars()` | Backend detection + visitor execution |
| Schema | `ma.schema({...})` | `.apply(df)` | Backend detection + CastSchemaFactory |

---

## 2. Update: `a.architecture/relational-ast.md`

**Add section: "Extension Nodes"**

The 10 Substrait-aligned node types cover the core relational algebra. SourceRelNode is a mountainash extension node (lives in `relation_nodes/extensions_mountainash/`) for Python data sources.

- SourceRelNode is a leaf node with no `input` field
- Fields: `data: Any`, `detected_format: CONST_PYTHON_DATAFORMAT`
- Created by `ma.relation(python_data)` when `_is_python_data()` returns True
- Detection is eager (lightweight type check at build time), conversion is deferred (happens at visitor execution time via PydataIngress)
- `accept()` dispatches to `visitor.visit_source_rel(self)`

This follows the substrait-vs-mountainash separation principle: extension nodes in `extensions_mountainash/`, core nodes in the parent directory.

---

## 3. Update: `a.architecture/relation-visitor-composition.md`

**Add section: "Source Node Handling"**

UnifiedRelationVisitor handles SourceRelNode by materializing Python data into a DataFrame at execution time:

```python
def visit_source_rel(self, node):
    df = PydataIngress.convert(node.data)
    return self.backend.read(df)
```

PydataIngress delegates to PydataIngressFactory which auto-detects the Python data format (list-of-dicts, dict-of-lists, dataclass, Pydantic, named tuple, etc.) and converts to a Polars DataFrame. The result is passed to `backend.read()` just like a ReadRelNode.

Backend detection for pure SourceRelNode trees defaults to CONST_BACKEND.POLARS (since PydataIngress produces Polars DataFrames).

---

## 4. Update: `c.api-design/build-then-collect.md`

**Add section: "Source Dispatch"**

`ma.relation()` accepts both DataFrames and Python data:
- DataFrames (Polars, Pandas, Ibis, etc.) → `ReadRelNode(dataframe=data)`
- Python data (list, dict, dataclass, Pydantic) → `SourceRelNode(data=data, detected_format=...)`

`_is_python_data()` performs a lightweight type check (`isinstance(data, (list, dict))` plus dataclass/Pydantic attribute checks). Detection is eager. Conversion is deferred to terminal execution.

**Add section: "Sink Terminals"**

Beyond `.collect()` and `.to_polars()`, Relation provides additional sink terminals for Python data output:

- `.to_dicts()` → `list[dict[str, Any]]`
- `.to_tuples()` → `list[tuple]`
- `.to_dataclasses(cls)` → `list[T]` (via `cls(**row)`)
- `.to_pydantic(cls)` → `list[T]` (via `cls.model_validate(row)` when available)
- `.to_dict()` → `dict[str, list[Any]]`

These delegate to `.to_polars()` then convert, keeping the deferred execution model intact.

---

## 5. Update: `a.architecture/unified-package-roadmap.md`

Update the tracking table:

| # | Item | Status |
|---|------|--------|
| 12 | Schema/pydata alignment | Done (Layer 4.4 — SchemaBuilder, SourceRelNode, sink terminals) |
| 13 | Comprehensive schema tests | Done (371 passed, 27 xfailed across 8 test files) |
| 14 | Comprehensive pydata tests | Done (101 passed, 4 skipped across 6 test files) |

---

## 6. Update: `README.md` (principles index)

Add entry under c. API Design:
```
| build-then-apply.md | ENFORCED | SchemaBuilder deferred definition; .apply(df) triggers backend detection |
```
