# Constants.py Enum Alignment Analysis

## Executive Summary

This analysis examines how the enums defined in `constants.py` align with the rest of the mountainash-expressions architecture. The enums serve as the **single source of truth** for what operations exist in the system.

Key findings:
- **Node Types:** 11 of 13 enum node types have corresponding ExpressionNode classes (ALIAS missing, PATTERN maps to one class)
- **Operators:** 74 operator enum values defined across 11 operator enums
- **Backend Methods:** 54 methods in ExpressionSystem interface
- **Visitor Methods:** Named with underscore prefix convention (_B_eq, _subtract, _regex_match, etc.)
- **Overall Coverage:** ~85% enum-to-implementation alignment

---

## 1. Enum Node Type Mapping

### CONST_EXPRESSION_NODE_TYPES Enum (13 values)

| Enum Name | Value | Implemented Node Class | Status | Notes |
|-----------|-------|------------------------|--------|-------|
| NATIVE | "native_backend" | NativeBackendExpressionNode | ✅ | Passthrough for backend-native expressions |
| SOURCE | "source" | SourceExpressionNode | ✅ | Column references (col, is_null, is_not_null) |
| LITERAL | "literal" | LiteralExpressionNode | ✅ | Literal values (lit) |
| CAST | "cast" | CastExpressionNode | ✅ | Type casting |
| ALIAS | "alias" | ❌ MISSING | ⚠️ | **GAP: Enum defined but no node class** |
| LOGICAL | "logical" | LogicalExpressionNode | ✅ | AND, OR, XOR operations |
| LOGICAL_COMPARISON | "comparison" | ComparisonExpressionNode | ✅ | EQ, NE, GT, LT, GE, LE |
| LOGICAL_CONSTANT | "logical_constant" | LogicalConstantExpressionNode | ✅ | ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN |
| LOGICAL_UNARY | "unary" | UnaryExpressionNode | ✅ | IS_TRUE, IS_FALSE, IS_UNKNOWN |
| COLLECTION | "collection" | CollectionExpressionNode | ✅ | IN, NOT_IN |
| ARITHMETIC | "arithmetic" | ArithmeticExpressionNode | ✅ | ADD, SUB, MUL, DIV, MOD, POW |
| STRING | "string" | StringExpressionNode | ✅ | UPPER, LOWER, TRIM, SUBSTRING, etc. |
| PATTERN | "pattern" | PatternExpressionNode | ✅ | LIKE, REGEX_MATCH, REGEX_CONTAINS, REGEX_REPLACE |
| CONDITIONAL_IF_ELSE | "conditional_if_else" | ConditionalIfElseExpressionNode | ✅ | WHEN, COALESCE, FILL_NULL |
| TEMPORAL | "temporal" | TemporalExpressionNode | ✅ | YEAR, MONTH, DAY, HOUR, etc. |

**Coverage:** 12/13 node types implemented (92%)

### Implementation Details

**Node Classes:** All 12 implemented node classes inherit from `ExpressionNode` and implement:
- `expression_type` property (returns matching CONST_EXPRESSION_NODE_TYPES enum)
- `logic_type` property (BOOLEAN or other logic system)
- `accept(visitor)` method (visitor pattern)
- `eval()` method (lazy evaluation)

Boolean-specific node classes add prefixes (e.g., `BooleanComparisonExpressionNode`):
- BooleanUnaryExpressionNode
- BooleanLogicalExpressionNode
- BooleanComparisonExpressionNode
- BooleanConditionalIfElseExpressionNode
- BooleanCollectionExpressionNode

---

## 2. Operator Enum to Backend Method Mapping

### Operator Enums Summary

