# Enum Alignment - Quick Reference

## Single Page Overview

### What Are The Enums?

The enums in `constants.py` define the **complete catalog** of what operations the system supports:

```python
CONST_EXPRESSION_NODE_TYPES          # What KIND of expression? (13 types)
CONST_EXPRESSION_*_OPERATORS         # What OPERATION specifically? (78 total)
```

### Where Do They Go?

```
Enum Value
    ↓
   [Node Class]           # e.g., ComparisonExpressionNode
    ↓
   [Visitor Mixin]        # e.g., BooleanComparisonExpressionVisitor
    ↓
   [Abstract Method]      # e.g., _B_eq() { pass }
    ↓
   [Concrete Impl]        # e.g., def _B_eq(left, right): ...
    ↓
   [Backend Method]       # e.g., backend.eq(left, right)
    ↓
[Backend-Native Expr]     # e.g., pl.Expr | nw.Expr | ir.Expr
```

### The Problem

**Gap at last step:** Backend methods missing for ~77% of operations

```
      Defined in Enum    Visitor Impl    Backend Method
ADD   ✅                 ✅              ✅
SUB   ✅                 ✅              ✅
DIV   ✅                 ✅              ❌ MISSING
UPPER ✅                 ✅              ❌ MISSING
YEAR  ✅                 ✅              ❌ MISSING
WHEN  ✅                 ✅              ❌ MISSING
```

---

## Alignment Status Matrix

### Perfect Alignment (100%)
| Operation | Enum | Node | Visitor | Backend | Example |
|-----------|------|------|---------|---------|---------|
| EQ | ✅ | ✅ | ✅ | ✅ | col("x").eq(5) |
| NE | ✅ | ✅ | ✅ | ✅ | col("x").ne(5) |
| GT | ✅ | ✅ | ✅ | ✅ | col("x").gt(5) |
| LT | ✅ | ✅ | ✅ | ✅ | col("x").lt(5) |
| GE | ✅ | ✅ | ✅ | ✅ | col("x").ge(5) |
| LE | ✅ | ✅ | ✅ | ✅ | col("x").le(5) |
| AND | ✅ | ✅ | ✅ | ✅ | expr1.and_(expr2) |
| OR | ✅ | ✅ | ✅ | ✅ | expr1.or_(expr2) |
| NOT | ✅ | ✅ | ✅ | ✅ | expr.not_() |
| ADD | ✅ | ✅ | ✅ | ✅ | col("x").add(5) |
| SUB | ✅ | ✅ | ✅ | ✅ | col("x").sub(5) |
| MUL | ✅ | ✅ | ✅ | ✅ | col("x").mul(5) |
| MOD | ✅ | ✅ | ✅ | ✅ | col("x").mod(5) |
| IN | ✅ | ✅ | ✅ | ✅ | col("x").is_in([1,2,3]) |
| CAST | ✅ | ✅ | ✅ | ✅ | col("x").cast("int") |
| LIT | ✅ | ✅ | ✅ | ✅ | lit(42) |
| COL | ✅ | ✅ | ✅ | ✅ | col("x") |

### Partial Alignment
| Operation | Enum | Node | Visitor | Backend | Issue |
|-----------|------|------|---------|---------|-------|
| NOT_IN | ✅ | ✅ | ✅ | ❌ | Backend method missing |
| XOR | ✅ | ✅ | ❌ | ❌ | Visitor & backend missing |
| DIV | ✅ | ✅ | ✅ | ❌ | Backend method missing |
| POW | ✅ | ✅ | ✅ | ❌ | Backend method missing |
| FLOOR_DIV | ✅ | ✅ | ✅ | ❌ | Backend method missing |

### Missing Alignment
| Operation | Enum | Node | Visitor | Backend | Example |
|-----------|------|------|---------|---------|---------|
| UPPER | ✅ | ✅ | ✅ | ❌ | col("x").upper() |
| LOWER | ✅ | ✅ | ✅ | ❌ | col("x").lower() |
| TRIM | ✅ | ✅ | ✅ | ❌ | col("x").trim() |
| SUBSTRING | ✅ | ✅ | ✅ | ❌ | col("x").substring(0, 5) |
| ... (8 more) | ✅ | ✅ | ✅ | ❌ | String ops missing backend |
| YEAR | ✅ | ✅ | ✅ | ❌ | col("date").year() |
| MONTH | ✅ | ✅ | ✅ | ❌ | col("date").month() |
| ... (20 more) | ✅ | ✅ | ✅ | ❌ | Temporal ops missing backend |
| LIKE | ✅ | ✅ | ✅ | ❌ | col("x").like("%pattern%") |
| REGEX | ✅ | ✅ | ✅ | ❌ | col("x").regex_match(".*") |
| WHEN | ✅ | ✅ | ✅ | ❌ | when(...).then(...) |
| COALESCE | ✅ | ✅ | ✅ | ❌ | coalesce(col1, col2) |
| IS_TRUE | ✅ | ✅ | ✅ | ❌ | col("bool").is_true() |

### No Alignment
| Operation | Enum | Node | Visitor | Backend | Issue |
|-----------|------|------|---------|---------|-------|
| ALIAS | ✅ | ❌ | ❌ | ❌ | Nothing implemented |
| XOR_EXCL | ✅ | ✅ | ❌ | ❌ | Visitor & backend missing |
| XOR_PAR | ✅ | ✅ | ❌ | ❌ | Visitor & backend missing |

