# Backend Verification Checklist

**Date:** 2025-01-09
**Purpose:** Ensure complete and correct backend implementations
**Use:** Verify existing backends and guide new backend creation

---

## Overview

This checklist ensures that all backend implementations:
1. Implement all required protocol methods
2. Align with visitor mixin categories
3. Pass all tests
4. Satisfy type checking
5. Follow architectural patterns

---

## Pre-Refactoring Checklist (Current State)

Use this to verify god class backends before refactoring.

### ExpressionSystem God Class Completeness

Backend: _________________

- [ ] **Core Operations (2)**
  - [ ] `col(name, **kwargs)` - Column reference
  - [ ] `lit(value, **kwargs)` - Literal value

- [ ] **Comparison Operations (6)**
  - [ ] `eq(left, right)` - Equality (==)
  - [ ] `ne(left, right)` - Inequality (!=)
  - [ ] `gt(left, right)` - Greater than (>)
  - [ ] `lt(left, right)` - Less than (<)
  - [ ] `ge(left, right)` - Greater or equal (>=)
  - [ ] `le(left, right)` - Less or equal (<=)

- [ ] **Logical Operations (3)**
  - [ ] `and_(left, right)` - Logical AND
  - [ ] `or_(left, right)` - Logical OR
  - [ ] `not_(operand)` - Logical NOT

- [ ] **Collection Operations (1)**
  - [ ] `is_in(operand, values)` - Membership test

- [ ] **Null Operations (1)**
  - [ ] `is_null(operand)` - Null check

- [ ] **Type Operations (1)**
  - [ ] `cast(operand, dtype)` - Type conversion

