  cat << 'EOF'

   ================================================================================
   MOUNTAINASH EXPRESSIONS - COMPLETE INVENTORY FOR SUBSTRAIT REFACTORING
   ================================================================================

   Last Updated: 2025-11-29
   Codebase: /home/nathanielramm/git/mountainash/mountainash-expressions
   Branch: feature/claude_expansion
   Total Implementation: ~21,000+ lines of code

   ================================================================================
   1. EXPRESSION NODE TYPES (1,468 lines total)
   ================================================================================

   Location: src/mountainash_expressions/core/expression_nodes/

   NODE CATEGORIES & COUNTS:
   - Core: 2 node types (ColumnExpressionNode, LiteralExpressionNode)
   - Boolean: 8 node types
   - Arithmetic: 2 node types
   - String: 6 node types
   - Temporal: 6 node types
   - Null: 4 node types
   - Type: 1 node type
   - Name: 4 node types
   - Horizontal: 1 node type
   - Native: 1 node type
   - Conditional: 1 node type
   - Ternary: 6 node types

   TOTAL NODE CLASSES: 42

   KEY NODE HIERARCHY:
   ExpressionNode (Pydantic BaseModel, ABC)
     ├── BaseCoreExpressionNode
     │   ├── ColumnExpressionNode (fields: column)
     │   └── LiteralExpressionNode (fields: value)
     ├── BooleanExpressionNode
     │   ├── BooleanUnaryExpressionNode (operand)
     │   ├── BooleanIterableExpressionNode (operands)
     │   ├── BooleanComparisonExpressionNode (left, right)
     │   ├── BooleanBetweenExpressionNode (left, right, closed)
     │   ├── BooleanIsCloseExpressionNode (left, right, precision)
     │   ├── BooleanCollectionExpressionNode (operand, element, container)
     │   └── BooleanConstantExpressionNode
     ├── BaseArithmeticExpressionNode
     │   ├── ArithmeticExpressionNode (left, right)
     │   └── ArithmeticIterableExpressionNode (operands)
     ├── BaseStringExpressionNode
     │   ├── StringExpressionNode (operand) - unary
     │   ├── StringPatternNode (operand, pattern) - binary
     │   ├── StringReplaceNode (operand, pattern, replacement)
     │   ├── StringSliceNode (operand, offset, length)
     │   └── StringConcatNode (operands) - n-ary
     ├── BaseTemporalExpressionNode
     │   ├── TemporalExtractExpressionNode (operand)
     │   ├── TemporalDiffExpressionNode (left, right)
     │   ├── TemporalAdditionExpressionNode (operand, delta)
     │   ├── TemporalTruncateExpressionNode (operand, unit)
     │   ├── TemporalOffsetExpressionNode (operand, offset)
     │   └── TemporalSnapshotExpressionNode
     ├── BaseNullExpressionNode
     │   ├── NullExpressionNode (operand, value)
     │   ├── NullConditionalExpressionNode (operand, condition)
     │   ├── NullConstantExpressionNode
     │   └── NullLogicalExpressionNode (operand)
     ├── BaseTypeExpressionNode
     │   └── TypeExpressionNode (operand, type)
     ├── BaseNameExpressionNode
     │   ├── NameExpressionNode (operand)
     │   ├── NameAliasExpressionNode (operand, name)
     │   ├── NamePrefixExpressionNode (operand, prefix)
     │   └── NameSuffixExpressionNode (operand, suffix)
     ├── BaseHorizontalExpressionNode
     │   └── HorizontalExpressionNode (operands)
     ├── NativeExpressionNode (native_expr)
     ├── BaseConditionalExpressionNode
     │   └── ConditionalExpressionNode (condition, consequence, alternative)
     └── TernaryExpressionNode (return -1/0/1)
         ├── TernaryColumnExpressionNode (column, unknown_values)
         ├── TernaryComparisonExpressionNode (left, right)
         ├── TernaryIterableExpressionNode (operands)
         ├── TernaryUnaryExpressionNode (operand)
         ├── TernaryConstantExpressionNode
         └── TernaryCollectionExpressionNode (operand, element, container)

   FILE BREAKDOWN:
   - base_expression_node.py: 39 lines
   - core_expression_nodes.py: 62 lines
   - boolean_expression_nodes.py: 157 lines
   - arithmetic_expression_nodes.py: 86 lines
   - string_expression_nodes.py: 173 lines
   - temporal_expression_nodes.py: 110 lines
   - null_expression_nodes.py: 86 lines
   - type_expression_nodes.py: 41 lines
   - name_expression_nodes.py: 74 lines
   - horizontal_expression_nodes.py: 51 lines
   - native_expression_nodes.py: 41 lines
   - conditional_expression_nodes.py: 62 lines
   - ternary_expression_nodes.py: 207 lines
   - __init__.py: 160 lines
   - types.py: 111 lines

   ================================================================================
   2. OPERATOR ENUMS (1,551 lines total)
   ================================================================================

   Location: src/mountainash_expressions/core/protocols/

   ENUM_CORE_OPERATORS (2 members)
   - COL, LIT

   ENUM_BOOLEAN_OPERATORS (21 members)
   - Comparison: EQ, NE, GT, LT, GE, LE, IS_CLOSE, BETWEEN
   - Collection: IS_IN, IS_NOT_IN
   - Constants: ALWAYS_TRUE, ALWAYS_FALSE
   - Logical: AND, OR, XOR, XOR_PARITY
   - Unary: IS_TRUE, IS_FALSE, NOT

   ENUM_ARITHMETIC_OPERATORS (7 members)
   - Ordered: SUBTRACT, DIVIDE, MODULO, POWER, FLOOR_DIVIDE
   - Commutative: ADD, MULTIPLY

   ENUM_STRING_OPERATORS (18 members)
   - Modifying: STR_UPPER, STR_LOWER, STR_TRIM, STR_LTRIM, STR_RTRIM, STR_SUBSTRING, STR_LENGTH, STR_REPLACE
   - Logical: STR_CONTAINS, STR_STARTS_WITH, STR_ENDS_WITH
   - Iterable: STR_CONCAT
   - Pattern: PAT_REGEX_REPLACE, PAT_LIKE, PAT_REGEX_MATCH, PAT_REGEX_CONTAINS

   ENUM_TEMPORAL_OPERATORS (26 members)
   - Extraction: DT_EXTRACT_YEAR, DT_EXTRACT_MONTH, DT_EXTRACT_DAY, DT_EXTRACT_HOUR,
                DT_EXTRACT_MINUTE, DT_EXTRACT_SECOND, DT_EXTRACT_WEEKDAY, DT_EXTRACT_WEEK,
                DT_EXTRACT_QUARTER
   - Difference: DT_DIFF_YEARS, DT_DIFF_MONTHS, DT_DIFF_DAYS, DT_DIFF_HOURS,
                DT_DIFF_MINUTES, DT_DIFF_SECONDS, DT_DIFF_MILLISECONDS
   - Addition: DT_ADD_DAYS, DT_ADD_HOURS, DT_ADD_MINUTES, DT_ADD_SECONDS,
              DT_ADD_MONTHS, DT_ADD_YEARS
   - Truncation: DT_TRUNCATE
   - Flexible: DT_OFFSET_BY, DT_NOW

   ENUM_HORIZONTAL_OPERATORS (3 members)
   - COALESCE, GREATEST, LEAST

   ENUM_NULL_OPERATORS (4 members)
   - FILL_NULL, IS_NULL, IS_NOT_NULL, NULL_VALUE

   ENUM_TYPE_OPERATORS (1 member)
   - CAST

   ENUM_NAME_OPERATORS (3 members)
   - ALIAS, PREFIX, SUFFIX

   ENUM_NATIVE_OPERATORS (1 member)
   - NATIVE

   ENUM_CONDITIONAL_OPERATORS (1 member)
   - WHEN_THEN_OTHERWISE

   ENUM_TERNARY_OPERATORS (29 members)
   - Comparison: T_EQ, T_NE, T_GT, T_LT, T_GE, T_LE, T_IS_IN, T_IS_NOT_IN
   - Logical: T_AND, T_OR, T_NOT, T_XOR, T_XOR_PARITY
   - Booleanizers: IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN, MAYBE_TRUE, MAYBE_FALSE
   - Conversion: TO_TERNARY
   - Constants: ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN
   - Terminal Operators (set): IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN, MAYBE_TRUE, MAYBE_FALSE

   TOTAL OPERATORS: 116+

   FILE BREAKDOWN:
   - core_protocols.py: 47 lines
   - boolean_protocols.py: 153 lines
   - arithmetic_protocols.py: 111 lines
   - string_protocols.py: 171 lines
   - temporal_protocols.py: 210 lines
   - horizontal_protocols.py: 58 lines
   - null_protocols.py: 65 lines
   - type_protocols.py: 32 lines
   - name_protocols.py: 48 lines
   - native_protocols.py: 41 lines
   - conditional_protocols.py: 61 lines
   - ternary_protocols.py: 476 lines
   - __init__.py: 78 lines

   PROTOCOL PATTERN (typical enum):
   3 protocols per enum category:
   1. {Category}VisitorProtocol - Visitor methods for nodes
   2. {Category}ExpressionProtocol - Backend primitive operations
   3. {Category}BuilderProtocol - Fluent user-facing API

   ================================================================================
   3. EXPRESSION VISITORS (2,265 lines total)
   ================================================================================

   Location: src/mountainash_expressions/core/expression_visitors/

   VISITOR CLASSES (11 category visitors):

   1. ExpressionVisitor (43 lines)
      - Abstract base class
      - Constructor: __init__(expression_system)
      - Helper: _get_expr_op(expr_ops, node)
      - Abstract: visit_expression_node(node)

   2. CoreExpressionVisitor (58 lines)
      - Methods: visit_expression_node, col, lit

   3. BooleanExpressionVisitor (286 lines)
      - 21 methods via _boolean_ops dispatch
      - Handles 8 node types

   4. ArithmeticExpressionVisitor (130 lines)
      - 7 methods via _arithmetic_ops dispatch
      - Handles 2 node types

   5. StringExpressionVisitor (163 lines)
      - 18+ methods for string operations
      - Handles 5 node types

   6. TemporalExpressionVisitor (228 lines)
      - 26+ methods for temporal operations
      - Handles 6 node types

   7. NullExpressionVisitor (83 lines)
      - 4 methods for null operations
      - Handles 4 node types

   8. TypeExpressionVisitor (48 lines)
      - 1 method: cast()

   9. NameExpressionVisitor (83 lines)
      - 3 methods: alias, prefix, suffix

   10. HorizontalExpressionVisitor (77 lines)
       - 3 methods: coalesce, greatest, least

   11. NativeExpressionVisitor (51 lines)
       - 1 method: native()

   12. ConditionalExpressionVisitor (62 lines)
       - 1 method: when_then_otherwise()

   13. TernaryExpressionVisitor (374 lines)
       - 29 methods via _ternary_ops dispatch
       - Handles 6 node types

   VISITOR FACTORY (visitor_factory.py: 526 lines)
   - Central dispatch mechanism
   - Registries:
     * _visitors_registry: Dict[backend, Dict[logic_type, visitor_class]]
     * _expression_systems_registry: Dict[backend, expression_system_class]
   - Key methods:
     * register(backend, logic_type, visitor_class)
     * register_expression_system(backend, system_class)
     * get_visitor_for_node(node, expression_system, logic_type)
     * _identify_backend(dataframe_or_backend)
   - Dispatch: 48 isinstance checks → 13 visitor classes

   VISITOR FACTORY DISPATCH (48 node type checks):

   Boolean nodes (7 types):
     BooleanComparisonExpressionNode → BooleanExpressionVisitor
     BooleanIterableExpressionNode → BooleanExpressionVisitor
     BooleanCollectionExpressionNode → BooleanExpressionVisitor
     BooleanUnaryExpressionNode → BooleanExpressionVisitor
     BooleanConstantExpressionNode → BooleanExpressionVisitor
     BooleanIsCloseExpressionNode → BooleanExpressionVisitor
     BooleanBetweenExpressionNode → BooleanExpressionVisitor

   Arithmetic nodes (2 types):
     ArithmeticExpressionNode → ArithmeticExpressionVisitor
     ArithmeticIterableExpressionNode → ArithmeticExpressionVisitor

   Core nodes (2 types):
     ColumnExpressionNode → CoreExpressionVisitor
     LiteralExpressionNode → CoreExpressionVisitor

   String nodes (5 types):
     StringExpressionNode → StringExpressionVisitor
     StringPatternNode → StringExpressionVisitor
     StringReplaceNode → StringExpressionVisitor
     StringSliceNode → StringExpressionVisitor
     StringConcatNode → StringExpressionVisitor

   Temporal nodes (6 types):
     TemporalExtractExpressionNode → TemporalExpressionVisitor
     TemporalDiffExpressionNode → TemporalExpressionVisitor
     TemporalAdditionExpressionNode → TemporalExpressionVisitor
     TemporalTruncateExpressionNode → TemporalExpressionVisitor
     TemporalOffsetExpressionNode → TemporalExpressionVisitor
     TemporalSnapshotExpressionNode → TemporalExpressionVisitor

   Null nodes (4 types):
     NullExpressionNode → NullExpressionVisitor
     NullConstantExpressionNode → NullExpressionVisitor
     NullConditionalExpressionNode → NullExpressionVisitor
     NullLogicalExpressionNode → NullExpressionVisitor

   Type nodes (1 type):
     TypeExpressionNode → TypeExpressionVisitor

   Name nodes (4 types):
     NameAliasExpressionNode → NameExpressionVisitor
     NamePrefixExpressionNode → NameExpressionVisitor
     NameSuffixExpressionNode → NameExpressionVisitor
     NameExpressionNode → NameExpressionVisitor

   Horizontal nodes (1 type):
     HorizontalExpressionNode → HorizontalExpressionVisitor

   Native nodes (1 type):
     NativeExpressionNode → NativeExpressionVisitor

   Conditional nodes (1 type):
     ConditionalExpressionNode → ConditionalExpressionVisitor

   Ternary nodes (6 types):
     TernaryComparisonExpressionNode → TernaryExpressionVisitor
     TernaryIterableExpressionNode → TernaryExpressionVisitor
     TernaryUnaryExpressionNode → TernaryExpressionVisitor
     TernaryConstantExpressionNode → TernaryExpressionVisitor
     TernaryCollectionExpressionNode → TernaryExpressionVisitor
     TernaryColumnExpressionNode → TernaryExpressionVisitor

   BACKEND IDENTIFICATION (Priority order):
   1. Narwhals - Check "narwhals" in module_name or _compliant_frame attribute
   2. Ibis - Check "ibis" in module_name
   3. Polars - Check "polars" in module_name
   4. Pandas - Check "pandas" in module_name

   String aliases supported: pl, polars, ir, ibis, nw, narwhals, pd, pandas

   FILE BREAKDOWN:
   - expression_visitor.py: 43 lines
   - visitor_factory.py: 526 lines
   - core_visitor.py: 58 lines
   - boolean_visitor.py: 286 lines
   - arithmetic_visitor.py: 130 lines
   - string_visitor.py: 163 lines
   - temporal_visitor.py: 228 lines
   - null_visitor.py: 83 lines
   - type_visitor.py: 48 lines
   - name_visitor.py: 83 lines
   - horizontal_visitor.py: 77 lines
   - native_visitor.py: 51 lines
   - conditional_visitor.py: 62 lines
   - ternary_visitor.py: 374 lines
   - __init__.py: 44 lines
   - types.py: 9 lines

   ================================================================================
   4. BACKEND EXPRESSION SYSTEMS (4,376 lines total)
   ================================================================================

   Location: src/mountainash_expressions/backends/expression_systems/

   BACKEND COMPOSITION PATTERN:

   {Backend}ExpressionSystem = (
       {Backend}BaseExpressionSystem +
       {Backend}CoreExpressionSystem +
       {Backend}BooleanExpressionSystem +
       {Backend}ArithmeticExpressionSystem +
       {Backend}StringExpressionSystem +
       {Backend}TemporalExpressionSystem +
       {Backend}TypeExpressionSystem +
       {Backend}NullExpressionSystem +
       {Backend}HorizontalExpressionSystem +
       {Backend}NameExpressionSystem +
       {Backend}NativeExpressionSystem +
       {Backend}ConditionalExpressionSystem +
       {Backend}TernaryExpressionSystem
   )

   POLARS BACKEND (1,754 lines)
   Location: polars/

   File breakdown:
   - __init__.py: 63 lines (composition & registration)
   - base.py: 34 lines
   - core.py: 47 lines (col, lit)
   - boolean.py: 315 lines (21 operations)
   - arithmetic.py: 123 lines (7 operations)
   - string.py: 215 lines (18+ operations)
   - temporal.py: 321 lines (26+ operations)
   - null.py: 78 lines (4 operations)
   - type.py: 33 lines (1 operation)
   - name.py: 74 lines (3 operations)
   - horizontal.py: 57 lines (3 operations)
   - native.py: 33 lines (passthrough)
   - conditional.py: 32 lines (1 operation)
   - ternary.py: 329 lines (29 operations)

   Largest implementations:
   - Ternary: 329 lines (complex three-valued logic)
   - Temporal: 321 lines (extract, diff, add, truncate)
   - Boolean: 315 lines (full comparison & logical set)
   - String: 215 lines (pattern matching, text ops)

   IBIS BACKEND (1,300 lines)
   Location: ibis/

   File breakdown:
   - __init__.py: 52 lines
   - base.py: 37 lines
   - core.py: 20 lines (minimal, inherits)
   - boolean.py: 111 lines
   - arithmetic.py: 36 lines
   - string.py: 91 lines
   - temporal.py: 352 lines (most complex - SQL semantics differ)
   - null.py: 31 lines
   - type.py: 13 lines (minimal)
   - name.py: 116 lines
   - horizontal.py: 62 lines
   - native.py: 33 lines
   - conditional.py: 32 lines
   - ternary.py: 314 lines

   Largest implementations:
   - Temporal: 352 lines (SQL datetime complexity)
   - Ternary: 314 lines
   - Name: 116 lines
   - Boolean: 111 lines

   NARWHALS BACKEND (1,322 lines)
   Location: narwhals/

   File breakdown:
   - __init__.py: 52 lines
   - base.py: 37 lines
   - core.py: 45 lines
   - boolean.py: 160 lines
   - arithmetic.py: 66 lines
   - string.py: 123 lines
   - temporal.py: 254 lines
   - null.py: 31 lines
   - type.py: 15 lines
   - name.py: 86 lines
   - horizontal.py: 59 lines
   - native.py: 33 lines
   - conditional.py: 32 lines
   - ternary.py: 329 lines

   Largest implementations:
   - Ternary: 329 lines
   - Temporal: 254 lines
   - Boolean: 160 lines
   - String: 123 lines

   PROTOCOL COVERAGE MATRIX:

   | Protocol | Polars | Ibis  | Narwhals |
   |----------|--------|-------|----------|
   | Core     | 47L    | 20L   | 45L      |
   | Boolean  | 315L   | 111L  | 160L     |
   | Arithmetic | 123L | 36L   | 66L      |
   | String   | 215L   | 91L   | 123L     |
   | Temporal | 321L   | 352L  | 254L     |
   | Null     | 78L    | 31L   | 31L      |
   | Type     | 33L    | 13L   | 15L      |
   | Name     | 74L    | 116L  | 86L      |
   | Horizontal | 57L  | 62L   | 59L      |
   | Native   | 33L    | 33L   | 33L      |
   | Conditional | 32L | 32L   | 32L      |
   | Ternary  | 329L   | 314L  | 329L     |

   All 3 backends implement all 12 protocols.
   Temporal is most complex per-backend (SQL semantics).
   Ternary is largest per-backend (three-valued logic).

   ================================================================================
   5. COMPLETE OPERATOR INVENTORY
   ================================================================================

   TOTAL OPERATORS: 116+

   By Category:
   - Core: 2 (col, lit)
   - Boolean: 21 (comparison, logical, constants)
   - Arithmetic: 7 (math operations)
   - String: 18+ (text & pattern)
   - Temporal: 26+ (date/time)
   - Null: 4 (null predicates)
   - Type: 1 (casting)
   - Name: 3 (renaming)
   - Horizontal: 3 (coalesce, greatest, least)
   - Native: 1 (passthrough)
   - Conditional: 1 (if-then-else)
   - Ternary: 29 (three-valued logic)

   SUBSTRAIT MAPPING TARGETS:

   Core operators:
   - COL → plan.ReferenceSegment
   - LIT → plan.Literal

   Boolean operators (21):
   - Comparisons (6): EQ, NE, GT, LT, GE, LE
   - Collections (2): IS_IN, IS_NOT_IN
   - Logical (4): AND, OR, XOR, XOR_PARITY
   - Unary (3): NOT, IS_TRUE, IS_FALSE
   - Constants (2): ALWAYS_TRUE, ALWAYS_FALSE
   - Advanced (2): IS_CLOSE, BETWEEN
   - Special (1): IS_CLOSE needs precision param

   Arithmetic operators (7):
   - Binary (5): ADD, SUBTRACT, MULTIPLY, DIVIDE, MODULO
   - Advanced (2): POWER, FLOOR_DIVIDE

   String operators (18):
   - Unary (6): UPPER, LOWER, TRIM, LTRIM, RTRIM, LENGTH
   - Binary (9): SUBSTRING, STARTSWITH, ENDSWITH, CONTAINS, REPLACE, SPLIT, FIND, PAD, ZFILL
   - N-ary (1): CONCAT
   - Pattern (2): REGEX_MATCH, REGEX_REPLACE

   Temporal operators (26):
   - Extract (9): YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEKDAY, WEEK, QUARTER
   - Diff (7): DIFF_YEARS, DIFF_MONTHS, DIFF_DAYS, DIFF_HOURS, DIFF_MINUTES, DIFF_SECONDS, DIFF_MILLISECONDS
   - Add (6): ADD_YEARS, ADD_MONTHS, ADD_DAYS, ADD_HOURS, ADD_MINUTES, ADD_SECONDS
   - Transform (3): TRUNCATE, OFFSET_BY, NOW

   Null operators (4):
   - IS_NULL, IS_NOT_NULL, FILL_NULL, NULL_VALUE

   Type operators (1):
   - CAST

   Name operators (3):
   - ALIAS, PREFIX, SUFFIX

   Horizontal operators (3):
   - COALESCE, GREATEST, LEAST

   Native operator (1):
   - NATIVE (backend-specific passthrough)

   Conditional operator (1):
   - WHEN_THEN_OTHERWISE

   Ternary operators (29):
   - Comparisons (8): T_EQ, T_NE, T_GT, T_LT, T_GE, T_LE, T_IS_IN, T_IS_NOT_IN
   - Logical (5): T_AND, T_OR, T_NOT, T_XOR, T_XOR_PARITY
   - Booleanizers (6): IS_TRUE, IS_FALSE, IS_UNKNOWN, IS_KNOWN, MAYBE_TRUE, MAYBE_FALSE
   - Conversion (1): TO_TERNARY
   - Constants (3): ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN

   ================================================================================
   6. CODE METRICS SUMMARY
   ================================================================================

   Total Codebase: 21,000+ lines

   Breakdown by Component:
   - Expression Nodes: 1,468 lines (7%)
   - Protocols/Enums: 1,551 lines (7%)
   - Visitors: 2,265 lines (11%)
   - Backends: 4,376 lines (21%)
   - Core Total: ~9,660 lines
   - Tests: ~11,000+ lines (52%)

   Expression Complexity:
   - Node Types: 42 classes
   - Operator Enums: 12 enums
   - Total Operators: 116+
   - Visitor Classes: 13 (+ factory)
   - Backend Systems: 3 (Polars, Ibis, Narwhals)
   - Backend Implementations: 36 (12 protocols × 3 backends)

   Average Lines per Component:
   - Node category: ~115 lines
   - Protocol enum: ~130 lines
   - Visitor class: ~175 lines
   - Backend protocol impl: ~120 lines

   Architecture Layers:
   1. User API (BooleanExpressionAPI, entry points)
   2. Namespace/Builder Layer (create ExpressionNodes)
   3. AST/Node Layer (Pydantic-validated tree)
   4. Visitor Layer (dispatch to backends)
   5. Expression System Layer (protocol implementations)
   6. Backend Native Layer (pl.Expr | nw.Expr | ir.Expr)

   ================================================================================
   7. KEY FILES FOR SUBSTRAIT REFACTORING
   ================================================================================

   CRITICAL REFACTORING POINTS:

   1. Expression Node Hierarchy
      File: src/mountainash_expressions/core/expression_nodes/
      Impact: Maps to Substrait Expression types
      Complexity: 42 node classes → Substrait expression classes

   2. Operator Enums
      File: src/mountainash_expressions/core/protocols/*.py
      Impact: Maps to Substrait ScalarFunction IDs
      Complexity: 116+ operators → Substrait function IDs

   3. Visitor Factory Dispatch
      File: src/mountainash_expressions/core/expression_visitors/visitor_factory.py (526L)
      Impact: Central dispatch logic
      Complexity: 48 isinstance checks → Substrait expression handler dispatch

   4. Backend Implementations
      File: src/mountainash_expressions/backends/expression_systems/*/
      Impact: Implement Substrait → backend compilation
      Complexity: 4,376 lines → new Substrait compilation layer

   5. Constants & Enums
      File: src/mountainash_expressions/constants.py
      Impact: Backend types, logic types
      Complexity: CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES, TERNARY_TERMINAL_OPERATORS

   STRATEGIC REFACTORING PATH:

   Phase 1: Node Layer Mapping
   - Map ExpressionNode hierarchy to Substrait Expression types
   - Create Substrait adapter for each node category
   - Maintain backward compatibility with visitors

   Phase 2: Operator Mapping
   - Map 116+ operators to Substrait ScalarFunction IDs
   - Create operator function registry
   - Handle backend-specific semantics (temporal, null, ternary)

   Phase 3: Dispatch Refactoring
   - Replace isinstance dispatch with Substrait expression type checks
   - Implement Substrait plan → visitor dispatch
   - Maintain self-organizing visitor pattern

   Phase 4: Backend Compilation
   - Map Substrait functions to backend-native functions
   - Implement Substrait plan compilation per backend
   - Preserve backend-specific optimizations

   Phase 5: Ternary Logic Bridge
   - Keep ternary logic system (unique to mountainash)
   - Map to Substrait expressions with booleanizer functions
   - Maintain UNKNOWN sentinel handling

   ================================================================================

   EOF
