# ExpressionSystem Refactoring Roadmap

**Date:** 2025-01-09
**Status:** Planning - Detailed Implementation Plan
**Goal:** Transform monolithic ExpressionSystem backends into protocol-based mixins

---

## Overview

This document provides a detailed, phase-by-phase implementation plan for refactoring the ExpressionSystem architecture from god classes to focused protocol mixins.

**Estimated Total Duration:** 3-4 weeks
**Risk Level:** Medium (mitigated by incremental approach and comprehensive testing)
**Breaking Changes:** None for external users (internal refactoring only)

---

## Phase 1: Complete ABC Interface

**Duration:** 1-2 days
**Risk:** Low (additive change)
**Dependencies:** None

### Goals

1. Fix interface drift in ExpressionSystem base class
2. Document complete interface (all 60+ methods)
3. Enable type checking to verify backend completeness

### Tasks

#### Task 1.1: Audit Current Abstract Methods
- [ ] Read `core/expression_system/base.py`
- [ ] List all currently declared abstract methods (expected: 19)
- [ ] Compare against actual implementation methods in Polars/Narwhals/Ibis
- [ ] Create list of missing abstract method declarations (expected: 49)

#### Task 1.2: Add Missing Abstract Methods
- [ ] Add arithmetic methods (subtract, multiply, divide, modulo, power, floor_divide)
- [ ] Add all string operations (12 methods)
- [ ] Add all pattern operations (4 methods)
- [ ] Add all conditional operations (3 methods)
- [ ] Add all temporal operations (20+ methods)
- [ ] Organize methods by category with clear comment sections
- [ ] Add comprehensive docstrings for each method

#### Task 1.3: Verify Completeness
- [ ] Run `hatch run mypy:check` to verify type checking
- [ ] Ensure all three backends (Polars, Narwhals, Ibis) still pass type checks
- [ ] Fix any type errors revealed by complete interface

#### Task 1.4: Update Documentation
- [ ] Update docstrings in ExpressionSystem base class
- [ ] Document expected behavior for each method
- [ ] Note backend-specific differences (e.g., modulo semantics)

### Success Criteria

- ✅ ExpressionSystem declares all 60+ abstract methods
- ✅ Methods organized by category
- ✅ All backends pass type checking
- ✅ Comprehensive docstrings added
- ✅ Zero test failures

### Deliverables

- Updated `core/expression_system/base.py` (from 309 lines to ~600 lines)
- Type checking passes for all backends
- Git commit: "Complete ExpressionSystem abstract interface"

---

## Phase 2: Define Protocol Architecture

**Duration:** 2-3 days
**Risk:** Low (no behavioral changes)
**Dependencies:** Phase 1 complete

### Goals

1. Create protocol interface definitions
2. Establish foundation for mixin extraction
3. Enable structural typing

### Tasks

#### Task 2.1: Create Directory Structure
- [ ] Create `src/mountainash_expressions/backends/protocols/`
- [ ] Add `__init__.py` with protocol exports
- [ ] Create placeholder files for 8 protocols

#### Task 2.2: Define Core Protocol
- [ ] Create `backends/protocols/core_protocol.py`
- [ ] Define `CoreBackend` protocol with `col()`, `lit()`
- [ ] Add `@runtime_checkable` decorator
- [ ] Add comprehensive docstrings with examples

#### Task 2.3: Define Comparison Protocol
- [ ] Create `backends/protocols/comparison_protocol.py`
- [ ] Define `ComparisonBackend` protocol
- [ ] Implement: eq(), ne(), gt(), lt(), ge(), le()
- [ ] Add docstrings and examples

#### Task 2.4: Define Logical Protocol
- [ ] Create `backends/protocols/logical_protocol.py`
- [ ] Define `LogicalBackend` protocol
- [ ] Implement: and_(), or_(), not_()

#### Task 2.5: Define Arithmetic Protocol
- [ ] Create `backends/protocols/arithmetic_protocol.py`
- [ ] Define `ArithmeticBackend` protocol
- [ ] Implement: add(), subtract(), multiply(), divide(), modulo(), power(), floor_divide()
- [ ] Document modulo semantic differences across backends

#### Task 2.6: Define String Protocol
- [ ] Create `backends/protocols/string_protocol.py`
- [ ] Define `StringBackend` protocol
- [ ] Implement all 12 string operations
- [ ] Add detailed docstrings

#### Task 2.7: Define Pattern Protocol
- [ ] Create `backends/protocols/pattern_protocol.py`
- [ ] Define `PatternBackend` protocol
- [ ] Implement: pattern_like(), pattern_regex_match(), pattern_regex_contains(), pattern_regex_replace()

