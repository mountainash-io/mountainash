# Orthogonal Expression Architecture Diagrams

**mountainash-expressions Package**

---

## Document Overview

This document contains comprehensive architectural diagrams for the orthogonal expression system in the mountainash-expressions package. The diagrams illustrate the four core dimensions and their relationships.

---

## Diagram Contents

1. **Core Dimensions Overview** - Shows the 5 architectural dimensions and their possible values

2. **Component Binding Relationships** - Illustrates how different components bind parameters together

3. **Orthogonal Relationship Matrix** - Visual representation of which dimensions are orthogonal vs bound together

4. **Compilation Flow Architecture** - Sequence diagram showing expression compilation process

5. **Parameter Binding Points** - Shows where each parameter gets bound during compilation

---

## Key Architectural Principles

### 1. Logic Type & Expression Type Are Bound
- `BooleanLogicalAndNode` ≠ `TernaryLogicalAndNode`
- Same operation, different NULL handling semantics
- Requires different visitor methods

### 2. Visitors Are Backend-Specific, Logic-Agnostic
- One `UniversalVisitor` per backend
- Handles ALL logic types via method dispatch
- No separate `BooleanVisitor`, `TernaryVisitor` per backend

### 3. Expression Systems Support All Logic Types
- Each backend provides both boolean and ternary operations
- No capability matrix needed
- Operations may delegate if not natively supported

### 4. Clean Parameter Separation
- Nodes: bind `expression_type + logic_type`
- Visitors: bind `backend_type` only
- Methods: dispatch on `expression_type + logic_type`
- Systems: provide operations for `backend_type`

---

*Generated from: mountainash-expressions/docs/ExpressionSystemRefactoring/orthogonal_architecture_analysis.md*