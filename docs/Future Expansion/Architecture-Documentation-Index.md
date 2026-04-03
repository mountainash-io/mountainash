# Architecture Documentation Index

**Date:** 2025-01-09
**Status:** Documentation Complete - Ready for Review
**Scope:** Complete architectural review and planning for mountainash-expressions
**Latest Update:** Refined to unified protocol architecture (shared base protocols)

---

## Overview

This documentation suite provides comprehensive architectural analysis and planning for mountainash-expressions, covering both **ExpressionSystem backend refactoring** and **ExpressionNode structure optimization** for the 9-phase expansion roadmap.

**Key Architectural Innovation:** Unified protocol architecture using shared base operations protocols, removing artificial separation between visitor and backend interfaces.

---

## Documentation Structure

### Part 1: ExpressionSystem Backend Refactoring

**Problem:** Backend god classes (663-883 lines with 68+ methods each)
**Solution:** Protocol-based mixin architecture with unified shared base protocols
**Impact:** Major maintainability improvement, type-safe alignment, removes legacy artifacts, zero external API changes

#### Documents:

1. **ExpressionSystem-Refactoring-Index.md**
   - Navigation guide for refactoring documentation
   - Quick reference tables
   - Implementation path summary
   - 📍 **START HERE** for backend refactoring

2. **Architectural-Review-ExpressionSystem-Refactoring.md** (18KB)
   - God class problem analysis
   - Asymmetric architecture identification
   - ABC vs Protocol trade-offs
   - Complete method inventory (60+ methods)

3. **Alignment-Matrix.md** (25KB)
   - Public API → Nodes → Visitors → Backends mapping
   - 100% coverage verification
   - Proposed 8:8:8 protocol alignment

4. **Protocol-Architecture-Proposal.md** (22KB)
   - 8 backend protocol definitions with code examples
   - Backend mixin implementation examples
   - Shared base mixin strategy
   - Complete directory structure

5. **Visitor-Backend-Protocol-Alignment.md** (40KB)
   - Initial dual protocol analysis (8 visitor + 8 backend)
   - Identified visitor method sprawl problem
   - Historical: Led to unified protocol refinement

6. **Unified-Protocol-Architecture.md** (40KB) ⭐⭐
   - **REFINED ARCHITECTURAL APPROACH**
   - Single set of base operations protocols (8)
   - Visitor protocols extend base protocols (8)
   - Total: 16 protocols, but conceptually unified
   - Removes `_B_` prefix legacy artifact
   - Type-safe compiler-enforced alignment
   - 📍 **ESSENTIAL** - this is the approved architecture

7. **Refactoring-Roadmap.md** (28KB)
   - 7-phase implementation plan (3-4 weeks)
   - Needs update for unified protocol approach
   - Will include visitor method renaming phase
   - Detailed tasks with success criteria
   - Risk mitigation strategies
   - Testing requirements

8. **Backend-Verification-Checklist.md** (18KB)
   - Pre/post-refactoring checklists
   - Protocol compliance verification
   - New backend creation guide
   - Integration testing checklist

---

### Part 2: ExpressionNode Structure Optimization

**Problem:** Current structure (24 types, 65 ops) needs expansion for roadmap (170+ ops)
**Solution:** Strategic node splitting and new type additions
**Impact:** Scalable architecture maintaining design principles

#### Documents:

9. **ExpressionNode-Architecture-Review.md** (45KB) ⭐
   - **Comprehensive node structure analysis**
   - Current vs planned coverage (65 → 170+ operations)
   - Node granularity assessment
   - Critical structural changes needed:
     - Temporal node split (Phase 4) - REQUIRED
     - Window infrastructure (Phase 8) - MAJOR
     - Backend capability system - RECOMMENDED
   - 8 new node types detailed
   - Design principles codified
   - File organization proposed
   - 📍 **START HERE** for node architecture

10. **Core-Node-Structure-Recommendation.md** (25KB)
    - Analysis of 5 core nodes (Source, Literal, Cast, Native, Alias)
    - Alias node infrastructure exists but not implemented
    - Recommendation: Keep all 5 together in core_nodes.py
    - High priority implementation (1-2 days)

---

### Part 3: Strategic Vision & Planning

**Purpose:** Long-term direction and adoption strategy
**Focus:** Realistic goals, differentiation, internal adoption