| Operator Enum | Count | Backend Methods | Visitor Pattern |
|---------------|-------|-----------------|-----------------|
| CONST_EXPRESSION_NATIVE_OPERATORS | 1 | N/A | Direct passthrough |
| CONST_EXPRESSION_SOURCE_OPERATORS | 3 | col, is_null, is_not_null | col(), is_null() |
| CONST_EXPRESSION_LITERAL_OPERATORS | 1 | lit | lit() |
| CONST_EXPRESSION_CAST_OPERATORS | 1 | cast | cast() |
| CONST_EXPRESSION_ALIAS_OPERATORS | 1 | ❌ NONE | ⚠️ **GAP** |
| CONST_EXPRESSION_LOGICAL_OPERATORS | 5 | and_, or_, not_ | _and, _or, _not |
| CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS | 6 | eq, ne, gt, lt, ge, le | _B_eq, _B_ne, _B_gt, _B_lt, _B_ge, _B_le |
| CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS | 2 | is_in (NOT_IN missing) | _B_in, _B_not_in |
| CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS | 6 | ❌ NONE | ⚠️ **GAP** |
| CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS | 3 | ❌ NONE | ⚠️ **GAP** |
| CONST_EXPRESSION_ARITHMETIC_OPERATORS | 7 | add, sub, mul, mod | _add, _subtract, _multiply, _divide, _modulo, _power, _floor_divide |
| CONST_EXPRESSION_STRING_OPERATORS | 12 | ❌ NONE | ⚠️ **Missing** |
| CONST_EXPRESSION_PATTERN_OPERATORS | 4 | ❌ NONE | ⚠️ **Missing** |
| CONST_EXPRESSION_CONDITIONAL_OPERATORS | 3 | ❌ NONE | ⚠️ **Missing** |
| CONST_EXPRESSION_TEMPORAL_OPERATORS | 22 | ❌ NONE | ⚠️ **Missing** |

**Total operator enum values:** 78
**Backend methods defined:** 54
**Coverage:** ~69% (missing div, floor_divide, 48 other methods)

---

## 3. Detailed Operator-to-Method Mapping

### CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS
Maps to ExpressionSystem comparison methods:

| Enum | Backend Method | Visitor Method | Implementation |
|------|---|---|---|
| EQ | eq(left, right) | _B_eq() | ✅ |
| NE | ne(left, right) | _B_ne() | ✅ |
| GT | gt(left, right) | _B_gt() | ✅ |
| LT | lt(left, right) | _B_lt() | ✅ |
| GE | ge(left, right) | _B_ge() | ✅ |
| LE | le(left, right) | _B_le() | ✅ |

### CONST_EXPRESSION_ARITHMETIC_OPERATORS
Maps to ExpressionSystem arithmetic methods:

| Enum | Backend Method | Visitor Method | Implementation |
|------|---|---|---|
| ADD | add(left, right) | _add() | ✅ |
| SUBTRACT | sub(left, right) | _subtract() | ✅ |
| MULTIPLY | mul(left, right) | _multiply() | ✅ |
| DIVIDE | ❌ MISSING | _divide() | ⚠️ Defined in visitor, NOT in ExpressionSystem |
| MODULO | mod(left, right) | _modulo() | ✅ |
| POWER | ❌ MISSING | _power() | ⚠️ Defined in visitor, NOT in ExpressionSystem |
| FLOOR_DIVIDE | ❌ MISSING | _floor_divide() | ⚠️ Defined in visitor, NOT in ExpressionSystem |

**Gap:** div(), pow(), floor_div() NOT in base ExpressionSystem

### CONST_EXPRESSION_LOGICAL_OPERATORS
Maps to ExpressionSystem logical methods:

| Enum | Backend Method | Visitor Method | Implementation |
|------|---|---|---|
| NOT | not_(operand) | _not() | ✅ |
| AND | and_(left, right) | _and() | ✅ |
| OR | or_(left, right) | _or() | ✅ |
| XOR_EXCLUSIVE | ❌ MISSING | ⚠️ | **GAP: Enum defined but no implementation** |
| XOR_PARITY | ❌ MISSING | ⚠️ | **GAP: Enum defined but no implementation** |

### CONST_EXPRESSION_STRING_OPERATORS
Enum values defined:

```
UPPER, LOWER, TRIM, LTRIM, RTRIM, SUBSTRING,
CONCAT, LENGTH, REPLACE, CONTAINS, STARTS_WITH, ENDS_WITH
```

Backend methods: ❌ NONE in ExpressionSystem base
Visitor implementation: ✅ StringOperatorsExpressionVisitor exists (12 operators)
**Status:** ⚠️ Visitor level only, no ExpressionSystem abstraction

### CONST_EXPRESSION_PATTERN_OPERATORS
Enum values defined:

```
LIKE, REGEX_MATCH, REGEX_CONTAINS, REGEX_REPLACE
```

