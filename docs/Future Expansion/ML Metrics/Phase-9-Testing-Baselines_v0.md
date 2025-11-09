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

### Canonical Package: **scikit-learn** (sklearn.metrics)

**Why scikit-learn?**
- Industry standard for ML metrics (11 years of development, 2011 paper)
- Extensively tested and validated
- Used by millions of practitioners worldwide
- Reference implementation for textbooks and courses
- Well-documented edge case handling

**Version Pinning:**
```python
# Recommended for testing
scikit-learn>=1.3.0,<2.0.0
```

### Metric-by-Metric Baselines

#### 1. Precision

**Canonical Function:** `sklearn.metrics.precision_score`

```python
from sklearn.metrics import precision_score

# Binary classification
precision = precision_score(y_true, y_pred)

# Formula: TP / (TP + FP)
# mountainash-expressions must match exactly
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html

**Testing Notes:**
- Test with perfect predictions (precision = 1.0)
- Test with all positive predictions
- Test with all negative predictions
- Test with imbalanced classes
- Edge case: All predictions are 0 → undefined (sklearn returns 0.0 with warning)

#### 2. Recall

**Canonical Function:** `sklearn.metrics.recall_score`

```python
from sklearn.metrics import recall_score

# Binary classification
recall = recall_score(y_true, y_pred)

# Formula: TP / (TP + FN)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html

**Testing Notes:**
- Test with perfect predictions (recall = 1.0)
- Test when no positives are predicted
- Test with all samples positive
- Edge case: No positive samples in y_true → undefined (sklearn returns 0.0 with warning)

#### 3. F1 Score

**Canonical Function:** `sklearn.metrics.f1_score`

```python
from sklearn.metrics import f1_score

# Binary classification
f1 = f1_score(y_true, y_pred)

# Formula: 2 * (precision * recall) / (precision + recall)
# Harmonic mean of precision and recall
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html

**Testing Notes:**
- Test with perfect predictions (f1 = 1.0)
- Test with zero precision or recall (f1 = 0.0)
- Verify F1 = 2*TP / (2*TP + FP + FN)
- Edge case: Both precision and recall are 0 → F1 = 0

#### 4. Accuracy

**Canonical Function:** `sklearn.metrics.accuracy_score`

```python
from sklearn.metrics import accuracy_score

# Binary classification
accuracy = accuracy_score(y_true, y_pred)

# Formula: (TP + TN) / (TP + TN + FP + FN)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html

**Testing Notes:**
- Test with perfect predictions (accuracy = 1.0)
- Test with random predictions
- Test with all wrong predictions (accuracy = 0.0)
- Simplest metric - least edge cases

#### 5. Confusion Matrix

**Canonical Function:** `sklearn.metrics.confusion_matrix`

```python
from sklearn.metrics import confusion_matrix

# Binary classification
cm = confusion_matrix(y_true, y_pred)
# Returns 2x2 matrix:
# [[TN, FP],
#  [FN, TP]]

tn, fp, fn, tp = cm.ravel()
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html

**Testing Notes:**
- Verify matrix structure matches sklearn convention
- All metrics can be derived from confusion matrix
- Test with single class (edge case)

### Comprehensive Testing

**Use classification_report for validation:**

```python
from sklearn.metrics import classification_report

# Get all metrics at once
report = classification_report(y_true, y_pred, output_dict=True)

# Validate against mountainash-expressions
assert np.isclose(
    ma.precision(col('actual'), col('pred')).eval()(df),
    report['1']['precision']
)
```

---

## Phase 9B: Ranking Metrics

### Canonical Package: **scikit-learn** (sklearn.metrics)

Same rationale as Phase 9A - industry standard implementation.

### Metric-by-Metric Baselines

#### 1. ROC-AUC

**Canonical Function:** `sklearn.metrics.roc_auc_score`

```python
from sklearn.metrics import roc_auc_score

# Binary classification with probability predictions
roc_auc = roc_auc_score(y_true, y_score)

# y_score should be probabilities (0.0 to 1.0)
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html

**Alternative (for verification):** `sklearn.metrics.roc_curve` + `sklearn.metrics.auc`

```python
from sklearn.metrics import roc_curve, auc

# Calculate ROC curve
fpr, tpr, thresholds = roc_curve(y_true, y_score)

# Calculate AUC from ROC curve
roc_auc = auc(fpr, tpr)

# Should match roc_auc_score
```

**Testing Notes:**
- Test with perfect predictions (AUC = 1.0)
- Test with random predictions (AUC ≈ 0.5)
- Test with inverse predictions (AUC = 0.0)
- Test with ties in predictions
- Verify AUC interpretation: Probability that a random positive sample ranks higher than a random negative sample

