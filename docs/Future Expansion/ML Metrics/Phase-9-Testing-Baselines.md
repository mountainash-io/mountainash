# Phase 9 Testing Baselines: Canonical Reference Implementations

**Created:** 2025-01-09
**Purpose:** Define canonical baseline packages for validating ML/Statistical metrics implementations

This document identifies the "gold standard" reference implementations for each metric in Phase 9, enabling rigorous testing and validation of mountainash-expressions implementations.

---

## Overview

Each Phase 9 metric implementation must be tested against trusted canonical implementations to ensure correctness. This document specifies which packages/functions serve as the baseline for each metric.

### Testing Approach

```python
# General testing pattern
import numpy as np
from sklearn.metrics import <canonical_function>
from mountainash_expressions import ma, col

# Generate test data
actual = np.array([0, 1, 1, 0, 1])
prediction = np.array([0, 1, 0, 1, 1])

# Calculate with canonical implementation
expected = <canonical_function>(actual, prediction)

# Calculate with mountainash-expressions
df = pd.DataFrame({'actual': actual, 'pred': prediction})
result = ma.<metric>(col('actual'), col('pred')).eval()(df)

# Assert match (within tolerance for floating point)
assert np.isclose(result, expected, rtol=1e-5)
```

---

## Phase 9A: Classification Metrics

### Primary Canonical Package: **scikit-learn** (sklearn.metrics)

**Why scikit-learn?**
- Industry standard for ML metrics (14 years of development, 2011 paper)
- Extensively tested and validated
- Used by millions of practitioners worldwide
- Reference implementation for textbooks and courses
- Well-documented edge case handling

**Version Pinning:**
```python
# Recommended for testing
scikit-learn>=1.3.0,<2.0.0
```

### Secondary Validation Package: **scores** (scores.categorical)

**Why scores?**
- Peer-reviewed implementation (JOSS 2024, NCI Australia)
- Independent implementation = additional validation confidence
- Implements same metrics with forecast verification terminology
- Uses xarray for multidimensional data (different calculation approach)
- 60+ metrics including all Phase 9A functions

**Citation:**
```
Leeuwenburg et al. (2024) "scores: A Python package for verifying and 
evaluating models and predictions with xarray", Journal of Open Source 
Software, 9(99), 6889. https://doi.org/10.21105/joss.06889
```

**Key terminology differences:**
- **Precision** → "Success Ratio" or "Positive Predictive Value" (PPV)
- **Recall** → "Hit Rate" / "Probability of Detection (POD)" / "True Positive Rate"
- **F1 Score** → "F1 Score" (same name)
- **Accuracy** → "Fraction Correct" or "Accuracy"

**Version Pinning:**
```python
# Optional for additional validation
scores>=1.0.0
```

**Documentation:** 
- GitHub: https://github.com/nci/scores
- Docs: https://scores.readthedocs.io/
- Paper: https://joss.theoj.org/papers/10.21105/joss.06889

**Use Case:** Cross-validate against sklearn to ensure implementation correctness across different calculation approaches and data structures (pandas vs xarray).

**Testing Strategy:**
```python
from sklearn.metrics import precision_score, recall_score
import scores.categorical as cat_scores
import xarray as xr

# sklearn (primary baseline)
sklearn_precision = precision_score(y_true, y_pred)
sklearn_recall = recall_score(y_true, y_pred)

# scores (secondary validation) - requires xarray format
# Convert to xarray DataArrays for scores package
obs_xr = xr.DataArray(y_true)
fcst_xr = xr.DataArray(y_pred)

# scores uses BinaryContingencyManager
# (API differs - see scores documentation)

# Both implementations should agree with mountainash-expressions
ma_precision = ma.precision(col('actual'), col('pred')).eval()(df)
assert np.isclose(ma_precision, sklearn_precision, rtol=1e-5)
```

**Note:** scores is optional - sklearn remains the primary baseline. Use scores for additional confidence when debugging edge cases or validating against independent implementations.