#### Task 2.8: Define Conditional Protocol
- [ ] Create `backends/protocols/conditional_protocol.py`
- [ ] Define `ConditionalBackend` protocol
- [ ] Implement: conditional_when(), conditional_coalesce(), conditional_fill_null()

#### Task 2.9: Define Temporal Protocol
- [ ] Create `backends/protocols/temporal_protocol.py`
- [ ] Define `TemporalBackend` protocol
- [ ] Implement all 20+ temporal operations
- [ ] Organize into extraction, arithmetic, difference, utility sections

#### Task 2.10: Protocol Verification
- [ ] Create test file to verify backends satisfy protocols
- [ ] Use `isinstance(backend, ProtocolName)` for runtime checking
- [ ] Verify all three backends pass protocol checks

### Success Criteria

- ✅ 8 protocol files created with complete interfaces
- ✅ All protocols have `@runtime_checkable` decorator
- ✅ Comprehensive docstrings with examples
- ✅ Current backends satisfy all protocols (verified via isinstance checks)
- ✅ Zero test failures

### Deliverables

- 8 new protocol definition files (~100-300 lines each)
- Updated `backends/protocols/__init__.py` with exports
- Protocol verification test
- Git commit: "Define protocol architecture for backend operations"

---

## Phase 3: Extract Polars Backend Mixins

**Duration:** 4-5 days
**Risk:** Medium (refactoring existing code)
**Dependencies:** Phase 2 complete

### Goals

1. Create first backend mixin implementation (template for others)
2. Reduce PolarsExpressionSystem from 663 lines to ~100 lines
3. Verify all tests still pass

### Tasks

#### Task 3.1: Create Mixin Directory
- [ ] Create `backends/polars/mixins/`
- [ ] Add `__init__.py` with mixin exports

#### Task 3.2: Extract PolarsCoreMixin
- [ ] Create `polars_core_mixin.py`
- [ ] Move `col()` and `lit()` from PolarsExpressionSystem
- [ ] Add type hints
- [ ] Run tests to verify no breakage

#### Task 3.3: Extract PolarsComparisonMixin
- [ ] Create `polars_comparison_mixin.py`
- [ ] Move all 6 comparison methods
- [ ] Verify implements `ComparisonBackend` protocol
- [ ] Run tests

#### Task 3.4: Extract PolarsLogicalMixin
- [ ] Create `polars_logical_mixin.py`
- [ ] Move `and_()`, `or_()`, `not_()`
- [ ] Run tests

#### Task 3.5: Extract PolarsArithmeticMixin
- [ ] Create `polars_arithmetic_mixin.py`
- [ ] Move all 7 arithmetic methods
- [ ] Run tests

#### Task 3.6: Extract PolarsStringMixin
- [ ] Create `polars_string_mixin.py`
- [ ] Move all 12 string methods
- [ ] Verify implementations use `pl.Expr.str.*` correctly
- [ ] Run tests

#### Task 3.7: Extract PolarsPatternMixin
- [ ] Create `polars_pattern_mixin.py`
- [ ] Move all 4 pattern methods
- [ ] Run tests

#### Task 3.8: Extract PolarsConditionalMixin
- [ ] Create `polars_conditional_mixin.py`
- [ ] Move all 3 conditional methods
- [ ] Run tests

#### Task 3.9: Extract PolarsTemporalMixin
- [ ] Create `polars_temporal_mixin.py`
- [ ] Move all 20+ temporal methods
- [ ] This will be the largest mixin (~200 lines)
- [ ] Run tests

#### Task 3.10: Refactor PolarsExpressionSystem
- [ ] Update `polars_expression_system.py` to inherit from all 8 mixins
- [ ] Remove all method implementations (now in mixins)
- [ ] Keep only `backend_type` property and composition
- [ ] Verify file is now ~40-100 lines

#### Task 3.11: Full Test Suite
- [ ] Run `hatch run test:test` (full suite)
- [ ] Ensure all 703 tests pass
- [ ] No behavioral changes allowed
- [ ] Fix any failures

#### Task 3.12: Type Checking
- [ ] Run `hatch run mypy:check`
- [ ] Fix any type errors
- [ ] Ensure Protocol compliance

### Success Criteria

- ✅ PolarsExpressionSystem reduced from 663 → ~100 lines
- ✅ 8 focused mixins created (50-200 lines each)
- ✅ All 703 tests pass
- ✅ Type checking passes
- ✅ Each mixin implements corresponding protocol
- ✅ Zero behavioral changes

### Deliverables

- 8 new Polars mixin files
- Refactored `polars_expression_system.py`
- Updated `backends/polars/mixins/__init__.py`
- Git commit: "Refactor Polars backend to protocol mixins"