#### 2. Gini Coefficient

**Canonical Calculation:** `2 * AUC - 1`

```python
from sklearn.metrics import roc_auc_score

# Gini coefficient
gini = 2 * roc_auc_score(y_true, y_score) - 1

# Range: -1 to 1
# Perfect model: Gini = 1.0
# Random model: Gini = 0.0
# Inverse model: Gini = -1.0
```

**No direct sklearn function** - but formula is canonical in credit risk literature.

**Alternative verification (manual calculation):**

```python
import numpy as np

def gini_manual(y_true, y_score):
    """Manual Gini calculation for verification"""
    # Sort by prediction score (descending)
    sorted_indices = np.argsort(y_score)[::-1]
    y_sorted = y_true[sorted_indices]

    # Cumulative sums
    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)

    cum_pos = np.cumsum(y_sorted == 1)
    cum_neg = np.cumsum(y_sorted == 0)

    # Calculate area between curves
    # (This is a simplified version - full implementation in your legacy code)
    gini = (np.sum(cum_pos[:-1] * (cum_neg[1:] - cum_neg[:-1])) / (n_pos * n_neg)) * 2 - 1

    return gini

# Should match 2*AUC - 1
```

**Testing Notes:**
- Verify Gini = 2*AUC - 1 identity holds
- Use your legacy implementation from 2014-2016 as additional verification
- Test edge cases: all same predictions, perfect separation

#### 3. Log Loss (Binary Cross-Entropy)

**Canonical Function:** `sklearn.metrics.log_loss`

```python
from sklearn.metrics import log_loss

# Binary classification with probability predictions
logloss = log_loss(y_true, y_pred_proba)

# Formula: -1/N * sum(y*log(p) + (1-y)*log(1-p))
```

**Documentation:** https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html

**Testing Notes:**
- Test with perfect predictions (log_loss → 0)
- Test with probability = 0.5 for all
- Test edge case: probability = 0.0 or 1.0 (sklearn clips to avoid log(0))
- Verify sklearn uses natural log (ln)

---

## Phase 9C: Credit Risk Metrics

### Challenge: No Single Canonical Package

Unlike Phase 9A/9B, credit risk metrics don't have a universally accepted canonical implementation. Multiple packages exist with slight variations.

### Primary Baseline Options

#### Option 1: **scorecardpy** (Recommended)

**Package:** `scorecardpy`
**GitHub:** https://github.com/ShichenXie/scorecardpy
**PyPI:** https://pypi.org/project/scorecardpy/

**Why scorecardpy?**
- Most popular Python scorecard package (R port)
- Implements WoE, IV, PSI
- Active maintenance (last updated 2023)
- Good documentation
- Used in industry

**Installation:**
```bash
pip install scorecardpy
```

**Limitations:**
- Focuses on binning and WoE transformation
- PSI implementation exists but less documented
- Not as comprehensive as your 2014-2016 implementation

#### Option 2: **toad** (Alternative)

**Package:** `toad`
**GitHub:** https://github.com/amphibian-dev/toad

**Why toad?**
- Chinese credit risk community standard
- Comprehensive feature selection tools
- IV and stepwise selection built-in

**Installation:**
```bash
pip install toad
```

#### Option 3: **Your Legacy Implementation** (2014-2016)

**Location:** `/home/nathanielramm/Downloads/metrics/`

**Why use your own code as baseline?**
- Battle-tested in production for years
- You understand the edge cases and assumptions
- Matches your domain expertise
- Can serve as additional verification

**Approach:**
1. Extract calculation logic from Django dependencies
2. Create standalone functions
3. Use as reference alongside scorecardpy

### Metric-by-Metric Baselines

#### 1. Information Value (IV)

**Primary Baseline:** `scorecardpy.iv()`

```python
import scorecardpy as sc

# Calculate IV for a single feature
iv_table = sc.iv(df, y='target', x='feature')

# Returns DataFrame with bins and IV values
total_iv = iv_table['total_iv'].iloc[0]
```

**Secondary Baseline:** Your legacy `metric_iv.py`

**Manual Calculation (for verification):**

```python
def information_value(df, feature, target, bins=10):
    """
    IV = sum((pct_good - pct_bad) * WoE)
    where WoE = ln(pct_good / pct_bad)
    """
    # Bin the feature
    df['bin'] = pd.qcut(df[feature], bins, duplicates='drop')

    # Calculate good/bad rates per bin
    grouped = df.groupby('bin')[target].agg(['sum', 'count'])
    grouped['n_good'] = grouped['count'] - grouped['sum']
    grouped['n_bad'] = grouped['sum']

    total_good = grouped['n_good'].sum()
    total_bad = grouped['n_bad'].sum()

    grouped['pct_good'] = grouped['n_good'] / total_good
    grouped['pct_bad'] = grouped['n_bad'] / total_bad

    # Calculate WoE
    grouped['woe'] = np.log(grouped['pct_good'] / grouped['pct_bad'])

    # Calculate IV
    grouped['iv'] = (grouped['pct_good'] - grouped['pct_bad']) * grouped['woe']

    return grouped['iv'].sum()
```