**Additional Metrics in scores (beyond Phase 9A):**
- Cohen's Kappa (Heidke Skill Score)
- Critical Success Index (Threat Score)
- Equitable Threat Score
- True Skill Statistic
- Symmetric Extremal Dependence Index (SEDI)
- Odds Ratio Skill Score

These could inform future phases beyond basic classification metrics.


### Metric-by-Metric Baselines

#### 1. Precision

**Primary:** `sklearn.metrics.precision_score`
**Secondary:** `scores.categorical` (as "Success Ratio" or "PPV")

```python
from sklearn.metrics import precision_score

# Binary classification
precision = precision_score(y_true, y_pred)

# Formula: TP / (TP + FP)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html

**Testing Notes:**
- Test with perfect predictions (precision = 1.0)
- Test with all positive predictions
- Edge case: All predictions are 0 → undefined (sklearn returns 0.0 with warning)

#### 2. Recall

**Primary:** `sklearn.metrics.recall_score`
**Secondary:** `scores.categorical` (as "Hit Rate" or "POD")

```python
from sklearn.metrics import recall_score

# Binary classification
recall = recall_score(y_true, y_pred)

# Formula: TP / (TP + FN)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html

**Testing Notes:**
- Test with perfect predictions (recall = 1.0)
- Edge case: No positive samples in y_true → undefined (sklearn returns 0.0 with warning)

#### 3. F1 Score

**Primary:** `sklearn.metrics.f1_score`
**Secondary:** `scores.categorical.f_score()`

```python
from sklearn.metrics import f1_score

# Binary classification
f1 = f1_score(y_true, y_pred)

# Formula: 2 * (precision * recall) / (precision + recall)
# Also: 2*TP / (2*TP + FP + FN)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html

**Testing Notes:**
- Verify F1 = harmonic mean of precision and recall
- Edge case: Both precision and recall are 0 → F1 = 0

#### 4. Accuracy

**Primary:** `sklearn.metrics.accuracy_score`
**Secondary:** `scores.categorical` (as "Fraction Correct")

```python
from sklearn.metrics import accuracy_score

# Binary classification
accuracy = accuracy_score(y_true, y_pred)

# Formula: (TP + TN) / (TP + TN + FP + FN)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html

---

## Phase 9B: Ranking Metrics

### Primary Canonical Package: **scikit-learn** (sklearn.metrics)

Same rationale as Phase 9A - industry standard implementation.

**Note:** The `scores` package focuses on categorical/continuous metrics, not probability-based ranking metrics like AUC.

### Polars-Specific Baseline: **polars_ds_extension**

**Why polars_ds?**
- **Polars-native implementation** - Written in Rust, optimized for Polars
- **Expression-based API** - Similar design philosophy to mountainash-expressions
- **Performance reference** - Can benchmark against highly optimized Rust implementation
- **Integration patterns** - Learn how to integrate metrics into Polars expression system

**Metrics Implemented:**
- ROC-AUC calculation
- Log loss
- WoE (Weight of Evidence) encoding (relevant for Phase 9C)
- Statistical tests (t-test, chi-square, F-test)

**Package:** `polars_ds_extension`
**GitHub:** https://github.com/abstractqqq/polars_ds_extension
**Docs:** https://polars-ds-extension.readthedocs.io/

**Installation:**
```bash
pip install polars-ds-extension
```

**Use Case:**
- **Primary:** Polars backend-specific validation
- **Secondary:** Performance benchmarking
- **Tertiary:** API design reference for Polars integration

**Testing Strategy:**
```python
import polars as pl
import polars_ds as pds
from sklearn.metrics import roc_auc_score

# Create Polars DataFrame
df = pl.DataFrame({
    'actual': y_true,
    'pred_proba': y_score
})

# sklearn (primary baseline - backend-agnostic)
sklearn_auc = roc_auc_score(y_true, y_score)

# polars_ds (Polars-specific baseline)
# (API may differ - check documentation)
# polars_ds_auc = df.select(pds.query_roc_auc(...))

# mountainash-expressions with Polars backend
ma_auc = ma.roc_auc(col('actual'), col('pred_proba')).eval()(df)

# All should agree
assert np.isclose(ma_auc, sklearn_auc, rtol=1e-5)
# Can also compare performance against polars_ds
```

