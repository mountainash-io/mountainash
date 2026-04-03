# Constants.py Enum Alignment - Executive Summary

## Quick Overview

The enums in `constants.py` serve as the **single source of truth** for operation definitions, but there's a **significant gap** between what's defined in enums and what's abstracted in the `ExpressionSystem` interface.

### Coverage at a Glance

```
Node Types:           12/13 implemented (92%) ✅
├─ MISSING: ALIAS
└─ Status: Mostly complete

Operator Definitions: 78 enum values defined
├─ In ExpressionSystem: 18 methods (23%)
├─ In Visitor Mixins: 50 operations (64%)
└─ Status: CRITICAL GAP

Implementation Path: Enum → Node → Visitor → Backend Methods
└─ Problem: Last step (Backend Methods) missing for many operations
```

---

## The Architecture Flow

```
User Code
    ↓
ExpressionBuilder creates AST node
    ↓
Node.accept(visitor) dispatches to mixin
    ↓
Visitor mixin uses enum as dispatch key
    ↓
Abstract visitor method (_B_eq, _add, etc.)
    ↓
Concrete implementation in UniversalBooleanExpressionVisitor
    ↓
Calls self.backend.* method from ExpressionSystem
    ↓
Backend-native expression (pl.Expr, nw.Expr, ir.Expr, etc.)
```

**The Gap:** Step 5 works for ~23% of operations. The remaining 77% are implemented at the visitor level without backend abstraction.

---

## Critical Gaps (Highest Priority)

### 1. Missing Arithmetic Methods in ExpressionSystem
**Impact:** DIVIDE, POWER, FLOOR_DIVIDE operators defined but no backend abstraction

```
Enum Defined:    CONST_EXPRESSION_ARITHMETIC_OPERATORS
├─ ADD ✅         → backend.add()
├─ SUBTRACT ✅    → backend.sub()
├─ MULTIPLY ✅    → backend.mul()
├─ DIVIDE ❌      → NO BACKEND METHOD (only visitor)
├─ MODULO ✅      → backend.mod()
├─ POWER ❌       → NO BACKEND METHOD (only visitor)
└─ FLOOR_DIVIDE ❌ → NO BACKEND METHOD (only visitor)

Visitor Methods:   _divide(), _power(), _floor_divide() ✅
Backend Methods:   div(), pow(), floor_div() ❌ MISSING
```

**Recommendation:** Add div(), pow(), floor_div() to ExpressionSystem base class and all backends.

### 2. String Operations - No Backend Abstraction at All
**Impact:** 12 operators defined but entirely at visitor level

```
Enum Defined:       CONST_EXPRESSION_STRING_OPERATORS (12 operators)
├─ UPPER, LOWER, TRIM, LTRIM, RTRIM
├─ SUBSTRING, CONCAT, LENGTH
├─ REPLACE, CONTAINS, STARTS_WITH, ENDS_WITH
│
Visitor Methods:    StringOperatorsExpressionVisitor ✅
Backend Methods:    ❌ NONE in ExpressionSystem
```

**Recommendation:** Create StringOperationsProtocol in ExpressionSystem with all 12 methods.

### 3. Temporal Operations - No Backend Abstraction at All
**Impact:** 22 operators defined entirely at visitor level (most complex)

```
Enum Defined:       CONST_EXPRESSION_TEMPORAL_OPERATORS (22 operators)
├─ Extraction: YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEKDAY, WEEK, QUARTER
├─ Addition: ADD_DAYS, ADD_HOURS, ADD_MINUTES, ADD_SECONDS, ADD_MONTHS, ADD_YEARS
├─ Difference: DIFF_DAYS, DIFF_HOURS, DIFF_MINUTES, DIFF_SECONDS, DIFF_MONTHS, DIFF_YEARS
├─ Other: TRUNCATE, OFFSET_BY
│
Visitor Methods:    TemporalOperatorsExpressionVisitor ✅
Backend Methods:    ❌ NONE in ExpressionSystem
```

**Recommendation:** Create TemporalOperationsProtocol in ExpressionSystem with all 22 methods.

### 4. Other Visitor-Only Operations
- **Pattern:** 4 operators (LIKE, REGEX_MATCH, REGEX_CONTAINS, REGEX_REPLACE)
- **Conditional:** 3 operators (WHEN, COALESCE, FILL_NULL)
- **Unary/Constants:** 9 operators (IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN, etc.)

