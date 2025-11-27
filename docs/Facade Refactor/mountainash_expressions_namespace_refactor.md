# MountainAsh Expressions: Fluent API Namespace Refactor

## Overview

This document describes the refactoring of `mountainash_expressions` from a mixin-based fluent API to a descriptor-based namespace architecture. The goal is to improve composability, enable facade variants (boolean vs ternary logic), and maintain a clean separation of concerns.

---

## Current Architecture

### Structure

```
ExpressionAPI (facade)
├── inherits: BaseExpressionAPI
├── inherits: BooleanExpressionBuilder (mixin)
├── inherits: StringExpressionBuilder (mixin)
├── inherits: NameExpressionBuilder (mixin)
└── ... other mixins
```

### Characteristics

- All methods are flat on the facade class
- Each mixin returns `ExpressionBuilder` or `BaseExpressionBuilder`
- No logical grouping of operations at runtime
- Difficult to swap operation implementations (e.g., boolean vs ternary logic)

### Example Current Usage

```python
col("a").eq(5).and_(col("b").gt(3))
col("name").upper().alias("NAME")
```

---

## Target Architecture

### Structure

```
BaseExpressionAPI (abstract base)
├── Explicit namespaces (descriptors):
│   ├── .str  → StringNamespace
│   ├── .dt   → DateNamespace
│   └── .name → NameNamespace
├── Flat namespaces (via __getattr__):
│   ├── ComparisonNamespace (eq, ne, gt, lt, ge, le)
│   ├── LogicalNamespace (and_, or_, not_, xor)
│   └── ArithmeticNamespace (add, sub, mul, div, mod)
└── _FLAT_NAMESPACES: tuple[type[BaseNamespace], ...]

BooleanExpressionAPI(BaseExpressionAPI)
└── _FLAT_NAMESPACES = (BooleanComparisonNamespace, BooleanLogicalNamespace, ArithmeticNamespace)

TernaryExpressionAPI(BaseExpressionAPI)
└── _FLAT_NAMESPACES = (TernaryComparisonNamespace, TernaryLogicalNamespace, ArithmeticNamespace)
```

### Target Usage (Unchanged)

```python
col("a").eq(5).and_(col("b").gt(3))      # Flat methods still work
col("name").str.upper().name.alias("NAME")  # Explicit namespaces
```

---

## Design Decisions

### 1. Descriptor-Based Explicit Namespaces

Domain-specific operations (`.str`, `.dt`, `.name`) use descriptors that lazily bind namespace instances to the facade.

**Rationale:** Clean separation, IDE discoverability, no wrapper boilerplate.

### 2. `__getattr__` Dispatch for Flat Namespaces

Universal operations (comparison, logical, arithmetic) are searched via `__getattr__` across a tuple of namespace classes.

**Rationale:** Keeps the API surface flat for common operations while allowing namespace swapping.

### 3. Facade Composition via `_FLAT_NAMESPACES`

Different facade variants (boolean, ternary) compose different namespace implementations.

**Rationale:** Enables swapping logic implementations without touching shared code.

### 4. Explicit Coercion in Builder Layer

When mixing logic types (e.g., ternary node used in boolean context), the builder explicitly wraps with coercion nodes (e.g., `IS_TRUE`).

**Rationale:** AST is portable and serialisable — what you see is what executes. Visitors stay dumb.

### 5. `create()` Factory Pattern

All namespaces use `self._api.create(node)` to return new facade instances, preserving the concrete facade type.

**Rationale:** `TernaryExpressionAPI` methods return `TernaryExpressionAPI`, not base class.

---

## Implementation

### File Structure

```
mountainash_expressions/
├── core/
│   ├── __init__.py
│   ├── expression_nodes/
│   │   └── ... (unchanged)
│   ├── protocols/
│   │   └── ... (unchanged)
│   ├── expression_api/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseExpressionAPI
│   │   ├── boolean.py           # BooleanExpressionAPI
│   │   ├── ternary.py           # TernaryExpressionAPI
│   │   └── descriptor.py        # NamespaceDescriptor
│   └── namespaces/
│       ├── __init__.py
│       ├── base.py              # BaseNamespace
│       ├── string.py            # StringNamespace
│       ├── date.py              # DateNamespace
│       ├── name.py              # NameNamespace
│       ├── comparison/
│       │   ├── __init__.py
│       │   ├── boolean.py       # BooleanComparisonNamespace
│       │   └── ternary.py       # TernaryComparisonNamespace
│       ├── logical/
│       │   ├── __init__.py
│       │   ├── boolean.py       # BooleanLogicalNamespace
│       │   └── ternary.py       # TernaryLogicalNamespace
│       └── arithmetic.py        # ArithmeticNamespace (shared)
```

