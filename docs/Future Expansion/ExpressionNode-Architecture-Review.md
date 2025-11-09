# ExpressionNode Architecture Review

**Date:** 2025-01-09
**Status:** Analysis Complete - Documentation Phase
**Scope:** Current node structure (24 types, 65 operations) + Roadmap expansion (170+ operations)

---

## Executive Summary

The mountainash-expressions ExpressionNode architecture uses a **parameter-driven design** with 24 node types handling 65 operations (~40% coverage). This review examines the current structure, analyzes fitness for the 9-phase expansion roadmap (170+ operations), and provides specific recommendations for structural changes.

### Key Findings

**Current State:**
- ✅ **Well-designed** for current scope (65 operations)
- ✅ **Parameter-driven** approach (one node per category, not per operator)
- ✅ **1:1 visitor mapping** (clean alignment)
- ✅ **Backend category mirroring** (easy implementation)

**Expansion Requirements:**
- ⚠️ **Temporal node requires split** (23 ops → 40+ ops by Phase 4)
- ⚠️ **Window functions need new architecture** (Phase 8, major effort)
- ✅ **Most categories can extend** without structural changes

**Recommendation:** Current architecture is **fit for purpose with targeted enhancements**. Requires 2 critical structural changes: (1) Temporal node split in Phase 4, (2) Window infrastructure in Phase 8.

---

## 1. Current ExpressionNode Structure

### Node Hierarchy (24 Node Types)

```
ExpressionNode (Abstract Base Class)
│
├── Core Nodes (4 types)
│   ├── NativeBackendExpressionNode          # Passthrough for backend-native expressions
│   ├── SourceExpressionNode                 # Column references (col)
│   ├── LiteralExpressionNode                # Literal values (lit)
│   └── CastExpressionNode                   # Type casting
│
├── Logical Nodes (5 types)
│   ├── LogicalConstantExpressionNode        # ALWAYS_TRUE, ALWAYS_FALSE
│   ├── UnaryExpressionNode                  # Base for unary operations
│   ├── LogicalExpressionNode                # AND, OR, XOR (n-ary)
│   ├── ComparisonExpressionNode             # EQ, NE, GT, LT, GE, LE (binary)
│   └── CollectionExpressionNode             # IN, NOT_IN (element vs container)
│
├── Operation Nodes (5 types)
│   ├── ArithmeticExpressionNode             # +, -, *, /, %, **, // (binary)
│   ├── StringExpressionNode                 # UPPER, LOWER, TRIM, SUBSTRING, etc.
│   ├── PatternExpressionNode                # LIKE, REGEX_MATCH, REGEX_CONTAINS, REGEX_REPLACE
│   ├── ConditionalIfElseExpressionNode      # WHEN-THEN-OTHERWISE, COALESCE, FILL_NULL
│   └── TemporalExpressionNode               # YEAR, MONTH, DAY, ADD_DAYS, DIFF_DAYS, etc.
│
└── Boolean-Specific Variants (10 types)
    ├── BooleanExpressionNode                # Base for boolean logic
    ├── BooleanUnaryExpressionNode           # NOT, IS_NULL, IS_NOT_NULL
    ├── BooleanLogicalExpressionNode         # Boolean AND/OR
    ├── BooleanComparisonExpressionNode      # Boolean comparisons
    ├── BooleanConditionalIfElseExpressionNode  # Boolean conditionals
    └── BooleanCollectionExpressionNode      # Boolean IS_IN/IS_NOT_IN
```

**Total:** 24 node types handling 65 operations (ratio: 2.7 operations per node type)

---

## 2. Design Pattern Analysis

### Parameter-Driven vs Operator-Driven

**Current Approach: Parameter-Driven with Operator Dispatch**

```python
# CURRENT (Parameter-driven)
# One node type handles multiple operations via operator parameter
ArithmeticExpressionNode(
    operator=CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD,
    left=col("a"),
    right=col("b")
)

ArithmeticExpressionNode(
    operator=CONST_EXPRESSION_ARITHMETIC_OPERATORS.MULTIPLY,
    left=col("x"),
    right=col("y")
)

# ALTERNATIVE (Operator-driven) - NOT USED
# Separate node type per operation
# AddExpressionNode(left=col("a"), right=col("b"))      # ❌ Not used
# MultiplyExpressionNode(left=col("x"), right=col("y")) # ❌ Not used
```

### Node Parameter Patterns

| Node Type | Operator Enum | Primary Parameters | Variadic | Assessment |
|-----------|---------------|-------------------|----------|------------|
| **Core** |
| SourceExpressionNode | COL | value (column name) | - | ✅ Single purpose |
| LiteralExpressionNode | LIT | value (literal) | - | ✅ Single purpose |
| CastExpressionNode | CAST | value (expr), type (dtype) | kwargs | ✅ Single purpose |
| **Logical** |
| ComparisonExpressionNode | EQ, NE, GT, LT, GE, LE | left, right | kwargs | ✅ Binary comparisons |
| LogicalExpressionNode | AND, OR, XOR | operands (list) | - | ✅ N-ary logic |
| UnaryExpressionNode | NOT, IS_NULL, etc. | operand | - | ✅ Unary operations |
| **Operations** |
| ArithmeticExpressionNode | ADD, SUB, MUL, DIV, MOD, POW, FLOOR_DIV | left, right | - | ✅ Binary arithmetic |
| StringExpressionNode | UPPER, LOWER, TRIM, SUBSTRING, etc. (12 ops) | operand | *args, **kwargs | ✅ Flexible strings |
| PatternExpressionNode | LIKE, REGEX_* (4 ops) | operand, pattern | *args, **kwargs | ✅ Pattern matching |
| ConditionalIfElseExpressionNode | WHEN, COALESCE, FILL_NULL (3 ops) | condition, consequence, alternative, values | - | ✅ Control flow |
| TemporalExpressionNode | YEAR, MONTH, ADD_DAYS, DIFF_DAYS, etc. (23 ops) | operand | *args, **kwargs | ⚠️ Growing large |

