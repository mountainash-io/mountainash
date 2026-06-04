---
title: Expression Function Registry and Compilation
description: The function registry system, Substrait alignment, build-then-compile pattern, unified visitor, and protocol-based expression system architecture.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 7: Expression Function Registry and Compilation

## Summary

Substrait and Mountainash key prefixes, ExpressionFunctionDef, ExpressionFunctionRegistry, function lookup, Substrait spec alignment, build-then-compile pattern, expression compilation, unified visitor, API builder protocols, expression system protocols, and Mountainash extensions.

## Concepts Covered

- FKEY Substrait Prefix
- FKEY Mountainash Prefix
- ExpressionFunctionDef
- ExpressionFunctionRegistry
- Function Registry Lookup
- Substrait Spec Alignment
- Build Then Compile
- Expression Compilation
- Unified Expression Visitor
- API Builder Protocols
- Expression System Protocols
- Mountainash Extensions

## Prerequisites

- [Chapter 3. Expression API Basics](../03-expression-api-basics/)
- [Chapter 6. Expression AST and Function Keys](../06-expression-ast-and-function-keys/)

---

## Introduction

The previous chapters described how users build expression ASTs through the fluent API. This chapter explores the machinery that connects those ASTs to backend execution. The function registry maps every operation to its Substrait metadata and compilation method. The build-then-compile pattern separates construction from execution. The unified visitor traverses AST trees and dispatches to expression system implementations. Protocols define the contracts that backends must satisfy.

<!-- concept:67 -->
## FKEY Substrait Prefix

Functions whose semantics align with the Substrait specification use function keys from the Substrait-prefixed enum classes. These functions have well-defined behavior specified by the Substrait community, including standardized URIs that identify the function definition source.

The Substrait prefix encompasses operations that any compliant system should understand: comparison (`equal`, `not_equal`, `less_than`), arithmetic (`add`, `subtract`, `multiply`), boolean (`and`, `or`, `not`), string (`concat`, `like`), and datetime operations.

```python
# Substrait-aligned function keys come from standard enum classes
CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD       # Substrait: arithmetic.add
CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ  # Substrait: comparison.equal
CONST_EXPRESSION_STRING_OPERATORS.UPPER         # Substrait: string.upper
```

Each Substrait function has an associated URI pointing to the official extension YAML file where its signature and behavior are defined. This URI is stored in the `ExpressionFunctionDef` and used when serializing expressions to the Substrait protobuf format.

<!-- concept:68 -->
## FKEY Mountainash Prefix

Functions that extend beyond the Substrait specification use mountainash-prefixed function keys. These represent operations that mountainash provides for practical utility but that have no standard Substrait equivalent.

Mountainash extensions include the name namespace operations (alias, prefix, suffix), null handling extensions (fill_null beyond basic coalesce), native passthrough, ternary logic operations, and aggregate functions with custom semantics.

```python
# Mountainash extension function keys
# These use dedicated enum classes or the mountainash extension URI
MOUNTAINASH_URI = "https://mountainash.io/extensions/functions.yaml"
```

The extension prefix signals to downstream systems that these functions may not be portable to other Substrait-compliant tools. However, within mountainash's own compilation pipeline, they are handled identically to Substrait functions by the appropriate expression system implementations.

<!-- concept:69 -->
## ExpressionFunctionDef

`ExpressionFunctionDef` is a frozen dataclass that stores the complete definition of a single function in the registry. It maps between the internal function key, the Substrait metadata, and the compilation target.

```python
@dataclass(frozen=True)
class ExpressionFunctionDef:
    function_key: Enum
    substrait_uri: str | None
    substrait_name: str | None
    is_extension: bool = False
    options: tuple[str, ...] = field(default_factory=tuple)
    protocol_method: Optional[Callable] = None
```

Each field serves a specific purpose in the compilation pipeline:

- **function_key**: The enum value used in `ScalarFunctionNode` to identify this function
- **substrait_uri**: The URI for Substrait serialization (None for pure extensions)
- **substrait_name**: The function name within the Substrait extension (e.g., "add", "equal")
- **is_extension**: Whether this is a mountainash extension (not in standard Substrait)
- **options**: Valid option names this function accepts (stored in ScalarFunctionNode.options)
- **protocol_method**: Reference to the protocol method for signature introspection

The `get_signature()` method uses Python's `inspect.signature()` on the protocol method to provide type information about the function's parameters at introspection time.

<!-- concept:70 -->
## ExpressionFunctionRegistry

The `ExpressionFunctionRegistry` is a singleton container that holds all registered `ExpressionFunctionDef` instances. It provides lookup by function key and serves as the central authority for function metadata.

```python
class ExpressionFunctionRegistry:
    """Central registry mapping function keys to definitions."""

    def register(self, definition: ExpressionFunctionDef) -> None:
        """Register a function definition."""
        ...

    def lookup(self, function_key: Enum) -> ExpressionFunctionDef:
        """Look up a function definition by its key."""
        ...

    def all_definitions(self) -> list[ExpressionFunctionDef]:
        """Return all registered definitions."""
        ...
```

The registry is populated during module initialization. Each function category (arithmetic, comparison, string, etc.) registers its definitions when the expressions module loads. This lazy-but-complete registration ensures the registry is always available for compilation without requiring explicit setup.

#### Diagram: Function Registry Architecture
<iframe src="../../sims/function-registry-arch/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Function Registry Architecture</summary>
Type: diagram
**sim-id:** function-registry-arch<br/>
**Library:** vis-network<br/>
**Status:** Specified

A three-column architecture diagram. Left column: "API Layer" shows entry point functions (col, lit, when) and namespace methods (.str.upper, .dt.year). Middle column: "Registry" shows ExpressionFunctionRegistry as a central hub connecting function keys to ExpressionFunctionDef records. Right column: "Compilation Layer" shows expression system methods dispatched by the visitor. Edges connect API methods through the registry to their compilation targets. Clicking a function key in the registry shows its full ExpressionFunctionDef fields. Colors: DarkGreen for API, LimeGreen for AST/Registry, Gold for backends. Learning objective: Trace how a user API call maps through the function registry to a backend compilation method (Bloom: Analyze).
</details>

<!-- concept:71 -->
## Function Registry Lookup

Function registry lookup is the process by which the compilation system retrieves the metadata needed to compile a specific operation. When the visitor encounters a `ScalarFunctionNode`, it uses the node's `function_key` to look up the corresponding `ExpressionFunctionDef` from the registry.

The lookup provides the compiler with everything it needs: the backend method name to call, the expected argument structure, and any valid options. If a function key is not found in the registry, it indicates a programming error (a node was constructed with an unregistered key).

```python
# During compilation, the visitor does roughly:
fdef = registry.lookup(node.function_key)
backend_method = getattr(expression_system, fdef.backend_method)
result = backend_method(node)
```

The lookup is a dictionary access operation (\(O(1)\) time complexity), making it negligible in the overall compilation cost.

<!-- concept:72 -->
## Substrait Spec Alignment

Substrait spec alignment refers to mountainash's strategy of aligning its function semantics and naming with the Substrait specification wherever possible. This alignment enables future interoperability with other Substrait-compliant systems and provides a stable reference for function behavior.

The alignment manifests in several ways:

- Function keys map to Substrait extension URIs
- Function names match Substrait naming conventions (e.g., "equal" not "eq")
- Argument ordering follows Substrait conventions
- Return type semantics match Substrait definitions
- Extension functions are explicitly marked with `is_extension=True`

This does not mean mountainash is a full Substrait implementation. Rather, it uses Substrait as a design reference and interoperability target. The internal representation is optimized for Python ergonomics, while the serialization layer handles Substrait format translation.

<!-- concept:73 -->
## Build Then Compile

