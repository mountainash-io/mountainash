# Orthogonal Expression Architecture Diagram

## Core Dimensions Overview

```mermaid
graph TB
    subgraph "Dimension 1: LogicType"
        LT1[boolean]
        LT2[ternary]
        LT3[fuzzy]
    end
    
    subgraph "Dimension 2: ExpressionType"
        ET1[logical_and]
        ET2[logical_or]
        ET3[comparison_eq]
        ET4[comparison_gt]
        ET5[column]
        ET6[literal]
    end
    
    subgraph "Dimension 3: BackendType"
        BT1[narwhals]
        BT2[polars]
        BT3[ibis]
    end
    
    subgraph "Dimension 4: Visitors"
        V1[UniversalVisitor]
    end
    
    subgraph "Dimension 5: Visitor Methods"
        VM1[visit_boolean_logical_and]
        VM2[visit_ternary_logical_and]
        VM3[visit_boolean_comparison_eq]
        VM4[visit_ternary_comparison_eq]
    end
```

## Component Binding Relationships

```mermaid
graph LR
    subgraph "ExpressionNode"
        EN[ExpressionNode<br/>BINDS: expression_type + logic_type]
        EN --> EN1[BooleanLogicalAndNode<br/>expression_type="logical_and"<br/>logic_type="boolean"]
        EN --> EN2[TernaryLogicalAndNode<br/>expression_type="logical_and"<br/>logic_type="ternary"]
        EN --> EN3[BooleanComparisonGtNode<br/>expression_type="comparison_gt"<br/>logic_type="boolean"]
        EN --> EN4[TernaryComparisonGtNode<br/>expression_type="comparison_gt"<br/>logic_type="ternary"]
    end
    
    subgraph "Visitor"
        V[UniversalVisitor<br/>BINDS: backend_type only]
        V --> V1[UniversalVisitor<br/>(NarwhalsExpressionSystem)]
        V --> V2[UniversalVisitor<br/>(PolarsExpressionSystem)]
        V --> V3[UniversalVisitor<br/>(IbisExpressionSystem)]
    end
    
    subgraph "VisitorMethods"
        VM[Visitor Methods<br/>BINDS: expression_type + logic_type]
        VM --> VM1[visit_boolean_logical_and<br/>handles: logical_and + boolean]
        VM --> VM2[visit_ternary_logical_and<br/>handles: logical_and + ternary]
        VM --> VM3[visit_boolean_comparison_gt<br/>handles: comparison_gt + boolean]
        VM --> VM4[visit_ternary_comparison_gt<br/>handles: comparison_gt + ternary]
    end
    
    subgraph "ExpressionSystem"
        ES[ExpressionSystem<br/>BINDS: backend_type only]
        ES --> ES1[NarwhalsExpressionSystem<br/>provides all logic operations]
        ES --> ES2[PolarsExpressionSystem<br/>provides all logic operations]
        ES --> ES3[IbisExpressionSystem<br/>provides all logic operations]
    end
    
    EN1 -.-> VM1
    EN2 -.-> VM2
    EN3 -.-> VM3
    EN4 -.-> VM4
    
    V1 --> ES1
    V2 --> ES2
    V3 --> ES3
```

## Orthogonal Relationship Matrix

```mermaid
graph TB
    subgraph "Orthogonality Matrix"
        subgraph "LogicType × ExpressionType"
            LT_ET["BOUND TOGETHER<br/>BooleanLogicalAnd ≠ TernaryLogicalAnd<br/>Different NULL handling"]
        end
        
        subgraph "BackendType × LogicType"
            BT_LT["ORTHOGONAL<br/>Each backend supports all logic types<br/>via different operations"]
        end
        
        subgraph "BackendType × ExpressionType"  
            BT_ET["ORTHOGONAL<br/>Each backend supports all expression types<br/>via native operations"]
        end
        
        subgraph "Visitor × LogicType"
            V_LT["ORTHOGONAL<br/>One visitor handles all logic types<br/>via method dispatch"]
        end
        
        subgraph "Visitor × ExpressionType"
            V_ET["ORTHOGONAL<br/>One visitor handles all expression types<br/>via method dispatch"]
        end
    end
```

## Compilation Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant ExpressionNode
    participant Visitor
    participant VisitorMethod
    participant ExpressionSystem
    
    Note over User: 1. Create expression tree with bound logic_type
    User->>ExpressionNode: TernaryLogicalAndNode(children)
    Note over ExpressionNode: expression_type="logical_and"<br/>logic_type="ternary"<br/>BOUND TOGETHER
    
    Note over User: 2. Choose backend_type
    User->>ExpressionSystem: PolarsExpressionSystem()
    Note over ExpressionSystem: backend_type="polars"<br/>provides all logic operations
    
    Note over User: 3. Create visitor with backend
    User->>Visitor: UniversalVisitor(polars_system)
    Note over Visitor: backend_type="polars"<br/>handles ALL logic types
    
    Note over User: 4. Compile expression
    User->>ExpressionNode: expr.accept(visitor)
    ExpressionNode->>Visitor: accept(visitor)
    
    Note over Visitor: Route based on expression_type + logic_type
    Visitor->>VisitorMethod: visit_ternary_logical_and(node)
    Note over VisitorMethod: Method binds:<br/>expression_type="logical_and"<br/>logic_type="ternary"
    
    VisitorMethod->>ExpressionSystem: native_ternary_and(left, right)
    Note over ExpressionSystem: Uses backend-specific<br/>ternary AND operation
    ExpressionSystem-->>VisitorMethod: polars.Expr
    VisitorMethod-->>Visitor: polars.Expr
    Visitor-->>ExpressionNode: polars.Expr
    ExpressionNode-->>User: polars.Expr
```

## Parameter Binding Points

```mermaid
graph TB
    subgraph "1. Node Creation"
        NC["expression_type + logic_type<br/>BOUND TOGETHER<br/>Example: BooleanLogicalAndNode"]
    end
    
    subgraph "2. System Creation"  
        SC["backend_type<br/>BOUND TO SYSTEM<br/>Example: PolarsExpressionSystem"]
    end
    
    subgraph "3. Visitor Creation"
        VC["backend_type inherited<br/>VISITOR IS LOGIC-AGNOSTIC<br/>Example: UniversalVisitor(polars_system)"]
    end
    
    subgraph "4. Method Dispatch"
        MD["expression_type + logic_type<br/>DETERMINE METHOD<br/>Example: visit_boolean_logical_and()"]
    end
    
    subgraph "5. Parameter Processing"
        PP["backend_type + optional visitor<br/>FOR CONVERSION<br/>Example: ExpressionParameter(polars_system, visitor)"]
    end
    
    NC --> MD
    SC --> VC
    VC --> PP
    MD --> PP
```

## Component Matrix Summary

| Component | Required Parameters | Optional Parameters | Orthogonal To |
|-----------|-------------------|-------------------|---------------|
| **ExpressionNode** | `expression_type + logic_type` (bound) | - | `backend_type` only |
| **Visitor** | `backend_type` | - | `logic_type + expression_type` |
| **Visitor Method** | `expression_type + logic_type` (bound) | - | `backend_type` |
| **ExpressionSystem** | `backend_type` | - | `logic_type + expression_type` |
| **ExpressionParameter** | `backend_type` | `visitor` | `logic_type + expression_type` |

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

This orthogonal architecture ensures:
- **Composability**: Any logic type works with any backend
- **Extensibility**: New backends or logic types don't break existing code
- **Type Safety**: Parameters bound at appropriate points
- **Performance**: No runtime type checking or complex dispatch