### Component Implementations

#### 1. NamespaceDescriptor (`expression_api/descriptor.py`)

```python
"""Descriptor for binding namespace classes to ExpressionAPI instances."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from .base import BaseExpressionAPI

T = TypeVar("T")


class NamespaceDescriptor(Generic[T]):
    """
    Descriptor that lazily binds a namespace class to an ExpressionAPI instance.
    
    When accessed on a class, returns the descriptor itself.
    When accessed on an instance, returns a namespace instance bound to that API.
    
    Example:
        class ExpressionAPI:
            str = NamespaceDescriptor(StringNamespace)
        
        api = ExpressionAPI(node)
        api.str  # Returns StringNamespace(api)
    """
    
    def __init__(self, namespace_cls: type[T]) -> None:
        """
        Initialise the descriptor.
        
        Args:
            namespace_cls: The namespace class to instantiate on access.
        """
        self._namespace_cls = namespace_cls
    
    def __get__(
        self,
        obj: BaseExpressionAPI | None,
        objtype: type[BaseExpressionAPI] | None = None,
    ) -> T | NamespaceDescriptor[T]:
        """
        Return namespace instance bound to the accessing API instance.
        
        Args:
            obj: The instance accessing the descriptor (None if class access).
            objtype: The class owning the descriptor.
            
        Returns:
            Namespace instance if accessed on instance, descriptor if accessed on class.
        """
        if obj is None:
            return self
        return self._namespace_cls(obj)
```

#### 2. BaseNamespace (`namespaces/base.py`)

```python
"""Base class for expression namespaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes import ExpressionNode


class BaseNamespace:
    """
    Base class for all expression namespaces.
    
    Provides shared utilities for node access, value conversion, and building
    new API instances. Subclasses implement domain-specific operations.
    
    Attributes:
        _api: The parent ExpressionAPI instance this namespace is bound to.
    """
    
    def __init__(self, api: BaseExpressionAPI) -> None:
        """
        Initialise the namespace.
        
        Args:
            api: The parent ExpressionAPI instance.
        """
        self._api = api
    
    @property
    def _node(self) -> ExpressionNode:
        """Access the current expression node from the parent API."""
        return self._api._node
    
    def _to_node_or_value(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> ExpressionNode:
        """
        Convert input to an ExpressionNode, applying coercion if needed.
        
        Args:
            other: Value, node, or API instance to convert.
            
        Returns:
            ExpressionNode representing the input, possibly coerced.
        """
        node = self._api._to_node_or_value(other)
        return self._coerce_if_needed(node)
    
    def _coerce_if_needed(self, node: ExpressionNode) -> ExpressionNode:
        """
        Apply type coercion to a node if required by this namespace.
        
        Override in subclasses that require specific input types.
        Default implementation returns the node unchanged.
        
        Args:
            node: The node to potentially coerce.
            
        Returns:
            The original node or a wrapped coercion node.
        """
        return node
    
    def _build(self, node: ExpressionNode) -> BaseExpressionAPI:
        """
        Return a new API instance with the given node.
        
        Uses the parent API's create() factory to preserve the concrete type.
        
        Args:
            node: The new expression node.
            
        Returns:
            New ExpressionAPI instance of the same type as the parent.
        """
        return self._api.create(node)
```

#### 3. BaseExpressionAPI (`expression_api/base.py`)

