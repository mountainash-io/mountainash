"""
Cross-backend tests for t_col() - ternary-aware column references.

t_col() acts as a universal, configurable nullif() that allows you to specify
which values should be treated as UNKNOWN in ternary logic operations.

Features tested:
1. Default behavior (NULL = UNKNOWN)
2. Custom sentinel values (e.g., -99999, "N/A", "<MISSING>")
3. Multiple sentinel values
4. Mixed NULL and sentinel values
5. Interaction with all ternary comparison operators
6. Interaction with ternary logical operators
7. Real-world use cases (legacy data, missing value indicators)

All tests run across backends: Polars, Narwhals, and Ibis (Polars/DuckDB).
"""

import pytest
import mountainash.expressions as ma


# Ternary constant values for raw sentinel assertions
T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1


# =============================================================================
# Test: Default Behavior (NULL = UNKNOWN)
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColDefaultBehavior:
    """Test t_col() with default behavior (only NULL is UNKNOWN)."""

    def test_t_col_default_null_is_unknown(self, backend_name, backend_factory, select_and_extract):
        """Test that t_col() with no args treats NULL as UNKNOWN."""
        data = {"score": [80, None, 60]}
        df = backend_factory.create(data, backend_name)

        # t_col with default - same as col() for ternary
        expr = ma.t_col("score").t_gt(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 80 > 70 should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] NULL > 70 should be UNKNOWN"
        assert values[2] == T_FALSE, f"[{backend_name}] 60 > 70 should be FALSE"

    def test_t_col_equivalent_to_col_for_null(self, backend_name, backend_factory, select_and_extract):
        """Test that t_col() and col() produce same results for NULL handling."""
        data = {"value": [100, None, 50]}
        df = backend_factory.create(data, backend_name)

        # Both should treat NULL as UNKNOWN
        expr_t_col = ma.t_col("value").t_eq(100)
        expr_col = ma.col("value").t_eq(100)

        values_t_col = select_and_extract(df, expr_t_col.compile(df, booleanizer=None), "result", backend_name)
        values_col = select_and_extract(df, expr_col.compile(df, booleanizer=None), "result", backend_name)

        assert values_t_col == values_col, f"[{backend_name}] t_col and col should be equivalent for NULL"


