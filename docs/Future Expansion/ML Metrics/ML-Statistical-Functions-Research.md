# ML and Statistical Functions in DataFrame Frameworks

**Research Date:** 2025-11-09
**Purpose:** Assess built-in ML/statistical function support across dataframe libraries to inform mountainash-expressions expansion strategy

---

## Executive Summary

**CORRECTED FINDING (2025-11-09):** ML metrics CAN be calculated as dataframe operations when you have predictions and actuals as columns!

**Initial Assessment (INCORRECT):**
- ❌ I initially concluded ML metrics belong in sklearn, not dataframe operations

**Corrected Assessment (CORRECT):**
- ✅ **ML Metrics ARE Dataframe Operations** when you have a table with `prediction` and `actual` columns
- ✅ Precision, Recall, F1 can be calculated using **CASE statements** + **aggregations** (COUNT, SUM)
- ✅ ROC-AUC, Gini can be calculated using **window functions** (RANK, cumulative SUM)
- ✅ These operations are **row-level comparisons** followed by **aggregations**

**Key Dependencies:**
1. **Conditional logic** - CASE/WHEN statements (we have via ternary expressions)
2. **Aggregation functions** - COUNT, SUM (table-level, may need aggregation framework)
3. **Window functions** - RANK(), ROW_NUMBER(), cumulative SUM() ← **Phase 8!**

**Recommendation:**
- ✅ Add **Phase 9: ML Metrics** after Phase 8 (Window Functions) is completed
- ✅ Continue with statistical functions (entropy, skew, kurtosis) as planned
- ✅ Math functions (abs, sqrt, trig) - comprehensive coverage exists, continue as Phase 1

---

## 1. Polars: Statistical Functions

### ✅ Built-in Statistical Functions

Polars has **excellent** statistical function support:

#### Distribution Measures
```python
# Entropy (Information Theory)
df.select(pl.col("a").entropy(base=2))  # ✅ BUILT-IN
# Formula: -sum(pk * log(pk)) where pk are discrete probabilities

# Skewness
df.select(pl.col("values").skew(bias=True))  # ✅ BUILT-IN
# Measures asymmetry of distribution

# Kurtosis
df.select(pl.col("values").kurtosis(fisher=True))  # ✅ BUILT-IN
# Measures "tailedness" of distribution
```

#### Correlation Methods
```python
# Pearson correlation
df.select(pl.corr("a", "b", method="pearson"))  # ✅ BUILT-IN

# Spearman rank correlation
df.select(pl.corr("a", "b", method="spearman"))  # ✅ BUILT-IN

# Note: Kendall's tau NOT supported in Polars
```

#### Variance and Standard Deviation
```python
# Variance
df.select(pl.col("values").var())  # ✅ BUILT-IN

# Standard deviation
df.select(pl.col("values").std())  # ✅ BUILT-IN

# Rolling variance
df.select(pl.col("values").rolling_var(window_size=7))  # ✅ BUILT-IN
```

#### Mathematical Functions (Complete)
```python
# Absolute value, rounding
.abs(), .round(n), .floor(), .ceil()  # ✅ BUILT-IN

# Trigonometry (full suite)
.arccos(), .arcsin(), .arctan(), .arctan2()  # ✅ BUILT-IN
.arccosh(), .arcsinh(), .arctanh()  # ✅ Hyperbolic

# Logarithms
.log(base), .log10(), .ln(), .exp()  # ✅ BUILT-IN

# Square root, power
.sqrt(), .pow(n)  # ✅ BUILT-IN

# Quantiles
.quantile(0.95)  # ✅ BUILT-IN
```

**Source:** https://docs.pola.rs/py-polars/html/reference/expressions/computation.html

---

---

## 2. ML Classification Metrics as Dataframe Operations

### ✅ Precision, Recall, F1, Accuracy (Ibis Implementation)

**Source:** https://ibis-project.org/posts/classification-metrics-on-the-backend/

Ibis blog post (Dec 2024) demonstrates calculating classification metrics **directly on the backend** using dataframe operations.

#### Basic Approach: Confusion Matrix Components

```python
# Given table with 'actual' and 'prediction' columns (both binary 0/1)
import ibis

# True Positives: both actual and prediction are 1
tp = (t.actual * t.prediction).sum()

# False Positives: prediction is 1, actual is 0
fp = t.prediction.sum() - tp

# False Negatives: actual is 1, prediction is 0
fn = t.actual.sum() - tp

# True Negatives: both actual and prediction are 0
tn = t.actual.count() - tp - fp - fn
```