```python
"""Base class for expression API facades."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, Union

from .descriptor import NamespaceDescriptor
from ..namespaces.string import StringNamespace
from ..namespaces.date import DateNamespace
from ..namespaces.name import NameNamespace
from ..namespaces.base import BaseNamespace

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode


class BaseExpressionAPI:
    """
    Abstract base class for fluent expression API facades.
    
    Provides:
    - Explicit namespaces via descriptors (.str, .dt, .name)
    - Flat method dispatch via __getattr__ for _FLAT_NAMESPACES
    - Factory method for creating new instances preserving type
    
    Subclasses define _FLAT_NAMESPACES to compose their operation set.
    
    Attributes:
        _node: The current expression node.
    """
    
    # Explicit namespaces — always available
    str = NamespaceDescriptor(StringNamespace)
    dt = NamespaceDescriptor(DateNamespace)
    name = NamespaceDescriptor(NameNamespace)
    
    # Subclasses override to define flat namespace composition
    _FLAT_NAMESPACES: tuple[type[BaseNamespace], ...] = ()
    
    def __init__(self, node: ExpressionNode) -> None:
        """
        Initialise the API with an expression node.
        
        Args:
            node: The root expression node.
        """
        self._node = node
    
    @classmethod
    def create(cls, node: ExpressionNode) -> Self:
        """
        Factory method for creating new API instances.
        
        Preserves the concrete class type when called from subclasses.
        
        Args:
            node: The expression node for the new instance.
            
        Returns:
            New instance of the concrete API class.
        """
        return cls(node)
    
    def __getattr__(self, name: str) -> Any:
        """
        Dispatch attribute access to flat namespaces.
        
        Searches _FLAT_NAMESPACES in order for the requested attribute.
        Raises AttributeError if not found in any namespace.
        
        Args:
            name: The attribute name to look up.
            
        Returns:
            The bound method from the first namespace containing it.
            
        Raises:
            AttributeError: If no namespace contains the attribute.
        """
        for ns_cls in self._FLAT_NAMESPACES:
            ns = ns_cls(self)
            if hasattr(ns, name):
                return getattr(ns, name)
        raise AttributeError(
            f"'{type(self).__name__}' has no attribute '{name}'"
        )
    
    def _to_node_or_value(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> ExpressionNode:
        """
        Convert input to an ExpressionNode.
        
        Handles:
        - ExpressionAPI instances: extracts ._node
        - ExpressionNode instances: returns as-is
        - Other values: wraps in LiteralNode
        
        Args:
            other: The value to convert.
            
        Returns:
            An ExpressionNode representing the input.
        """
        if isinstance(other, BaseExpressionAPI):
            return other._node
        if isinstance(other, ExpressionNode):
            return other
        # Import here to avoid circular dependency
        from ..expression_nodes import LiteralNode
        return LiteralNode(other)
    
    def compile(self, target: str | Any) -> Any:
        """
        Compile the expression tree to a target backend.
        
        Args:
            target: Backend identifier string ('polars', 'ibis', etc.)
                    or a DataFrame instance to infer backend from.
                    
        Returns:
            Backend-specific expression (e.g., pl.Expr, ibis.Expr).
        """
        visitor = self._create_visitor(target)
        return visitor.visit(self._node)
    
    def _create_visitor(self, target: str | Any) -> Any:
        """
        Create the appropriate visitor for the target backend.
        
        Args:
            target: Backend identifier or DataFrame instance.
            
        Returns:
            Configured visitor with injected expression systems.
        """
        # Implementation depends on existing visitor factory
        from ..visitors import ExpressionVisitorFactory
        return ExpressionVisitorFactory.create(target)
```

#### 4. BooleanExpressionAPI (`expression_api/boolean.py`)

```python
"""Boolean logic expression API facade."""

from __future__ import annotations

from .base import BaseExpressionAPI
from ..namespaces.comparison.boolean import BooleanComparisonNamespace
from ..namespaces.logical.boolean import BooleanLogicalNamespace
from ..namespaces.arithmetic import ArithmeticNamespace


class BooleanExpressionAPI(BaseExpressionAPI):
    """
    Expression API with standard two-valued boolean logic.
    
    Flat namespaces:
    - BooleanComparisonNamespace: eq, ne, gt, lt, ge, le
    - BooleanLogicalNamespace: and_, or_, not_, xor
    - ArithmeticNamespace: add, sub, mul, div, mod
    """
    
    _FLAT_NAMESPACES = (
        BooleanComparisonNamespace,
        BooleanLogicalNamespace,
        ArithmeticNamespace,
    )
```

#### 5. TernaryExpressionAPI (`expression_api/ternary.py`)

