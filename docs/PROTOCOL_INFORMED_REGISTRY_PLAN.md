# Substrait Alignment with Protocol-Driven Type Safety

## Problem Statement

The current Substrait alignment implementation lost key benefits of the protocol-driven architecture:
1. **Hardcoded strings** for function names and backend methods
2. **No type information** for argument handling (string literals vs expressions)
3. **Lost ENUM-based dispatch** - no compile-time exhaustiveness checking
4. **Lost protocol contracts** - no IDE support or type verification

## Proposed Solution: Protocol-Informed Registry

Keep the registry architecture but enhance it to use ENUMs and introspect protocols for type information.

### Core Principles

1. **ENUMs for function identification** - Replace all hardcoded function name strings
2. **Protocols for type contracts** - Use protocol method signatures for introspection
3. **Registry as mapping layer** - Maps ENUMs → Protocol methods → Backend methods
4. **Substrait nodes unchanged** - Keep ScalarFunctionNode etc. for serialization

### Architecture

```
User API (Namespaces)
       ↓
ScalarFunctionNode(function=SUBSTRAIT_FUNC.EQ, args=[...])
       ↓
FunctionRegistry.get(SUBSTRAIT_FUNC.EQ)
       ↓
FunctionDef(
    enum=SUBSTRAIT_FUNC.EQ,
    protocol=BooleanExpressionProtocol,
    method="eq",
    substrait_uri="..."
)
       ↓
UnifiedVisitor introspects BooleanExpressionProtocol.eq signature
       ↓
Resolves args based on type hints (str→raw, Any→expression)
       ↓
Calls backend.eq(*resolved_args)
```

## Implementation Plan

### Phase 1: Define Substrait-Aligned ENUMs

Create ENUMs that map to Substrait function URIs. Organize by Substrait extension category.

**File: `core/substrait_nodes/enums.py`**

```python
from enum import Enum

class SubstraitExtension:
    """Substrait extension URIs."""
    COMPARISON = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_comparison.yaml"
    BOOLEAN = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml"
    ARITHMETIC = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_arithmetic.yaml"
    STRING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_string.yaml"
    DATETIME = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_datetime.yaml"
    MOUNTAINASH = "https://mountainash.dev/extensions/functions_custom.yaml"

class SUBSTRAIT_COMPARISON(Enum):
    """Substrait comparison functions."""
    EQ = "equal"
    NE = "not_equal"
    GT = "gt"
    LT = "lt"
    GE = "gte"
    LE = "lte"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    COALESCE = "coalesce"
    BETWEEN = "between"
    # Value is the Substrait function name

class SUBSTRAIT_BOOLEAN(Enum):
    """Substrait boolean functions."""
    AND = "and"
    OR = "or"
    NOT = "not"
    XOR = "xor"

class SUBSTRAIT_ARITHMETIC(Enum):
    """Substrait arithmetic functions."""
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    MODULO = "modulus"
    POWER = "power"

class SUBSTRAIT_STRING(Enum):
    """Substrait string functions."""
    UPPER = "upper"
    LOWER = "lower"
    CONCAT = "concat"
    SUBSTRING = "substring"
    TRIM = "trim"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REPLACE = "replace"
    CHAR_LENGTH = "char_length"

class SUBSTRAIT_DATETIME(Enum):
    """Substrait datetime functions."""
    EXTRACT_YEAR = "extract"  # with component=YEAR
    EXTRACT_MONTH = "extract"
    EXTRACT_DAY = "extract"
    # etc.

class MOUNTAINASH_EXTENSION(Enum):
    """Mountainash custom extensions."""
    FLOOR_DIVIDE = "floor_divide"
    IS_CLOSE = "is_close"
    T_EQ = "ternary_equal"
    T_AND = "ternary_and"
    # etc.

# Union type for all function enums
SubstraitFunction = (
    SUBSTRAIT_COMPARISON |
    SUBSTRAIT_BOOLEAN |
    SUBSTRAIT_ARITHMETIC |
    SUBSTRAIT_STRING |
    SUBSTRAIT_DATETIME |
    MOUNTAINASH_EXTENSION
)
```

### Phase 2: Update FunctionDef to Reference Protocols

**File: `core/functions/registry.py`**