---

## 3. Current vs Planned Coverage

### Operations by Category

| Category | Current Ops | Roadmap Ops | Total Target | Coverage | Node Types |
|----------|-------------|-------------|--------------|----------|------------|
| **Core** (col, lit, cast) | 4 | 0 | 4 | 100% | 3 |
| **Boolean/Logical** | 7+ | 0 | 7 | 100%+ | 5 |
| **Comparison** | 6 | +2 (BETWEEN, IDENTICAL_TO) | 8 | 75% | 1 |
| **Arithmetic** | 7 | +1 (NEGATE) | 8 | 87.5% | 1 |
| **Math** | 0 | +26 (basic + advanced) | 26 | 0% | **0 → 1 NEW** |
| **String (Basic)** | 12 | 0 | 12 | 100% | 1 |
| **String (Advanced)** | 0 | +10 (split, find, extract) | 10 | 0% | 1 (extend) |
| **Pattern/Regex** | 4+ | 0 | 4 | 100%+ | 1 |
| **Temporal (Extract)** | 9 | +6 | 15 | 60% | 1 |
| **Temporal (Arithmetic)** | 12 | +2 | 14 | 86% | 1 |
| **Temporal (Construction)** | 0 | +9 | 9 | 0% | **0 → 1 NEW** |
| **Conditional** | 3 | +5 (CASE, NULLIF, etc.) | 8 | 37.5% | 1 (extend) |
| **Array** | 0 | +18 | 18 | 0% | **0 → 1 NEW** |
| **Bitwise** | 0 | +6 | 6 | 0% | **0 → 1 NEW** |
| **Window/Analytic** | 0 | +17 | 17 | 0% | **0 → 1-3 NEW** |
| **ML Metrics** | 0 | +12 | 12 | 0% | **0 → 2-3 NEW** |
| **TOTAL** | **65** | **+105** | **170** | **~38%** | **24 → 32** |

**Expansion:** +8 new node types needed (+33% increase in types, +161% increase in operations)

---

## 4. Node Granularity Assessment

### Optimal Granularity (5-20 operators per node)

**Well-Sized Nodes:**

| Node Type | Operators | Assessment |
|-----------|-----------|------------|
| ArithmeticExpressionNode | 7 | ✅ Excellent (binary operations, consistent structure) |
| StringExpressionNode | 12 (→22 after Phase 3) | ✅ Good (flexible *args handles variability) |
| PatternExpressionNode | 4 | ✅ Good (focused on pattern matching) |
| ConditionalIfElseExpressionNode | 3 (→8 after Phase 2) | ✅ Good (control flow operations) |
| ComparisonExpressionNode | 6 | ✅ Excellent (all binary comparisons) |
| LogicalExpressionNode | 3 | ✅ Good (n-ary logic) |

### Growing Too Large (>25 operators)

**⚠️ TemporalExpressionNode: 23 operators → 40+ after Phase 4**

Current operations (23):
- **Extraction (9):** YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEKDAY, WEEK, QUARTER
- **Arithmetic Add (6):** ADD_DAYS, ADD_MONTHS, ADD_YEARS, ADD_HOURS, ADD_MINUTES, ADD_SECONDS
- **Arithmetic Diff (6):** DIFF_DAYS, DIFF_MONTHS, DIFF_YEARS, DIFF_HOURS, DIFF_MINUTES, DIFF_SECONDS
- **Utility (2):** TRUNCATE, OFFSET_BY

Phase 4 additions (+17):
- **Construction (5):** DATE_FROM_YMD, DATETIME_FROM_COMPONENTS, TIME_FROM_HMS, etc.
- **Parsing (4):** STRING_TO_DATE, STRING_TO_DATETIME, ISO_TO_DATE, etc.
- **Constants (3):** NOW, TODAY, CURRENT_TIME
- **Additional (5):** DAY_OF_YEAR, ISO_YEAR, EPOCH_SECONDS, etc.

**Total after Phase 4: 40 operations in ONE node type** ❌

**Recommendation: SPLIT into 3 node types**

```python
# SPLIT TEMPORAL NODES (Phase 4)

class TemporalExtractExpressionNode(ExpressionNode):
    """Extract temporal components (YEAR, MONTH, DAY, etc.)"""
    # 15 operations total (9 current + 6 new)

class TemporalArithmeticExpressionNode(ExpressionNode):
    """Temporal arithmetic (ADD_*, DIFF_*, OFFSET_BY)"""
    # 14 operations total (12 current + 2 new)

class TemporalConstructionExpressionNode(ExpressionNode):
    """Temporal construction (DATE_FROM_YMD, NOW, STRING_TO_DATE, etc.)"""
    # 12 operations (all new in Phase 4)
```

**Benefits:**
- ✅ Each node type: 12-15 operations (optimal range)
- ✅ Clear semantic grouping (extract vs arithmetic vs construct)
- ✅ Easier visitor implementation (focused concerns)
- ✅ Better alignment with backend APIs

---

## 5. Visitor-to-Node Alignment

### Current Mapping (Excellent 1:1 alignment)

