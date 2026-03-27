---
  Substrait Alignment Refactoring: Complete Scope

  Executive Summary

  Objective: Refactor the node/visitor/protocol architecture to align with Substrait's expression model, enabling native Substrait serialization/deserialization
  while preserving the public API.

  Impact:
  - ~5,300 lines in core/ (nodes, protocols, visitors) - major refactoring
  - ~4,400 lines in backends/ - minimal changes (methods stay, dispatch changes)
  - ~2,800 lines in namespaces/ - no changes (builds nodes, same interface)
  - Public API - unchanged
  - Tests - should pass with minimal updates

  ---
  Current Architecture Inventory

  Expression Nodes (15 files, ~1,241 lines)

  | File                            | Node Classes                                | Purpose                         |
  |---------------------------------|---------------------------------------------|---------------------------------|
  | base_expression_node.py         | ExpressionNode                              | Abstract base                   |
  | core_expression_nodes.py        | ColumnExpressionNode, LiteralExpressionNode | Core primitives                 |
  | boolean_expression_nodes.py     | 8 classes                                   | Comparison, logical, collection |
  | arithmetic_expression_nodes.py  | 2 classes                                   | Binary/iterable arithmetic      |
  | string_expression_nodes.py      | 9+ classes                                  | String operations               |
  | temporal_expression_nodes.py    | 6 classes                                   | Date/time operations            |
  | null_expression_nodes.py        | 4 classes                                   | Null handling                   |
  | horizontal_expression_nodes.py  | 1 class                                     | Coalesce/greatest/least         |
  | name_expression_nodes.py        | 4 classes                                   | Alias/prefix/suffix             |
  | type_expression_nodes.py        | 1 class                                     | Cast                            |
  | native_expression_nodes.py      | 1 class                                     | Passthrough                     |
  | conditional_expression_nodes.py | 1 class                                     | When/then/otherwise             |
  | ternary_expression_nodes.py     | 7 classes                                   | Ternary logic                   |

  Total: ~40+ node classes

  Operator Enums (11 enums, ~150 members)

  | Enum                      | Members
                                                                                        |
  |---------------------------|--------------------------------------------------------------------------------------------------------------------------------------
  --------------------------------------------------------------------------------------|
  | ENUM_CORE_OPERATORS       | COL, LIT
                                                                                        |
  | ENUM_BOOLEAN_OPERATORS    | EQ, NE, GT, LT, GE, LE, IS_CLOSE, BETWEEN, IS_IN, IS_NOT_IN, AND, OR, XOR, XOR_PARITY, NOT, IS_TRUE, IS_FALSE, ALWAYS_TRUE,
  ALWAYS_FALSE                                                                                   |
  | ENUM_ARITHMETIC_OPERATORS | ADD, SUBTRACT, MULTIPLY, DIVIDE, MODULO, POWER, FLOOR_DIVIDE
                                                                                        |
  | ENUM_STRING_OPERATORS     | STR_UPPER, STR_LOWER, STR_TRIM, STR_LTRIM, STR_RTRIM, STR_SUBSTRING, STR_LENGTH, STR_REPLACE, STR_CONTAINS, STR_STARTS_WITH,
  STR_ENDS_WITH, STR_CONCAT, PAT_LIKE, PAT_REGEX_MATCH, PAT_REGEX_CONTAINS, PAT_REGEX_REPLACE   |
  | ENUM_TEMPORAL_OPERATORS   | 26 operators (extract, diff, add, truncate, etc.)
                                                                                        |
  | ENUM_NULL_OPERATORS       | IS_NULL, IS_NOT_NULL, FILL_NULL
                                                                                        |
  | ENUM_HORIZONTAL_OPERATORS | COALESCE, GREATEST, LEAST
                                                                                        |
  | ENUM_NAME_OPERATORS       | ALIAS, PREFIX, SUFFIX
                                                                                        |
  | ENUM_TYPE_OPERATORS       | CAST
                                                                                        |
  | ENUM_NATIVE_OPERATORS     | NATIVE
                                                                                        |
  | ENUM_TERNARY_OPERATORS    | T_EQ, T_NE, T_GT, T_LT, T_GE, T_LE, T_IS_IN, T_IS_NOT_IN, T_AND, T_OR, T_NOT, T_XOR, T_XOR_PARITY, IS_TRUE, IS_FALSE, IS_UNKNOWN,
  IS_KNOWN, MAYBE_TRUE, MAYBE_FALSE, TO_TERNARY, ALWAYS_TRUE, ALWAYS_FALSE, ALWAYS_UNKNOWN |

  Visitors (16 files, ~1,862 lines)

  | Visitor                      | Handles                   |
  |------------------------------|---------------------------|
  | CoreExpressionVisitor        | col, lit                  |
  | BooleanExpressionVisitor     | Comparisons, logical ops  |
  | ArithmeticExpressionVisitor  | Math operations           |
  | StringExpressionVisitor      | String operations         |
  | TemporalExpressionVisitor    | Date/time operations      |
  | NullExpressionVisitor        | Null handling             |
  | HorizontalExpressionVisitor  | Coalesce, greatest, least |
  | NameExpressionVisitor        | Alias, prefix, suffix     |
  | TypeExpressionVisitor        | Cast                      |
  | NativeExpressionVisitor      | Passthrough               |
  | ConditionalExpressionVisitor | When/then/otherwise       |
  | TernaryExpressionVisitor     | Ternary logic             |

  Backend ExpressionSystems (3 backends, ~4,400 lines)

  Each backend has ~12 mixin classes implementing protocol methods. These stay largely unchanged.

  ---
  Target Architecture

  Substrait-Aligned Node Types (6 core types)

  # core/expression_nodes/substrait_nodes.py

  class SubstraitNode(BaseModel, ABC):
      """Base for all Substrait-aligned expression nodes."""

      def to_substrait(self) -> substrait.Expression: ...

      @classmethod
      def from_substrait(cls, expr: substrait.Expression) -> SubstraitNode: ...


  class LiteralNode(SubstraitNode):
      """Constant value."""
      value: Any
      dtype: Optional[str] = None  # Substrait type hint


  class FieldReferenceNode(SubstraitNode):
      """Column reference."""
      field: str  # Column name


  class ScalarFunctionNode(SubstraitNode):
      """Universal function call - ALL operations use this."""
      function: str  # Function identifier (maps to registry)
      arguments: list[SubstraitNode]
      options: dict[str, Any] = {}  # Function-specific options


  class IfThenNode(SubstraitNode):
      """Conditional expression."""
      conditions: list[tuple[SubstraitNode, SubstraitNode]]  # [(cond, result), ...]
      else_clause: SubstraitNode


  class CastNode(SubstraitNode):
      """Type conversion."""
      input: SubstraitNode
      target_type: str
      failure_behavior: Literal["throw", "null"] = "throw"


  class SingularOrListNode(SubstraitNode):
      """Membership test (IN operator)."""
      value: SubstraitNode
      options: list[SubstraitNode]

  Unified Function Registry

  # core/functions/registry.py

  from dataclasses import dataclass
  from enum import Enum

  class SubstraitExtension(str, Enum):
      """Standard Substrait extension URIs."""
      COMPARISON = "https://github.com/substrait-io/substrait/extensions/functions_comparison.yaml"
      BOOLEAN = "https://github.com/substrait-io/substrait/extensions/functions_boolean.yaml"
      ARITHMETIC = "https://github.com/substrait-io/substrait/extensions/functions_arithmetic.yaml"
      STRING = "https://github.com/substrait-io/substrait/extensions/functions_string.yaml"
      DATETIME = "https://github.com/substrait-io/substrait/extensions/functions_datetime.yaml"
      # Mountainash extensions
      MOUNTAINASH = "https://mountainash.io/extensions/functions.yaml"


  @dataclass(frozen=True)
  class FunctionDef:
      """Function definition with Substrait mapping."""
      name: str                    # Internal name (used in code)
      substrait_uri: str           # Substrait extension URI
      substrait_name: str          # Substrait function name
      backend_method: str          # Method name on ExpressionSystem
      category: str                # For organization: "comparison", "boolean", etc.
      is_extension: bool = False   # True for mountainash-specific functions


  class FunctionRegistry:
      """Central registry mapping function names to definitions."""

      _functions: dict[str, FunctionDef] = {}

      @classmethod
      def register(cls, func: FunctionDef) -> None:
          cls._functions[func.name] = func

      @classmethod
      def get(cls, name: str) -> FunctionDef:
          return cls._functions[name]

      @classmethod
      def get_substrait_uri(cls, name: str) -> str:
          return cls._functions[name].substrait_uri

      @classmethod
      def get_backend_method(cls, name: str) -> str:
          return cls._functions[name].backend_method


  # Register all functions
  FUNCTIONS = [
      # Comparison (Substrait standard)
      FunctionDef("eq", SubstraitExtension.COMPARISON, "equal", "eq", "comparison"),
      FunctionDef("ne", SubstraitExtension.COMPARISON, "not_equal", "ne", "comparison"),
      FunctionDef("gt", SubstraitExtension.COMPARISON, "gt", "gt", "comparison"),
      FunctionDef("lt", SubstraitExtension.COMPARISON, "lt", "lt", "comparison"),
      FunctionDef("ge", SubstraitExtension.COMPARISON, "gte", "ge", "comparison"),
      FunctionDef("le", SubstraitExtension.COMPARISON, "lte", "le", "comparison"),
      FunctionDef("is_null", SubstraitExtension.COMPARISON, "is_null", "is_null", "comparison"),
      FunctionDef("coalesce", SubstraitExtension.COMPARISON, "coalesce", "coalesce", "comparison"),

      # Boolean (Substrait standard)
      FunctionDef("and", SubstraitExtension.BOOLEAN, "and", "and_", "boolean"),
      FunctionDef("or", SubstraitExtension.BOOLEAN, "or", "or_", "boolean"),
      FunctionDef("not", SubstraitExtension.BOOLEAN, "not", "not_", "boolean"),
      FunctionDef("xor", SubstraitExtension.BOOLEAN, "xor", "xor_", "boolean"),

      # Arithmetic (Substrait standard)
      FunctionDef("add", SubstraitExtension.ARITHMETIC, "add", "add", "arithmetic"),
      FunctionDef("subtract", SubstraitExtension.ARITHMETIC, "subtract", "subtract", "arithmetic"),
      FunctionDef("multiply", SubstraitExtension.ARITHMETIC, "multiply", "multiply", "arithmetic"),
      FunctionDef("divide", SubstraitExtension.ARITHMETIC, "divide", "divide", "arithmetic"),
      FunctionDef("modulo", SubstraitExtension.ARITHMETIC, "modulus", "modulo", "arithmetic"),
      FunctionDef("power", SubstraitExtension.ARITHMETIC, "power", "power", "arithmetic"),

      # String (Substrait standard)
      FunctionDef("upper", SubstraitExtension.STRING, "upper", "str_upper", "string"),
      FunctionDef("lower", SubstraitExtension.STRING, "lower", "str_lower", "string"),
      FunctionDef("concat", SubstraitExtension.STRING, "concat", "str_concat", "string"),
      FunctionDef("substring", SubstraitExtension.STRING, "substring", "str_substring", "string"),
      FunctionDef("trim", SubstraitExtension.STRING, "trim", "str_trim", "string"),
      FunctionDef("contains", SubstraitExtension.STRING, "contains", "str_contains", "string"),
      FunctionDef("starts_with", SubstraitExtension.STRING, "starts_with", "str_starts_with", "string"),
      FunctionDef("ends_with", SubstraitExtension.STRING, "ends_with", "str_ends_with", "string"),
      FunctionDef("like", SubstraitExtension.STRING, "like", "pat_like", "string"),
      FunctionDef("regex_match", SubstraitExtension.STRING, "regexp_match_substring", "pat_regex_match", "string"),

      # Temporal (Substrait standard)
      FunctionDef("extract_year", SubstraitExtension.DATETIME, "extract", "dt_year", "temporal"),
      FunctionDef("extract_month", SubstraitExtension.DATETIME, "extract", "dt_month", "temporal"),
      FunctionDef("extract_day", SubstraitExtension.DATETIME, "extract", "dt_day", "temporal"),
      # ... etc

      # Mountainash extensions (non-standard)
      FunctionDef("is_close", SubstraitExtension.MOUNTAINASH, "is_close", "is_close", "comparison", is_extension=True),
      FunctionDef("xor_parity", SubstraitExtension.MOUNTAINASH, "xor_parity", "xor_parity", "boolean", is_extension=True),
      FunctionDef("floor_divide", SubstraitExtension.MOUNTAINASH, "floor_divide", "floor_divide", "arithmetic", is_extension=True),

      # Ternary (Mountainash extension - lowered at namespace layer)
      # These don't need registry entries - they're lowered before reaching here
  ]

  for func in FUNCTIONS:
      FunctionRegistry.register(func)

  Unified Visitor

  # core/expression_visitors/unified_visitor.py

  class UnifiedExpressionVisitor:
      """Single visitor that handles all Substrait-aligned nodes."""

      def __init__(self, expression_system: ExpressionSystem):
          self.backend = expression_system

      def visit(self, node: SubstraitNode) -> SupportedExpressions:
          """Dispatch to appropriate handler based on node type."""
          if isinstance(node, LiteralNode):
              return self.visit_literal(node)
          elif isinstance(node, FieldReferenceNode):
              return self.visit_field_reference(node)
          elif isinstance(node, ScalarFunctionNode):
              return self.visit_scalar_function(node)
          elif isinstance(node, IfThenNode):
              return self.visit_if_then(node)
          elif isinstance(node, CastNode):
              return self.visit_cast(node)
          elif isinstance(node, SingularOrListNode):
              return self.visit_singular_or_list(node)
          else:
              raise ValueError(f"Unknown node type: {type(node)}")

      def visit_literal(self, node: LiteralNode) -> SupportedExpressions:
          return self.backend.lit(node.value)

      def visit_field_reference(self, node: FieldReferenceNode) -> SupportedExpressions:
          return self.backend.col(node.field)

      def visit_scalar_function(self, node: ScalarFunctionNode) -> SupportedExpressions:
          """Universal function dispatch via registry."""
          # Resolve arguments recursively
          args = [self.visit(arg) for arg in node.arguments]

          # Look up backend method from registry
          func_def = FunctionRegistry.get(node.function)
          method = getattr(self.backend, func_def.backend_method)

          # Call with appropriate signature
          return method(*args, **node.options)

      def visit_if_then(self, node: IfThenNode) -> SupportedExpressions:
          """Handle conditional expressions."""
          # Build when/then/otherwise chain
          builder = None
          for condition, result in node.conditions:
              cond_expr = self.visit(condition)
              result_expr = self.visit(result)
              if builder is None:
                  builder = self.backend.when(cond_expr).then(result_expr)
              else:
                  builder = builder.when(cond_expr).then(result_expr)

          else_expr = self.visit(node.else_clause)
          return builder.otherwise(else_expr)

      def visit_cast(self, node: CastNode) -> SupportedExpressions:
          input_expr = self.visit(node.input)
          return self.backend.cast(input_expr, node.target_type)

      def visit_singular_or_list(self, node: SingularOrListNode) -> SupportedExpressions:
          value_expr = self.visit(node.value)
          options = [self.visit(opt) if isinstance(opt, SubstraitNode) else opt
                     for opt in node.options]
          return self.backend.is_in(value_expr, options)

  Namespace Layer: Convenience → Substrait

  The namespace layer builds convenience nodes that get lowered:

  # core/namespaces/ternary.py (example)

  class TernaryNamespace(BaseNamespace):
      """Ternary operations - builds convenience nodes that lower to Substrait."""

      def t_gt(self, other) -> BaseExpressionAPI:
          """Ternary greater-than: returns -1/0/1."""
          other_node = self._to_node(other)

          # Build the lowered Substrait representation directly
          # when(left.is_null() | right.is_null()).then(0)
          # .otherwise(when(left > right).then(1).otherwise(-1))

          left = self._node
          right = other_node

          null_check = ScalarFunctionNode(
              function="or",
              arguments=[
                  ScalarFunctionNode("is_null", [left]),
                  ScalarFunctionNode("is_null", [right]),
              ]
          )

          comparison = ScalarFunctionNode("gt", [left, right])

          node = IfThenNode(
              conditions=[
                  (null_check, LiteralNode(0)),
                  (comparison, LiteralNode(1)),
              ],
              else_clause=LiteralNode(-1)
          )

          return self._build(node)

  ---
  Migration Plan

  Phase 1: Foundation (New Files, No Breaking Changes)

  Create new modules alongside existing:

  core/
  ├── expression_nodes/           # EXISTING - keep for now
  ├── substrait_nodes/            # NEW
  │   ├── __init__.py
  │   ├── base.py                 # SubstraitNode base class
  │   ├── literal.py              # LiteralNode
  │   ├── field_reference.py      # FieldReferenceNode
  │   ├── scalar_function.py      # ScalarFunctionNode
  │   ├── if_then.py              # IfThenNode
  │   ├── cast.py                 # CastNode
  │   └── singular_or_list.py     # SingularOrListNode
  │
  ├── functions/                  # NEW
  │   ├── __init__.py
  │   ├── registry.py             # FunctionRegistry
  │   ├── definitions.py          # All FunctionDef registrations
  │   └── substrait_mapping.py    # Substrait URI constants
  │
  ├── expression_visitors/        # EXISTING - keep for now
  └── unified_visitor/            # NEW
      ├── __init__.py
      └── visitor.py              # UnifiedExpressionVisitor

  Estimated: ~800 new lines

  Phase 2: Adapter Layer

  Create adapters that convert old nodes to new nodes:

  # core/adapters/node_adapter.py

  def to_substrait_node(old_node: ExpressionNode) -> SubstraitNode:
      """Convert legacy node to Substrait-aligned node."""

      if isinstance(old_node, ColumnExpressionNode):
          return FieldReferenceNode(field=old_node.column)

      elif isinstance(old_node, LiteralExpressionNode):
          return LiteralNode(value=old_node.value)

      elif isinstance(old_node, BooleanComparisonExpressionNode):
          op_map = {
              ENUM_BOOLEAN_OPERATORS.EQ: "eq",
              ENUM_BOOLEAN_OPERATORS.NE: "ne",
              ENUM_BOOLEAN_OPERATORS.GT: "gt",
              # ...
          }
          return ScalarFunctionNode(
              function=op_map[old_node.operator],
              arguments=[
                  to_substrait_node(old_node.left),
                  to_substrait_node(old_node.right),
              ]
          )
      # ... etc for all node types

  Estimated: ~400 lines

  Phase 3: Dual-Path Compilation

  Update BooleanExpressionAPI.compile() to support both paths:

  class BooleanExpressionAPI:
      def compile(self, df, *, use_substrait: bool = False):
          if use_substrait:
              # New path: convert to Substrait nodes, use unified visitor
              substrait_node = to_substrait_node(self._node)
              backend = ExpressionVisitorFactory._identify_backend(df)
              system = ExpressionVisitorFactory._expression_systems_registry[backend]()
              visitor = UnifiedExpressionVisitor(system)
              return visitor.visit(substrait_node)
          else:
              # Legacy path: existing visitor dispatch
              return self._compile_legacy(df)

  Estimated: ~50 lines, test both paths work identically

  Phase 4: Namespace Refactoring

  Update namespaces to build Substrait nodes directly:

  # core/namespaces/boolean.py

  class BooleanComparisonNamespace(BaseNamespace):
      def eq(self, other) -> BaseExpressionAPI:
          other_node = self._to_substrait_node(other)
          node = ScalarFunctionNode(
              function="eq",
              arguments=[self._node, other_node]
          )
          return self._build(node)

  This is the bulk of the work: ~2,800 lines of namespace code needs updating

  Phase 5: Remove Legacy

  Once all tests pass with use_substrait=True:

  1. Remove old expression node classes
  2. Remove old visitor classes
  3. Remove old protocol enums
  4. Make Substrait path the default

  Phase 6: Substrait Serialization

  Add serialization methods:

  class BooleanExpressionAPI:
      def to_substrait(self) -> bytes:
          """Serialize to Substrait protobuf."""
          substrait_node = to_substrait_node(self._node)
          return substrait_node.to_substrait().SerializeToString()

      @classmethod
      def from_substrait(cls, data: bytes) -> BooleanExpressionAPI:
          """Deserialize from Substrait protobuf."""
          proto = substrait.Expression()
          proto.ParseFromString(data)
          node = SubstraitNode.from_substrait(proto)
          return cls(node)

  ---
  Effort Estimate

  | Phase | Description              | New Lines | Modified Lines  | Risk   |
  |-------|--------------------------|-----------|-----------------|--------|
  | 1     | Foundation (new modules) | ~800      | 0               | Low    |
  | 2     | Adapter layer            | ~400      | 0               | Low    |
  | 3     | Dual-path compilation    | ~50       | ~100            | Medium |
  | 4     | Namespace refactoring    | ~500      | ~2,800          | Medium |
  | 5     | Remove legacy            | 0         | -3,000 (delete) | Medium |
  | 6     | Substrait serialization  | ~300      | ~50             | Low    |

  Total: ~2,050 new lines, ~3,000 lines deleted, ~3,000 lines modified

  Net result: Simpler codebase with ~2,000 fewer lines

  ---
  Files Changed Summary

  New Files (~10)

  - core/substrait_nodes/*.py (6 files)
  - core/functions/*.py (3 files)
  - core/unified_visitor/*.py (1 file)

  Modified Files (~25)

  - core/namespaces/*.py (11 files) - build Substrait nodes
  - core/expression_api/*.py (2 files) - add serialization
  - core/expression_visitors/visitor_factory.py - unified dispatch
  - tests/**/*.py - minimal changes (public API unchanged)

  Deleted Files (~30)

  - core/expression_nodes/*.py (15 files) - replaced by substrait_nodes
  - core/expression_visitors/*_visitor.py (12 files) - replaced by unified
  - core/protocols/*.py (12 files) - enums no longer needed

  Unchanged Files

  - backends/expression_systems/**/*.py - methods stay, just called differently
  - core/namespaces/entrypoints.py - public API unchanged

  ---
  Risk Mitigation

  1. Phase 3 is the key gate: Both paths must produce identical results before proceeding
  2. Test coverage: Run full test suite at each phase boundary
  3. Rollback: Keep legacy code until Phase 5; can always revert
  4. Backend compatibility: ExpressionSystem methods don't change signatures

  ---
  Success Criteria

  1. All existing tests pass
  2. expr.to_substrait() produces valid Substrait protobuf
  3. BooleanExpressionAPI.from_substrait() round-trips correctly
  4. Codebase is ~2,000 lines smaller
  5. Adding new operations requires only:
    - One FunctionDef in registry
    - One method on ExpressionSystem (already exists for most)
    - One namespace method (already exists)
