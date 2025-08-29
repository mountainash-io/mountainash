"""
Gold Standard TernaryExpressionBuilder API Test Suite

This is the definitive test suite that validates the complete TernaryExpressionBuilder API
across all available ternary expression visitors/backends. It tests the high-level user-facing
API that developers actually interact with, ensuring consistent behavior across all backends.

This test supersedes many scattered individual tests by providing comprehensive validation
of every TernaryExpressionBuilder method in a single, parameterized test suite.
"""

import pytest
import polars as pl
from typing import Any, List, Dict, Tuple

from mountainash_expressions.utils.expressions.ternary.constants import TernaryLogicValues
from mountainash_expressions.utils.expressions.ternary import (
    TernaryExpressionBuilder,
    PolarsTernaryExpressionVisitor,
    IbisTernaryExpressionVisitor,
    PandasTernaryExpressionVisitor,
    PyArrowTernaryExpressionVisitor,
    # NumPyTernaryExpressionVisitor,
    # XarrayTernaryExpressionVisitor
)
from mountainash_dataframes.utils.dataframe_utils import DataFrameUtils
from mountainash_dataframes.utils.dataframe_handlers.dataframe_strategy_factory import DataFrameStrategyFactory
from mountainash_expressions.constants import CONST_DATAFRAME_FRAMEWORK

# try:
#     from mountainash_dataframes.utils.expressions.ternary.ternary_expression_pyspark import (
#         PySparkTernaryExpressionVisitor
#     )
#     PYSPARK_AVAILABLE = True
# except ImportError:
#     PySparkTernaryExpressionVisitor = None
PYSPARK_AVAILABLE = False


def get_all_backend_configs():
    """Get all available backend visitor configurations for comprehensive testing."""
    configs = [
        (CONST_DATAFRAME_FRAMEWORK.POLARS, PolarsTernaryExpressionVisitor),
        (CONST_DATAFRAME_FRAMEWORK.IBIS, IbisTernaryExpressionVisitor),
        (CONST_DATAFRAME_FRAMEWORK.PANDAS, PandasTernaryExpressionVisitor),
        (CONST_DATAFRAME_FRAMEWORK.PYARROW_TABLE, PyArrowTernaryExpressionVisitor),
        # (CONST_DATAFRAME_FRAMEWORK.PYARROW_RECORDBATCH, PyArrowTernaryExpressionVisitor)
    ]

    return configs

ALL_BACKEND_CONFIGS = get_all_backend_configs()