The "build then compile" pattern is mountainash's fundamental architectural principle. User code builds an AST of expression and relation nodes without any reference to a specific backend. Compilation to backend-native code happens as a separate, later phase triggered by a terminal operation.

This separation provides three critical benefits:

1. **Backend independence at build time**: The same expression code works regardless of which backend will execute it
2. **Optimization opportunity**: The full AST is visible before compilation, enabling rewrites
3. **Testability**: ASTs can be inspected and compared without executing against real data

```python
import mountainash as ma

# BUILD phase: pure AST construction, no backend involved
expr = ma.col("price") * ma.col("qty") + ma.col("tax")

# COMPILE phase: triggered by terminal operation, backend-specific
# (happens internally when relation.to_polars() is called)
# visitor.visit(expr) -> pl.col("price") * pl.col("qty") + pl.col("tax")
```

The build phase uses the fluent API and produces `ExpressionNode` trees. The compile phase uses the visitor pattern to walk those trees and produce backend-native expressions.

<!-- concept:74 -->
## Expression Compilation

Expression compilation is the process of transforming an `ExpressionNode` AST into a backend-native expression object. The compiler walks the tree depth-first, visiting each node and producing the corresponding backend output.

The compilation process for a single expression tree works as follows. The root node's `accept` method is called with the visitor. The visitor dispatches based on node type (field reference, literal, scalar function, cast, if-then, window). For scalar functions, the visitor recursively compiles argument expressions before passing them to the backend method identified by the function key.

```python
# Simplified compilation flow
def visit_scalar_function(self, node: ScalarFunctionNode):
    # 1. Recursively compile arguments
    compiled_args = [arg.accept(self) for arg in node.arguments]

    # 2. Look up the backend method
    method = self._get_compile_method(node.function_key)

    # 3. Call backend method with compiled arguments
    return method(compiled_args, node.options)
```

!!! note "Compilation is Recursive"
    Expression trees can be arbitrarily deep. A `ScalarFunctionNode` whose arguments are themselves `ScalarFunctionNode` instances triggers recursive compilation. The visitor handles this naturally through the `accept` pattern -- each argument's `accept` call triggers another round of visitor dispatch.

<!-- concept:75 -->
## Unified Expression Visitor

The `UnifiedExpressionVisitor` is the concrete visitor class that coordinates expression compilation. It holds a reference to an expression system (the backend implementation) and dispatches each node type to the appropriate system method.

```python
class UnifiedExpressionVisitor:
    def __init__(self, expression_system):
        self.system = expression_system

    def visit(self, node: ExpressionNode) -> Any:
        return node.accept(self)

    def visit_field_reference(self, node: FieldReferenceNode) -> Any:
        return self.system.compile_field_reference(node)

    def visit_literal(self, node: LiteralNode) -> Any:
        return self.system.compile_literal(node)

    def visit_scalar_function(self, node: ScalarFunctionNode) -> Any:
        return self.system.compile_scalar_function(node, self)

    def visit_cast(self, node: CastNode) -> Any:
        return self.system.compile_cast(node, self)
```

The visitor is "unified" because all backends share the same visitor class. The backend-specific behavior lives in the expression system object that the visitor delegates to. This means adding a new node type requires one change in the visitor (a new visit method) but no changes per backend unless that backend handles the node differently.

<!-- concept:76 -->
## API Builder Protocols

API builder protocols define the interface that expression namespace classes must implement. They ensure that every namespace (string, datetime, struct, list, name) provides the expected methods and that those methods produce correctly structured AST nodes.

The protocols are organized by category (Substrait-standard vs mountainash extensions) and by namespace. Each protocol class declares the methods that the corresponding namespace must offer.

```python
class StringBuilderProtocol(Protocol):
    def upper(self) -> BaseExpressionAPI: ...
    def lower(self) -> BaseExpressionAPI: ...
    def trim(self) -> BaseExpressionAPI: ...
    def contains(self, pattern: str) -> BooleanExpressionAPI: ...
    # ... etc
```

