# Expression System Refactoring Project Plan

## Project Overview

**Objective**: Transform MountainAsh Expressions from a dataframe-specific library to a universal expression system that can compile to multiple backend expression systems, focusing on Narwhals, Polars, and Ibis.

**Scope**: Major architectural refactoring targeting clean expression system architecture without backward compatibility constraints.

**Duration**: 8-10 weeks (streamlined scope)

**Risk Level**: Medium (focused scope reduces complexity)

## Project Phases

### Phase 1: Architecture Proof-of-Concept (Weeks 1-2)

#### 1.1 Core Architecture Design
- [ ] **Define Expression System Protocol**
  - Implement `ExpressionSystem` interface focused on Narwhals/Polars/Ibis
  - Design visitor pattern without table parameters
  - Create expression compilation pipeline
  - Define logic type handling strategy

#### 1.2 Narwhals Prototype Implementation
- [ ] **Narwhals Backend Implementation**
  - Create NarwhalsExpressionSystem class
  - Implement Boolean logic visitor
  - Implement Ternary logic visitor using if-then-else constructs
  - Test expression compilation and execution

- [ ] **Validation and Testing**
  - End-to-end expression compilation pipeline
  - Performance comparison with current system
  - Logic type correctness validation
  - Multi-dataframe backend testing via Narwhals

**Deliverables:**
- Working Narwhals expression system
- Validated architecture patterns
- Performance baseline metrics
- Proof-of-concept demonstration

### Phase 2: Core Architecture Implementation (Weeks 3-4)

#### 2.1 Implement Orthogonal Architecture Components
- [ ] **ExpressionParameter System**
  - Implement centralized parameter type detection and conversion
  - Handle MountainAsh nodes, native expressions, column names, literals
  - Create parameter type enumeration and conversion logic
  - Test parameter dispatch across different input types

- [ ] **Expression Node Type System**
  - Create specific node types for each operator (1-1 mapping)
  - Implement LogicalAndNode, ComparisonEqNode, ComparisonGtNode, etc.
  - Ensure nodes are orthogonal to logic_type and backend_type
  - Update visitor pattern to use specific node types

- [ ] **Visitor-Method 1-1 Mapping**
  - Implement visit_logical_and(), visit_comparison_eq(), etc. methods
  - Create BooleanVisitor(logic_type="boolean") and TernaryVisitor(logic_type="ternary")
  - Ensure visitors work with any backend through ExpressionSystem protocol
  - Remove table parameters and implement clean _process_operand() pattern

- [ ] **Expression System Protocol**
  ```
  src/mountainash_expressions/core/expression_system/
  ├── base.py                  # ExpressionSystem abstract base
  ├── parameter.py             # ExpressionParameter with type dispatch
  ├── registry.py              # Backend registry
  └── compiler.py              # Expression compilation
  ```

#### 2.2 Orthogonality Validation
- [ ] **Cross-Dimensional Testing**
  - Test that visitors work with any backend (visitor-backend orthogonality)
  - Test that backends work with any logic type (logic-backend orthogonality)
  - Test that visitors handle any expression type (visitor-expression orthogonality)
  - Validate proper parameter binding at each component

**Deliverables:**
- Complete orthogonal architecture implementation
- ExpressionParameter centralized type dispatch
- All five orthogonal dimensions validated
- Clean visitor pattern with 1-1 operator mapping

### Phase 3: Multi-Backend Implementation (Weeks 5-6)

#### 3.1 All Expression Systems Implementation
- [ ] **Implement All Three Backends Simultaneously**
  ```
  src/mountainash_expressions/backends/
  ├── narwhals_system/
  │   └── expression_system.py     # NarwhalsExpressionSystem(backend_type="narwhals")
  ├── polars_system/
  │   └── expression_system.py     # PolarsExpressionSystem(backend_type="polars")
  └── ibis_system/
      └── expression_system.py     # IbisExpressionSystem(backend_type="ibis")
  ```

- [ ] **Backend-Specific Native Operations**
  - Each backend implements ExpressionSystem protocol
  - Native boolean operations (native_and, native_or, native_not)
  - Native ternary operations (native_ternary_and, native_ternary_or, native_ternary_not)
  - Backend-specific type detection (is_native_expression)
  - Column and literal creation (col, lit)