# =============================================================================
# Test: Custom Sentinel Values
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColCustomSentinels:
    """Test t_col() with custom sentinel values (like a universal nullif)."""

    def test_numeric_sentinel_as_unknown(self, backend_name, backend_factory, select_and_extract):
        """Test treating a numeric sentinel value as UNKNOWN."""
        # Legacy system uses -99999 as "not evaluated"
        data = {"score": [80, -99999, 60, None]}
        df = backend_factory.create(data, backend_name)

        # -99999 should be treated as UNKNOWN (like nullif)
        expr = ma.t_col("score", unknown={-99999}).t_gt(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 80 > 70 should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] -99999 should be UNKNOWN"
        assert values[2] == T_FALSE, f"[{backend_name}] 60 > 70 should be FALSE"
        # NULL without None in unknown set - still FALSE (not UNKNOWN)
        assert values[3] == T_FALSE, f"[{backend_name}] NULL should be FALSE (not in unknown set)"

    def test_string_sentinel_as_unknown(self, backend_name, backend_factory, select_and_extract):
        """Test treating a string sentinel value as UNKNOWN."""
        data = {"status": ["active", "N/A", "inactive", None]}
        df = backend_factory.create(data, backend_name)

        # "N/A" should be treated as UNKNOWN
        expr = ma.t_col("status", unknown={"N/A"}).t_eq("active")
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 'active' == 'active' should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] 'N/A' should be UNKNOWN"
        assert values[2] == T_FALSE, f"[{backend_name}] 'inactive' == 'active' should be FALSE"
        # NULL without None in unknown set
        assert values[3] == T_FALSE, f"[{backend_name}] NULL should be FALSE (not in unknown set)"

    def test_zero_as_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test treating 0 as UNKNOWN (common in legacy systems)."""
        data = {"count": [5, 0, 10, 3]}
        df = backend_factory.create(data, backend_name)

        # 0 means "not measured" in this legacy system
        expr = ma.t_col("count", unknown={0}).t_gt(2)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 5 > 2 should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] 0 should be UNKNOWN"
        assert values[2] == T_TRUE, f"[{backend_name}] 10 > 2 should be TRUE"
        assert values[3] == T_TRUE, f"[{backend_name}] 3 > 2 should be TRUE"


# =============================================================================
# Test: Multiple Sentinel Values
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColMultipleSentinels:
    """Test t_col() with multiple sentinel values."""

    def test_multiple_numeric_sentinels(self, backend_name, backend_factory, select_and_extract):
        """Test multiple numeric sentinel values as UNKNOWN."""
        # -1 = not applicable, -999 = error, None = missing
        data = {"value": [100, -1, -999, None, 50]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("value", unknown={-1, -999, None}).t_gt(0)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 100 > 0 should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] -1 should be UNKNOWN"
        assert values[2] == T_UNKNOWN, f"[{backend_name}] -999 should be UNKNOWN"
        assert values[3] == T_UNKNOWN, f"[{backend_name}] NULL should be UNKNOWN"
        assert values[4] == T_TRUE, f"[{backend_name}] 50 > 0 should be TRUE"

    def test_multiple_string_sentinels(self, backend_name, backend_factory, select_and_extract):
        """Test multiple string sentinel values as UNKNOWN."""
        data = {"category": ["A", "N/A", "<MISSING>", "", "B"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("category", unknown={"N/A", "<MISSING>", ""}).t_eq("A")
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 'A' == 'A' should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] 'N/A' should be UNKNOWN"
        assert values[2] == T_UNKNOWN, f"[{backend_name}] '<MISSING>' should be UNKNOWN"
        assert values[3] == T_UNKNOWN, f"[{backend_name}] '' should be UNKNOWN"
        assert values[4] == T_FALSE, f"[{backend_name}] 'B' == 'A' should be FALSE"

    def test_null_plus_sentinel_combined(self, backend_name, backend_factory, select_and_extract):
        """Test NULL and custom sentinel together as UNKNOWN."""
        data = {"score": [80, None, -99999, 60]}
        df = backend_factory.create(data, backend_name)

        # Both NULL and -99999 are UNKNOWN
        expr = ma.t_col("score", unknown={None, -99999}).t_gt(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE, f"[{backend_name}] 80 > 70 should be TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] NULL should be UNKNOWN"
        assert values[2] == T_UNKNOWN, f"[{backend_name}] -99999 should be UNKNOWN"
        assert values[3] == T_FALSE, f"[{backend_name}] 60 > 70 should be FALSE"


# =============================================================================
# Test: All Ternary Comparison Operators with t_col
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColWithAllComparisons:
    """Test t_col() with all ternary comparison operators."""

    def test_t_eq_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_col().t_eq() with sentinel value."""
        data = {"val": [10, -1, 10, 20]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("val", unknown={-1}).t_eq(10)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN  # -1 is sentinel
        assert values[2] == T_TRUE
        assert values[3] == T_FALSE

    def test_t_ne_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_col().t_ne() with sentinel value."""
        data = {"val": [10, -1, 10, 20]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("val", unknown={-1}).t_ne(10)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_FALSE
        assert values[1] == T_UNKNOWN  # -1 is sentinel
        assert values[2] == T_FALSE
        assert values[3] == T_TRUE

    def test_t_gt_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_col().t_gt() with sentinel value."""
        data = {"val": [80, -99999, 60]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("val", unknown={-99999}).t_gt(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_FALSE

    def test_t_lt_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_col().t_lt() with sentinel value."""
        data = {"val": [50, -99999, 80]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("val", unknown={-99999}).t_lt(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_FALSE

    def test_t_ge_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_col().t_ge() with sentinel value."""
        data = {"val": [70, -99999, 60]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("val", unknown={-99999}).t_ge(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_FALSE

    def test_t_le_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_col().t_le() with sentinel value."""
        data = {"val": [70, -99999, 80]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("val", unknown={-99999}).t_le(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_FALSE


# =============================================================================
# Test: t_col with Ternary Logical Operators
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColWithLogicalOperators:
    """Test t_col() combined with ternary logical operators."""

    def test_t_and_with_sentinels(self, backend_name, backend_factory, select_and_extract):
        """Test t_and with two t_col expressions using different sentinels."""
        data = {
            "income": [80000, -1, 70000, 90000],  # -1 = not disclosed
            "credit": [750, 700, -999, 720],  # -999 = not available
        }
        df = backend_factory.create(data, backend_name)

        # Both conditions must be TRUE - sentinels propagate UNKNOWN
        expr = (
            ma.t_col("income", unknown={-1}).t_gt(70000)
            .t_and(ma.t_col("credit", unknown={-999}).t_ge(700))
        )
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: T AND T = T
        # Row 1: U AND T = U (income is -1)
        # Row 2: F AND U = F (credit is -999, but income < 70000 = F wins)
        # Row 3: T AND T = T
        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_FALSE  # F AND U = F (minimum)
        assert values[3] == T_TRUE

    def test_t_or_with_sentinels(self, backend_name, backend_factory, select_and_extract):
        """Test t_or with t_col expressions using sentinels."""
        data = {
            "score1": [80, -1, 60, -1],
            "score2": [70, 90, -1, -1],
        }
        df = backend_factory.create(data, backend_name)

        # Either score > 70 - sentinels propagate UNKNOWN
        expr = (
            ma.t_col("score1", unknown={-1}).t_gt(70)
            .t_or(ma.t_col("score2", unknown={-1}).t_gt(70))
        )
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: T OR F = T
        # Row 1: U OR T = T (score2 = 90 > 70)
        # Row 2: F OR U = U
        # Row 3: U OR U = U
        assert values[0] == T_TRUE
        assert values[1] == T_TRUE  # T OR U = T
        assert values[2] == T_UNKNOWN
        assert values[3] == T_UNKNOWN

    def test_t_not_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_not with t_col sentinel."""
        data = {"active": [1, -1, 0]}  # -1 = unknown status
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("active", unknown={-1}).t_eq(1).t_not()
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: NOT TRUE = FALSE
        # Row 1: NOT UNKNOWN = UNKNOWN
        # Row 2: NOT FALSE = TRUE
        assert values[0] == T_FALSE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_TRUE


# =============================================================================
# Test: t_col with Collection Operations
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColWithCollections:
    """Test t_col() with ternary collection operations."""

    def test_t_is_in_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_is_in with t_col sentinel."""
        data = {"code": ["A", "B", "<NA>", "C"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("code", unknown={"<NA>"}).t_is_in(["A", "B"])
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE   # "A" in [A,B]
        assert values[1] == T_TRUE   # "B" in [A,B]
        assert values[2] == T_UNKNOWN  # "<NA>" is sentinel
        assert values[3] == T_FALSE  # "C" not in [A,B]

    def test_t_is_not_in_with_sentinel(self, backend_name, backend_factory, select_and_extract):
        """Test t_is_not_in with t_col sentinel."""
        data = {"code": ["A", "B", "<NA>", "C"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("code", unknown={"<NA>"}).t_is_not_in(["A", "B"])
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_FALSE  # "A" in [A,B]
        assert values[1] == T_FALSE  # "B" in [A,B]
        assert values[2] == T_UNKNOWN  # "<NA>" is sentinel
        assert values[3] == T_TRUE   # "C" not in [A,B]


# =============================================================================
# Test: Real-World Use Cases
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColRealWorldUseCases:
    """Test t_col() in real-world scenarios."""

    def test_legacy_data_sentinel_handling(self, backend_name, backend_factory, get_result_count):
        """
        Scenario: Legacy system uses -99999 for "not evaluated".

        We want to filter for scores > 70, but:
        - Treat -99999 as "we don't know" (UNKNOWN)
        - Use strict filtering (is_true) - only definite passes
        """
        data = {
            "student_id": [1, 2, 3, 4, 5],
            "exam_score": [85, -99999, 65, 90, -99999],
        }
        df = backend_factory.create(data, backend_name)

        # Filter for passing scores, treating -99999 as UNKNOWN
        expr = ma.t_col("exam_score", unknown={-99999}).t_gt(70)
        result = df.filter(expr.compile(df))  # Default: is_true

        count = get_result_count(result, backend_name)
        # Only students 1 and 4 definitely pass (85 and 90)
        # Students 2 and 5 are UNKNOWN (excluded by is_true)
        # Student 3 is FALSE (65 < 70)
        assert count == 2, f"[{backend_name}] Expected 2 definite passes"

    def test_survey_data_with_skip_values(self, backend_name, backend_factory, get_result_count):
        """
        Scenario: Survey data where -1 means "prefer not to answer".

        We want to find satisfied customers (score >= 4), giving benefit
        of doubt to those who didn't answer.
        """
        data = {
            "customer_id": [1, 2, 3, 4, 5],
            "satisfaction": [5, -1, 3, 4, -1],
        }
        df = backend_factory.create(data, backend_name)

        # Find satisfied or potentially satisfied
        expr = ma.t_col("satisfaction", unknown={-1}).t_ge(4)
        result = df.filter(expr.compile(df, booleanizer="maybe_true"))

        count = get_result_count(result, backend_name)
        # Customers 1, 2, 4, 5: TRUE or UNKNOWN (included by maybe_true)
        # Customer 3: FALSE (3 < 4)
        assert count == 4, f"[{backend_name}] Expected 4 (satisfied + unknown)"

    def test_multi_source_data_integration(self, backend_name, backend_factory, select_and_extract):
        """
        Scenario: Merging data from multiple sources with different sentinels.

        Source A uses -1 for missing
        Source B uses 0 for missing
        Combined analysis treats both as UNKNOWN.
        """
        data = {
            "id": [1, 2, 3, 4],
            "score_a": [80, -1, 60, 90],  # -1 = missing from source A
            "score_b": [70, 85, 0, 75],   # 0 = missing from source B
        }
        df = backend_factory.create(data, backend_name)

        # Both scores must be above threshold
        expr = (
            ma.t_col("score_a", unknown={-1}).t_gt(65)
            .t_and(ma.t_col("score_b", unknown={0}).t_gt(65))
        )
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: T AND T = T (80>65 and 70>65)
        # Row 1: U AND T = U (-1 is unknown)
        # Row 2: F AND U = F (60<65)
        # Row 3: T AND T = T (90>65 and 75>65)
        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_FALSE
        assert values[3] == T_TRUE

    def test_find_unknown_values(self, backend_name, backend_factory, get_result_count):
        """
        Scenario: Find all records where the value is uncertain.

        Use is_unknown() to identify records that need review.
        """
        data = {
            "record_id": [1, 2, 3, 4, 5],
            "quality_score": [95, -1, 80, -1, 70],
        }
        df = backend_factory.create(data, backend_name)

        # Find records needing review (UNKNOWN quality)
        expr = ma.t_col("quality_score", unknown={-1}).t_gt(0).is_unknown()
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Records 2 and 4 have -1 (UNKNOWN)
        assert count == 2, f"[{backend_name}] Expected 2 records needing review"


# =============================================================================
# Test: t_col with Auto-Booleanization
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColWithAutoBooleanization:
    """Test that t_col() works correctly with auto-booleanization."""

    def test_t_col_default_booleanizer(self, backend_name, backend_factory, select_and_extract):
        """Test t_col with default is_true booleanizer."""
        data = {"score": [80, -99999, 60]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("score", unknown={-99999}).t_gt(70)
        # Default booleanizer is is_true
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert values[0] is True   # TRUE -> True
        assert values[1] is False  # UNKNOWN -> False (is_true)
        assert values[2] is False  # FALSE -> False

    def test_t_col_maybe_true_booleanizer(self, backend_name, backend_factory, select_and_extract):
        """Test t_col with maybe_true booleanizer (benefit of doubt)."""
        data = {"score": [80, -99999, 60]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("score", unknown={-99999}).t_gt(70)
        values = select_and_extract(df, expr.compile(df, booleanizer="maybe_true"), "result", backend_name)

        assert values[0] is True   # TRUE -> True
        assert values[1] is True   # UNKNOWN -> True (maybe_true)
        assert values[2] is False  # FALSE -> False

    def test_t_col_chained_to_boolean_context(self, backend_name, backend_factory, select_and_extract):
        """Test t_col ternary expression chained with boolean operation."""
        data = {
            "score": [80, -99999, 60],
            "active": [True, True, True],
        }
        df = backend_factory.create(data, backend_name)

        # t_col ternary result used in boolean AND
        expr = ma.t_col("score", unknown={-99999}).t_gt(70).and_(ma.col("active").eq(True))
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        # is_true(T) AND True = True
        # is_true(U) AND True = False AND True = False
        # is_true(F) AND True = False AND True = False
        assert values[0] is True
        assert values[1] is False
        assert values[2] is False


# =============================================================================
# Test: Edge Cases
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTColEdgeCases:
    """Test edge cases for t_col()."""

    def test_empty_unknown_set(self, backend_name, backend_factory, select_and_extract):
        """Test t_col with empty unknown set (nothing is UNKNOWN)."""
        data = {"score": [80, None, 60]}
        df = backend_factory.create(data, backend_name)

        # Empty set - even NULL is not UNKNOWN
        expr = ma.t_col("score", unknown=set()).t_gt(70)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_TRUE
        # NULL with empty unknown set - comparison may fail or be FALSE
        # The exact behavior depends on backend, but should not be UNKNOWN
        assert values[2] == T_FALSE

    def test_sentinel_that_matches_comparison_target(self, backend_name, backend_factory, select_and_extract):
        """Test when sentinel value equals the comparison target."""
        data = {"val": [100, 50, 50]}  # 50 is both a sentinel and valid value
        df = backend_factory.create(data, backend_name)

        # This is a weird case - 50 is sentinel but also comparison target
        expr = ma.t_col("val", unknown={50}).t_eq(50)
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert values[0] == T_FALSE  # 100 != 50
        assert values[1] == T_UNKNOWN  # 50 is sentinel -> UNKNOWN
        assert values[2] == T_UNKNOWN  # 50 is sentinel -> UNKNOWN

    def test_comparison_between_two_t_cols(self, backend_name, backend_factory, select_and_extract):
        """Test comparison between two t_col expressions with different sentinels."""
        data = {
            "a": [100, -1, 80, 90],
            "b": [100, 80, -999, 90],
        }
        df = backend_factory.create(data, backend_name)

        # Both columns have different sentinels
        # Note: Current implementation may not fully support this case
        # This test documents the expected behavior
        expr = ma.t_col("a", unknown={-1}).t_eq(ma.t_col("b", unknown={-999}))
        values = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: 100 == 100 = T (both valid)
        # Row 1: -1 (U) == 80 = U (left is unknown)
        # Row 2: 80 == -999 (U) = U (right is unknown)
        # Row 3: 90 == 90 = T (both valid)
        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_UNKNOWN
        assert values[3] == T_TRUE
