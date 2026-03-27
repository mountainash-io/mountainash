"""
Tests for cross-backend consistency in join module.

This module validates that join operations produce equivalent results across all backends,
ensuring consistent behavior regardless of the underlying DataFrame implementation.
"""

import pytest
import narwhals as nw
from pytest_check import check

from mountainash.dataframes.join import DataFrameJoinFactory
from mountainash.dataframes.cast import DataFrameCastFactory


# Core backends for consistency testing
CORE_BACKEND_NAMES = ["pandas", "polars", "pyarrow", "ibis", "narwhals"]


@pytest.mark.unit
class TestCrossBackendInnerJoin:
    """Test that inner join produces consistent results across backends."""

    def test_inner_join_consistency(self, all_backend_join_pairs):
        """Test that all backends return the same inner join results."""
        results = {}

        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.inner_join(
                pair["left"],
                pair["right"],
                predicates="id"
            )

            # Convert to pandas for comparison
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            results[backend_name] = {
                "row_count": len(result_df),
                "columns": set(result_df.columns),
                "ids": sorted(result_df['id'].tolist())
            }

        # All backends should have same row count
        reference_count = results["pandas"]["row_count"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["row_count"],
                reference_count,
                msg=f"{backend_name} inner join row count doesn't match pandas"
            )

        # All backends should have same IDs
        reference_ids = results["pandas"]["ids"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["ids"],
                reference_ids,
                msg=f"{backend_name} inner join IDs don't match pandas"
            )

    def test_inner_join_data_integrity(self, all_backend_join_pairs):
        """Test that inner join preserves data integrity across backends."""
        results = {}

        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.inner_join(pair["left"], pair["right"], predicates="id")

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            # Sort by id for consistent comparison
            result_df = result_df.sort_values('id').reset_index(drop=True)

            results[backend_name] = result_df

        # Compare data values across backends
        reference_df = results["pandas"]
        for backend_name, result_df in results.items():
            if backend_name == "pandas":
                continue

            # Check that ID=2 has same data
            ref_row = reference_df[reference_df['id'] == 2].iloc[0]
            test_row = result_df[result_df['id'] == 2].iloc[0]

            check.equal(
                test_row['name'],
                ref_row['name'],
                msg=f"{backend_name} data doesn't match pandas for ID=2"
            )


@pytest.mark.unit
class TestCrossBackendLeftJoin:
    """Test that left join produces consistent results across backends."""

    def test_left_join_consistency(self, all_backend_join_pairs):
        """Test that all backends return the same left join results."""
        results = {}

        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.left_join(pair["left"], pair["right"], predicates="id")

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            results[backend_name] = {
                "row_count": len(result_df),
                "ids": sorted(result_df['id'].tolist())
            }

        # All backends should have same row count (all left rows)
        reference_count = results["pandas"]["row_count"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["row_count"],
                reference_count,
                msg=f"{backend_name} left join row count doesn't match pandas"
            )

        # All backends should preserve all left IDs
        reference_ids = results["pandas"]["ids"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["ids"],
                reference_ids,
                msg=f"{backend_name} left join IDs don't match pandas"
            )

    def test_left_join_preserves_left_data(self, all_backend_join_pairs):
        """Test that left join preserves all left table data."""
        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.left_join(pair["left"], pair["right"], predicates="id")

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            # All left IDs should be present
            left_cast_strategy = cast_factory.get_strategy(pair["left"])
            left_df = left_cast_strategy.to_pandas(pair["left"])

            left_ids = set(left_df['id'])
            result_ids = set(result_df['id'])

            check.is_true(
                left_ids.issubset(result_ids),
                msg=f"{backend_name} left join doesn't preserve all left IDs"
            )


@pytest.mark.unit
class TestCrossBackendOuterJoin:
    """Test that outer join produces consistent results across backends."""

    def test_outer_join_consistency(self, all_backend_join_pairs):
        """Test that all backends return the same outer join results.

        Note: Outer joins use coalesce_keys=True by default, which merges duplicate
        join key columns into a single column for consistent results across backends.
        """
        results = {}

        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.outer_join(pair["left"], pair["right"], predicates="id")

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            # With coalescing, all IDs should be in single 'id' column
            # Filter out NaN values before sorting
            result_ids = result_df['id'].dropna().tolist()

            results[backend_name] = {
                "row_count": len(result_df),
                "ids": sorted(result_ids)
            }

        # All backends should have same row count
        reference_count = results["pandas"]["row_count"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["row_count"],
                reference_count,
                msg=f"{backend_name} outer join row count doesn't match pandas"
            )

        # All backends should have same IDs
        reference_ids = results["pandas"]["ids"]
        for backend_name, result_info in results.items():
            check.equal(
                set(result_info["ids"]),
                set(reference_ids),
                msg=f"{backend_name} outer join IDs don't match pandas"
            )

    def test_outer_join_includes_all_data(self, all_backend_join_pairs):
        """Test that outer join includes all data from both tables.

        Note: With coalesce_keys=True (default for outer joins), all join key values
        are merged into a single column, preventing data loss from duplicate columns.
        """
        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.outer_join(pair["left"], pair["right"], predicates="id")

            # Convert everything to pandas
            cast_factory = DataFrameCastFactory()

            result_strategy = cast_factory.get_strategy(result)
            result_df = result_strategy.to_pandas(result)

            left_strategy = cast_factory.get_strategy(pair["left"])
            left_df = left_strategy.to_pandas(pair["left"])

            right_strategy = cast_factory.get_strategy(pair["right"])
            right_df = right_strategy.to_pandas(pair["right"])

            # All IDs from both tables should be in result
            # With coalescing, all IDs are in single 'id' column (no 'id_right')
            left_ids = set(left_df['id'])
            right_ids = set(right_df['id'])
            result_ids = set(result_df['id'].dropna())  # Filter NaN if present

            all_ids = left_ids.union(right_ids)

            check.equal(
                sorted(set(result_ids)),
                sorted(set(all_ids)),
                msg=f"{backend_name} outer join doesn't include all IDs"
            )


