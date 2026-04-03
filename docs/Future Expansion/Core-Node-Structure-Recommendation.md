# Core Node Structure Recommendation

**Date:** 2025-01-09
**Status:** Architectural Recommendation
**Scope:** Core/foundational expression nodes (Source, Literal, Cast, Native, Alias)

---

## Executive Summary

Core nodes are **fundamentally different** from operation nodes. They represent universal data access and manipulation primitives rather than computed operations. This document analyzes the current structure and provides recommendations for organizing these 5 foundational nodes.

**Key Finding:** Current structure is sound, but **Alias should be added as the 5th core node** and the group should remain together in a single `core_nodes.py` file.

---

## 1. What Makes Core Nodes Different?

### Distinguishing Characteristics

| Characteristic | Core Nodes | Operation Nodes |
|---------------|------------|-----------------|
| **Purpose** | Data access & manipulation | Computation & transformation |
| **Universality** | Every backend needs these | Backend-specific availability |
| **Parameter Pattern** | Distinct shapes per node | Operator-driven within category |
| **Size** | Small (single purpose) | Variable (5-30 operators) |
| **Extensibility** | Rarely extended | Frequently extended |
| **User Frequency** | Every expression uses these | Selectively used |
| **Backend Translation** | Direct mapping | May require complex translation |

### Semantic Categories

**Core Nodes = Foundational Building Blocks**
- **Not operations:** They don't compute values
- **Primitives:** Everything else builds on these
- **Universal:** Every expression system needs them
- **Stable:** Rarely change once defined

**Operation Nodes = Computed Expressions**
- **Compute values:** Arithmetic, string, temporal operations
- **Derived:** Build on core primitives
- **Variable availability:** Backend-specific
- **Evolving:** New operations added frequently

---

## 2. Current Core Nodes (4 implemented)

### 2.1 SourceExpressionNode (Column Reference)

**Purpose:** Reference a column from the data source

**Parameters:**
```python
class SourceExpressionNode(ExpressionNode):
    def __init__(self, operator: str, value: Any):
        self.operator = operator  # "COL"
        self.value = value        # Column name (string)
```

**Usage:**
```python
col("age")  → SourceExpressionNode(operator=COL, value="age")
```

**Backend Translation:**
- Polars: `pl.col("age")`
- Narwhals: `nw.col("age")`
- Ibis: `table["age"]` or `ibis._["age"]`