```python
"""Ternary logic expression API facade."""

from __future__ import annotations

from .base import BaseExpressionAPI
from ..namespaces.comparison.ternary import TernaryComparisonNamespace
from ..namespaces.logical.ternary import TernaryLogicalNamespace
from ..namespaces.arithmetic import ArithmeticNamespace


class TernaryExpressionAPI(BaseExpressionAPI):
    """
    Expression API with three-valued ternary logic (true/false/unknown).
    
    Flat namespaces:
    - TernaryComparisonNamespace: eq, ne, gt, lt, ge, le (return ternary)
    - TernaryLogicalNamespace: and_, or_, not_, xor (Kleene logic)
    - ArithmeticNamespace: add, sub, mul, div, mod (shared)
    """
    
    _FLAT_NAMESPACES = (
        TernaryComparisonNamespace,
        TernaryLogicalNamespace,
        ArithmeticNamespace,
    )
```

#### 6. Example Namespace: BooleanComparisonNamespace (`namespaces/comparison/boolean.py`)

```python
"""Boolean comparison operations namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..base import BaseNamespace
from ...protocols import BooleanBuilderProtocol, ENUM_BOOLEAN_OPERATORS
from ...expression_nodes import BooleanComparisonExpressionNode

if TYPE_CHECKING:
    from ...expression_api.base import BaseExpressionAPI
    from ...expression_nodes import ExpressionNode


class BooleanComparisonNamespace(BaseNamespace, BooleanBuilderProtocol):
    """
    Comparison operations producing boolean results.
    
    Methods:
        eq: Equal to (==)
        ne: Not equal to (!=)
        gt: Greater than (>)
        lt: Less than (<)
        ge: Greater than or equal (>=)
        le: Less than or equal (<=)
    """
    
    def eq(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Equal to (==).
        
        Args:
            other: Value or expression to compare with.
            
        Returns:
            New ExpressionAPI with comparison node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.EQ,
            self._node,
            other_node,
        )
        return self._build(node)
    
    def ne(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Not equal to (!=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NE,
            self._node,
            other_node,
        )
        return self._build(node)
    
    def gt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than (>)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GT,
            self._node,
            other_node,
        )
        return self._build(node)
    
    def lt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Less than (<)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LT,
            self._node,
            other_node,
        )
        return self._build(node)
    
    def ge(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Greater than or equal (>=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GE,
            self._node,
            other_node,
        )
        return self._build(node)
    
    def le(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Less than or equal (<=)."""
        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LE,
            self._node,
            other_node,
        )
        return self._build(node)
```

#### 7. Example Namespace with Coercion: BooleanLogicalNamespace (`namespaces/logical/boolean.py`)

```python
"""Boolean logical operations namespace with ternary coercion."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..base import BaseNamespace
from ...protocols import ENUM_BOOLEAN_OPERATORS, CONST_LOGIC_TYPES
from ...expression_nodes import (
    BooleanBinaryExpressionNode,
    BooleanUnaryExpressionNode,
    ExpressionNode,
)

if TYPE_CHECKING:
    from ...expression_api.base import BaseExpressionAPI


class BooleanLogicalNamespace(BaseNamespace):
    """
    Logical operations for boolean expressions.
    
    Automatically coerces ternary inputs to boolean via IS_TRUE.
    
    Methods:
        and_: Logical AND
        or_: Logical OR
        not_: Logical NOT
        xor: Logical XOR
    """
    
    def _coerce_if_needed(self, node: ExpressionNode) -> ExpressionNode:
        """
        Coerce ternary nodes to boolean via IS_TRUE wrapper.
        
        Args:
            node: The node to potentially coerce.
            
        Returns:
            Original node if boolean, wrapped node if ternary.
        """
        logic_type = getattr(node, "logic_type", None)
        if logic_type == CONST_LOGIC_TYPES.TERNARY:
            return BooleanUnaryExpressionNode(
                ENUM_BOOLEAN_OPERATORS.IS_TRUE,
                node,
            )
        return node
    
    def and_(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical AND.
        
        Args:
            other: Expression to AND with.
            
        Returns:
            New ExpressionAPI with AND node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanBinaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.AND,
            self._coerce_if_needed(self._node),
            other_node,
        )
        return self._build(node)
    
    def or_(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical OR.
        
        Args:
            other: Expression to OR with.
            
        Returns:
            New ExpressionAPI with OR node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanBinaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.OR,
            self._coerce_if_needed(self._node),
            other_node,
        )
        return self._build(node)
    
    def not_(self) -> BaseExpressionAPI:
        """
        Logical NOT.
        
        Returns:
            New ExpressionAPI with NOT node.
        """
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NOT,
            self._coerce_if_needed(self._node),
        )
        return self._build(node)
    
    def xor(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical XOR.
        
        Args:
            other: Expression to XOR with.
            
        Returns:
            New ExpressionAPI with XOR node.
        """
        other_node = self._to_node_or_value(other)
        node = BooleanBinaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.XOR,
            self._coerce_if_needed(self._node),
            other_node,
        )
        return self._build(node)
```

