# MOUNTAINASH-EXPRESSIONS CODEBASE STRUCTURE

## Summary Statistics
- Total Python Files in src/: 20
- Total Lines of Code: ~2,634 lines
- Active Package Structure: src/mountainash_expressions/
- Deprecated Archive: _deprecated/mountainash_expressions/

---

## ACTUAL DIRECTORY STRUCTURE

### Root Package: src/mountainash_expressions/

```
src/mountainash_expressions/
├── backends/                          # BACKEND IMPLEMENTATIONS (2+ subdirs)
│   └── narwhals/                      # Narwhals backend (5 files)
│       ├── __init__.py                # Exports: NarwhalsBackendVisitorMixin, NarwhalsBooleanExpressionVisitor, NarwhalsTernaryExpressionVisitor
│       ├── narwhals_visitor.py        # Base Narwhals visitor mixin (72 lines)
│       ├── narwhals_boolean_visitor.py # Boolean logic for Narwhals (117 lines)
│       ├── narwhals_ternary_visitor.py # Ternary logic for Narwhals (282 lines)
│       └── narwhals_parameters.py     # Parameters/configuration (0 lines - empty)
│
└── core/                              # CORE LOGIC & VISITORS (6 subdirs)
    ├── backend_visitors/              # ABSTRACT BACKEND INTERFACE
    │   └── backend_visitor.py          # BackendVisitor abstract base class (43 lines)
    │                                   # Defines interface: _col, _lit, _as_list, _as_set, 
    │                                   #                   _is_null, _not_null, etc.
    │
    ├── expression_nodes/              # EXPRESSION NODE HIERARCHY (2 files)
    │   ├── expression_nodes.py         # Base expression nodes (259 lines)
    │   │                               # Classes:
    │   │                               #   - ExpressionNode (ABC)
    │   │                               #   - NativeBackendExpressionNode
    │   │                               #   - SourceExpressionNode
    │   │                               #   - LiteralExpressionNode
    │   │                               #   - CastExpressionNode
    │   │                               #   - LogicalConstantExpressionNode
    │   │                               #   - UnaryExpressionNode
    │   │                               #   - LogicalExpressionNode
    │   │                               #   - ComparisonExpressionNode
    │   │                               #   - CollectionExpressionNode
    │   │                               #   - ArithmeticExpressionNode
    │   │                               #   - ConditionalIfElseExpressionNode
    │   │
    │   └── boolean_expession_nodes.py  # Boolean-specific nodes (129 lines) [typo: "expession"]
    │                                   # Classes:
    │                                   #   - BooleanExpressionNode
    │                                   #   - BooleanUnaryExpressionNode
    │                                   #   - BooleanLogicalExpressionNode
    │                                   #   - BooleanComparisonExpressionNode
    │                                   #   - BooleanConditionalIfElseExpressionNode
    │                                   #   - BooleanCollectionExpressionNode
    │                                   # Methods: eval(), eval_is_true(), eval_is_false()
    │
    ├── expression_parameters/          # PARAMETER TYPE DETECTION (1 file)
    │   └── expression_parameter.py     # ExpressionParameter class (5,073 bytes)
    │                                   # Handles parameter type detection and conversion
    │                                   # ParameterType enum: EXPRESSION_NODE, NATIVE_EXPRESSION,
    │                                   #                     COLUMN_REFERENCE, LITERAL_VALUE, UNKNOWN
    │
    └── expression_visitors/            # VISITOR PATTERN IMPLEMENTATION (2 dirs, 2 files)
        ├── expression_visitor.py       # Base ExpressionVisitor ABC (154 lines)
        │                               # Defines visitor interface with property methods:
        │                               #   - backend_type: CONST_VISITOR_BACKENDS
        │                               #   - logic_type: CONST_LOGIC_TYPES
        │                               # Source/Literal/Cast operation handlers
        │                               # Visit methods for all expression types
        │
        ├── boolean_expression_visitor.py # Boolean-specific visitor (342 lines)
        │                                 # BooleanExpressionVisitor implementation
        │
        ├── boolean_mixins/             # BOOLEAN OPERATION MIXINS (5 files)
        │   ├── boolean_collection_visitor_mixin.py     # Collection operations (3,185 bytes)
        │   ├── boolean_comparison_visitor_mixin.py     # Comparison operations (3,259 bytes)
        │   ├── boolean_logical_visitor_mixin.py        # Logical operations (3,258 bytes)
        │   ├── boolean_logicial_constant_visitor_mixin.py # Logical constants (2,177 bytes) [typo: "logicial"]
        │   └── boolean_unary_visitor_mixin.py          # Unary operations (3,230 bytes)
        │
        └── common_mixins/              # SHARED OPERATION MIXINS (4 files)
            ├── cast_visitor_mixin.py    # Type casting operations (4,725 bytes)
            ├── literal_visitor_mixin.py # Literal value handling (4,725 bytes)
            ├── native_expression_visitor_mixin.py # Native backend expressions (4,725 bytes)
            └── source_visitor_mixin.py  # Source column handling (4,725 bytes)

```

