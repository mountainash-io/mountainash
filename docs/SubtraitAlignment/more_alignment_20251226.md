 │ Mountainash Expression System Migration Plan                                                                                                                 │
   │                                                                                                                                                              │
   │ Migration Plan: Align mountainash-expressions with Substrait topology using deprecated reference implementations                                             │
   │                                                                                                                                                              │
   │ Executive Summary                                                                                                                                            │
   │                                                                                                                                                              │
   │ | Phase   | Component               | Status | Work Items                                      |                                                             │
   │ |---------|-------------------------|--------|-------------------------------------------------|                                                             │
   │ | Phase 1 | Node Layer Fixes        | TODO   | Fix SingularOrListNode, ConditionalNode imports |                                                             │
   │ | Phase 2 | Backend Reorganization  | TODO   | Rename modules → Substrait topology             |                                                             │
   │ | Phase 3 | Method Migration        | TODO   | Port 250+ methods from deprecated               |                                                             │
   │ | Phase 4 | Protocol Alignment      | TODO   | Complete protocol stubs                         |                                                             │
   │ | Phase 5 | API Namespace Exposure  | TODO   | Expose 65 missing API methods                   |                                                             │
   │ | Phase 6 | New Function Categories | TODO   | Rounding, Logarithmic, Set, Aggregate           |                                                             │
   │ | Phase 7 | Substrait Serialization | TODO   | to_substrait/from_substrait                     |                                                             │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 1: Node Layer Fixes (DETAILED)                                                                                                                         │
   │                                                                                                                                                              │
   │ GitHub Issues                                                                                                                                                │
   │                                                                                                                                                              │
   │ - Milestone: https://github.com/mountainash-io/mountainash-expressions/milestone/1                                                                           │
   │ - Issue #1: Create SingularOrListNode expression node                                                                                                        │
   │ - Issue #2: Fix ConditionalNode import in init.py                                                                                                            │
   │ - Issue #3: Add visit_singular_or_list() to UnifiedExpressionVisitor                                                                                         │
   │ - Issue #4: Implement is_in() in backend expression systems                                                                                                  │
   │                                                                                                                                                              │
   │ Current State Analysis                                                                                                                                       │
   │                                                                                                                                                              │
   │ Expression Nodes Directory:                                                                                                                                  │
   │ ├── exn_base.py           ✅ EXISTS - Abstract base class                                                                                                    │
   │ ├── exn_literal.py        ✅ EXISTS - Constant values                                                                                                        │
   │ ├── exn_field_reference.py ✅ EXISTS - Column references                                                                                                     │
   │ ├── exn_scalar_function.py ✅ EXISTS - Function calls                                                                                                        │
   │ ├── exn_ifthen.py         ✅ EXISTS - Conditional (when/then/otherwise)                                                                                      │
   │ ├── exn_cast.py           ✅ EXISTS - Type conversions                                                                                                       │
   │ ├── exn_conditional.py    ❌ MISSING - Imported but doesn't exist                                                                                            │
   │ └── exn_singular_or_list.py ❌ MISSING - Imported but doesn't exist                                                                                          │
   │                                                                                                                                                              │
   │ Issue #1: Create SingularOrListNode                                                                                                                          │
   │                                                                                                                                                              │
   │ Problem:                                                                                                                                                     │
   │ - visitor.py line 25 imports SingularOrListNode from ..expression_nodes                                                                                      │
   │ - expression_nodes/__init__.py declares it in docstring but doesn't import                                                                                   │
   │ - File exn_singular_or_list.py does NOT exist                                                                                                                │
   │                                                                                                                                                              │
   │ File to Create: src/mountainash_expressions/core/expression_nodes/exn_singular_or_list.py                                                                    │
   │                                                                                                                                                              │
   │ """SingularOrList node for membership tests (IN operator).                                                                                                   │
   │                                                                                                                                                              │
   │ Corresponds to Substrait's SingularOrList expression type.                                                                                                   │
   │ Used for: value IN (option1, option2, ...)                                                                                                                   │
   │ """                                                                                                                                                          │
   │                                                                                                                                                              │
   │ from __future__ import annotations                                                                                                                           │
   │ from typing import Any, List                                                                                                                                 │
   │                                                                                                                                                              │
   │ from .exn_base import ExpressionNode                                                                                                                         │
   │                                                                                                                                                              │
   │                                                                                                                                                              │
   │ class SingularOrListNode(ExpressionNode):                                                                                                                    │
   │     """Substrait SingularOrList - membership test (IN operator).                                                                                             │
   │                                                                                                                                                              │
   │     Tests if a value is contained within a list of options.                                                                                                  │
   │     Equivalent to SQL: value IN (option1, option2, ...)                                                                                                      │
   │                                                                                                                                                              │
   │     Unlike other nodes, SingularOrListNode does NOT have a function_key                                                                                      │
   │     because it's a structural expression type, not a function call.                                                                                          │
   │     (Same pattern as IfThenNode, CastNode, LiteralNode, FieldReferenceNode)                                                                                  │
   │                                                                                                                                                              │
   │     Attributes:                                                                                                                                              │
   │         value: The expression to test for membership                                                                                                         │
   │         options: List of expressions representing possible values                                                                                            │
   │                                                                                                                                                              │
   │     Examples:                                                                                                                                                │
   │         >>> # status IN ('active', 'pending')                                                                                                                │
   │         >>> SingularOrListNode(                                                                                                                              │
   │         ...     value=FieldReferenceNode(column="status"),                                                                                                   │
   │         ...     options=[                                                                                                                                    │
   │         ...         LiteralNode(value="active"),                                                                                                             │
   │         ...         LiteralNode(value="pending"),                                                                                                            │
   │         ...     ]                                                                                                                                            │
   │         ... )                                                                                                                                                │
   │     """                                                                                                                                                      │
   │                                                                                                                                                              │
   │     value: ExpressionNode                                                                                                                                    │
   │     options: List[ExpressionNode]                                                                                                                            │
   │                                                                                                                                                              │
   │     def accept(self, visitor: Any) -> Any:                                                                                                                   │
   │         """Accept a visitor for double-dispatch."""                                                                                                          │
   │         return visitor.visit_singular_or_list(self)                                                                                                          │
   │                                                                                                                                                              │
   │ Note on Base Class Architecture:                                                                                                                             │
   │                                                                                                                                                              │
   │ The base class ExpressionNode declares function_key: Enum but no child classes actually use it:                                                              │
   │ - LiteralNode - no function_key                                                                                                                              │
   │ - FieldReferenceNode - no function_key                                                                                                                       │
   │ - ScalarFunctionNode - has function_key COMMENTED OUT (lines 41-42)                                                                                          │
   │ - IfThenNode - no function_key                                                                                                                               │
   │ - CastNode - no function_key                                                                                                                                 │
   │                                                                                                                                                              │
   │ Analysis: The function_key in base class appears to be a design artifact that's not currently used.                                                          │
   │ All structural expression types (Literal, FieldReference, IfThen, Cast, SingularOrList) don't need it.                                                       │
   │ ScalarFunctionNode has it commented out, suggesting it was planned but not implemented.                                                                      │
   │                                                                                                                                                              │
   │ Recommendation for SingularOrListNode: Follow the existing pattern - just don't define function_key.                                                         │
   │ The Pydantic BaseModel inheritance doesn't require redefinition of parent fields.                                                                            │
   │                                                                                                                                                              │
   │ Future Technical Debt: Consider removing function_key: Enum from ExpressionNode base class                                                                   │
   │ since no children actually use it. This is outside Phase 1 scope but noted for Phase 2.                                                                      │
   │                                                                                                                                                              │
   │ Issue #2: Fix ConditionalNode Import                                                                                                                         │
   │                                                                                                                                                              │
   │ Problem:                                                                                                                                                     │
   │ - expression_nodes/__init__.py line 24: from .exn_conditional import ConditionalNode                                                                         │
   │ - File exn_conditional.py does NOT exist                                                                                                                     │
   │ - File exn_ifthen.py EXISTS with IfThenNode class                                                                                                            │
   │                                                                                                                                                              │
   │ File to Modify: src/mountainash_expressions/core/expression_nodes/__init__.py                                                                                │
   │                                                                                                                                                              │
   │ Current (BROKEN):                                                                                                                                            │
   │ from .exn_conditional import ConditionalNode  # Line 24                                                                                                      │
   │                                                                                                                                                              │
   │ Fixed:                                                                                                                                                       │
   │ from .exn_ifthen import IfThenNode                                                                                                                           │
   │ # Backward compatibility alias                                                                                                                               │
   │ ConditionalNode = IfThenNode                                                                                                                                 │
   │                                                                                                                                                              │
   │ Additional Changes:                                                                                                                                          │
   │ - Add SingularOrListNode to imports                                                                                                                          │
   │ - Add to __all__ list                                                                                                                                        │
   │                                                                                                                                                              │
   │ Issue #3: Visitor Method (ALREADY IMPLEMENTED)                                                                                                               │
   │                                                                                                                                                              │
   │ Discovery: The visitor already has visit_singular_or_list implemented!                                                                                       │
   │                                                                                                                                                              │
   │ File: src/mountainash_expressions/core/unified_visitor/visitor.py                                                                                            │
   │ - Line 25: Imports SingularOrListNode (will work once file exists)                                                                                           │
   │ - Lines ~380-408: visit_singular_or_list() method already implemented                                                                                        │
   │                                                                                                                                                              │
   │ def visit_singular_or_list(self, node: SingularOrListNode) -> SupportedExpressions:                                                                          │
   │     """Compile membership test to backend expression.                                                                                                        │
   │                                                                                                                                                              │
   │     Args:                                                                                                                                                    │
   │         node: SingularOrListNode with value and options list                                                                                                 │
   │                                                                                                                                                              │
   │     Returns:                                                                                                                                                 │
   │         Backend is_in expression                                                                                                                             │
   │     """                                                                                                                                                      │
   │     # Visit the value being tested                                                                                                                           │
   │     value_expr = self.visit(node.value)                                                                                                                      │
   │                                                                                                                                                              │
   │     # For is_in, we typically pass the literal values directly                                                                                               │
   │     options = []                                                                                                                                             │
   │     for opt in node.options:                                                                                                                                 │
   │         if isinstance(opt, LiteralNode):                                                                                                                     │
   │             options.append(opt.value)                                                                                                                        │
   │         elif isinstance(opt, SubstraitNode):                                                                                                                 │
   │             options.append(self.visit(opt))                                                                                                                  │
   │         else:                                                                                                                                                │
   │             options.append(opt)                                                                                                                              │
   │                                                                                                                                                              │
   │     return self.backend.is_in(value_expr, *options)                                                                                                          │
   │                                                                                                                                                              │
   │ Status: ✅ NO WORK NEEDED (already done)                                                                                                                     │
   │                                                                                                                                                              │
   │ Issue #4: Backend is_in() Methods (ALREADY IMPLEMENTED)                                                                                                      │
   │                                                                                                                                                              │
   │ Discovery: All backends already have is_in() methods!                                                                                                        │
   │                                                                                                                                                              │
   │ | Backend  | File                                            | Line | Status    |                                                                            │
   │ |----------|-------------------------------------------------|------|-----------|                                                                            │
   │ | Polars   | backends/expression_systems/polars/boolean.py   | 257  | ✅ EXISTS |                                                                            │
   │ | Narwhals | backends/expression_systems/narwhals/boolean.py | 127  | ✅ EXISTS |                                                                            │
   │ | Ibis     | backends/expression_systems/ibis/boolean.py     | 88   | ✅ EXISTS |                                                                            │
   │                                                                                                                                                              │
   │ Polars Implementation (line 257-268):                                                                                                                        │
   │ def is_in(self, element: Any, collection: List[Any]) -> pl.Expr:                                                                                             │
   │     """Membership test using Polars is_in() method.                                                                                                          │
   │     ...                                                                                                                                                      │
   │     """                                                                                                                                                      │
   │     return element.is_in(collection)                                                                                                                         │
   │                                                                                                                                                              │
   │ Narwhals Implementation (line 127-129):                                                                                                                      │
   │ def is_in(self, element: Any, collection: List[Any]) -> nw.Expr:                                                                                             │
   │     """Membership test using Narwhals is_in() method."""                                                                                                     │
   │     return element.is_in(collection)                                                                                                                         │
   │                                                                                                                                                              │
   │ Status: ✅ NO WORK NEEDED (already done)                                                                                                                     │
   │                                                                                                                                                              │
   │ Phase 1 Implementation Summary                                                                                                                               │
   │                                                                                                                                                              │
   │ | Issue | Description                | Work Required              |                                                                                          │
   │ |-------|----------------------------|----------------------------|                                                                                          │
   │ | #1    | Create SingularOrListNode  | CREATE new file (48 lines) |                                                                                          │
   │ | #2    | Fix ConditionalNode import | EDIT init.py (3 lines)     |                                                                                          │
   │ | #3    | Add visitor method         | ✅ ALREADY DONE            |                                                                                          │
   │ | #4    | Backend is_in() methods    | ✅ ALREADY DONE            |                                                                                          │
   │                                                                                                                                                              │
   │ Total Work: ~55 lines of code in 2 files                                                                                                                     │
   │                                                                                                                                                              │
   │ Files to Modify/Create                                                                                                                                       │
   │                                                                                                                                                              │
   │ CREATE: src/mountainash_expressions/core/expression_nodes/exn_singular_or_list.py                                                                            │
   │ MODIFY: src/mountainash_expressions/core/expression_nodes/__init__.py                                                                                        │
   │                                                                                                                                                              │
   │ Existing Code That Uses SingularOrListNode                                                                                                                   │
   │                                                                                                                                                              │
   │ Discovery: Several API namespaces already create SingularOrListNode instances:                                                                               │
   │                                                                                                                                                              │
   │ | File                                           | Line | Method    |                                                                                        │
   │ |------------------------------------------------|------|-----------|                                                                                        │
   │ | api_namespaces/core/exns_scalar_boolean.py     | 197  | is_in()   |                                                                                        │
   │ | api_namespaces/deprecated/boolean.py           | 192  | is_in()   |                                                                                        │
   │ | api_namespaces/deprecated/scalar_comparison.py | 195  | is_in()   |                                                                                        │
   │ | api_namespaces/deprecated/ternary.py           | 156  | t_is_in() |                                                                                        │
   │                                                                                                                                                              │
   │ Current Code Pattern (from exns_scalar_boolean.py:215-218):                                                                                                  │
   │ node = SingularOrListNode(                                                                                                                                   │
   │     value=self._node,                                                                                                                                        │
   │     options=[LiteralNode(value=v) for v in values],                                                                                                          │
   │ )                                                                                                                                                            │
   │                                                                                                                                                              │
   │ Implication: These files will work once SingularOrListNode exists. No changes needed to API namespaces.                                                      │
   │                                                                                                                                                              │
   │ Validation Steps                                                                                                                                             │
   │                                                                                                                                                              │
   │ After implementation, verify:                                                                                                                                │
   │ 1. python -c "from mountainash_expressions.core.expression_nodes import SingularOrListNode"                                                                  │
   │ 2. python -c "from mountainash_expressions.core.expression_nodes import ConditionalNode, IfThenNode; assert ConditionalNode is IfThenNode"                   │
   │ 3. python -c "from mountainash_expressions.core.expression_api.api_namespaces.core.exns_scalar_boolean import BooleanAPINamespace" (uses SingularOrListNode) │
   │ 4. Run existing tests: hatch run test:test                                                                                                                   │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Source Reference: Deprecated Implementations                                                                                                                 │
   │                                                                                                                                                              │
   │ Available Migration Sources                                                                                                                                  │
   │                                                                                                                                                              │
   │ | Source Location                         | Contents                  | Lines |                                                                              │
   │ |-----------------------------------------|---------------------------|-------|                                                                              │
   │ | _deprecated/202511/expression_nodes/    | 14 node classes           | ~1000 |                                                                              │
   │ | _deprecated/202511/expression_builders/ | 11 builder classes        | ~2374 |                                                                              │
   │ | _deprecated/202511/expression_visitors/ | 10 visitor mixins         | ~896  |                                                                              │
   │ | _deprecated/202510/backends/            | Backend-specific visitors | ~500+ |                                                                              │
   │                                                                                                                                                              │
   │ Key Deprecated Files by Category                                                                                                                             │
   │                                                                                                                                                              │
   │ Boolean Operations:                                                                                                                                          │
   │ ├── boolean_operators_visitor_mixin.py   → and_, or_, not_, xor_                                                                                             │
   │ ├── boolean_comparison_visitor_mixin.py  → eq, ne, gt, lt, ge, le                                                                                            │
   │ ├── boolean_unary_visitor_mixin.py       → is_true, is_false                                                                                                 │
   │ └── boolean_collection_visitor_mixin.py  → is_in, contains                                                                                                   │
   │                                                                                                                                                              │
   │ String Operations:                                                                                                                                           │
   │ └── string_operators_visitor_mixin.py    → 12 operations mapped                                                                                              │
   │                                                                                                                                                              │
   │ Temporal Operations:                                                                                                                                         │
   │ └── temporal_operators_visitor_mixin.py  → 23 operations mapped                                                                                              │
   │                                                                                                                                                              │
   │ Arithmetic Operations:                                                                                                                                       │
   │ └── arithmetic_operators_visitor_mixin.py → add, subtract, multiply, etc.                                                                                    │
   │                                                                                                                                                              │
   │ Conditional Operations:                                                                                                                                      │
   │ └── conditional_operators_visitor_mixin.py → when_then_else, coalesce                                                                                        │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 1: Node Layer Fixes                                                                                                                                    │
   │                                                                                                                                                              │
   │ 1.1 Fix Missing SingularOrListNode                                                                                                                           │
   │                                                                                                                                                              │
   │ Problem: Declared in __init__.py but exn_singular_or_list.py doesn't exist                                                                                   │
   │                                                                                                                                                              │
   │ Reference: _deprecated/202511/expression_nodes/ contains BooleanCollectionExpressionNode                                                                     │
   │                                                                                                                                                              │
   │ Files to Create/Modify:                                                                                                                                      │
   │ - Create core/expression_nodes/exn_singular_or_list.py                                                                                                       │
   │ - Port implementation from deprecated BooleanCollectionExpressionNode                                                                                        │
   │ - Add visit_singular_or_list() to UnifiedExpressionVisitor                                                                                                   │
   │ - Add is_in() backend implementations                                                                                                                        │
   │                                                                                                                                                              │
   │ 1.2 Fix ConditionalNode Import                                                                                                                               │
   │                                                                                                                                                              │
   │ Problem: __init__.py imports from non-existent exn_conditional.py                                                                                            │
   │                                                                                                                                                              │
   │ Fix: Update import to reference exn_ifthen.py (IfThenNode)                                                                                                   │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 2: Backend Module Reorganization                                                                                                                       │
   │                                                                                                                                                              │
   │ Decision: Full Substrait naming + Mountainash extensions                                                                                                     │
   │                                                                                                                                                              │
   │ Current → Substrait Module Mapping                                                                                                                           │
   │                                                                                                                                                              │
   │ CURRENT (14 modules)           →  SUBSTRAIT + EXTENSIONS (18 modules)                                                                                        │
   │ ─────────────────────────────────────────────────────────────────────                                                                                        │
   │ core.py (col, lit)             →  field_reference.py + literal.py                                                                                            │
   │ arithmetic.py                  →  scalar_arithmetic.py                                                                                                       │
   │ boolean.py (comparisons)       →  scalar_comparison.py                                                                                                       │
   │ boolean.py (logical)           →  scalar_boolean.py                                                                                                          │
   │ boolean.py (is_in)             →  scalar_set.py                                                                                                              │
   │ string.py                      →  scalar_string.py                                                                                                           │
   │ temporal.py                    →  scalar_datetime.py                                                                                                         │
   │ null.py                        →  (merge into scalar_comparison)                                                                                             │
   │ horizontal.py                  →  (merge into scalar_comparison)                                                                                             │
   │ conditional.py                 →  conditional.py                                                                                                             │
   │ type.py                        →  cast.py                                                                                                                    │
   │ (missing)                      →  scalar_rounding.py (NEW)                                                                                                   │
   │ (missing)                      →  scalar_logarithmic.py (NEW)                                                                                                │
   │ (missing)                      →  scalar_aggregate.py (NEW)                                                                                                  │
   │                                                                                                                                                              │
   │ MOUNTAINASH EXTENSIONS (keep separate):                                                                                                                      │
   │ name.py                        →  ext_name.py (Mountainash extension)                                                                                        │
   │ native.py                      →  ext_native.py (Mountainash extension)                                                                                      │
   │ ternary.py                     →  ext_ternary.py (Mountainash extension)                                                                                     │
   │                                                                                                                                                              │
   │ 2.1 Rename Core Modules                                                                                                                                      │
   │                                                                                                                                                              │
   │ For each backend (polars, narwhals, ibis):                                                                                                                   │
   │ - core.py → split into field_reference.py + literal.py                                                                                                       │
   │ - type.py → rename to cast.py                                                                                                                                │
   │                                                                                                                                                              │
   │ 2.2 Split Boolean Module                                                                                                                                     │
   │                                                                                                                                                              │
   │ For each backend:                                                                                                                                            │
   │ - Extract comparisons (eq, ne, gt, lt, ge, le, between, is_null) → scalar_comparison.py                                                                      │
   │ - Extract logical ops (and_, or_, not_, xor_) → scalar_boolean.py                                                                                            │
   │ - Extract set ops (is_in) → scalar_set.py                                                                                                                    │
   │                                                                                                                                                              │
   │ 2.3 Merge Horizontal/Null into Comparison                                                                                                                    │
   │                                                                                                                                                              │
   │ - Move coalesce() from horizontal.py → scalar_comparison.py                                                                                                  │
   │ - Move is_null() from null.py → scalar_comparison.py                                                                                                         │
   │ - Deprecate horizontal.py and null.py                                                                                                                        │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 3: Method Migration from Deprecated                                                                                                                    │
   │                                                                                                                                                              │
   │ 3.1 Arithmetic Methods                                                                                                                                       │
   │                                                                                                                                                              │
   │ Source: _deprecated/202511/expression_visitors/arithmetic_mixins/                                                                                            │
   │                                                                                                                                                              │
   │ | Current        | Deprecated Reference | Status        |                                                                                                    │
   │ |----------------|----------------------|---------------|                                                                                                    │
   │ | add()          | _add()               | Exists        |                                                                                                    │
   │ | subtract()     | _subtract()          | Exists        |                                                                                                    │
   │ | multiply()     | _multiply()          | Exists        |                                                                                                    │
   │ | divide()       | _divide()            | Exists        |                                                                                                    │
   │ | modulo()       | _modulo()            | Exists        |                                                                                                    │
   │ | power()        | _power()             | Exists        |                                                                                                    │
   │ | floor_divide() | _floor_divide()      | Exists        |                                                                                                    │
   │ | negate()       | _negate()            | MISSING - ADD |                                                                                                    │
   │ | abs()          | _abs()               | MISSING - ADD |                                                                                                    │
   │ | sign()         | _sign()              | MISSING - ADD |                                                                                                    │
   │ | sqrt()         | _sqrt()              | MISSING - ADD |                                                                                                    │
   │ | exp()          | _exp()               | MISSING - ADD |                                                                                                    │
   │ | ln()           | _ln()                | MISSING - ADD |                                                                                                    │
   │                                                                                                                                                              │
   │ 3.2 String Methods                                                                                                                                           │
   │                                                                                                                                                              │
   │ Source: _deprecated/202511/expression_visitors/string_mixins/string_operators_visitor_mixin.py                                                               │
   │                                                                                                                                                              │
   │ All 12 operations have deprecated implementations ready to port.                                                                                             │
   │                                                                                                                                                              │
   │ 3.3 Temporal Methods (DUAL API)                                                                                                                              │
   │                                                                                                                                                              │
   │ Decision: Both Substrait and Extension APIs                                                                                                                  │
   │                                                                                                                                                              │
   │ Current: 22 individual methods (dt_year, dt_month, dt_add_days, etc.)                                                                                        │
   │ Substrait: 2 methods with component dispatch                                                                                                                 │
   │                                                                                                                                                              │
   │ Implementation: Implement BOTH patterns independently:                                                                                                       │
   │                                                                                                                                                              │
   │ # Substrait API (scalar_datetime.py)                                                                                                                         │
   │ def extract(self, expr, component: DatetimeComponent) -> Expr:                                                                                               │
   │     """Substrait-standard extraction with component parameter."""                                                                                            │
   │     ...                                                                                                                                                      │
   │                                                                                                                                                              │
   │ def add_intervals(self, expr, interval: Interval) -> Expr:                                                                                                   │
   │     """Substrait-standard interval addition."""                                                                                                              │
   │     ...                                                                                                                                                      │
   │                                                                                                                                                              │
   │ # Extension API (ext_temporal.py) - Keep existing                                                                                                            │
   │ def dt_year(self, expr) -> Expr: ...                                                                                                                         │
   │ def dt_month(self, expr) -> Expr: ...                                                                                                                        │
   │ def dt_add_days(self, expr, days: int) -> Expr: ...                                                                                                          │
   │ # ... all 22 methods                                                                                                                                         │
   │                                                                                                                                                              │
   │ Files:                                                                                                                                                       │
   │ - scalar_datetime.py - Substrait extract() and add_intervals()                                                                                               │
   │ - ext_temporal.py - Mountainash extension with individual methods                                                                                            │
   │                                                                                                                                                              │
   │ 3.4 Comparison Method Renaming                                                                                                                               │
   │                                                                                                                                                              │
   │ Add aliases for Substrait compatibility:                                                                                                                     │
   │                                                                                                                                                              │
   │ | Current | Substrait Alias         |                                                                                                                        │
   │ |---------|-------------------------|                                                                                                                        │
   │ | eq()    | equal()                 |                                                                                                                        │
   │ | ne()    | not_equal()             |                                                                                                                        │
   │ | gt()    | greater_than()          |                                                                                                                        │
   │ | lt()    | less_than()             |                                                                                                                        │
   │ | ge()    | greater_than_or_equal() |                                                                                                                        │
   │ | le()    | less_than_or_equal()    |                                                                                                                        │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 4: Protocol Alignment                                                                                                                                  │
   │                                                                                                                                                              │
   │ 4.1 Complete Protocol Stubs                                                                                                                                  │
   │                                                                                                                                                              │
   │ | Protocol File               | Current   | Target     | Source                       |                                                                      │
   │ |-----------------------------|-----------|------------|------------------------------|                                                                      │
   │ | prtcl_scalar_arithmetic.py  | 7 methods | 12 methods | Uncomment + add missing      |                                                                      │
   │ | prtcl_scalar_boolean.py     | 4 methods | 6 methods  | Add is_true, is_false        |                                                                      │
   │ | prtcl_scalar_comparison.py  | 4 methods | 12 methods | Add between, coalesce, etc.  |                                                                      │
   │ | prtcl_scalar_string.py      | 30 stubs  | 30 methods | Complete implementations     |                                                                      │
   │ | prtcl_scalar_rounding.py    | empty     | 4 methods  | ceil, floor, round, truncate |                                                                      │
   │ | prtcl_scalar_logarithmic.py | empty     | 5 methods  | ln, log, log10, log2, exp    |                                                                      │
   │ | prtcl_scalar_set.py         | empty     | 2 methods  | is_in, index_in              |                                                                      │
   │                                                                                                                                                              │
   │ 4.2 Protocol → Backend Wiring                                                                                                                                │
   │                                                                                                                                                              │
   │ For each protocol method:                                                                                                                                    │
   │ 1. Define protocol signature                                                                                                                                 │
   │ 2. Implement in all 3 backends                                                                                                                               │
   │ 3. Register in function registry                                                                                                                             │
   │ 4. Expose in fluent API                                                                                                                                      │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 5: API Namespace Exposure                                                                                                                              │
   │                                                                                                                                                              │
   │ 5.1 Empty Namespaces to Complete                                                                                                                             │
   │                                                                                                                                                              │
   │ | Namespace      | Methods to Add                                                                   |                                                        │
   │ |----------------|----------------------------------------------------------------------------------|                                                        │
   │ | arithmetic.py  | add, subtract, multiply, divide, modulo, power, negate, abs, sign, sqrt, exp, ln |                                                        │
   │ | cast.py        | cast_to_int, cast_to_float, cast_to_string, cast_to_date, ...                    |                                                        │
   │ | conditional.py | when, then, otherwise, if_else                                                   |                                                        │
   │ | horizontal.py  | coalesce, greatest, least                                                        |                                                        │
   │ | native.py      | native_expr                                                                      |                                                        │
   │                                                                                                                                                              │
   │ 5.2 Partial Namespaces to Extend                                                                                                                             │
   │                                                                                                                                                              │
   │ | Namespace            | Current   | To Add                                                                              |                                   │
   │ |----------------------|-----------|-------------------------------------------------------------------------------------|                                   │
   │ | scalar_comparison.py | 2 methods | eq, ne, gt, lt, ge, le, between                                                     |                                   │
   │ | scalar_string.py     | 6 methods | substring, replace, concat, split, contains, starts_with, ends_with, like, regexp_* |                                   │
   │ | ternary.py           | 8 methods | t_eq, t_ne, t_gt, t_lt, t_ge, t_le, t_is_in, t_is_not_in, t_and, t_or, t_xor        |                                   │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 6: New Function Categories                                                                                                                             │
   │                                                                                                                                                              │
   │ 6.1 Rounding Functions (NEW)                                                                                                                                 │
   │                                                                                                                                                              │
   │ Files to create:                                                                                                                                             │
   │ - backends/*/scalar_rounding.py (3 files)                                                                                                                    │
   │ - expression_protocols/substrait/prtcl_scalar_rounding.py                                                                                                    │
   │ - api_namespaces/rounding.py                                                                                                                                 │
   │                                                                                                                                                              │
   │ Methods: ceil, floor, round, truncate                                                                                                                        │
   │                                                                                                                                                              │
   │ 6.2 Logarithmic Functions (NEW)                                                                                                                              │
   │                                                                                                                                                              │
   │ Files to create:                                                                                                                                             │
   │ - backends/*/scalar_logarithmic.py (3 files)                                                                                                                 │
   │ - expression_protocols/substrait/prtcl_scalar_logarithmic.py                                                                                                 │
   │ - api_namespaces/logarithmic.py                                                                                                                              │
   │                                                                                                                                                              │
   │ Methods: ln, log, log10, log2, exp, sqrt                                                                                                                     │
   │                                                                                                                                                              │
   │ 6.3 Set Functions (NEW)                                                                                                                                      │
   │                                                                                                                                                              │
   │ Files to create:                                                                                                                                             │
   │ - backends/*/scalar_set.py (3 files)                                                                                                                         │
   │ - expression_protocols/substrait/prtcl_scalar_set.py                                                                                                         │
   │                                                                                                                                                              │
   │ Methods: is_in, is_not_in, index_in                                                                                                                          │
   │                                                                                                                                                              │
   │ 6.4 Aggregate Functions (NEW NODE TYPE)                                                                                                                      │
   │                                                                                                                                                              │
   │ Files to create:                                                                                                                                             │
   │ - core/expression_nodes/exn_aggregate.py                                                                                                                     │
   │ - core/expression_nodes/enums/aggregate.py                                                                                                                   │
   │ - backends/*/scalar_aggregate.py (3 files)                                                                                                                   │
   │ - expression_protocols/substrait/prtcl_scalar_aggregate.py                                                                                                   │
   │ - api_namespaces/aggregate.py                                                                                                                                │
   │                                                                                                                                                              │
   │ Methods: sum, count, count_star, avg, min, max, stddev, variance, any_value                                                                                  │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Phase 7: Substrait Serialization                                                                                                                             │
   │                                                                                                                                                              │
   │ 7.1 Export Visitor                                                                                                                                           │
   │                                                                                                                                                              │
   │ File: core/substrait/substrait_export_visitor.py                                                                                                             │
   │                                                                                                                                                              │
   │ class SubstraitExportVisitor(ExpressionVisitor):                                                                                                             │
   │     def visit_literal(self, node: LiteralNode) -> substrait.Literal: ...                                                                                     │
   │     def visit_field_reference(self, node: FieldReferenceNode) -> substrait.FieldReference: ...                                                               │
   │     def visit_scalar_function(self, node: ScalarFunctionNode) -> substrait.ScalarFunction: ...                                                               │
   │     def visit_if_then(self, node: IfThenNode) -> substrait.IfThen: ...                                                                                       │
   │     def visit_cast(self, node: CastNode) -> substrait.Cast: ...                                                                                              │
   │     def visit_singular_or_list(self, node: SingularOrListNode) -> substrait.SingularOrList: ...                                                              │
   │                                                                                                                                                              │
   │ 7.2 Import Factory                                                                                                                                           │
   │                                                                                                                                                              │
   │ File: core/substrait/substrait_import_factory.py                                                                                                             │
   │                                                                                                                                                              │
   │ class SubstraitImportFactory:                                                                                                                                │
   │     @classmethod                                                                                                                                             │
   │     def from_expression(cls, expr: substrait.Expression, schema: Schema) -> ExpressionNode: ...                                                              │
   │                                                                                                                                                              │
   │ 7.3 Connect to Node Methods                                                                                                                                  │
   │                                                                                                                                                              │
   │ Update base node to call visitors:                                                                                                                           │
   │ def to_substrait(self) -> substrait.Expression:                                                                                                              │
   │     visitor = SubstraitExportVisitor()                                                                                                                       │
   │     return visitor.visit(self)                                                                                                                               │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Work Sequence (Recommended Order)                                                                                                                            │
   │                                                                                                                                                              │
   │ Batch 1: Foundation Fixes (1-2 days)                                                                                                                         │
   │                                                                                                                                                              │
   │ 1. Fix SingularOrListNode (Phase 1.1)                                                                                                                        │
   │ 2. Fix ConditionalNode import (Phase 1.2)                                                                                                                    │
   │                                                                                                                                                              │
   │ Batch 2: Backend Reorganization (2-3 days)                                                                                                                   │
   │                                                                                                                                                              │
   │ 3. Rename/split modules (Phase 2)                                                                                                                            │
   │ 4. Update imports throughout codebase                                                                                                                        │
   │                                                                                                                                                              │
   │ Batch 3: Method Migration (3-5 days)                                                                                                                         │
   │                                                                                                                                                              │
   │ 5. Port arithmetic methods from deprecated (Phase 3.1)                                                                                                       │
   │ 6. Port string methods (Phase 3.2)                                                                                                                           │
   │ 7. Add temporal extract() wrapper (Phase 3.3)                                                                                                                │
   │ 8. Add comparison aliases (Phase 3.4)                                                                                                                        │
   │                                                                                                                                                              │
   │ Batch 4: New Functions (3-4 days)                                                                                                                            │
   │                                                                                                                                                              │
   │ 9. Implement rounding (Phase 6.1)                                                                                                                            │
   │ 10. Implement logarithmic (Phase 6.2)                                                                                                                        │
   │ 11. Implement set operations (Phase 6.3)                                                                                                                     │
   │                                                                                                                                                              │
   │ Batch 5: API Exposure (2-3 days)                                                                                                                             │
   │                                                                                                                                                              │
   │ 12. Complete empty namespaces (Phase 5.1)                                                                                                                    │
   │ 13. Extend partial namespaces (Phase 5.2)                                                                                                                    │
   │                                                                                                                                                              │
   │ Batch 6: Protocol Completion (2-3 days)                                                                                                                      │
   │                                                                                                                                                              │
   │ 14. Complete all protocol stubs (Phase 4)                                                                                                                    │
   │                                                                                                                                                              │
   │ Batch 7: Advanced Features (5-7 days)                                                                                                                        │
   │                                                                                                                                                              │
   │ 15. Implement AggregateNode (Phase 6.4)                                                                                                                      │
   │ 16. Implement Substrait serialization (Phase 7)                                                                                                              │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Key File Paths                                                                                                                                               │
   │                                                                                                                                                              │
   │ mountainash-expressions Repository                                                                                                                           │
   │                                                                                                                                                              │
   │ /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/                                                                                  │
   │                                                                                                                                                              │
   │ Core Nodes:                                                                                                                                                  │
   │ ├── src/mountainash_expressions/core/expression_nodes/                                                                                                       │
   │ │   ├── exn_base.py                                                                                                                                          │
   │ │   ├── exn_literal.py                                                                                                                                       │
   │ │   ├── exn_field_reference.py                                                                                                                               │
   │ │   ├── exn_scalar_function.py                                                                                                                               │
   │ │   ├── exn_ifthen.py                                                                                                                                        │
   │ │   ├── exn_cast.py                                                                                                                                          │
   │ │   └── exn_singular_or_list.py  ← CREATE THIS                                                                                                               │
   │                                                                                                                                                              │
   │ Backend Systems:                                                                                                                                             │
   │ ├── src/mountainash_expressions/backends/expression_systems/                                                                                                 │
   │ │   ├── polars/  (14 modules)                                                                                                                                │
   │ │   ├── narwhals/  (14 modules)                                                                                                                              │
   │ │   └── ibis/  (14 modules)                                                                                                                                  │
   │                                                                                                                                                              │
   │ Protocols:                                                                                                                                                   │
   │ ├── src/mountainash_expressions/core/expression_protocols/substrait/                                                                                         │
   │ │   ├── prtcl_scalar_arithmetic.py                                                                                                                           │
   │ │   ├── prtcl_scalar_boolean.py                                                                                                                              │
   │ │   ├── prtcl_scalar_comparison.py                                                                                                                           │
   │ │   ├── prtcl_scalar_string.py                                                                                                                               │
   │ │   ├── prtcl_scalar_datetime.py                                                                                                                             │
   │ │   ├── prtcl_scalar_rounding.py  ← COMPLETE                                                                                                                 │
   │ │   ├── prtcl_scalar_logarithmic.py  ← COMPLETE                                                                                                              │
   │ │   └── prtcl_scalar_set.py  ← COMPLETE                                                                                                                      │
   │                                                                                                                                                              │
   │ API Namespaces:                                                                                                                                              │
   │ ├── src/mountainash_expressions/expression_api/api_namespaces/                                                                                               │
   │ │   ├── arithmetic.py  ← COMPLETE (empty)                                                                                                                    │
   │ │   ├── cast.py  ← COMPLETE (empty)                                                                                                                          │
   │ │   ├── conditional.py  ← COMPLETE (empty)                                                                                                                   │
   │ │   └── ...                                                                                                                                                  │
   │                                                                                                                                                              │
   │ Deprecated (Reference Sources):                                                                                                                              │
   │ └── _deprecated/                                                                                                                                             │
   │     ├── 202510/  (older snapshot)                                                                                                                            │
   │     └── 202511/  (most recent)                                                                                                                               │
   │         ├── expression_nodes/                                                                                                                                │
   │         ├── expression_builders/                                                                                                                             │
   │         └── expression_visitors/                                                                                                                             │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Total Effort Estimate                                                                                                                                        │
   │                                                                                                                                                              │
   │ | Batch | Description            | Days       |                                                                                                              │
   │ |-------|------------------------|------------|                                                                                                              │
   │ | 1     | Foundation Fixes       | 1-2        |                                                                                                              │
   │ | 2     | Backend Reorganization | 2-3        |                                                                                                              │
   │ | 3     | Method Migration       | 3-5        |                                                                                                              │
   │ | 4     | New Functions          | 3-4        |                                                                                                              │
   │ | 5     | API Exposure           | 2-3        |                                                                                                              │
   │ | 6     | Protocol Completion    | 2-3        |                                                                                                              │
   │ | 7     | Advanced Features      | 5-7        |                                                                                                              │
   │ | Total |                        | 18-27 days |                                                                                                              │
   │                                                                                                                                                              │
   │ ---                                                                                                                                                          │
   │ Appendix: Current vs. Target Architecture                                                                                                                    │
   │                                                                                                                                                              │
   │ Expression Node Mapping (Substrait Aligned)                                                                                                                  │
   │                                                                                                                                                              │
   │ LiteralNode         ⟷ substrait.Literal                                                                                                                      │
   │ FieldReferenceNode  ⟷ substrait.FieldReference                                                                                                               │
   │ ScalarFunctionNode  ⟷ substrait.ScalarFunction                                                                                                               │
   │ IfThenNode          ⟷ substrait.IfThen                                                                                                                       │
   │ CastNode            ⟷ substrait.Cast                                                                                                                         │
   │ SingularOrListNode  ⟷ substrait.SingularOrList                                                                                                               │
   │ AggregateNode       ⟷ substrait.AggregateFunction (NEW)                                                                                                      │
   │ WindowNode          ⟷ substrait.WindowFunction (FUTURE)                                                                                                      │
   │                                                                                                                                                              │
   │ Function Enums (Current)                                                                                                                                     │
   │                                                                                                                                                              │
   │ SUBSTRAIT_COMPARISON:  12 functions                                                                                                                          │
   │ SUBSTRAIT_BOOLEAN:      6 functions                                                                                                                          │
   │ SUBSTRAIT_ARITHMETIC:  12 functions                                                                                                                          │
   │ SUBSTRAIT_STRING:      17 functions                                                                                                                          │
   │ SUBSTRAIT_DATETIME:    25 functions                                                                                                                          │
   │ MOUNTAINASH_TERNARY:   21 functions (extension)                                                                                                              │
   │ MOUNTAINASH_*:          8 custom functions                                                                                                                   │
   │ ─────────────────────────────────────                                                                                                                        │
   │ TOTAL:                101 functions defined                                                                                                                  │
   │                                                                                                                                                              │
   │ Coverage Gap Summary                                                                                                                                         │
   │                                                                                                                                                              │
   │ ┌─────────────────────────────────────────────────────────────┐                                                                                              │
   │ │ LAYER          │ DECLARED │ IMPLEMENTED │ GAP              │                                                                                               │
   │ ├─────────────────────────────────────────────────────────────┤                                                                                              │
   │ │ Function Enums │   105    │    105      │ 0% (all defined) │                                                                                               │
   │ │ Protocols      │   153    │    ~40      │ 74% stubs        │                                                                                               │
   │ │ Public API     │   105    │     40      │ 62% missing      │                                                                                               │
   │ │ Backends       │   105    │    101      │ 4% missing       │