**IV Interpretation:**
- < 0.02: Not predictive
- 0.02 - 0.1: Weak
- 0.1 - 0.3: Medium
- 0.3 - 0.5: Strong
- \> 0.5: Suspicious (possible overfitting)

**Testing Notes:**
- Compare with scorecardpy
- Compare with your legacy implementation
- Verify IV > 0 always (by construction)
- Test with different binning strategies

#### 2. Weight of Evidence (WoE)

**Primary Baseline:** `scorecardpy.woebin()` + `scorecardpy.woebin_ply()`

```python
import scorecardpy as sc

# Create bins and calculate WoE
bins = sc.woebin(df, y='target', x=['feature1', 'feature2'])

# Apply WoE transformation
df_woe = sc.woebin_ply(df, bins)
```

**Manual Calculation:**

```python
def weight_of_evidence(pct_good, pct_bad):
    """
    WoE = ln(pct_good / pct_bad)

    Interpretation:
    - WoE > 0: More goods than bads (lower risk)
    - WoE < 0: More bads than goods (higher risk)
    - WoE = 0: Equal distribution
    """
    return np.log(pct_good / pct_bad)
```

**Testing Notes:**
- Verify ln (natural log) not log10
- Test edge cases: pct_good = 0 or pct_bad = 0 (undefined)
- Your legacy code handles this with smoothing
- Compare with scorecardpy's approach

#### 3. Population Stability Index (PSI)

**Primary Baseline:** Custom implementation (no standard package)

**Reference Implementation:** NannyML blog post
- URL: https://www.nannyml.com/blog/population-stability-index-psi
- Provides canonical formula and implementation

```python
def psi(reference, monitored, bins=10):
    """
    PSI = sum((pct_monitored - pct_reference) * ln(pct_monitored / pct_reference))

    Interpretation:
    - PSI < 0.1: No significant change
    - 0.1 <= PSI < 0.2: Moderate change
    - PSI >= 0.2: Significant change (model drift)
    """
    # Use same bin edges for both
    full_data = np.concatenate([reference, monitored])
    _, bin_edges = np.histogram(full_data, bins='doane')

    # Calculate histograms
    ref_hist, _ = np.histogram(reference, bins=bin_edges)
    mon_hist, _ = np.histogram(monitored, bins=bin_edges)

    # Convert to proportions
    ref_pct = ref_hist / np.sum(ref_hist)
    mon_pct = mon_hist / np.sum(mon_hist)

    # Avoid log(0)
    ref_pct = np.where(ref_pct == 0, 1e-6, ref_pct)
    mon_pct = np.where(mon_pct == 0, 1e-6, mon_pct)

    # Calculate PSI
    psi_values = (mon_pct - ref_pct) * np.log(mon_pct / ref_pct)

    return np.sum(psi_values)
```

**Secondary Baseline:** Your legacy `metric_psi.py`

**Testing Notes:**
- No sklearn implementation
- Use NannyML formula as primary reference
- Your legacy code as secondary verification
- Test with identical distributions (PSI ≈ 0)
- Test with completely different distributions (PSI large)

#### 4. Marginal Information Value (MIV)

**Primary Baseline:** Your legacy `metric_avse.py`

**No standard package** - this is domain-specific to your 2014-2016 framework.

