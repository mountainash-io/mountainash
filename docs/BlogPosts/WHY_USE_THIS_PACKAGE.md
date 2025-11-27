# Why Use mountainash-expressions?

## The One-Sentence Pitch

**Write DataFrame expressions once, run them anywhere, store them forever, and know they'll behave identically regardless of backend.**

---

## The Problem Space

### The Illusion of DataFrame Interoperability

Every DataFrame library promises compatibility. The reality:

```python
# "Simple" modulo operation
result = df.filter(col("value") % 3 == 2)
```

| Backend | Result for value=-7 | Why |
|---------|---------------------|-----|
| Python/Polars | 2 | Modulo (sign of divisor) |
| DuckDB | -1 | Remainder (sign of dividend) |
| SQLite | -1 | Remainder (sign of dividend) |
| PostgreSQL | 2 | Modulo |
| MySQL | -1 | Remainder |

**Same expression. Different results. Silent data corruption.**

This isn't a bug—it's a fundamental semantic difference that no API abstraction can hide. Narwhals gives you `col("value") % 3` everywhere, but the *meaning* changes depending on where you run it.

### The Real Problems We Solve

1. **Semantic Divergence** - Backends behave differently for the same operations
2. **Missing Operations** - No library has `last_day_of_month()` that works everywhere
3. **NULL Handling Chaos** - Every backend treats NULL differently in comparisons
4. **Expression Lock-in** - Your business rules are trapped in one library's syntax
5. **No Inspection** - You can't see what a Polars expression does without running it
6. **No Serialization** - You can't save an expression to a database or send it over a network
7. **No Telemetry** - You can't log what transformations were applied to your data

---

## Who Needs This?

### 1. Platform Developers Building Multi-Backend Systems

You're building a data platform that must work with:
- Local development: SQLite or DuckDB
- Production: PostgreSQL or Snowflake
- Analytics: Polars or Spark
- Real-time: Kafka + Flink

**Without mountainash-expressions:**
```python
# You write this THREE times
if backend == "polars":
    result = df.filter(pl.col("age") > 30)
elif backend == "pandas":
    result = df[df["age"] > 30]
elif backend == "ibis":
    result = table.filter(table.age > 30)
```

**With mountainash-expressions:**
```python
# Write once
expr = ma.col("age").gt(30)
result = df.filter(expr.compile(df))  # Works on ANY backend
```

### 2. Package Authors Building DataFrame-Agnostic Libraries

You're writing a library (data validation, feature engineering, ETL framework) that should work regardless of what DataFrame library your users choose.

**The Nightmare:**
- Support Polars? Write Polars code.
- Support Pandas? Write it again.
- Support Ibis? Write it a third time.
- New library emerges? Rewrite everything.

**The Solution:**
```python
# Your library's filtering logic
def apply_quality_filters(df, config):
    expr = (
        ma.col("completeness").ge(config.min_completeness)
        .and_(ma.col("freshness_days").le(config.max_age))
        .and_(ma.col("source").is_in(config.trusted_sources))
    )
    return df.filter(expr.compile(df))

# Works for ALL your users, regardless of their DataFrame choice
```

### 3. Enterprises Facing Platform Migrations

You're migrating from Pandas to Polars. Or from on-prem PostgreSQL to Snowflake. Or from Spark to DuckDB.

**The Horror:**
- Thousands of filtering expressions scattered across your codebase
- Each one needs manual translation
- Subtle behavioral differences cause silent bugs
- Months of work, high risk

**The Alternative:**
```python
# Your expressions are backend-agnostic from day one
business_rules = [
    ma.col("status").eq("active"),
    ma.col("last_login").dt.within_last("30 days"),
    ma.col("subscription_tier").is_in(["pro", "enterprise"]),
]

# Migration = change the DataFrame type, expressions just work
old_result = pandas_df.filter(rule.compile(pandas_df))
new_result = polars_df.filter(rule.compile(polars_df))  # Identical behavior
```