---

## CONSTANTS & DEPENDENCIES

### Constants Importing Issue
**CRITICAL**: The codebase imports constants that don't exist in src/mountainash_expressions/:

```python
# In files like expression_nodes.py:
from ..constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES
from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS

# But constants.py does NOT exist in src/mountainash_expressions/
# Constants ARE available in _deprecated/mountainash_expressions/core/constants.py
```

### Available Constants (from deprecated folder):
- **CONST_VISITOR_BACKENDS**: enum(PANDAS, POLARS, IBIS, PYARROW)
- **CONST_LOGIC_TYPES**: enum(BOOLEAN, TERNARY, FUZZY)
- **CONST_EXPRESSION_NODE_TYPES**: enum(LITERAL, COLUMN, LOGICAL)
- **CONST_EXPRESSION_LOGIC_OPERATORS**: enum(EQ, NE, GT, LT, etc.)
- **CONST_TERNARY_LOGIC_VALUES**: IntEnum(-1=FALSE, 0=UNKNOWN, 1=TRUE)

---

## KEY FILES & THEIR PURPOSES

### Core Expression System
| File | Lines | Purpose |
|------|-------|---------|
| expression_nodes.py | 259 | Base expression node hierarchy with 11 node types |
| boolean_expession_nodes.py | 129 | Boolean-specific node implementations (6 classes) |
| expression_parameter.py | 150+ | Parameter type detection and conversion |

### Visitor Pattern
| File | Lines | Purpose |
|------|-------|---------|
| expression_visitor.py | 154 | Abstract base visitor interface |
| boolean_expression_visitor.py | 342 | Boolean logic visitor implementation |
| backend_visitor.py | 43 | Abstract backend visitor interface |

### Boolean Operation Handlers (Mixins)
| File | Bytes | Purpose |
|------|-------|---------|
| boolean_comparison_visitor_mixin.py | 3,259 | Handles ==, !=, >, <, >=, <= |
| boolean_logical_visitor_mixin.py | 3,258 | Handles AND, OR, XOR operations |
| boolean_unary_visitor_mixin.py | 3,230 | Handles NOT operations |
| boolean_collection_visitor_mixin.py | 3,185 | Handles IN, contains operations |
| boolean_logicial_constant_visitor_mixin.py | 2,177 | Handles TRUE, FALSE constants |

### Common Operation Handlers (Mixins)
| File | Bytes | Purpose |
|------|-------|---------|
| cast_visitor_mixin.py | 4,725 | Type casting (CAST operator) |
| literal_visitor_mixin.py | 4,725 | Literal value handling (LIT operator) |
| source_visitor_mixin.py | 4,725 | Column reference handling (COL operator) |
| native_expression_visitor_mixin.py | 4,725 | Backend-native expression passthrough |

### Narwhals Backend (Unified DataFrame Framework)
| File | Lines | Purpose |
|------|-------|---------|
| narwhals_visitor.py | 72 | Base Narwhals visitor with _col, _lit, _as_list, etc. |
| narwhals_boolean_visitor.py | 117 | Boolean expressions for Narwhals backend |
| narwhals_ternary_visitor.py | 282 | Ternary (3-valued logic) for Narwhals |
| narwhals_parameters.py | 0 | Empty - placeholder for parameters |
| __init__.py | 9 | Exports three classes |

---

## MISSING BACKENDS

The documented structure mentions these backends, but they DON'T exist in src/:
- ~~ibis/~~ 
- ~~pandas/~~ 
- ~~polars/~~ 
- ~~pyarrow/~~ 