#### Documents:

11. **VISION.md** (20KB)
    - Honest assessment of package aims and scope
    - Target audience: Internal Mountain Ash tools (primary), library authors (secondary)
    - Differentiator: Ternary logic (TRUE/FALSE/UNKNOWN)
    - Success metrics: 50%+ internal adoption + 5-10 external users
    - Scope discipline: Expression evaluation only, not full DataFrame API
    - Not trying to be: Complete DataFrame library, SQL compiler, mass-market tool

---

### Part 4: Enum Alignment Architecture

**Problem:** Enums define operations, but alignment with protocols and backends incomplete
**Finding:** 78 operators defined, only 18 (23%) have backend abstraction
**Impact:** 77% of operations lack proper backend abstraction layer

#### Documents:

12. **ENUM_ALIGNMENT_QUICK_REF.md** (Quick reference)
    - Alignment matrix: Enums → Nodes → Visitors → Backends
    - 5-minute overview of gaps
    - Coverage percentages by category

13. **ENUM_ALIGNMENT_SUMMARY.md** (Executive summary)
    - Critical gap analysis
    - Backend abstraction coverage: ~70% alignment
    - 50 operations implemented at visitor level only
    - Priority recommendations and action plan

14. **ENUM_ALIGNMENT_ANALYSIS.md** (57KB, comprehensive)
    - Complete enum-to-architecture mapping
    - 11 operator categories analyzed
    - Detailed gap identification
    - Implementation roadmap by priority
    - 📍 **ESSENTIAL** for understanding architectural glue

15. **README_ENUM_ANALYSIS.md** (Navigation guide)
    - Master index for enum analysis
    - Quick start guide
    - How to use the documentation

16. **Interface-Test-Architecture.md** (45KB) ⭐⭐⭐
    - **CRITICAL: Ensures complete architectural alignment**
    - Interface test suite design (8 test categories)
    - VisitorDispatch protocol (missing layer discovered!)
    - PUBLIC vs _private naming conventions
    - 17 total protocols (8 operations + 1 dispatch + 8 visitor)
    - Automated verification strategy
    - 📍 **ESSENTIAL** for maintaining alignment across all 5 layers

---

## Quick Navigation

### I want to understand...

**...the backend god class problem**
→ Read: `Architectural-Review-ExpressionSystem-Refactoring.md` (Sections 1-4)

**...how operations flow through the system**
→ Read: `Alignment-Matrix.md`

**...the proposed backend architecture**
→ Read: `Protocol-Architecture-Proposal.md`

**...the unified protocol architecture** ⭐⭐
→ Read: `Unified-Protocol-Architecture.md` (ESSENTIAL - shared base protocols)

**...how to implement the backend refactoring**
→ Read: `Refactoring-Roadmap.md`

**...how to verify backend correctness**
→ Read: `Backend-Verification-Checklist.md`

**...the node structure and expansion needs**
→ Read: `ExpressionNode-Architecture-Review.md` ⭐

**...the core node organization**
→ Read: `Core-Node-Structure-Recommendation.md`

**...the strategic vision and adoption goals**
→ Read: `VISION.md`

**...the enum alignment and architectural glue** ⭐
→ Read: `ENUM_ALIGNMENT_ANALYSIS.md` (comprehensive)
→ Quick ref: `ENUM_ALIGNMENT_QUICK_REF.md` (5 minutes)
→ Summary: `ENUM_ALIGNMENT_SUMMARY.md` (15 minutes)

**...the interface test architecture and alignment verification** ⭐⭐⭐
→ Read: `Interface-Test-Architecture.md` (CRITICAL - ensures 5-layer alignment)

---

## Critical Findings Summary

### ExpressionSystem Backends (Part 1)

**Current Problems:**
- ✅ **God classes confirmed:** 663-883 lines, 68+ methods per backend
- ⚠️ **Asymmetric architecture:** Visitors use mixins, backends don't
- ❌ **Interface drift:** 19 declared abstract methods, 60+ actually implemented
- ⚠️ **Visitor method sprawl:** visit_* methods spread across mixin hierarchy
- ❌ **No alignment enforcement:** Visitor and backend can drift apart
- ⚠️ **Legacy `_B_` prefix:** Artificial naming difference (visitor `_B_eq` vs backend `eq`)

