# Mountainash Unified Package Roadmap

**Status:** ACTIVE
**Created:** 2026-03-28
**Last Updated:** 2026-03-28

## Overview

The mountainash unified package consolidation is complete (Phases 1-4). Five modules now live under one `mountainash` namespace:

| Module | Source | Tests | Status |
|--------|--------|-------|--------|
| `mountainash.core` | ~300 lines | via expressions + relations | Stable — shared constants, types, enums |
| `mountainash.expressions` | ~25,000 lines | ~2850 passing | Mature — Substrait-aligned expression AST |
| `mountainash.relations` | ~60 files | 290 passing, 3 xfailed | **NEW** — Substrait-aligned relational AST |
| `mountainash.dataframes` | ~6,300 lines | 85 passing | **Deprecated** — superseded by relations |
| `mountainash.schema` | ~6,485 lines | 10 smoke tests | Ported, partial wiring |
| `mountainash.pydata` | ~3,833 lines | 2 passing (2 skipped) | Ported, partial wiring |

**Full suite:** ~3250 passed, ~280 xfailed, 7 pre-existing failures.

### What changed (2026-03-28)

**Relational AST** (`mountainash.relations`) was built as a complete replacement for `mountainash.dataframes`. It mirrors the expressions architecture: immutable Pydantic AST nodes → three-layer separation (protocol → API → backend) → unified visitor → deferred compilation. Entry point: `ma.relation(df)`.

This supersedes roadmap items 3.1 (core table ops), 3.2 (reshape), and 4.1–4.3 (dataframes alignment). The old `dataframes` module is now on a deprecation path.

This roadmap tracks remaining work from "ported but loosely connected" to "unified, architecturally aligned whole."

---

## Layer 1: Cross-Module Wiring

**Priority:** Immediate
**Goal:** Make the ported modules actually work together, not just import successfully.
**Dependencies:** None (foundation for everything else)

### 1.1 Wire schema transforms to dataframes infrastructure

**What:** The schema `transform/` module is currently optional (try/except) because it imports `BaseStrategyFactory` and `DataFrameTypeFactoryMixin` from `mountainash.dataframes.factories` — a path from the OLD dataframes package that doesn't exist in the ported version.

**Fix:** Update schema transform imports to use the actual ported paths:
- `BaseStrategyFactory` → find where it lives in `mountainash.dataframes` now, or inline the base class
- `DataFrameTypeFactoryMixin` → same
- `runtime_imports` (import_polars, import_pandas, etc.) → find in ported dataframes or inline

**Success criteria:** `from mountainash.schema import SchemaTransformFactory` works without try/except. Schema transforms can be applied to a Polars DataFrame.

**Estimated scope:** Small (import path fixes, possibly extracting a few functions)

---

### 1.2 Wire pydata ingress to dataframes infrastructure

**What:** Pydata's `PydataIngressFactory` imports from `mountainash.dataframes.factories`, `mountainash.dataframes.runtime_imports`, and `mountainash.dataframes.typing` — OLD paths that don't exist.

**Fix:** Same as 1.1 — update to actual ported paths.

**Success criteria:** `from mountainash.pydata.ingress import PydataIngressFactory` works. Can convert a Python dict to a Polars DataFrame via `PydataIngressFactory().convert(data)`.

**Estimated scope:** Small

---

### 1.3 Validate end-to-end pipeline

**What:** Test the full pipeline: Python data → DataFrame → schema transform → expression filter → output.

**Success criteria:** This works:
```python
import mountainash as ma
from mountainash.schema import SchemaConfig
from mountainash.pydata.ingress import PydataIngressFactory

# Ingress
data = [{"age": "25", "name": "alice"}, {"age": "35", "name": "bob"}]
df = PydataIngressFactory().convert(data)

# Schema transform (cast string age to int)
config = SchemaConfig(columns={"age": {"cast": "integer"}})
# ... apply transform ...

# Expression filter
result = ma.table(df).filter(ma.col("age").gt(30)).to_polars()
```

**Estimated scope:** Small (integration test, minimal code changes)

---

## Layer 2: Shared Infrastructure Refactoring

**Priority:** High
**Goal:** Eliminate duplication, establish `mountainash.core` as the single source of truth for shared patterns.
**Dependencies:** Layer 1 (need working cross-module imports first)

### 2.1 Extract factory base classes to core

