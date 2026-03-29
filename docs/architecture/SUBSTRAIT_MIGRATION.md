# Substrait Migration Architecture

> **Living Architecture Document** for mountainash-expressions Substrait alignment

## Table of Contents

1. [Overview](#overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Milestones](#milestones)
4. [Phase Details](#phase-details)
5. [ADR Index](#adr-index)

---

## Overview

### Goal

Align mountainash-expressions with Substrait topology to enable:
- Cross-language expression serialization
- Backend interoperability (Polars, Narwhals, Ibis)
- Standard function naming and semantics
- Future Substrait import/export capability

### Current State

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER          │ DECLARED │ IMPLEMENTED │ GAP              │
├─────────────────────────────────────────────────────────────┤
│ Function Enums │   105    │    105      │ 0% (complete)    │
│ Protocols      │   153    │    ~40      │ 74% stubs        │
│ Public API     │   105    │     40      │ 62% missing      │
│ Backends       │   105    │    101      │ 4% missing       │
└─────────────────────────────────────────────────────────────┘
```

### Target State

- Full Substrait module naming convention
- Mountainash extensions clearly separated (`ext_*.py`)
- Dual temporal API (Substrait + extension)
- Complete protocol implementations
- 100% API exposure for all defined functions

---

## Architecture Decisions

### AD-001: Module Naming Convention

**Decision**: Full Substrait naming with extension prefix

| Category | Pattern | Example |
|----------|---------|---------|
| Substrait scalar | `scalar_{category}.py` | `scalar_arithmetic.py` |
| Substrait core | `{name}.py` | `field_reference.py`, `literal.py` |
| Mountainash ext | `ext_{name}.py` | `ext_ternary.py`, `ext_name.py` |

### AD-002: Temporal API Strategy

**Decision**: Dual API implementation

- **Substrait API**: `extract(component)`, `add_intervals(interval)`
- **Extension API**: `dt_year()`, `dt_month()`, `dt_add_days()`, etc.

Both APIs implemented independently in separate modules.

### AD-003: Expression Node Alignment

**Decision**: 1:1 mapping with Substrait expression types

| Substrait | Mountainash | Status |
|-----------|-------------|--------|
| Literal | LiteralNode | ✅ |
| FieldReference | FieldReferenceNode | ✅ |
| ScalarFunction | ScalarFunctionNode | ✅ |
| IfThen | IfThenNode | ✅ |
| Cast | CastNode | ✅ |
| SingularOrList | SingularOrListNode | ❌ CREATE |
| AggregateFunction | AggregateNode | ❌ CREATE |
| WindowFunction | WindowNode | ❌ FUTURE |

---

## Milestones

### Milestone 1: Foundation (Phase 1)

**Target**: Fix blocking node layer issues
**Milestone**: [Phase 1: Foundation](https://github.com/mountainash-io/mountainash-expressions/milestone/1)

| Issue | Description | Priority |
|-------|-------------|----------|
| [#1](https://github.com/mountainash-io/mountainash-expressions/issues/1) | Create SingularOrListNode | P0 |
| [#2](https://github.com/mountainash-io/mountainash-expressions/issues/2) | Fix ConditionalNode import | P0 |
| [#3](https://github.com/mountainash-io/mountainash-expressions/issues/3) | Add visit_singular_or_list() to visitor | P0 |
| [#4](https://github.com/mountainash-io/mountainash-expressions/issues/4) | Implement is_in() backend methods | P1 |

**Exit Criteria**:
- [ ] All 6 node types implemented and importable
- [ ] UnifiedExpressionVisitor handles all node types
- [ ] Tests pass for SingularOrListNode

**ADR**: `docs/adr/ADR-001-singular-or-list-node.md`

---

### Milestone 2: Module Reorganization (Phase 2)

**Target**: Rename modules to Substrait topology

| Task | Description |
|------|-------------|
| Split core.py | → field_reference.py + literal.py |
| Split boolean.py | → scalar_comparison.py + scalar_boolean.py + scalar_set.py |
| Rename type.py | → cast.py |
| Merge null.py | → scalar_comparison.py |
| Merge horizontal.py | → scalar_comparison.py |
| Rename extensions | → ext_name.py, ext_native.py, ext_ternary.py |

**Exit Criteria**:
- [ ] All modules follow naming convention
- [ ] All imports updated throughout codebase
- [ ] Tests pass with new module structure

**ADR**: `docs/adr/ADR-004-module-reorganization.md`

---

### Milestone 3: Method Migration (Phase 3)

**Target**: Port implementations from deprecated code

| Task | Source | Methods |
|------|--------|---------|
| Arithmetic | `_deprecated/202511/` | negate, abs, sign, sqrt, exp, ln |
| String | `_deprecated/202511/` | All 12 operations |
| Temporal | `_deprecated/202511/` | Dual API implementation |
| Comparison | Current | Add Substrait aliases |

**Exit Criteria**:
- [ ] All deprecated implementations ported
- [ ] Both Substrait and extension temporal APIs work
- [ ] Substrait comparison aliases functional

**ADR**: `docs/adr/ADR-005-method-migration.md`

---

### Milestone 4: New Function Categories (Phase 6)

**Target**: Implement missing Substrait function categories

| Category | Methods | Files |
|----------|---------|-------|
| Rounding | ceil, floor, round, truncate | 3 backend + 1 protocol + 1 API |
| Logarithmic | ln, log, log10, log2, exp, sqrt | 3 backend + 1 protocol + 1 API |
| Set | is_in, is_not_in, index_in | 3 backend + 1 protocol |
| Aggregate | sum, count, avg, min, max, etc. | NEW NODE + 3 backend + 1 protocol + 1 API |

**Exit Criteria**:
- [ ] All new functions implemented across all backends
- [ ] Protocol definitions complete
- [ ] API namespaces expose new functions
- [ ] AggregateNode created and integrated

**ADR**: `docs/adr/ADR-006-new-functions.md`

---

### Milestone 5: Protocol & API Completion (Phases 4-5)

**Target**: Complete all protocol stubs and API exposure

| Protocol | Current | Target |
|----------|---------|--------|
| scalar_arithmetic | 7 | 12 |
| scalar_boolean | 4 | 6 |
| scalar_comparison | 4 | 12 |
| scalar_string | 30 stubs | 30 implemented |
| scalar_rounding | 0 | 4 |
| scalar_logarithmic | 0 | 5 |
| scalar_set | 0 | 2 |

**Exit Criteria**:
- [ ] All protocol methods implemented
- [ ] All API namespaces populated
- [ ] 100% coverage of declared function enums

**ADR**: `docs/adr/ADR-007-protocol-completion.md`

---

### Milestone 6: Substrait Serialization (Phase 7)

**Target**: Enable Substrait import/export

| Component | Description |
|-----------|-------------|
| SubstraitExportVisitor | Expression → substrait.Expression |
| SubstraitImportFactory | substrait.Expression → ExpressionNode |
| Function Registry | URI-based function resolution |
| Roundtrip Tests | Verify lossless serialization |

**Exit Criteria**:
- [ ] `node.to_substrait()` produces valid Substrait protobuf
- [ ] `ExpressionNode.from_substrait()` reconstructs nodes
- [ ] Roundtrip tests pass for all node types

**ADR**: `docs/adr/ADR-006-substrait-serialization.md`

---

## Phase Details

### Phase 1: Node Layer Fixes

**Duration**: 1-2 days

#### 1.1 Create SingularOrListNode

```python
# File: src/mountainash_expressions/core/expression_nodes/exn_singular_or_list.py

@dataclass
class SingularOrListNode(ExpressionNode):
    """Substrait SingularOrList - membership test (IN operator)."""
    value: ExpressionNode  # Value to test
    options: List[ExpressionNode]  # List of options

    def accept(self, visitor: ExpressionVisitor) -> Any:
        return visitor.visit_singular_or_list(self)
```

**Reference**: `_deprecated/202511/expression_nodes/BooleanCollectionExpressionNode`

#### 1.2 Fix ConditionalNode Import

```python
# File: src/mountainash_expressions/core/expression_nodes/__init__.py

# BEFORE (broken):
from .exn_conditional import ConditionalNode

# AFTER (fixed):
# ConditionalNode is actually IfThenNode - remove or alias
from .exn_ifthen import IfThenNode
ConditionalNode = IfThenNode  # Backward compatibility alias
```

#### 1.3 Add Visitor Method

```python
# File: src/mountainash_expressions/core/unified_visitor/visitor.py

def visit_singular_or_list(self, node: SingularOrListNode) -> Any:
    """Compile membership test to backend expression."""
    value = self.visit(node.value)
    options = [self.visit(opt) for opt in node.options]
    return self.backend.is_in(value, options)
```

#### 1.4 Backend Implementation

```python
# File: src/mountainash_expressions/backends/expression_systems/polars/scalar_set.py

def is_in(self, value: pl.Expr, options: List[pl.Expr]) -> pl.Expr:
    """Polars is_in implementation."""
    return value.is_in(pl.concat_list(options))
```

---

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | SingularOrList Node Implementation | PENDING |
| ADR-002 | Module Reorganization to Substrait Topology | PENDING |
| ADR-003 | Method Migration from Deprecated | PENDING |
| ADR-004 | New Function Categories | PENDING |
| ADR-005 | Protocol and API Completion | PENDING |
| ADR-006 | Substrait Serialization | PENDING |

---

## Effort Summary

| Milestone | Phases | Days |
|-----------|--------|------|
| 1. Foundation | Phase 1 | 1-2 |
| 2. Reorganization | Phase 2 | 2-3 |
| 3. Migration | Phase 3 | 3-5 |
| 4. New Functions | Phase 6 | 3-4 |
| 5. Protocol/API | Phases 4-5 | 4-6 |
| 6. Serialization | Phase 7 | 5-7 |
| **Total** | | **18-27** |

---

## Key File Paths

```
/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/

src/mountainash_expressions/
├── core/
│   ├── expression_nodes/
│   │   ├── exn_singular_or_list.py  ← CREATE
│   │   └── __init__.py              ← FIX IMPORT
│   ├── unified_visitor/
│   │   └── visitor.py               ← ADD METHOD
│   └── expression_protocols/substrait/
│       └── prtcl_scalar_*.py        ← COMPLETE
├── backends/expression_systems/
│   ├── polars/                      ← REORGANIZE
│   ├── narwhals/                    ← REORGANIZE
│   └── ibis/                        ← REORGANIZE
└── expression_api/api_namespaces/   ← COMPLETE

_deprecated/
├── 202510/                          ← REFERENCE
└── 202511/                          ← REFERENCE (most recent)

docs/
├── architecture/
│   └── SUBSTRAIT_MIGRATION.md       ← THIS DOC
└── adr/
    ├── ADR-001-singular-or-list-node.md
    ├── ADR-002-module-reorganization.md
    └── ...
```