**Recommended Solution (UNIFIED PROTOCOLS):**
- **16 total protocols** (8 base operations + 8 visitor extensions)
- Unified protocol architecture with shared base:
  - Base operations protocols: Define core operations (eq, ne, add, sub, etc.)
  - Visitor protocols: Extend base + add visit_* methods
  - Both visitors AND backends implement same base operations
- Remove `_B_` prefix - align method names everywhere
- Protocol-based mixins for each backend (8 mixins of 50-200 lines)
- Shared base mixins for code reuse
- Type-safe compiler enforcement prevents drift
- Result: 663-883 lines → 8 files of 50-200 lines each + guaranteed alignment

**Timeline:** 3-4 weeks, 7-8 phases (includes visitor method renaming), incremental with testing after each phase

---

### ExpressionNode Structure (Part 2)

**Current State:**
- ✅ **Well-designed** for current scope (24 types, 65 operations, ~40% coverage)
- ✅ **Parameter-driven** approach (one node per category, not per operator)
- ✅ **1:1 visitor mapping** (clean alignment)
- ✅ **Backend mirroring** (easy implementation)

**Expansion Requirements:**
- **Current:** 24 node types → **Future:** 32 node types (+33%)
- **Current:** 65 operations → **Future:** 170+ operations (+161%)
- **Efficiency gain:** Node types grow 33%, operations grow 161%

**Critical Structural Changes:**

1. **Temporal Node Split (Phase 4) - REQUIRED**
   - Split TemporalExpressionNode (23 ops → would be 40+) into:
     - TemporalExtractExpressionNode (15 ops)
     - TemporalArithmeticExpressionNode (14 ops)
     - TemporalConstructionExpressionNode (12 ops)
   - **Timing:** Before Phase 4 implementation (weeks 6-9)
   - **Effort:** 1-2 weeks refactoring

2. **Window Infrastructure (Phase 8) - MAJOR**
   - New module: `core/window/`
   - New classes: WindowSpecification, WindowFunctionNode
   - **Timing:** Weeks 15-20
   - **Effort:** 3-5 weeks
   - **Complexity:** HIGH (frame semantics, backend translation)

3. **Backend Capability System (Before Phase 6) - RECOMMENDED**
   - Add capability checking for operations (array support varies by backend)
   - **Timing:** Before Phase 6 (weeks 10-12)
   - **Effort:** 1 week

**New Node Types Needed:**
- MathExpressionNode (Phase 1)
- Temporal split → 3 nodes (Phase 4)
- ArrayExpressionNode (Phase 6)
- BitwiseExpressionNode (Phase 7)
- WindowFunctionNode (Phase 8)
- Metric nodes: 2-3 types (Phase 9)

---

### Enum Alignment Architecture (Part 4)

**The Architectural Glue:**
- ✅ **Well-designed enums:** 13 node types, 78 operators across 11 categories
- ✅ **Node implementation:** 92% (12/13 node types implemented)
- ⚠️ **Backend abstraction gap:** Only 23% (18/78 operators in ExpressionSystem)
- ❌ **Missing abstraction:** 50 operations (64%) implemented at visitor level only
- ❌ **Completely unimplemented:** 2 operations (ALIAS, XOR variants)

**Current State:**
- Enums define 78 operations
- ExpressionSystem abstracts only 18 operations (23%)
- Remaining 60 operations hardcoded in visitor implementations
- Overall alignment: ~70% (functional but architecturally inconsistent)

**Critical Issue:**
The implementation path breaks down at backend abstraction:
```
Enum → Node Class → Visitor Mixin → [MISSING] → Backend Method
                                         ↓
                               Direct backend calls
                               (not abstracted!)
```

**Gaps by Category:**
- **Arithmetic:** 3 operators missing (div, pow, floor_div)
- **String:** 12 operators missing (upper, lower, contains, etc.)
- **Temporal:** 22 operators missing (year, month, add_days, etc.)
- **Pattern:** 4 operators missing (regex_match, like, etc.)
- **Conditional:** 3 operators missing (when, coalesce, fill_null)
- **Collection:** 1 operator missing (is_not_in)

**Recommended Fix:** Add 60 methods to ExpressionSystem base protocols during refactoring