### 4. Teams Needing Auditable Business Rules

Compliance requires you to:
- Document what filters were applied to data
- Prove that rules were applied consistently
- Version control your business logic
- Allow non-developers to modify rules

**Traditional Approach:** Business rules are buried in code. Auditing requires reading Python. Changes require deployments.

**With mountainash-expressions:**
```python
# Rules are DATA, not code
rule = ma.col("transaction_amount").gt(10000).and_(
    ma.col("country").is_in(["US", "CA", "GB"])
)

# Serialize to JSON for storage/audit
rule_json = rule.to_json()
# {"type": "and", "operands": [{"type": "gt", "left": {"type": "col", ...}}]}

# Store in database with metadata
db.execute("""
    INSERT INTO audit_rules (rule_id, rule_json, applied_by, applied_at)
    VALUES (?, ?, ?, ?)
""", [rule_id, rule_json, user_id, datetime.now()])

# Reconstruct and apply
loaded_rule = ma.from_json(rule_json)
filtered_df = df.filter(loaded_rule.compile(df))
```

### 5. Data Scientists Needing Reproducibility

Your notebook works. Six months later, you need to reproduce the exact analysis.

**The Problem:**
- Polars updated, behavior changed
- You switched to a different backend
- The exact filter logic is lost in notebook cell 47

**The Solution:**
```python
# Save your expression alongside your results
analysis_config = {
    "date": "2024-01-15",
    "filter": ma.col("score").ge(0.8).and_(ma.col("category").eq("A")).to_json(),
    "result_hash": hash(result_df),
}

# Months later, reproduce exactly
loaded_filter = ma.from_json(analysis_config["filter"])
reproduced_result = df.filter(loaded_filter.compile(df))
assert hash(reproduced_result) == analysis_config["result_hash"]
```

---

## The Technical Advantages

### 1. AST-First Design: Expressions as Data

Unlike Polars/Pandas/Ibis where expressions are opaque objects, mountainash-expressions builds a transparent Abstract Syntax Tree:

```python
expr = ma.col("age").gt(30).and_(ma.col("active").eq(True))

# You can INSPECT the expression
print(expr._node)
# BooleanIterableExpressionNode(
#     operator=ENUM_BOOLEAN_OPERATORS.AND,
#     operands=[
#         BooleanComparisonExpressionNode(operator=EQ, left=ColumnNode("age"), right=LiteralNode(30)),
#         BooleanComparisonExpressionNode(operator=EQ, left=ColumnNode("active"), right=LiteralNode(True)),
#     ]
# )

# You can TRANSFORM the expression
def add_tenant_filter(expr, tenant_id):
    """Inject tenant isolation into any expression."""
    tenant_check = ma.col("tenant_id").eq(tenant_id)
    return expr.and_(tenant_check)

secured_expr = add_tenant_filter(user_expr, current_tenant)

# You can SERIALIZE the expression
json_repr = expr.to_json()
yaml_repr = expr.to_yaml()
```

**Use Cases:**
- Store expressions in databases
- Send expressions over APIs
- Version control expressions in Git
- Build expression editors in UIs
- Generate documentation from expressions

### 2. Semantic Normalization: Same Behavior Everywhere

We don't just translate syntax—we normalize *semantics*:

```python
# Division: Always float division, even on SQLite
ma.col("a").divide(ma.col("b"))
# Polars: a / b → 6.666...
# SQLite: CAST(a AS REAL) / CAST(b AS REAL) → 6.666...  (not integer division!)

# Modulo: Always Python semantics (sign of divisor)
ma.col("a").modulo(ma.col("b"))
# Polars: a % b → 2
# DuckDB: ((a % b) + b) % b → 2  (normalized from remainder!)

# NULL handling: Explicit ternary logic
ma.col("nullable").t_eq(5).maybe_true()
# Returns True for: equal to 5 OR unknown
# Consistent across ALL backends
```