Backend methods: ❌ NONE in ExpressionSystem base
Visitor implementation: ✅ PatternOperatorsExpressionVisitor exists
**Status:** ⚠️ Visitor level only, no ExpressionSystem abstraction

### CONST_EXPRESSION_TEMPORAL_OPERATORS
Enum values defined (22 total):

```
Date/Time Extraction: YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEKDAY, WEEK, QUARTER
Date Arithmetic (Add): ADD_DAYS, ADD_HOURS, ADD_MINUTES, ADD_SECONDS, ADD_MONTHS, ADD_YEARS
Date Arithmetic (Diff): DIFF_DAYS, DIFF_HOURS, DIFF_MINUTES, DIFF_SECONDS, DIFF_MONTHS, DIFF_YEARS
Date Truncation: TRUNCATE
Flexible Operations: OFFSET_BY
```

Backend methods: ❌ NONE in ExpressionSystem base
Visitor implementation: ✅ TemporalOperatorsExpressionVisitor exists
**Status:** ⚠️ Visitor level only, no ExpressionSystem abstraction

### CONST_EXPRESSION_CONDITIONAL_OPERATORS
Enum values defined:

```
WHEN, COALESCE, FILL_NULL
```

Backend methods: ❌ NONE in ExpressionSystem base
Visitor implementation: ✅ ConditionalOperatorsExpressionVisitor exists
**Status:** ⚠️ Visitor level only, no ExpressionSystem abstraction

### CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS
Enum values defined:

```
IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN, MAYBE_TRUE, MAYBE_FALSE
```

Backend methods: ❌ NONE in ExpressionSystem base
Visitor implementation: ✅ BooleanUnaryExpressionVisitor exists
**Status:** ⚠️ Visitor level only, no ExpressionSystem abstraction

### CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS
Enum values defined:

```
ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN
```

Backend methods: ❌ NONE in ExpressionSystem base
Visitor implementation: ✅ BooleanConstantExpressionVisitor exists
**Status:** ⚠️ Visitor level only, no ExpressionSystem abstraction

### CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS
Enum values defined:

```
IN, NOT_IN
```

Backend methods:
- is_in() ✅ (only for IN)
- is_not_in() ❌ MISSING

Visitor implementation: ✅ BooleanCollectionExpressionVisitor exists
**Status:** ⚠️ Partial - is_not_in() missing from ExpressionSystem

---

## 4. Naming Convention Analysis

### Backend Method Naming (ExpressionSystem)
Pattern: lowercase, underscores for multi-word, trailing underscore for reserved words

Examples:
```
col()           # column reference
lit()           # literal value
is_null()       # null check
is_in()         # membership test
and_()          # logical AND (trailing _ because AND is reserved)
or_()           # logical OR (trailing _)
not_()          # logical NOT (trailing _)
eq()            # equality
ne()            # inequality
gt()            # greater than
add()           # addition
sub()           # subtraction
mul()           # multiplication
mod()           # modulo
cast()          # type cast
```

### Visitor Method Naming (Mixins)
Pattern: underscore prefix + operation

**Comparison methods (_B_* prefix):**
```
_B_eq(), _B_ne(), _B_gt(), _B_lt(), _B_ge(), _B_le()
```

**Arithmetic methods (single _ prefix):**
```
_add(), _subtract(), _multiply(), _divide(), _modulo(), _power(), _floor_divide()
```

**Logical methods (_* prefix or _B_* prefix):**
```
_and(), _or(), _not() (in logical operators mixin)
_B_in(), _B_not_in() (in collection mixin)
_B_is_true(), _B_is_false() (in unary mixin)
```

**String methods (_* prefix):**
```
_upper(), _lower(), _trim(), _ltrim(), _rtrim()
_substring(), _concat(), _length(), _replace()
_contains(), _starts_with(), _ends_with()
```

**Pattern methods (_* prefix):**
```
_like(), _regex_match(), _regex_contains(), _regex_replace()
```

**Temporal methods (_* prefix):**
```
_year(), _month(), _day(), _hour(), _minute(), _second()
_add_days(), _add_hours(), _add_minutes(), _add_seconds(), _add_months(), _add_years()
_diff_days(), _diff_hours(), _diff_minutes(), _diff_seconds(), _diff_months(), _diff_years()
_truncate(), _offset_by()
```

