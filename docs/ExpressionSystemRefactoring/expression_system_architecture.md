# Expression System Backend Architecture

## Requirements

### Functional Requirements

1. **Universal Expression Language**
   - Single expression tree works across multiple execution backends
   - Support for Boolean, Ternary, and Fuzzy logic types
   - Expression composition through logical operations (AND, OR, NOT, XOR)
   - Expression evaluation without requiring table context during construction

2. **Multi-Backend Expression Support**
   - Target expression systems rather than just dataframe types
   - Support for Narwhals (dataframes), SQLAlchemy (SQL), Ibis (analytical), MongoDB (NoSQL), Django ORM
   - Backend-specific optimization opportunities
   - Native logic type support where available

3. **Logic Type Preservation**
   - Each backend implements logic types according to its native capabilities
   - Automatic fallback/emulation for unsupported logic types
   - Consistent semantic behavior across backends regardless of implementation

4. **Lazy Expression Construction**
   - Expressions built without immediate evaluation
   - No table/context parameter required during expression tree construction
   - Compilation step converts abstract expression to backend-specific expression

### Non-Functional Requirements

1. **Performance**
   - Minimal overhead in expression construction
   - Backend-specific optimizations preserved
   - Lazy evaluation where supported by backend

2. **Extensibility**
   - Easy addition of new expression backends
   - Plugin-based architecture for backend registration
   - Support for custom logic types and operations

3. **Type Safety**
   - Each backend maintains its own type system
   - Compile-time detection of unsupported operations
   - Clear error messages for incompatible backend/logic combinations

## Target Architecture

### Core Components

#### 1. Expression Tree Layer (Unchanged)
```
LogicalExpressionNode
├── ColumnExpressionNode
├── LiteralExpressionNode  
├── ComparisonExpressionNode
└── LogicalOperationNode
```

**Responsibilities:**
- Abstract representation of logical expressions
- Language-agnostic expression structure
- Visitor pattern support for traversal

#### 2. Expression System Registry
```
ExpressionSystemRegistry
├── NarwhalsExpressionSystem
├── SQLAlchemyExpressionSystem
├── IbisExpressionSystem
├── MongoDBExpressionSystem
└── DjangoORMExpressionSystem
```

**Responsibilities:**
- Discovery and registration of available expression systems
- Capability reporting (supported logic types, operations)
- Backend-specific visitor factory

#### 3. Logic-Aware Expression Visitors
```
For each ExpressionSystem:
├── BooleanExpressionVisitor
├── TernaryExpressionVisitor
└── FuzzyExpressionVisitor
```

**Responsibilities:**
- Convert abstract expression tree to backend-specific expressions
- Handle logic type semantics for target backend
- Optimize expressions using backend capabilities

#### 4. Universal Expression Facade
```
UniversalExpression
├── compile(backend, logic_type) → BackendExpression
├── supports(backend, logic_type) → boolean
└── optimize_for(backend) → UniversalExpression
```

**Responsibilities:**
- User-friendly interface to expression system
- Backend capability validation
- Expression compilation orchestration

### Expression System Interface

Each expression system must implement the `ExpressionSystem` protocol:

```python
class ExpressionSystem(Protocol):
    """Protocol that all expression systems must implement."""
    
    # Core expression building
    def col(self, name: str) -> Any: ...
    def lit(self, value: Any) -> Any: ...
    
    # Logical operations
    def and_(self, left: Any, right: Any) -> Any: ...
    def or_(self, left: Any, right: Any) -> Any: ...
    def not_(self, expr: Any) -> Any: ...
    def xor(self, left: Any, right: Any) -> Any: ...
    
    # Comparison operations  
    def eq(self, left: Any, right: Any) -> Any: ...
    def ne(self, left: Any, right: Any) -> Any: ...
    def gt(self, left: Any, right: Any) -> Any: ...
    def lt(self, left: Any, right: Any) -> Any: ...
    def ge(self, left: Any, right: Any) -> Any: ...
    def le(self, left: Any, right: Any) -> Any: ...
    def is_in(self, expr: Any, values: list) -> Any: ...
    
    # Null handling
    def is_null(self, expr: Any) -> Any: ...
    def is_not_null(self, expr: Any) -> Any: ...
    
    # Logic type support
    def supports_logic_type(self, logic_type: str) -> bool: ...
    def get_logic_visitor(self, logic_type: str) -> Type[ExpressionVisitor]: ...
    
    # Backend identification
    def get_backend_id(self) -> str: ...
    def get_native_type(self) -> type: ...
```

### Backend Capability Matrix

| Expression System | Boolean | Ternary | Fuzzy | Native Support | Notes |
|------------------|---------|---------|-------|----------------|-------|
| **Narwhals** | ✓ | Emulated | Emulated | Multi-dataframe | Integer encoding for ternary |
| **SQLAlchemy** | ✓ | ✓ | Emulated | SQL databases | Native NULL handling |
| **Ibis** | ✓ | ✓ | Varies | Analytical SQL | Depends on backend engine |
| **MongoDB** | ✓ | ✓ | ✓ | NoSQL document | Native $exists, numeric ranges |
| **Django ORM** | ✓ | Emulated | Emulated | Django models | Q objects with isnull |
| **PySpark SQL** | ✓ | ✓ | Emulated | Distributed | Native NULL in SQL |
| **DuckDB** | ✓ | ✓ | Emulated | In-process SQL | Fast analytical queries |