Only **narwhals/** backend is implemented (unified cross-backend approach).

---

## MISSING __init__.py FILES (CRITICAL)

**ISSUE**: Only ONE __init__.py exists in the entire src/mountainash_expressions/:

Exists:
- src/mountainash_expressions/backends/narwhals/__init__.py

Missing:
- src/mountainash_expressions/__init__.py (MAIN PACKAGE)
- src/mountainash_expressions/core/__init__.py
- src/mountainash_expressions/core/backend_visitors/__init__.py
- src/mountainash_expressions/core/expression_nodes/__init__.py
- src/mountainash_expressions/core/expression_parameters/__init__.py
- src/mountainash_expressions/core/expression_visitors/__init__.py
- src/mountainash_expressions/core/expression_visitors/boolean_mixins/__init__.py
- src/mountainash_expressions/core/expression_visitors/common_mixins/__init__.py
- src/mountainash_expressions/backends/__init__.py

**CONSEQUENCE**: Package cannot be imported properly. Relative imports will fail.

---

## DEPRECATED ARCHIVE (_deprecated/)

The _deprecated/mountainash_expressions/ folder contains the OLD architecture:

```
_deprecated/mountainash_expressions/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── constants.py          # CONSTANTS LIVE HERE (not in src/)
│   ├── logic/                # Logic implementations
│   │   ├── __init__.py
│   │   ├── boolean/          # Boolean logic (2+ files)
│   │   └── ternary/          # Ternary logic (4 files)
│   └── visitor/              # Visitor implementations
│       ├── __init__.py
│       ├── backends/         # Backend-specific visitors (5+ backends)
│       └── logic/            # Logic-specific visitors
├── backends/                 # Backend implementations
│   ├── ibis/
│   ├── narwhals/
│   ├── pandas/
│   ├── polars/
│   └── pyarrow/
```

Contains **52 Python files** from the old modular architecture.

---

## DISCREPANCIES BETWEEN CLAUDE.MD & ACTUAL STRUCTURE

| Expected (CLAUDE.md) | Actual |
|---|---|
| core/logic/boolean/ | Only boolean_expession_nodes.py in expression_nodes/ |
| core/logic/ternary/ | NOT IN SRC (narwhals has ternary support) |
| core/logic/expression_builder.py | MISSING |
| core/logic/expression_converter.py | MISSING |
| core/logic/conversion_matrix.py | MISSING |
| core/visitor/visitor_factory.py | MISSING |
| Multiple __init__.py files | Only 1 __init__.py exists |
| constants.py in src/ | NOT IN SRC (in _deprecated only) |
| backends/ibis/ | MISSING |
| backends/pandas/ | MISSING |
| backends/polars/ | MISSING |
| backends/pyarrow/ | MISSING |
| Only backends/narwhals/ | EXISTS & IMPLEMENTED |

---

## CRITICAL ISSUES

1. **Missing Main __init__.py**: No src/mountainash_expressions/__init__.py - package cannot be imported
2. **Missing Constants File**: Imports from non-existent ..constants
3. **Missing __init__.py in Subdirectories**: 7 missing __init__.py files break namespace packages
4. **Architecture Mismatch**: CLAUDE.md describes consolidated structure but actual code is incomplete
5. **Incomplete Backend Support**: Only Narwhals; Pandas, Polars, Ibis, PyArrow not in src/
6. **Missing Core Utilities**: Builder, Converter, Conversion Matrix not implemented
7. **Import Path Issues**: References to non-existent modules (e.g., ExpressionVisitorFactory)

---

## WHAT EXISTS & IS FUNCTIONAL

✓ Base expression node hierarchy (11 types)
✓ Boolean expression nodes (6 types)
✓ Boolean visitor implementation
✓ Expression parameter type detection system
✓ Boolean operation mixins (5 types)
✓ Common operation mixins (4 types)
✓ Backend visitor interface
✓ Narwhals backend implementation (Boolean & Ternary)
✓ Typo found: "boolean_expession_nodes.py" (missing 'r')
✓ Typo found: "boolean_logicial_constant_visitor_mixin.py" (should be "logical")

---

## WHAT'S INCOMPLETE/MISSING

✗ Main package initialization
✗ Constants module
✗ Package exports/imports
✗ Expression builder system
✗ Expression converter system
✗ Conversion matrix (Boolean ↔ Ternary)
✗ Ternary node implementations (in src/)
✗ Ternary visitor (in core/, narwhals has it)
✗ Visitor factory
✗ Pandas backend
✗ Polars backend
✗ Ibis backend
✗ PyArrow backend
✗ All required __init__.py files