**Timeline:** 2-3 weeks (can be phased with protocol refactoring)

---

## Design Principles (Codified)

### For ExpressionSystem Backends

1. **Unified Protocol Architecture** - Shared base operations protocols (8) + visitor extensions (8)
2. **Protocol-Based Mixins** - Focused protocols matching visitor categories
3. **Split at 25+ Methods** - Each mixin 50-200 lines
4. **Symmetric Architecture** - Visitors and backends both use mixins
5. **Backend Mirroring** - Protocols align with backend API structure
6. **Shared Base Mixins** - Only for truly identical code
7. **Type-Safe Alignment** - Compiler-enforced lockstep via shared base protocols

### For ExpressionNodes

1. **Parameter-Driven Categories** - One node per operation category, not per operator
2. **Split at 25-30 Operators** - Mandatory split if category exceeds threshold
3. **1:1 Visitor Mapping** - One visitor mixin per node category
4. **Backend Category Mirroring** - Align nodes with backend API structure
5. **Flexible Parameters** - Use *args, **kwargs for variable signatures

### For Visitor-Backend Alignment

1. **Shared Base Protocols** - Both implement same base operations protocols
2. **Consistent Naming** - Remove `_B_` prefix, use `operation()` everywhere
3. **Visitor Extends Base** - Visitor protocols extend operations + add visit_* methods
4. **Backend Implements Base** - Backends implement operations directly
5. **Complete Coverage** - Type checker enforces all methods exist
6. **Single Source of Truth** - Base protocol definitions document all operations
7. **Impossible to Drift** - Compiler errors if alignment breaks

### For Interface Alignment (5-Layer Verification)

1. **Enums are Truth** - All operations defined in enums first
2. **Node → Visitor Protocol** - VisitorDispatch ensures every node has visit_* method
3. **Operator → Method Mapping** - Consistent naming (OPERATOR_NAME → operator_name())
4. **PUBLIC Protocol Methods** - All protocol methods have no underscore prefix
5. **_PRIVATE Helpers** - All non-protocol methods have underscore prefix
6. **Automated Testing** - Interface tests verify alignment on every commit
7. **Complete Protocol Hierarchy** - 17 protocols (8 operations + 1 dispatch + 8 visitor)

---

## Implementation Priorities

### Phase 0: ExpressionSystem Refactoring (Parallel to Phase 1-2)
- **Duration:** 3-4 weeks
- **Parallel Work:** Can proceed alongside Phase 1-2 node additions
- **Benefit:** Eliminates god classes before major expansion
- **Risk:** Medium (mitigated by testing after each phase)

### Phase 1: Math Operations (Immediate)
- **Add:** MathExpressionNode (12 operators)
- **Duration:** 2-3 weeks
- **Dependency:** None
- **Risk:** Low

### Phase 2-3: Conditionals + Strings (Short-term)
- **Extend:** ConditionalIfElseExpressionNode (+5 ops)
- **Extend:** StringExpressionNode (+10 ops)
- **Duration:** 3-4 weeks
- **Risk:** Low

### Phase 4: Temporal Expansion + SPLIT (Critical)
- **SPLIT:** TemporalExpressionNode → 3 nodes ⚠️ **REQUIRED**
- **Add:** TemporalConstructionExpressionNode
- **Duration:** 3-4 weeks (includes 1-2 week split refactoring)
- **Risk:** Medium (structural change)
- **Impact:** Prevents mega-node problem

### Phase 5-7: Math Advanced + Arrays + Bitwise (Mid-term)
- **Extend:** MathExpressionNode (+14 ops)
- **Add:** ArrayExpressionNode (18 ops)
- **Add:** BitwiseExpressionNode (6 ops)
- **Implement:** Backend capability system
- **Duration:** 7-9 weeks
- **Risk:** Medium (array backend compatibility)

### Phase 8: Window Functions (Major)
- **Add:** WindowFunctionNode + infrastructure ⚠️ **MAJOR**
- **Duration:** 3-5 weeks
- **Risk:** HIGH (complex architecture)
- **Strategy:** Research Ibis first, prototype on Polars

### Phase 9: ML Metrics (Long-term)
- **Add:** 2-3 metric node types
- **Duration:** 4-7 weeks
- **Dependency:** Phase 8 (for ranking metrics)
- **Risk:** Medium (domain-specific)