**Recommendation:** Create corresponding protocols in ExpressionSystem.

### 5. Missing Enum → Implementation Mappings
- **XOR_EXCLUSIVE, XOR_PARITY:** Defined in enum but no visitor or backend implementation
- **ALIAS:** Node type enum defined but no node class or backend method
- **NOT_IN:** Enum defined, visitor implemented, but no backend method
- **IS_NOT_NULL:** Should exist in SOURCE_OPERATORS but missing from both enum and backend

---

## Detailed Coverage by Category

| Category | Enum Count | Backend Methods | Visitor | Coverage | Priority |
|----------|---|---|---|---|---|
| Comparison | 6 | 6 ✅ | ✅ | 100% | Complete |
| Type/Cast | 1 | 1 ✅ | ✅ | 100% | Complete |
| Core (col, lit) | 2 | 2 ✅ | ✅ | 100% | Complete |
| Logical (AND, OR, NOT) | 3 | 3 ✅ | ✅ | 100% | Complete |
| Arithmetic (basic) | 4 | 4 ✅ | ✅ | 100% | Complete |
| **Arithmetic (advanced)** | 3 | 0 ❌ | ✅ | 0% | **P1** |
| **String** | 12 | 0 ❌ | ✅ | 0% | **P1** |
| **Temporal** | 22 | 0 ❌ | ✅ | 0% | **P1** |
| **Pattern** | 4 | 0 ❌ | ✅ | 0% | **P2** |
| **Conditional** | 3 | 0 ❌ | ✅ | 0% | **P2** |
| **Unary** | 6 | 0 ❌ | ✅ | 0% | **P2** |
| **Constants** | 3 | 0 ❌ | ✅ | 0% | **P2** |
| Collection (IN) | 1 | 1 ✅ | ✅ | 100% | Complete |
| **Collection (NOT_IN)** | 1 | 0 ❌ | ✅ | 0% | **P2** |
| **Unimplemented** | 2 | 0 ❌ | ❌ | 0% | **P3** |
| **TOTAL** | **78** | **18** | **50** | **23%** | |

---

## Why This Matters

### Current Problem
- **78 operations defined in enums**
- **Only 18 abstracted to ExpressionSystem level** (23%)
- **50 implemented at visitor level only** (64%)
- **2 completely unimplemented** (XOR, ALIAS)

### Consequences
1. **Hard to add new backends** - Must implement 50+ visitor methods instead of just 50 backend methods
2. **Inconsistent architecture** - Some ops have backend abstraction, most don't
3. **Type safety issues** - Can't use protocols/ABCs to enforce backend contracts
4. **Documentation fragmented** - Enum docstrings, visitor docstrings, backend docstrings don't align
5. **Testing harder** - Backend implementations can't be validated against a unified protocol

### The Fix
Extend ExpressionSystem to include ALL 78 operations. Then:
- Backend implementations become straightforward (implement protocol)
- Visitor layer becomes a thin dispatch layer
- New backends get clear requirements
- Full type safety across all layers

---

## Enum Structure Overview

### Node Type Enums (What kind of expression?)
```
CONST_EXPRESSION_NODE_TYPES
├─ NATIVE           → NativeBackendExpressionNode ✅
├─ SOURCE           → SourceExpressionNode ✅
├─ LITERAL          → LiteralExpressionNode ✅
├─ CAST             → CastExpressionNode ✅
├─ ALIAS            → (node class missing) ❌
├─ LOGICAL          → LogicalExpressionNode ✅
├─ LOGICAL_COMPARISON → ComparisonExpressionNode ✅
├─ LOGICAL_UNARY    → UnaryExpressionNode ✅
├─ LOGICAL_CONSTANT → LogicalConstantExpressionNode ✅
├─ COLLECTION       → CollectionExpressionNode ✅
├─ ARITHMETIC       → ArithmeticExpressionNode ✅
├─ STRING           → StringExpressionNode ✅
├─ PATTERN          → PatternExpressionNode ✅
├─ CONDITIONAL_IF_ELSE → ConditionalIfElseExpressionNode ✅
└─ TEMPORAL         → TemporalExpressionNode ✅
```

