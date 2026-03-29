# ADR-007: Mountainash Extension System

## Status
PROPOSED

## Context

The mountainash-expressions package provides both Substrait-standard operations and custom operations that extend beyond the Substrait specification. These custom operations include:

- **Ternary Logic**: Three-valued logic (TRUE/UNKNOWN/FALSE) for NULL-aware comparisons
- **DateTime Extensions**: Convenience functions like `add_days`, `diff_hours`, extraction shortcuts
- **Null Extensions**: `fill_null`, `null_if`
- **Name Extensions**: `alias`, `prefix`, `suffix`

Currently, these custom operations exist in deprecated code paths (`expression_protocols/deprecated/`, `backends/deprecated_expression_systems/`) and are not integrated with the new Substrait-aligned FunctionRegistry system introduced in ADR-004.

Tests fail with errors like:
```
KeyError: 'Unknown function: MOUNTAINASH_TERNARY.IS_TRUE'
```

We need a clean architecture for:
1. Distinguishing Substrait-standard functions from custom extensions
2. Enabling future serialization of plans that include extensions
3. Maintaining backward compatibility with existing tests (163+ ternary tests)
4. Following Substrait's extension patterns

## Decision

We will implement a **Mountainash Extension System** with the following structure:

### 1. Extension URIs

Custom functions will use file-based URIs pointing to YAML definitions stored in the repository:

```python
class MountainashExtension:
    """Mountainash custom extension URIs - stored in /extensions/."""
    TERNARY = "file://extensions/functions_ternary.yaml"
    DATETIME = "file://extensions/functions_datetime.yaml"
    NULL = "file://extensions/functions_null.yaml"
    NAME = "file://extensions/functions_name.yaml"
```

### 2. Protocol Organization

Create a new `mountainash_extensions/` directory under `expression_protocols/`:

```
expression_protocols/
├── substrait/              # Substrait-standard protocols
├── extensions/             # Auto-generated Substrait stubs (existing)
├── mountainash_extensions/ # NEW: Custom extension protocols
│   ├── __init__.py
│   ├── ext_ternary.py
│   ├── ext_datetime.py
│   ├── ext_null.py
│   └── ext_name.py
└── deprecated/             # Old protocols (leave as-is)
```

### 3. Function Registration

All `MOUNTAINASH_*` ENUMs will be registered in `definitions.py` with:
- `is_extension=True` flag
- Custom `substrait_uri` pointing to extension files
- Protocol method references for FunctionRegistry dispatch

```python
ExpressionFunctionDef(
    function_key=MOUNTAINASH_TERNARY.IS_TRUE,
    substrait_uri=MountainashExtension.TERNARY,
    substrait_name="ternary_is_true",
    is_extension=True,
    protocol_method=TernaryExpressionProtocol.is_true_ternary,
)
```

### 4. Backend Composition

Migrate deprecated backend implementations to new expression system composition:
- Copy working code from `deprecated_expression_systems/`
- Update imports to use new protocol locations
- Compose into existing ExpressionSystem classes via mixin inheritance

### 5. Extension YAML Definitions

Create YAML files in `/extensions/` following Substrait format:

```yaml
urn: file://extensions/functions_ternary.yaml
name: Mountainash Ternary Logic Functions
description: Three-valued logic operations for NULL-aware comparisons

scalar_functions:
  - name: ternary_is_true
    description: Check if ternary value is TRUE (1)
    impls:
      - args:
          - name: operand
            value: i8
        return: boolean
```

## Consequences

### Positive
- **Clean separation** between Substrait-standard and custom operations
- **Future-proof** for plan serialization with extension metadata
- **Leverages working deprecated code** (migration over recreation)
- **Follows Substrait extension patterns** for compatibility
- **Testable** - 163+ existing ternary tests validate the migration

### Negative
- **Increased directory structure complexity** (one more directory level)
- **Need to maintain extension YAML files** for documentation/serialization
- **Some code duplication** during migration period (deprecated code remains)

### Risks
- Custom operations may conflict with future Substrait additions
- Extension URIs need to be stable across versions

## Alternatives Considered

### 1. Inline custom operations in Substrait protocols
**Rejected**: Muddles the distinction between standard and custom operations. Makes it harder to identify what requires custom backend support vs. what is portable.

### 2. Single extensions protocol file
**Rejected**: Ternary alone has 20+ methods. Separation by domain (ternary, datetime, null, name) provides better organization and allows incremental migration.

### 3. Rewrite implementations from scratch
**Rejected**: Deprecated implementations are tested and working. Migration preserves tested code and reduces risk.

### 4. Use existing `extensions/` directory for custom protocols
**Rejected**: That directory contains auto-generated stubs from Substrait YAML files. Mixing custom protocols there would create confusion about what is Substrait-standard vs. Mountainash-specific.

## Implementation

See GitHub Milestone: **Substrait Alignment Phase 6 - Mountainash Extensions**

Issues:
- #46: ADR-007 and mountainash_extensions setup
- #47: Implement Ternary Extension
- #48: Implement DateTime Extension
- #49: Implement Null Extension
- #50: Implement Name Extension
- #51: Create Extension YAML Definitions
- #52: Full Test Verification
