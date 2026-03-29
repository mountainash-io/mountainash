# Principles Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the principles repository to reflect schema/pydata alignment work and add the build-then-apply principle.

**Architecture:** 1 new principle document, 4 existing document updates, 1 index update. All changes are markdown in the principles repository at `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/`. Plus one roadmap status update in the project repository.

**Tech Stack:** Markdown only. No code changes.

---

## File Map

| Action | Path | What Changes |
|--------|------|-------------|
| Create | `mountainash-central/.../c.api-design/build-then-apply.md` | New principle: SchemaBuilder deferred pattern |
| Modify | `mountainash-central/.../a.architecture/relational-ast.md` | Add Extension Nodes section (SourceRelNode) |
| Modify | `mountainash-central/.../a.architecture/relation-visitor-composition.md` | Add Source Node Handling section |
| Modify | `mountainash-central/.../c.api-design/build-then-collect.md` | Add Source Dispatch + Sink Terminals sections |
| Modify | `mountainash-central/.../a.architecture/unified-package-roadmap.md` | Note items #12-14 done |
| Modify | `mountainash-central/.../README.md` | Add build-then-apply entry |
| Modify | `mountainash-expressions/docs/superpowers/roadmap/2026-03-28-unified-package-roadmap.md` | Mark #12-14 done in tracking table |

Base path for principles: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions`

---

### Task 1: Create build-then-apply.md

**Files:**
- Create: `mountainash-central/01.principles/mountainash-expresions/c.api-design/build-then-apply.md`

- [ ] **Step 1: Create the new principle document**

```markdown
# Build Then Apply (Schema)

> **Status:** ENFORCED

## The Principle

Schema definition and application are separate phases — the same deferred pattern as expressions' build-then-compile and relations' build-then-collect. `ma.schema({...})` returns a `SchemaBuilder` holding the spec. `.apply(df)` detects the backend via `CastSchemaFactory` and transforms the DataFrame. No DataFrame is needed at definition time.

## Rationale

Separating definition from application means schemas can be defined once, shared across contexts, validated before use, and applied to any backend. The `SchemaBuilder` uses target-oriented keys (output column name as key) which is intuitive for users defining what they want. The underlying `SchemaConfig` uses source-oriented keys. `SchemaBuilder._to_schema_config_columns()` translates between conventions.

## Examples

**Build phase (backend-agnostic):**

```python
import mountainash as ma

s = ma.schema({
    "age": {"cast": "integer"},
    "name": {"rename": "full_name"},
    "score": {"null_fill": 0.0},
})
# At this point: no DataFrame, no backend detected
# s is a SchemaBuilder holding the spec dict
```

**Apply phase (triggers backend detection):**

```python
result = s.apply(df)
# 1. Translate target-oriented keys → source-oriented (SchemaConfig)
# 2. CastSchemaFactory detects backend from df type
# 3. Backend strategy applies rename, cast, null_fill
# 4. Return transformed DataFrame (same backend as input)
```

**Other terminals:**

| Terminal | Returns | Phase |
|----------|---------|-------|
| `.apply(df)` | Transformed DataFrame | Execute |
| `.extract(source)` | `SchemaBuilder` | Build (classmethod) |
| `.validate(df)` | `ValidationResult` | Inspect |
| `.columns` | `list[str]` | Inspect |
| `.transforms` | `dict` | Inspect |

**Key convention — target-oriented vs source-oriented:**

SchemaBuilder (user-facing): `{"target_col": {"rename": "source_col", "cast": "integer"}}`
SchemaConfig (internal):     `{"source_col": {"rename": "target_col", "cast": "integer"}}`

**Pattern comparison across modules:**

| Module | Build | Terminal | Deferred Until |
|--------|-------|----------|----------------|
| Expressions | `ma.col("x").gt(5)` | `.compile(df)` | Backend detection + native expression |
| Relations | `ma.relation(df).filter(...)` | `.collect()` / `.to_polars()` | Backend detection + visitor execution |
| Schema | `ma.schema({...})` | `.apply(df)` | Backend detection + CastSchemaFactory |

## Anti-Patterns

- Applying transforms at definition time — `SchemaBuilder` holds only spec data
- Requiring users to specify which backend to use — CastSchemaFactory auto-detects
- Mixing target-oriented and source-oriented keys in the same API — SchemaBuilder is target-oriented, SchemaConfig is source-oriented, `_to_schema_config_columns()` bridges

## Technical Reference

- `src/mountainash/schema/schema_builder.py` — `SchemaBuilder` class, `_to_schema_config_columns()` key translation
- `src/mountainash/schema/config/schema_config.py` — `SchemaConfig.apply()`, backend delegation
- `src/mountainash/schema/transform/cast_schema_factory.py` — `CastSchemaFactory`, backend detection
- `src/mountainash/__init__.py` — `ma.schema` entry point (aliased from `SchemaBuilder`)