**What:** `BaseStrategyFactory` and `DataFrameTypeFactoryMixin` are generic patterns used by dataframes, schema, and pydata. They currently live in the old dataframes factory module. Extract to `mountainash.core.factories`.

**Creates:**
- `mountainash/core/factories.py` — `BaseStrategyFactory[InputT, StrategyT]`, `DataFrameTypeFactoryMixin`

**Consumers:** dataframes (CastDataFrameFactory, etc.), schema (CastSchemaFactory), pydata (PydataIngressFactory)

**Estimated scope:** Medium (move + update all consumers + tests)

---

### 2.2 Extract runtime imports to core

**What:** `import_polars()`, `import_pandas()`, `import_narwhals()`, `import_ibis()` — lazy import helpers used by dataframes, schema, and pydata backends. Currently in `mountainash.dataframes.runtime_imports` (old path) or scattered.

**Creates:**
- `mountainash/core/lazy_imports.py` — all lazy import helpers

**Estimated scope:** Small

---

### 2.3 Unify backend constants ✅ DONE

Collapsed 11 overlapping backend enums across 6 files into `CONST_BACKEND` (StrEnum) + `CONST_BACKEND_SYSTEM` + `CONST_DATAFRAME_TYPE` + `CONST_IBIS_INMEMORY_BACKEND` in `mountainash.core.constants`. Old enum files replaced with re-export shims.

---

### 2.4 Unify type aliases ✅ DONE

`mountainash.core.types` is now the single source of truth for all shared type aliases (DataFrame, expression, series). Eliminated 428 lines of duplication. Old typing modules re-export from core.

---

## Layer 3: Missing Operations

**Priority:** Medium
**Goal:** Complete the operation set across both expressions and relations.
**Dependencies:** Layer 1 (working wiring), Layer 2 (shared infra)

### 3.1 Core table operations ✅ SUPERSEDED by Relational AST

The `mountainash.relations` module now provides all core table operations via a Substrait-aligned relational AST: sort, with_columns, group_by+agg, unique, filter, join (7 types + asof), head/tail/slice, select/drop/rename, concat/union, drop_nulls, with_row_index, explode, sample, pivot, unpivot, top_k.

**290 tests passing** across Polars, Narwhals (pandas + PyArrow), and Ibis backends.

See: `docs/superpowers/specs/2026-03-28-relational-ast-design.md`

---

### 3.2 Reshape operations ✅ SUPERSEDED by Relational AST

Pivot, unpivot, explode are implemented as ExtensionRelNode operations in `mountainash.relations`.

---

### 3.3 Window functions (expressions)

**What:** Substrait defines window function extensions. The expression system has protocol stubs (`prtcl_expsys_window_arithmetic.py`) but no backend implementations.

**Approach:** Implement window function support in expressions: `ma.col("x").over(partition_by="group")`.

**Estimated scope:** Large

---

## Layer 4: Architectural Alignment

**Priority:** Medium-Low
**Goal:** Align remaining modules (schema, pydata) and deprecate old dataframes.
**Dependencies:** Layer 3 (relations module complete)

### 4.1–4.3 Dataframes alignment ✅ SUPERSEDED

The `mountainash.relations` module was built from scratch with Substrait-aligned naming, wiring audit, and protocol categories. The old `mountainash.dataframes` module does not need alignment — it is being deprecated.

**Migration plan:**
1. ~~Both systems coexist~~ ✅ Done — `ma.relation()` and `ma.table()` both work
2. Port any remaining `dataframes`-only consumers to `relations`
3. Add DeprecationWarning to `ma.table()`
4. Remove `mountainash.dataframes` after migration complete

---

### 4.4 Schema + pydata alignment

**What:** Bring schema and pydata modules to the same pattern: protocols, consistent naming, testable units.

**Lower priority** — these modules are smaller and less architecturally complex.

**Estimated scope:** Medium

---

## Layer 5: Testing + Documentation

**Priority:** Ongoing (parallel with other layers)
**Goal:** Comprehensive coverage and up-to-date documentation.

### 5.1 Comprehensive schema tests

**What:** Schema has 10 smoke tests. Need full coverage of:
- SchemaConfig creation, serialization, application
- UniversalType mappings (all backends)
- Schema transforms across all 5 backends
- Extractors (from dataclass, Pydantic, DataFrame)
- Validators

**Estimated scope:** Medium

---

### 5.2 Comprehensive pydata tests