**Key Advantages:**
1. **Rust performance** - Baseline for optimization targets
2. **Polars integration** - Shows best practices for Polars expression API
3. **Lazy evaluation** - Demonstrates efficient computation patterns
4. **Parallel computation** - Supports grouped aggregations

**Limitations:**
- Polars-specific (not general-purpose like sklearn)
- API may differ from sklearn conventions
- Less widely used (smaller community)

**Note:** polars_ds is **optional** for Polars backend validation only. sklearn remains the primary cross-backend baseline.

### Metric-by-Metric Baselines

#### 1. ROC-AUC

**Primary:** `sklearn.metrics.roc_auc_score`
**Secondary (Polars):** `polars_ds_extension` ROC-AUC

```python
from sklearn.metrics import roc_auc_score

# Binary classification with probability predictions
roc_auc = roc_auc_score(y_true, y_score)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html
**polars_ds docs:** https://polars-ds-extension.readthedocs.io/en/latest/metrics.html

**Alternative (for verification):** `sklearn.metrics.roc_curve` + `sklearn.metrics.auc`

```python
from sklearn.metrics import roc_curve, auc

fpr, tpr, thresholds = roc_curve(y_true, y_score)
roc_auc = auc(fpr, tpr)  # Should match roc_auc_score
```

**Testing Notes:**
- Test with perfect predictions (AUC = 1.0)
- Test with random predictions (AUC ≈ 0.5)
- Verify AUC interpretation: Probability that random positive ranks higher than random negative

#### 2. Gini Coefficient

**Canonical Calculation:** `2 * AUC - 1`

```python
from sklearn.metrics import roc_auc_score

# Gini coefficient
gini = 2 * roc_auc_score(y_true, y_score) - 1

# Range: -1 to 1
# Perfect model: Gini = 1.0
# Random model: Gini = 0.0
```

**Secondary Baseline:** Your legacy implementation (`metric_gini.py`)

**Testing Notes:**
- Verify Gini = 2*AUC - 1 identity holds
- Use your legacy implementation as additional verification
- Test edge cases: all same predictions, perfect separation

#### 3. Log Loss

**Primary:** `sklearn.metrics.log_loss`
**Secondary (Polars):** `polars_ds_extension` log loss

```python
from sklearn.metrics import log_loss

# Binary classification with probability predictions
logloss = log_loss(y_true, y_pred_proba)

# Formula: -1/N * sum(y*log(p) + (1-y)*log(1-p))
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html
**polars_ds docs:** https://polars-ds-extension.readthedocs.io/en/latest/metrics.html

---

## Phase 9C: Credit Risk Metrics

### Challenge: No Single Canonical Package

Multiple packages exist with variations. Multi-baseline approach recommended.

### Primary Baseline: **scorecardpy**

**Package:** `scorecardpy`
**GitHub:** https://github.com/ShichenXie/scorecardpy
**Why:** Most popular Python scorecard package, R port, industry usage

```bash
pip install scorecardpy
```

### Secondary Baselines

1. **Your Legacy Implementation** (2014-2016)
   - Location: `/home/nathanielramm/Downloads/metrics/`
   - Battle-tested in production
   - Domain expertise

2. **toad** (alternative package)
   - Chinese credit risk community standard
   - GitHub: https://github.com/amphibian-dev/toad

3. **polars_ds_extension** (for WoE only)
   - Polars-native WoE encoding
   - GitHub: https://github.com/abstractqqq/polars_ds_extension
   - Use for Polars backend validation

### Metric-by-Metric Baselines

#### 1. Information Value (IV)

**Primary:** `scorecardpy.iv()`

```python
import scorecardpy as sc

iv_table = sc.iv(df, y='target', x='feature')
total_iv = iv_table['total_iv'].iloc[0]
```

**Secondary:** Your legacy `metric_iv.py`