---

## Phase 4: Replicate for Narwhals and Ibis

**Duration:** 5-6 days (2-3 days per backend)
**Risk:** Medium
**Dependencies:** Phase 3 complete

### Goals

1. Apply mixin pattern to remaining backends
2. Achieve consistent architecture across all backends

### Tasks - Narwhals

#### Task 4.1: Create Narwhals Mixin Structure
- [ ] Create `backends/narwhals/mixins/`
- [ ] Add `__init__.py`

#### Task 4.2: Extract Narwhals Mixins (8 files)
- [ ] Extract narwhals_core_mixin.py
- [ ] Extract narwhals_comparison_mixin.py
- [ ] Extract narwhals_logical_mixin.py
- [ ] Extract narwhals_arithmetic_mixin.py
- [ ] Extract narwhals_string_mixin.py
- [ ] Extract narwhals_pattern_mixin.py
- [ ] Extract narwhals_conditional_mixin.py
- [ ] Extract narwhals_temporal_mixin.py

#### Task 4.3: Refactor NarwhalsExpressionSystem
- [ ] Update to inherit from all 8 mixins
- [ ] Remove all method implementations
- [ ] Verify ~40-100 lines

#### Task 4.4: Test Narwhals Backend
- [ ] Run full test suite
- [ ] Ensure all tests pass
- [ ] Fix any failures

### Tasks - Ibis

#### Task 4.5: Create Ibis Mixin Structure
- [ ] Create `backends/ibis/mixins/`
- [ ] Add `__init__.py`

#### Task 4.6: Extract Ibis Mixins (8 files)
- [ ] Extract ibis_core_mixin.py
- [ ] Extract ibis_comparison_mixin.py
- [ ] Extract ibis_logical_mixin.py
- [ ] Extract ibis_arithmetic_mixin.py
- [ ] Extract ibis_string_mixin.py
- [ ] Extract ibis_pattern_mixin.py
- [ ] Extract ibis_conditional_mixin.py
- [ ] Extract ibis_temporal_mixin.py
- [ ] Note: Ibis may have more backend-specific logic (SQL translation)

#### Task 4.7: Refactor IbisExpressionSystem
- [ ] Update to inherit from all 8 mixins
- [ ] Remove all method implementations
- [ ] Verify ~40-100 lines

#### Task 4.8: Test Ibis Backend
- [ ] Run full test suite
- [ ] Ensure all tests pass
- [ ] Fix any failures

### Success Criteria

- ✅ NarwhalsExpressionSystem: 734 → ~100 lines
- ✅ IbisExpressionSystem: 883 → ~100 lines
- ✅ 8 focused mixins per backend
- ✅ All 703 tests pass after each backend refactoring
- ✅ Type checking passes
- ✅ Protocol compliance verified

### Deliverables

- 16 new mixin files (8 for Narwhals, 8 for Ibis)
- Refactored expression_system.py files for both backends
- Git commits:
  - "Refactor Narwhals backend to protocol mixins"
  - "Refactor Ibis backend to protocol mixins"

---

## Phase 5: Extract Shared Base Mixins

**Duration:** 2-3 days
**Risk:** Low-Medium
**Dependencies:** Phase 4 complete

### Goals

1. Identify truly identical code across backends
2. Extract shared mixins to eliminate duplication
3. Improve DRY principle adherence

### Tasks

#### Task 5.1: Analyze Backend Similarities
- [ ] Compare Polars vs Narwhals implementations
- [ ] Compare Polars vs Ibis implementations
- [ ] Identify methods with identical implementations
- [ ] Expected candidates: comparison (operator overloading), arithmetic (operator overloading)

#### Task 5.2: Create Common Mixin Directory
- [ ] Create `backends/common/mixins/`
- [ ] Add `__init__.py`

#### Task 5.3: Extract OperatorOverloadingComparisonMixin
- [ ] Create `operator_overloading_comparison_mixin.py`
- [ ] Implement all 6 comparison operations using Python operators
- [ ] Works for: Polars, Narwhals, Ibis (all support operator overloading)

#### Task 5.4: Extract OperatorOverloadingArithmeticMixin
- [ ] Create `operator_overloading_arithmetic_mixin.py`
- [ ] Implement arithmetic operations using Python operators
- [ ] May need backend-specific overrides for some operations

#### Task 5.5: Extract NullHandlingMixin (if applicable)
- [ ] Identify common null handling patterns
- [ ] Extract if truly identical across backends

