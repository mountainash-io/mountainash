# Analysis of User's Existing ML Metrics Implementation

**Date:** 2025-11-09
**Source:** `/home/nathanielramm/Downloads/metrics/` (2014-2016 implementation)
**Purpose:** Understand existing implementation to inform mountainash-expressions simplification

---

## Executive Summary

**What User Has:** A Django-based credit risk metrics system with SQL + Python hybrid calculations for Gini, PSI, Information Value, and Actual vs Expected metrics.

**Key Complexity:** Heavy Django ORM coupling, complex dimension model, manual cumulative sum calculations in Python, and database storage overhead.

**Simplification for mountainash-expressions:** Remove Django/database dependencies, use window functions for cumulative operations, work with raw dataframes instead of discretized bins, stateless evaluation.

---

## Metrics Implemented

### 1. Gini Coefficient (`metric_gini.py`)

**Purpose:** Measure model discrimination power (ROC-AUC related: Gini = 2*AUC - 1)

**Current Implementation:**
```python
# SQL: Aggregate predictions into scorebands
SELECT
    scoreband,
    sum(outcomevalue_num) as numbin_bad,
    sum(1-outcomevalue_num) as numbin_good,
    pct_bad = numbin_bad / numtot_bad,
    pct_good = numbin_good / numtot_good,
    pct_pop = (numbin_bad + numbin_good) / (numtot_bad + numtot_good)
FROM tbl_predictiondata pd
INNER JOIN tbl_outcomedata oc ...
GROUP BY scoreband
ORDER BY scoreband DESC

# Python: Calculate cumulative sums and Gini
cusum_bad[idx] = cusum_bad[idx-1] + row['pct_bad']
cusum_good[idx] = cusum_good[idx-1] + row['pct_good']

gini_rect = (cusum_bad[idx] - row['pct_bad']) * row['pct_good']
gini_tri = row['pct_bad'] * row['pct_good'] * 0.5

gini = (sum(gini_rect) * 0.5) + sum(gini_tri) - 0.5
```

**What Makes It Complex:**
1. ❌ Discretization into scorebands required
2. ❌ Cumulative sums calculated in Python (not SQL)
3. ❌ Stores intermediate bin values in database
4. ❌ Django ORM dimension model (ObservationTime, PerformanceTime, etc.)

**Simplified mountainash-expressions Version:**
```python
# Direct calculation using window functions (NO discretization needed!)
import mountainash_expressions as ma

# Given dataframe with 'prediction' and 'actual' columns
gini = ma.gini(
    prediction=col("pred_proba"),  # Raw probabilities, not binned!
    actual=col("actual")
)

# Implementation (conceptual):
# 1. ORDER BY prediction DESC
# 2. Calculate cumulative TP rate: cum_sum(actual) / sum(actual)
# 3. Calculate cumulative FP rate: cum_sum(1-actual) / sum(1-actual)
# 4. Calculate AUC using trapezoidal rule
# 5. Gini = 2*AUC - 1
```

**Key Simplifications:**
- ✅ No discretization/binning required
- ✅ Window functions do cumulative sums
- ✅ No database storage
- ✅ Works directly with raw predictions

---

### 2. Population Stability Index (`metric_psi.py`)

**Purpose:** Detect model drift by comparing prediction distributions across time periods

**Current Implementation:**
```sql
SELECT
    scoreband,
    log(pct_bin_analysis / pct_bin_base) as log_bin,
    pct_bin_base = numbin_base / numtot_base,
    pct_bin_analysis = numbin_analysis / numtot_analysis
FROM ...

# Python
psi = sum(log_bin)
```

**What It Does:**
- Compares prediction distribution at two time points
- PSI > 0.1 indicates significant distribution shift
- PSI > 0.25 indicates severe shift (model needs retraining)

**Simplified mountainash-expressions Version:**
```python
# Compare two dataframes
psi = ma.psi(
    base=df_base,
    analysis=df_analysis,
    score_column="prediction",
    bins=10  # Optional: auto-discretize or use custom bins
)

# Or with explicit binning
psi = ma.psi(
    base_pct=col("base_pct"),
    analysis_pct=col("analysis_pct")
)
# Result: sum((analysis_pct - base_pct) * log(analysis_pct / base_pct))
```

**Key Insight:** PSI is a **model monitoring metric**, useful for detecting when to retrain models!

---

### 3. Information Value (`metric_iv.py`)