---

## Coverage Breakdown

### By Implementation Layer

```
Backend Methods Present:
├─ Comparison: 6/6 ✅
├─ Logical: 3/5 (missing XOR variants)
├─ Arithmetic: 4/7 (missing div, pow, floor_div)
├─ Collection: 1/2 (missing is_not_in)
├─ Null checks: 1/2 (missing is_not_null)
├─ String: 0/12 ❌
├─ Pattern: 0/4 ❌
├─ Temporal: 0/22 ❌
├─ Conditional: 0/3 ❌
├─ Unary: 0/6 ❌
└─ Constants: 0/3 ❌
    Total: 18/78 (23%)
```

### By Usage Pattern

```
Fully Supported (use freely):
  col(), lit(), cast()                    # Core
  eq, ne, gt, lt, ge, le                  # Comparison
  and_, or_, not_                         # Boolean logic
  add, sub, mul, mod                      # Arithmetic
  is_in()                                 # Collection
  
Partially Supported (may have limitations):
  div, pow, floor_div                     # Arithmetic (missing backend abstraction)
  is_not_in()                             # Collection (missing backend abstraction)
  
Visitor-Only (works but not optimized):
  .upper(), .lower(), .trim()             # String ops
  .year(), .month(), .day()               # Temporal ops
  .like(), .regex_match()                 # Pattern ops
  .when().then()                          # Conditional ops
  .is_true(), .is_false()                 # Unary ops
  
Not Implemented:
  .alias()                                # Aliasing
  XOR operations                          # Boolean XOR
```

---

## How to Use This Information

### For Backend Developers
**If adding a new backend, implement these REQUIRED methods:**

```python
class MyBackendExpressionSystem(ExpressionSystem):
    # Required: All comparison operations
    def eq(self, left, right): ...
    def ne(self, left, right): ...
    def gt(self, left, right): ...
    def lt(self, left, right): ...
    def ge(self, left, right): ...
    def le(self, left, right): ...
    
    # Required: All logical operations
    def and_(self, left, right): ...
    def or_(self, left, right): ...
    def not_(self, expr): ...
    
    # Required: Basic arithmetic
    def add(self, left, right): ...
    def sub(self, left, right): ...
    def mul(self, left, right): ...
    def mod(self, left, right): ...
    
    # Required: Core primitives
    def col(self, name): ...
    def lit(self, value): ...
    def cast(self, expr, dtype): ...
    
    # Required: Collections
    def is_in(self, expr, collection): ...
    
    # Required: Null checks
    def is_null(self, expr): ...
    
    # OPTIONAL (visitor will handle): String, Pattern, Temporal, Conditional, Unary
    # But recommended for better performance!
```

### For Architecture Decisions
**Current situation:** The system works with visitor-only implementation, but adds overhead.

**Best practice:** Implement all 78 operations in ExpressionSystem for optimal performance and consistency.

---

## Metrics at a Glance

| Metric | Value |
|--------|-------|
| Total Operations Defined | 78 |
| Node Types Implemented | 12/13 (92%) |
| Backend Methods | 18 |
| Backend Abstraction Coverage | 23% |
| Visitor Implementation Coverage | 100% |
| Systems Working | 100% (visitor layer falls back) |
| Architecture Quality | 70% (gaps but functional) |

---

## Files to Reference

```
constants.py           - ALL enums defined here
expression_nodes.py    - Node class implementations
universal_visitor.py   - Main visitor (776 lines)
*_expression_visitor_mixin.py - Visitor dispatch logic
*_expression_system.py - Backend implementations
```

---

## Quick Decision Tree

**Should I implement an operation?**

```
Is it defined in an enum in constants.py?
  ├─ YES: Have a Node class?
  │ ├─ NO: Create node class first
  │ └─ YES: Have visitor methods?
  │   ├─ NO: Create visitor mixin
  │   └─ YES: Have backend methods?
  │     ├─ NO: Add to ExpressionSystem base + all backends
  │     └─ YES: Done! ✅
  │
  └─ NO: Don't implement! Add enum first.
```

---

## The Ask

To fully align enums with implementation:

1. **Add 3 arithmetic methods:** div(), pow(), floor_div()
2. **Add 1 collection method:** is_not_in()
3. **Add 12 string methods:** upper, lower, trim, ltrim, rtrim, substring, concat, length, replace, contains, starts_with, ends_with
4. **Add 4 pattern methods:** like, regex_match, regex_contains, regex_replace
5. **Add 22 temporal methods:** year, month, day, hour, minute, second, weekday, week, quarter, add_days, add_hours, add_minutes, add_seconds, add_months, add_years, diff_days, diff_hours, diff_minutes, diff_seconds, diff_months, diff_years, truncate, offset_by
6. **Add 3 conditional methods:** when, coalesce, fill_null
7. **Add 6 unary methods:** is_true, is_false, is_unknown, is_known, maybe_true, maybe_false
8. **Add 3 constant methods:** always_true, always_false, always_unknown
9. **Remove/implement:** XOR_EXCLUSIVE, XOR_PARITY, ALIAS
10. **Add 1 missing method:** is_not_null

**Total:** ~60 new methods to add to ExpressionSystem + backend implementations

**Benefit:** Full abstraction layer, easier new backends, better type safety.
