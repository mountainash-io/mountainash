# Mountainash Unified Package Roadmap

**Status:** ACTIVE
**Created:** 2026-03-28
**Last Updated:** 2026-03-28

## Overview

The mountainash unified package consolidation is complete (Phases 1-4). Four previously separate packages now live under one `mountainash` namespace:

| Module | Source | Lines | Tests | Status |
|--------|--------|-------|-------|--------|
| `mountainash.core` | 3 files | ~250 | via expressions | Stable |
| `mountainash.expressions` | 224 files | ~25,000 | 2842 passing | Mature |
| `mountainash.dataframes` | 45 files | ~6,300 | 85 passing | Ported, working |
| `mountainash.schema` | 19 files | ~6,485 | 10 smoke tests | Ported, partial wiring |
| `mountainash.pydata` | 23 files | ~3,833 | 2 passing (2 skipped) | Ported, partial wiring |

**Full suite:** 2939 passed, 278 xfailed, 27 pre-existing failures, 5 skipped.

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

### 2.3 Unify backend constants

**What:** Three different backend enums exist:
- `mountainash.core.constants.CONST_VISITOR_BACKENDS` (expressions)
- `mountainash.dataframes.core.dataframe_system.constants.CONST_DATAFRAME_BACKEND` (dataframes)
- Various `CONST_DATAFRAME_TYPE` references (schema, pydata)

**Target:** One `mountainash.core.constants.CONST_BACKEND` enum that all modules use. Keep module-specific aliases for backwards compat.

**Estimated scope:** Medium (enum consolidation + update all references)

---

### 2.4 Unify type aliases

**What:** `SupportedDataFrames`, `SupportedExpressions` duplicated across modules.

**Target:** Single source in `mountainash.core.types`, re-exported by modules for convenience.

**Note:** Phase 1 already moved expressions types to core. This completes the job for dataframes types.

**Estimated scope:** Small

---

## Layer 3: Missing Operations

**Priority:** Medium
**Goal:** Make `mountainash.dataframes` genuinely useful for real-world data workflows.
**Dependencies:** Layer 1 (working wiring), optionally Layer 2 (cleaner infra)

### 3.1 Core table operations

**What:** The most-requested operations missing from TableBuilder:

| Operation | Priority | Substrait Analog |
|-----------|----------|-----------------|
| `sort` / `order_by` | High | SortRel |
| `with_columns` | High | ProjectRel (extend) |
| `group_by` + `agg` | High | AggregateRel |
| `unique` / `distinct` | Medium | — |
| `describe` / `summary` | Low | — |

**Approach:** Add to DataFrameSystem protocol, implement in all 3 backends, expose via TableBuilder.

**Estimated scope:** Large (new protocols, 3 backend implementations each, TableBuilder namespaces, tests)

---

### 3.2 Reshape operations

**What:** pivot, melt/unpivot, transpose — exist in the OLD dataframes architecture but weren't ported (they were in the superseded module structure).

**Approach:** Reimplement in the new DataFrameSystem pattern.

**Estimated scope:** Medium

---

### 3.3 Window functions (expressions)

**What:** Substrait defines window function extensions. The expression system has protocol stubs (`prtcl_expsys_window_arithmetic.py`) but no backend implementations.

**Approach:** Implement window function support in expressions: `ma.col("x").over(partition_by="group")`.

**Estimated scope:** Large

---

## Layer 4: Architectural Alignment

**Priority:** Medium-Low
**Goal:** Bring dataframes/schema/pydata up to the same architectural standard as expressions.
**Dependencies:** Layers 1-2 (stable foundation), ideally Layer 3 (align with final operation set)

### 4.1 Dataframes naming conventions

**What:** Expression files use prefixes (`prtcl_`, `expsys_`, `exn_`, `api_bldr_`). Dataframes files don't. Align for consistency.

**Renames:**
- `core/protocols/builder_protocols.py` → `prtcl_*.py` per protocol
- `backends/polars/dataframe_system.py` → `dfsys_pl_*.py` or similar
- Protocol files split by category (currently one file with all protocols)