| Visitor Mixin | Visit Method | Node Types | Ratio | Assessment |
|---------------|--------------|------------|-------|------------|
| **Common** |
| CastExpressionVisitor | visit_cast_expression() | CastExpressionNode | 1:1 | ✅ Perfect |
| LiteralExpressionVisitor | visit_literal_expression() | LiteralExpressionNode | 1:1 | ✅ Perfect |
| SourceExpressionVisitor | visit_source_expression() | SourceExpressionNode | 1:1 | ✅ Perfect |
| **Boolean** |
| BooleanComparisonExpressionVisitor | visit_comparison_expression() | ComparisonExpressionNode + Boolean variant | 1:2 | ✅ Acceptable |
| BooleanOperatorsExpressionVisitor | visit_logical_expression() | LogicalExpressionNode + Boolean variant | 1:2 | ✅ Acceptable |
| **Operations** |
| ArithmeticOperatorsExpressionVisitor | visit_arithmetic_expression() | ArithmeticExpressionNode | 1:1 | ✅ Perfect |
| StringOperatorsExpressionVisitor | visit_string_expression() | StringExpressionNode | 1:1 | ✅ Perfect |
| PatternOperatorsExpressionVisitor | visit_pattern_expression() | PatternExpressionNode | 1:1 | ✅ Perfect |
| ConditionalOperatorsExpressionVisitor | visit_conditional_expression() | ConditionalIfElseExpressionNode + Boolean variant | 1:2 | ✅ Acceptable |
| TemporalOperatorsExpressionVisitor | visit_temporal_expression() | TemporalExpressionNode | 1:1 | ✅ Perfect |

**Key Insight:** 1:1 mapping is the norm, 1:2 for Boolean variants is acceptable.

**Recommendation:** Maintain 1:1 mapping when adding new node types.

### Visitor Internal Dispatch Pattern

```python
# Example: ArithmeticOperatorsExpressionVisitor
@property
def arithmetic_ops(self) -> Dict[str, Callable]:
    """Map operators to implementation methods"""
    return {
        CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD:          self._add,
        CONST_EXPRESSION_ARITHMETIC_OPERATORS.SUBTRACT:     self._subtract,
        CONST_EXPRESSION_ARITHMETIC_OPERATORS.MULTIPLY:     self._multiply,
        CONST_EXPRESSION_ARITHMETIC_OPERATORS.DIVIDE:       self._divide,
        CONST_EXPRESSION_ARITHMETIC_OPERATORS.MODULO:       self._modulo,
        CONST_EXPRESSION_ARITHMETIC_OPERATORS.POWER:        self._power,
        CONST_EXPRESSION_ARITHMETIC_OPERATORS.FLOOR_DIVIDE: self._floor_divide,
    }

def visit_arithmetic_expression(self, node: ArithmeticExpressionNode) -> Any:
    """Visit arithmetic node, dispatch to operator-specific method"""
    left = self._process_operand(node.left)
    right = self._process_operand(node.right)

    # Dispatch based on operator
    op_func = self.arithmetic_ops[node.operator]
    return op_func(left, right)
```

**Pattern Benefits:**
- ✅ One visit method per node type (clean interface)
- ✅ Operator dispatch via dictionary (fast, extensible)
- ✅ Abstract methods per operator (backend implements)
- ✅ Visitor complexity is manageable

**Recommendation:** Continue this pattern for new node types.

---

## 6. Backend Operation Alignment

### Backend API Mirroring

ExpressionNodes successfully mirror backend API structure:

| Node Category | Polars API | Ibis API | Alignment |
|---------------|------------|----------|-----------|
| Arithmetic | `pl.Expr` operators (+, -, *, /) | `ir.Expr` operators | ✅ Direct mapping |
| String | `pl.Expr.str.*` namespace | `ir.StringValue.*` methods | ✅ Namespace mirroring |
| Temporal | `pl.Expr.dt.*` namespace | `ir.TimestampValue.*` methods | ✅ Namespace mirroring |
| Pattern | `pl.Expr.str.contains()` | `ir.StringValue.like()` | ✅ Abstracted differences |
| Array (future) | `pl.Expr.list.*` namespace | `ir.ArrayValue.*` methods | ✅ Will mirror |

**Key Success:** Nodes abstract backend differences while maintaining semantic alignment.

**Example:**
```python
# User writes (backend-agnostic)
StringExpressionNode(operator=UPPER, operand=col("name"))

# Polars backend generates
pl.col("name").str.to_uppercase()

# Ibis backend generates
table["name"].upper()

# Different syntax, same semantics ✅
```

---

## 7. Critical Structural Changes Needed

### Change 1: Temporal Node Split (Phase 4) - REQUIRED

**When:** Before Phase 4 implementation (weeks 6-9)

**Why:** Prevents 40+ operator mega-node

**What:**

**Before (Current):**
```
TemporalExpressionNode
├── YEAR, MONTH, DAY, HOUR, MINUTE, SECOND (extraction)
├── ADD_DAYS, ADD_MONTHS, DIFF_DAYS, etc. (arithmetic)
└── TRUNCATE, OFFSET_BY (utility)
# 23 operators
```

