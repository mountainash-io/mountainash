"""
Cross-backend tests for ternary logic operations.

Tests three-valued logic operations where:
- TRUE = 1 (internal sentinel)
- UNKNOWN = 0 (internal sentinel)
- FALSE = -1 (internal sentinel)

IMPORTANT: The -1/0/1 values are INTERNAL SENTINELS only.
Users work with real-world data (including NULLs), and ternary comparisons
PRODUCE these values internally. The values help us reason about uncertainty
in data - they don't replace the data itself.

Typical workflow:
1. Real data with NULLs representing unknown values
2. Ternary comparisons (t_gt, t_eq, etc.) produce ternary results
3. Ternary logical ops (t_and, t_or) combine multiple conditions
4. Booleanizers (is_true, maybe_true) convert to boolean for filtering

All tests run across backends: Polars, Narwhals, and Ibis (Polars/DuckDB).
"""

import pytest
import mountainash.expressions as ma


# Ternary constant values for assertions (internal sentinels)
T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1


# =============================================================================
# Cross-Backend Tests - Ternary Comparisons
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTernaryComparisons:
    """Test ternary comparison operators with real-world data containing NULLs."""

    def test_t_eq_with_nulls(self, backend_name, backend_factory, select_and_extract):
        """Test t_eq handles NULLs as UNKNOWN."""
        data = {
            "actual_value": [100, 200, 300, None, 500],
            "expected_value": [100, 999, 300, 400, None],
        }
        df = backend_factory.create(data, backend_name)

        # Compare actual vs expected - NULL in either operand -> UNKNOWN
        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.col("actual_value").t_eq(ma.col("expected_value"))
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: 100 == 100 -> TRUE (1)
        # Row 1: 200 == 999 -> FALSE (-1)
        # Row 2: 300 == 300 -> TRUE (1)
        # Row 3: NULL == 400 -> UNKNOWN (0)
        # Row 4: 500 == NULL -> UNKNOWN (0)
        assert values[0] == T_TRUE, f"[{backend_name}] 100 == 100 should be TRUE"
        assert values[1] == T_FALSE, f"[{backend_name}] 200 == 999 should be FALSE"
        assert values[2] == T_TRUE, f"[{backend_name}] 300 == 300 should be TRUE"
        assert values[3] == T_UNKNOWN, f"[{backend_name}] NULL == 400 should be UNKNOWN"
        assert values[4] == T_UNKNOWN, f"[{backend_name}] 500 == NULL should be UNKNOWN"

    def test_t_gt_with_nulls(self, backend_name, backend_factory, select_and_extract):
        """Test t_gt returns UNKNOWN when operand is NULL."""
        data = {
            "score": [80, 90, None, 60, 70],
        }
        df = backend_factory.create(data, backend_name)

        # score > 70 - NULL scores are UNKNOWN, not excluded
        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 80 > 70 should be TRUE"
        assert values[1] == T_TRUE, f"[{backend_name}] 90 > 70 should be TRUE"
        assert values[2] == T_UNKNOWN, f"[{backend_name}] NULL > 70 should be UNKNOWN"
        assert values[3] == T_FALSE, f"[{backend_name}] 60 > 70 should be FALSE"
        assert values[4] == T_FALSE, f"[{backend_name}] 70 > 70 should be FALSE"

    def test_t_lt_with_nulls(self, backend_name, backend_factory, select_and_extract):
        """Test t_lt returns UNKNOWN when operand is NULL."""
        data = {
            "age": [25, None, 35, 20, 30],
        }
        df = backend_factory.create(data, backend_name)

        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.col("age").t_lt(30)
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 25 < 30 should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] NULL < 30 should be UNKNOWN"
        assert values[2] == T_FALSE, f"[{backend_name}] 35 < 30 should be FALSE"
        assert values[3] == T_TRUE, f"[{backend_name}] 20 < 30 should be TRUE"
        assert values[4] == T_FALSE, f"[{backend_name}] 30 < 30 should be FALSE"