#### Task 5.6: Update Backend Mixins to Use Shared Mixins
- [ ] Update PolarsComparisonMixin to inherit from shared mixin
- [ ] Update NarwhalsComparisonMixin to inherit from shared mixin
- [ ] Update IbisComparisonMixin to inherit from shared mixin
- [ ] Similar for arithmetic if applicable

#### Task 5.7: Test All Backends
- [ ] Run full test suite for all backends
- [ ] Ensure no behavioral changes
- [ ] Fix any failures

### Success Criteria

- ✅ Shared mixins created in `backends/common/`
- ✅ Backend-specific mixins inherit from shared mixins where appropriate
- ✅ Code duplication reduced
- ✅ All 703 tests pass
- ✅ Type checking passes
- ✅ No behavioral changes

### Deliverables

- 2-3 shared base mixin files
- Updated backend-specific mixins (inherit from shared)
- Git commit: "Extract shared base mixins for code reuse"

---

## Phase 6: Migrate to Protocol Composition

**Duration:** 2-3 days
**Risk:** Medium (type system changes)
**Dependencies:** Phase 5 complete

### Goals

1. Replace ABC with Protocol composition
2. Enable structural typing
3. Complete architectural migration

### Tasks

#### Task 6.1: Create Protocol Composition Base
- [ ] Update `core/expression_system/base.py`
- [ ] Change from ABC to Protocol composition
- [ ] Inherit from all 8 protocols
- [ ] Keep `backend_type` property

#### Task 6.2: Update Type Hints Throughout Codebase
- [ ] Search for `ExpressionSystem` type hints
- [ ] Update visitor factory type annotations
- [ ] Update visitor __init__ type annotations
- [ ] Update any other references

#### Task 6.3: Remove ABC Imports
- [ ] Remove `from abc import ABC, abstractmethod`
- [ ] Add `from typing import Protocol, runtime_checkable`
- [ ] Update all decorators

#### Task 6.4: Verify Backend Protocol Compliance
- [ ] Runtime check: `isinstance(polars_backend, ExpressionSystem)`
- [ ] Runtime check: `isinstance(polars_backend, ComparisonBackend)`
- [ ] Verify for all 3 backends
- [ ] Ensure all pass

#### Task 6.5: Type Checking
- [ ] Run `hatch run mypy:check`
- [ ] Fix any type errors from Protocol migration
- [ ] Ensure type safety maintained

#### Task 6.6: Full Test Suite
- [ ] Run `hatch run test:test`
- [ ] Ensure all 703 tests pass
- [ ] No behavioral changes allowed

### Success Criteria

- ✅ ExpressionSystem is now Protocol composition
- ✅ No more ABC inheritance
- ✅ Structural typing enabled
- ✅ All backends satisfy protocols (runtime checked)
- ✅ Type checking passes
- ✅ All 703 tests pass
- ✅ Zero behavioral changes

### Deliverables

- Updated `core/expression_system/base.py` (ABC → Protocol)
- Updated type hints throughout codebase
- Git commit: "Migrate ExpressionSystem from ABC to Protocol composition"

---

## Phase 7: Documentation and Cleanup

**Duration:** 2-3 days
**Risk:** Low
**Dependencies:** Phase 6 complete

### Goals

1. Update all documentation
2. Clean up temporary files
3. Create alignment verification
4. Final testing

### Tasks

#### Task 7.1: Update CLAUDE.md
- [ ] Update architecture section with protocol mixins
- [ ] Update file structure documentation
- [ ] Add protocol architecture explanation
- [ ] Update line count statistics
- [ ] Add mixin organization details

#### Task 7.2: Create Alignment Verification Matrix
- [ ] Document final alignment (Nodes → Visitors → Protocols → Backends → API)
- [ ] Create verification checklist for new backends
- [ ] Document protocol compliance requirements

#### Task 7.3: Update Package Documentation
- [ ] Update README if applicable
- [ ] Update any architecture diagrams
- [ ] Add protocol documentation

#### Task 7.4: Clean Up Temporary Files
- [ ] Remove 5 `.tmp` files from boolean_mixins/
- [ ] Remove 16 backup files across project
- [ ] Clean up any test artifacts

#### Task 7.5: Final Comprehensive Testing
- [ ] Run full test suite: `hatch run test:test`
- [ ] Run type checking: `hatch run mypy:check`
- [ ] Run linting: `hatch run ruff:check`
- [ ] Generate coverage report
- [ ] Ensure 100% test pass rate

#### Task 7.6: Create Migration Guide
- [ ] Document how to add new backends
- [ ] Document how to add new operations
- [ ] Document protocol compliance verification
- [ ] Add examples

### Success Criteria