**After (Phase 4):**
```
TemporalExtractExpressionNode
├── YEAR, MONTH, DAY, HOUR, MINUTE, SECOND
├── WEEKDAY, WEEK, QUARTER
├── DAY_OF_YEAR, ISO_YEAR (Phase 4)
# 15 operators ✅

TemporalArithmeticExpressionNode
├── ADD_DAYS, ADD_MONTHS, ADD_YEARS
├── ADD_HOURS, ADD_MINUTES, ADD_SECONDS
├── DIFF_DAYS, DIFF_MONTHS, DIFF_YEARS
├── DIFF_HOURS, DIFF_MINUTES, DIFF_SECONDS
├── OFFSET_BY
# 14 operators ✅

TemporalConstructionExpressionNode
├── DATE_FROM_YMD, DATETIME_FROM_COMPONENTS
├── TIME_FROM_HMS
├── STRING_TO_DATE, STRING_TO_DATETIME
├── NOW, TODAY, CURRENT_TIME
├── TRUNCATE, EPOCH_SECONDS
# 12 operators ✅
```

**Impact:**
- ✓ File changes: Create `core/expression_nodes/temporal/` directory
- ✓ Visitor changes: Split `TemporalOperatorsExpressionVisitor` into 3 mixins
- ✓ Backend changes: Implement 3 mixin sets (reuse existing implementations)
- ✓ Test changes: Organize temporal tests by category

**Effort:** 1-2 weeks

**Benefits:**
- Optimal node granularity (12-15 operators each)
- Clear semantic separation
- Easier maintenance
- Better documentation

---

### Change 2: Window Infrastructure (Phase 8) - MAJOR

**When:** Weeks 15-20

**Why:** Window functions require fundamentally different architecture

**What:**

**New Classes:**

```python
class WindowSpecification:
    """Window frame specification (not an ExpressionNode)"""
    def __init__(
        self,
        group_by: Optional[List[str]] = None,
        order_by: Optional[List[Tuple[str, str]]] = None,  # (col, "asc"/"desc")
        frame_type: str = "ROWS",  # "ROWS" or "RANGE"
        frame_start: Union[str, int] = "UNBOUNDED PRECEDING",
        frame_end: Union[str, int] = "CURRENT ROW"
    ):
        self.group_by = group_by
        self.order_by = order_by
        self.frame_type = frame_type
        self.frame_start = frame_start
        self.frame_end = frame_end

class WindowFunctionNode(ExpressionNode):
    """Window/analytic function node"""
    def __init__(
        self,
        operator: str,        # RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD, etc.
        operand: Any,         # Expression to apply window function to
        window: WindowSpecification,
        *args,                # offset for LAG/LEAD, n for NTILE, etc.
        **kwargs
    ):
        self.operator = operator
        self.operand = operand
        self.window = window
        self.args = args
        self.kwargs = kwargs
```

**Operations (17 total):**
- **Ranking (5):** RANK, DENSE_RANK, ROW_NUMBER, PERCENT_RANK, NTILE
- **Offset (4):** LAG, LEAD, FIRST_VALUE, LAST_VALUE
- **Cumulative (8):** CUMSUM, CUMMEAN, CUMMIN, CUMMAX, CUMCOUNT, CUMPROD, RUNNING_SUM, RUNNING_AVG

**ExpressionBuilder API:**

```python
# User writes
expr = (
    col("sales")
    .sum()
    .over(
        group_by=["region"],
        order_by=[("date", "asc")],
        frame=("ROWS", "UNBOUNDED PRECEDING", "CURRENT ROW")
    )
)

# Creates
WindowFunctionNode(
    operator=SUM,
    operand=col("sales"),
    window=WindowSpecification(
        group_by=["region"],
        order_by=[("date", "asc")],
        frame_type="ROWS",
        frame_start="UNBOUNDED PRECEDING",
        frame_end="CURRENT ROW"
    )
)
```

**Impact:**
- ✓ New module: `core/window/` (specification.py, window_nodes.py)
- ✓ New visitor mixin: `WindowFunctionsExpressionVisitor`
- ✓ Backend mixins: Implement window operations (complex SQL/DataFrame translation)
- ✓ ExpressionBuilder: Add `.over()` method
- ✓ Tests: Comprehensive window frame semantics testing

**Effort:** 3-5 weeks (major architectural addition)

**Complexity Drivers:**
- Window frame semantics (ROWS vs RANGE, PRECEDING/FOLLOWING)
- Backend translation (SQL window clauses vs DataFrame window ops)
- Partition/order handling
- Frame boundary edge cases

**Recommendation:** Research Ibis window implementation first, prototype on Polars.

---

### Change 3: Backend Capability System (Before Phase 6) - RECOMMENDED

**When:** Before Phase 6 (weeks 10-12)

**Why:** Array operations not supported by all backends (SQLite, older Ibis)

**What:**

```python
# Backend capability declaration
class PolarsExpressionSystem:
    @property
    def capabilities(self) -> Set[str]:
        return {
            "arithmetic", "string", "temporal", "pattern",
            "conditional", "array", "window", "math"
        }

class IbisSQLiteExpressionSystem:
    @property
    def capabilities(self) -> Set[str]:
        return {
            "arithmetic", "string", "temporal", "pattern",
            "conditional", "math"
            # NO: "array", "window" (not supported in SQLite)
        }

# Visitor factory checks capabilities
def get_visitor_for_backend(df, logic_type):
    backend = identify_backend(df)

    # Check if operation is supported
    if operation_category not in backend.capabilities:
        raise UnsupportedOperationError(
            f"{operation_category} not supported by {backend.backend_type}"
        )

    return create_visitor(backend, logic_type)
```

**Impact:**
- ✓ Add `capabilities` property to all ExpressionSystems
- ✓ Visitor factory checks capabilities before creating visitor
- ✓ Clear error messages for unsupported operations
- ✓ Documentation of backend support matrix

**Effort:** 1 week

**Benefits:**
- Graceful degradation for limited backends
- Clear user feedback
- Prevents runtime errors deep in execution
- Documents backend limitations