- [ ] **Orthogonality Validation Across All Backends**
  - Same BooleanVisitor works with all three backends
  - Same TernaryVisitor works with all three backends
  - All backends handle same expression node types
  - ExpressionParameter works uniformly across all backends

**Deliverables:**
- All three expression systems implemented
- Orthogonal architecture validated across all backends
- Backend-agnostic visitor functionality confirmed
- Uniform ExpressionParameter behavior

### Phase 4: Logic Type Implementation (Weeks 7-8)

#### 4.1 Boolean and Ternary Logic Across All Backends
- [ ] **Boolean Logic Implementation**
  - BooleanVisitor(logic_type="boolean") working with all backends
  - Standard AND/OR/NOT semantics using native_and, native_or, native_not
  - Consistent boolean behavior across Narwhals, Polars, Ibis
  - Performance validation for boolean operations

- [ ] **Ternary Logic Implementation**  
  - TernaryVisitor(logic_type="ternary") working with all backends
  - NULL-aware AND/OR/NOT semantics using native_ternary_and, native_ternary_or, native_ternary_not
  - when/then/otherwise constructs in Narwhals and Polars
  - case/when/else constructs in Ibis
  - Semantic consistency validation across all backends

- [ ] **Logic Type Orthogonality Validation**
  - Same expression tree processed by different logic types
  - Boolean vs Ternary semantic differences validated
  - All backends support both logic types through same interface
  - Logic type switching without expression tree changes

#### 4.2 Advanced Expression Types
- [ ] **Extended Comparison Operations**
  - All comparison operators (eq, ne, gt, lt, ge, le, in, is_null) across all backends
  - Consistent comparison semantics for both boolean and ternary logic
  - Proper null/unknown handling in comparisons

**Deliverables:**
- Both logic types working across all backends
- Logic type orthogonality validated
- Semantic consistency across backend-logic combinations  
- Complete comparison operator support

### Phase 5: Integration & Optimization (Weeks 9-10)

#### 5.1 API Finalization
- [ ] **Universal Expression API**
  ```python
  # Clean API design
  from mountainash_expressions import expr
  
  # Universal expression building
  expression = (expr.col("age") > 25) & (expr.col("active") == True)
  
  # Backend compilation
  narwhals_expr = expression.compile("narwhals", "boolean")
  polars_expr = expression.compile("polars", "ternary") 
  ibis_expr = expression.compile("ibis", "boolean")
  ```

- [ ] **Performance Optimization**
  - Expression compilation caching
  - Backend-specific optimizations
  - Memory usage optimization
  - Benchmark-driven improvements

#### 5.2 Testing & Documentation
- [ ] **Comprehensive Testing**
  - Cross-backend test matrix
  - Performance regression testing
  - Logic type correctness validation
  - Real-world scenario testing

- [ ] **Documentation**
  - Architecture overview and design decisions
  - Backend implementation guides
  - API documentation with examples
  - Performance tuning guides

**Deliverables:**
- Finalized universal API
- Optimized performance across all backends
- Comprehensive test suite
- Complete documentation

## Orthogonal Implementation Strategy

### Phase 1-2: Architecture Foundation (Weeks 1-4)
**Goal**: Prove the orthogonal architecture with Narwhals prototype
- Establish ExpressionParameter centralized type dispatch
- Create 1-1 node-operator and visitor method-operator mapping
- Validate that architecture dimensions are truly orthogonal
- Build foundation that supports any combination of (backend_type, logic_type, expression_type)

### Phase 3: Multi-Backend Dimension (Weeks 5-6)  
**Goal**: Implement all backends simultaneously
- All three backends (Narwhals, Polars, Ibis) implemented in parallel
- Validate backend orthogonality: same visitors work with all backends
- Confirm ExpressionParameter handles all backend types uniformly
- Performance comparison across backends with identical logic

### Phase 4: Multi-Logic Dimension (Weeks 7-8)
**Goal**: Implement all logic types simultaneously  
- Both logic types (Boolean, Ternary) implemented across all backends
- Validate logic type orthogonality: same backends work with both logic types
- Semantic consistency testing for all (backend, logic_type) combinations
- Complete expression type coverage (logical, comparison, basic operations)

### Phase 5: Integration & Validation (Weeks 9-10)
**Goal**: Validate complete orthogonal architecture
- Full matrix testing: 3 backends × 2 logic types × N expression types
- Performance validation across all combinations
- API finalization based on orthogonal principles
- Documentation of parameter binding patterns