# =============================================================================
# Cross-Backend Tests - Ternary Logical Operations
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTernaryLogicalOperations:
    """Test ternary logical operations on comparison results (not raw -1/0/1 data)."""

    def test_t_and_combines_comparisons(self, backend_name, backend_factory, select_and_extract):
        """Test t_and combining two ternary comparisons with real data."""
        # Real-world scenario: Find employees with high salary AND good performance
        data = {
            "salary": [80000, 90000, None, 60000, 75000],
            "performance_score": [85, None, 90, 70, 80],
        }
        df = backend_factory.create(data, backend_name)

        # Both conditions must be TRUE for overall TRUE
        # Either NULL -> that condition is UNKNOWN -> overall may be UNKNOWN
        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.col("salary").t_gt(70000).t_and(ma.col("performance_score").t_ge(80))
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: (80k > 70k)=T AND (85 >= 80)=T -> TRUE
        # Row 1: (90k > 70k)=T AND (NULL >= 80)=U -> UNKNOWN (minimum)
        # Row 2: (NULL > 70k)=U AND (90 >= 80)=T -> UNKNOWN (minimum)
        # Row 3: (60k > 70k)=F AND (70 >= 80)=F -> FALSE
        # Row 4: (75k > 70k)=T AND (80 >= 80)=T -> TRUE
        assert values[0] == T_TRUE, f"[{backend_name}] T AND T should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] T AND U should be UNKNOWN"
        assert values[2] == T_UNKNOWN, f"[{backend_name}] U AND T should be UNKNOWN"
        assert values[3] == T_FALSE, f"[{backend_name}] F AND F should be FALSE"
        assert values[4] == T_TRUE, f"[{backend_name}] T AND T should be TRUE"

    def test_t_or_combines_comparisons(self, backend_name, backend_factory, select_and_extract):
        """Test t_or combining two ternary comparisons with real data."""
        # Real-world scenario: Accept if high salary OR good performance
        data = {
            "salary": [80000, 50000, None, 60000, 50000],
            "performance_score": [60, 90, 85, None, 70],
        }
        df = backend_factory.create(data, backend_name)

        # Either condition TRUE -> overall TRUE
        # Both FALSE -> overall FALSE
        # Otherwise UNKNOWN
        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.col("salary").t_gt(70000).t_or(ma.col("performance_score").t_ge(80))
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: (80k > 70k)=T OR (60 >= 80)=F -> TRUE (maximum)
        # Row 1: (50k > 70k)=F OR (90 >= 80)=T -> TRUE (maximum)
        # Row 2: (NULL > 70k)=U OR (85 >= 80)=T -> TRUE (maximum)
        # Row 3: (60k > 70k)=F OR (NULL >= 80)=U -> UNKNOWN (maximum)
        # Row 4: (50k > 70k)=F OR (70 >= 80)=F -> FALSE
        assert values[0] == T_TRUE, f"[{backend_name}] T OR F should be TRUE"
        assert values[1] == T_TRUE, f"[{backend_name}] F OR T should be TRUE"
        assert values[2] == T_TRUE, f"[{backend_name}] U OR T should be TRUE"
        assert values[3] == T_UNKNOWN, f"[{backend_name}] F OR U should be UNKNOWN"
        assert values[4] == T_FALSE, f"[{backend_name}] F OR F should be FALSE"

    def test_t_not_inverts_comparison(self, backend_name, backend_factory, select_and_extract):
        """Test t_not inverting a ternary comparison result."""
        # Real-world scenario: Find those NOT in the high-earner category
        data = {
            "salary": [80000, 60000, None],
        }
        df = backend_factory.create(data, backend_name)

        # NOT (salary > 70000)
        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.col("salary").t_gt(70000).t_not()
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: NOT (80k > 70k)=T -> FALSE
        # Row 1: NOT (60k > 70k)=F -> TRUE
        # Row 2: NOT (NULL > 70k)=U -> UNKNOWN (stays UNKNOWN)
        assert values[0] == T_FALSE, f"[{backend_name}] NOT TRUE should be FALSE"
        assert values[1] == T_TRUE, f"[{backend_name}] NOT FALSE should be TRUE"
        assert values[2] == T_UNKNOWN, f"[{backend_name}] NOT UNKNOWN should be UNKNOWN"


