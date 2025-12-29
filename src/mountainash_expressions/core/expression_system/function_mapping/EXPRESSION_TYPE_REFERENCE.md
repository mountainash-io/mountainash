# Expression Type Reference

This document explains how different expression types map to Substrait's expression model and whether they use the function registry.

## Substrait Expression Model

Substrait defines 6 core expression types. Our implementation maps these to specific node classes:

| Expression Type | Substrait Type | Node Class | Uses Registry | Description |
|-----------------|----------------|------------|---------------|-------------|
| Column reference | `FieldReference` | `FieldReferenceNode` | No | Reference to a named field |
| Constant value | `Literal` | `LiteralNode` | No | Literal/constant value |
| Function call | `ScalarFunction` | `ScalarFunctionNode` | **Yes** | Scalar function invocation |
| Conditional | `IfThen` | `IfThenNode` | No | When/then/otherwise logic |
| Type conversion | `Cast` | `CastNode` | No | Type casting |
| Membership test | `SingularOrList` | `SingularOrListNode` | No | IN operator |

## Why Some Types Don't Use the Registry

### Primitive Expression Types (No Registry)

These are fundamental building blocks, not function calls:

```python
# FieldReference - just references a column by name
col("age")  # → FieldReferenceNode(field="age")

# Literal - just holds a constant value
lit(42)     # → LiteralNode(value=42)
```

They have dedicated visitor methods:
- `visit_field_reference(node)` → backend's `col()` method
- `visit_literal(node)` → backend's `lit()` method

### Structural Expression Types (No Registry)

These have special structure that doesn't fit the function call pattern:

```python
# IfThen - has condition/then/else structure
when(cond).then(val).otherwise(alt)  # → IfThenNode

# Cast - has expression + target type
col("x").cast(int)  # → CastNode(expr, target_type)

# SingularOrList - has value + list of options
col("status").is_in(["a", "b"])  # → SingularOrListNode
```

### ScalarFunction (Uses Registry)

All other operations are scalar functions that need registry metadata:

```python
# Comparison
col("age").gt(30)  # → ScalarFunctionNode(function_key=KEY_SCALAR_COMPARISON.GT, ...)

# Arithmetic
col("a").add(col("b"))  # → ScalarFunctionNode(function_key=KEY_SCALAR_ARITHMETIC.ADD, ...)

# String
col("name").str.upper()  # → ScalarFunctionNode(function_key=KEY_SCALAR_STRING.UPPER, ...)
```

## Registry Entry Structure

For `ScalarFunctionNode` operations, the registry provides:

```python
ExpressionFunctionDef(
    function_key=KEY_SCALAR_COMPARISON.GT,           # Compile-time safe identifier
    substrait_uri=SubstraitExtension.SCALAR_COMPARISON,  # Extension URI for serialization
    substrait_name="gt",                             # Substrait function name
    protocol_method=ScalarComparisonExpressionProtocol.gt,  # Backend method reference
)
```

## Visitor Dispatch Flow

```
Expression Node
      │
      ├── FieldReferenceNode ──→ visit_field_reference() ──→ backend.col()
      │
      ├── LiteralNode ─────────→ visit_literal() ─────────→ backend.lit()
      │
      ├── IfThenNode ──────────→ visit_if_then() ─────────→ backend.if_then()
      │
      ├── CastNode ────────────→ visit_cast() ────────────→ backend.cast()
      │
      ├── SingularOrListNode ──→ visit_singular_or_list() → backend.is_in()
      │
      └── ScalarFunctionNode ──→ visit_scalar_function()
                                        │
                                        ▼
                                 Registry Lookup
                                        │
                                        ▼
                                 protocol_method()
                                        │
                                        ▼
                                 backend.{method}()
```

## Summary

| Category | Node Types | Registry | Dispatch |
|----------|------------|----------|----------|
| Primitives | FieldReference, Literal | No | Direct visitor method |
| Structural | IfThen, Cast, SingularOrList | No | Direct visitor method |
| Functions | ScalarFunction | **Yes** | Registry → protocol_method |

The function registry (`definitions.py`) only contains entries for `ScalarFunctionNode` operations, which represent actual function calls in the Substrait model.