---

## Success Metrics

### Code Quality
- [ ] God classes eliminated (3 backends)
- [ ] 24 focused backend mixins created (8 per backend)
- [ ] Shared base mixins extracted (2-3)
- [ ] Alias node implemented (core infrastructure)
- [ ] Node types: 24 → 32 (+8 types, +33%)
- [ ] Operations: 65 → 170+ (+105 ops, +161%)

### Architecture
- [ ] 17 protocols defined (8 operations + 1 dispatch + 8 visitor)
- [ ] Unified protocol architecture implemented (shared base)
- [ ] VisitorDispatch protocol ensuring node → visit_* alignment
- [ ] `_B_` prefix removed from all visitor methods
- [ ] _private prefix added to all helper methods
- [ ] Type-safe visitor-backend alignment enforced
- [ ] Symmetric visitor-backend architecture achieved
- [ ] Node granularity optimized (no node >30 operators)
- [ ] Complete 5-layer alignment (enums ↔ nodes ↔ visitors ↔ protocols ↔ backends)

### Testing
- [ ] All 703+ tests passing (expanding with coverage)
- [ ] Type checking passing (mypy)
- [ ] Linting passing (ruff)
- [ ] No behavioral changes in refactoring
- [ ] Interface tests implemented (8 test suites)
- [ ] Enum → Node class mapping verified
- [ ] Operator → Protocol method mapping verified
- [ ] Node → visit_* method mapping verified
- [ ] Protocol extension hierarchy verified
- [ ] Backend protocol compliance verified
- [ ] Visitor protocol compliance verified
- [ ] Naming convention compliance verified
- [ ] Interface tests in CI/CD pipeline

### Documentation
- [ ] CLAUDE.md updated with new architecture
- [ ] All design principles codified
- [ ] Backend support matrix documented
- [ ] Verification checklists complete

---

## Risk Management

### High-Risk Items

1. **Window Function Complexity (Phase 8)**
   - Frame semantics, backend variability
   - **Mitigation:** Prototype on Polars, research Ibis thoroughly

2. **Temporal Node Split Timing (Phase 4)**
   - Split too early (wasted) or too late (painful)
   - **Decision:** Split in Phase 4 before adding 17 new operators
   - **Mitigation:** Clear migration plan, test-driven

### Medium-Risk Items

3. **Backend Refactoring Test Failures**
   - **Mitigation:** Test after EVERY task, rollback capability

4. **Array Backend Compatibility (Phase 6)**
   - **Mitigation:** Backend capability system, clear documentation

5. **Math Node Growth (Phase 5)**
   - 26 operators approaches 30 limit
   - **Mitigation:** Monitor, split if exceeds threshold

---

## Recommendations for Review

### For Immediate Decision:

1. **Approve ExpressionNode architecture** with planned structural changes
2. **Approve Temporal node split** for Phase 4 (prevents mega-node)
3. **Approve Window infrastructure** design approach (research + prototype)
4. **Approve Backend capability system** before Phase 6

### For Phase 0 Refactoring:

5. **Approve ExpressionSystem protocol refactoring** (3-4 weeks)
6. **Review Refactoring-Roadmap.md** for detailed implementation plan
7. **Consider parallel work** (refactoring alongside Phase 1-2)

### For Documentation:

8. **Review and validate** all architectural findings
9. **Update CLAUDE.md** with approved architectural principles
10. **Create tracking** for critical structural changes

---

## Next Steps

### Immediate (This Week):
1. ✅ Review all documentation
2. ✅ Validate architectural findings
3. ✅ Approve design principles
4. ✅ Decide on refactoring timeline (parallel or sequential)

### Short-term (Next 2 weeks):
5. Begin Phase 1 (Math node) OR Phase 0 (Backend refactoring)
6. Update CLAUDE.md with approved architecture
7. Set up tracking for structural changes

### Medium-term (Months 2-3):
8. Execute Phase 4 temporal split
9. Implement backend capability system
10. Continue phase-by-phase expansion

### Long-term (Months 4-6):
11. Window infrastructure (Phase 8)
12. ML metrics (Phase 9)
13. Complete 100% coverage

---

## Documentation Completeness

