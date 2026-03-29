# Analysis of User's Credit Risk Framework

**Date:** 2025-11-09
**Source:** `/home/nathanielramm/Downloads/framework/` (2014-2016 implementation)
**Purpose:** Understand data model coupling and discretization complexity to inform mountainash-expressions simplification

---

## Executive Summary

**What User Built:** A comprehensive credit risk analytics framework with discretization, query building, metrics calculation, and database persistence - approximately **4,179 lines of Python code**.

**Key Components:**
1. **Discretization** (1,321 lines) - Bin continuous variables, aggregate categoricals
2. **Query Builders** (1,537 lines) - Generate SQL CASE statements from database bin definitions
3. **Metrics** (1,321 lines) - Gini, IV, PSI, AvsE calculations
4. **Framework Total:** ~4,179 lines + Django models

**Core Problem:** Tight coupling to Django ORM and database schema makes it inflexible and complex.

**Lesson for mountainash-expressions:** Build a **stateless, dataframe-agnostic** expression system that works directly with data, no database required.

---

## Code Size Breakdown

```
Framework Structure:
├── transform/discretise/   1,321 lines
│   ├── discretiser_datafield.py    904 lines  ← Bin creation logic
│   ├── discretiser_scoreband.py    290 lines  ← Score band system
│   ├── discretiser_base.py          95 lines  ← Quantile calculations
│   └── smoother_base.py             32 lines  ← Smoothing (unused?)
├── query/                  1,537 lines
│   ├── query_datafield.py        1,041 lines  ← SQL CASE statement builder
│   ├── query_scoreband.py          448 lines  ← Score band SQL generator
│   └── query_base.py                48 lines  ← Base query utilities
└── metrics/                1,321 lines
    ├── metric_gini.py              303 lines  ← Gini coefficient
    ├── metric_iv.py                202 lines  ← Information Value
    ├── metric_psi.py               181 lines  ← Population Stability Index
    ├── metric_avse.py              500+ lines ← Actual vs Expected suite
    └── metric_base.py              133 lines  ← Storage infrastructure

TOTAL: ~4,179 lines of Python (excludes Django models, templates, views)
```

---

## Discretization System

### Purpose
Transform continuous variables into discrete bins for:
1. Interpretability - Easier to understand age 25-35 than raw age values
2. Stability - Bins are more stable than raw values over time
3. Regulatory compliance - Basel II/III requires interpretable models
4. Monotonicity - Can enforce monotonic relationship with outcome

### Binning Methods Implemented

#### 1. Equal Population Mass (Quantiles)
```python
# From discretiser_base.py
def calculate_quantile_edges(self, arr_values, numrecords, numbins):
    # Creates bins with equal number of records in each
    binsize = int(numrecords / numbins)
    bin_boundaryvals = [binsize * (idx+1) / numrecords for idx in range(numbins)]
    bin_edges = mstats.mquantiles(arr_values, bin_boundaryvals)
    return bin_edges
```

**Use Case:** Default method for creating scorecards - ensures each bin has enough observations

#### 2. Equal Width (Histogram)
```python
def calculate_histogram_edges(self, arr_values, numbins):
    # Creates bins with equal value range
    hist, bin_edges = np.histogram(arr_values, numbins)
    return bin_edges
```

**Use Case:** When you want evenly spaced bins (e.g., age: 0-10, 10-20, 20-30...)

### Bin Types Supported

**Numeric Bins:**
1. `DFBIN_TYPE_NUMRANGE` - Normal bins: [25, 35), [35, 45)
2. `DFBIN_TYPE_SPECIAL` - Special values: -999, -99, etc.
3. `DFBIN_TYPE_MINOVERFLOW` - Low overflow: [LOW, min_value)
4. `DFBIN_TYPE_MAXOVERFLOW` - High overflow: [max_value, HIGH]

**Character Bins:**
1. `DFBIN_TYPE_CHARVALUE` - Specific values: IN ('CA', 'NY', 'TX')
2. `DFBIN_TYPE_CHAROVERFLOW` - Everything else: NOT IN (...)
3. `DFBIN_TYPE_CHAROTHER` - Aggregated low-frequency values

### Database Schema for Bins