These protocols serve as documentation and as verification targets for static type checkers. They ensure that the API surface remains consistent and that new namespace implementations satisfy the required contract.

<!-- concept:77 -->
## Expression System Protocols

Expression system protocols define the interface that backend compilation classes must implement. Each protocol declares the methods that a backend expression system needs for compiling specific operation categories.

The protocols are split by function category to enable granular implementation. A backend that supports arithmetic but not window functions can implement the arithmetic protocol without the window protocol.

```python
class ScalarArithmeticProtocol(Protocol):
    def compile_add(self, args, options) -> Any: ...
    def compile_subtract(self, args, options) -> Any: ...
    def compile_multiply(self, args, options) -> Any: ...
    # ... etc

class ScalarComparisonProtocol(Protocol):
    def compile_equal(self, args, options) -> Any: ...
    def compile_not_equal(self, args, options) -> Any: ...
    # ... etc
```

The concrete expression systems (PolarsExpressionSystem, NarwhalsExpressionSystem, IbisExpressionSystem) satisfy these protocols through multiple inheritance, combining all the protocol implementations into a single class per backend.

#### Diagram: Protocol and System Composition
<iframe src="../../sims/protocol-system-composition/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Protocol and System Composition</summary>
Type: diagram
**sim-id:** protocol-system-composition<br/>
**Library:** vis-network<br/>
**Status:** Specified

A UML-style class diagram showing the relationship between protocols and implementations. Top row: protocol classes (ScalarArithmeticProtocol, ScalarComparisonProtocol, ScalarStringProtocol, WindowProtocol). Bottom row: three concrete systems (PolarsExpressionSystem, NarwhalsExpressionSystem, IbisExpressionSystem). Dashed arrows show protocol satisfaction. Each system connects to multiple protocols via multiple inheritance. Clicking a system shows which protocols it satisfies and any missing methods. Colors: LimeGreen for protocols, Gold for backends. Learning objective: Explain how multiple inheritance composes protocol implementations into complete expression systems (Bloom: Understand).
</details>

<!-- concept:78 -->
## Mountainash Extensions

Mountainash extensions are functions that go beyond the Substrait specification to provide practical features that users commonly need. These extensions are clearly marked in the registry with `is_extension=True` and use the mountainash extension URI.

Extension categories include:

- **Name operations**: alias, prefix, suffix (column renaming)
- **Null extensions**: fill_null with expression argument, drop_nulls
- **Native passthrough**: wrapping backend-specific expressions
- **Ternary logic**: three-valued truth operations beyond standard boolean
- **Aggregate extensions**: custom aggregation semantics
- **List operations**: array manipulation not covered by Substrait
- **Struct operations**: nested data access

Extensions are implemented identically to Substrait functions at the code level. They have function keys, registry entries, API builder methods, and expression system compile methods. The only difference is metadata: their `ExpressionFunctionDef` records `is_extension=True` and points to the mountainash extension URI rather than a Substrait URI.

## Key Takeaways

- Substrait-prefixed function keys align with the Substrait specification for interoperability, while mountainash-prefixed keys cover practical extensions beyond the standard.
- `ExpressionFunctionDef` captures the complete metadata for each function: key, Substrait URI, backend method, options, and protocol reference.
- The `ExpressionFunctionRegistry` provides O(1) lookup from function key to compilation metadata, serving as the central authority for all registered functions.
- Build-then-compile separates AST construction (backend-agnostic) from code generation (backend-specific), enabling optimization and portability.
- Expression compilation walks AST trees depth-first via the visitor pattern, recursively compiling arguments before calling backend methods.
- The `UnifiedExpressionVisitor` delegates to a pluggable expression system object, keeping the visitor code backend-agnostic.
- API builder protocols and expression system protocols define contracts that enable new backends and namespaces to be added without modifying core code.
- Mountainash extensions are marked with `is_extension=True` and handled identically to Substrait functions by the compilation machinery.