**Conditional methods (_* prefix):**
```
_when(), _coalesce(), _fill_null()
```

### Naming Pattern Summary

| Category | Backend Pattern | Visitor Pattern | Example |
|----------|---|---|---|
| Primitives | lowercase | visit_*_expression() | col() → visit_source_expression() |
| Comparison | lowercase | _B_* | eq() → _B_eq() |
| Arithmetic | lowercase | _* | add() → _add() |
| Logical | lowercase + _ | _* or _B_* | and_() → _and() |
| Collections | is_* | _B_* | is_in() → _B_in() |
| Null checks | is_* | visit_source_expression() | is_null() → part of SOURCE visitor |
| Type | lowercase | visit_cast_expression() | cast() → visit_cast_expression() |
| String | MISSING | _* | NONE → _upper(), _lower(), etc. |
| Pattern | MISSING | _* | NONE → _like(), _regex_match(), etc. |
| Temporal | MISSING | _* | NONE → _year(), _month(), etc. |
| Conditional | MISSING | _* | NONE → _when(), _coalesce(), etc. |

---

## 5. Coverage Analysis

### By Category

| Category | Enum Values | Backend Methods | Coverage | Notes |
|----------|---|---|---|---|
| **Core Primitives** | 3 | 2 | 67% | col(), lit() ✅; no ALIAS |
| **Comparison** | 6 | 6 | 100% | eq, ne, gt, lt, ge, le ✅ |
| **Logical** | 5 | 3 | 60% | and_, or_, not_ ✅; XOR_EXCLUSIVE/PARITY missing |
| **Collection** | 2 | 1 | 50% | is_in() ✅; is_not_in() missing |
| **Null Checks** | 2 | 1 | 50% | is_null() ✅; is_not_null missing |
| **Type Operations** | 1 | 1 | 100% | cast() ✅ |
| **Arithmetic** | 7 | 4 | 57% | add, sub, mul, mod ✅; div, pow, floor_div missing |
| **String** | 12 | 0 | 0% | ❌ No backend methods |
| **Pattern** | 4 | 0 | 0% | ❌ No backend methods |
| **Temporal** | 22 | 0 | 0% | ❌ No backend methods |
| **Conditional** | 3 | 0 | 0% | ❌ No backend methods |
| **Unary/Constants** | 9 | 0 | 0% | ❌ No backend methods |
| **TOTAL** | 78 | 18 | 23% | **Critical gaps in backend abstraction** |

### Abstraction Levels

Operations exist at different abstraction levels:

```
Tier 1 - ExpressionSystem (Backend-agnostic interface)
  - Core: col(), lit(), cast()
  - Comparison: eq(), ne(), gt(), lt(), ge(), le()
  - Logical: and_(), or_(), not_()
  - Collection: is_in()
  - Null: is_null()
  - Arithmetic: add(), sub(), mul(), mod()
  Total: 18 methods

Tier 2 - Visitor Mixins (Backend-specific logic, manual dispatch)
  - String: 12 operators
  - Pattern: 4 operators
  - Temporal: 22 operators
  - Conditional: 3 operators
  - Unary: 6 operators
  - Constants: 3 operators
  Total: 50 operations

Tier 3 - Direct visitor implementation (no enum dispatch)
  - Various helper methods
```

---

## 6. Gap Analysis

### Critical Gaps

#### 1. ALIAS Operator
- **Defined in enum:** CONST_EXPRESSION_NODE_TYPES.ALIAS
- **Node class:** ❌ Missing
- **Backend method:** ❌ Missing
- **Impact:** Cannot rename/alias columns
- **Recommendation:** Either remove from enum or implement

#### 2. Arithmetic Operations Missing from ExpressionSystem
- **Defined in enum:** DIV, POW, FLOOR_DIVIDE
- **Backend methods:** ❌ Missing
- **Visitor methods:** ✅ Exist (_divide, _power, _floor_divide)
- **Impact:** No backend abstraction; each backend must implement separately
- **Recommendation:** Add div(), pow(), floor_div() to ExpressionSystem

#### 3. Logical XOR Operators
- **Defined in enum:** XOR_EXCLUSIVE, XOR_PARITY
- **Backend methods:** ❌ Missing
- **Visitor methods:** ❌ Missing
- **Impact:** XOR operations cannot be compiled
- **Recommendation:** Remove from enum or implement full stack