```python
# Django models (conceptual - actual code not shown)
class DatafieldTransform(Model):
    datafieldtransform_id = AutoField(primary_key=True)
    datafieldtransformname = CharField(max_length=200)
    datafield = ForeignKey(DataField)
    numbins = IntegerField()
    binning_method = CharField()  # 'quantile' or 'histogram'

class DatafieldBin(Model):
    datafieldbin_id = AutoField(primary_key=True)
    datafieldtransform = ForeignKey(DatafieldTransform)
    datafieldbinname = CharField()  # "01. [25 - 35)"
    datafieldbintype = CharField()  # NUMRANGE, SPECIAL, etc.
    datafieldbinminval = FloatField(null=True)
    datafieldbinmaxval = FloatField(null=True)
    datafieldbinminexc = BooleanField()  # Exclude min?
    datafieldbinmaxexc = BooleanField()  # Exclude max?
    datafieldbinnumber = IntegerField()  # Sort order

class DatafieldBinValue(Model):
    datafieldbinvalue_id = AutoField(primary_key=True)
    datafieldbin = ForeignKey(DatafieldBin)
    bincharvalue = CharField()  # For character bins: 'CA', 'NY', etc.
```

**Problem:** Bins are stored in database, not derived on-the-fly!

---

## Query Builder System

### Purpose
Dynamically generate SQL CASE statements based on database bin definitions.

### SQL CASE Statement Generation

```python
# From query_datafield.py:buildsql_datafieldtransform_case()

def buildsql_datafieldtransform_case(self, datafieldtransform_id, varname_suffix=''):
    """
    Queries database for bin definitions, builds SQL CASE statement

    Output:
    CASE
        WHEN age >= 25 AND age < 35 THEN '01. [25 - 35)'
        WHEN age >= 35 AND age < 45 THEN '02. [35 - 45)'
        WHEN age >= 45 AND age < 55 THEN '03. [45 - 55)'
        WHEN age >= 55 THEN '04. [55 - HIGH]'
        WHEN age < 25 THEN '00. [LOW - 25)'
        ELSE 'ERROR'
    END AS age_binned
    """

    # Fetch bin definitions from database
    resDatafieldBins = DatafieldBin.objects.filter(
        datafieldtransform_id=datafieldtransform_id
    )

    sql_case = ' CASE '

    # Loop through each bin and build WHEN clause
    for objDFBin in resDatafieldBins:
        if objDFBin.datafieldbintype == 'NUMRANGE':
            # Choose template based on exclusions
            if minexc == False and maxexc == False:
                sql_case += """
 WHEN {field} >= {min} AND {field} <= {max} THEN '{binname}'"""
            elif minexc == True and maxexc == False:
                sql_case += """
 WHEN {field} > {min} AND {field} <= {max} THEN '{binname}'"""
            # ... etc for all combinations

        elif objDFBin.datafieldbintype == 'CHARVALUE':
            # Build IN list from DatafieldBinValue table
            binvalues = DatafieldBinValue.objects.filter(
                datafieldbin_id=objDFBin.datafieldbin_id
            )
            char_list = convert_binvalueobjects_to_list(binvalues)
            sql_case += """
 WHEN {field} IN {char_list} THEN '{binname}'"""

    sql_case += """ ELSE 'ERROR' END AS {varname}"""

    return sql_case, varname
```

**Result:** A 1,041-line SQL string builder that reads bin definitions from database!

**Problem:** Every metric calculation requires:
1. Query database for bin definitions
2. Build SQL CASE statement
3. Execute main query with CASE statement
4. Calculate metric in Python
5. Store results back to database

---

## Data Model Coupling Issues

### Issue 1: Dimension Explosion

```python
# From metric_base.py:store_metric()

def store_metric(self, metricvalue,
                 obstime_id=None, obstime=None,
                 perftime_id=None, perftime=None,
                 vintagetime_id=None, vintagetime=None,
                 analysistime_id=None, analysistime=None,
                 predmodelsuite_id=None, predmodelsuite=None,
                 predmodel_id=None, predmodel=None,
                 outcome_id=None, outcome=None,
                 metric_id=None, metric=None,
                 scorebandsystem_id=None, scorebandsystem=None,
                 scoreband_id=None, scoreband=None,
                 subpopref_id=None, subpopref=None,
                 datafieldtransform_id=None, datafieldtransform=None,
                 datafieldbin_id=None, datafieldbin=None,
                 randomdigitband_id=None, randomdigitband=None,
                 component1='', component2='', component3='', component4='',
                 exception_ind=False, exception_reason=''):

    # Create or retrieve MetricReference with ALL these dimensions!
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

    # Then store the actual value
    objMetricValue, created = MetricValue.objects.get_or_create(
        metricreference_id=objMetricRef.pk,
        metriccomponentlev1=component1,
        metriccomponentlev2=component2,
        metriccomponentlev3=component3,
        metriccomponentlev4=component4
    )
    objMetricValue.metricvalue = metricvalue
    objMetricValue.save()
```