## Future Extensions (Post-Project)
- **SQLAlchemy Backend**: Direct SQL database integration
- **MongoDB Backend**: NoSQL document query support
- **Custom Backends**: Plugin architecture for third-party extensions

## Risk Management

### High Risk Items

#### 1. Performance Regression
**Risk**: New architecture introduces performance overhead
**Mitigation**: 
- Continuous performance monitoring with Narwhals baseline
- Direct performance comparison: native Polars vs Narwhals vs new architecture
- Backend-specific optimization passes
- Expression compilation caching

#### 2. Architecture Scalability
**Risk**: Patterns that work for Narwhals don't scale to Polars/Ibis
**Mitigation**:
- Start simple with Narwhals proof-of-concept
- Validate each backend addition thoroughly
- Refactor architecture based on learnings from each backend
- Conservative feature progression

#### 3. Logic Type Semantic Consistency  
**Risk**: Ternary logic behaves differently across backends
**Mitigation**:
- Standardized if-then-else patterns for ternary logic
- Comprehensive cross-backend semantic testing
- Clear documentation of null/NA/missing handling per backend
- Reference test cases for logic type behavior

### Medium Risk Items

#### 1. Development Timeline
**Risk**: 10-week timeline proves insufficient
**Mitigation**:
- Streamlined scope (no backward compatibility)
- Progressive architecture validation (Narwhals → Polars → Ibis)
- Focus on three backends only
- Defer SQLAlchemy/MongoDB to future

#### 2. Expression Compilation Complexity
**Risk**: Compilation from abstract expressions to backend-specific expressions proves complex
**Mitigation**:
- Start with simple expressions in proof-of-concept
- Build complexity gradually
- Leverage if-then-else constructs for ternary logic
- Use proven patterns from existing visitor implementations

## Success Criteria

### Functional Success
- [ ] **Three backends fully functional**: Narwhals, Polars, Ibis
- [ ] **All logic types work across all backends**: Boolean and Ternary logic
- [ ] **Expression composition**: Complex nested expressions work identically across backends
- [ ] **Semantic consistency**: Ternary logic behaves consistently using if-then-else patterns
- [ ] **Performance acceptability**: Within 15% of current system performance

### Technical Success
- [ ] **Clean, extensible architecture**: Easy to add new backends
- [ ] **Expression compilation pipeline**: Abstract expressions → backend expressions
- [ ] **Comprehensive testing**: Cross-backend validation for all operations
- [ ] **No table parameters**: Visitors build expressions directly
- [ ] **Logic type flexibility**: Easy custom null/NA/missing handling per backend

### Architecture Validation Success
- [ ] **Narwhals proof-of-concept**: Validates core architecture patterns
- [ ] **Polars native integration**: Proves architecture scales to different expression APIs  
- [ ] **Ibis analytical support**: Validates cross-paradigm compatibility
- [ ] **Performance comparison**: Native vs universal approaches benchmarked
- [ ] **Extensibility demonstration**: New backend can be added in defined timeframe

## Resource Requirements

### Development Resources (Streamlined)
- **Lead Developer**: 10 weeks full-time (architecture, core implementation)
- **Validation**: Self-validation through comprehensive testing
- **Documentation**: Integrated with development process

### Infrastructure Resources
- **CI/CD**: Multi-backend test matrix (Narwhals, Polars, Ibis)
- **Testing**: Expression system validation infrastructure
- **Performance**: Benchmarking across three backends

### External Dependencies
- **Narwhals**: Multi-dataframe compatibility layer
- **Polars**: Native expression system
- **Ibis**: Analytical expression system
- **Testing Infrastructure**: Consistent test data across backends

## Key Simplifications from Original Plan

1. **No Backward Compatibility**: Focus entirely on clean target architecture
2. **Three Backend Focus**: Narwhals, Polars, Ibis only (defer SQL/NoSQL)
3. **Streamlined Scope**: 10 weeks vs 16 weeks
4. **Architectural Validation**: Progressive validation through each backend addition
5. **Ternary Logic Simplification**: if-then-else constructs across all backends

This streamlined plan focuses on proving the universal expression architecture with three complementary backends while maintaining architectural quality and performance.