---

## 8. New Node Types Required

### Phase 1: Math (Basic) - 2-3 weeks

```python
class MathExpressionNode(ExpressionNode):
    """Mathematical functions"""
    def __init__(self, operator: str, operand: Any, *args, **kwargs):
        self.operator = operator  # ABS, SIGN, SQRT, ROUND, FLOOR, CEIL, etc.
        self.operand = operand
        self.args = args          # e.g., precision for ROUND, base for LOG
        self.kwargs = kwargs
```

**Operators (12):** ABS, SIGN, SQRT, ROUND, FLOOR, CEIL, LN, LOG, LOG10, LOG2, EXP, IS_NAN, IS_INF

**Granularity:** ✅ Good (12 operators)

**Phase 5 Extension:** +14 operators (SIN, COS, TAN, ASIN, ACOS, ATAN, ATAN2, COT, RADIANS, DEGREES, CLIP, PI, E)

**Total after Phase 5:** 26 operators (acceptable, < 30 limit)

---

### Phase 4: Temporal Construction - 3-4 weeks

```python
class TemporalConstructionExpressionNode(ExpressionNode):
    """Temporal construction, parsing, and constants"""
    def __init__(self, operator: str, *args, **kwargs):
        self.operator = operator  # DATE_FROM_YMD, STRING_TO_DATE, NOW, etc.
        self.args = args          # Components (year, month, day, etc.)
        self.kwargs = kwargs      # Format strings, timezones, etc.
```

**Operators (12):**
- Construction: DATE_FROM_YMD, DATETIME_FROM_COMPONENTS, TIME_FROM_HMS
- Parsing: STRING_TO_DATE, STRING_TO_DATETIME, ISO_TO_DATE, PARSE_TIMESTAMP
- Constants: NOW, TODAY, CURRENT_TIME
- Utility: TRUNCATE, EPOCH_SECONDS

**Granularity:** ✅ Good (12 operators)

---

### Phase 6: Arrays - 4-6 weeks

```python
class ArrayExpressionNode(ExpressionNode):
    """Array/list operations"""
    def __init__(self, operator: str, operand: Any, *args, **kwargs):
        self.operator = operator  # ARRAY_LENGTH, ARRAY_INDEX, ARRAY_SLICE, etc.
        self.operand = operand    # Array expression
        self.args = args          # Index, values, etc.
        self.kwargs = kwargs
```

**Operators (18):**
- Access: ARRAY_LENGTH, ARRAY_INDEX, ARRAY_SLICE
- Membership: ARRAY_CONTAINS, ARRAY_DISTINCT
- Transformation: ARRAY_CONCAT, ARRAY_UNION, ARRAY_INTERSECT, ARRAY_FLATTEN, ARRAY_SORT, ARRAY_REMOVE
- Aggregation: ARRAY_SUM, ARRAY_MEAN, ARRAY_MIN, ARRAY_MAX
- Predicates: ARRAY_ANY, ARRAY_ALL
- Construction: ARRAY_CONSTRUCT

**Granularity:** ✅ Good (18 operators)

**Backend Support:** ⚠️ Polars (full), Ibis-Polars (good), Ibis-DuckDB (good), SQLite (poor)

**Requirement:** Backend capability system (Change 3)

---

### Phase 7: Bitwise - 1-2 weeks

```python
class BitwiseExpressionNode(ExpressionNode):
    """Bitwise operations"""
    def __init__(self, operator: str, left: Any, right: Any = None):
        self.operator = operator  # AND, OR, XOR, NOT, LEFT_SHIFT, RIGHT_SHIFT
        self.left = left
        self.right = right        # None for unary NOT
```

**Operators (6):** BITWISE_AND, BITWISE_OR, BITWISE_XOR, BITWISE_NOT, LEFT_SHIFT, RIGHT_SHIFT

**Granularity:** ✅ Good (6 operators, small focused category)

---

### Phase 8: Window Functions - 3-5 weeks

```python
class WindowFunctionNode(ExpressionNode):
    """Window/analytic functions"""
    def __init__(
        self,
        operator: str,
        operand: Any,
        window: WindowSpecification,
        *args,
        **kwargs
    ):
        self.operator = operator
        self.operand = operand
        self.window = window
        self.args = args
        self.kwargs = kwargs
```

**Operators (17):** RANK, DENSE_RANK, ROW_NUMBER, PERCENT_RANK, NTILE, LAG, LEAD, FIRST_VALUE, LAST_VALUE, CUMSUM, CUMMEAN, CUMMIN, CUMMAX, CUMCOUNT, CUMPROD, RUNNING_SUM, RUNNING_AVG

**Granularity:** ✅ Good (17 operators)

**Complexity:** ⚠️ HIGH (requires WindowSpecification infrastructure)

**Potential Split:**
- Option A: Single `WindowFunctionNode` (17 operators)
- Option B: Split into `RankingFunctionNode`, `OffsetFunctionNode`, `CumulativeFunctionNode`

**Recommendation:** Start with single node, split if complexity warrants.

---

### Phase 9: ML Metrics - 4-7 weeks

