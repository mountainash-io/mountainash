# ADR-008: Substrait vs Mountainash Extension Alignment

## Status

**Implemented** (Updated 2025-12-30)

## Date

- Original: 2025-12-26
- Updated: 2025-12-30

## Context

The mountainash-expressions package implements a cross-backend DataFrame expression system built on two foundations:

1. **Substrait** - An open specification for data compute operations (https://substrait.io/)
2. **Mountainash Extensions** - Custom operations that extend Substrait for DataFrame-specific use cases

The codebase has been refactored to maintain clear boundaries between these two origins across all architectural layers. This separation:

- Makes it immediately clear whether code is Substrait-standard or custom
- Simplifies navigation and contribution
- Enables distinct testing strategies (compliance vs. behavior)
- Facilitates future Substrait serialization

## Decision

**Every architectural layer explicitly separates Substrait-aligned components from Mountainash Extensions.**

The separation is maintained through:
1. Physical directory structure (`substrait/` vs `extensions_mountainash/`)
2. File naming prefixes (`expsys_pl_` vs `expsys_pl_ext_ma_`)
3. Enum naming (`KEY_*` vs `MOUNTAINASH_*`)
4. Class naming patterns (documented below)

## Implemented Architecture

### Directory Structure

```
src/mountainash_expressions/
├── core/
│   ├── expression_nodes/
│   │   └── substrait/                          # Minimal 7-node AST
│   │       ├── exn_base.py                     # Base ExpressionNode
│   │       ├── exn_field_reference.py          # Column references
│   │       ├── exn_literal.py                  # Constants
│   │       ├── exn_scalar_function.py          # Universal function node
│   │       ├── exn_cast.py                     # Type conversion
│   │       ├── exn_ifthen.py                   # Conditionals
│   │       └── exn_singular_or_list.py         # IN/NOT IN
│   │
│   ├── expression_system/
│   │   └── function_keys/
│   │       └── enums.py                        # All ENUMs (KEY_* & MOUNTAINASH_*)
│   │
│   ├── expression_protocols/
│   │   ├── api_builders/
│   │   │   ├── substrait/                      # Builder protocol stubs
│   │   │   │   └── prtcl_api_bldr_*.py
│   │   │   └── extensions_mountainash/         # Extension builder protocols
│   │   │       └── prtcl_api_bldr_ext_ma_*.py
│   │   │
│   │   └── expression_systems/
│   │       ├── substrait/                      # ExpressionSystem protocols
│   │       │   └── prtcl_expsys_*.py
│   │       └── extensions_mountainash/         # Extension system protocols
│   │           └── prtcl_expsys_ext_ma_*.py
│   │
│   └── expression_api/
│       └── api_builders/
│           ├── substrait/                      # API builder implementations
│           │   └── api_bldr_*.py
│           └── extensions_mountainash/         # Extension API builders
│               └── api_bldr_ext_ma_*.py
│
└── backends/
    └── expression_systems/
        ├── polars/
        │   ├── substrait/                      # Polars Substrait implementations
        │   │   └── expsys_pl_*.py
        │   └── extensions_mountainash/         # Polars extension implementations
        │       └── expsys_pl_ext_ma_*.py
        │
        ├── ibis/
        │   ├── substrait/
        │   │   └── expsys_ib_*.py
        │   └── extensions_mountainash/
        │       └── expsys_ib_ext_ma_*.py
        │
        └── narwhals/
            ├── substrait/
            │   └── expsys_nw_*.py
            └── extensions_mountainash/
                └── expsys_nw_ext_ma_*.py
```

### Implemented Categories

#### Substrait Categories (13)

| Category | Function Key Enum | Protocol File | Description |
|----------|-------------------|---------------|-------------|
| `field_reference` | `KEY_FIELD_REFERENCE` | `prtcl_expsys_field_reference.py` | Column references |
| `literal` | `KEY_LITERAL` | `prtcl_expsys_literal.py` | Constant values |
| `cast` | `KEY_CAST` | `prtcl_expsys_cast.py` | Type conversion |
| `conditional` | `KEY_CONDITIONAL` | `prtcl_expsys_conditional.py` | If-then-else |
| `scalar_aggregate` | `KEY_SCALAR_AGGREGATE` | `prtcl_expsys_scalar_aggregate.py` | Aggregations |
| `scalar_arithmetic` | `KEY_SCALAR_ARITHMETIC` | `prtcl_expsys_scalar_arithmetic.py` | Math operations |
| `scalar_boolean` | `KEY_SCALAR_BOOLEAN` | `prtcl_expsys_scalar_boolean.py` | Boolean logic |
| `scalar_comparison` | `KEY_SCALAR_COMPARISON` | `prtcl_expsys_scalar_comparison.py` | Comparisons, null checks |
| `scalar_datetime` | `KEY_SCALAR_DATETIME` | `prtcl_expsys_scalar_datetime.py` | Date extraction |
| `scalar_logarithmic` | `KEY_SCALAR_LOGARITHMIC` | `prtcl_expsys_scalar_logarithmic.py` | Log functions |
| `scalar_rounding` | `KEY_SCALAR_ROUNDING` | `prtcl_expsys_scalar_rounding.py` | Round/ceil/floor |
| `scalar_set` | `KEY_SCALAR_SET` | `prtcl_expsys_scalar_set.py` | Set operations |
| `scalar_string` | `KEY_SCALAR_STRING` | `prtcl_expsys_scalar_string.py` | String operations |

#### Mountainash Extensions (6)

| Category | Function Key Enum | Protocol File | Description |
|----------|-------------------|---------------|-------------|
| `ext_ma_arithmetic` | `MOUNTAINASH_ARITHMETIC` | `prtcl_expsys_ext_ma_scalar_arithmetic.py` | floor_divide |
| `ext_ma_datetime` | `MOUNTAINASH_DATETIME` | `prtcl_expsys_ext_ma_scalar_datetime.py` | Convenience temporal ops |
| `ext_ma_name` | `MOUNTAINASH_NAME` | `prtcl_expsys_ext_ma_name.py` | alias/prefix/suffix |
| `ext_ma_null` | `MOUNTAINASH_NULL` | `prtcl_expsys_ext_ma_null.py` | fill_null, null_if |
| `ext_ma_scalar_boolean` | `MOUNTAINASH_COMPARISON` | N/A | xor_parity |
| `ext_ma_scalar_ternary` | `MOUNTAINASH_TERNARY` | `prtcl_expsys_ext_ma_scalar_ternary.py` | Three-valued logic |

## Naming Conventions

### File Naming

| Component | Substrait Pattern | Mountainash Pattern |
|-----------|-------------------|---------------------|
| Expression Nodes | `exn_<type>.py` | N/A (use ScalarFunctionNode) |
| Builder Protocols | `prtcl_api_bldr_<category>.py` | `prtcl_api_bldr_ext_ma_<category>.py` |
| ExpressionSystem Protocols | `prtcl_expsys_<category>.py` | `prtcl_expsys_ext_ma_<category>.py` |
| API Builders | `api_bldr_<category>.py` | `api_bldr_ext_ma_<category>.py` |
| Backend Implementations | `expsys_<backend>_<category>.py` | `expsys_<backend>_ext_ma_<category>.py` |

### File Prefix Reference

| Prefix | Meaning | Example |
|--------|---------|---------|
| `exn_` | Expression Node | `exn_scalar_function.py` |
| `prtcl_` | Protocol | `prtcl_expsys_scalar_comparison.py` |
| `api_bldr_` | API Builder | `api_bldr_scalar_comparison.py` |
| `expsys_` | Expression System (backend impl) | `expsys_pl_scalar_comparison.py` |
| `ext_ma_` | Mountainash Extension | `expsys_pl_ext_ma_null.py` |

### Backend Prefix Reference

| Prefix | Backend |
|--------|---------|
| `pl_` | Polars |
| `ib_` | Ibis |
| `nw_` | Narwhals |

### Class Naming

| Component | Substrait Pattern | Mountainash Pattern |
|-----------|-------------------|---------------------|
| Function Key Enums | `KEY_<CATEGORY>` | `MOUNTAINASH_<CATEGORY>` |
| ExpressionSystem Protocols | `Substrait<Category>ExpressionSystemProtocol` | `MountainAsh<Category>ExpressionSystemProtocol` |
| Backend Implementations | `<Backend><Category>ExpressionSystem` | `<Backend><Category>ExtensionSystem` |

## Implementation Examples

### 1. Function Key Definition

```python
# Substrait (from function_keys/enums.py)
class KEY_SCALAR_COMPARISON(Enum):
    """Substrait comparison functions."""
    EQUAL = auto()
    NOT_EQUAL = auto()
    GT = auto()
    LT = auto()
    # ...

# Mountainash Extension
class MOUNTAINASH_TERNARY(Enum):
    """Mountainash ternary logic operations."""
    T_EQ = "t_eq"
    T_NE = "t_ne"
    T_AND = "t_and"
    # ...
```

### 2. Protocol Definition

```python
# Substrait Protocol (prtcl_expsys_scalar_comparison.py)
class SubstraitScalarComparisonExpressionSystemProtocol(Protocol):
    """Protocol for comparison operations."""

    def equal(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Whether two values are equal."""
        ...

    def lt(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Less than comparison."""
        ...

# Mountainash Extension Protocol (prtcl_expsys_ext_ma_null.py)
class MountainAshNullExpressionSystemProtocol(Protocol):
    """Backend protocol for Mountainash null handling extensions."""

    def fill_null(
        self,
        input: SupportedExpressions,
        replacement: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Replace NULL values with the specified replacement value."""
        ...
```

### 3. Backend Implementation

```python
# Substrait Backend (expsys_pl_scalar_comparison.py)
class PolarsScalarComparisonExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitScalarComparisonExpressionSystemProtocol
):
    """Polars implementation of ScalarComparisonExpressionProtocol."""

    def equal(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        return x.eq(y)

    def lt(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        return x.lt(y)

# Mountainash Extension Backend (expsys_pl_ext_ma_null.py)
class PolarsNullExtensionSystem(
    PolarsBaseExpressionSystem,
    MountainAshNullExpressionSystemProtocol
):
    """Polars implementation of Mountainash null extensions."""

    def fill_null(self, input: PolarsExpr, replacement: PolarsExpr, /) -> PolarsExpr:
        return input.fill_null(replacement)
```

### 4. API Builder (Namespace)

```python
# API Builder creates ScalarFunctionNode with appropriate ENUM
class ScalarComparisonNamespace(BaseNamespace):
    """Comparison operations namespace."""

    def eq(self, other) -> BaseExpressionAPI:
        """Equal to (==)."""
        other_node = self._to_node_or_value(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_COMPARISON.EQUAL,
            arguments=[self._node, other_node],
        )
        return self._build(node)
```

### 5. End-to-End Flow

```python
import mountainash_expressions as ma

# 1. User builds expression (creates AST)
expr = ma.col("age").gt(30)
# Creates: ScalarFunctionNode(
#     function_key=KEY_SCALAR_COMPARISON.GT,
#     arguments=[FieldReferenceNode("age"), LiteralNode(30)]
# )

# 2. Compile to backend-native expression
backend_expr = expr.compile(df)
# Visitor dispatches to: PolarsScalarComparisonExpressionSystem.gt()
# Returns: pl.col("age").gt(30)

# 3. Use with DataFrame
result = df.filter(backend_expr)
```

## Known Gaps / Future Work

### Naming Inconsistencies

1. **MountainAsh vs Mountainash casing**: Some protocol classes use `MountainAsh` (camelCase) while file names use `mountainash` (lowercase). Should standardize.

2. **Extension class suffix**: Some backend extension classes (e.g., `PolarsTernarySystem`) lack the `ExtensionSystem` suffix that would clarify their nature.

### Structural Items

3. **Deprecated folders**: `_deprecated/` and `deprecated/` directories still exist and should be cleaned up once migration is confirmed complete.

4. **Native expression handling**: Currently reuses LiteralNode with special handling. May benefit from a dedicated `NativeNode` type.

5. **Unified visitor**: The visitor implementation that dispatches based on function registry is still being finalized.

### Documentation

6. **Extension URI definitions**: The `MountainashExtension` class defines URIs (`file://extensions/...`) but the actual YAML files don't exist yet. These are placeholders for future Substrait serialization.

## Consequences

### Positive

- **Clear mental model**: File location immediately indicates Substrait vs. Extension
- **IDE-friendly**: Consistent prefixes enable efficient navigation and autocomplete
- **Testability**: Can write Substrait compliance tests vs. extension behavior tests separately
- **Contribution clarity**: New extensions don't touch core Substrait code
- **Future-proof**: Structure supports Substrait serialization when ready

### Negative

- **More directories**: Deeper nesting requires understanding the structure
- **Boilerplate**: Structural patterns repeat between Substrait and Extensions
- **Migration effort**: Required significant refactoring (now complete)

## The 1:1 Alignment Principle

For each operation category, there is a clear vertical alignment:

```
Function Key          Protocol                    Backend Implementation
─────────────────────────────────────────────────────────────────────────
KEY_SCALAR_COMPARISON → SubstraitScalar...Protocol → expsys_pl_scalar_comparison.py
MOUNTAINASH_TERNARY   → MountainAshTernary...      → expsys_pl_ext_ma_scalar_ternary.py
MOUNTAINASH_NULL      → MountainAshNull...         → expsys_pl_ext_ma_null.py
```

### Antipatterns to Avoid

- **Extension keys in Substrait directories**: If it uses `MOUNTAINASH_*` enums, it belongs in `extensions_mountainash/`
- **Special-case hacks in visitor**: Extension operations should have their own registered handlers
- **Mixed operations in same file**: Keep files pure to one category

## References

- [Substrait Specification](https://substrait.io/)
- [ADR-002: Substrait Builder Protocols](./ADR-002-substrait-builder-protocols.md)
- [ADR-007: Mountainash Extension System](./ADR-007-mountainash-extension-system.md)