**ExpressionSystem Refactoring:**
- ✅ Problem analysis
- ✅ Proposed solution (protocols + mixins)
- ✅ **Unified protocol architecture** (shared base + visitor extensions)
- ✅ `_B_` prefix removal strategy
- ✅ Implementation roadmap (needs update for unified approach)
- ✅ Verification checklists
- ✅ Alignment matrices

**ExpressionNode Architecture:**
- ✅ Current structure analysis
- ✅ Coverage assessment (65 → 170+ ops)
- ✅ Granularity evaluation
- ✅ Critical changes identified (Temporal split, Window infrastructure)
- ✅ Core node organization (5 nodes)
- ✅ New node types specified (8 new types)
- ✅ Design principles codified

**Enum Alignment Architecture:**
- ✅ Complete enum-to-architecture mapping
- ✅ Gap analysis (77% operations missing backend abstraction)
- ✅ Coverage percentages by category
- ✅ Priority recommendations
- ✅ Implementation roadmap by priority

**Interface Test Architecture:**
- ✅ 5-layer alignment verification design
- ✅ VisitorDispatch protocol specification
- ✅ PUBLIC vs _private naming conventions
- ✅ 8 interface test suite designs
- ✅ 17-protocol hierarchy (8 operations + 1 dispatch + 8 visitor)
- ✅ Automated alignment verification strategy
- ✅ CI/CD integration plan

**Strategic Vision:**
- ✅ Honest assessment of aims and scope
- ✅ Target audience identified
- ✅ Differentiation strategy (ternary logic)
- ✅ Success metrics defined
- ✅ Scope discipline articulated

**Total Documentation:** ~420KB across 16 documents

---

## Questions for User

1. **Unified Protocol Architecture:** Approve implementing 17 protocols (8 operations + 1 dispatch + 8 visitor) with shared base for guaranteed alignment?

2. **VisitorDispatch Protocol:** Approve new protocol ensuring every ExpressionNode has corresponding visit_* method?

3. **Interface Tests:** Approve implementing 8 interface test suites to verify 5-layer alignment (enums ↔ nodes ↔ visitors ↔ protocols ↔ backends)?

4. **Naming Conventions:** Approve PUBLIC (no prefix) for protocol methods and _private (underscore) for all helpers?

5. **Remove `_B_` Prefix:** Approve removing legacy `_B_` prefix from all visitor methods to align with backend method names?

6. **Backend Abstraction Gap:** Approve adding 60 missing methods to ExpressionSystem protocols (currently only 23% coverage)?

7. **Timing:** Should backend refactoring (Phase 0) run in parallel with Phase 1-2, or sequentially?

8. **Priorities:** Is window function support (Phase 8, 97% coverage) more critical than ML metrics (Phase 9, 100% coverage)?

9. **Temporal Split:** Approve splitting TemporalExpressionNode in Phase 4 before adding 17 new operators?

10. **Backend Capability:** Approve implementing capability system before Phase 6 (arrays)?

11. **Risk Tolerance:** Comfortable with 3-5 week window infrastructure effort (complex but critical)?

12. **Alias Node:** Approve immediate implementation of AliasExpressionNode (1-2 days, high priority)?

---

## Key Architectural Enhancement

### Unified Protocol Architecture (Refined Discovery)

The most significant architectural insight from this review is the **unified protocol architecture** that ensures visitor-backend alignment through shared base protocols:

**Problem Identified:**
- Visitor methods (`visit_*` and `_B_operation()`) spread across mixin hierarchy
- Backend methods (`operation()`) in separate ExpressionSystem implementations
- No compiler enforcement of alignment
- Could drift out of sync
- **Legacy artifact:** `_B_` prefix creates artificial naming difference

**Initial Solution (Dual Protocols):**
- 8 visitor protocols + 8 backend protocols (16 total, paired)
- Visitor has `_B_eq()`, backend has `eq()` - different names, same operation

**Refined Solution (Unified Protocols):**
- 8 **base operations protocols** (ComparisonOperations, ArithmeticOperations, etc.)
- 8 **visitor protocols** that EXTEND base operations + add visit_* methods
- Both visitors AND backends implement the SAME base operations protocols
- Remove `_B_` prefix - both use `eq()`, `ne()`, etc.
- **Result:** One set of operations, implemented by both, compiler-enforced alignment