```python
from dataclasses import dataclass
from typing import Type, Protocol
from enum import Enum

@dataclass(frozen=True)
class FunctionDef:
    """Definition of a Substrait-aligned function."""

    # The enum identifying this function (replaces string 'name')
    func: Enum  # e.g., SUBSTRAIT_COMPARISON.EQ

    # The Substrait function name (for serialization)
    substrait_name: str  # e.g., "equal" - the actual Substrait spec name

    # The protocol that defines the method signature (for grouping/documentation)
    protocol: Type[Protocol]  # e.g., BooleanExpressionProtocol

    # Direct reference to the protocol method (not a string!)
    protocol_method: Callable  # e.g., BooleanExpressionProtocol.eq

    # Substrait extension URI (for serialization)
    extension_uri: str  # e.g., SubstraitExtension.COMPARISON

    # Category for organization
    category: str  # e.g., "comparison"

    @property
    def method_name(self) -> str:
        """Get the method name for backend dispatch."""
        return self.protocol_method.__name__


class FunctionRegistry:
    """Registry mapping Substrait functions to protocol methods."""

    _functions: dict[Enum, FunctionDef] = {}

    @classmethod
    def register(cls, func_def: FunctionDef) -> None:
        cls._functions[func_def.func] = func_def

    @classmethod
    def get(cls, func: Enum) -> FunctionDef:
        if func not in cls._functions:
            raise KeyError(f"Unknown function: {func}")
        return cls._functions[func]

    @classmethod
    def get_method_signature(cls, func: Enum) -> inspect.Signature:
        """Get the protocol method signature for introspection."""
        func_def = cls.get(func)
        # Direct reference - no getattr needed!
        return inspect.signature(func_def.protocol_method)
```

### Phase 3: Update Function Definitions

**File: `core/functions/definitions.py`**

```python
from ..protocols import (
    BooleanExpressionProtocol,
    ArithmeticExpressionProtocol,
    StringExpressionProtocol,
    # etc.
)
from .registry import FunctionRegistry, FunctionDef
from ..substrait_nodes.enums import *

def register_all_functions():
    """Register all function definitions."""

    # Comparison functions
    FunctionRegistry.register(FunctionDef(
        func=SUBSTRAIT_COMPARISON.EQ,
        substrait_name="equal",  # Substrait spec name
        protocol=BooleanExpressionProtocol,
        protocol_method=BooleanExpressionProtocol.eq,  # Direct reference!
        extension_uri=SubstraitExtension.COMPARISON,
        category="comparison",
    ))

    FunctionRegistry.register(FunctionDef(
        func=SUBSTRAIT_COMPARISON.GT,
        substrait_name="gt",
        protocol=BooleanExpressionProtocol,
        protocol_method=BooleanExpressionProtocol.gt,  # Direct reference!
        extension_uri=SubstraitExtension.COMPARISON,
        category="comparison",
    ))

    # String functions - direct method reference preserves type signature
    FunctionRegistry.register(FunctionDef(
        func=SUBSTRAIT_STRING.CONTAINS,
        substrait_name="contains",
        protocol=StringExpressionProtocol,
        protocol_method=StringExpressionProtocol.str_contains,  # Signature: (operand, substring: str)
        extension_uri=SubstraitExtension.STRING,
        category="string",
    ))

    # etc.
```

### Phase 4: Update ScalarFunctionNode

**File: `core/substrait_nodes/scalar_function.py`**

```python
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel
from .enums import SubstraitFunction

class ScalarFunctionNode(SubstraitNode):
    """Substrait scalar function call."""

    # ENUM instead of string!
    function: Enum  # SubstraitFunction union type

    arguments: List[SubstraitNode]
    options: Dict[str, Any] = {}

    def accept(self, visitor):
        return visitor.visit_scalar_function(self)

    @property
    def substrait_name(self) -> str:
        """Get Substrait function name for serialization."""
        return self.function.value
```

### Phase 5: Update UnifiedVisitor with Protocol Introspection

**File: `core/unified_visitor/visitor.py`**