## Future Considerations

- Schema composition: combining multiple SchemaBuilders into a pipeline
- Schema diffing: comparing two SchemaBuilders to see what would change
- Lazy validation: `.validate(df)` currently checks columns only; could add type compatibility checks
```

- [ ] **Step 2: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/c.api-design/build-then-apply.md
git commit -m "docs(principles): add build-then-apply principle for SchemaBuilder"
```

---

### Task 2: Update relational-ast.md — add Extension Nodes section

**Files:**
- Modify: `mountainash-central/01.principles/mountainash-expresions/a.architecture/relational-ast.md`

- [ ] **Step 1: Add Extension Nodes section before Anti-Patterns**

After the "Nodes compose into plan trees" code block (after line 54), add:

```markdown
## Extension Nodes

The 10 Substrait-aligned node types cover the core relational algebra. `SourceRelNode` is a mountainash extension node (in `relation_nodes/extensions_mountainash/`) for Python data sources.

| Node | Namespace | Key Fields |
|------|-----------|------------|
| `SourceRelNode` | Mountainash extension | `data: Any`, `detected_format: CONST_PYTHON_DATAFORMAT` |

`SourceRelNode` is a leaf node — it has no `input` field, like `ReadRelNode`. The difference:
- `ReadRelNode` holds an existing DataFrame (Polars, Pandas, etc.)
- `SourceRelNode` holds raw Python data (list, dict, dataclass, Pydantic) with a detected format tag

Detection is eager (lightweight `_is_python_data()` check at `ma.relation()` call time). Conversion is deferred (happens at visitor execution time via `PydataIngress.convert()`).

This follows the substrait-vs-mountainash separation: extension nodes live in `extensions_mountainash/`, core Substrait nodes live in the parent directory.
```

- [ ] **Step 2: Update the Technical Reference to include SourceRelNode**

Add to the Technical Reference section:

```markdown
- `src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_source.py` — `SourceRelNode`
```

- [ ] **Step 3: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/a.architecture/relational-ast.md
git commit -m "docs(principles): add SourceRelNode extension node to relational-ast"
```

---

### Task 3: Update relation-visitor-composition.md — add Source Node Handling

**Files:**
- Modify: `mountainash-central/01.principles/mountainash-expresions/a.architecture/relation-visitor-composition.md`

- [ ] **Step 1: Add Source Node Handling section before Anti-Patterns**

After the "Three types of expressions in relational nodes" list (after line 44), add:

```markdown
## Source Node Handling

`visit_source_rel()` materializes Python data into a DataFrame at execution time:

```python
def visit_source_rel(self, node: Any) -> Any:
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress
    df = PydataIngress.convert(node.data)
    return self.backend.read(df)
```

`PydataIngress` delegates to `PydataIngressFactory` which auto-detects the Python data format (list-of-dicts, dict-of-lists, dataclass, Pydantic, named tuple, etc.) and converts to a Polars DataFrame. The result is passed to `backend.read()` — the same entry point as `ReadRelNode`.

**Backend detection for SourceRelNode trees:** When the plan tree contains only `SourceRelNode` leaves (no `ReadRelNode`), `_detect_backend()` defaults to `CONST_BACKEND.POLARS` since PydataIngress produces Polars DataFrames.
```

- [ ] **Step 2: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/a.architecture/relation-visitor-composition.md
git commit -m "docs(principles): add source node handling to relation-visitor-composition"
```

---

### Task 4: Update build-then-collect.md — add Source Dispatch and Sink Terminals

**Files:**
- Modify: `mountainash-central/01.principles/mountainash-expresions/c.api-design/build-then-collect.md`

- [ ] **Step 1: Add Source Dispatch section after the terminal operations table**

After the terminal operations table (after line 49), add:

```markdown
## Source Dispatch

`ma.relation()` accepts both DataFrames and Python data:

```python
# DataFrame → ReadRelNode (holds existing DataFrame)
r = ma.relation(polars_df)

# Python data → SourceRelNode (deferred conversion)
r = ma.relation([{"name": "Alice", "age": 30}])
r = ma.relation({"name": ["Alice", "Bob"], "age": [30, 25]})
```

`_is_python_data()` performs a lightweight type check (`isinstance(data, (list, dict))` plus dataclass/Pydantic attribute checks). Detection is eager — it happens at `ma.relation()` call time. Conversion is deferred — it happens at terminal execution time via `PydataIngress.convert()` in the visitor.

## Sink Terminals

Beyond `.collect()` and `.to_polars()`, Relation provides additional terminal operations for Python data output:

| Terminal | Returns | Mechanism |
|----------|---------|-----------|
| `.to_dicts()` | `list[dict[str, Any]]` | `.to_polars().to_dicts()` |
| `.to_dict()` | `dict[str, list[Any]]` | `.to_polars().to_dict(as_series=False)` |
| `.to_tuples()` | `list[tuple]` | `.to_polars().rows()` |
| `.to_dataclasses(cls)` | `list[T]` | `.to_dicts()` → `cls(**row)` |
| `.to_pydantic(cls)` | `list[T]` | `.to_dicts()` → `cls.model_validate(row)` |

These all delegate to `.to_polars()` first, keeping the deferred execution model intact. The Polars DataFrame is the common intermediate format.
```