#### Metric Calculations

```python
# Accuracy: proportion of correct predictions
accuracy = (t.actual == t.prediction).mean()

# Precision: proportion of true positives out of all positive predictions
precision = tp / t.prediction.sum()

# Recall: proportion of true positives out of all actual positives
recall = tp / t.actual.sum()

# F1 Score: harmonic mean of precision and recall
f1_score = 2 * tp / (t.actual.sum() + t.prediction.sum())
```

**Operations Required:**
- ✅ Element-wise multiplication: `actual * prediction`
- ✅ Element-wise comparison: `actual == prediction`
- ✅ Aggregations: `.sum()`, `.count()`, `.mean()`
- ✅ Arithmetic operations: `+`, `-`, `*`, `/`

**Backend Support:** Works across DuckDB, Postgres, Snowflake, SQLite, BigQuery

**Key Insight:** These metrics require **aggregations only**, NO window functions needed!

---

### ⚠️ ROC-AUC and Gini (Require Window Functions)

**ROC-AUC and Gini coefficient require ranking**, which depends on window functions:

```python
# Pseudocode for AUC calculation
# 1. Rank predictions in descending order
ranked = t.select(
    actual=t.actual,
    prediction=t.prediction
).order_by(t.prediction.desc())

# 2. Calculate cumulative true positives and false positives
cumulative_tp = t.actual.sum().over(order_by=t.prediction.desc())
cumulative_fp = (1 - t.actual).sum().over(order_by=t.prediction.desc())

# 3. Calculate AUC using trapezoidal rule
# (requires window functions for cumulative sums)
```

**Formula:** Gini = 2 * AUC - 1

**Operations Required:**
- ❌ RANK() or ROW_NUMBER() - **Phase 8: Window Functions**
- ❌ Cumulative SUM() - **Phase 8: Window Functions**
- ✅ Arithmetic operations

**Dependency:** ROC-AUC and Gini depend on **Phase 8 (Window Functions)** being implemented first.

---

### ❌ NOT Built-in (Custom Implementations in Decision Trees)

#### Gini Impurity (Decision Tree Metric)
```python
# NOT the same as Gini coefficient for ROC-AUC!
# Formula: Gini Impurity = 1 - sum(p_i^2) where p_i are class probabilities
# Use case: Decision tree splitting criterion (internal to sklearn)
```

**Finding:** Gini impurity is a **decision tree algorithm metric** used internally by sklearn.DecisionTreeClassifier, not a general dataframe operation.

**Articles found:**
- "Entropy in machine learning: Entropy vs Gini index"
- "Build a Decision Tree in Polars from Scratch" (uses custom Gini implementation)
- Multiple tutorials showing custom Gini functions

#### Information Gain
```python
# NOT built-in to Polars
# Formula: IG = Entropy(parent) - WeightedAvg(Entropy(children))
# Use case: Decision tree feature selection
```

**Finding:** Information gain is a **derived metric** calculated from entropy. Since Polars has `entropy()`, information gain can be computed manually.

#### ML Classification Metrics
```python
# NOT in Polars core (require sklearn or extensions)
# - Precision, Recall, F1-Score
# - ROC-AUC, PR-AUC
# - Accuracy, Confusion Matrix
```

**Finding:** These are **model evaluation metrics**, not dataframe operations. They require sklearn.metrics or similar.

**Extension Available:** `polars-ds` (third-party extension)
```python
# polars-ds extension adds ML metrics
import polars_ds as plds

df.select(plds.query_adj_r2("actual", "pred", p=5))
# Provides: adjusted R², RMSE, MAE, etc.
```

**Source:** https://polars-ds-extension.readthedocs.io/en/latest/metrics.html

---

## 2. DuckDB: Statistical Aggregate Functions

### ✅ Built-in Aggregate Functions

DuckDB provides standard SQL aggregate statistical functions:

#### Statistical Aggregates
```sql
-- Variance and Standard Deviation
SELECT VAR_POP(amount), VAR_SAMP(amount) FROM sales;  -- ✅ BUILT-IN
SELECT STDDEV_POP(amount), STDDEV_SAMP(amount) FROM sales;  -- ✅ BUILT-IN

-- Correlation and Covariance
SELECT CORR(x, y) FROM data;  -- ✅ BUILT-IN (Pearson)
SELECT COVAR_POP(x, y), COVAR_SAMP(x, y) FROM data;  -- ✅ BUILT-IN

-- Percentiles and Quantiles
SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) FROM data;  -- ✅ BUILT-IN
SELECT MEDIAN(value) FROM data;  -- ✅ BUILT-IN
```