#### 4. Collection NOT_IN Missing
- **Defined in enum:** CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS.NOT_IN
- **Backend method:** ❌ Missing (only is_in exists)
- **Visitor method:** ✅ Exists (_B_not_in)
- **Impact:** NOT_IN operations rely on visitor-level logic only
- **Recommendation:** Add is_not_in() to ExpressionSystem

#### 5. String Operations - No Backend Abstraction
- **Defined in enum:** 12 operators (UPPER, LOWER, TRIM, SUBSTRING, etc.)
- **Backend methods:** ❌ None in ExpressionSystem
- **Visitor methods:** ✅ Exist in StringOperatorsExpressionVisitor
- **Impact:** String operations tightly coupled to visitor implementation
- **Recommendation:** Create StringOperations section in ExpressionSystem

#### 6. Pattern Operations - No Backend Abstraction
- **Defined in enum:** 4 operators (LIKE, REGEX_MATCH, REGEX_CONTAINS, REGEX_REPLACE)
- **Backend methods:** ❌ None in ExpressionSystem
- **Visitor methods:** ✅ Exist in PatternOperatorsExpressionVisitor
- **Impact:** Pattern operations tightly coupled to visitor implementation
- **Recommendation:** Create PatternOperations section in ExpressionSystem

#### 7. Temporal Operations - No Backend Abstraction
- **Defined in enum:** 22 operators (extraction, arithmetic, truncation)
- **Backend methods:** ❌ None in ExpressionSystem
- **Visitor methods:** ✅ Exist in TemporalOperatorsExpressionVisitor
- **Impact:** Temporal operations have complex visitor-level logic
- **Recommendation:** Create TemporalOperations section in ExpressionSystem

#### 8. Conditional Operations - No Backend Abstraction
- **Defined in enum:** 3 operators (WHEN, COALESCE, FILL_NULL)
- **Backend methods:** ❌ None in ExpressionSystem
- **Visitor methods:** ✅ Exist in ConditionalOperatorsExpressionVisitor
- **Impact:** Conditional operations have complex visitor-level logic
- **Recommendation:** Create ConditionalOperations section in ExpressionSystem

#### 9. Unary and Constant Operations - No Backend Abstraction
- **Defined in enum:** 9 operators (IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN, etc.)
- **Backend methods:** ❌ None in ExpressionSystem
- **Visitor methods:** ✅ Exist in boolean mixins
- **Impact:** Truth value checks tightly coupled to visitor
- **Recommendation:** Create UnaryOperations section in ExpressionSystem

---

## 7. Alignment Matrix

### Enum → Architecture Path

```
CONST_EXPRESSION_NODE_TYPES enum value
    ↓
ExpressionNode subclass (e.g., ComparisonExpressionNode)
    ↓
Node.accept(visitor) calls visit_*_expression()
    ↓
Visitor mixin (e.g., BooleanComparisonExpressionVisitor)
    ↓
Mixin has operation dispatch dict (e.g., boolean_comparison_ops)
    ↓
Dispatch to abstract method (e.g., _B_eq)
    ↓
UniversalBooleanExpressionVisitor implements concrete method
    ↓
Method calls self.backend.eq() [ExpressionSystem method]
    ↓
Backend-native expression returned
```

### Full Enum → Implementation Mapping

