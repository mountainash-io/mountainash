# Architectural Review: ExpressionSystem Protocol Refactoring

**Date:** 2025-01-09
**Status:** Planning - Documentation Phase
**Goal:** Eliminate god classes, achieve symmetric architecture across visitors and backends

---

## Executive Summary

This document provides a comprehensive architectural review of the mountainash-expressions package, identifying god class problems in the ExpressionSystem backend implementations and proposing a protocol-based mixin architecture to achieve symmetry with the existing visitor pattern.

### Key Findings

1. **God Class Confirmed:** ExpressionSystem backends are 663-883 lines with 68+ methods each
2. **Asymmetric Architecture:** Visitors use 14 focused mixins, backends use monolithic classes
3. **Interface Drift:** Base class declares 19 methods, implementations have 68+ methods
4. **Solution:** Extend mixin paradigm to backends using Protocol composition

---

## 1. God Class Problem Analysis

### 1.1 ExpressionSystem Base Class

**Location:** `src/mountainash_expressions/core/expression_system/base.py`
**Size:** 309 lines
**Declared Abstract Methods:** 19
**Actual Implementation Methods:** 68+

#### Method Categories

| Category | Methods in Base | Methods in Implementations | Gap |
|----------|----------------|---------------------------|-----|
| Core Primitives | 2 (col, lit) | 2 | ✅ Complete |
| Comparison | 6 (eq, ne, gt, lt, ge, le) | 6 | ✅ Complete |
| Logical | 3 (and_, or_, not_) | 3 | ✅ Complete |
| Collection | 1 (is_in) | 1 | ✅ Complete |
| Null Operations | 1 (is_null) | 1 | ✅ Complete |
| Type Operations | 1 (cast) | 1 | ✅ Complete |
| Arithmetic | 4 (add, sub, mul, mod) | 7 | ❌ Missing 3 |
| String | 0 | 12 | ❌ Missing 12 |
| Pattern | 0 | 4 | ❌ Missing 4 |
| Conditional | 0 | 3 | ❌ Missing 3 |
| Temporal | 0 | 20+ | ❌ Missing 20+ |

**Total Gap:** 49 missing abstract method declarations

### 1.2 Backend Implementation Sizes

| Backend | File | Lines | Methods | Assessment |
|---------|------|-------|---------|------------|
| **Polars** | `backends/polars/expression_system/polars_expression_system.py` | 663 | 68 | **GOD CLASS** |
| **Narwhals** | `backends/narwhals/expression_system/narwhals_expression_system.py` | 734 | ~70 | **GOD CLASS** |
| **Ibis** | `backends/ibis/expression_system/ibis_expression_system.py` | 883 | ~70 | **GOD CLASS** |

#### God Class Indicators

- ✅ Single class responsible for all backend operations (7+ unrelated categories)
- ✅ Implementations exceed 600 lines (well above 300-line guideline)
- ✅ Violates Single Responsibility Principle
- ✅ High coupling - changes affect entire class
- ✅ Difficult to test individual operation categories
- ✅ Code duplication across backends (similar patterns repeated)

**Verdict:** Confirmed god classes requiring refactoring

### 1.3 UniversalBooleanExpressionVisitor

**Location:** `src/mountainash_expressions/core/expression_visitors/universal_boolean_visitor.py`
**Size:** 776 lines, 88 methods

#### Mixin Composition

```python
class UniversalBooleanExpressionVisitor(
    # Common (3 mixins)
    CastExpressionVisitor,              # 4 methods
    LiteralExpressionVisitor,           # 4 methods
    SourceExpressionVisitor,            # 6 methods

    # Boolean (5 mixins)
    BooleanCollectionExpressionVisitor,  # 6 methods
    BooleanComparisonExpressionVisitor,  # 10 methods
    BooleanConstantExpressionVisitor,    # 6 methods
    BooleanOperatorsExpressionVisitor,   # 9 methods
    BooleanUnaryExpressionVisitor,       # 9 methods

    # Operations (5 mixins)
    ArithmeticOperatorsExpressionVisitor,    # 11 methods
    StringOperatorsExpressionVisitor,        # 16 methods
    PatternOperatorsExpressionVisitor,       # 8 methods
    ConditionalOperatorsExpressionVisitor,   # 9 methods
    TemporalOperatorsExpressionVisitor,      # 28 methods
):
    def __init__(self, backend: ExpressionSystem):
        self.backend = backend  # Dependency injection
```