#### Aggregate Statistics
```sql
-- Count, Sum, Average
SELECT COUNT(*), SUM(amount), AVG(amount) FROM sales;  -- ✅ BUILT-IN

-- Min, Max
SELECT MIN(value), MAX(value) FROM data;  -- ✅ BUILT-IN
```

**Source:** https://duckdb.org/docs/stable/sql/functions/aggregates.html

### ❌ NOT Built-in

- ❌ Entropy (information theory)
- ❌ Skewness, Kurtosis
- ❌ Gini coefficient
- ❌ ML metrics (F1, ROC-AUC, etc.)
- ❌ Spearman/Kendall correlation (only Pearson)

**Note:** DuckDB focuses on SQL-standard aggregates, not advanced statistical measures.

---

## 3. Ibis: Mathematical Expression Functions

### ✅ Built-in Mathematical Functions

Ibis provides comprehensive mathematical operations for expressions:

#### Basic Math
```python
# Absolute value, sign
expr.abs()  # ✅ BUILT-IN
expr.sign()  # ✅ BUILT-IN

# Rounding
expr.ceil(), expr.floor(), expr.round(n)  # ✅ BUILT-IN

# Square root, power
expr.sqrt(), expr.pow(n)  # ✅ BUILT-IN

# Logarithms
expr.ln(), expr.log(base), expr.log10(), expr.log2(), expr.exp()  # ✅ BUILT-IN
```

#### Trigonometry
```python
# Standard trigonometric functions
expr.cos(), expr.sin(), expr.tan()  # ✅ BUILT-IN
expr.acos(), expr.asin(), expr.atan(), expr.atan2(x, y)  # ✅ BUILT-IN

# Hyperbolic functions (backend-dependent)
expr.cosh(), expr.sinh(), expr.tanh()  # ⚠️ Backend-dependent
```

#### Clipping and Bounds
```python
expr.clip(lower=0, upper=100)  # ✅ BUILT-IN
```

**Source:** https://ibis-project.org/reference/expression-numeric.html

### ❌ NOT Built-in (Expression-level)

- ❌ Entropy, Skewness, Kurtosis (these are aggregates, not expressions)
- ❌ Correlation at expression level (correlation is an aggregate)
- ❌ ML metrics (table-level operations)

**Note:** Ibis focuses on **row-level expressions**, not **aggregations**. Statistical functions like correlation, variance exist as table-level operations, not expression-level.

---

## 4. IbisML: ML Pipeline Integration

### What is IbisML?

**IbisML** is a separate project that integrates Ibis with scikit-learn for scalable ML pipelines.

**Purpose:**
- Feature engineering at scale using Ibis
- Preprocessing transformations (scaling, encoding)
- Integration with sklearn estimators
- NOT for providing ML metrics as expressions

**Use Cases:**
```python
import ibis
import ibisml as ml

# Load data with DuckDB backend
table = ibis.read_csv("data.csv")

# Build preprocessing pipeline
pipeline = ml.Pipeline([
    ml.StandardScaler(),
    ml.OneHotEncoder(cols=["category"]),
])

# Transform data
transformed = pipeline.fit_transform(table)

# Train sklearn model
from sklearn.ensemble import XGBClassifier
model = XGBClassifier()
model.fit(transformed.to_pandas(), y)
```

**Key Point:** IbisML is about **preprocessing**, not **built-in ML functions** in expressions.

**Sources:**
- https://github.com/ibis-project/ibis-ml
- https://ibis-project.org/posts/ibisml/

---

## 5. Pandas: Statistical Methods

Pandas has extensive statistical functions, primarily at **Series/DataFrame level**:

### ✅ Built-in Statistical Methods

```python
# Correlation
df.corr(method='pearson')  # ✅ Pearson
df.corr(method='spearman')  # ✅ Spearman
df.corr(method='kendall')  # ✅ Kendall

# Variance, Standard Deviation
df.var(), df.std()  # ✅ BUILT-IN

# Skewness, Kurtosis
df.skew()  # ✅ BUILT-IN
df.kurt()  # ✅ BUILT-IN (kurtosis)

# Quantiles, Percentiles
df.quantile(0.95)  # ✅ BUILT-IN
```