**You write logic. We handle the backend weirdness.**

### 3. Extended Pattern Library: Operations That Should Exist

Every data engineer has written these functions dozens of times:

```python
# Temporal patterns
ma.col("date").dt.last_day_of_month()
ma.col("date").dt.start_of_quarter()
ma.col("timestamp").dt.truncate_to("15 minutes")
ma.col("date").dt.is_business_day(calendar="NYSE")
ma.col("date").dt.add_business_days(5, calendar="US")

# Natural language time (like journalctl/find)
ma.col("created").dt.within_last("24 hours")
ma.col("updated").dt.older_than("7 days")
ma.col("expires").dt.between_ago("1 hour", "3 hours")

# String normalization
ma.col("text").str.normalize_whitespace()  # Multiple spaces → single space
ma.col("name").str.normalize_unicode("NFC")
ma.col("html").str.strip_html_tags()

# Financial
ma.col("price").round_to_tick(0.05)
ma.col("amount").as_percentage_of(ma.col("total"))

# Data quality
ma.col("email").is_valid_format("email")
ma.col("phone").is_valid_format("phone_us")
ma.col("value").is_outlier(method="iqr", threshold=1.5)
```

**These work on every backend.** No more copying utility functions between projects.

### 4. Ternary Logic: NULL-Aware Comparisons Done Right

SQL's three-valued logic is powerful but every DataFrame library implements it differently:

```python
# The problem: What does this return when score is NULL?
df.filter(col("score") > 50)
# Polars: NULL → excluded (NULL > 50 = NULL, treated as False)
# Pandas: NULL → excluded (but with different semantics)
# SQL: NULL → excluded (NULL > 50 = UNKNOWN, filtered out)

# With ternary logic, you're EXPLICIT:
ma.col("score").t_gt(50).is_true()      # Exclude unknowns (strict)
ma.col("score").t_gt(50).maybe_true()   # Include unknowns (lenient)
ma.col("score").t_gt(50).is_unknown()   # Find the unknowns (data quality)

# Custom sentinel values for legacy data:
ma.t_col("legacy_score", unknown={-99999, -1}).t_gt(50)
ma.t_col("status", unknown={"NA", "<MISSING>", None}).t_eq("active")
```

### 5. Telemetry & Observability: Know What Happened

Expressions are inspectable, so you can log exactly what was applied:

```python
# Middleware pattern for logging
class ExpressionLogger:
    def __init__(self, base_df):
        self.df = base_df
        self.applied_expressions = []

    def filter(self, expr):
        # Log the expression BEFORE compilation
        self.applied_expressions.append({
            "timestamp": datetime.now(),
            "operation": "filter",
            "expression": expr.to_json(),
            "expression_hash": expr.fingerprint(),
            "input_rows": len(self.df),
        })

        # Apply
        result = self.df.filter(expr.compile(self.df))

        # Log results
        self.applied_expressions[-1]["output_rows"] = len(result)
        self.applied_expressions[-1]["rows_removed"] = len(self.df) - len(result)

        self.df = result
        return self

# Usage
logged_df = ExpressionLogger(df)
logged_df.filter(ma.col("active").eq(True))
logged_df.filter(ma.col("score").ge(80))

# Full audit trail
print(logged_df.applied_expressions)
# [
#   {"operation": "filter", "expression": {"type": "eq", ...}, "input_rows": 1000, "output_rows": 750},
#   {"operation": "filter", "expression": {"type": "ge", ...}, "input_rows": 750, "output_rows": 234},
# ]
```

**Use Cases:**
- Debug data pipelines ("why did this row disappear?")
- Performance monitoring (which expressions are slow?)
- Compliance logging (what rules were applied?)
- Usage analytics (which columns are queried most?)

### 6. Expression Composition: Build Complex Rules from Simple Parts

Expressions are first-class objects that can be composed:

```python
# Define reusable rule components
is_active_user = ma.col("status").eq("active")
is_recent = ma.col("last_seen").dt.within_last("30 days")
is_premium = ma.col("tier").is_in(["pro", "enterprise"])
has_valid_email = ma.col("email").str.contains("@").and_(ma.col("email_verified").eq(True))

# Compose into complex rules
marketing_eligible = is_active_user.and_(is_recent).and_(has_valid_email)
upsell_candidates = marketing_eligible.and_(is_premium.not_())
churn_risk = is_active_user.and_(is_recent.not_())

# Store compositions as configurations
rule_library = {
    "marketing_eligible": marketing_eligible.to_json(),
    "upsell_candidates": upsell_candidates.to_json(),
    "churn_risk": churn_risk.to_json(),
}

# Load and apply dynamically
rule_name = request.params["rule"]
rule = ma.from_json(rule_library[rule_name])
result = df.filter(rule.compile(df))
```

### 7. Testing & Validation: Prove Correctness

Because expressions are abstract, you can test them systematically:

```python
import pytest
from hypothesis import given, strategies as st

# Property-based testing: expression behaves the same on all backends
@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=10))
def test_modulo_consistency(values):
    expr = ma.col("value").modulo(3)

    # Create same data on different backends
    polars_df = pl.DataFrame({"value": values})
    pandas_df = pd.DataFrame({"value": values})
    duckdb_table = ibis.memtable({"value": values})

    # Apply expression
    polars_result = polars_df.select(expr.compile(polars_df))["value"].to_list()
    pandas_result = pandas_df.assign(result=expr.compile(pandas_df))["result"].to_list()
    duckdb_result = duckdb_table.select(expr.compile(duckdb_table)).execute()["value"].to_list()

    # All backends produce identical results
    assert polars_result == pandas_result == duckdb_result

# Regression testing: rules haven't changed
def test_business_rule_unchanged():
    rule = load_production_rule("churn_detection_v2")
    expected_hash = "a1b2c3d4..."  # Stored from previous version
    assert rule.fingerprint() == expected_hash
```

---

## Comparison with Alternatives

### Narwhals: Complementary, Not Competing

**Important:** Narwhals is not a competitor—it's one of our backends!

As Marco Gorelli (Narwhals creator) often says, Narwhals is targeted at **library developers building universal DataFrame packages**, not general end-user usage. That's exactly how we use it.

```
mountainash-expressions
    │
    ├── Polars backend (direct)
    ├── Ibis backend (direct) → DuckDB, SQLite, PostgreSQL, Snowflake...
    └── Narwhals backend → Pandas, cuDF, Modin, PyArrow, and more!
```

**We leverage Narwhals** to extend our reach to users who aren't on Polars or Ibis directly. When you compile an expression against a Pandas DataFrame, we use Narwhals under the hood to execute it.

| Layer | Purpose |
|-------|---------|
| **Narwhals** | Unified DataFrame API for library authors |
| **mountainash-expressions** | Semantic normalization + extended patterns + serialization + AST inspection |

**Narwhals gives us the "how to call methods"—we add the "what those methods should mean" and patterns that don't exist anywhere.**

### vs. Writing Backend-Specific Code

| Aspect | Native Libraries | mountainash-expressions |
|--------|------------------|------------------------|
| **Development time** | O(n) for n backends | O(1) |
| **Maintenance** | n codepaths to update | 1 codebase |
| **Testing** | n test suites | 1 parametrized suite |
| **Migration risk** | High (rewrite) | Low (expressions unchanged) |
| **Consistency** | Manual verification | Guaranteed |

### vs. SQL as the Universal Language