### Logic Type Implementation Strategies

#### Boolean Logic
- **Native Support**: All backends support boolean operations
- **Implementation**: Direct mapping to backend boolean operations

#### Ternary Logic (TRUE/FALSE/UNKNOWN)
- **Native Support**: SQL-based backends (NULL semantics)
- **Emulation Strategies**:
  - Integer encoding: 0=FALSE, 1=UNKNOWN, 2=TRUE (Narwhals)
  - Nullable boolean with special handling (Django ORM)
  - Document field existence checking (MongoDB)

#### Fuzzy Logic (0.0 to 1.0 continuous)
- **Native Support**: MongoDB (numeric ranges)
- **Emulation Strategies**:
  - Float columns with range validation (SQL/Narwhals)
  - Custom field types (Django)
  - Probabilistic interpretation of boolean (where forced)

### Visitor Architecture

#### Base Visitor Interface
```python
class ExpressionVisitor(ABC):
    """Base visitor for expression compilation."""
    
    def __init__(self, expression_system: ExpressionSystem):
        self.backend = expression_system
    
    @abstractmethod
    def visit_logical_operation(self, node: LogicalOperationNode) -> Any: ...
    
    @abstractmethod 
    def visit_comparison(self, node: ComparisonExpressionNode) -> Any: ...
    
    @abstractmethod
    def visit_column(self, node: ColumnExpressionNode) -> Any: ...
    
    @abstractmethod
    def visit_literal(self, node: LiteralExpressionNode) -> Any: ...
```

#### Logic-Specific Visitor Interfaces
```python
class BooleanExpressionVisitor(ExpressionVisitor):
    """Visitor for standard boolean logic."""
    
    def visit_and(self, operands: List[Any]) -> Any:
        # Standard boolean AND semantics
        pass
    
    def visit_or(self, operands: List[Any]) -> Any:
        # Standard boolean OR semantics  
        pass

class TernaryExpressionVisitor(ExpressionVisitor):
    """Visitor for three-valued logic."""
    
    def visit_and(self, operands: List[Any]) -> Any:
        # Kleene/SQL NULL semantics
        pass
        
    def visit_is_unknown(self, operand: Any) -> Any:
        # Check for UNKNOWN/NULL state
        pass

class FuzzyExpressionVisitor(ExpressionVisitor):
    """Visitor for fuzzy/probabilistic logic."""
    
    def visit_and(self, operands: List[Any]) -> Any:
        # Product t-norm or minimum t-norm
        pass
        
    def visit_degree(self, operand: Any) -> Any:
        # Return membership degree [0,1]
        pass
```

### Expression Compilation Pipeline

#### 1. Expression Construction Phase
```
User Code → LogicalExpressionNode Tree
```
- Pure abstract expression construction
- No backend-specific code
- No evaluation or table context required

#### 2. Backend Selection Phase
```
ExpressionTree + Backend + LogicType → Visitor Selection
```
- Capability validation (backend supports logic type)
- Visitor instantiation for backend/logic combination
- Optimization hint processing

#### 3. Compilation Phase
```
ExpressionTree + Visitor → BackendExpression
```
- Tree traversal using visitor pattern
- Backend-specific expression construction
- Logic type semantic preservation

#### 4. Execution Phase
```
BackendExpression + ExecutionContext → Results
```
- Backend-specific execution (filter, select, etc.)
- Native performance optimization
- Result materialization

### Error Handling Strategy

#### Compilation Errors
- **Unsupported Logic Type**: Clear message with supported alternatives
- **Unsupported Operation**: Suggestion for equivalent operations
- **Type Mismatch**: Backend-specific type requirements

#### Runtime Errors  
- **Backend Unavailable**: Graceful degradation to alternative backends
- **Expression Complexity**: Automatic simplification or chunking
- **Resource Limits**: Memory/time limits with partial results

### Extension Points

#### Custom Expression Systems
```python
class CustomExpressionSystem(ExpressionSystem):
    """User-defined expression system."""
    
    def register_custom_operation(self, name: str, impl: Callable): ...
    def add_logic_type(self, logic_type: str, visitor: Type[ExpressionVisitor]): ...
```

#### Custom Logic Types
```python
class QuantumLogicVisitor(ExpressionVisitor):
    """Example: Quantum superposition logic."""
    
    def visit_superposition(self, operands: List[Any]) -> Any: ...
    def visit_entanglement(self, left: Any, right: Any) -> Any: ...
```

#### Backend Plugins
```python
class BackendPlugin:
    def get_expression_system(self) -> ExpressionSystem: ...
    def get_supported_logic_types(self) -> List[str]: ...
    def get_optimization_hints(self) -> Dict[str, Any]: ...
```

This architecture maintains your existing visitor pattern and logic types while enabling expression compilation to any backend system, providing true universality in logical expression evaluation.