### ❌ NOT Built-in

- ❌ Entropy (requires scipy or custom implementation)
- ❌ Gini coefficient
- ❌ ML metrics (require sklearn.metrics)

**Note:** Pandas focuses on descriptive statistics, not information theory or ML metrics.

---

## 6. Comparison Matrix

| Function Category | Polars | DuckDB | Ibis | Pandas | Sklearn |
|-------------------|--------|--------|------|--------|---------|
| **Mathematical** |
| abs, sqrt, round | ✅ | ✅ | ✅ | ✅ | N/A |
| Trigonometry (sin, cos, tan) | ✅ | ✅ | ✅ | ✅ | N/A |
| Logarithms (ln, log, exp) | ✅ | ✅ | ✅ | ✅ | N/A |
| **Statistical** |
| Variance, Std Dev | ✅ | ✅ | ✅ (agg) | ✅ | ✅ |
| Correlation (Pearson) | ✅ | ✅ | ✅ (agg) | ✅ | ✅ |
| Correlation (Spearman) | ✅ | ❌ | ⚠️ | ✅ | ✅ |
| Correlation (Kendall) | ❌ | ❌ | ⚠️ | ✅ | ✅ |
| Skewness | ✅ | ❌ | ❌ | ✅ | ❌ |
| Kurtosis | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Information Theory** |
| Entropy | ✅ | ❌ | ❌ | ❌ | ✅ |
| **ML Metrics (Classification)** |
| Gini Coefficient | ❌ | ❌ | ❌ | ❌ | ✅ (custom) |
| Information Gain | ❌ | ❌ | ❌ | ❌ | ✅ (custom) |
| Precision, Recall, F1 | ❌ | ❌ | ❌ | ❌ | ✅ |
| ROC-AUC, PR-AUC | ❌ | ❌ | ❌ | ❌ | ✅ |
| **ML Metrics (Regression)** |
| MSE, RMSE, MAE | ❌ | ❌ | ❌ | ❌ | ✅ |
| R², Adjusted R² | ❌ | ❌ | ❌ | ❌ | ✅ |

**Legend:**
- ✅ Built-in support
- ⚠️ Backend-dependent or limited support
- ❌ Not available / Requires external library

---

## 7. Key Insights

### 7.1 Statistical Functions vs ML Metrics

**Statistical Functions** (✅ Well-supported in dataframes):
- Descriptive statistics: mean, median, variance, std dev
- Distribution measures: skewness, kurtosis, entropy
- Correlation: Pearson, Spearman, (sometimes Kendall)
- Mathematical: trigonometry, logarithms, rounding

**ML Metrics** (❌ NOT in dataframe libraries):
- Classification metrics: precision, recall, F1, ROC-AUC
- Regression metrics: MSE, RMSE, MAE, R²
- Decision tree metrics: Gini coefficient, information gain

**Why the difference?**
- Statistical functions operate on **single columns** or **pairs of columns**
- ML metrics operate on **predictions vs actuals** (model evaluation)
- ML metrics are **sklearn.metrics** domain, not dataframe domain

### 7.2 Polars Leads in Statistical Functions

**Polars has the most comprehensive built-in statistical support:**

1. ✅ `entropy()` - Unique among dataframe libraries
2. ✅ `skew()` and `kurtosis()` - Distribution analysis
3. ✅ Pearson and Spearman correlation
4. ✅ Complete mathematical functions (trig, log, etc.)
5. ✅ Rolling window statistics

**Missing in Polars:**
- ❌ Kendall's tau correlation
- ❌ Mutual information
- ❌ Any ML metrics (these belong in sklearn)

### 7.3 Gini Coefficient is NOT a General Statistical Function

**Important Finding:** Gini coefficient is primarily used in:
1. Decision tree splitting (sklearn DecisionTreeClassifier)
2. Economics (income inequality - different formula)

It is **NOT** a general statistical measure like correlation or entropy.

**For ML use cases:**
- Gini is calculated internally by decision tree algorithms
- Not typically needed as a standalone dataframe operation
- If needed, can be implemented as custom function

### 7.4 Entropy is the Exception