**Assessment:**
- ❌ NOT a god class - well-factored through mixin composition
- ✅ Each mixin focuses on single operation category
- ✅ Clear separation of concerns
- ✅ Easy to test individual mixins
- ✅ Easy to add new operation categories

**Verdict:** Visitor architecture is exemplary - backends should mirror this pattern

---

## 2. Current Mixin Architecture

### 2.1 Visitor Mixin Inventory

| Category | Mixin File | Abstract Methods | Total Methods | Lines |
|----------|-----------|------------------|---------------|-------|
| **Common** ||||
| Cast | `cast_visitor_mixin.py` | 1 | 4 | ~50 |
| Literal | `literal_visitor_mixin.py` | 1 | 4 | ~60 |
| Source | `source_visitor_mixin.py` | 3 | 6 | ~80 |
| Native | `native_expression_visitor_mixin.py` | 1 | 4 | ~50 |
| **Boolean** ||||
| Collection | `boolean_collection_visitor_mixin.py` | 2 | 6 | ~100 |
| Comparison | `boolean_comparison_visitor_mixin.py` | 6 | 10 | ~150 |
| Constants | `boolean_constant_visitor_mixin.py` | 0 | 6 | ~80 |
| Operators | `boolean_operators_visitor_mixin.py` | 7 | 9 | ~120 |
| Unary | `boolean_unary_visitor_mixin.py` | 4 | 9 | ~100 |
| **Operations** ||||
| Arithmetic | `arithmetic_operators_visitor_mixin.py` | 7 | 11 | ~150 |
| String | `string_operators_visitor_mixin.py` | 12 | 16 | ~200 |
| Pattern | `pattern_operators_visitor_mixin.py` | 4 | 8 | ~100 |
| Conditional | `conditional_operators_visitor_mixin.py` | 3 | 9 | ~120 |
| Temporal | `temporal_operators_visitor_mixin.py` | 23 | 28 | ~300 |

**Total:** 14 mixins, 74 abstract methods, ~110 total methods, ~1,660 lines

**Average Mixin Size:** 118 lines (vs 663-883 for backend implementations)

### 2.2 Mixin Method Types

Each visitor mixin contains two types of methods:

#### A. Concrete Visitor Methods (AST Traversal)

```python
def visit_comparison_expression(self, node: BooleanComparisonExpressionNode) -> Any:
    """Visit a comparison expression node - CONCRETE method."""
    # 1. Resolve expression parameters
    # 2. Extract operands
    # 3. Dispatch to appropriate abstract method based on operator
    # 4. Return backend expression
```

**Purpose:** Handle AST traversal logic (same for all backends)

#### B. Abstract Backend Operation Methods

```python
@abstractmethod
def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> Any:
    """Equality comparison - ABSTRACT method."""
    pass
```

**Purpose:** Define interface for backend operations (implemented in UniversalBooleanVisitor)

### 2.3 Pattern Analysis

**Strengths:**
- ✅ Clear separation: AST logic (concrete) vs backend operations (abstract)
- ✅ Focused mixins (50-300 lines each)
- ✅ Easy to extend (add new mixin for new category)
- ✅ Easy to test (test each mixin independently)
- ✅ Single Responsibility Principle maintained

**This pattern should be replicated for backends.**

---

## 3. Expression Node to Backend Alignment

### 3.1 Complete Node-Visitor-Backend Mapping