**Result:** 14 dimension objects + 4 component levels = 18 parameters to track ONE metric value!

**Problem:** Over-engineered for tracking every possible dimension of every metric calculation.

### Issue 2: Pre-defined Bin Systems Required

```python
# Before calculating ANY metric, must:

# 1. Create DatafieldTransform
objTransform = DatafieldTransform.objects.create(
    datafield_id=age_field_id,
    datafieldtransformname="Age Bands",
    numbins=10,
    binning_method="quantile"
)

# 2. Run discretizer to calculate bin edges
discretizer = DataFieldDiscretiser()
bin_edges = discretizer.calculate_quantile_edges(age_values, numrecords, 10)

# 3. Store bin definitions in database
discretizer.calculate_and_update_datafieldbins(
    objTransform.pk, bin_edges, numbins=10, precision=2, arr_specialvals=[]
)
# → Creates 10+ DatafieldBin records with min/max values

# 4. THEN can calculate metrics
engine = MetricEngine_IV()
engine.calc_IV_datafield(
    datafieldtransform_id=objTransform.pk,
    outcome_id=default_outcome_id,
    obstime_id=base_obstime_id
)
```

**Problem:** Can't calculate metrics ad-hoc - must pre-define and store bin systems!

### Issue 3: SQL Generation Complexity

**Current approach:**
```python
# 1. Fetch bin definitions from DB
bins = DatafieldBin.objects.filter(datafieldtransform_id=123)

# 2. Build 200+ line SQL CASE statement
sql_case = "CASE "
for bin in bins:
    sql_case += f"WHEN field >= {bin.min} AND field < {bin.max} THEN '{bin.name}' "
sql_case += "ELSE 'ERROR' END"

# 3. Embed in larger query
sql = f"""
SELECT {sql_case} as age_bin,
       SUM(outcome) as bad,
       COUNT(*) as total
FROM predictions
GROUP BY age_bin
"""

# 4. Execute
cursor.execute(sql)
results = cursor.fetchall()

# 5. Calculate metric in Python
iv = calculate_iv_from_results(results)
```

**Complexity:** 1,041 lines of SQL string building code!

---

## What Went Wrong (User's Retrospective)

### ❌ Mistake 1: Database-First Design
**Problem:** Made bins a database entity instead of a data transformation

**Should have been:** Bins are derived on-the-fly from data, not stored

### ❌ Mistake 2: Django Model Coupling
**Problem:** Everything depends on Django ORM models

**Should have been:** Pure Python/SQL that works with any database or dataframe

### ❌ Mistake 3: Dimension Model Explosion
**Problem:** 14 dimensions to track every metric calculation

**Should have been:** Let users manage their own dimensions with standard dataframe operations

### ❌ Mistake 4: SQL String Building
**Problem:** 1,000+ lines of code to build SQL strings from database objects

**Should have been:** Expression system that compiles to SQL/backend operations

### ❌ Mistake 5: Required Pre-configuration
**Problem:** Must set up bin systems before calculating metrics

**Should have been:** Ad-hoc calculation with optional auto-binning

---

## Lessons for mountainash-expressions

### ✅ Principle 1: Stateless Evaluation

**Don't:**
```python
# Create and store bin system
transform_id = create_bins_in_database(field="age", bins=10)

# Calculate metric using stored bins
iv = calculate_iv(datafieldtransform_id=transform_id)
```

**Do:**
```python
# Pure evaluation, no storage
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=10  # Auto-bin on the fly
).eval()(df)
```

### ✅ Principle 2: Dataframe-Agnostic

**Don't:**
```python
# Tied to specific database tables
from apps.input.models import DatafieldTransform
obj = DatafieldTransform.objects.get(pk=123)
```

**Do:**
```python
# Works with any dataframe
import polars as pl
import pandas as pd
import ibis

# All work the same way
iv_polars = ma.information_value(...).eval()(polars_df)
iv_pandas = ma.information_value(...).eval()(pandas_df)
iv_ibis = ma.information_value(...).eval()(ibis_table)
```

### ✅ Principle 3: Optional Auto-Binning

**Don't:**
```python
# Must pre-define bins in database
bin_system = create_bin_system(field="age", method="quantile", bins=10)
store_in_database(bin_system)
# ... later ...
metric = calculate_metric(bin_system_id=123)
```