**Purpose:** Feature selection metric for credit risk - identifies which features best separate goods from bads

**Current Implementation:**
```python
# SQL aggregates by bins
SELECT
    binname,
    pct_bad = numbin_bad / numtot_bad,
    pct_good = numbin_good / numtot_good,
    WoE = ln(pct_good / pct_bad),
    IV_bin = (pct_good - pct_bad) * WoE
FROM ...

# Python
iv = sum(IV_bin)
```

**Interpretation:**
- IV < 0.02: Not predictive
- IV 0.02-0.1: Weak predictor
- IV 0.1-0.3: Medium predictor
- IV 0.3-0.5: Strong predictor
- IV > 0.5: **Suspicious** (check for leakage!)

**Simplified mountainash-expressions Version:**
```python
# Calculate IV for a feature
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=10
)

# Or with WoE (Weight of Evidence) per bin
woe_df = ma.weight_of_evidence(
    feature=col("age"),
    target=col("default"),
    bins=10
)
# Returns: DataFrame with bins, WoE, IV per bin
```

**Key Insight:** Information Value is primarily a **feature selection** metric, not model evaluation!

---

### 4. Actual vs Expected (`metric_avse.py`)

**Purpose:** Suite of regression metrics comparing predicted vs actual outcomes

**Metrics Calculated:**

#### APE (Absolute Percentage Error)
```python
ape = abs(1 - (expected / actual)) * 100
```

#### MAPE (Mean Absolute Percentage Error)
```python
mape = sum(abs(actual - expected) / actual * pct_pop)
```

#### RMSE (Root Mean Squared Error)
```python
rmse = sqrt(sum((actual - expected)^2))
```

#### RMSLE (Root Mean Squared Log Error)
```python
rmsle = sqrt(sum((log(actual+1) - log(expected+1))^2))
```

#### MIV (Marginal Information Value)
```python
# Change in IV when comparing base vs analysis period
miv = sum((pct_good - pct_bad) * delta_WoE)
```

#### Log Loss (Binary Cross-Entropy)
```python
logloss = -sum(actual * log(expected) + (1-actual) * log(1-expected)) / n
```

**Simplified mountainash-expressions Version:**
```python
# Individual metrics
rmse = ma.rmse(prediction=col("pred"), actual=col("actual"))
rmsle = ma.rmsle(prediction=col("pred"), actual=col("actual"))
logloss = ma.log_loss(prediction=col("pred"), actual=col("actual"))

# Or calculate multiple at once
metrics = ma.regression_metrics(
    prediction=col("pred"),
    actual=col("actual"),
    metrics=["rmse", "rmsle", "mape", "logloss"]
)
```

---

## Complexity Analysis

### What Makes Current Implementation Complex

#### 1. Django ORM Integration
```python
# Heavy database coupling
objMetricRef, created = MetricReference.objects.get_or_create(
    clientproject=objClientproject,
    obstime=objObstime,
    perftime=objPerftime,
    vintagetime=objVintagetime,
    analysistime=objAnalysistime,
    predmodelsuite=objPredmodelsuite,
    predmodel=objPredmodel,
    outcome=objOutcome,
    metric=objMetric,
    scorebandsystem=objScorebandsystem,
    scoreband=objScoreband,
    subpopref=objSubpopref,
    datafieldtransform=objdatafieldtransform,
    datafieldbin=objDatafieldbin,
    randomdigitband=objRandomdigitband
)
```

**Problem:** 14 dimension objects to track a single metric!

**mountainash-expressions:** No storage, just evaluate and return

---

#### 2. Complex Dimension Model
```python
# Time dimensions
objObstime      # Observation time
objPerftime     # Performance time
objVintagetime  # Vintage time
objAnalysistime # Analysis time

# Each has associated TimeWindow objects
```

**Problem:** Over-engineered for most use cases

**mountainash-expressions:** User manages their own time filtering with standard dataframe operations

---

#### 3. Manual Cumulative Sums in Python
```python
# Current approach
idx = 0
for row in arr_values:
    if idx == 0:
        cusum_bad[idx] = row['pct_bad']
    else:
        cusum_bad[idx] = cusum_bad[idx-1] + row['pct_bad']
    idx += 1
```

**Problem:** Inefficient, requires fetching data to Python

**mountainash-expressions:** Use SQL window functions
```sql
-- Cumulative sum done in SQL
SUM(pct_bad) OVER (ORDER BY scoreband DESC) as cusum_bad
```

---