### Operator Enums (What operation specifically?)
```
CONST_EXPRESSION_COMPARISON_OPERATORS     → 6 ops → 6 backend methods ✅
CONST_EXPRESSION_LOGICAL_OPERATORS        → 5 ops → 3 backend methods ⚠️
CONST_EXPRESSION_ARITHMETIC_OPERATORS     → 7 ops → 4 backend methods ⚠️
CONST_EXPRESSION_STRING_OPERATORS         → 12 ops → 0 backend methods ❌
CONST_EXPRESSION_PATTERN_OPERATORS        → 4 ops → 0 backend methods ❌
CONST_EXPRESSION_TEMPORAL_OPERATORS       → 22 ops → 0 backend methods ❌
CONST_EXPRESSION_CONDITIONAL_OPERATORS    → 3 ops → 0 backend methods ❌
CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS  → 6 ops → 0 backend methods ❌
CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS → 3 ops → 0 backend methods ❌
CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS → 2 ops → 1 backend method ⚠️
CONST_EXPRESSION_SOURCE_OPERATORS         → 3 ops → 2 backend methods ⚠️
CONST_EXPRESSION_CAST_OPERATORS           → 1 op  → 1 backend method ✅
CONST_EXPRESSION_LITERAL_OPERATORS        → 1 op  → 1 backend method ✅
```

---

## Visitor Method Naming Convention

Visitor mixins use these naming patterns (should be standardized):

```
Comparison:  _B_eq(), _B_ne(), _B_gt(), _B_lt(), _B_ge(), _B_le()
Arithmetic:  _add(), _subtract(), _multiply(), _divide(), _modulo(), _power()
Logical:     _and(), _or(), _not()
String:      _upper(), _lower(), _trim(), _substring(), _concat(), _length(), etc.
Pattern:     _like(), _regex_match(), _regex_contains(), _regex_replace()
Temporal:    _year(), _month(), _day(), _hour(), _add_days(), _diff_days(), etc.
Conditional: _when(), _coalesce(), _fill_null()
Unary:       _is_true(), _is_false(), _is_unknown()
Constants:   _always_true(), _always_false()
```

**Inconsistency:** Boolean operations use _B_* prefix, others use _* prefix. Should standardize.

---

## Recommended Action Plan

### Phase 1: Quick Wins (1-2 days)
1. Add div(), pow(), floor_div() to ExpressionSystem
2. Update 3 backends to implement these
3. Add is_not_in() to ExpressionSystem
4. Remove XOR_EXCLUSIVE, XOR_PARITY from enum (or implement)
5. Resolve ALIAS (implement or remove)

### Phase 2: String/Pattern/Conditional (3-5 days)
1. Create StringOperationsProtocol in ExpressionSystem
2. Create PatternOperationsProtocol in ExpressionSystem
3. Create ConditionalOperationsProtocol in ExpressionSystem
4. Implement in all 3 backends
5. Visitor becomes thin dispatch layer

### Phase 3: Temporal Operations (2-3 days)
1. Create TemporalOperationsProtocol in ExpressionSystem
2. Implement in all 3 backends
3. Visitor becomes thin dispatch layer

### Phase 4: Unary/Constants/Remaining (1-2 days)
1. Create UnaryOperationsProtocol
2. Create ConstantOperationsProtocol
3. Implement in all backends

### Phase 5: Testing & Documentation (1-2 days)
1. Add protocol-based tests
2. Update architecture documentation
3. Create backend implementation guide

---

## Key Files

- **Enums:** `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/constants.py`
- **ExpressionSystem Base:** `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_system/base.py`
- **Backend Implementations:** `src/mountainash_expressions/backends/{polars,narwhals,ibis}/expression_system/`
- **Visitor Mixins:** `src/mountainash_expressions/core/expression_visitors/{boolean,arithmetic,string,pattern,temporal,conditional}_mixins/`
- **Detailed Analysis:** `docs/ENUM_ALIGNMENT_ANALYSIS.md`

---

## Bottom Line

**The enums are well-designed.** The problem is the implementation is incomplete - about 50 operations defined in enums are implemented at the visitor layer without backend abstraction. This creates architectural inconsistency but doesn't break functionality.

**To align the system:** Promote visitor-level operations to ExpressionSystem level. This requires implementing the operation in each backend but creates a cleaner, more maintainable architecture.

**Effort:** ~2-3 weeks for a complete overhaul, but could be phased in gradually.