**Do:**
```python
# Auto-bin with sensible defaults
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=10  # Auto quantile binning
)

# Or explicit bins
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=[0, 18, 25, 35, 45, 55, 65, 100]  # Custom edges
)

# Or work with pre-binned data
iv = ma.information_value(
    feature=col("age_bin"),  # Already binned
    target=col("default"),
    bins=None  # Use existing bins
)
```

### ✅ Principle 4: Expression Compilation

**Don't:**
```python
# Build SQL strings manually
sql = f"""
SELECT CASE
    WHEN age >= 25 AND age < 35 THEN '01'
    WHEN age >= 35 AND age < 45 THEN '02'
    ...
END as age_bin,
SUM(default) as bad,
COUNT(*) as total
FROM data
GROUP BY age_bin
"""
cursor.execute(sql)
```

**Do:**
```python
# Let expression system handle it
iv_expr = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=10
)

# Compiles to backend-appropriate SQL/operations
result = iv_expr.eval()(df)  # Polars? Ibis? Pandas? Doesn't matter!
```

### ✅ Principle 5: No Required Infrastructure

**Don't:**
```python
# Setup required
python manage.py migrate  # Create DB tables
python manage.py createsuperuser  # Create admin user
# Log in to admin panel
# Create ClientProject
# Create ObservationTime windows
# Create PerformanceTime windows
# Create DataField definitions
# Create Outcome definitions
# Create Metric definitions
# THEN can use the framework!
```

**Do:**
```python
# Just works
import mountainash_expressions as ma

result = ma.gini(
    prediction=col("pred"),
    actual=col("actual")
).eval()(df)

# That's it!
```

---

## Discretization Simplification Strategy

### Current Complexity (904 lines)

```python
# From discretiser_datafield.py

class DataFieldDiscretiser(BaseDiscretiser):

    def calculate_and_update_datafieldbins(
        self, datafieldtransform_id, bin_edges, numbins,
        precision, arr_specialvals
    ):
        # 1. Delete existing bins from database
        DatafieldBin.objects.filter(
            datafieldtransform_id=datafieldtransform_id
        ).delete()

        # 2. Handle special values
        if len(arr_specialvals) > 0:
            # Create special value bin
            # Create MIN overflow bin
            # Create bridge bin from special val to first real val
            # ... 50+ lines of logic

        # 3. Create regular bins
        for idx in range(numbins):
            binname = f"{idx:02d}. [{bin_edges[idx]} - {bin_edges[idx+1]})"
            DatafieldBin.objects.create(
                datafieldtransform_id=datafieldtransform_id,
                datafieldbinname=binname,
                datafieldbintype='NUMRANGE',
                datafieldbinminval=bin_edges[idx],
                datafieldbinmaxval=bin_edges[idx+1],
                datafieldbinminexc=False,
                datafieldbinmaxexc=True,
                datafieldbinnumber=idx
            )

        # 4. Create MAX overflow bin
        # 5. Handle character bins
        # 6. Handle categorical aggregation
        # ... 200+ more lines
```

### Simplified for mountainash-expressions

```python
# Simple binning utility (not required, but helpful)

def auto_bin(column, bins=10, method='quantile', special_values=None):
    """
    Auto-bin a column for interpretability

    Args:
        column: Column expression
        bins: Number of bins or explicit bin edges
        method: 'quantile', 'equal_width', or 'custom'
        special_values: Optional list of special values to bin separately

    Returns:
        Binned column expression
    """
    if isinstance(bins, int):
        if method == 'quantile':
            edges = col(column).quantile(
                [i/bins for i in range(bins+1)]
            )
        elif method == 'equal_width':
            min_val = col(column).min()
            max_val = col(column).max()
            width = (max_val - min_val) / bins
            edges = [min_val + i*width for i in range(bins+1)]
    else:
        edges = bins  # Custom edges provided

    # Simple CASE expression
    return col(column).cut(
        breaks=edges,
        labels=[f"Bin {i}" for i in range(len(edges)-1)]
    )

# Usage
iv = ma.information_value(
    feature=auto_bin(col("age"), bins=10, method='quantile'),
    target=col("default")
)
```

**Result:** ~30 lines instead of 904!

---

## Recommended Simplifications

### For Phase 9A: Basic ML Metrics

**No binning needed!**
```python
# Precision, Recall, F1 work with raw predictions
precision = ma.precision(
    prediction=col("pred"),  # Binary 0/1
    actual=col("actual")     # Binary 0/1
)
# No bins, no database, no complexity!
```

### For Phase 9B: Gini/AUC

**No binning needed!**
```python
# Gini works with raw probabilities
gini = ma.gini(
    prediction=col("pred_proba"),  # Continuous 0-1
    actual=col("actual")            # Binary 0/1
)
# Ranking happens via window functions, no bins!
```