**Characteristics:**
- ✅ Single purpose (column reference)
- ✅ Distinct parameter shape (column name string)
- ✅ Universal (every backend)
- ✅ Stable (won't change)

---

### 2.2 LiteralExpressionNode (Constant Value)

**Purpose:** Represent a constant literal value

**Parameters:**
```python
class LiteralExpressionNode(ExpressionNode):
    def __init__(self, operator: str, value: Any):
        self.operator = operator  # "LIT"
        self.value = value        # Literal value (int, str, bool, etc.)
```

**Usage:**
```python
lit(42)       → LiteralExpressionNode(operator=LIT, value=42)
lit("hello")  → LiteralExpressionNode(operator=LIT, value="hello")
lit(True)     → LiteralExpressionNode(operator=LIT, value=True)
```

**Backend Translation:**
- Polars: `pl.lit(42)`
- Narwhals: `nw.lit(42)`
- Ibis: `ibis.literal(42)`

**Characteristics:**
- ✅ Single purpose (literal value)
- ✅ Distinct parameter shape (any value)
- ✅ Universal (every backend)
- ✅ Stable (won't change)

**Potential Enhancement:**
```python
# Could add optional dtype parameter
lit(42, dtype=pl.Int64)  # Explicit type
```

---

### 2.3 CastExpressionNode (Type Conversion)

**Purpose:** Convert expression to different data type

**Parameters:**
```python
class CastExpressionNode(ExpressionNode):
    def __init__(self, operator: str, value: Any, type: Any, **kwargs):
        self.operator = operator  # "CAST"
        self.value = value        # Expression to cast
        self.type = type          # Target dtype
        self.kwargs = kwargs      # Backend-specific options
```

**Usage:**
```python
col("age").cast(pl.Int64)  → CastExpressionNode(
    operator=CAST,
    value=SourceExpressionNode("age"),
    type=pl.Int64
)
```

**Backend Translation:**
- Polars: `col.cast(dtype)`
- Narwhals: `col.cast(dtype)`
- Ibis: `col.cast(dtype)` or `col.astype(dtype)`

**Characteristics:**
- ✅ Single purpose (type conversion)
- ✅ Distinct parameter shape (expression + dtype)
- ✅ Universal (every backend)
- ⚠️ Questionable as "core" - could be categorized as transformation

**Phase 7 Extension:**
- Add `TRY_CAST` operator (safe casting that returns null on failure)

**Categorization Question:**
- **Core Primitive** (current) - because it's fundamental data manipulation
- **Transformation** (alternative) - because it operates on expressions
- **Recommendation:** Keep as core (it's universal and frequently used)

---

### 2.4 NativeBackendExpressionNode (Escape Hatch)

**Purpose:** Pass through native backend expressions for advanced use

**Parameters:**
```python
class NativeBackendExpressionNode(ExpressionNode):
    def __init__(self, operator: str, native_expr: Any):
        self.operator = operator  # "NATIVE"
        self.native_expr = native_expr  # Backend-specific expression object
```

**Usage:**
```python
# Advanced user who knows Polars API
native(pl.col("sales").rolling_mean(window_size=7))

# Use case: Operations not yet supported by mountainash-expressions
native(ibis_table.custom_aggregation())
```

**Backend Translation:**
- Returns native_expr directly (no translation)

**Characteristics:**
- ✅ Single purpose (escape hatch)
- ✅ Distinct parameter shape (any backend expression)
- ✅ Universal (every backend needs escape hatch)
- ✅ Stable (won't change)
- ⚠️ Power user feature (most users won't use)

**When to Use:**
- Operations not yet implemented in mountainash-expressions
- Backend-specific optimizations
- Experimental features
- Migration from native backend code

**Caveat:** Breaks cross-backend portability!

---

## 3. Missing Core Node: Alias

### 3.1 Current State

**Constants Defined:**
```python
# In constants.py
CONST_EXPRESSION_NODE_TYPES.ALIAS = "alias"
CONST_EXPRESSION_ALIAS_OPERATORS.ALIAS = auto()
```

**But No Implementation:**
- No `AliasExpressionNode` class exists
- Not in expression_nodes.py
- Not in ExpressionBuilder API

### 3.2 Why Alias is Critical

**Use Cases:**

1. **Output Column Naming:**
```python
# SQL: SELECT age * 2 AS double_age
df.select(
    col("age").mul(2).alias("double_age")
)
```

2. **Intermediate Computation Naming:**
```python
# Name complex expressions for readability
revenue = col("price").mul(col("quantity")).alias("revenue")
profit = revenue.sub(col("cost")).alias("profit")
```

3. **SQL Generation:**
```python
# Ibis requires aliases for derived columns
table.select([
    col("name"),
    col("score").add(10).alias("adjusted_score")
])
```

4. **DataFrame Compatibility:**
```python
# Polars with_columns expects named expressions
df.with_columns(
    total_sales=col("price") * col("quantity")  # Name required
)
```

### 3.3 Proposed Implementation

```python
class AliasExpressionNode(ExpressionNode):
    """
    Alias expression node - names an expression for output.

    This is a core primitive because:
    - Every backend supports aliasing
    - Required for SQL-like operations
    - Fundamental to expression output naming
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.ALIAS

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """Aliases inherit logic type from wrapped expression."""
        return self.operand.logic_type if hasattr(self.operand, 'logic_type') else CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: str, operand: ExpressionNode, alias: str):
        self.operator = operator  # "ALIAS"
        self.operand = operand    # Expression to alias
        self.alias = alias        # Output name

    def accept(self, visitor: "ExpressionVisitor") -> Any:
        return visitor.visit_alias_expression(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_alias_expression(self)
        return eval_expr
```

### 3.4 Backend Translation

**Polars:**
```python
def alias(self, operand: pl.Expr, alias_name: str) -> pl.Expr:
    return operand.alias(alias_name)
```

**Narwhals:**
```python
def alias(self, operand: nw.Expr, alias_name: str) -> nw.Expr:
    return operand.alias(alias_name)
```

**Ibis:**
```python
def alias(self, operand: ir.Expr, alias_name: str) -> ir.Expr:
    return operand.name(alias_name)
```

### 3.5 ExpressionBuilder API

```python
class ExpressionBuilder:
    def alias(self, name: str) -> "ExpressionBuilder":
        """Name this expression for output."""
        node = AliasExpressionNode(
            operator=CONST_EXPRESSION_ALIAS_OPERATORS.ALIAS,
            operand=self._node,
            alias=name
        )
        return ExpressionBuilder(node)

# Usage
col("age").mul(2).alias("double_age")
```

### 3.6 Visitor Mixin

**New Mixin:**
```python
# In common_mixins/alias_visitor_mixin.py
class AliasExpressionVisitor(ExpressionVisitor):
    """Visitor mixin for alias expressions."""

    @abstractmethod
    def _alias(self, operand: Any, alias_name: str) -> Any:
        """Alias an expression with a name."""
        pass

    def visit_alias_expression(self, node: AliasExpressionNode) -> Any:
        """Visit alias expression node."""
        operand_expr = self._process_operand(node.operand)
        return self._alias(operand_expr, node.alias)
```

**Add to UniversalBooleanVisitor:**
```python
class UniversalBooleanExpressionVisitor(
    # ... existing mixins ...
    AliasExpressionVisitor,  # NEW
    # ... other mixins ...
):
    def _alias(self, operand: Any, alias_name: str) -> Any:
        """Implement alias using backend."""
        return self.backend.alias(operand, alias_name)
```

### 3.7 Recommendation

✅ **Add Alias as the 5th core node**

**Rationale:**
1. Universal across all backends
2. Critical for SQL-like operations
3. Required for DataFrame operations (with_columns, select)
4. Simple, single-purpose primitive
5. Infrastructure already exists (constants defined)
6. Missing functionality users will need

**Priority:** HIGH (should be added before Phase 1)

**Effort:** 1-2 days
- Implement AliasExpressionNode
- Add visitor mixin
- Implement in all 3 backends
- Add ExpressionBuilder method
- Write tests

---

## 4. Core Node Organization

### 4.1 Current File Structure

```
core/expression_nodes/
├── __init__.py
├── expression_nodes.py        # All base nodes (14 classes, 500+ lines)
└── boolean_expression_nodes.py  # Boolean variants
```

**Issues:**
- ❌ Core nodes (4 types) mixed with operation nodes (10 types) in single file
- ❌ File size: 500+ lines, will grow to 800+ by Phase 9
- ❌ Difficult to find specific node types

### 4.2 Proposed File Structure

```
core/expression_nodes/
├── __init__.py                    # Export all node types
│
├── base_nodes.py                  # ExpressionNode base class only
│
├── core_nodes.py                  # NEW: 5 core nodes together
│   ├── SourceExpressionNode
│   ├── LiteralExpressionNode
│   ├── CastExpressionNode
│   ├── NativeBackendExpressionNode
│   └── AliasExpressionNode       # NEW
│
├── logical_nodes.py               # Logical operation nodes
│   ├── LogicalConstantExpressionNode
│   ├── UnaryExpressionNode
│   ├── LogicalExpressionNode
│   ├── ComparisonExpressionNode
│   └── CollectionExpressionNode
│
├── arithmetic_nodes.py            # Arithmetic + Math nodes
│   ├── ArithmeticExpressionNode
│   └── MathExpressionNode        # Phase 1
│
├── string_nodes.py                # String + Pattern nodes
│   ├── StringExpressionNode
│   └── PatternExpressionNode
│
├── temporal/                      # Temporal nodes (Phase 4 split)
│   ├── extract_nodes.py
│   ├── arithmetic_nodes.py
│   └── construction_nodes.py
│
├── conditional_nodes.py           # ConditionalIfElseExpressionNode
│
├── array_nodes.py                 # ArrayExpressionNode (Phase 6)
│
├── bitwise_nodes.py               # BitwiseExpressionNode (Phase 7)
│
├── window/                        # Window infrastructure (Phase 8)
│   ├── specification.py
│   └── window_nodes.py
│
├── metrics/                       # ML metrics (Phase 9)
│   ├── classification_nodes.py
│   ├── ranking_nodes.py
│   └── credit_risk_nodes.py
│
└── boolean_expression_nodes.py    # Boolean variants
```

### 4.3 Core Nodes File Details

**File:** `core/expression_nodes/core_nodes.py`

**Contents:**
- 5 node classes: Source, Literal, Cast, Native, Alias
- ~200-250 lines total (50 lines per node average)
- Clear docstrings for each
- Imports from base_nodes.py

**Rationale:**
1. **Cohesive grouping** - All foundational primitives together
2. **Small file** - 200-250 lines is very manageable
3. **Easy to find** - Core nodes logically grouped
4. **Semantic clarity** - File name indicates universal primitives
5. **Stable** - These rarely change, won't grow significantly

---

## 5. Parameter Shape Analysis

### Comparison: Core vs Operation Nodes

| Node Type | Parameter Pattern | Shape | Operator-Driven? |
|-----------|------------------|-------|------------------|
| **CORE NODES** |
| Source | `(operator, value: str)` | Column name | ❌ No (single operator COL) |
| Literal | `(operator, value: Any)` | Any value | ❌ No (single operator LIT) |
| Cast | `(operator, value: Expr, type: dtype)` | Expr + dtype | ❌ No (single operator CAST) |
| Native | `(operator, native_expr: Any)` | Backend expr | ❌ No (single operator NATIVE) |
| Alias | `(operator, operand: Expr, alias: str)` | Expr + name | ❌ No (single operator ALIAS) |
| **OPERATION NODES** |
| Arithmetic | `(operator, left: Expr, right: Expr)` | Binary | ✅ Yes (7 operators) |
| String | `(operator, operand: Expr, *args, **kwargs)` | Variadic | ✅ Yes (12 operators) |
| Temporal | `(operator, operand: Expr, *args, **kwargs)` | Variadic | ✅ Yes (23 operators) |
| Conditional | `(operator, condition, consequence, alternative)` | Ternary | ✅ Yes (3 operators) |

**Key Insight:** Core nodes have **distinct, unique parameter shapes** per node. Operation nodes use **operator dispatch within shared parameter patterns**.

### Why This Matters

**Core Nodes:**
- Each node has unique semantics
- Parameters reflect those unique semantics
- Not operator-driven (single operator each)
- Parameter shape IS the interface

**Operation Nodes:**
- Multiple operations share semantics (e.g., all arithmetic is binary)
- Parameters are consistent within category
- Operator-driven (multiple operators per node type)
- Operator enum EXTENDS the interface

**Implication:** Core nodes should NOT be combined into a single operator-driven node.

---

## 6. Categorization Question: Core vs Transformation

### Should Cast/Alias Be Separate?

**Option A: All 5 Together (Recommended)**
```
core_nodes.py
├── SourceExpressionNode       # Data access
├── LiteralExpressionNode       # Data access
├── NativeBackendExpressionNode # Data access
├── CastExpressionNode          # Transformation
└── AliasExpressionNode         # Transformation
```

**Option B: Split Access vs Transformation**
```
access_nodes.py
├── SourceExpressionNode
├── LiteralExpressionNode
└── NativeBackendExpressionNode

transformation_nodes.py
├── CastExpressionNode
└── AliasExpressionNode
```

### Analysis

**Argument for Split:**
- Semantic distinction (access vs transform)
- Cast/Alias operate on expressions (not primitives)
- Clear categorization

**Argument for Together:**
- All 5 are universal primitives
- All 5 are single-purpose (not operator-driven)
- All 5 are stable (rarely change)
- All 5 are foundational (everything builds on these)
- File size: 200-250 lines (very manageable)

**Recommendation:** **Keep all 5 together in `core_nodes.py`**

**Rationale:**
1. **Foundational cohesion** trumps semantic distinction
2. **Single file is small** (200-250 lines)
3. **Easy to find** - one place for all core primitives
4. **User mental model** - "these are the building blocks"
5. **No practical benefit** to splitting into 2 files

---

## 7. Universal Nature of Core Nodes

### Backend Requirements

**All backends MUST implement:**
- ✅ col() - column reference
- ✅ lit() - literal value
- ✅ cast() - type conversion
- ✅ native() - escape hatch (passthrough)
- ✅ alias() - output naming

**Backend Capability Matrix:**

| Node | Polars | Narwhals | Ibis | Pandas | SQLite | Required |
|------|--------|----------|------|--------|--------|----------|
| Source | ✅ | ✅ | ✅ | ✅ | ✅ | YES |
| Literal | ✅ | ✅ | ✅ | ✅ | ✅ | YES |
| Cast | ✅ | ✅ | ✅ | ✅ | ✅ | YES |
| Native | ✅ | ✅ | ✅ | ✅ | ✅ | YES |
| Alias | ✅ | ✅ | ✅ | ✅ | ✅ | YES |

**Contrast with Operation Nodes:**

| Node | Polars | Narwhals | Ibis | Pandas | SQLite | Required |
|------|--------|----------|------|--------|--------|----------|
| Array | ✅ | ✅ | ⚠️ | ⚠️ | ❌ | NO |
| Window | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | NO |
| Bitwise | ✅ | ✅ | ✅ | ✅ | ⚠️ | NO |
| Temporal (advanced) | ✅ | ✅ | ⚠️ | ⚠️ | ❌ | NO |

**Universality:** Core nodes work on ALL backends. Operation nodes may not.

---

## 8. Visitor Alignment for Core Nodes

### Current Visitor Mixins

| Core Node | Visitor Mixin | Visit Method | Backend Method |
|-----------|---------------|--------------|----------------|
| Source | SourceExpressionVisitor | visit_source_expression() | col() |
| Literal | LiteralExpressionVisitor | visit_literal_expression() | lit() |
| Cast | CastExpressionVisitor | visit_cast_expression() | cast() |
| Native | NativeExpressionVisitor | visit_native_expression() | (passthrough) |
| Alias | **MISSING** | **MISSING** | **MISSING** |

### Proposed Addition

**New Visitor Mixin:**
```python
# common_mixins/alias_visitor_mixin.py
class AliasExpressionVisitor(ExpressionVisitor):
    @abstractmethod
    def _alias(self, operand: Any, alias_name: str) -> Any:
        pass

    def visit_alias_expression(self, node: AliasExpressionNode) -> Any:
        operand_expr = self._process_operand(node.operand)
        return self._alias(operand_expr, alias_name=node.alias)
```

**Backend Implementation:**
```python
# CoreBackend protocol (from protocol refactoring)
class CoreBackend(Protocol):
    def col(self, name: str) -> Any: ...
    def lit(self, value: Any) -> Any: ...
    def alias(self, operand: Any, alias_name: str) -> Any: ...  # NEW

# Polars implementation
class PolarsCoreMixin:
    def col(self, name: str) -> pl.Expr:
        return pl.col(name)

    def lit(self, value: Any) -> pl.Expr:
        return pl.lit(value)

    def alias(self, operand: pl.Expr, alias_name: str) -> pl.Expr:  # NEW
        return operand.alias(alias_name)
```

### Backend Protocol Alignment

**After adding Alias, CoreBackend protocol will have:**
1. col() - column reference
2. lit() - literal value
3. alias() - expression naming

**Note:** Cast and Native are separate protocols (type operations, escape hatch).

---

## 9. Recommendations Summary

### 9.1 File Organization

✅ **Recommendation:** Create `core/expression_nodes/core_nodes.py`

**Contents:**
- SourceExpressionNode
- LiteralExpressionNode
- CastExpressionNode
- NativeBackendExpressionNode
- AliasExpressionNode (NEW)

**Size:** ~200-250 lines (manageable, stable)

**Benefits:**
- Cohesive grouping of universal primitives
- Small, focused file
- Easy to find core nodes
- Clear semantic meaning

---

### 9.2 Add Alias Node

✅ **Recommendation:** Implement AliasExpressionNode

**Priority:** HIGH (before Phase 1)

**Effort:** 1-2 days

**Tasks:**
1. Implement AliasExpressionNode class
2. Add AliasExpressionVisitor mixin
3. Implement in all backends (Polars, Narwhals, Ibis)
4. Add .alias() method to ExpressionBuilder
5. Write tests (cross-backend parametrized)
6. Update documentation

**Benefits:**
- Completes core primitive set
- Enables SQL-like column naming
- Required for DataFrame operations
- User-requested functionality

---

### 9.3 Keep Core Nodes Together

✅ **Recommendation:** Do NOT split into access/transformation files

**Rationale:**
- All 5 are foundational primitives
- All 5 are universal (every backend)
- All 5 are stable (rarely change)
- Small file size (200-250 lines)
- Cohesive grouping

---

### 9.4 Design Principles for Core Nodes

**Codify these principles:**

1. **Single Purpose** - Each core node has exactly one responsibility
2. **Universal** - Must work on all backends
3. **Distinct Parameters** - Each node has unique parameter shape
4. **Not Operator-Driven** - Single operator per node (no operator dispatch)
5. **Stable** - Rarely extended or modified
6. **Foundational** - Everything builds on these
7. **Small** - Implementation typically < 50 lines per node

---

### 9.5 Distinguish from Operation Nodes

**Core Nodes:**
- Data access and manipulation primitives
- Universal (all backends)
- Stable (rarely change)
- Distinct parameter shapes
- Small (single purpose)

**Operation Nodes:**
- Computed expressions
- Variable backend support
- Frequently extended
- Operator-driven within categories
- Larger (5-30 operators)

---

## 10. Implementation Checklist

### Phase 0: Add Alias Node (1-2 days, before Phase 1)

**Node Implementation:**
- [ ] Create AliasExpressionNode in expression_nodes.py
- [ ] Define accept() and eval() methods
- [ ] Add to __init__.py exports

**Visitor Implementation:**
- [ ] Create alias_visitor_mixin.py in common_mixins/
- [ ] Define AliasExpressionVisitor class
- [ ] Add visit_alias_expression() method
- [ ] Add _alias() abstract method
- [ ] Add to UniversalBooleanVisitor mixin list

**Backend Implementation:**
- [ ] Add alias() method to PolarsCoreMixin
- [ ] Add alias() method to NarwhalsCoreMixin
- [ ] Add alias() method to IbisCoreMixin
- [ ] Update CoreBackend protocol (if refactoring done)

**ExpressionBuilder API:**
- [ ] Add .alias(name: str) method to ExpressionBuilder
- [ ] Update docstrings

**Tests:**
- [ ] Create test_alias.py in cross_backend/
- [ ] Test parametrized across all backends
- [ ] Test with complex expressions
- [ ] Test with chaining

**Documentation:**
- [ ] Update CLAUDE.md with alias node
- [ ] Update alignment matrix
- [ ] Add to public API documentation

---

### Phase 0.5: Reorganize Core Nodes (0.5-1 day, optional)

**File Reorganization:**
- [ ] Create core/expression_nodes/core_nodes.py
- [ ] Move 5 core nodes to new file
- [ ] Update imports in __init__.py
- [ ] Update all references
- [ ] Run full test suite (ensure no breaks)

**Documentation:**
- [ ] Update file organization in CLAUDE.md
- [ ] Update architecture documentation

---

## 11. Conclusion

Core nodes are the **foundational primitives** of the expression system. They should:

1. **Stay together** in a single `core_nodes.py` file (5 nodes, ~200-250 lines)
2. **Include Alias** as the 5th core node (currently missing, should be added)
3. **Remain distinct** from operation nodes (different categorization, different patterns)
4. **Be universal** (work on all backends, required functionality)
5. **Stay stable** (rarely extended, well-defined interfaces)

**Priority Actions:**
1. ✅ **Add Alias node** (HIGH priority, 1-2 days)
2. ✅ **Keep 5 core nodes together** (don't split)
3. ✅ **Optional reorganization** into core_nodes.py (quality of life)

The current structure is fundamentally sound. Adding Alias completes the core primitive set and provides critical functionality users need.

---

**Document Complete** ✅