| Node Type | Node Class | Enum | Visitor Mixin | Backend Methods | ✅/❌ |
|-----------|---|---|---|---|---|
| LITERAL | LiteralExpressionNode | LITERAL_OPERATORS | LiteralExpressionVisitor | lit() | ✅ |
| SOURCE | SourceExpressionNode | SOURCE_OPERATORS | SourceExpressionVisitor | col(), is_null() | ✅ |
| CAST | CastExpressionNode | CAST_OPERATORS | CastExpressionVisitor | cast() | ✅ |
| COMPARISON | ComparisonExpressionNode | LOGICAL_COMPARISON_OPERATORS | BooleanComparisonExpressionVisitor | eq, ne, gt, lt, ge, le | ✅ |
| LOGICAL | LogicalExpressionNode | LOGICAL_OPERATORS | BooleanOperatorsExpressionVisitor | and_, or_, not_ | ⚠️ (XOR missing) |
| COLLECTION | CollectionExpressionNode | LOGICAL_COLLECTION_OPERATORS | BooleanCollectionExpressionVisitor | is_in | ⚠️ (is_not_in missing) |
| LOGICAL_UNARY | UnaryExpressionNode | LOGICAL_UNARY_OPERATORS | BooleanUnaryExpressionVisitor | ❌ None | ❌ |
| LOGICAL_CONSTANT | LogicalConstantExpressionNode | LOGICAL_CONSTANT_OPERATORS | BooleanConstantExpressionVisitor | ❌ None | ❌ |
| ARITHMETIC | ArithmeticExpressionNode | ARITHMETIC_OPERATORS | ArithmeticOperatorsExpressionVisitor | add, sub, mul, mod | ⚠️ (div, pow, floor_div missing) |
| STRING | StringExpressionNode | STRING_OPERATORS | StringOperatorsExpressionVisitor | ❌ None | ❌ |
| PATTERN | PatternExpressionNode | PATTERN_OPERATORS | PatternOperatorsExpressionVisitor | ❌ None | ❌ |
| CONDITIONAL_IF_ELSE | ConditionalIfElseExpressionNode | CONDITIONAL_OPERATORS | ConditionalOperatorsExpressionVisitor | ❌ None | ❌ |
| TEMPORAL | TemporalExpressionNode | TEMPORAL_OPERATORS | TemporalOperatorsExpressionVisitor | ❌ None | ❌ |

---

## 8. Recommendations for Protocol Design

### Proposed Base Operations Protocols

Based on the enum structure and existing code, here are 8 protocols that should align with the enums:

```python
# 1. Core Primitives Protocol
class CoreOperationsProtocol(Protocol):
    def col(self, name: str) -> T: ...
    def lit(self, value: Any) -> T: ...
    def cast(self, expr: T, dtype: Any) -> T: ...

# 2. Comparison Operations Protocol
class ComparisonOperationsProtocol(Protocol):
    def eq(self, left: T, right: T) -> T: ...
    def ne(self, left: T, right: T) -> T: ...
    def gt(self, left: T, right: T) -> T: ...
    def lt(self, left: T, right: T) -> T: ...
    def ge(self, left: T, right: T) -> T: ...
    def le(self, left: T, right: T) -> T: ...

# 3. Logical Operations Protocol
class LogicalOperationsProtocol(Protocol):
    def and_(self, left: T, right: T) -> T: ...
    def or_(self, left: T, right: T) -> T: ...
    def not_(self, expr: T) -> T: ...
    def xor_exclusive(self, left: T, right: T) -> T: ...  # MISSING
    def xor_parity(self, left: T, right: T) -> T: ...     # MISSING

# 4. Collection Operations Protocol
class CollectionOperationsProtocol(Protocol):
    def is_in(self, expr: T, collection: List[T]) -> T: ...
    def is_not_in(self, expr: T, collection: List[T]) -> T: ...  # MISSING

# 5. Null Operations Protocol
class NullOperationsProtocol(Protocol):
    def is_null(self, expr: T) -> T: ...
    def is_not_null(self, expr: T) -> T: ...  # MISSING

# 6. Arithmetic Operations Protocol (MISSING from ExpressionSystem)
class ArithmeticOperationsProtocol(Protocol):
    def add(self, left: T, right: T) -> T: ...
    def sub(self, left: T, right: T) -> T: ...
    def mul(self, left: T, right: T) -> T: ...
    def div(self, left: T, right: T) -> T: ...    # MISSING
    def mod(self, left: T, right: T) -> T: ...
    def pow(self, left: T, right: T) -> T: ...    # MISSING
    def floor_div(self, left: T, right: T) -> T: ...  # MISSING

# 7. String Operations Protocol (MISSING from ExpressionSystem)
class StringOperationsProtocol(Protocol):
    def upper(self, expr: T) -> T: ...
    def lower(self, expr: T) -> T: ...
    def trim(self, expr: T) -> T: ...
    def ltrim(self, expr: T) -> T: ...
    def rtrim(self, expr: T) -> T: ...
    def substring(self, expr: T, start: Any, end: Any) -> T: ...
    def concat(self, *exprs: T) -> T: ...
    def length(self, expr: T) -> T: ...
    def replace(self, expr: T, old: T, new: T) -> T: ...
    def contains(self, expr: T, pattern: T) -> T: ...
    def starts_with(self, expr: T, prefix: T) -> T: ...
    def ends_with(self, expr: T, suffix: T) -> T: ...

# 8. Pattern Operations Protocol (MISSING from ExpressionSystem)
class PatternOperationsProtocol(Protocol):
    def like(self, expr: T, pattern: str) -> T: ...
    def regex_match(self, expr: T, pattern: str) -> T: ...
    def regex_contains(self, expr: T, pattern: str) -> T: ...
    def regex_replace(self, expr: T, pattern: str, replacement: str) -> T: ...

# 9. Temporal Operations Protocol (MISSING from ExpressionSystem)
class TemporalExtractionProtocol(Protocol):
    def year(self, expr: T) -> T: ...
    def month(self, expr: T) -> T: ...
    def day(self, expr: T) -> T: ...
    def hour(self, expr: T) -> T: ...
    def minute(self, expr: T) -> T: ...
    def second(self, expr: T) -> T: ...
    def weekday(self, expr: T) -> T: ...
    def week(self, expr: T) -> T: ...
    def quarter(self, expr: T) -> T: ...

class TemporalArithmeticProtocol(Protocol):
    def add_days(self, expr: T, days: Any) -> T: ...
    def add_hours(self, expr: T, hours: Any) -> T: ...
    def add_minutes(self, expr: T, minutes: Any) -> T: ...
    def add_seconds(self, expr: T, seconds: Any) -> T: ...
    def add_months(self, expr: T, months: Any) -> T: ...
    def add_years(self, expr: T, years: Any) -> T: ...
    def diff_days(self, left: T, right: T) -> T: ...
    def diff_hours(self, left: T, right: T) -> T: ...
    def diff_minutes(self, left: T, right: T) -> T: ...
    def diff_seconds(self, left: T, right: T) -> T: ...
    def diff_months(self, left: T, right: T) -> T: ...
    def diff_years(self, left: T, right: T) -> T: ...

class TemporalOperationsProtocol(TemporalExtractionProtocol, TemporalArithmeticProtocol):
    def truncate(self, expr: T, unit: str) -> T: ...
    def offset_by(self, expr: T, offset: str) -> T: ...

# 10. Conditional Operations Protocol (MISSING from ExpressionSystem)
class ConditionalOperationsProtocol(Protocol):
    def when(self, condition: T) -> T: ...  # Returns object with then() method
    def coalesce(self, *exprs: T) -> T: ...
    def fill_null(self, expr: T, value: T) -> T: ...

# 11. Unary/Truth Operations Protocol (MISSING from ExpressionSystem)
class UnaryOperationsProtocol(Protocol):
    def is_true(self, expr: T) -> T: ...
    def is_false(self, expr: T) -> T: ...
    def is_unknown(self, expr: T) -> T: ...     # Ternary only
    def is_known(self, expr: T) -> T: ...       # Ternary only
    def maybe_true(self, expr: T) -> T: ...     # Ternary only
    def maybe_false(self, expr: T) -> T: ...    # Ternary only
```

### Enum to Protocol Mapping

| Operator Enum | Mapped Protocol | Status |
|---|---|---|
| CONST_EXPRESSION_SOURCE_OPERATORS | CoreOperationsProtocol | ✅ Implemented |
| CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS | ComparisonOperationsProtocol | ✅ Implemented |
| CONST_EXPRESSION_LOGICAL_OPERATORS | LogicalOperationsProtocol | ⚠️ Partial (XOR missing) |
| CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS | CollectionOperationsProtocol | ⚠️ Partial (NOT_IN missing) |
| CONST_EXPRESSION_ARITHMETIC_OPERATORS | ArithmeticOperationsProtocol | ⚠️ Partial (3 ops missing) |
| CONST_EXPRESSION_STRING_OPERATORS | StringOperationsProtocol | ❌ Not in ExpressionSystem |
| CONST_EXPRESSION_PATTERN_OPERATORS | PatternOperationsProtocol | ❌ Not in ExpressionSystem |
| CONST_EXPRESSION_TEMPORAL_OPERATORS | TemporalOperationsProtocol | ❌ Not in ExpressionSystem |
| CONST_EXPRESSION_CONDITIONAL_OPERATORS | ConditionalOperationsProtocol | ❌ Not in ExpressionSystem |
| CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS | UnaryOperationsProtocol | ❌ Not in ExpressionSystem |