**What:** Pydata has 2 passing tests. Need coverage of:
- All 10 ingress handlers (dataclass, Pydantic, dict, list, tuple, etc.)
- Egress strategies
- Round-trip tests (Python → DataFrame → Python)

**Estimated scope:** Medium

---

### 5.3 Dataframes edge case tests

**What:** 85 tests pass but 20 pre-existing resolver failures (pandas cross-backend). Fix or document these.

**Estimated scope:** Small-Medium

---

### 5.4 CLAUDE.md updates

**What:** CLAUDE.md was updated for Phase 1 but not for dataframes, schema, or pydata. Add sections for each module.

**Estimated scope:** Small

---

### 5.5 Principles repo updates

**What:** The wiring matrix in `mountainash-central` covers expressions only. Add:
- Dataframes wiring matrix (once Layer 4.2 audit exists)
- Unified package architecture principle document
- Roadmap pointer

**Estimated scope:** Small

---

## Layer 6: Release + Deprecation

**Priority:** Low (after Layers 1-3 are stable)
**Goal:** Publish the unified package and deprecate the old ones.

### 6.1 PyPI publication strategy

**What:** Decide on:
- Package name on PyPI (`mountainash`?)
- Version numbering (CalVer? SemVer?)
- Optional dependency groups (`[dataframes]`, `[schema]`, `[pydata]`, `[all]`)

---

### 6.2 Old package deprecation

**What:** The old `mountainash-expressions`, `mountainash-dataframes`, `mountainash-schema`, `mountainash-pydata` packages. Strategy:
- Publish final versions that are thin shims pointing to `mountainash`
- Emit DeprecationWarning on import
- Remove after N months

---

### 6.3 CI/CD unification

**What:** One CI pipeline for the unified package instead of four separate ones.

---

## Dependency Graph (Updated)

```
✅ DONE                           REMAINING
─────────────────                 ─────────────────
Layer 2.3 Constants               Layer 1.1 Schema wiring
Layer 2.4 Types                   Layer 1.2 Pydata wiring
Layer 3.1 Table ops (relations)   Layer 1.3 End-to-end test
Layer 3.2 Reshape (relations)     Layer 2.1 Factory base → core
Layer 4.1-4.3 (superseded)        Layer 2.2 Runtime imports → core
                                  Layer 3.3 Window functions
                                  Layer 4.4 Schema/pydata alignment
                                  Layer 5.1-5.5 Testing + docs
                                  Layer 6 Release

Dependency flow for remaining work:
  1.1 + 1.2 → 1.3 → 2.1 + 2.2
                        │
                        ├── 3.3 Window functions
                        ├── 4.4 Schema/pydata alignment
                        ├── 5.1-5.5 Testing + docs
                        └── 6.1-6.3 Release
```

## Recommended Execution Order (Updated)

| # | Item | Layer | Est. Size | Status |
|---|------|-------|-----------|--------|
| ~~1~~ | ~~Unify backend constants~~ | 2.3 | ~~M~~ | ✅ Done |
| ~~2~~ | ~~Unify type aliases~~ | 2.4 | ~~S~~ | ✅ Done |
| ~~3~~ | ~~Core table operations~~ | 3.1 | ~~L~~ | ✅ Superseded by Relational AST |
| ~~4~~ | ~~Reshape operations~~ | 3.2 | ~~M~~ | ✅ Superseded by Relational AST |
| ~~5~~ | ~~Dataframes alignment~~ | 4.1-4.3 | ~~M~~ | ✅ Superseded by Relational AST |
| 6 | Wire schema transforms | 1.1 | S | Not started |
| 7 | Wire pydata ingress | 1.2 | S | Not started |
| 8 | End-to-end pipeline test | 1.3 | S | Not started (depends on 6, 7) |
| 9 | Extract factory base to core | 2.1 | M | Not started |
| 10 | Extract runtime imports to core | 2.2 | S | Not started |
| 11 | Window functions (.over()) | 3.3 | L | Not started |
| 12 | Schema/pydata alignment | 4.4 | M | Not started |
| 13 | Comprehensive schema tests | 5.1 | M | Not started |
| 14 | Comprehensive pydata tests | 5.2 | M | Not started |
| 15 | CLAUDE.md + principles updates | 5.4-5.5 | S | ✅ Done (this update) |
| 16 | Deprecate dataframes module | 4.1 | S | Not started |
| 17 | PyPI strategy + release | 6.1-6.3 | M | Not started |

**Size key:** S = 1-2 hours, M = half day, L = 1-2 days