**Polars `entropy()` is unique:**
- Only dataframe library with built-in entropy
- Information theory measure (not just ML)
- Useful for: data compression, feature selection, decision trees
- Formula: `-sum(pk * log(pk))`

**Use case for mountainash-expressions:**
- Consider adding `entropy()` as it's expression-level
- Aligns with Polars, fills gap in other backends

---

## 8. Recommendations for mountainash-expressions

### 8.1 Priority 1: Mathematical Functions ✅

**Already planned in Phase 1 (Math Operations):**
- ✅ abs, sign, sqrt, round, floor, ceil
- ✅ ln, log, log10, log2, exp
- ✅ Trigonometry: sin, cos, tan, asin, acos, atan, atan2

**Status:** Continue as planned. These are expression-level operations with excellent backend support.

### 8.2 Priority 2: Statistical Functions (New Category)

**Consider adding as new phase:**

#### High Value (Expression-level)
```python
# Entropy (information theory)
col("probabilities").entropy(base=2)  # Polars: ✅, Others: ❌

# Clipping (already in Ibis comparison)
col("value").clip(lower=0, upper=100)  # Ibis: ✅, Polars: ✅
```

#### Medium Value (Aggregate-level - May be out of scope)
```python
# Correlation (table-level aggregate)
corr(col("a"), col("b"), method="pearson")  # Polars: ✅, DuckDB: ✅

# Variance, Std Dev (aggregates)
col("values").var(), col("values").std()  # All: ✅

# Skewness, Kurtosis (aggregates)
col("values").skew(), col("values").kurtosis()  # Polars: ✅, Pandas: ✅
```

**Note:** These are **aggregates**, not expressions. May be outside scope of mountainash-expressions if focus is on row-level operations.

### 8.3 Priority 3: ML Metrics ✅ RECOMMENDED (After Phase 8)

**CORRECTED RECOMMENDATION:** ML metrics ARE dataframe operations and should be added!

#### Phase 9A: Classification Metrics (No Window Functions Required)
**Effort:** 1-2 weeks
**Priority:** 🔴 HIGH
**Operations:** 4
**Dependencies:** Aggregation framework only

```python
# Given table with 'prediction' and 'actual' columns (binary 0/1)

# Accuracy: proportion of correct predictions
ma.accuracy(prediction=col("pred"), actual=col("actual"))
# Implementation: (actual == prediction).mean()

# Precision: TP / (TP + FP)
ma.precision(prediction=col("pred"), actual=col("actual"))
# Implementation: (actual * prediction).sum() / prediction.sum()

# Recall: TP / (TP + FN)
ma.recall(prediction=col("pred"), actual=col("actual"))
# Implementation: (actual * prediction).sum() / actual.sum()

# F1 Score: harmonic mean of precision and recall
ma.f1_score(prediction=col("pred"), actual=col("actual"))
# Implementation: 2 * tp / (actual.sum() + prediction.sum())
```

**Operations Required:**
- ✅ Element-wise operations (*, ==)
- ✅ Aggregations (.sum(), .count(), .mean())
- ❌ NO window functions needed!

**Reference:** https://ibis-project.org/posts/classification-metrics-on-the-backend/

#### Phase 9B: Ranking-Based Metrics (Requires Window Functions)
**Effort:** 2-3 weeks
**Priority:** 🟡 MEDIUM-HIGH
**Operations:** 2
**Dependencies:** Phase 8 (Window Functions) MUST be complete first

```python
# ROC-AUC: area under ROC curve
ma.roc_auc(prediction=col("pred_proba"), actual=col("actual"))
# Requires: RANK(), cumulative SUM() over ordered predictions

# Gini Coefficient: 2 * AUC - 1
ma.gini(prediction=col("pred_proba"), actual=col("actual"))
# Derived from AUC
```

**Operations Required:**
- ❌ RANK() or ROW_NUMBER() - Phase 8
- ❌ Cumulative SUM().over() - Phase 8
- ✅ Arithmetic operations

### 8.4 Suggested New Phase: Statistical Functions

**Phase 8B: Statistical Functions (Optional)**
**Effort:** 1-2 weeks
**Priority:** 🟡 MEDIUM
**Operations:** 3-5

#### Expression-level Statistical Operations
```python
# Entropy (unique to Polars, high value)
col("probabilities").entropy(base=2)

# Clip (already in Ibis gaps)
col("value").clip(lower=0, upper=100)

# Checks for special values
col("value").is_nan()
col("value").is_inf()
col("value").is_finite()
```