```python
class ClassificationMetricNode(ExpressionNode):
    """Classification metrics (precision, recall, F1, accuracy)"""
    def __init__(
        self,
        operator: str,
        actual: ExpressionNode,
        prediction: ExpressionNode
    ):
        self.operator = operator  # PRECISION, RECALL, F1_SCORE, ACCURACY
        self.actual = actual
        self.prediction = prediction

class RankingMetricNode(ExpressionNode):
    """Ranking metrics (ROC AUC, Gini, log loss)"""
    def __init__(
        self,
        operator: str,
        actual: ExpressionNode,
        prediction_proba: ExpressionNode
    ):
        self.operator = operator  # ROC_AUC, GINI, LOG_LOSS
        self.actual = actual
        self.prediction_proba = prediction_proba

class CreditRiskMetricNode(ExpressionNode):
    """Credit risk metrics with discretization (WOE, IV, PSI)"""
    def __init__(
        self,
        operator: str,
        actual: ExpressionNode,
        feature: ExpressionNode,
        bins: Union[int, List[float]],
        method: str = "quantile"
    ):
        self.operator = operator  # WOE, INFORMATION_VALUE, PSI, MARGINAL_IV
        self.actual = actual
        self.feature = feature
        self.bins = bins
        self.method = method
```

**Operators:**
- ClassificationMetricNode (4): PRECISION, RECALL, F1_SCORE, ACCURACY
- RankingMetricNode (4): ROC_AUC, GINI, LOG_LOSS, NORMALIZED_GINI
- CreditRiskMetricNode (4): WOE, INFORMATION_VALUE, PSI, MARGINAL_IV

**Total:** 12 operators across 3 node types

**Granularity:** ✅ Excellent (4 operators per specialized node)

**Dependencies:**
- Phase 9A (Classification): No dependencies
- Phase 9B (Ranking): Requires Phase 8 (window functions for ranking)
- Phase 9C (Credit Risk): Custom discretization logic

---

## 9. Node Type Inventory (Current vs Future)

### Current (24 node types, 65 operations)

| Category | Node Types | Operations | Avg Ops/Node |
|----------|------------|------------|--------------|
| Core | 4 | 4 | 1.0 |
| Logical | 5 | 13 | 2.6 |
| Operations | 5 | 48 | 9.6 |
| Boolean Variants | 10 | (same as base) | - |
| **TOTAL** | **24** | **65** | **2.7** |

### Future (32 node types, 170+ operations)

| Category | Node Types | Operations | Avg Ops/Node | New Types |
|----------|------------|------------|--------------|-----------|
| Core | 4 | 4 | 1.0 | - |
| Logical | 5 | 15 | 3.0 | - |
| Arithmetic | 1 | 8 | 8.0 | - |
| Math | 1 | 26 | 26.0 | +1 ✅ |
| String | 1 | 22 | 22.0 | - |
| Pattern | 1 | 4 | 4.0 | - |
| Temporal Extract | 1 | 15 | 15.0 | +1 ✅ |
| Temporal Arithmetic | 1 | 14 | 14.0 | +1 ✅ |
| Temporal Construction | 1 | 12 | 12.0 | +1 ✅ |
| Conditional | 1 | 8 | 8.0 | - |
| Array | 1 | 18 | 18.0 | +1 ✅ |
| Bitwise | 1 | 6 | 6.0 | +1 ✅ |
| Window | 1 | 17 | 17.0 | +1 ✅ |
| Metrics | 3 | 12 | 4.0 | +3 ✅ |
| Boolean Variants | 10+ | (same as base) | - | (+2 variants) |
| **TOTAL** | **32** | **170+** | **5.3** | **+8 core, +2 variants** |

**Key Metrics:**
- Node types: 24 → 32 (+33% increase)
- Operations: 65 → 170+ (+161% increase)
- Efficiency: 2.7 → 5.3 ops/node (better granularity balance)

**Interpretation:** Parameter-driven design scales efficiently. Small increase in node types supports large increase in operations.

---

## 10. Design Principles (Codified)

### Principle 1: Parameter-Driven Categories

**Rule:** One node type per operation category, not per operator.

**Rationale:**
- Reduces node proliferation
- Simplifies visitor interface
- Aligns with backend API structure
- Extensible via operator enum

**Example:**
```python
# ✅ GOOD: Parameter-driven
ArithmeticExpressionNode(operator=ADD, left, right)
ArithmeticExpressionNode(operator=MULTIPLY, left, right)

# ❌ BAD: Operator-driven
AddExpressionNode(left, right)
MultiplyExpressionNode(left, right)
```

---

### Principle 2: Split at 25-30 Operators

**Rule:** If a node type exceeds 25-30 operators, mandatory split.

**Triggers:**
- 25+ operators: Consider split (review semantic groupings)
- 30+ operators: Mandatory split (too large to maintain)

**Strategy:** Split by operational sub-category (extract vs arithmetic vs construction)

**Example:**
```python
# BEFORE (40 operators - TOO LARGE)
TemporalExpressionNode
├── Extract (15)
├── Arithmetic (14)
└── Construction (12)

# AFTER (split into 3)
TemporalExtractExpressionNode (15)     ✅
TemporalArithmeticExpressionNode (14)  ✅
TemporalConstructionExpressionNode (12) ✅
```

---

### Principle 3: Maintain 1:1 Visitor Mapping

**Rule:** One visitor mixin per node category (1:2 for Boolean variants acceptable).

**Alignment:**
```
Node Type <--> Visitor Mixin <--> Backend Mixin Category
```

**Benefits:**
- Clear separation of concerns
- Easy to locate visitor logic
- Mirrors backend structure

**Example:**
```python
# Node
ArithmeticExpressionNode

# Visitor
ArithmeticOperatorsExpressionVisitor
├── visit_arithmetic_expression()  # Handles node
├── _add(), _subtract(), etc.      # Abstract backend ops

# Backend
PolarsArithmeticMixin
├── add(), subtract(), etc.        # Concrete implementations
```

---

### Principle 4: Backend Category Mirroring