**Estimated scope:** Medium (mechanical renames + import updates)

---

### 4.2 Dataframes wiring audit

**What:** Extend the expressions wiring audit (`test_protocol_alignment.py`) to cover DataFrameSystem protocols. Same approach: protocol methods are source of truth, test validates ENUM → function mapping → backend implementation chain.

**Estimated scope:** Medium (new test class, KNOWN_ASPIRATIONAL for dataframes)

---

### 4.3 Substrait-informed protocol categories

**What:** Align DataFrameSystem protocol categories with Substrait relational operations:

| Current Protocol | Substrait Analog |
|-----------------|-----------------|
| `CastProtocol` | — (Mountainash extension) |
| `IntrospectProtocol` | — (Mountainash extension) |
| `SelectProtocol` | ProjectRel |
| `JoinProtocol` | JoinRel |
| `FilterProtocol` | FilterRel |
| `RowProtocol` | FetchRel (limit/offset) |
| `LazyProtocol` | — (execution control) |
| (missing) | SortRel, AggregateRel |

**Approach:** Rename protocol categories to use Substrait naming where applicable. Add new protocols for sort/aggregate.

**Estimated scope:** Medium

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

## Dependency Graph

```
Layer 1 (Wiring)
  ├── 1.1 Schema transforms
  ├── 1.2 Pydata ingress
  └── 1.3 End-to-end pipeline test
          │
Layer 2 (Shared Infra)
  ├── 2.1 Factory base → core
  ├── 2.2 Runtime imports → core
  ├── 2.3 Unify constants
  └── 2.4 Unify types
          │
Layer 3 (Operations)          Layer 4 (Alignment)
  ├── 3.1 sort/group_by/agg    ├── 4.1 Naming conventions
  ├── 3.2 Reshape               ├── 4.2 Wiring audit
  ├── 3.3 Window functions       ├── 4.3 Substrait categories
  │                              └── 4.4 Schema/pydata alignment
  │                                      │
  └──────────────┬───────────────────────┘
                 │
Layer 5 (Testing + Docs)  ←── parallel with all layers
  ├── 5.1-5.3 Test coverage
  └── 5.4-5.5 Documentation
                 │
Layer 6 (Release)
  ├── 6.1 PyPI strategy
  ├── 6.2 Deprecation
  └── 6.3 CI/CD
```

## Recommended Execution Order

Each item becomes its own brainstorm → spec → plan → implement cycle:

| # | Item | Layer | Est. Size | Depends On |
|---|------|-------|-----------|------------|
| 1 | Wire schema transforms | 1.1 | S | — |
| 2 | Wire pydata ingress | 1.2 | S | — |
| 3 | End-to-end pipeline test | 1.3 | S | 1, 2 |
| 4 | Extract factory base to core | 2.1 | M | 1, 2 |
| 5 | Extract runtime imports to core | 2.2 | S | 1, 2 |
| 6 | Unify backend constants | 2.3 | M | 4, 5 |
| 7 | Unify type aliases | 2.4 | S | 6 |
| 8 | sort / with_columns / group_by+agg | 3.1 | L | 3 |
| 9 | Reshape operations | 3.2 | M | 3 |
| 10 | Dataframes naming conventions | 4.1 | M | 8, 9 |
| 11 | Dataframes wiring audit | 4.2 | M | 10 |
| 12 | Substrait protocol categories | 4.3 | M | 10, 11 |
| 13 | Comprehensive schema tests | 5.1 | M | 1 |
| 14 | Comprehensive pydata tests | 5.2 | M | 2 |
| 15 | CLAUDE.md updates | 5.4 | S | 3 |
| 16 | Window functions | 3.3 | L | 8 |
| 17 | Schema/pydata alignment | 4.4 | M | 12 |
| 18 | Principles repo updates | 5.5 | S | 11 |
| 19 | PyPI strategy + release | 6.1-6.3 | M | all above |

**Size key:** S = 1-2 hours, M = half day, L = 1-2 days