| Aspect | SQL | mountainash-expressions |
|--------|-----|------------------------|
| **Type safety** | String-based | Python objects with IDE support |
| **Composability** | Limited (string concat) | Full (object composition) |
| **Testing** | Hard (strings) | Easy (objects) |
| **Backend support** | SQL backends only | SQL + DataFrame backends |
| **Serialization** | Yes (it's text) | Yes (structured) |

---

## Real-World Scenarios

### Scenario 1: Multi-Tenant SaaS Data Platform

**Situation:** You're building a data platform where each customer has different data filtering requirements.

**Traditional Approach:**
```python
# Hard-coded customer logic
if customer_id == "acme":
    result = df.filter((pl.col("status") == "active") & (pl.col("region") == "US"))
elif customer_id == "globex":
    result = df.filter((pl.col("type").is_in(["A", "B"])) & (pl.col("score") > 0.5))
elif customer_id == "initech":
    # ... hundreds more
```

**With mountainash-expressions:**
```python
# Store rules per-customer in database
customer_rules = db.query("SELECT filter_rule FROM customer_config WHERE id = ?", [customer_id])
rule = ma.from_json(customer_rules["filter_rule"])
result = df.filter(rule.compile(df))

# Customers can even edit their rules via UI
# Changes take effect immediately, no deployment needed
```

### Scenario 2: Gradual Migration from Pandas to Polars

**Situation:** You have 500 Pandas pipelines. Leadership wants Polars for performance. You can't rewrite everything at once.

**Traditional Approach:** Rewrite each pipeline one by one over 18 months. Hope nothing breaks.

**With mountainash-expressions:**
```python
# Phase 1: Wrap existing logic in abstract expressions
filter_expr = ma.col("value").gt(threshold).and_(ma.col("category").is_in(valid_categories))

# Phase 2: Run BOTH backends in parallel, compare results
pandas_result = pandas_df[filter_expr.compile(pandas_df)]
polars_result = polars_df.filter(filter_expr.compile(polars_df))
assert_dataframes_equal(pandas_result, polars_result)  # Validation!

# Phase 3: Switch to Polars with confidence
result = polars_df.filter(filter_expr.compile(polars_df))
```

### Scenario 3: Compliance Audit Trail

**Situation:** Regulators require you to prove that data filtering was applied correctly and consistently.

**Traditional Approach:** Screenshot your code? Hope Git history is enough?

**With mountainash-expressions:**
```python
# Every filter application is logged
@audit_logged
def process_customer_data(df, customer_id):
    rule = load_customer_rule(customer_id)

    audit_log.record({
        "timestamp": datetime.now(),
        "customer_id": customer_id,
        "rule_applied": rule.to_json(),
        "rule_version": rule.version,
        "rule_fingerprint": rule.fingerprint(),
        "input_rows": len(df),
        "columns_accessed": rule.referenced_columns(),
    })

    result = df.filter(rule.compile(df))

    audit_log.record({
        "output_rows": len(result),
        "execution_time_ms": elapsed,
    })

    return result

# Auditors can:
# 1. See exactly what rule was applied (JSON representation)
# 2. Verify the rule hasn't changed (fingerprint)
# 3. Know what columns were accessed (referenced_columns)
# 4. Reconstruct the exact filtering logic (from_json)
```

### Scenario 4: A/B Testing Filter Strategies

**Situation:** You want to test whether a stricter filter improves downstream model performance.

**With mountainash-expressions:**
```python
# Define variants
filter_control = ma.col("score").ge(0.5)
filter_treatment = ma.col("score").ge(0.7).and_(ma.col("confidence").ge(0.8))

# Store experiment config
experiment = {
    "name": "strict_filter_test",
    "control": filter_control.to_json(),
    "treatment": filter_treatment.to_json(),
    "allocation": 0.5,
}

# Apply based on assignment
variant = "treatment" if hash(user_id) % 2 == 0 else "control"
filter_expr = ma.from_json(experiment[variant])
result = df.filter(filter_expr.compile(df))

# Analysis can reconstruct exactly what was applied
# No ambiguity about what "stricter filter" meant
```

---

## The Vision: Expressions as a Universal Data Contract

Imagine a world where:

1. **Business analysts** define filtering rules in a visual UI
2. **Rules are stored** in a version-controlled database
3. **Data engineers** apply rules without knowing their contents
4. **Auditors** can inspect exactly what was applied
5. **The same rule** works whether you're on Polars today or Spark tomorrow
6. **Tests prove** the rule behaves identically across backends
7. **Migrations** require zero changes to business logic

**This is what mountainash-expressions enables.**

---

## Getting Started

```python
import mountainash_expressions as ma

# 1. Build an expression
expr = ma.col("age").gt(30).and_(ma.col("status").eq("active"))

# 2. Inspect it
print(expr.to_json())

# 3. Apply it to ANY DataFrame
result = your_df.filter(expr.compile(your_df))

# 4. Store it for later
db.save("user_filter", expr.to_json())

# 5. Load and reuse
loaded_expr = ma.from_json(db.load("user_filter"))
result = another_df.filter(loaded_expr.compile(another_df))
```

---

## Roadmap: What's Implemented vs. Planned

### Fully Implemented ✅

- **Three-layer protocol architecture** - Visitor, Expression, Builder protocols
- **Backend support** - Polars (direct), Ibis (direct), Narwhals (Pandas, cuDF, etc.)
- **Boolean operations** - All comparison and logical operators
- **Arithmetic operations** - Add, subtract, multiply, divide, modulo, power
- **String operations** - Upper, lower, trim, contains, replace, etc.
- **Temporal operations** - Year, month, day extraction, date arithmetic
- **Horizontal operations** - Coalesce, greatest, least
- **Null handling** - is_null, is_not_null, fill_null
- **Semantic normalization** - Consistent modulo, division behavior across backends
- **Natural language temporal** - `within_last("24 hours")`, `older_than("7 days")`

### Designed, Implementation Ready 🔄

- **Ternary logic** - Full design in `docs/TERNARY_LOGIC_ARCHITECTURE.md`
  - `t_eq()`, `t_and()`, `t_or()`, `t_not()`
  - Booleanizers: `is_true()`, `maybe_true()`, `is_unknown()`
  - Custom sentinel values per column

### Planned / Aspirational 📋

- **Expression serialization**
  ```python
  expr.to_json()           # Serialize to JSON
  expr.to_yaml()           # Serialize to YAML
  ma.from_json(string)     # Deserialize from JSON
  ```

- **Expression inspection utilities**
  ```python
  expr.fingerprint()           # Content hash for change detection
  expr.referenced_columns()    # List of columns accessed
  expr.complexity_score()      # Estimate of expression complexity
  ```

- **Extended pattern library**
  ```python
  .dt.last_day_of_month()
  .dt.is_business_day(calendar="NYSE")
  .dt.truncate_to("15 minutes")
  .str.normalize_whitespace()
  .is_valid_format("email")
  ```

- **Pandas backend** - Detection exists, full implementation needed

The AST-first architecture makes all these features straightforward to implement—the expression nodes are already inspectable Python objects.

---

## Summary

| If You Need... | Status | What We Provide |
|----------------|--------|-----------------|
| Backend portability | ✅ Now | Polars, Ibis, Narwhals (→Pandas, cuDF, etc.) |
| Semantic consistency | ✅ Now | Normalized modulo, division, NULL handling |
| Extended temporal patterns | ✅ Now | `within_last()`, `older_than()`, date arithmetic |
| Platform migrations | ✅ Now | Same expressions work on any backend |
| Package development | ✅ Now | True DataFrame-agnostic expression building |
| Cross-backend testing | ✅ Now | Parametrized test suite included |
| NULL-aware logic | 🔄 Designed | Ternary logic with custom sentinels |
| Expression serialization | 📋 Planned | JSON/YAML representation |
| Audit trail utilities | 📋 Planned | Fingerprinting, column extraction |
| Extended pattern library | 📋 Planned | Business day calc, truncation, validation |

**Stop writing the same logic for every DataFrame library. Stop hoping backends behave the same. Start using expressions that mean what they say.**