**Rule:** Align node categories with backend API structure.

**Mapping:**
```
StringExpressionNode    → pl.Expr.str.*       → StringBackend protocol
TemporalExpressionNode  → pl.Expr.dt.*        → TemporalBackend protocol
ArrayExpressionNode     → pl.Expr.list.*      → ArrayBackend protocol
MathExpressionNode      → Math functions      → MathBackend protocol
```

**Benefits:**
- Easier backend implementation
- Better documentation alignment
- User mental model matches backend

---

### Principle 5: Flexible Parameters

**Rule:** Use *args, **kwargs for variable-signature operations within a category.

**Pattern:**
```python
class StringExpressionNode(ExpressionNode):
    def __init__(self, operator: str, operand: Any, *args, **kwargs):
        self.operator = operator
        self.operand = operand
        self.args = args        # Variable positional args
        self.kwargs = kwargs    # Variable keyword args

# Examples
StringExpressionNode(UPPER, col("name"))  # Unary, no args
StringExpressionNode(SUBSTRING, col("name"), start=0, end=5)  # With kwargs
StringExpressionNode(REPLACE, col("name"), "old", "new")  # With args
```

**Benefits:**
- Single node type handles diverse signatures
- Extensible without parameter bloat
- Backward compatible when adding operations

---

## 11. File Organization (Current vs Proposed)

### Current Structure

```
core/expression_nodes/
├── __init__.py
├── expression_nodes.py              # All base nodes (14 classes, 500+ lines)
└── boolean_expression_nodes.py      # Boolean variants (10 classes, 300+ lines)
```

**Issues:**
- ❌ Single file with 14 heterogeneous classes
- ❌ Will grow to 800+ lines by Phase 9
- ❌ Difficult to navigate

---

### Proposed Structure (After Refactoring)

```
core/expression_nodes/
├── __init__.py                      # Export all node types
│
├── base_nodes.py                    # ExpressionNode (base class)
│
├── core_nodes.py                    # Source, Literal, Cast, Native (4 types)
│
├── logical_nodes.py                 # Constant, Unary, Logical, Comparison, Collection (5 types)
│
├── arithmetic_nodes.py              # Arithmetic, Math (2 types)
│
├── string_nodes.py                  # String, Pattern (2 types)
│
├── temporal/                        # NEW: Temporal node split
│   ├── __init__.py
│   ├── extract_nodes.py            # TemporalExtractExpressionNode
│   ├── arithmetic_nodes.py          # TemporalArithmeticExpressionNode
│   └── construction_nodes.py        # TemporalConstructionExpressionNode
│
├── array_nodes.py                   # NEW: ArrayExpressionNode (Phase 6)
│
├── conditional_nodes.py             # ConditionalIfElseExpressionNode
│
├── bitwise_nodes.py                 # NEW: BitwiseExpressionNode (Phase 7)
│
├── window/                          # NEW: Window infrastructure (Phase 8)
│   ├── __init__.py
│   ├── specification.py            # WindowSpecification class
│   └── window_nodes.py             # WindowFunctionNode
│
├── metrics/                         # NEW: ML metrics (Phase 9)
│   ├── __init__.py
│   ├── classification_nodes.py     # ClassificationMetricNode
│   ├── ranking_nodes.py             # RankingMetricNode
│   └── credit_risk_nodes.py         # CreditRiskMetricNode (optional)
│
└── boolean_expression_nodes.py      # Boolean variants (existing, may extend)
```

**Benefits:**
- ✅ Logical file organization (one file per category or family)
- ✅ Easy to locate nodes
- ✅ Smaller files (100-200 lines each)
- ✅ Clear extension points for new phases

---

## 12. Recommendations Summary

### Immediate Actions (Phase 1-2)

1. **Add MathExpressionNode** (Phase 1)
   - New file: `core/expression_nodes/arithmetic_nodes.py` (or separate `math_nodes.py`)
   - 12 operators initially, extensible to 26 in Phase 5
   - New visitor mixin: `MathOperatorsExpressionVisitor`

2. **Extend ConditionalIfElseExpressionNode** (Phase 2)
   - Add operators: CASE, NULLIF
   - Add parameter pattern for CASE branches
   - Update visitor dispatch logic

3. **Document Node Granularity Policy**
   - Codify 25-30 operator split trigger
   - Document parameter-driven design rationale
   - Add to CLAUDE.md

---

### Short-Term Actions (Phase 3-5)

4. **Extend StringExpressionNode** (Phase 3)
   - Add 10 operators: SPLIT, FIND, PAD_LEFT, PAD_RIGHT, etc.
   - Total: 12 → 22 operators (acceptable)
   - Update visitor and backend mixins

5. **SPLIT TemporalExpressionNode** (Phase 4) - CRITICAL
   - Create `core/expression_nodes/temporal/` directory
   - Split into 3 node types: Extract, Arithmetic, Construction
   - Create 3 corresponding visitor mixins
   - Update all backends with 3 temporal mixin implementations
   - Migrate tests to new structure
   - **Timing:** Before Phase 4 implementation
   - **Effort:** 1-2 weeks

6. **Extend MathExpressionNode** (Phase 5)
   - Add 14 operators: SIN, COS, TAN, trigonometric functions
   - Total: 12 → 26 operators (acceptable, < 30 limit)

---

### Mid-Term Actions (Phase 6-7)

7. **Implement Backend Capability System** (Before Phase 6)
   - Add `capabilities` property to all ExpressionSystems
   - Visitor factory checks capabilities
   - Clear error messages for unsupported operations
   - **Effort:** 1 week

