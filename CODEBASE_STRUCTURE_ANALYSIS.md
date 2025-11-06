# MOUNTAINASH-EXPRESSIONS CODEBASE STRUCTURE - FINAL REPORT

## Executive Summary

The mountainash-expressions package is a dual-logic expression system that is **currently incomplete and partially migrated**. It has 20 Python files (2,634 lines) in the active src/ directory, with a deprecated archive containing the previous architecture with 52 files.

**Critical Finding**: The codebase cannot currently be imported due to missing __init__.py files (8 of 9) and a missing constants module that all code attempts to import.

---

## Complete Directory Map with Absolute Paths

### ACTIVE SOURCE CODE DIRECTORY

```
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/
├── backends/
│   ├── (MISSING __init__.py)
│   └── narwhals/                                    [EXISTS, FULLY IMPLEMENTED]
│       ├── __init__.py
│       ├── narwhals_visitor.py
│       ├── narwhals_boolean_visitor.py
│       ├── narwhals_ternary_visitor.py
│       └── narwhals_parameters.py
│
└── core/                                            [MISSING __init__.py]
    ├── backend_visitors/                           [MISSING __init__.py]
    │   └── backend_visitor.py
    │
    ├── expression_nodes/                           [MISSING __init__.py]
    │   ├── expression_nodes.py
    │   └── boolean_expession_nodes.py              [TYPO in filename]
    │
    ├── expression_parameters/                      [MISSING __init__.py]
    │   └── expression_parameter.py
    │
    └── expression_visitors/                        [MISSING __init__.py]
        ├── expression_visitor.py
        ├── boolean_expression_visitor.py
        ├── boolean_mixins/                         [MISSING __init__.py]
        │   ├── boolean_collection_visitor_mixin.py
        │   ├── boolean_comparison_visitor_mixin.py
        │   ├── boolean_logical_visitor_mixin.py
        │   ├── boolean_logicial_constant_visitor_mixin.py [TYPO in filename]
        │   └── boolean_unary_visitor_mixin.py
        │
        └── common_mixins/                          [MISSING __init__.py]
            ├── cast_visitor_mixin.py
            ├── literal_visitor_mixin.py
            ├── native_expression_visitor_mixin.py
            └── source_visitor_mixin.py
```

---

## COMPLETE FILE LISTING WITH ABSOLUTE PATHS

### 1. NARWHALS BACKEND IMPLEMENTATION (5 files)

1. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/__init__.py`
   - Size: 323 bytes | Lines: 9
   - Exports: NarwhalsBackendVisitorMixin, NarwhalsBooleanExpressionVisitor, NarwhalsTernaryExpressionVisitor

2. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_visitor.py`
   - Size: ~2.3 KB | Lines: 72
   - Class: NarwhalsBackendBaseVisitor
   - Purpose: Base Narwhals visitor with collection/comparison operations

3. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_boolean_visitor.py`
   - Size: ~4.2 KB | Lines: 117
   - Class: NarwhalsBooleanExpressionVisitor
   - Purpose: Boolean expression support for Narwhals

4. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_ternary_visitor.py`
   - Size: ~12.6 KB | Lines: 282
   - Class: NarwhalsTernaryExpressionVisitor
   - Purpose: Ternary (3-valued) logic support for Narwhals

5. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_parameters.py`
   - Size: 0 bytes | Lines: 0
   - Status: EMPTY FILE (placeholder)

### 2. CORE - BACKEND VISITORS (1 file)

6. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/backend_visitors/backend_visitor.py`
   - Size: ~791 bytes | Lines: 43
   - Class: BackendVisitor (ABC)
   - Purpose: Abstract interface for backend-specific operations

### 3. CORE - EXPRESSION NODES (2 files)

7. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_nodes/expression_nodes.py`
   - Size: ~6.5 KB | Lines: 259
   - Purpose: Base expression node hierarchy (11 node types)
   - Classes: ExpressionNode, NativeBackendExpressionNode, SourceExpressionNode, LiteralExpressionNode, CastExpressionNode, LogicalConstantExpressionNode, UnaryExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, CollectionExpressionNode, ArithmeticExpressionNode, ConditionalIfElseExpressionNode

8. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_nodes/boolean_expession_nodes.py`
   - Size: ~4.5 KB | Lines: 129
   - Purpose: Boolean-specific expression nodes (6 classes)
   - Classes: BooleanExpressionNode, BooleanUnaryExpressionNode, BooleanLogicalExpressionNode, BooleanComparisonExpressionNode, BooleanConditionalIfElseExpressionNode, BooleanCollectionExpressionNode
   - NOTE: Filename has typo (missing 'r' in 'expression')