- ✅ CLAUDE.md fully updated
- ✅ Alignment matrix documented
- ✅ All temporary files removed
- ✅ All tests pass (703/703)
- ✅ Type checking passes
- ✅ Linting passes
- ✅ Documentation complete
- ✅ Migration guide created

### Deliverables

- Updated CLAUDE.md
- Alignment verification matrix
- Migration guide for new backends
- Clean codebase (no .tmp files)
- Git commit: "Complete protocol refactoring - update documentation and cleanup"

---

## Risk Mitigation

### Risk: Test Failures During Refactoring

**Probability:** Medium
**Impact:** High (blocks progress)

**Mitigation:**
- Test after EVERY task (not just phase)
- Keep changes small and incremental
- Can rollback to previous task if needed
- Use git commits liberally

### Risk: Type Checking Failures

**Probability:** Low
**Impact:** Medium

**Mitigation:**
- Run mypy after each major change
- Use type ignore comments only as last resort
- Fix type issues before proceeding

### Risk: Protocol Migration Breaking External Code

**Probability:** Low (internal refactoring)
**Impact:** High if external users exist

**Mitigation:**
- Package is internal to Mountain Ash ecosystem
- No external API changes
- Protocol migration is internal implementation detail

### Risk: Performance Regression from Mixin Composition

**Probability:** Very Low
**Impact:** Low

**Mitigation:**
- Python MRO handles multiple inheritance efficiently
- Mixin composition has negligible overhead
- Run performance tests if concerns arise

### Risk: Incomplete Protocol Definitions

**Probability:** Low
**Impact:** Medium

**Mitigation:**
- Comprehensive audit in Phase 1
- Protocol definitions based on working implementations
- Runtime checking verifies compliance

---

## Success Metrics

### Code Quality

- [ ] God classes eliminated (663-883 lines → ~100 lines)
- [ ] 24 focused mixins created (8 per backend)
- [ ] Code duplication reduced (shared base mixins)
- [ ] Clear separation of concerns

### Testing

- [ ] 703/703 tests passing (100%)
- [ ] No behavioral changes
- [ ] Type checking passes
- [ ] Linting passes

### Architecture

- [ ] 8 protocol interfaces defined
- [ ] Perfect alignment: Protocols ↔ Visitor Mixins
- [ ] Symmetric architecture (visitors and backends both use mixins)
- [ ] Complete interface documentation

### Maintainability

- [ ] Each mixin 50-200 lines (vs 663-883)
- [ ] Easy to locate operations (category-based)
- [ ] Easy to test (focused mixins)
- [ ] Easy to extend (add new mixin category)

---

## Rollback Plan

If major issues arise at any phase:

1. **Immediate:** Stop work, don't proceed to next task
2. **Assess:** Determine if issue is fixable or requires rollback
3. **Rollback:** Git revert to last known good commit (each task has commit)
4. **Analyze:** Understand what went wrong
5. **Adjust:** Update plan if needed
6. **Retry:** Attempt task again with fixes

**Key:** Frequent commits allow granular rollback without losing much work.

---

## Timeline Summary

| Phase | Duration | Dependencies | Risk |
|-------|----------|--------------|------|
| 1. Complete ABC Interface | 1-2 days | None | Low |
| 2. Define Protocols | 2-3 days | Phase 1 | Low |
| 3. Extract Polars Mixins | 4-5 days | Phase 2 | Medium |
| 4. Extract Narwhals/Ibis Mixins | 5-6 days | Phase 3 | Medium |
| 5. Extract Shared Mixins | 2-3 days | Phase 4 | Low-Medium |
| 6. Migrate to Protocol Composition | 2-3 days | Phase 5 | Medium |
| 7. Documentation & Cleanup | 2-3 days | Phase 6 | Low |
| **TOTAL** | **18-25 days** | Sequential | Medium |

**Estimated Calendar Time:** 3-4 weeks (accounting for testing delays, fixes, etc.)

---

## Post-Refactoring Benefits

### For Developers

- ✅ Easy to find operations (category-based organization)
- ✅ Easy to test (focused mixins)
- ✅ Easy to extend (add new category mixin)
- ✅ Clear patterns to follow

### For New Backends

- ✅ Implement 8 small mixins instead of 1 large class
- ✅ Clear checklist (8 protocols to satisfy)
- ✅ Can reuse shared base mixins
- ✅ Type checking verifies completeness

### For Architecture

- ✅ Symmetric design (visitors and backends match)
- ✅ Protocol-based (structural typing, loose coupling)
- ✅ DRY principle (shared mixins)
- ✅ Single Responsibility Principle (each mixin = one category)

---

**Ready to proceed?** Start with Phase 1, Task 1.1!