**Example:**
```python
# Base Operations Protocol (shared by both)
class ComparisonOperations(Protocol):
    def eq(self, left, right) -> Any: ...
    def ne(self, left, right) -> Any: ...
    # ... 4 more

# Visitor Protocol (extends base)
class ComparisonVisitor(ComparisonOperations, Protocol):
    def visit_comparison_expression(self, node) -> Any: ...
    # Inherits: eq, ne, gt, lt, ge, le

# Backend implements base directly
class PolarsExpressionSystem(ComparisonOperations, ...):
    def eq(self, left, right):
        return left == right  # Actual implementation

# Visitor implements extended protocol
class UniversalBooleanVisitor(ComparisonVisitor, ...):
    def eq(self, left, right):
        # Delegates to backend
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.eq(left_expr, right_expr)

    def visit_comparison_expression(self, node):
        # AST traversal
        ...
```

**Key Insight:** The `_B_` prefix was a legacy artifact. Visitors and backends perform the SAME operations, so they should implement the SAME protocols with the SAME method names. Visitors delegate to backends, but both follow the same interface.

This refinement transforms the architecture from "two hierarchies in lockstep" to "one shared base with clear extension pattern" - simpler, clearer, and equally type-safe.

---

## Critical Discovery: 5-Layer Alignment Gap

### Interface Test Architecture (Final Enhancement)

The architectural review revealed that **five layers must stay perfectly aligned**, but there's no automated verification:

**The 5 Layers:**
1. **Enums** (78 operators across 11 categories) - THE SINGLE SOURCE OF TRUTH
2. **ExpressionNodes** (13 node types) - AST structure
3. **Visitor Protocols** (visit_* methods) - AST traversal interface
4. **Operations Protocols** (operation methods) - Backend interface
5. **Backend Implementations** (pl.Expr, nw.Expr, ir.Expr) - Concrete implementations

**Current State:**
- ✅ Layer 1→2: 92% aligned (12/13 nodes - ALIAS missing)
- ❌ Layer 1→4: Only 23% aligned (18/78 operators in ExpressionSystem)
- ✅ Layer 2→3: ~100% aligned (all nodes have visit_* methods)
- ⚠️ Layer 3→4: No formal alignment (implemented but not enforced)
- ⚠️ Layer 4→5: Partial (missing 60 backend methods)

**Critical Gap:** **77% of operations (60/78) lack backend abstraction layer!**

**The Problem:**
```
Enum → Node Class → Visitor Mixin → [MISSING ABSTRACTION] → Backend Method
                                              ↓
                                    Direct backend calls
                                    (hardcoded in visitors!)
```

**The Solution: Interface Tests + VisitorDispatch Protocol**

1. **VisitorDispatch Protocol** (NEW discovery!)
   - Ensures every ExpressionNode has a visit_* method
   - Type-safe enforcement at compile time
   - Missing layer in original protocol hierarchy

2. **8 Interface Test Suites**
   - Enum → Node class mapping
   - Operator → Protocol method mapping
   - Node → visit_* method mapping
   - Protocol extension hierarchy
   - Backend protocol compliance
   - Visitor protocol compliance
   - Naming convention enforcement
   - Run on every commit (CI/CD)

3. **Complete Protocol Hierarchy**
   - 8 operations protocols (base)
   - 1 VisitorDispatch protocol (NEW)
   - 8 visitor protocols (extend operations + dispatch)
   - **Total: 17 protocols** (not 16!)

4. **PUBLIC vs _private Convention**
   - Protocol methods: PUBLIC (no prefix)
   - Helper methods: _private (underscore prefix)
   - Remove legacy `_B_` prefix from all visitor methods

**Benefits:**
- ✅ Compiler-enforced 5-layer alignment
- ✅ Impossible to add operation without full implementation
- ✅ Automated verification on every commit
- ✅ Clear contracts at every layer
- ✅ Self-documenting architecture

**Impact:**
Transforms architecture from "mostly aligned" (70%) to **"guaranteed alignment" (100%)** with automated verification preventing drift.

**Effort:** 4-5 weeks (can be phased with refactoring)

---

**Documentation Suite Complete** ✅

**Ready for:** Architecture review, decision on priorities, implementation planning

**Total:** 16 comprehensive documents, ~420KB, covering every architectural layer from enums to backend implementations