# =============================================================================
# Cross-Backend Tests - Ternary to Boolean Conversions (Booleanizers)
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTernaryToBooleanConversions:
    """Test booleanizers that convert ternary comparison results to boolean."""

    def test_is_true_strict_filter(self, backend_name, backend_factory, select_and_extract):
        """Test is_true: only definite TRUE becomes True."""
        data = {
            "score": [90, 60, None],  # Above threshold, below, unknown
        }
        df = backend_factory.create(data, backend_name)

        # score > 70, then is_true (strict - only definite passes)
        expr = ma.col("score").t_gt(70).is_true()
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] == True, f"[{backend_name}] is_true(TRUE) should be True"
        assert values[1] == False, f"[{backend_name}] is_true(FALSE) should be False"
        assert values[2] == False, f"[{backend_name}] is_true(UNKNOWN) should be False"

    def test_is_unknown_identifies_uncertain(self, backend_name, backend_factory, select_and_extract):
        """Test is_unknown: identifies rows where we can't determine the answer."""
        data = {
            "score": [90, 60, None],
        }
        df = backend_factory.create(data, backend_name)

        # Find rows where score > 70 is UNKNOWN (i.e., score is NULL)
        expr = ma.col("score").t_gt(70).is_unknown()
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] == False, f"[{backend_name}] is_unknown(TRUE) should be False"
        assert values[1] == False, f"[{backend_name}] is_unknown(FALSE) should be False"
        assert values[2] == True, f"[{backend_name}] is_unknown(UNKNOWN) should be True"

    def test_maybe_true_benefit_of_doubt(self, backend_name, backend_factory, select_and_extract):
        """Test maybe_true: TRUE or UNKNOWN -> True (benefit of the doubt)."""
        data = {
            "score": [90, 60, None],
        }
        df = backend_factory.create(data, backend_name)

        # score > 70, maybe_true (includes uncertain cases)
        expr = ma.col("score").t_gt(70).maybe_true()
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] == True, f"[{backend_name}] maybe_true(TRUE) should be True"
        assert values[1] == False, f"[{backend_name}] maybe_true(FALSE) should be False"
        assert values[2] == True, f"[{backend_name}] maybe_true(UNKNOWN) should be True"

    def test_is_known_filters_nulls(self, backend_name, backend_factory, select_and_extract):
        """Test is_known: identifies rows with definite TRUE or FALSE (not UNKNOWN)."""
        data = {
            "score": [90, 60, None],
        }
        df = backend_factory.create(data, backend_name)

        # Find rows where we can make a definite determination
        expr = ma.col("score").t_gt(70).is_known()
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] == True, f"[{backend_name}] is_known(TRUE) should be True"
        assert values[1] == True, f"[{backend_name}] is_known(FALSE) should be True"
        assert values[2] == False, f"[{backend_name}] is_known(UNKNOWN) should be False"


# =============================================================================
# Cross-Backend Tests - Boolean to Ternary Conversions
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestBooleanToTernaryConversions:
    """Test converting boolean expressions to ternary for combination."""

    def test_to_ternary_from_boolean_column(self, backend_name, backend_factory, select_and_extract):
        """Test to_ternary: converts boolean True/False to ternary 1/-1."""
        data = {
            "is_active": [True, False, True, False],
        }
        df = backend_factory.create(data, backend_name)

        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.col("is_active").to_ternary()
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] to_ternary(True) should be 1"
        assert values[1] == T_FALSE, f"[{backend_name}] to_ternary(False) should be -1"
        assert values[2] == T_TRUE
        assert values[3] == T_FALSE