#### 8. NameNamespace (`namespaces/name.py`)

```python
"""Column name/alias operations namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseNamespace
from ..protocols import NameBuilderProtocol, ENUM_NAME_OPERATORS
from ..expression_nodes import (
    NameAliasExpressionNode,
    NamePrefixExpressionNode,
    NameSuffixExpressionNode,
    NameExpressionNode,
)

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI


class NameNamespace(BaseNamespace, NameBuilderProtocol):
    """
    Column name/alias operations.
    
    Operates on column metadata, not values. Always valid regardless
    of expression type.
    
    Methods:
        alias: Rename the expression
        prefix: Add prefix to column name
        suffix: Add suffix to column name
        to_upper: Convert column name to uppercase
        to_lower: Convert column name to lowercase
    """
    
    def alias(self, value: str) -> BaseExpressionAPI:
        """
        Rename the expression/column.
        
        Args:
            value: New name for the expression.
            
        Returns:
            New ExpressionAPI with alias node.
        """
        node = NameAliasExpressionNode(
            ENUM_NAME_OPERATORS.ALIAS,
            self._node,
            value,
        )
        return self._build(node)
    
    def prefix(self, value: str) -> BaseExpressionAPI:
        """
        Add prefix to column name.
        
        Args:
            value: Prefix to add.
            
        Returns:
            New ExpressionAPI with prefix node.
        """
        node = NamePrefixExpressionNode(
            ENUM_NAME_OPERATORS.NAME_PREFIX,
            self._node,
            value,
        )
        return self._build(node)
    
    def suffix(self, value: str) -> BaseExpressionAPI:
        """
        Add suffix to column name.
        
        Args:
            value: Suffix to add.
            
        Returns:
            New ExpressionAPI with suffix node.
        """
        node = NameSuffixExpressionNode(
            ENUM_NAME_OPERATORS.NAME_SUFFIX,
            self._node,
            value,
        )
        return self._build(node)
    
    def to_upper(self) -> BaseExpressionAPI:
        """
        Convert column name to uppercase.
        
        Returns:
            New ExpressionAPI with uppercase name node.
        """
        node = NameExpressionNode(
            ENUM_NAME_OPERATORS.NAME_TO_UPPER,
            self._node,
        )
        return self._build(node)
    
    def to_lower(self) -> BaseExpressionAPI:
        """
        Convert column name to lowercase.
        
        Returns:
            New ExpressionAPI with lowercase name node.
        """
        node = NameExpressionNode(
            ENUM_NAME_OPERATORS.NAME_TO_LOWER,
            self._node,
        )
        return self._build(node)
```

---

## Migration Steps

### Phase 1: Infrastructure

1. Create `expression_api/descriptor.py` with `NamespaceDescriptor`
2. Create `namespaces/base.py` with `BaseNamespace`
3. Create `expression_api/base.py` with `BaseExpressionAPI`
4. Add tests for descriptor binding and `__getattr__` dispatch

### Phase 2: Namespace Conversion

For each existing mixin:

1. Create corresponding namespace class in `namespaces/`
2. Inherit from `BaseNamespace` and appropriate protocol
3. Convert methods:
   - Replace `self._node` access (unchanged)
   - Replace `self._to_node_or_value()` calls (unchanged)
   - Replace `return ExpressionBuilder(node)` with `return self._build(node)`
4. Add coercion logic to `_coerce_if_needed()` if needed
5. Add tests for the namespace in isolation

**Conversion order (suggested):**

1. `NameNamespace` — simplest, no coercion
2. `StringNamespace` — no coercion, many methods
3. `ArithmeticNamespace` — shared across facades
4. `BooleanComparisonNamespace` — foundation for boolean facade
5. `BooleanLogicalNamespace` — includes coercion
6. `TernaryComparisonNamespace` — ternary variant
7. `TernaryLogicalNamespace` — ternary variant with Kleene logic
8. `DateNamespace` — if exists