- [ ] **Arithmetic Operations (7)**
  - [ ] `add(left, right)` - Addition (+)
  - [ ] `subtract(left, right)` - Subtraction (-)
  - [ ] `multiply(left, right)` - Multiplication (*)
  - [ ] `divide(left, right)` - Division (/)
  - [ ] `modulo(left, right)` - Modulo (%)
  - [ ] `power(left, right)` - Exponentiation (**)
  - [ ] `floor_divide(left, right)` - Floor division (//)

- [ ] **String Operations (12)**
  - [ ] `str_upper(operand)` - Convert to uppercase
  - [ ] `str_lower(operand)` - Convert to lowercase
  - [ ] `str_trim(operand)` - Trim whitespace
  - [ ] `str_ltrim(operand)` - Left trim
  - [ ] `str_rtrim(operand)` - Right trim
  - [ ] `str_substring(operand, start, end)` - Extract substring
  - [ ] `str_concat(*operands)` - Concatenate strings
  - [ ] `str_length(operand)` - String length
  - [ ] `str_replace(operand, pattern, replacement)` - Replace substring
  - [ ] `str_contains(operand, substring)` - Contains check
  - [ ] `str_starts_with(operand, prefix)` - Starts with check
  - [ ] `str_ends_with(operand, suffix)` - Ends with check

- [ ] **Pattern Operations (4)**
  - [ ] `pattern_like(operand, pattern)` - SQL LIKE matching
  - [ ] `pattern_regex_match(operand, pattern)` - Full regex match
  - [ ] `pattern_regex_contains(operand, pattern)` - Regex contains
  - [ ] `pattern_regex_replace(operand, pattern, replacement)` - Regex replace

- [ ] **Conditional Operations (3)**
  - [ ] `conditional_when(condition, then_value, else_value)` - If-then-else
  - [ ] `conditional_coalesce(*operands)` - First non-null
  - [ ] `conditional_fill_null(operand, fill_value)` - Fill nulls

- [ ] **Temporal Operations (23)**
  - [ ] `temporal_year(operand)` - Extract year
  - [ ] `temporal_month(operand)` - Extract month
  - [ ] `temporal_day(operand)` - Extract day
  - [ ] `temporal_hour(operand)` - Extract hour
  - [ ] `temporal_minute(operand)` - Extract minute
  - [ ] `temporal_second(operand)` - Extract second
  - [ ] `temporal_weekday(operand)` - Extract weekday
  - [ ] `temporal_week(operand)` - Extract week number
  - [ ] `temporal_quarter(operand)` - Extract quarter
  - [ ] `temporal_add_days(operand, days)` - Add days
  - [ ] `temporal_add_months(operand, months)` - Add months
  - [ ] `temporal_add_years(operand, years)` - Add years
  - [ ] `temporal_add_hours(operand, hours)` - Add hours
  - [ ] `temporal_add_minutes(operand, minutes)` - Add minutes
  - [ ] `temporal_add_seconds(operand, seconds)` - Add seconds
  - [ ] `temporal_diff_days(left, right)` - Days difference
  - [ ] `temporal_diff_months(left, right)` - Months difference
  - [ ] `temporal_diff_years(left, right)` - Years difference
  - [ ] `temporal_diff_hours(left, right)` - Hours difference
  - [ ] `temporal_diff_minutes(left, right)` - Minutes difference
  - [ ] `temporal_diff_seconds(left, right)` - Seconds difference
  - [ ] `temporal_truncate(operand, unit)` - Truncate to unit
  - [ ] `temporal_offset_by(operand, offset)` - Offset by duration

**Total Methods:** 60+ (should match implementation)

---

## Post-Refactoring Checklist (Protocol Mixins)

Use this to verify mixin-based backends after refactoring.

### Mixin Structure Verification

Backend: _________________

- [ ] **Directory Structure**
  - [ ] `backends/<backend_name>/mixins/` directory exists
  - [ ] `backends/<backend_name>/mixins/__init__.py` exists
  - [ ] All 8 mixin files present
  - [ ] `backends/<backend_name>/expression_system/<backend_name>_expression_system.py` updated

- [ ] **Mixin Files Created (8 required)**
  - [ ] `<backend>_core_mixin.py`
  - [ ] `<backend>_comparison_mixin.py`
  - [ ] `<backend>_logical_mixin.py`
  - [ ] `<backend>_arithmetic_mixin.py`
  - [ ] `<backend>_string_mixin.py`
  - [ ] `<backend>_pattern_mixin.py`
  - [ ] `<backend>_conditional_mixin.py`
  - [ ] `<backend>_temporal_mixin.py`

### CoreBackend Protocol Compliance

- [ ] **Methods Implemented (2)**
  - [ ] `col(name, **kwargs) -> BackendExpr`
  - [ ] `lit(value, **kwargs) -> BackendExpr`

- [ ] **Return Types Correct**
  - [ ] Returns backend-specific expression type (pl.Expr, nw.Expr, ir.Expr, etc.)

- [ ] **Type Hints Present**
  - [ ] All parameters have type hints
  - [ ] Return types specified

- [ ] **Docstrings Present**
  - [ ] Each method has docstring
  - [ ] Describes parameters and return value

### ComparisonBackend Protocol Compliance

- [ ] **Methods Implemented (6)**
  - [ ] `eq(left, right) -> BackendExpr`
  - [ ] `ne(left, right) -> BackendExpr`
  - [ ] `gt(left, right) -> BackendExpr`
  - [ ] `lt(left, right) -> BackendExpr`
  - [ ] `ge(left, right) -> BackendExpr`
  - [ ] `le(left, right) -> BackendExpr`

- [ ] **Behavior Verification**
  - [ ] Comparisons return boolean expressions
  - [ ] Handle null values correctly per backend semantics
  - [ ] Tests pass for comparison operations

### LogicalBackend Protocol Compliance

- [ ] **Methods Implemented (3)**
  - [ ] `and_(left, right) -> BackendExpr`
  - [ ] `or_(left, right) -> BackendExpr`
  - [ ] `not_(operand) -> BackendExpr`

- [ ] **Behavior Verification**
  - [ ] Logical operations return boolean expressions
  - [ ] Short-circuit evaluation if supported by backend
  - [ ] Tests pass for logical operations

### ArithmeticBackend Protocol Compliance

- [ ] **Methods Implemented (7)**
  - [ ] `add(left, right) -> BackendExpr`
  - [ ] `subtract(left, right) -> BackendExpr`
  - [ ] `multiply(left, right) -> BackendExpr`
  - [ ] `divide(left, right) -> BackendExpr`
  - [ ] `modulo(left, right) -> BackendExpr`
  - [ ] `power(left, right) -> BackendExpr`
  - [ ] `floor_divide(left, right) -> BackendExpr`

- [ ] **Behavior Verification**
  - [ ] Division returns float (not integer division)
  - [ ] Modulo semantics documented (Python vs SQL style)
  - [ ] Handle division by zero per backend
  - [ ] Tests pass for arithmetic operations

### StringBackend Protocol Compliance

- [ ] **Methods Implemented (12)**
  - [ ] `str_upper(operand) -> BackendExpr`
  - [ ] `str_lower(operand) -> BackendExpr`
  - [ ] `str_trim(operand) -> BackendExpr`
  - [ ] `str_ltrim(operand) -> BackendExpr`
  - [ ] `str_rtrim(operand) -> BackendExpr`
  - [ ] `str_substring(operand, start, end) -> BackendExpr`
  - [ ] `str_concat(*operands) -> BackendExpr`
  - [ ] `str_length(operand) -> BackendExpr`
  - [ ] `str_replace(operand, pattern, replacement) -> BackendExpr`
  - [ ] `str_contains(operand, substring) -> BackendExpr`
  - [ ] `str_starts_with(operand, prefix) -> BackendExpr`
  - [ ] `str_ends_with(operand, suffix) -> BackendExpr`

- [ ] **Behavior Verification**
  - [ ] String methods handle nulls correctly
  - [ ] Substring uses 0-based indexing consistently
  - [ ] Tests pass for string operations

### PatternBackend Protocol Compliance

- [ ] **Methods Implemented (4)**
  - [ ] `pattern_like(operand, pattern) -> BackendExpr`
  - [ ] `pattern_regex_match(operand, pattern) -> BackendExpr`
  - [ ] `pattern_regex_contains(operand, pattern) -> BackendExpr`
  - [ ] `pattern_regex_replace(operand, pattern, replacement) -> BackendExpr`

- [ ] **Behavior Verification**
  - [ ] LIKE pattern uses SQL semantics (%, _)
  - [ ] Regex uses backend's regex flavor
  - [ ] Tests pass for pattern operations

### ConditionalBackend Protocol Compliance

- [ ] **Methods Implemented (3)**
  - [ ] `conditional_when(condition, then_value, else_value) -> BackendExpr`
  - [ ] `conditional_coalesce(*operands) -> BackendExpr`
  - [ ] `conditional_fill_null(operand, fill_value) -> BackendExpr`

- [ ] **Behavior Verification**
  - [ ] When-then-else handles nulls correctly
  - [ ] Coalesce returns first non-null
  - [ ] Fill null replaces only nulls
  - [ ] Tests pass for conditional operations

### TemporalBackend Protocol Compliance

- [ ] **Extraction Methods (9)**
  - [ ] `temporal_year(operand) -> BackendExpr`
  - [ ] `temporal_month(operand) -> BackendExpr`
  - [ ] `temporal_day(operand) -> BackendExpr`
  - [ ] `temporal_hour(operand) -> BackendExpr`
  - [ ] `temporal_minute(operand) -> BackendExpr`
  - [ ] `temporal_second(operand) -> BackendExpr`
  - [ ] `temporal_weekday(operand) -> BackendExpr`
  - [ ] `temporal_week(operand) -> BackendExpr`
  - [ ] `temporal_quarter(operand) -> BackendExpr`

- [ ] **Addition Methods (6)**
  - [ ] `temporal_add_days(operand, days) -> BackendExpr`
  - [ ] `temporal_add_months(operand, months) -> BackendExpr`
  - [ ] `temporal_add_years(operand, years) -> BackendExpr`
  - [ ] `temporal_add_hours(operand, hours) -> BackendExpr`
  - [ ] `temporal_add_minutes(operand, minutes) -> BackendExpr`
  - [ ] `temporal_add_seconds(operand, seconds) -> BackendExpr`

- [ ] **Difference Methods (6)**
  - [ ] `temporal_diff_days(left, right) -> BackendExpr`
  - [ ] `temporal_diff_months(left, right) -> BackendExpr`
  - [ ] `temporal_diff_years(left, right) -> BackendExpr`
  - [ ] `temporal_diff_hours(left, right) -> BackendExpr`
  - [ ] `temporal_diff_minutes(left, right) -> BackendExpr`
  - [ ] `temporal_diff_seconds(left, right) -> BackendExpr`

- [ ] **Utility Methods (2)**
  - [ ] `temporal_truncate(operand, unit) -> BackendExpr`
  - [ ] `temporal_offset_by(operand, offset) -> BackendExpr`

- [ ] **Behavior Verification**
  - [ ] Weekday: 0=Monday, 6=Sunday (ISO standard)
  - [ ] Calendar-aware operations handle month/year boundaries
  - [ ] Tests pass for temporal operations

---

## Backend Composition Verification

Backend: _________________

- [ ] **ExpressionSystem Composition**
  - [ ] Inherits from all 8 category mixins
  - [ ] No method implementations (all in mixins)
  - [ ] Only has `backend_type` property
  - [ ] File size: 30-100 lines (vs original 663-883)

- [ ] **Example:**
  ```python
  class MyBackendExpressionSystem(
      MyBackendCoreMixin,
      MyBackendComparisonMixin,
      MyBackendLogicalMixin,
      MyBackendArithmeticMixin,
      MyBackendStringMixin,
      MyBackendPatternMixin,
      MyBackendConditionalMixin,
      MyBackendTemporalMixin,
  ):
      @property
      def backend_type(self):
          return CONST_VISITOR_BACKENDS.MY_BACKEND
  ```

---

## Protocol Runtime Verification

Backend: _________________

- [ ] **Runtime Protocol Checks Pass**
  ```python
  backend = MyBackendExpressionSystem()

  # Core protocols
  assert isinstance(backend, CoreBackend)
  assert isinstance(backend, ComparisonBackend)
  assert isinstance(backend, LogicalBackend)
  assert isinstance(backend, ArithmeticBackend)
  assert isinstance(backend, StringBackend)
  assert isinstance(backend, PatternBackend)
  assert isinstance(backend, ConditionalBackend)
  assert isinstance(backend, TemporalBackend)

  # Complete system
  assert isinstance(backend, ExpressionSystem)
  ```

---

## Type Checking Verification

Backend: _________________

- [ ] **Type Hints Complete**
  - [ ] All method parameters have type hints
  - [ ] All return types specified
  - [ ] Backend-specific expression types used (pl.Expr, nw.Expr, etc.)

- [ ] **MyPy Passes**
  - [ ] Run: `hatch run mypy:check`
  - [ ] No type errors for this backend
  - [ ] Protocol compliance verified

---

## Test Suite Verification

Backend: _________________

- [ ] **Cross-Backend Tests Pass**
  - [ ] All comparison tests pass
  - [ ] All logical tests pass
  - [ ] All arithmetic tests pass
  - [ ] All string tests pass
  - [ ] All pattern tests pass
  - [ ] All conditional tests pass
  - [ ] All temporal tests pass

- [ ] **Backend-Specific Tests**
  - [ ] Backend detection works
  - [ ] Visitor factory creates correct visitor
  - [ ] ExpressionBuilder integration works

- [ ] **Test Statistics**
  - [ ] Total tests: _____ / 703
  - [ ] Passing: _____ (should be 100%)
  - [ ] Failing: _____ (should be 0)
  - [ ] Skipped: _____ (document reason)
  - [ ] xfail: _____ (document known issues)

---

## Documentation Verification

Backend: _________________

- [ ] **Docstrings**
  - [ ] Every mixin class has docstring
  - [ ] Every method has docstring
  - [ ] Parameters documented
  - [ ] Return values documented
  - [ ] Examples provided where helpful

- [ ] **CLAUDE.md Updated**
  - [ ] Backend listed in supported backends
  - [ ] Mixin structure documented
  - [ ] Known issues/limitations noted

- [ ] **Protocol Documentation**
  - [ ] Backend satisfies all 8 protocols
  - [ ] Any protocol deviations documented
  - [ ] Backend-specific behavior noted

---

## Alignment Verification

Backend: _________________

- [ ] **Node Alignment**
  - [ ] Every expression node type has corresponding operations
  - [ ] No missing operations for supported nodes

- [ ] **Visitor Alignment**
  - [ ] Every visitor mixin category has corresponding backend mixin
  - [ ] Method names align (visitor `_add()` ↔ backend `add()`)

- [ ] **Protocol Alignment**
  - [ ] Each backend mixin implements exactly one protocol
  - [ ] No missing protocol methods
  - [ ] No extra methods (unless backend-specific)

- [ ] **Public API Alignment**
  - [ ] All ExpressionBuilder methods work with this backend
  - [ ] Helper functions (filter, select, with_columns) work
  - [ ] Natural language temporal helpers work

---

## Shared Mixin Usage Verification

Backend: _________________

- [ ] **Can Use Shared Mixins?**
  - [ ] Comparison operations via operator overloading? → Use OperatorOverloadingComparisonMixin
  - [ ] Arithmetic operations via operator overloading? → Use OperatorOverloadingArithmeticMixin
  - [ ] Standard null handling? → Use NullHandlingMixin (if exists)

- [ ] **Inheritance Correct**
  - [ ] Backend mixin inherits from shared mixin if applicable
  - [ ] Backend mixin overrides only what's needed
  - [ ] Tests still pass with shared mixins

---

## Performance Verification

Backend: _________________

- [ ] **No Performance Regression**
  - [ ] Mixin composition adds negligible overhead
  - [ ] Expression compilation time similar to pre-refactoring
  - [ ] Query execution time unchanged

- [ ] **Memory Usage**
  - [ ] No memory leaks
  - [ ] Expression object sizes similar

---

## Integration Verification

Backend: _________________

- [ ] **Visitor Factory Integration**
  - [ ] Backend auto-detected from DataFrame type
  - [ ] Correct ExpressionSystem instantiated
  - [ ] Visitor creation works

- [ ] **ExpressionBuilder Integration**
  - [ ] All builder methods work
  - [ ] Compile produces backend expressions
  - [ ] Filter/select/with_columns work

- [ ] **End-to-End Test**
  ```python
  import mountainash_expressions as ma

  # Create expression
  expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))

  # Compile for backend
  backend_expr = expr.compile(my_dataframe)

  # Execute
  result = my_dataframe.filter(backend_expr)

  # Verify result
  assert result is not None
  assert len(result) > 0  # Assuming some matches
  ```

---

## New Backend Creation Checklist

Use this when implementing a brand new backend.

Backend Name: _________________
Backend Type: _________________ (e.g., pl.Expr, nw.Expr, ir.Expr)

### Phase 1: Setup

- [ ] Create `backends/<backend_name>/` directory
- [ ] Create `backends/<backend_name>/mixins/` directory
- [ ] Create `backends/<backend_name>/mixins/__init__.py`
- [ ] Create `backends/<backend_name>/expression_system/` directory
- [ ] Create `backends/<backend_name>/expression_system/__init__.py`

### Phase 2: Implement Mixins (8 required)

For each mixin:
- [ ] Create `<backend>_core_mixin.py` - implement CoreBackend protocol
- [ ] Create `<backend>_comparison_mixin.py` - implement ComparisonBackend protocol
- [ ] Create `<backend>_logical_mixin.py` - implement LogicalBackend protocol
- [ ] Create `<backend>_arithmetic_mixin.py` - implement ArithmeticBackend protocol
- [ ] Create `<backend>_string_mixin.py` - implement StringBackend protocol
- [ ] Create `<backend>_pattern_mixin.py` - implement PatternBackend protocol
- [ ] Create `<backend>_conditional_mixin.py` - implement ConditionalBackend protocol
- [ ] Create `<backend>_temporal_mixin.py` - implement TemporalBackend protocol

### Phase 3: Compose ExpressionSystem

- [ ] Create `<backend>_expression_system.py`
- [ ] Inherit from all 8 mixins
- [ ] Implement `backend_type` property
- [ ] Add docstring
- [ ] Verify file is 30-100 lines

### Phase 4: Register Backend

- [ ] Add backend constant to `CONST_VISITOR_BACKENDS`
- [ ] Add backend detection to `visitor_factory.py`
- [ ] Register ExpressionSystem in factory

### Phase 5: Create Tests

- [ ] Add backend DataFrame fixtures to `conftest.py`
- [ ] Add backend to cross-backend test parametrization
- [ ] Run test suite
- [ ] Fix failures

### Phase 6: Documentation

- [ ] Add backend to CLAUDE.md supported backends list
- [ ] Document any backend-specific behavior
- [ ] Document known limitations
- [ ] Add usage examples

---

## Final Verification Checklist

Before marking refactoring complete:

- [ ] **All Backends Verified**
  - [ ] Polars: All checklists passed
  - [ ] Narwhals: All checklists passed
  - [ ] Ibis: All checklists passed

- [ ] **All Tests Passing**
  - [ ] 703/703 tests pass
  - [ ] Zero failures
  - [ ] Skipped/xfail documented

- [ ] **Type Checking Passing**
  - [ ] MyPy passes for all backends
  - [ ] Protocol compliance verified

- [ ] **Documentation Complete**
  - [ ] CLAUDE.md updated
  - [ ] All protocols documented
  - [ ] Alignment matrix complete

- [ ] **Code Quality**
  - [ ] Linting passes
  - [ ] No .tmp files remaining
  - [ ] No god classes (all files < 300 lines)

- [ ] **Architecture Goals Met**
  - [ ] Symmetric architecture achieved
  - [ ] Protocol-based design complete
  - [ ] Shared mixins extracted
  - [ ] DRY principle followed

---

**Refactoring Complete!** ✅