### 4. CORE - EXPRESSION PARAMETERS (1 file)

9. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_parameters/expression_parameter.py`
   - Size: ~5.1 KB | Lines: ~150
   - Classes: ParameterType (enum), ExpressionParameter
   - Purpose: Parameter type detection and conversion
   - Parameter Types: EXPRESSION_NODE, NATIVE_EXPRESSION, COLUMN_REFERENCE, LITERAL_VALUE, UNKNOWN

### 5. CORE - EXPRESSION VISITORS - BASE (2 files)

10. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/expression_visitor.py`
    - Size: ~4.7 KB | Lines: 154
    - Class: ExpressionVisitor (ABC)
    - Purpose: Abstract visitor interface for expression evaluation
    - Key Concepts: backend_type property, logic_type property, operation dispatch

11. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_expression_visitor.py`
    - Size: ~11.3 KB | Lines: 342
    - Class: BooleanExpressionVisitor
    - Purpose: Boolean logic visitor implementation

### 6. CORE - EXPRESSION VISITORS - BOOLEAN MIXINS (5 files)

12. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_collection_visitor_mixin.py`
    - Size: ~3.2 KB | Lines: ~104
    - Purpose: Collection operations (IN, CONTAINS)

13. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_comparison_visitor_mixin.py`
    - Size: ~3.3 KB | Lines: ~104
    - Purpose: Comparison operations (EQ, NE, GT, LT, GE, LE)

14. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_logical_visitor_mixin.py`
    - Size: ~3.3 KB | Lines: ~104
    - Purpose: Logical operations (AND, OR, XOR)

15. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_logicial_constant_visitor_mixin.py`
    - Size: ~2.2 KB | Lines: ~69
    - Purpose: Logical constants (ALWAYS_TRUE, ALWAYS_FALSE)
    - NOTE: Filename has typo ("logicial" should be "logical")

16. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_unary_visitor_mixin.py`
    - Size: ~3.2 KB | Lines: ~103
    - Purpose: Unary operations (NOT)

### 7. CORE - EXPRESSION VISITORS - COMMON MIXINS (4 files)

17. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/cast_visitor_mixin.py`
    - Size: ~4.7 KB | Lines: ~150
    - Purpose: Type casting operations (CAST operator)

18. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/literal_visitor_mixin.py`
    - Size: ~4.7 KB | Lines: ~150
    - Purpose: Literal value handling (LIT operator)

19. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/native_expression_visitor_mixin.py`
    - Size: ~4.7 KB | Lines: ~150
    - Purpose: Backend-native expression passthrough

20. `/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/source_visitor_mixin.py`
    - Size: ~4.7 KB | Lines: ~150
    - Purpose: Source column reference handling (COL operator)

---

## MISSING COMPONENTS

### Critical Missing Files

| Component | Status | Impact |
|-----------|--------|--------|
| src/mountainash_expressions/__init__.py | MISSING | Package cannot be imported |
| src/mountainash_expressions/constants.py | MISSING | All imports fail (CONST_*) |
| src/mountainash_expressions/core/__init__.py | MISSING | Core module not accessible |
| src/mountainash_expressions/backends/__init__.py | MISSING | Backends module not accessible |
| 6 more __init__.py files | MISSING | Subdirectory imports fail |

### Missing Backend Implementations

| Backend | Status |
|---------|--------|
| Narwhals | IMPLEMENTED |
| Pandas | MISSING |
| Polars | MISSING |
| Ibis | MISSING |
| PyArrow | MISSING |

### Missing Core Modules

| Module | Purpose | Status |
|--------|---------|--------|
| expression_builder.py | Build expressions fluently | MISSING |
| expression_converter.py | Convert between logic types | MISSING |
| conversion_matrix.py | Boolean ↔ Ternary mapping | MISSING |
| visitor_factory.py | Auto-select visitor by backend | MISSING |
| ternary_nodes.py | Ternary expression nodes | MISSING (has support in narwhals) |

---

## DEPRECATED ARCHIVE

Location: `/home/nathanielramm/git/mountainash/mountainash-expressions/_deprecated/mountainash_expressions/`

Contains 52 Python files from old architecture:
- constants.py (THE MISSING CONSTANTS!)
- core/logic/boolean/ - Old boolean implementation
- core/logic/ternary/ - Old ternary implementation
- core/visitor/backends/ - 5 backend implementations
- backends/ibis/, pandas/, polars/, pyarrow/, narwhals/

---

## CONSTANTS THAT ARE IMPORTED BUT DON'T EXIST

All code imports these constants from a missing module:

```python
from ..constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES
from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_VISITOR_BACKENDS
```

**Defined in** (deprecated): 
`/home/nathanielramm/git/mountainash/mountainash-expressions/_deprecated/mountainash_expressions/core/constants.py`

**Contains**:
- CONST_VISITOR_BACKENDS (enum: PANDAS, POLARS, IBIS, PYARROW)
- CONST_LOGIC_TYPES (enum: BOOLEAN, TERNARY, FUZZY)
- CONST_EXPRESSION_NODE_TYPES (enum: LITERAL, COLUMN, LOGICAL, + 8 more)
- CONST_EXPRESSION_LOGIC_OPERATORS (30+ operators)
- CONST_TERNARY_LOGIC_VALUES (IntEnum: -1=FALSE, 0=UNKNOWN, 1=TRUE)

---

## KNOWN ISSUES & TYPOS

| Issue | File | Severity |
|-------|------|----------|
| Filename typo: "expession" missing 'r' | boolean_expession_nodes.py | LOW |
| Filename typo: "logicial" should be "logical" | boolean_logicial_constant_visitor_mixin.py | LOW |
| Missing constants.py | Imported by all modules | CRITICAL |
| Missing main __init__.py | Package root | CRITICAL |
| Missing 8 __init__.py files | All subdirs | HIGH |
| Empty narwhals_parameters.py | Placeholder file | LOW |
| References to ExpressionVisitorFactory | Doesn't exist | HIGH |
| Only Narwhals backend | vs. documented 5 | MEDIUM |

---

## IMPLEMENTATION STATUS SUMMARY

### Implemented (20 files, 2,634 lines)

✓ Expression node hierarchy (12 node types)
✓ Boolean expression nodes (6 types)
✓ Boolean visitor implementation
✓ Boolean operation handlers (5 mixins)
✓ Common operation handlers (4 mixins)
✓ Expression parameter detection system
✓ Backend visitor interface
✓ Narwhals backend (Boolean + Ternary)

### Not Implemented in src/

✗ Main package initialization
✗ Constants module
✗ Package-level exports
✗ Expression builder
✗ Expression converter
✗ Conversion matrix
✗ Visitor factory
✗ Ternary node implementations
✗ Pandas backend
✗ Polars backend
✗ Ibis backend
✗ PyArrow backend

---

## ARCHITECTURE MISMATCH WITH CLAUDE.MD

The CLAUDE.md file documents an expected consolidated architecture that doesn't match the actual implementation:

| Expected (CLAUDE.md) | Actual | Delta |
|---|---|---|
| core/logic/boolean/ directory | Not present | File moved to expression_nodes/ |
| core/logic/ternary/ directory | Only narwhals backend | Missing core ternary |
| expression_builder.py | Missing | Not implemented |
| expression_converter.py | Missing | Not implemented |
| conversion_matrix.py | Missing | Not implemented |
| visitor_factory.py | Missing | Not implemented |
| Multiple __init__.py files | Only 1 exists | 8 missing |
| constants.py in src/ | In _deprecated/ | Migration incomplete |
| 5 backend implementations | Only narwhals | 4 missing |

---

## RECOMMENDATIONS

1. **Immediate**: Create the 9 missing __init__.py files
2. **Critical**: Migrate or recreate constants.py in src/
3. **High Priority**: Implement or migrate core utility modules (builder, converter, factory)
4. **Medium Priority**: Complete backend implementations or migrate from _deprecated/
5. **Low Priority**: Fix filenames (expession → expression, logicial → logical)

---

## ABSOLUTE FILE PATHS REFERENCE

All 20 source files:

```
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/__init__.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_visitor.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_boolean_visitor.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_ternary_visitor.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/backends/narwhals/narwhals_parameters.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/backend_visitors/backend_visitor.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_nodes/expression_nodes.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_nodes/boolean_expession_nodes.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_parameters/expression_parameter.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/expression_visitor.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_expression_visitor.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_collection_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_comparison_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_logical_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_logicial_constant_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/boolean_mixins/boolean_unary_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/cast_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/literal_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/native_expression_visitor_mixin.py
/home/nathanielramm/git/mountainash/mountainash-expressions/src/mountainash_expressions/core/expression_visitors/common_mixins/source_visitor_mixin.py
```