### Phase 3: Facade Assembly

1. Create `BooleanExpressionAPI` with appropriate `_FLAT_NAMESPACES`
2. Create `TernaryExpressionAPI` with ternary namespaces
3. Update `col()` factory to return appropriate facade
4. Deprecate old mixin-based `ExpressionAPI`

### Phase 4: Cleanup

1. Remove old mixin classes
2. Update imports throughout codebase
3. Update documentation
4. Remove deprecation warnings after transition period

---

## Testing Strategy

### Unit Tests

```python
# test_descriptor.py
class TestNamespaceDescriptor:
    def test_class_access_returns_descriptor(self):
        assert isinstance(BooleanExpressionAPI.str, NamespaceDescriptor)
    
    def test_instance_access_returns_namespace(self):
        api = BooleanExpressionAPI(mock_node)
        assert isinstance(api.str, StringNamespace)
    
    def test_namespace_bound_to_correct_api(self):
        api = BooleanExpressionAPI(mock_node)
        ns = api.str
        assert ns._api is api


# test_getattr_dispatch.py
class TestGetAttrDispatch:
    def test_flat_method_found(self):
        api = BooleanExpressionAPI(mock_node)
        assert callable(api.eq)
    
    def test_unknown_attribute_raises(self):
        api = BooleanExpressionAPI(mock_node)
        with pytest.raises(AttributeError):
            api.nonexistent_method
    
    def test_search_order_respected(self):
        # If method exists in multiple namespaces, first wins
        ...


# test_coercion.py
class TestTernaryCoercion:
    def test_ternary_coerced_in_boolean_context(self):
        bool_api = BooleanExpressionAPI(bool_node)
        ternary_api = TernaryExpressionAPI(ternary_node)
        
        result = bool_api.and_(ternary_api)
        
        # Assert the ternary operand is wrapped in IS_TRUE
        assert isinstance(result._node.right, BooleanUnaryExpressionNode)
        assert result._node.right.operator == ENUM_BOOLEAN_OPERATORS.IS_TRUE
```

### Integration Tests

```python
# test_integration.py
class TestFluentChaining:
    def test_cross_namespace_chaining(self):
        result = col("name").str.upper().name.alias("NAME").eq("JOHN")
        compiled = result.compile("polars")
        # Assert correct Polars expression
    
    def test_facade_type_preserved(self):
        api = TernaryExpressionAPI(mock_node)
        result = api.gt(5)
        assert isinstance(result, TernaryExpressionAPI)
    
    def test_mixed_logic_compilation(self):
        bool_expr = col("a").gt(5)  # BooleanExpressionAPI
        tern_expr = tcol("b").lt(3)  # TernaryExpressionAPI
        
        result = bool_expr.and_(tern_expr)
        compiled = result.compile("polars")
        # Assert IS_TRUE coercion present in output
```

---

## Backward Compatibility

### Deprecation Path

```python
# Old API (deprecated)
class ExpressionAPI(BaseExpressionAPI, BooleanExpressionBuilder, ...):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "ExpressionAPI is deprecated. Use BooleanExpressionAPI or "
            "TernaryExpressionAPI instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
```

### col() Factory

```python
def col(name: str, logic: Literal["boolean", "ternary"] = "boolean") -> BaseExpressionAPI:
    """
    Create a column reference expression.
    
    Args:
        name: Column name.
        logic: Logic system to use ("boolean" or "ternary").
        
    Returns:
        ExpressionAPI configured for the specified logic system.
    """
    node = ColumnReferenceNode(name)
    if logic == "ternary":
        return TernaryExpressionAPI(node)
    return BooleanExpressionAPI(node)


# Convenience alias
def tcol(name: str) -> TernaryExpressionAPI:
    """Create a ternary logic column reference."""
    return col(name, logic="ternary")
```

---

## Future Extension: Configurable Unknown Value

### Motivation

Clickhouse and other columnar OLAP systems are architecturally optimised against NULL handling. Their recommended pattern is to use sentinel/default values (e.g., `-1`, `""`, `"UNKNOWN"`) rather than NULL. This trend is likely to grow as Clickhouse adoption increases.