# =============================================================================
# Cross-Backend Tests - Ternary Constants
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTernaryConstants:
    """Test ternary constant functions for edge cases and testing."""

    def test_always_true_constant(self, backend_name, backend_factory, select_and_extract):
        """Test always_true returns TRUE for all rows."""
        data = {"id": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.always_true()
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        for i, val in enumerate(values):
            assert val == T_TRUE, f"[{backend_name}] always_true row {i} should be 1, got {val}"

    def test_always_false_constant(self, backend_name, backend_factory, select_and_extract):
        """Test always_false returns FALSE for all rows."""
        data = {"id": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.always_false()
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        for i, val in enumerate(values):
            assert val == T_FALSE, f"[{backend_name}] always_false row {i} should be -1, got {val}"

    def test_always_unknown_constant(self, backend_name, backend_factory, select_and_extract):
        """Test always_unknown returns UNKNOWN for all rows."""
        data = {"id": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = ma.always_unknown()
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        for i, val in enumerate(values):
            assert val == T_UNKNOWN, f"[{backend_name}] always_unknown row {i} should be 0, got {val}"


# =============================================================================
# Cross-Backend Tests - Real-World Scenarios
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestRealWorldScenarios:
    """Test realistic use cases for ternary logic."""

    def test_strict_eligibility_filter(self, backend_name, backend_factory, get_result_count):
        """
        Scenario: Filter for definitely eligible candidates.
        Only include those who definitely pass all criteria.
        """
        data = {
            "score": [80, None, 90, 60, None],
        }
        df = backend_factory.create(data, backend_name)

        # Filter where score > 70, using is_true (strict - exclude unknowns)
        expr = ma.col("score").t_gt(70).is_true()
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Only rows with score > 70 AND not NULL: 80 and 90
        assert count == 2, f"[{backend_name}] Expected 2 definitely eligible, got {count}"

    def test_benefit_of_doubt_filter(self, backend_name, backend_factory, get_result_count):
        """
        Scenario: Filter with benefit of the doubt for unknowns.
        Include those who might pass (TRUE or UNKNOWN).
        """
        data = {
            "score": [80, None, 90, 60, None],
        }
        df = backend_factory.create(data, backend_name)

        # Filter where score > 70 OR unknown (benefit of doubt)
        expr = ma.col("score").t_gt(70).maybe_true()
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Rows with TRUE (80, 90) and UNKNOWN (NULL, NULL)
        assert count == 4, f"[{backend_name}] Expected 4 (including unknowns), got {count}"

    def test_complex_eligibility_with_multiple_criteria(self, backend_name, backend_factory, get_result_count):
        """
        Scenario: Loan eligibility requiring BOTH high income AND good credit.
        Only approve if we're certain both criteria are met.
        """
        data = {
            "income": [80000, 90000, None, 60000, 75000, 85000],
            "credit_score": [750, None, 720, 650, 700, 680],
        }
        df = backend_factory.create(data, backend_name)

        # Both income > 70000 AND credit_score >= 700 must be TRUE
        expr = (
            ma.col("income").t_gt(70000)
            .t_and(ma.col("credit_score").t_ge(700))
            .is_true()
        )
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: income=80k > 70k (T), credit=750 >= 700 (T) -> T AND T = T -> approve
        # Row 1: income=90k > 70k (T), credit=NULL (U) -> T AND U = U -> reject (strict)
        # Row 2: income=NULL (U), credit=720 >= 700 (T) -> U AND T = U -> reject (strict)
        # Row 3: income=60k > 70k (F), credit=650 >= 700 (F) -> F AND F = F -> reject
        # Row 4: income=75k > 70k (T), credit=700 >= 700 (T) -> T AND T = T -> approve
        # Row 5: income=85k > 70k (T), credit=680 >= 700 (F) -> T AND F = F -> reject
        assert count == 2, f"[{backend_name}] Expected 2 approved (rows 0, 4), got {count}"

    def test_chained_ternary_operations(self, backend_name, backend_factory, select_and_extract):
        """
        Scenario: Complex business rule with multiple conditions.
        Accept if (high_value OR premium_customer) AND NOT flagged_for_review.
        """
        data = {
            "order_value": [1000, 500, None, 2000, 300],
            "is_premium": [False, True, True, None, False],
            "flagged": [False, False, False, False, True],
        }
        df = backend_factory.create(data, backend_name)

        # Build the expression step by step:
        # 1. high_value: order_value > 800
        # 2. premium: is_premium = True
        # 3. flagged: flagged = True
        # Result: (high_value OR premium) AND NOT flagged
        high_value = ma.col("order_value").t_gt(800)
        premium = ma.col("is_premium").t_eq(True)
        flagged = ma.col("flagged").t_eq(True)

        # Use booleanizer=None to get raw sentinel values for testing internal logic
        expr = high_value.t_or(premium).t_and(flagged.t_not())
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: (1000>800=T OR F=F) AND NOT F=T -> T AND T = T
        # Row 1: (500>800=F OR T=T) AND NOT F=T -> T AND T = T
        # Row 2: (NULL>800=U OR T=T) AND NOT F=T -> T AND T = T
        # Row 3: (2000>800=T OR NULL=U) AND NOT F=T -> T AND T = T
        # Row 4: (300>800=F OR F=F) AND NOT T=F -> F AND F = F
        assert values[0] == T_TRUE
        assert values[1] == T_TRUE
        assert values[2] == T_TRUE
        assert values[3] == T_TRUE
        assert values[4] == T_FALSE