```python
import inspect
from typing import get_type_hints

class UnifiedExpressionVisitor:
    """Visitor that uses protocol introspection for type-aware dispatch."""

    def __init__(self, expression_system):
        self.backend = expression_system
        self._signature_cache: dict[Enum, inspect.Signature] = {}

    def _get_signature(self, func: Enum) -> inspect.Signature:
        """Get cached protocol method signature."""
        if func not in self._signature_cache:
            self._signature_cache[func] = FunctionRegistry.get_method_signature(func)
        return self._signature_cache[func]

    def _resolve_argument(self, arg: SubstraitNode, param: inspect.Parameter) -> Any:
        """Resolve argument based on protocol type hint."""
        # If parameter expects a raw value type, extract from LiteralNode
        if param.annotation in (str, int, float, bool):
            if isinstance(arg, LiteralNode):
                return arg.value
            else:
                # Expression where literal expected - compile and let backend handle
                return self.visit(arg)
        else:
            # Expression expected - compile it
            return self.visit(arg)

    def visit_scalar_function(self, node: ScalarFunctionNode):
        """Compile scalar function using protocol introspection."""
        func_def = FunctionRegistry.get(node.function)
        sig = self._get_signature(node.function)

        # Get parameter list (skip 'self')
        params = list(sig.parameters.values())[1:]

        # Resolve arguments based on type hints
        args = []
        for arg, param in zip(node.arguments, params):
            args.append(self._resolve_argument(arg, param))

        # Get backend method - use method_name property from direct reference
        method = getattr(self.backend, func_def.method_name)

        if node.options:
            return method(*args, **node.options)
        return method(*args)
```

### Phase 6: Update Namespaces to Use ENUMs

**File: `core/namespaces/boolean.py`**

```python
from ..substrait_nodes import ScalarFunctionNode
from ..substrait_nodes.enums import SUBSTRAIT_COMPARISON, SUBSTRAIT_BOOLEAN

class BooleanNamespace(BaseNamespace):

    def eq(self, other) -> BaseExpressionAPI:
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function=SUBSTRAIT_COMPARISON.EQ,  # ENUM, not string!
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def and_(self, *others) -> BaseExpressionAPI:
        # Build pairwise chain with ENUM
        operands = [self._node] + [self._to_substrait_node(o) for o in others]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function=SUBSTRAIT_BOOLEAN.AND,  # ENUM!
                arguments=[result, operand],
            )
        return self._build(result)
```

### Phase 7: Update String Namespace (demonstrates type-hint benefit)

**File: `core/namespaces/string.py`**

```python
from ..substrait_nodes.enums import SUBSTRAIT_STRING

class StringNamespace(BaseNamespace):

    def contains(self, substring) -> BaseExpressionAPI:
        # substring will be resolved correctly because
        # StringExpressionProtocol.str_contains has signature:
        #   str_contains(self, operand: Any, substring: str)
        # The visitor will see `substring: str` and extract raw value

        substring_node = self._to_substrait_node(substring)
        node = ScalarFunctionNode(
            function=SUBSTRAIT_STRING.CONTAINS,
            arguments=[self._node, substring_node],
        )
        return self._build(node)
```

## Benefits of This Approach

1. **No hardcoded strings** - ENUMs provide compile-time checking
2. **IDE autocomplete** - ENUMs autocomplete, show all available functions
3. **Type-aware dispatch** - Protocol signatures tell us argument types
4. **Clear registry** - Maps ENUMs to protocols, maintainable
5. **Substrait alignment** - Explicit `substrait_name` field for serialization
6. **Protocol contracts preserved** - Signatures define the interface
7. **Direct method references** - `protocol_method` is a direct reference, not a string lookup
8. **IDE navigation** - Click through from FunctionDef to protocol method definition
9. **Refactoring safe** - Rename protocol methods and references update together
10. **Extensible** - Add new ENUMs and registry entries for new functions

## Files to Modify

1. `core/substrait_nodes/enums.py` - **CREATE** - Define all function ENUMs
2. `core/substrait_nodes/__init__.py` - Export new enums
3. `core/substrait_nodes/scalar_function.py` - Change `function: str` to `function: Enum`
4. `core/functions/registry.py` - Update FunctionDef to reference protocols
5. `core/functions/definitions.py` - Rewrite to use ENUMs and protocols
6. `core/unified_visitor/visitor.py` - Add protocol introspection
7. `core/namespaces/*.py` - Update all to use ENUMs instead of strings

## Migration Strategy (Incremental)