| Node Type | Expression Node Class | Visitor Method | Visitor Mixin | Backend Methods |
|-----------|----------------------|----------------|---------------|-----------------|
| **LITERAL** | LiteralExpressionNode | visit_literal_expression() | LiteralExpressionVisitor | lit() |
| **SOURCE** | SourceExpressionNode | visit_source_expression() | SourceExpressionVisitor | col() |
| **CAST** | CastExpressionNode | visit_cast_expression() | CastExpressionVisitor | cast() |
| **NATIVE** | NativeBackendExpressionNode | visit_native_expression() | NativeExpressionVisitor | - |
| **LOGICAL_COMPARISON** | BooleanComparisonExpressionNode | visit_comparison_expression() | BooleanComparisonExpressionVisitor | eq(), ne(), gt(), lt(), ge(), le() |
| **LOGICAL** | BooleanLogicalExpressionNode | visit_logical_expression() | BooleanOperatorsExpressionVisitor | and_(), or_(), xor() |
| **LOGICAL_UNARY** | BooleanUnaryExpressionNode | visit_unary_expression() | BooleanUnaryExpressionVisitor | not_(), is_true(), is_false(), is_null() |
| **COLLECTION** | BooleanCollectionExpressionNode | visit_collection_expression() | BooleanCollectionExpressionVisitor | is_in() |
| **LOGICAL_CONSTANT** | LogicalConstantExpressionNode | visit_constant_expression() | BooleanConstantExpressionVisitor | - |
| **ARITHMETIC** | ArithmeticExpressionNode | visit_arithmetic_expression() | ArithmeticOperatorsExpressionVisitor | add(), subtract(), multiply(), divide(), modulo(), power(), floor_divide() |
| **STRING** | StringExpressionNode | visit_string_expression() | StringOperatorsExpressionVisitor | str_upper(), str_lower(), str_trim(), str_ltrim(), str_rtrim(), str_substring(), str_concat(), str_length(), str_replace(), str_contains(), str_starts_with(), str_ends_with() |
| **PATTERN** | PatternExpressionNode | visit_pattern_expression() | PatternOperatorsExpressionVisitor | pattern_like(), pattern_regex_match(), pattern_regex_contains(), pattern_regex_replace() |
| **CONDITIONAL_IF_ELSE** | BooleanConditionalIfElseExpressionNode | visit_conditional_expression() | ConditionalOperatorsExpressionVisitor | conditional_when(), conditional_coalesce(), conditional_fill_null() |
| **TEMPORAL** | TemporalExpressionNode | visit_temporal_expression() | TemporalOperatorsExpressionVisitor | temporal_year(), temporal_month(), temporal_day(), temporal_hour(), temporal_minute(), temporal_second(), temporal_weekday(), temporal_week(), temporal_quarter(), temporal_add_days(), temporal_add_months(), temporal_add_years(), temporal_add_hours(), temporal_add_minutes(), temporal_add_seconds(), temporal_diff_days(), temporal_diff_months(), temporal_diff_years(), temporal_diff_hours(), temporal_diff_minutes(), temporal_diff_seconds(), temporal_truncate(), temporal_offset_by() |

**Coverage:** 100% - Every node type has corresponding visitor and backend methods ✅

---

## 4. Architectural Asymmetry Problem

### 4.1 Current State