8. **Add ArrayExpressionNode** (Phase 6)
   - New file: `core/expression_nodes/array_nodes.py`
   - 18 operators for array/list operations
   - New visitor mixin: `ArrayOperatorsExpressionVisitor`
   - **Backend support:** Polars (full), Ibis-Polars (good), SQLite (poor)

9. **Add BitwiseExpressionNode** (Phase 7)
   - New file: `core/expression_nodes/bitwise_nodes.py`
   - 6 operators for bitwise operations
   - New visitor mixin: `BitwiseOperatorsExpressionVisitor`

10. **Extend Comparison/Arithmetic Nodes** (Phase 7)
    - ComparisonExpressionNode: +2 operators (BETWEEN, IDENTICAL_TO)
    - ArithmeticExpressionNode: +1 operator (NEGATE)
    - CastExpressionNode: +1 operator (TRY_CAST)

---

### Long-Term Actions (Phase 8-9)

11. **Implement Window Infrastructure** (Phase 8) - MAJOR
    - Create `core/window/` module
    - Implement WindowSpecification class
    - Create WindowFunctionNode (17 operators)
    - New visitor mixin: `WindowFunctionsExpressionVisitor`
    - Add `.over()` method to ExpressionBuilder
    - **Complexity:** HIGH
    - **Effort:** 3-5 weeks
    - **Strategy:** Research Ibis implementation, prototype on Polars

12. **Add Metric Nodes** (Phase 9)
    - Create `core/expression_nodes/metrics/` directory
    - ClassificationMetricNode (4 operators)
    - RankingMetricNode (4 operators, depends on window functions)
    - CreditRiskMetricNode (4 operators, optional)
    - **Effort:** 4-7 weeks (includes discretization logic)

---

### Continuous Actions

13. **Maintain 1:1 Node-Visitor Alignment**
    - Every new node type gets corresponding visitor mixin
    - Visitor mixins mirror node categories
    - Update alignment matrix documentation

14. **Monitor Node Granularity**
    - Review node size when adding operators
    - Split if approaching 25-30 operator threshold
    - Document split rationale

15. **Update Documentation**
    - Keep CLAUDE.md current with node structure
    - Update alignment matrix for new nodes
    - Document backend support for new operations

---

## 13. Risk Assessment

### High-Risk Items

**1. Window Function Architecture Complexity**
- **Risk:** Complex frame semantics, backend variability
- **Impact:** 3-5 week implementation, potential delays
- **Mitigation:**
  - Prototype on Polars first (simpler API)
  - Research Ibis window implementation thoroughly
  - Comprehensive frame specification tests
  - Phase 9B (ranking metrics) depends on this - can't defer

**2. Temporal Node Split Timing**
- **Risk:** Splitting too early (wasted effort) or too late (painful refactor)
- **Decision:** Split in Phase 4 (before adding 17 new operators)
- **Impact:** 1-2 weeks refactoring during Phase 4
- **Mitigation:** Clear migration plan, test-driven refactoring

---

### Medium-Risk Items

**3. Array Backend Compatibility**
- **Risk:** SQLite/older Ibis backends lack array support
- **Impact:** Some backends can't use array operations
- **Mitigation:** Backend capability system (Change 3), clear documentation

**4. Math Expression Node Scope**
- **Risk:** 26 total operators approaches 30 limit
- **Impact:** May need split if further expansion
- **Mitigation:** Monitor growth, split into basic/advanced if exceeds 30

---

### Low-Risk Items

**5. Boolean Hierarchy Maintenance**
- **Risk:** Maintaining parallel Boolean* hierarchy
- **Impact:** Some duplication, manageable complexity
- **Mitigation:** Defer refactoring until ternary logic implemented

**6. Metric Node Specialization**
- **Risk:** ML metrics may not fit expression abstraction cleanly
- **Impact:** Phase 9C (credit risk) may need custom logic
- **Mitigation:** Phase 9C is optional, can defer if problematic

---

## 14. Conclusion

The current ExpressionNode architecture is **well-designed and fit for purpose** for its current scope (65 operations, ~40% coverage). The parameter-driven design with operator dispatch successfully balances:
- ✅ Node type count (24 types for 65 operations)
- ✅ Visitor complexity (manageable operator dispatch)
- ✅ Backend alignment (mirrors API structure)
- ✅ Extensibility (easy to add operations)

**For roadmap expansion (170+ operations, 100% coverage), the architecture requires:**

1. **2 Critical Structural Changes:**
   - Temporal node split (Phase 4) - prevents mega-node
   - Window infrastructure (Phase 8) - enables analytic functions

2. **8 New Node Types:**
   - MathExpressionNode (Phase 1)
   - Temporal split (3 types, Phase 4)
   - ArrayExpressionNode (Phase 6)
   - BitwiseExpressionNode (Phase 7)
   - WindowFunctionNode (Phase 8)
   - Metric nodes (2-3 types, Phase 9)

3. **1 Architectural Enhancement:**
   - Backend capability system (before Phase 6)

**Efficiency Metrics:**
- Node types: 24 → 32 (+33%)
- Operations: 65 → 170+ (+161%)
- **Result:** Small increase in types supports large increase in operations

**Recommendation:** **Approve current architecture** with planned structural enhancements. The parameter-driven design scales efficiently and maintains clean alignment across layers (nodes → visitors → backends → API).

---

**Next Steps:**
1. Review and approve recommendations
2. Prioritize Phase 4 temporal split planning
3. Begin Math node implementation (Phase 1)
4. Research window function architecture (Phase 8 prep)

---

**Document Complete** ✅