### Phase A: ENUMs (Compile-Time Safety)

**Goal:** Replace hardcoded strings with ENUMs for IDE autocomplete and exhaustiveness checking.

1. **A1:** Create `core/substrait_nodes/enums.py` with all ENUM definitions
   - SUBSTRAIT_COMPARISON, SUBSTRAIT_BOOLEAN, SUBSTRAIT_ARITHMETIC, etc.
   - Each ENUM value is the Substrait function name
   - Run tests (expect same failures - no behavior change)

2. **A2:** Update `ScalarFunctionNode.function` to accept `Enum` type
   - Keep string support for backward compatibility: `function: str | Enum`
   - Run tests (expect same failures)

3. **A3:** Update namespaces one category at a time to use ENUMs
   - Start with BooleanNamespace (smallest, most tested)
   - Then ArithmeticNamespace, StringNamespace, etc.
   - Run tests after each namespace update

4. **A4:** Update FunctionRegistry to key by ENUM instead of string
   - Update `get()` method signature
   - Run tests (expect same failures)

**Checkpoint A:** All namespaces use ENUMs, registry keys are ENUMs, full IDE support.

### Phase B: Protocol References (Type Contracts)

**Goal:** Add protocol references to FunctionDef for documentation and future introspection.

5. **B1:** Update `FunctionDef` dataclass to include protocol reference
   ```python
   protocol: Type[Protocol]  # e.g., BooleanExpressionProtocol
   method: str               # e.g., "eq"
   ```

6. **B2:** Update `definitions.py` to populate protocol references
   - Each function registration includes its protocol and method name
   - Run tests (expect same failures - no behavior change yet)

**Checkpoint B:** Registry maps ENUMs → Protocol methods. Type contracts documented.

### Phase C: Protocol Introspection (Type-Aware Dispatch)

**Goal:** Use protocol signatures to determine argument handling at runtime.

7. **C1:** Add signature caching to UnifiedVisitor
   ```python
   def _get_signature(self, func: Enum) -> inspect.Signature:
       if func not in self._signature_cache:
           func_def = FunctionRegistry.get(func)
           method = getattr(func_def.protocol, func_def.method)
           self._signature_cache[func] = inspect.signature(method)
       return self._signature_cache[func]
   ```

8. **C2:** Add `_resolve_argument()` method that uses type hints
   - If parameter annotation is `str`, `int`, `float`, `bool` → extract raw value from LiteralNode
   - If parameter annotation is `Any` → compile to expression
   - Run tests (expect MANY fixes!)

9. **C3:** Add `_resolve_options()` for keyword arguments
   - Same logic for options dictionary
   - Run tests

10. **C4:** Remove string-based fallbacks once all tests pass

**Checkpoint C:** Full type-aware dispatch. Tests should pass. 521 failures fixed.

## Design Decisions

1. **ENUMs organized by Substrait extension** - SUBSTRAIT_COMPARISON, SUBSTRAIT_BOOLEAN, SUBSTRAIT_STRING, etc. to match official Substrait spec
2. **Full introspection for options** - Protocol signatures define all parameters including options, not just positional args

## Enhanced Protocol Introspection for Options

Protocol methods should have full signatures including keyword arguments:

```python
# In StringExpressionProtocol
def str_contains(
    self,
    operand: Any,
    substring: str,  # Raw value
    *,
    literal: bool = True,  # Option with type hint
) -> SupportedExpressions: ...

def str_substring(
    self,
    operand: Any,
    *,
    start: int,    # Option with type
    length: int = None,  # Optional with type
) -> SupportedExpressions: ...

# In BooleanExpressionProtocol
def is_close(
    self,
    left: Any,
    right: Any,
    *,
    precision: float = 1e-5,  # Option with type and default
) -> SupportedExpressions: ...
```

The visitor introspects both positional and keyword parameters:

```python
def _resolve_options(self, options: Dict[str, Any], sig: inspect.Signature) -> Dict[str, Any]:
    """Resolve options based on protocol type hints."""
    resolved = {}
    for name, value in options.items():
        if name in sig.parameters:
            param = sig.parameters[name]
            # Type-check if annotation exists
            if param.annotation != inspect.Parameter.empty:
                # Could add runtime type validation here
                pass
        resolved[name] = value
    return resolved
```