```
┌─────────────────────────────────────────────────────────────┐
│ VISITOR LAYER: Well-Factored with Mixins                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  14 Focused Mixins (50-300 lines each)                      │
│  ├── BooleanComparisonExpressionVisitor (~150 lines)        │
│  ├── ArithmeticOperatorsExpressionVisitor (~150 lines)      │
│  ├── StringOperatorsExpressionVisitor (~200 lines)          │
│  ├── TemporalOperatorsExpressionVisitor (~300 lines)        │
│  └── ... 10 more mixins                                     │
│                                                              │
│  Composed into:                                             │
│  UniversalBooleanExpressionVisitor (776 lines)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
                  Uses self.backend
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND LAYER: Monolithic God Classes                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PolarsExpressionSystem (663 lines, 68 methods)             │
│  ├── Comparison methods (6)                                 │
│  ├── Arithmetic methods (7)                                 │
│  ├── String methods (12)                                    │
│  ├── Temporal methods (20+)                                 │
│  └── ... all in one class                                   │
│                                                              │
│  NarwhalsExpressionSystem (734 lines, ~70 methods)          │
│  IbisExpressionSystem (883 lines, ~70 methods)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Problem Analysis

**Visitors:** Excellent separation of concerns
- Each category in focused mixin
- Easy to maintain
- Easy to test
- Easy to extend

**Backends:** Poor separation of concerns
- All categories in single class
- Difficult to maintain (find specific method among 68+)
- Difficult to test (mock entire backend)
- Difficult to extend (modify large file)
- Code duplication (similar patterns across backends)

**Asymmetry Impact:**
- Inconsistent architecture (visitors vs backends)
- Lost opportunity for code reuse
- Harder to verify completeness
- Confusing for contributors

---

## 5. Proposed Architecture: Protocol-Based Mixins

### 5.1 Target State

```
┌─────────────────────────────────────────────────────────────┐
│ VISITOR LAYER: Focused Mixins (Current - Keep)              │
├─────────────────────────────────────────────────────────────┤
│  14 Focused Mixins → UniversalBooleanVisitor                │
└─────────────────────────────────────────────────────────────┘
                            ↓
                  Uses self.backend
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PROTOCOL LAYER: Interface Definitions (New)                 │
├─────────────────────────────────────────────────────────────┤
│  8 Focused Protocols:                                       │
│  ├── CoreBackend (col, lit)                                 │
│  ├── ComparisonBackend (eq, ne, gt, lt, ge, le)            │
│  ├── LogicalBackend (and_, or_, not_)                       │
│  ├── ArithmeticBackend (add, sub, mul, div, mod, pow, //)   │
│  ├── StringBackend (upper, lower, trim, concat, ...)        │
│  ├── PatternBackend (like, regex_match, ...)                │
│  ├── ConditionalBackend (when, coalesce, fill_null)         │
│  └── TemporalBackend (year, month, add_days, diff_*, ...)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Implemented by
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND MIXIN LAYER: Focused Implementations (New)          │
├─────────────────────────────────────────────────────────────┤
│  Polars: 8 Focused Mixins (50-200 lines each)               │
│  ├── PolarsCoreMixin (~50 lines)                            │
│  ├── PolarsComparisonMixin (~80 lines)                      │
│  ├── PolarsArithmeticMixin (~100 lines)                     │
│  ├── PolarsStringMixin (~150 lines)                         │
│  ├── PolarsTemporalMixin (~200 lines)                       │
│  └── ... 3 more mixins                                      │
│                                                              │
│  Composed into:                                             │
│  PolarsExpressionSystem (~100 lines - composition only)     │
│                                                              │
│  (Same pattern for Narwhals, Ibis)                          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Benefits

1. **Symmetric Architecture:** Visitors and backends both use focused mixins
2. **Reduced Complexity:** 663-883 lines → 8 files of 50-200 lines each
3. **Code Reuse:** Shared mixins for operator-overloading backends
4. **Easy Verification:** Check each category independently
5. **Better Testing:** Test each mixin in isolation
6. **Clear Alignment:** Each protocol matches visitor mixin
7. **Type Safety:** Protocol checking ensures completeness
8. **Easier Extension:** Add new backend by implementing 8 small mixins

### 5.3 Protocol Categories Aligned to Visitor Mixins

| Protocol | Methods | Visitor Mixin Equivalent | Lines (Est.) |
|----------|---------|--------------------------|--------------|
| CoreBackend | 2 | SourceExpressionVisitor + LiteralExpressionVisitor | 50 |
| ComparisonBackend | 6 | BooleanComparisonExpressionVisitor | 80 |
| LogicalBackend | 3 | BooleanOperatorsExpressionVisitor (partial) | 40 |
| ArithmeticBackend | 7 | ArithmeticOperatorsExpressionVisitor | 100 |
| StringBackend | 12 | StringOperatorsExpressionVisitor | 150 |
| PatternBackend | 4 | PatternOperatorsExpressionVisitor | 60 |
| ConditionalBackend | 3 | ConditionalOperatorsExpressionVisitor | 50 |
| TemporalBackend | 20+ | TemporalOperatorsExpressionVisitor | 200 |

**Total:** 8 protocols, 57+ methods (rest are null checks, casting, etc.)

---

## 6. ABC vs Protocol Trade-offs

### 6.1 Abstract Base Classes (Current)

**Advantages:**
- ✅ Familiar pattern to Python developers
- ✅ Clear inheritance hierarchy
- ✅ Runtime enforcement (cannot instantiate if methods missing)
- ✅ __init_subclass__ hooks available
- ✅ Explicit interface declaration

**Disadvantages:**
- ❌ Requires inheritance (tight coupling)
- ❌ Single inheritance limitation (though mixins work)
- ❌ Cannot compose multiple ABCs easily
- ❌ Nominal typing (must explicitly inherit)

### 6.2 Protocols (Proposed)

**Advantages:**
- ✅ Structural typing (duck typing with type safety)
- ✅ No inheritance required (loose coupling)
- ✅ Can compose multiple protocols
- ✅ Better for focused interfaces
- ✅ `@runtime_checkable` for dynamic verification
- ✅ More Pythonic (duck typing tradition)

**Disadvantages:**
- ❌ No instantiation-time enforcement
- ❌ Runtime protocol checking has overhead
- ❌ Less familiar to some developers
- ❌ No __init_subclass__ hooks

### 6.3 Recommendation: Mixed Approach

**Use ABC for Visitors:** (Keep current pattern)
- Visitors have hierarchical structure
- Mixin composition works well with ABC
- Abstract methods enforce visitor contract

**Use Protocols for Backends:** (New pattern)
- Backends don't need inheritance hierarchy
- Protocols enable composition of focused interfaces
- Structural typing allows alternative implementations
- Mirrors the category-based visitor mixins

### 6.4 Migration Strategy

**Phase 1:** Complete ABC interface (add missing abstract methods)
- Immediate benefit: Type checking can verify completeness
- No breaking changes
- Documents full interface

**Phase 2-5:** Extract backend mixins
- Keep ABC inheritance during transition
- Mixins implement portions of ABC
- Test after each backend refactoring

**Phase 6:** Migrate to Protocol composition
- Replace ABC with Protocol composition
- Update type hints
- No external API changes (internal refactoring)

---

## 7. Missing Abstract Method Declarations

### 7.1 Methods to Add to ExpressionSystem Base Class

#### Arithmetic (3 additional methods)
```python
@abstractmethod
def subtract(self, left: Any, right: Any) -> Any:
    """Subtraction: left - right"""
    pass

@abstractmethod
def multiply(self, left: Any, right: Any) -> Any:
    """Multiplication: left * right"""
    pass

@abstractmethod
def divide(self, left: Any, right: Any) -> Any:
    """Division: left / right"""
    pass

@abstractmethod
def modulo(self, left: Any, right: Any) -> Any:
    """Modulo: left % right"""
    pass

@abstractmethod
def power(self, left: Any, right: Any) -> Any:
    """Exponentiation: left ** right"""
    pass

@abstractmethod
def floor_divide(self, left: Any, right: Any) -> Any:
    """Floor division: left // right"""
    pass
```

#### String (12 methods)
```python
@abstractmethod
def str_upper(self, operand: Any) -> Any:
    """Convert string to uppercase"""
    pass

@abstractmethod
def str_lower(self, operand: Any) -> Any:
    """Convert string to lowercase"""
    pass

@abstractmethod
def str_trim(self, operand: Any) -> Any:
    """Remove leading and trailing whitespace"""
    pass

@abstractmethod
def str_ltrim(self, operand: Any) -> Any:
    """Remove leading whitespace"""
    pass

@abstractmethod
def str_rtrim(self, operand: Any) -> Any:
    """Remove trailing whitespace"""
    pass

@abstractmethod
def str_substring(self, operand: Any, start: int, end: Optional[int] = None) -> Any:
    """Extract substring"""
    pass

@abstractmethod
def str_concat(self, *operands: Any) -> Any:
    """Concatenate strings"""
    pass

@abstractmethod
def str_length(self, operand: Any) -> Any:
    """Get string length"""
    pass

@abstractmethod
def str_replace(self, operand: Any, pattern: str, replacement: str) -> Any:
    """Replace substring"""
    pass

@abstractmethod
def str_contains(self, operand: Any, substring: str) -> Any:
    """Check if string contains substring"""
    pass

@abstractmethod
def str_starts_with(self, operand: Any, prefix: str) -> Any:
    """Check if string starts with prefix"""
    pass

@abstractmethod
def str_ends_with(self, operand: Any, suffix: str) -> Any:
    """Check if string ends with suffix"""
    pass
```

#### Pattern (4 methods)
```python
@abstractmethod
def pattern_like(self, operand: Any, pattern: str) -> Any:
    """SQL LIKE pattern matching"""
    pass

@abstractmethod
def pattern_regex_match(self, operand: Any, pattern: str) -> Any:
    """Full regex match"""
    pass

@abstractmethod
def pattern_regex_contains(self, operand: Any, pattern: str) -> Any:
    """Regex contains match"""
    pass

@abstractmethod
def pattern_regex_replace(self, operand: Any, pattern: str, replacement: str) -> Any:
    """Regex replace"""
    pass
```

#### Conditional (3 methods)
```python
@abstractmethod
def conditional_when(self, condition: Any, then_value: Any, else_value: Any = None) -> Any:
    """Conditional if-then-else"""
    pass

@abstractmethod
def conditional_coalesce(self, *operands: Any) -> Any:
    """Return first non-null value"""
    pass

@abstractmethod
def conditional_fill_null(self, operand: Any, fill_value: Any) -> Any:
    """Replace null with fill value"""
    pass
```

#### Temporal (20+ methods)
```python
# Extraction
@abstractmethod
def temporal_year(self, operand: Any) -> Any:
    """Extract year from datetime"""
    pass

@abstractmethod
def temporal_month(self, operand: Any) -> Any:
    """Extract month from datetime"""
    pass

@abstractmethod
def temporal_day(self, operand: Any) -> Any:
    """Extract day from datetime"""
    pass

@abstractmethod
def temporal_hour(self, operand: Any) -> Any:
    """Extract hour from datetime"""
    pass

@abstractmethod
def temporal_minute(self, operand: Any) -> Any:
    """Extract minute from datetime"""
    pass

@abstractmethod
def temporal_second(self, operand: Any) -> Any:
    """Extract second from datetime"""
    pass

@abstractmethod
def temporal_weekday(self, operand: Any) -> Any:
    """Extract weekday (0=Monday, 6=Sunday)"""
    pass

@abstractmethod
def temporal_week(self, operand: Any) -> Any:
    """Extract week number"""
    pass

@abstractmethod
def temporal_quarter(self, operand: Any) -> Any:
    """Extract quarter"""
    pass

# Arithmetic
@abstractmethod
def temporal_add_days(self, operand: Any, days: int) -> Any:
    """Add days to datetime"""
    pass

@abstractmethod
def temporal_add_months(self, operand: Any, months: int) -> Any:
    """Add months to datetime"""
    pass

@abstractmethod
def temporal_add_years(self, operand: Any, years: int) -> Any:
    """Add years to datetime"""
    pass

@abstractmethod
def temporal_add_hours(self, operand: Any, hours: int) -> Any:
    """Add hours to datetime"""
    pass

@abstractmethod
def temporal_add_minutes(self, operand: Any, minutes: int) -> Any:
    """Add minutes to datetime"""
    pass

@abstractmethod
def temporal_add_seconds(self, operand: Any, seconds: int) -> Any:
    """Add seconds to datetime"""
    pass

# Differences
@abstractmethod
def temporal_diff_days(self, left: Any, right: Any) -> Any:
    """Difference in days"""
    pass

@abstractmethod
def temporal_diff_months(self, left: Any, right: Any) -> Any:
    """Difference in months"""
    pass

@abstractmethod
def temporal_diff_years(self, left: Any, right: Any) -> Any:
    """Difference in years"""
    pass

@abstractmethod
def temporal_diff_hours(self, left: Any, right: Any) -> Any:
    """Difference in hours"""
    pass

@abstractmethod
def temporal_diff_minutes(self, left: Any, right: Any) -> Any:
    """Difference in minutes"""
    pass

@abstractmethod
def temporal_diff_seconds(self, left: Any, right: Any) -> Any:
    """Difference in seconds"""
    pass

# Utilities
@abstractmethod
def temporal_truncate(self, operand: Any, unit: str) -> Any:
    """Truncate to unit (day, hour, etc.)"""
    pass

@abstractmethod
def temporal_offset_by(self, operand: Any, offset: str) -> Any:
    """Offset by duration string (e.g., '2h', '30m')"""
    pass
```

**Total:** 49 missing abstract method declarations

---

## 8. Verification and Alignment

### 8.1 Backend Completeness Checklist

For each backend implementation, verify:

- [ ] **Core Operations (2)**
  - [ ] col() - Column reference
  - [ ] lit() - Literal value

- [ ] **Comparison Operations (6)**
  - [ ] eq() - Equality
  - [ ] ne() - Inequality
  - [ ] gt() - Greater than
  - [ ] lt() - Less than
  - [ ] ge() - Greater or equal
  - [ ] le() - Less or equal

- [ ] **Logical Operations (3)**
  - [ ] and_() - Logical AND
  - [ ] or_() - Logical OR
  - [ ] not_() - Logical NOT

- [ ] **Collection Operations (1)**
  - [ ] is_in() - Membership test

- [ ] **Null Operations (1)**
  - [ ] is_null() - Null check

- [ ] **Type Operations (1)**
  - [ ] cast() - Type casting

- [ ] **Arithmetic Operations (7)**
  - [ ] add() - Addition
  - [ ] subtract() - Subtraction
  - [ ] multiply() - Multiplication
  - [ ] divide() - Division
  - [ ] modulo() - Modulo
  - [ ] power() - Exponentiation
  - [ ] floor_divide() - Floor division

- [ ] **String Operations (12)**
  - [ ] str_upper() - Uppercase
  - [ ] str_lower() - Lowercase
  - [ ] str_trim() - Trim
  - [ ] str_ltrim() - Left trim
  - [ ] str_rtrim() - Right trim
  - [ ] str_substring() - Substring
  - [ ] str_concat() - Concatenate
  - [ ] str_length() - Length
  - [ ] str_replace() - Replace
  - [ ] str_contains() - Contains
  - [ ] str_starts_with() - Starts with
  - [ ] str_ends_with() - Ends with

- [ ] **Pattern Operations (4)**
  - [ ] pattern_like() - LIKE matching
  - [ ] pattern_regex_match() - Regex match
  - [ ] pattern_regex_contains() - Regex contains
  - [ ] pattern_regex_replace() - Regex replace

- [ ] **Conditional Operations (3)**
  - [ ] conditional_when() - If-then-else
  - [ ] conditional_coalesce() - Coalesce
  - [ ] conditional_fill_null() - Fill null

- [ ] **Temporal Operations (20+)**
  - [ ] temporal_year() - Extract year
  - [ ] temporal_month() - Extract month
  - [ ] temporal_day() - Extract day
  - [ ] temporal_hour() - Extract hour
  - [ ] temporal_minute() - Extract minute
  - [ ] temporal_second() - Extract second
  - [ ] temporal_weekday() - Extract weekday
  - [ ] temporal_week() - Extract week
  - [ ] temporal_quarter() - Extract quarter
  - [ ] temporal_add_days() - Add days
  - [ ] temporal_add_months() - Add months
  - [ ] temporal_add_years() - Add years
  - [ ] temporal_add_hours() - Add hours
  - [ ] temporal_add_minutes() - Add minutes
  - [ ] temporal_add_seconds() - Add seconds
  - [ ] temporal_diff_days() - Days difference
  - [ ] temporal_diff_months() - Months difference
  - [ ] temporal_diff_years() - Years difference
  - [ ] temporal_diff_hours() - Hours difference
  - [ ] temporal_diff_minutes() - Minutes difference
  - [ ] temporal_diff_seconds() - Seconds difference
  - [ ] temporal_truncate() - Truncate
  - [ ] temporal_offset_by() - Offset by duration

**Total:** 60 required methods (minimum)

### 8.2 Cross-Layer Alignment Matrix

See separate document: `Alignment-Matrix.md`

---

## 9. Recommendations

### Priority 1: Complete ABC Interface (Immediate)

**Action:** Add 49 missing abstract method declarations to `ExpressionSystem` base class

**Benefits:**
- Type checkers can verify backend completeness
- Documents full interface
- No breaking changes
- Foundation for future refactoring

**Effort:** 1-2 days

### Priority 2: Define Protocol Architecture (Short-term)

**Action:** Create `backends/protocols/` with 8 protocol definitions

**Benefits:**
- Defines focused interfaces
- Enables structural typing
- Prepares for mixin extraction
- Can be used for type hints immediately

**Effort:** 2-3 days

### Priority 3: Extract Backend Mixins (Medium-term)

**Action:** Refactor backends to use mixin composition

**Benefits:**
- Eliminates god classes
- Symmetric architecture
- Easier maintenance
- Code reuse across backends

**Effort:** 2-3 weeks (all three backends)

### Priority 4: Shared Base Mixins (Long-term)

**Action:** Extract common logic to `backends/common/`

**Benefits:**
- DRY principle
- Faster implementation of new backends
- Consistency across backends

**Effort:** 1 week

---

## 10. Conclusion

The mountainash-expressions package has an excellent visitor architecture with focused mixins, but suffers from god class problems in the backend layer. By extending the mixin paradigm to backends using Protocol composition, we can achieve:

1. **Symmetric architecture** - visitors and backends both use focused mixins
2. **Reduced complexity** - 663-883 line god classes → 8 mixins of 50-200 lines each
3. **Better maintainability** - easier to find, test, and extend specific operations
4. **Clear alignment** - protocols mirror visitor categories exactly
5. **Type safety** - complete interface declarations with protocol checking
6. **Code reuse** - shared base mixins for similar backends

The proposed refactoring is low-risk (incremental, well-tested) with high value (eliminates major architectural debt).

---

**Next Steps:** See `Refactoring-Roadmap.md` for detailed implementation plan.