#### 4. Scoreband/Bin Discretization System
```python
# Complex discretizer framework
from apps.analysis.framework.transform.discretise.discretiser_scoreband import ScorebandDiscretiser
from apps.analysis.framework.transform.discretise.discretiser_datafield import DataFieldDiscretiser

sql_scoreband_case, casevarname = objQuery.buildsql_scorebandsystem_case(scorebandsystem_id)
```

**Problem:** Requires pre-defined scoreband systems

**mountainash-expressions:** Optional auto-binning, or work directly with raw values

---

## Simplification Strategy for mountainash-expressions

### Principle 1: Pure Expression Evaluation
**Current:** Store metrics in database with complex dimension model
**Simplified:** Evaluate expression, return result, don't store

```python
# Current
metric_engine.calc_GINI_discrete(
    scorebandsystem_id=123,
    start_obstime_id=456,
    perftime_id=789,
    outcome_id=101,
    predmodel_id=202
)
# → Stores in MetricReference and MetricValue tables

# Simplified
gini_value = ma.gini(
    prediction=col("pred"),
    actual=col("actual")
).eval()(df)
# → Returns scalar value
```

---

### Principle 2: Use Window Functions for Cumulative Operations
**Current:** Fetch data to Python, calculate cumulative sums in loops
**Simplified:** Let SQL/backend do cumulative sums with window functions

```python
# Current (Python loop)
for idx, row in enumerate(arr_values):
    if idx == 0:
        cusum_bad[idx] = row['pct_bad']
    else:
        cusum_bad[idx] = cusum_bad[idx-1] + row['pct_bad']

# Simplified (Window function)
cusum_bad = col("pct_bad").cumsum().over(order_by=col("score").desc())
```

**Dependency:** Requires **Phase 8: Window Functions** to be implemented

---

### Principle 3: Work with Raw Data, Optional Binning
**Current:** Requires pre-discretized scorebands
**Simplified:** Work directly with raw predictions, auto-bin if needed

```python
# Current: Requires scoreband system defined in database
objSB = ScoreBandSystem.objects.get(scorebandsystem_id=scorebandsystem_id)

# Simplified: Auto-bin if needed, or work with raw data
# Option 1: Raw data (for Gini, AUC)
gini = ma.gini(prediction=col("pred_proba"), actual=col("actual"))

# Option 2: Auto-bin (for PSI, IV)
psi = ma.psi(base=df1, analysis=df2, score_column="pred", bins=10)

# Option 3: Custom bins
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=[0, 18, 25, 35, 45, 55, 65, 100]
)
```

---

### Principle 4: Stateless, Functional API
**Current:** Object-oriented with state management
**Simplified:** Pure functions, no state

```python
# Current
engine = MetricEngine_Gini()
metricref_id = engine.calc_GINI_discrete(
    scorebandsystem_id=123,
    start_obstime_id=456,
    perftime_id=789
)

# Simplified (Functional)
gini_expr = ma.gini(prediction=col("pred"), actual=col("actual"))
result = gini_expr.eval()(df)
```

---

## Recommendations for mountainash-expressions

### Phase 9A: Basic ML Metrics (Can do NOW)
**Priority:** 🔴 HIGH
**Effort:** 1-2 weeks
**Dependencies:** Aggregation framework only

```python
# Classification Metrics (Binary)
ma.accuracy(prediction=col("pred"), actual=col("actual"))
ma.precision(prediction=col("pred"), actual=col("actual"))
ma.recall(prediction=col("pred"), actual=col("actual"))
ma.f1_score(prediction=col("pred"), actual=col("actual"))

# Regression Metrics
ma.rmse(prediction=col("pred"), actual=col("actual"))
ma.rmsle(prediction=col("pred"), actual=col("actual"))
ma.mae(prediction=col("pred"), actual=col("actual"))
ma.mape(prediction=col("pred"), actual=col("actual"))
ma.log_loss(prediction=col("pred_proba"), actual=col("actual"))
```

**Note:** These require **only aggregations** (SUM, COUNT, MEAN), no window functions!

---

### Phase 9B: Ranking-Based Metrics (After Phase 8)
**Priority:** 🟡 MEDIUM-HIGH
**Effort:** 2-3 weeks
**Dependencies:** Phase 8 (Window Functions) MUST be complete

```python
# Requires window functions for ranking and cumulative sums
ma.roc_auc(prediction=col("pred_proba"), actual=col("actual"))
ma.gini(prediction=col("pred_proba"), actual=col("actual"))
```