**Manual Calculation:**
```python
def information_value(df, feature, target, bins=10):
    """IV = sum((pct_good - pct_bad) * WoE)"""
    df['bin'] = pd.qcut(df[feature], bins, duplicates='drop')
    grouped = df.groupby('bin')[target].agg(['sum', 'count'])
    
    grouped['n_good'] = grouped['count'] - grouped['sum']
    grouped['n_bad'] = grouped['sum']
    
    total_good = grouped['n_good'].sum()
    total_bad = grouped['n_bad'].sum()
    
    grouped['pct_good'] = grouped['n_good'] / total_good
    grouped['pct_bad'] = grouped['n_bad'] / total_bad
    grouped['woe'] = np.log(grouped['pct_good'] / grouped['pct_bad'])
    grouped['iv'] = (grouped['pct_good'] - grouped['pct_bad']) * grouped['woe']
    
    return grouped['iv'].sum()
```

**IV Interpretation:**
- < 0.02: Not predictive
- 0.02 - 0.1: Weak
- 0.1 - 0.3: Medium
- 0.3 - 0.5: Strong
- \> 0.5: Suspicious (possible overfitting)

#### 2. Weight of Evidence (WoE)

**Primary:** `scorecardpy.woebin()` + `scorecardpy.woebin_ply()`
**Secondary:** Your legacy implementation
**Polars-specific:** `polars_ds_extension` WoE encoding

```python
import scorecardpy as sc

bins = sc.woebin(df, y='target', x=['feature1', 'feature2'])
df_woe = sc.woebin_ply(df, bins)
```

**polars_ds usage (for Polars backend):**
```python
import polars as pl
import polars_ds as pds

# WoE encoding in Polars
# (Check docs for exact API)
# df = df.with_columns(pds.woe_encode(...))
```

**Formula:**
```python
WoE = ln(pct_good / pct_bad)
```

**Testing Notes:**
- Verify natural log (ln) not log10
- Handle edge cases: pct_good = 0 or pct_bad = 0
- For Polars backend, compare against polars_ds implementation

#### 3. Population Stability Index (PSI)

**Primary Reference:** NannyML blog implementation
**URL:** https://www.nannyml.com/blog/population-stability-index-psi

```python
def psi(reference, monitored, bins=10):
    """
    PSI = sum((pct_monitored - pct_reference) * 
              ln(pct_monitored / pct_reference))
    
    Interpretation:
    - PSI < 0.1: No significant change
    - 0.1 <= PSI < 0.2: Moderate change
    - PSI >= 0.2: Significant change (model drift)
    """
    full_data = np.concatenate([reference, monitored])
    _, bin_edges = np.histogram(full_data, bins='doane')
    
    ref_hist, _ = np.histogram(reference, bins=bin_edges)
    mon_hist, _ = np.histogram(monitored, bins=bin_edges)
    
    ref_pct = ref_hist / np.sum(ref_hist)
    mon_pct = mon_hist / np.sum(mon_hist)
    
    # Avoid log(0)
    ref_pct = np.where(ref_pct == 0, 1e-6, ref_pct)
    mon_pct = np.where(mon_pct == 0, 1e-6, mon_pct)
    
    psi_values = (mon_pct - ref_pct) * np.log(mon_pct / ref_pct)
    return np.sum(psi_values)
```

**Secondary:** Your legacy `metric_psi.py`

**Testing Notes:**
- No sklearn implementation
- Test with identical distributions (PSI ≈ 0)
- Test with completely different distributions (PSI large)

#### 4. Marginal Information Value (MIV)

**Primary Baseline:** Your legacy `metric_avse.py`

No standard package - domain-specific to your framework.

---

## Summary Table