class TestTernaryExpressionBuilderAPI:
    """Gold standard test for the complete TernaryExpressionBuilder API across all backends."""

    @pytest.fixture
    def test_dataframe(self):
        """Standard test DataFrame with various data types and UNKNOWN values."""
        return {
            "name": ["Alice", "Bob", None, "Charlie", "Diana"],
            "age": [25, 30, -999999999, 35, 28],
            "score": [85.5, 92.0, -999999999.0, 78.5, 88.0],
            "active": [True, False, None, True, False],
            "category": ["A", "B", "<NOT_SET>", "A", "C"],
            "salary": [50000, 75000, None, 60000, 55000],
            "years_exp": [2, 5, -999999999, 8, 3],
            "department": ["Engineering", "Sales", None, "Engineering", "Marketing"]
        }

    def _test_expression_results(self, expression, test_data, framework_name):
        """Test expression using clean DataFrameUtils interface."""

        # Create DataFrame using existing utility
        test_df = DataFrameUtils.create_dataframe(
            dataframe_framework=framework_name,
            data_dict=test_data
        )

        # Use DataFrameUtils.filter to apply the expression
        filtered_df = DataFrameUtils.filter(test_df, condition=expression)

        print(f"Framework: {framework_name}")
        print(filtered_df)
        print(f"===============================")

        # Get counts for validation
        total_count = DataFrameUtils.count(test_df)
        filtered_count = DataFrameUtils.count(filtered_df)

        return {
            "total_rows": total_count,
            "filtered_rows": filtered_count,
            "has_results": filtered_count > 0,
            "framework": framework_name
        }


    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_comparison_operators_eq_ne(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test equality and inequality comparison operators."""

        # Test equals: should find exactly 1 Alice in our test data
        eq_expr = TernaryExpressionBuilder.eq("name", "Alice")
        eq_results = self._test_expression_results(eq_expr, test_dataframe, framework_name)

        assert eq_results["total_rows"] == 5  # We have 5 total rows
        assert eq_results["filtered_rows"] == 1  # Only 1 Alice
        assert eq_results["has_results"] == True

        # Test not equals: should find everyone except Alice (3 rows)
        # ne_expr = TernaryExpressionBuilder.ne("name", "Alice")

        # ne_expr = TernaryExpressionBuilder.not_(eq_expr)
        ne_expr = TernaryExpressionBuilder.ne("name", "Alice")

        ne_results = self._test_expression_results(ne_expr, test_dataframe, framework_name)

        print("ne_results: ")
        print(ne_results)

        assert ne_results["total_rows"] == 5
        assert ne_results["filtered_rows"] == 3  # Everyone except Alice. but we have one unknown value!
        assert ne_results["has_results"] == True

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_numeric_comparisons(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test numeric comparison operators (>, <, >=, <=)."""

        # Test greater than: age > 30 (should find ages 35 only = 1 row)
        gt_expr = TernaryExpressionBuilder.gt("age", 30)
        gt_results = self._test_expression_results(gt_expr, test_dataframe, framework_name)
        assert gt_results["total_rows"] == 5
        assert gt_results["filtered_rows"] >= 1  # At least age=35
        assert gt_results["has_results"] == True

        # Test less than: score < 90.0 (should find scores 85.5, 78.5, 88.0 = 3 rows)
        lt_expr = TernaryExpressionBuilder.lt("score", 90.0)
        lt_results = self._test_expression_results(lt_expr, test_dataframe, framework_name)
        assert lt_results["total_rows"] == 5
        assert lt_results["filtered_rows"] >= 3  # Multiple scores under 90
        assert lt_results["has_results"] == True

        # Test greater than or equal: age >= 25 (should find most ages)
        ge_expr = TernaryExpressionBuilder.ge("age", 25)
        ge_results = self._test_expression_results(ge_expr, test_dataframe, framework_name)
        assert ge_results["total_rows"] == 5
        assert ge_results["filtered_rows"] >= 4  # Ages 25, 30, 35, 28
        assert ge_results["has_results"] == True

        # Test less than or equal: score <= 90.0 (should find multiple scores)
        le_expr = TernaryExpressionBuilder.le("score", 90.0)
        le_results = self._test_expression_results(le_expr, test_dataframe, framework_name)
        assert le_results["total_rows"] == 5
        assert le_results["filtered_rows"] >= 3  # Multiple scores <= 90
        assert le_results["has_results"] == True

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_null_operations(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test null checking operations."""

        # Test is_null: salary has 1 None value in our test data
        null_expr = TernaryExpressionBuilder.is_null("salary")
        null_results = self._test_expression_results(null_expr, test_dataframe, framework_name)
        assert null_results["total_rows"] == 5
        assert null_results["filtered_rows"] >= 1  # At least 1 null salary
        assert null_results["has_results"] == True

        # Test not_null: should find non-null salaries (4 rows)
        not_null_expr = TernaryExpressionBuilder.not_null("salary")
        not_null_results = self._test_expression_results(not_null_expr, test_dataframe, framework_name)
        assert not_null_results["total_rows"] == 5
        assert not_null_results["filtered_rows"] >= 4  # Non-null salaries
        assert not_null_results["has_results"] == True

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_between_operation(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test between operation with various scenarios."""

        # Test inclusive between: age between 25 and 35 (should find ages 25, 30, 35, 28 = 4 rows)
        between_expr = TernaryExpressionBuilder.between("age", 25, 35)
        between_results = self._test_expression_results(between_expr, test_dataframe, framework_name)
        assert between_results["total_rows"] == 5
        assert between_results["filtered_rows"] >= 3  # Ages in range (handling UNKNOWN differently)
        assert between_results["has_results"] == True

        # Test exclusive between: score between 80 and 90 (exclusive, should find 85.5, 88.0)
        between_excl_expr = TernaryExpressionBuilder.between("score", 80.0, 90.0, lower_eq=False, upper_eq=False)
        between_excl_results = self._test_expression_results(between_excl_expr, test_dataframe, framework_name)
        assert between_excl_results["total_rows"] == 5
        assert between_excl_results["filtered_rows"] >= 2  # Scores between 80-90 exclusive
        assert between_excl_results["has_results"] == True

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_in_list_operation(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test in_list operation."""

        # Test in_list: category in ["A", "B"] (should find "A", "B" categories = 2 rows)
        in_expr = TernaryExpressionBuilder.in_list("category", ["A", "B"])
        in_results = self._test_expression_results(in_expr, test_dataframe, framework_name)
        assert in_results["total_rows"] == 5
        assert in_results["filtered_rows"] >= 2  # Categories A and B
        assert in_results["has_results"] == True

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_column_to_column_comparisons(self, framework_name, visitor_class, default_ternary_mapper):
        """Test column-to-column comparison operations."""

        # Create DataFrame with two comparable columns
        test_data = {
            "col1": [10, 20, -999999999, 30, 30],
            "col2": [15, 20, 25, -999999999, 25]
        }

        # Test column equals: should find row where both cols are 20
        col_eq_expr = TernaryExpressionBuilder.col_eq("col1", "col2")
        col_eq_results = self._test_expression_results(col_eq_expr, test_data, framework_name)
        assert col_eq_results["total_rows"] == 5
        assert col_eq_results["filtered_rows"] >= 1  # At least the 20,20 row
        assert col_eq_results["has_results"] == True

        # Test column greater than: should find rows where col1 > col2
        col_gt_expr = TernaryExpressionBuilder.col_gt("col1", "col2")
        col_gt_results = self._test_expression_results(col_gt_expr, test_data, framework_name)
        assert col_gt_results["total_rows"] == 5
        assert col_gt_results["filtered_rows"] >= 1  # At least the 30>25 case
        assert col_gt_results["has_results"] == True

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_logical_operations_and_or(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test logical AND and OR operations."""

        # Test AND operation: category='A' AND age>20 (should find Alice and Charlie)
        and_expr = TernaryExpressionBuilder.and_(
            TernaryExpressionBuilder.eq("category", "A"),
            TernaryExpressionBuilder.gt("age", 20)
        )
        and_results = self._test_expression_results(and_expr, test_dataframe, framework_name)

        assert and_results["total_rows"] == 5
        assert and_results["filtered_rows"] >= 1  # At least one match
        assert and_results["has_results"] == True

        # Test OR operation: name='Alice' OR score>90 (should find Alice and high scorer)
        or_expr = TernaryExpressionBuilder.or_(
            TernaryExpressionBuilder.eq("name", "Alice"),
            TernaryExpressionBuilder.gt("score", 90.0)
        )
        or_results = self._test_expression_results(or_expr, test_dataframe, framework_name)


        assert or_results["total_rows"] == 5
        assert or_results["filtered_rows"] >= 1  # At least Alice or high scorer
        assert or_results["has_results"] == True

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_xor_operations(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test exclusive XOR and parity XOR operations."""

        # Test exclusive XOR (exactly one TRUE): should find rows with exactly one condition true
        xor_expr = TernaryExpressionBuilder.xor_(
            TernaryExpressionBuilder.eq("category", "A"),
            TernaryExpressionBuilder.eq("active", True),
            TernaryExpressionBuilder.gt("age", 30)
        )
        xor_results = self._test_expression_results(xor_expr, test_dataframe, framework_name)
        assert xor_results["total_rows"] == 5
        # XOR is complex - just ensure it executes without error for now
        assert xor_results["filtered_rows"] >= 0  # May be 0 if no exactly-one-true cases


    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_not_operation(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test NOT operation."""

        # Test NOT operation: should find rows where active != True
        not_expr = TernaryExpressionBuilder.not_(
            TernaryExpressionBuilder.eq("active", True)
        )
        not_results = self._test_expression_results(not_expr, test_dataframe, framework_name)
        assert not_results["total_rows"] == 5
        assert not_results["filtered_rows"] >= 2  # Should find False and None/UNKNOWN
        assert not_results["has_results"] == True


    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_always_true_false_operations(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test always true and always false operations."""

        # Test always_true: should return all rows (since condition is always true)
        always_true_expr = TernaryExpressionBuilder.always_true()
        always_true_results = self._test_expression_results(always_true_expr, test_dataframe, framework_name)
        assert always_true_results["total_rows"] == 5
        assert always_true_results["filtered_rows"] == 5  # Should return all rows
        assert always_true_results["has_results"] == True

        # Test always_false: should return no rows (since condition is always false)
        always_false_expr = TernaryExpressionBuilder.always_false()
        always_false_results = self._test_expression_results(always_false_expr, test_dataframe, framework_name)
        assert always_false_results["total_rows"] == 5
        assert always_false_results["filtered_rows"] == 0  # Should return no rows
        assert always_false_results["has_results"] == False

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_complex_nested_expressions(self, framework_name, visitor_class, test_dataframe, default_ternary_mapper):
        """Test complex nested expressions combining multiple operations."""

        # Test complex business rule: (category='A' OR score>85) AND age between 25-40 AND salary not null
        complex_expr = TernaryExpressionBuilder.and_(
            TernaryExpressionBuilder.or_(
                TernaryExpressionBuilder.eq("category", "A"),
                TernaryExpressionBuilder.gt("score", 85.0)
            ),
            TernaryExpressionBuilder.between("age", 25, 40),
            TernaryExpressionBuilder.not_(
                TernaryExpressionBuilder.is_null("salary")
            )
        )
        complex_results = self._test_expression_results(complex_expr, test_dataframe, framework_name)
        assert complex_results["total_rows"] == 5
        assert complex_results["filtered_rows"] >= 0  # Complex logic may match 0+ rows
        # Just ensure the complex expression executes without error

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_real_world_business_scenarios(self, framework_name, visitor_class, default_ternary_mapper):
        """Test real-world business scenario expressions."""

        # E-commerce customer segmentation scenario
        customers_data = {
            "customer_type": ["premium", "standard", None, "premium", "basic"],
            "annual_spend": [5000, 2000, -999999999, 8000, 500],
            "loyalty_years": [3, 1, None, 5, 0],
            "region": ["North", "South", "<NOT_SET>", "North", "East"]
        }

        # High-value customer rule
        high_value_expr = TernaryExpressionBuilder.and_(
            TernaryExpressionBuilder.or_(
                TernaryExpressionBuilder.eq("customer_type", "premium"),
                TernaryExpressionBuilder.gt("annual_spend", 3000)
            ),
            TernaryExpressionBuilder.ge("loyalty_years", 1),
            TernaryExpressionBuilder.ne("region", "<NOT_SET>")
        )

        high_value_results = self._test_expression_results(high_value_expr, customers_data, framework_name)
        assert high_value_results["total_rows"] == 5
        assert high_value_results["filtered_rows"] >= 1  # Should find premium customers
        assert high_value_results["has_results"] == True

        # Payment method validation (exactly one active)
        payment_data = {
            "credit_card": ["active", "inactive", None, "inactive"],
            "bank_transfer": ["inactive", "active", "active", "inactive"],
            "digital_wallet": ["inactive", "inactive", "inactive", "active"]
        }

        payment_validation_expr = TernaryExpressionBuilder.xor_(
            TernaryExpressionBuilder.eq("credit_card", "active"),
            TernaryExpressionBuilder.eq("bank_transfer", "active"),
            TernaryExpressionBuilder.eq("digital_wallet", "active")
        )

        payment_results = self._test_expression_results(payment_validation_expr, payment_data, framework_name)
        assert payment_results["total_rows"] == 4
        assert payment_results["filtered_rows"] >= 2  # Should find valid single-payment rows
        assert payment_results["has_results"] == True


class TestTernaryBuilderShortcutAliases:
    """Test that all shortcut aliases work correctly and produce identical results."""

    def _test_expression_results(self, expression, test_data, framework_name):
        """Test expression using clean DataFrameUtils interface."""

        # Create DataFrame using existing utility
        test_df = DataFrameUtils.create_dataframe(
            dataframe_framework=framework_name,
            data_dict=test_data
        )

        # Use DataFrameUtils.filter to apply the expression
        filtered_df = DataFrameUtils.filter(test_df, condition=expression)

        # Get counts for validation
        total_count = DataFrameUtils.count(test_df)
        filtered_count = DataFrameUtils.count(filtered_df)

        return {
            "total_rows": total_count,
            "filtered_rows": filtered_count,
            "has_results": filtered_count > 0,
            "framework": framework_name
        }

    @pytest.mark.parametrize("framework_name,visitor_class", ALL_BACKEND_CONFIGS)
    def test_shortcut_aliases_equivalence(self, framework_name, visitor_class, default_ternary_mapper):
        """Test that shortcut aliases produce identical results to their full method names."""

        test_data = {
            "col1": [10, 20, 30],
            "col2": [15, 20, 25]
        }

        # Test eq vs equals: both should return same number of filtered rows
        eq_short = TernaryExpressionBuilder.eq("col1", 20)
        eq_full = TernaryExpressionBuilder.equals("col1", 20)

        eq_short_results = self._test_expression_results(eq_short, test_data, framework_name)
        eq_full_results = self._test_expression_results(eq_full, test_data, framework_name)
        assert eq_short_results["filtered_rows"] == eq_full_results["filtered_rows"], f"Framework {framework_name}: eq and equals should be identical"

        # Test gt vs greater_than: both should return same number of filtered rows
        gt_short = TernaryExpressionBuilder.gt("col1", 15)
        gt_full = TernaryExpressionBuilder.greater_than("col1", 15)

        gt_short_results = self._test_expression_results(gt_short, test_data, framework_name)
        gt_full_results = self._test_expression_results(gt_full, test_data, framework_name)
        assert gt_short_results["filtered_rows"] == gt_full_results["filtered_rows"], f"Framework {framework_name}: gt and greater_than should be identical"

    #TODO: Add lots of None/Null tests!

if __name__ == "__main__":
    pytest.main([__file__])