**Approach:**
1. Extract calculation from your legacy code
2. Create standalone reference function
3. Use as primary baseline (you're the expert!)

**Testing Notes:**
- Document the formula clearly
- Explain the interpretation
- This may be unique to your framework

---

## Additional Testing Resources

### 1. Synthetic Data Generators

**For Phase 9A/9B:**
```python
from sklearn.datasets import make_classification

# Generate synthetic binary classification data
X, y = make_classification(
    n_samples=1000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    n_classes=2,
    weights=[0.7, 0.3],  # Imbalanced
    random_state=42
)
```

**For Phase 9C (credit risk):**
```python
# Generate feature with known IV
def generate_feature_with_iv(n_samples, target_iv, random_state=42):
    """
    Generate a feature with approximately target_iv
    Useful for testing IV calculations
    """
    # Implementation based on reverse-engineering IV formula
    pass
```

### 2. Edge Case Test Suite

**Create comprehensive test suite:**

```python
import pytest

class TestPhase9AMetrics:
    """Test classification metrics against sklearn baselines"""

    def test_precision_perfect_predictions(self):
        """Precision = 1.0 when all predictions correct"""
        pass

    def test_precision_all_positive_predictions(self):
        """Edge case: all predictions are positive"""
        pass

    def test_recall_no_positive_predictions(self):
        """Edge case: no positive predictions"""
        pass

    # ... more tests
```

### 3. Numerical Tolerance

**Floating-point comparisons:**

```python
# Use numpy's isclose for robust comparison
np.isclose(result, expected, rtol=1e-5, atol=1e-8)

# For metrics that should be exact (confusion matrix):
np.array_equal(result, expected)
```

---

## Testing Strategy

### Phase 9A: Classification Metrics

1. **Unit tests** against sklearn for each metric
2. **Integration test** using `classification_report`
3. **Property-based testing** (e.g., F1 = harmonic mean of precision/recall)
4. **Edge case testing** (all same class, perfect predictions, etc.)

### Phase 9B: Ranking Metrics

1. **Unit tests** against sklearn for ROC-AUC
2. **Mathematical identity tests** (Gini = 2*AUC - 1)
3. **Your legacy code verification** for Gini
4. **Monotonicity tests** (better predictions → higher AUC)

### Phase 9C: Credit Risk Metrics

1. **Multi-baseline approach:**
   - Primary: scorecardpy (WoE, IV)
   - Secondary: Your legacy code (all metrics)
   - Tertiary: Manual calculations
2. **Cross-validation** between baselines
3. **Domain expert review** (you!)
4. **Real-world data testing** (if available)

---

## Recommended Test Dependencies

```toml
[tool.hatch.envs.test.dependencies]
scikit-learn = ">=1.3.0,<2.0.0"  # Phase 9A, 9B
scorecardpy = ">=0.1.9"           # Phase 9C (IV, WoE)
toad = "*"                         # Phase 9C (alternative)
numpy = ">=1.23.0"
pandas = ">=2.0.0"
pytest = ">=7.0.0"
pytest-cov = "*"
```

---

## Documentation Requirements

For each metric, document:

1. **Canonical baseline** - which package/function
2. **Formula** - mathematical definition
3. **Test approach** - how we validate
4. **Edge cases** - what special cases to handle
5. **Interpretation** - what the metric means
6. **Tolerance** - acceptable numerical difference

---

## Summary Table

| Metric | Baseline Package | Function | Version |
|--------|------------------|----------|---------|
| **Phase 9A** |
| Precision | scikit-learn | `sklearn.metrics.precision_score` | >=1.3.0 |
| Recall | scikit-learn | `sklearn.metrics.recall_score` | >=1.3.0 |
| F1 Score | scikit-learn | `sklearn.metrics.f1_score` | >=1.3.0 |
| Accuracy | scikit-learn | `sklearn.metrics.accuracy_score` | >=1.3.0 |
| Confusion Matrix | scikit-learn | `sklearn.metrics.confusion_matrix` | >=1.3.0 |
| **Phase 9B** |
| ROC-AUC | scikit-learn | `sklearn.metrics.roc_auc_score` | >=1.3.0 |
| Gini | (formula) | `2 * roc_auc_score(...) - 1` | - |
| Log Loss | scikit-learn | `sklearn.metrics.log_loss` | >=1.3.0 |
| **Phase 9C** |
| Information Value | scorecardpy + legacy | `scorecardpy.iv()` | >=0.1.9 |
| Weight of Evidence | scorecardpy + legacy | `scorecardpy.woebin()` | >=0.1.9 |
| PSI | NannyML + legacy | (custom implementation) | - |
| Marginal IV | legacy | (your implementation) | - |

---

## References

### Phase 9A/9B
- **scikit-learn documentation:** https://scikit-learn.org/stable/modules/model_evaluation.html
- **Metrics API reference:** https://scikit-learn.org/stable/modules/classes.html#module-sklearn.metrics
- **Original paper:** Pedregosa et al. (2011) "Scikit-learn: Machine Learning in Python", JMLR

### Phase 9C
- **scorecardpy GitHub:** https://github.com/ShichenXie/scorecardpy
- **PSI reference:** https://www.nannyml.com/blog/population-stability-index-psi
- **Credit Risk Scorecards book:** Naeem Siddiqi (referenced in research)
- **Your legacy implementation:** `/home/nathanielramm/Downloads/metrics/`

---

**Next Steps:**

1. Install baseline packages in test environment
2. Create test fixtures with known values
3. Implement tests for each metric
4. Document any discrepancies or design decisions
5. Get domain expert (you!) review for Phase 9C

**Last Updated:** 2025-01-09