- [ ] **Step 2: Update the Relation vs Expression comparison table**

Replace the existing table (lines 53-58) with an expanded version:

```markdown
**Relation vs Expression compilation:**

| | Expressions | Relations |
|---|---|---|
| Build returns | `BaseExpressionAPI` wrapping `ExpressionNode` | `Relation` wrapping `RelationNode` |
| Compile trigger | `.compile(df)` | `.collect()` / `.to_polars()` / `.to_dicts()` / etc. |
| Backend detection | From passed DataFrame | From leaf `ReadRelNode.dataframe` (or default Polars for `SourceRelNode`) |
| Visitor | `UnifiedExpressionVisitor` | `UnifiedRelationVisitor` (composes expression visitor) |
```

- [ ] **Step 3: Add SourceRelNode to anti-patterns note**

Add to the anti-patterns section:

```markdown
- Eagerly converting Python data in `ma.relation()` — only detection happens at build time; conversion is deferred to visit time via SourceRelNode
```

- [ ] **Step 4: Add to Technical Reference**

```markdown
- `src/mountainash/relations/core/relation_nodes/extensions_mountainash/reln_ext_source.py` — `SourceRelNode` for Python data
- `src/mountainash/pydata/ingress/pydata_ingress.py` — `PydataIngress.convert()` for deferred conversion
```

- [ ] **Step 5: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/c.api-design/build-then-collect.md
git commit -m "docs(principles): add source dispatch and sink terminals to build-then-collect"
```

---

### Task 5: Update README.md index and roadmap status

**Files:**
- Modify: `mountainash-central/01.principles/mountainash-expresions/README.md`
- Modify: `mountainash-central/01.principles/mountainash-expresions/a.architecture/unified-package-roadmap.md`
- Modify: `mountainash-expressions/docs/superpowers/roadmap/2026-03-28-unified-package-roadmap.md`

- [ ] **Step 1: Add build-then-apply to README.md**

In the `## c. API Design` table (after the `build-then-collect.md` row), add:

```markdown
| [build-then-apply.md](c.api-design/build-then-apply.md) | ENFORCED | SchemaBuilder deferred definition; .apply(df) triggers backend detection via CastSchemaFactory |
```

- [ ] **Step 2: Update unified-package-roadmap.md in principles repo**

The principles version is a short pointer document. After the "Layer Overview" section, add:

```markdown
## Completed Items (as of 2026-03-29)

- **#12 Schema/pydata alignment** (Layer 4.4) — SchemaBuilder, SourceRelNode, sink terminals
- **#13 Comprehensive schema tests** (Layer 5.1) — 371 passed, 27 xfailed across 8 test files
- **#14 Comprehensive pydata tests** (Layer 5.2) — 101 passed, 4 skipped across 6 test files
```

- [ ] **Step 3: Update tracking table in project roadmap**

In `mountainash-expressions/docs/superpowers/roadmap/2026-03-28-unified-package-roadmap.md`, update lines 270-272:

Replace:
```
| 12 | Schema/pydata alignment | 4.4 | M | Not started |
| 13 | Comprehensive schema tests | 5.1 | M | Not started |
| 14 | Comprehensive pydata tests | 5.2 | M | Not started |
```

With:
```
| ~~12~~ | ~~Schema/pydata alignment~~ | 4.4 | ~~M~~ | ✅ Done (SchemaBuilder, SourceRelNode, sink terminals) |
| ~~13~~ | ~~Comprehensive schema tests~~ | 5.1 | ~~M~~ | ✅ Done (371 passed, 27 xfailed, 8 test files) |
| ~~14~~ | ~~Comprehensive pydata tests~~ | 5.2 | ~~M~~ | ✅ Done (101 passed, 4 skipped, 6 test files) |
```

- [ ] **Step 4: Commit both repos**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/README.md 01.principles/mountainash-expresions/a.architecture/unified-package-roadmap.md
git commit -m "docs(principles): add build-then-apply to index, update roadmap status"

cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions
git add docs/superpowers/roadmap/2026-03-28-unified-package-roadmap.md
git commit -m "docs: mark roadmap items #12-14 as done"
```