@pytest.mark.unit
class TestCrossBackendJoinTypes:
    """Test different join type combinations across backends."""

    def test_join_type_row_counts(self, all_backend_join_pairs):
        """Test that join types produce expected row count relationships."""
        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            inner_result = strategy.inner_join(pair["left"], pair["right"], predicates="id")
            left_result = strategy.left_join(pair["left"], pair["right"], predicates="id")
            outer_result = strategy.outer_join(pair["left"], pair["right"], predicates="id")

            # Convert to pandas
            cast_factory = DataFrameCastFactory()

            inner_df = cast_factory.get_strategy(inner_result).to_pandas(inner_result)
            left_df = cast_factory.get_strategy(left_result).to_pandas(left_result)
            outer_df = cast_factory.get_strategy(outer_result).to_pandas(outer_result)

            # Verify row count relationships
            check.less_equal(
                len(inner_df),
                len(left_df),
                msg=f"{backend_name}: inner join should have <= rows than left join"
            )

            check.less_equal(
                len(left_df),
                len(outer_df),
                msg=f"{backend_name}: left join should have <= rows than outer join"
            )


@pytest.mark.unit
class TestCrossBackendRealisticJoins:
    """Test cross-backend consistency with realistic data scenarios."""

    def test_employee_department_join(self, employees_data, departments_data):
        """Test employee-department join across all backends."""
        results = {}

        # Create DataFrames in all backends
        backends = {
            "pandas": lambda d: __import__('pandas').DataFrame(d),
            "polars": lambda d: __import__('polars').DataFrame(d),
        }

        for backend_name, create_fn in backends.items():
            emp_df = create_fn(employees_data)
            dept_df = create_fn(departments_data)

            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(emp_df)

            result = strategy.inner_join(
                emp_df,
                dept_df,
                predicates="department_id"
            )

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            results[backend_name] = len(result_df)

        # All backends should have same result count
        reference_count = results["pandas"]
        for backend_name, count in results.items():
            check.equal(
                count,
                reference_count,
                msg=f"{backend_name} employee-department join count doesn't match"
            )

    def test_employee_salary_join(self, employees_data, salaries_data):
        """Test employee-salary left join across backends."""
        results = {}

        backends = {
            "pandas": lambda d: __import__('pandas').DataFrame(d),
            "polars": lambda d: __import__('polars').DataFrame(d),
        }

        for backend_name, create_fn in backends.items():
            emp_df = create_fn(employees_data)
            sal_df = create_fn(salaries_data)

            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(emp_df)

            result = strategy.left_join(
                emp_df,
                sal_df,
                predicates="employee_id"
            )

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            # Should have all employees (some without salary data)
            results[backend_name] = {
                "row_count": len(result_df),
                "employee_ids": set(result_df['employee_id'].tolist())
            }

        # All backends should preserve all employees
        reference = results["pandas"]
        for backend_name, result_info in results.items():
            check.equal(
                result_info["row_count"],
                reference["row_count"],
                msg=f"{backend_name} left join row count doesn't match"
            )

            check.equal(
                result_info["employee_ids"],
                reference["employee_ids"],
                msg=f"{backend_name} doesn't preserve all employee IDs"
            )


@pytest.mark.unit
class TestCrossBackendColumnHandling:
    """Test that column handling is consistent across backends."""

    def test_join_preserves_column_names(self, all_backend_join_pairs):
        """Test that joins preserve column names consistently."""
        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.inner_join(pair["left"], pair["right"], predicates="id")

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            # Should have columns from both tables
            expected_columns = {"id", "name", "department", "salary", "bonus"}

            check.is_true(
                expected_columns.issubset(set(result_df.columns)),
                msg=f"{backend_name} doesn't preserve expected columns"
            )

    def test_join_column_order(self, all_backend_join_pairs):
        """Test that column order is reasonable across backends."""
        for backend_name, pair in all_backend_join_pairs.items():
            factory = DataFrameJoinFactory()
            strategy = factory.get_strategy(pair["left"])

            result = strategy.inner_join(pair["left"], pair["right"], predicates="id")

            # Convert to pandas
            cast_factory = DataFrameCastFactory()
            cast_strategy = cast_factory.get_strategy(result)
            result_df = cast_strategy.to_pandas(result)

            # Join key should be in columns
            check.is_in(
                "id",
                result_df.columns,
                msg=f"{backend_name} doesn't include join key 'id'"
            )