| Metric | Primary Baseline | Secondary Baseline | Version |
|--------|------------------|-------------------|---------|
| **Phase 9A** |
| Precision | sklearn.metrics | scores.categorical | >=1.3.0 |
| Recall | sklearn.metrics | scores.categorical | >=1.3.0 |
| F1 Score | sklearn.metrics | scores.categorical | >=1.3.0 |
| Accuracy | sklearn.metrics | scores.categorical | >=1.3.0 |
| **Phase 9B** |
| ROC-AUC | sklearn.metrics | polars_ds (Polars) | >=1.3.0 |
| Gini | 2*AUC - 1 | Your legacy code | - |
| Log Loss | sklearn.metrics | polars_ds (Polars) | >=1.3.0 |
| **Phase 9C** |
| IV | scorecardpy | Your legacy code | >=0.1.9 |
| WoE | scorecardpy | Your legacy + polars_ds | >=0.1.9 |
| PSI | NannyML formula | Your legacy code | - |
| MIV | Your legacy code | - | - |

---

## Recommended Test Dependencies

```toml
[tool.hatch.envs.test.dependencies]
# Phase 9A & 9B - Primary
scikit-learn = ">=1.3.0,<2.0.0"

# Phase 9A - Secondary (optional)
scores = ">=1.0.0"

# Phase 9B & 9C - Polars-specific (optional)
polars-ds-extension = "*"

# Phase 9C - Primary
scorecardpy = ">=0.1.9"

# Phase 9C - Alternative
toad = "*"

# General
numpy = ">=1.23.0"
pandas = ">=2.0.0"
polars = ">=1.0.0"  # For polars_ds_extension
xarray = ">=2023.0.0"  # For scores package
pytest = ">=7.0.0"
pytest-cov = "*"
```

---

## Testing Strategy

### Phase 9A: Dual-Baseline Validation

```python
import pytest
from sklearn.metrics import precision_score
import scores.categorical as cat_scores

def test_precision_dual_baseline():
    """Validate precision against both sklearn and scores"""
    y_true = [0, 1, 1, 0, 1]
    y_pred = [0, 1, 0, 1, 1]
    
    # Primary baseline (sklearn)
    sklearn_result = precision_score(y_true, y_pred)
    
    # Secondary baseline (scores) - if available
    # (scores API may differ)
    
    # mountainash-expressions
    df = pd.DataFrame({'actual': y_true, 'pred': y_pred})
    ma_result = ma.precision(col('actual'), col('pred')).eval()(df)
    
    # Both should match
    assert np.isclose(ma_result, sklearn_result, rtol=1e-5)
```

### Phase 9C: Multi-Baseline Approach

```python
def test_information_value_multi_baseline():
    """Validate IV against scorecardpy AND legacy code"""
    import scorecardpy as sc
    
    # Primary baseline
    sc_iv = sc.iv(df, y='target', x='feature')['total_iv'][0]
    
    # Secondary baseline (your legacy code)
    legacy_iv = calculate_iv_legacy(df, 'feature', 'target')
    
    # Manual calculation
    manual_iv = calculate_iv_manual(df, 'feature', 'target')
    
    # mountainash-expressions
    ma_iv = ma.information_value(
        col('target'), 
        col('feature'), 
        bins=10
    ).eval()(df)
    
    # All should agree (within tolerance)
    assert np.isclose(ma_iv, sc_iv, rtol=0.01)
    assert np.isclose(ma_iv, legacy_iv, rtol=0.01)
    assert np.isclose(ma_iv, manual_iv, rtol=0.01)
```

---

## References

### Phase 9A/9B
- **scikit-learn:** https://scikit-learn.org/stable/modules/model_evaluation.html
- **scikit-learn paper:** Pedregosa et al. (2011) JMLR
- **scores package:** Leeuwenburg et al. (2024) JOSS
- **scores docs:** https://scores.readthedocs.io/
- **polars_ds_extension:** https://github.com/abstractqqq/polars_ds_extension
- **polars_ds docs:** https://polars-ds-extension.readthedocs.io/

### Phase 9C
- **scorecardpy:** https://github.com/ShichenXie/scorecardpy
- **polars_ds_extension:** https://github.com/abstractqqq/polars_ds_extension (WoE encoding)
- **PSI reference:** https://www.nannyml.com/blog/population-stability-index-psi
- **Your legacy:** `/home/nathanielramm/Downloads/metrics/`

---

**Last Updated:** 2025-01-09