---

### Phase 9C: Credit Risk Metrics (Optional, After Phase 9B)
**Priority:** 🟢 MEDIUM
**Effort:** 2-3 weeks
**Dependencies:** Phase 9B complete, auto-binning framework

```python
# Feature Selection
ma.information_value(feature=col("age"), target=col("default"), bins=10)
ma.weight_of_evidence(feature=col("age"), target=col("default"), bins=10)

# Model Monitoring
ma.psi(base=df_base, analysis=df_analysis, score_column="pred", bins=10)

# Model Drift Detection
ma.miv(base=df_base, analysis=df_analysis, feature=col("age"), target=col("default"))
```

**Why Optional:** These are specialized credit risk metrics, may not be needed for all users

---

## Key Insights from User's Implementation

### 1. Gini IS a Dataframe Operation
✅ User's implementation proves Gini can be calculated with SQL + aggregations
✅ Just need window functions for cumulative sums
✅ No sklearn needed!

### 2. Binning is Optional
⚠️ User's implementation uses scorebands, but this is for interpretability
✅ Gini/AUC work fine with raw probabilities (no binning needed)
✅ IV/PSI benefit from binning for interpretability

### 3. Window Functions Are Critical
❌ User calculates cumulative sums in Python (inefficient)
✅ SQL window functions make this much cleaner
✅ **Phase 8 (Window Functions) unlocks Phase 9B**

### 4. Credit Risk Metrics Are Valuable
✅ Information Value (IV) - Feature selection
✅ Population Stability Index (PSI) - Model drift detection
✅ Weight of Evidence (WoE) - Interpretable feature transformation
✅ These are used heavily in financial services

---

## Technical Debt to Avoid

### ❌ Don't Replicate These Issues:

1. **No Django ORM coupling** - Keep it dataframe-agnostic
2. **No complex dimension model** - Let users manage their own time dimensions
3. **No database storage** - Pure evaluation, return results
4. **No Python loops for cumulative sums** - Use window functions
5. **No required discretization** - Make binning optional

---

## Implementation Roadmap

### Near-term (Phase 9A): Basic Metrics
**Can implement NOW without window functions:**
1. Accuracy, Precision, Recall, F1
2. RMSE, RMSLE, MAE, MAPE
3. Log Loss (Binary Cross-Entropy)

**Implementation:**
- Use CASE statements for TP/FP/FN/TN
- Use SUM() and COUNT() aggregations
- Reference: Ibis blog post implementation

---

### Mid-term (Phase 9B): Ranking Metrics
**Requires Phase 8 (Window Functions) first:**
1. ROC-AUC
2. Gini Coefficient

**Implementation:**
- ORDER BY prediction DESC
- RANK() or ROW_NUMBER()
- Cumulative SUM() OVER (ORDER BY ...)
- Trapezoidal rule for AUC

---

### Long-term (Phase 9C): Credit Risk Metrics
**Requires auto-binning framework:**
1. Information Value (IV)
2. Weight of Evidence (WoE)
3. Population Stability Index (PSI)
4. Marginal Information Value (MIV)

**Implementation:**
- Auto-binning using quantiles or custom thresholds
- GROUP BY bins
- Calculate WoE = ln(pct_good / pct_bad)
- Calculate IV = sum((pct_good - pct_bad) * WoE)

---

## Summary

**User's Implementation Shows:**
1. ✅ ML metrics ARE dataframe operations (not sklearn-only)
2. ✅ Gini calculation is feasible with window functions
3. ✅ Credit risk metrics (IV, PSI, WoE) have real value
4. ⚠️ Current implementation is over-engineered with Django/database coupling
5. ⚠️ Cumulative sums in Python are inefficient (should use window functions)

**For mountainash-expressions:**
1. ✅ Implement Phase 9A (basic metrics) soon - high value, low complexity
2. ✅ Implement Phase 9B (Gini, AUC) after Phase 8 (window functions)
3. ⚠️ Consider Phase 9C (credit risk metrics) based on user demand
4. ✅ Keep it simple: stateless, functional API with no database coupling

**Key Takeaway:** User's implementation validates that these metrics belong in mountainash-expressions, but shows the path to a much simpler design!

---

**Document Created:** 2025-11-09
**Source Code:** /home/nathanielramm/Downloads/metrics/ (2014-2016)
**Next Steps:** Incorporate findings into Phase 9 design and implementation roadmap