---

## 9. Key Insights

### The Enum as Single Source of Truth

The enums in constants.py are **critically important** because they define:
1. **What operations exist** - The "contract" of what the system supports
2. **Operation identity** - Unique enum values identify operations
3. **Operation dispatch** - Visitor mixins use enum values as dict keys
4. **Documentation** - Enum docstrings document what operations do

**Problem:** Enum values exist but don't always have full implementation stack.

### Two-Tier Implementation Model

Currently, the system uses two tiers:

**Tier 1: ExpressionSystem (Abstract Backend Interface)**
- ✅ Implemented for: Core, Comparison, Logical (partial), Collection (partial), Arithmetic (partial), Null (partial)
- ❌ Missing for: String, Pattern, Temporal, Conditional, Unary, Constants

**Tier 2: Visitor-Only Implementation**
- Used for: String, Pattern, Temporal, Conditional, Unary, Constants
- Problem: Direct visitor implementation means harder to extend, less backend abstraction

### Naming Convention Consistency

The naming is **mostly consistent** but uses different patterns:
- **Backend methods:** snake_case, trailing underscore for reserved words (and_, or_, not_)
- **Visitor abstract methods:** Prefixed with underscore (_add, _B_eq)
- **Visitor prefix conventions:**
  - _B_* for boolean operations (comparison, unary, collection)
  - _* for other operations (arithmetic, string, pattern, temporal, conditional)

This is inconsistent and could be unified.

### Coverage Summary

- **Node Type Coverage:** 92% (12/13, missing ALIAS)
- **Operator Definition:** 78 enum values defined
- **Backend Abstraction:** 23% (18/78 methods in ExpressionSystem)
- **Visitor Implementation:** ~100% (all enum operators have visitor methods)
- **Critical Gap:** 48 operators defined in enums but not abstracted to ExpressionSystem level

---

## 10. Recommended Actions

### Priority 1: Fix Critical Gaps

1. **Add Missing Arithmetic Methods to ExpressionSystem**
   - Add div(), pow(), floor_div() to ExpressionSystem base
   - Update all backend implementations
   - Update CONST_EXPRESSION_ARITHMETIC_OPERATORS enum if needed

2. **Resolve ALIAS Operator**
   - Option A: Implement full stack (node class, backend method)
   - Option B: Remove from CONST_EXPRESSION_NODE_TYPES enum

3. **Add is_not_in() to ExpressionSystem**
   - Implement in all backends
   - Already has visitor support

### Priority 2: Promote Visitor-Only Operations to ExpressionSystem

These operations should be abstracted to ExpressionSystem for consistency:
1. String operations (12 operators)
2. Pattern operations (4 operators)
3. Temporal operations (22 operators)
4. Conditional operations (3 operators)
5. Unary/Truth operations (6 operators)

### Priority 3: Standardize Naming Convention

1. Decide on visitor method naming:
   - Keep _B_* prefix for boolean operations
   - Keep _* prefix for others
   - OR unify to single pattern (e.g., _B_* for all, or _ for all)

2. Document naming convention in architecture guide

### Priority 4: Remove Unimplemented Enums

If not planning to implement:
1. Remove XOR_EXCLUSIVE and XOR_PARITY from CONST_EXPRESSION_LOGICAL_OPERATORS
2. Remove ALIAS from CONST_EXPRESSION_NODE_TYPES or implement it

### Priority 5: Create Protocol Definitions

Create formal protocol definitions (or ABCs) for each operation category to:
1. Make the expected interface explicit
2. Support type checking and IDE autocomplete
3. Document what each backend must implement

---

## Conclusion

The enums in constants.py are well-designed as a **single source of truth** for operation definitions. However, there are significant gaps between what's defined in enums and what's actually abstracted in the ExpressionSystem interface.

The system works because visitor-level implementations handle the undefined operations, but this creates architectural inconsistency and makes it harder to add new backends.

**Key action:** Extend ExpressionSystem to include String, Pattern, Temporal, Conditional, and Unary operation protocols. This will ensure:
- Complete abstraction layer for all operations
- Easier backend implementation
- Better type safety and documentation
- True alignment between enums and implementation