The ternary logic system should support **configurable unknown representation** — not hardcoded to NULL semantics.

### Design

**TernaryExpressionAPI carries unknown configuration:**

```python
class TernaryExpressionAPI(BaseExpressionAPI):
    """Three-valued logic with configurable unknown representation."""
    
    _FLAT_NAMESPACES = (
        TernaryComparisonNamespace,
        TernaryLogicalNamespace,
        ArithmeticNamespace,
    )
    
    def __init__(
        self,
        node: ExpressionNode,
        unknown_value: Any = None,  # None = NULL semantics
    ) -> None:
        super().__init__(node)
        self._unknown_value = unknown_value
    
    @classmethod
    def create(
        cls,
        node: ExpressionNode,
        *,
        unknown_value: Any = None,
    ) -> Self:
        instance = cls(node)
        instance._unknown_value = unknown_value
        return instance
    
    def _with_unknown(self, unknown_value: Any) -> Self:
        """Return new API with different unknown representation."""
        return self.create(self._node, unknown_value=unknown_value)
```

**Namespaces propagate unknown value:**

```python
class BaseNamespace:
    @property
    def _unknown_value(self) -> Any:
        """Access unknown value from parent API, if applicable."""
        return getattr(self._api, "_unknown_value", None)
    
    def _build(self, node: ExpressionNode) -> BaseExpressionAPI:
        """Preserve unknown_value when building new API instance."""
        if hasattr(self._api, "_unknown_value"):
            return self._api.create(node, unknown_value=self._api._unknown_value)
        return self._api.create(node)
```

**Coercion nodes carry sentinel metadata:**

```python
class TernaryCoercionNode(ExpressionNode):
    """Coerce ternary to boolean, aware of unknown representation."""
    
    operator: ENUM_BOOLEAN_OPERATORS  # IS_TRUE, IS_FALSE, IS_UNKNOWN
    operand: ExpressionNode
    unknown_value: Any = Field(default=None)  # Serialised with the AST
```

**Backend emission adapts:**

```python
class PolarsExpressionSystem:
    def is_unknown(self, operand: pl.Expr, unknown_value: Any) -> pl.Expr:
        if unknown_value is None:
            return operand.is_null()
        return operand.eq(unknown_value)


class ClickhouseExpressionSystem:
    def is_unknown(self, operand: str, unknown_value: Any) -> str:
        if unknown_value is None:
            return f"isNull({operand})"
        return f"{operand} = {self._literal(unknown_value)}"
```

**Factory functions:**

```python
def tcol(
    name: str,
    unknown: Any = None,
) -> TernaryExpressionAPI:
    """
    Create a ternary logic column reference.
    
    Args:
        name: Column name.
        unknown: Value representing "unknown" state.
                 None (default) uses NULL semantics.
                 Pass sentinel value for Clickhouse-style handling.
    
    Examples:
        # Traditional NULL-based unknown
        tcol("status").is_unknown()  # Compiles to: col.is_null()
        
        # Clickhouse sentinel-based unknown
        tcol("status", unknown=-1).is_unknown()  # Compiles to: col == -1
    """
    node = ColumnReferenceNode(name)
    return TernaryExpressionAPI(node, unknown_value=unknown)
```

### Implementation Priority

This extension can be deferred until after the core namespace refactor is complete. The key requirement is that the architecture **does not preclude** this extension:

1. `TernaryExpressionAPI` must be a separate class (not just a flag on `BooleanExpressionAPI`)
2. The `create()` factory must support additional parameters
3. Coercion nodes must be able to carry metadata

The current design satisfies all three requirements.

---

## Notes for Implementation

1. **Import cycles:** Use `TYPE_CHECKING` guards liberally. The namespace → API → namespace cycle is real.

2. **Protocol compliance:** Ensure each namespace still implements its corresponding protocol for type checking.

3. **`Self` type:** Use `typing.Self` (Python 3.11+) or `TypeVar` bound to the class for `create()` return type.

4. **Performance:** `__getattr__` creates namespace instances on every access. If profiling shows this is hot, consider caching, but likely unnecessary.

5. **IDE support:** `__getattr__` methods won't autocomplete. Consider adding type stubs or a `py.typed` marker with overloads if IDE support is critical.

6. **Serialisation:** Ensure node classes remain the source of truth. The facade layer is ephemeral.