#### Aggregate Statistical Operations (If in scope)
```python
# Correlation
ma.corr(col("a"), col("b"), method="pearson")
ma.corr(col("a"), col("b"), method="spearman")

# Distribution measures
col("values").skew()
col("values").kurtosis()
```

**Backend Compatibility:**
| Operation | Polars | Ibis | DuckDB | SQLite | Pandas |
|-----------|--------|------|--------|--------|--------|
| entropy() | ✅ | ❌ | ❌ | ❌ | ❌ |
| clip() | ✅ | ✅ | ⚠️ | ⚠️ | ✅ |
| is_nan() | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| corr() | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| skew() | ✅ | ❌ | ❌ | ❌ | ✅ |

---

## 9. Summary

### What We Learned

1. **Polars has excellent statistical support** - Best-in-class for entropy, skewness, kurtosis
2. **ML metrics ARE dataframe operations** - When you have predictions and actuals as columns! ← **CRITICAL CORRECTION**
3. **Mathematical functions are universal** - All frameworks support basic math/trig
4. **Ibis blog post confirms the approach** - Dec 2024 post shows classification metrics on backend
5. **Window functions unlock advanced metrics** - ROC-AUC and Gini require Phase 8

### Action Items for mountainash-expressions

✅ **Continue with planned math functions (Phase 1)**
- Full coverage across all backends
- High value, critical for analytical work

✅ **Add ML Classification Metrics (Phase 9A)**
- Precision, Recall, F1, Accuracy
- Requires only aggregations (no window functions!)
- Reference: Ibis blog post implementation
- **Can be done BEFORE Phase 8**

✅ **Add Ranking-Based Metrics (Phase 9B)**
- ROC-AUC, Gini coefficient
- Requires Phase 8 (Window Functions) first
- **Must wait for window function support**

⚠️ **Consider statistical functions (New phase)**
- `entropy()` is unique and valuable
- `clip()` already identified in Ibis gaps
- Aggregate functions (corr, var, std) may be out of scope

---

## 10. References

### Polars Documentation
- Functions: https://docs.pola.rs/py-polars/html/reference/expressions/functions.html
- Computation: https://docs.pola.rs/py-polars/html/reference/expressions/computation.html
- Statistical: https://docs.pola.rs/py-polars/html/reference/dataframe/api/polars.DataFrame.corr.html

### DuckDB Documentation
- Aggregate Functions: https://duckdb.org/docs/stable/sql/functions/aggregates.html
- Statistical Aggregates: https://duckdb.org/docs/stable/sql/functions/aggregates.html

### Ibis Documentation
- Numeric Expressions: https://ibis-project.org/reference/expression-numeric.html
- **Classification Metrics Blog Post (Dec 2024):** https://ibis-project.org/posts/classification-metrics-on-the-backend/

### IbisML
- GitHub: https://github.com/ibis-project/ibis-ml
- Blog Post: https://ibis-project.org/posts/ibisml/

### ML Metrics with SQL/Dataframes
- **BigQuery Gini Calculation:** Calculating Gini Coefficient in BigQuery with SQL (Medium)
- **SQL Classification Metrics:** StackOverflow - How to count classification_report in SQL
- **ROC-AUC Calculation:** Various implementations using RANK() and cumulative window functions

### Polars-DS Extension
- Documentation: https://polars-ds-extension.readthedocs.io/en/latest/metrics.html

### Scikit-learn
- Metrics Module: https://scikit-learn.org/stable/api/sklearn.metrics.html

---

**Research Conducted:** 2025-11-09
**Researcher:** Claude (Anthropic)
**Next Review:** After Phase 1 completion

---

## Revision History

**2025-11-09 (Initial Research):**
- ❌ Initially concluded ML metrics belong in sklearn, not dataframe operations
- Focused on mathematical and statistical functions

**2025-11-09 (CORRECTED):**
- ✅ User correctly pointed out: ML metrics ARE dataframe operations when predictions/actuals are columns
- ✅ Found Ibis blog post (Dec 2024) demonstrating classification metrics on backend
- ✅ Found SQL implementations using CASE statements, aggregations, and window functions
- ✅ Updated recommendations to include Phase 9A (Classification Metrics) and Phase 9B (Ranking Metrics)
- **Key insight:** Basic metrics (precision, recall, F1) don't need window functions; only ROC-AUC/Gini do!