### For Phase 9C: Credit Risk Metrics

**Optional auto-binning:**
```python
# Information Value with auto-binning
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=10  # Auto-create equal-population bins
)

# Or explicit bins
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=[0, 18, 25, 35, 45, 55, 65, 100]
)

# Or work with pre-binned data
iv = ma.information_value(
    feature=col("age_group"),  # Already binned
    target=col("default")
)
```

**Implementation:**
- Binning logic: ~100 lines (vs. 904 lines)
- No database storage
- Derived on-the-fly from data

---

## Framework Component Reusability

### ✅ Reuse: Binning Algorithms

**What to keep:**
- Quantile calculation logic
- Histogram calculation logic
- Special value handling concept

**How to adapt:**
- Remove Django model dependencies
- Make it a pure function
- Return edges, don't store

### ✅ Reuse: Metric Formulas

**What to keep:**
- Gini calculation: `(sum(rect) * 0.5) + sum(tri) - 0.5`
- IV calculation: `sum((pct_good - pct_bad) * WoE)`
- PSI calculation: `sum((pct_analysis - pct_base) * log(pct_analysis / pct_base))`

**How to adapt:**
- Use window functions for cumulative sums
- Let backend do GROUP BY, not Python loops
- No database storage

### ❌ Don't Reuse: Infrastructure

**What to abandon:**
- Dimension model (14 dimension objects)
- MetricReference/MetricValue storage
- SQL string builders
- Django ORM coupling
- Required pre-configuration

---

## Size Comparison: Current vs. Simplified

### Current Framework
```
Discretization:    1,321 lines
Query Builders:    1,537 lines
Metrics:           1,321 lines
Models/Admin:      ~500 lines (estimated)
TOTAL:            ~4,679 lines
```

### Simplified mountainash-expressions (Estimated)

```
Phase 9A (Basic Metrics):
- Precision, Recall, F1, Accuracy:     ~50 lines
- RMSE, MAE, Log Loss:                 ~30 lines
SUBTOTAL:                              ~80 lines

Phase 9B (Ranking Metrics):
- Gini/AUC (uses window functions):    ~100 lines
SUBTOTAL:                              ~100 lines

Phase 9C (Credit Risk - Optional):
- Auto-binning utility:                ~100 lines
- Information Value:                   ~80 lines
- PSI:                                 ~60 lines
- WoE:                                 ~40 lines
SUBTOTAL:                              ~280 lines

TOTAL:                                 ~460 lines
```

**Result:** 10x reduction in code size (4,679 → 460 lines)

**Achieved through:**
- No database coupling
- No dimension model
- No SQL string building
- Window functions instead of Python loops
- Stateless evaluation

---

## Summary

### What User Built (The Hard Way)
1. ✅ Comprehensive credit risk framework
2. ✅ Sophisticated discretization system
3. ✅ Working metric calculations
4. ❌ Tightly coupled to Django/database
5. ❌ Required extensive pre-configuration
6. ❌ 4,679 lines of complex infrastructure code

### What mountainash-expressions Should Build (The Simple Way)
1. ✅ Pure expression evaluation
2. ✅ Optional auto-binning (not required)
3. ✅ Dataframe-agnostic
4. ✅ Stateless, functional API
5. ✅ ~460 lines vs. 4,679 lines (10x reduction)

### Key Takeaways

**Do:**
- Make binning optional, not required
- Let backend do GROUP BY and window functions
- Work directly with dataframes
- Keep it stateless and functional
- Provide sensible defaults

**Don't:**
- Store bins in database
- Build SQL strings manually
- Create complex dimension models
- Require pre-configuration
- Couple to specific frameworks (Django, etc.)

**The Goal:**
```python
# This simple interface
iv = ma.information_value(
    feature=col("age"),
    target=col("default"),
    bins=10
).eval()(df)

# Instead of this complexity
transform_id = create_and_store_bins(field="age", method="quantile", bins=10)
iv = calculate_iv_with_stored_bins(
    datafieldtransform_id=transform_id,
    outcome_id=default_outcome_id,
    obstime_id=base_obstime_id,
    perftime_id=perf_time_id
)
```

---

**Document Created:** 2025-11-09
**Source Code:** /home/nathanielramm/Downloads/framework/ (~4,679 lines)
**Lesson:** User's working implementation validates the approach, but shows what NOT to do (database coupling, complexity, required infrastructure)
**Next Steps:** Build mountainash-expressions Phase 9 with clean, stateless design
