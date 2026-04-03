"""Cross-backend tests for cross-namespace fluent composition."""

import pytest
from datetime import datetime
import mountainash.expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeCrossNamespace:
    """Test expressions combining different namespaces."""

    def test_string_length_and_numeric_filter(self, backend_name, backend_factory, get_result_count):
        """String + comparison: name length > 3 AND score >= 80."""
        data = {"name": ["Al", "Bob", "Charlotte", "Diana"], "score": [90, 60, 85, 70]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.len().gt(3).and_(ma.col("score").ge(80))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 1, f"[{backend_name}] Expected 1 (Charlotte/85), got {count}"

    def test_string_upper_or_age_filter(self, backend_name, backend_factory, get_result_count):
        """String + boolean: uppercased name is 'ADMIN' OR age > 30."""
        data = {"name": ["admin", "user", "guest", "Admin"], "age": [25, 35, 20, 28]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.upper().eq(ma.lit("ADMIN")).or_(ma.col("age").gt(30))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # admin->ADMIN matches, user age 35 matches, Admin->ADMIN matches = 3
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"

    def test_datetime_year_and_string_status(self, backend_name, backend_factory, get_result_count):
        """Datetime + string: year is 2024 AND lowercased status is 'active'."""
        data = {
            "ts": [datetime(2024, 1, 1), datetime(2024, 6, 1), datetime(2023, 1, 1), datetime(2024, 9, 1)],
            "status": ["Active", "INACTIVE", "Active", "ACTIVE"],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.year().eq(2024).and_(
            ma.col("status").str.lower().eq(ma.lit("active"))
        )
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: 2024 + active -> yes
        # Row 1: 2024 + inactive -> no
        # Row 2: 2023 -> no
        # Row 3: 2024 + active -> yes
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_arithmetic_and_string_contains(self, backend_name, backend_factory, get_result_count):
        """Arithmetic + string: (price * qty) > 1000 AND name contains 'premium'."""
        data = {
            "name": ["premium widget", "basic bolt", "premium gear", "standard"],
            "price": [100, 200, 500, 300],
            "qty": [5, 3, 3, 10],
        }
        df = backend_factory.create(data, backend_name)

        expr = (ma.col("price") * ma.col("qty")).gt(1000).and_(
            ma.col("name").str.contains("premium")
        )
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # premium widget: 500 > 1000? No
        # basic bolt: 600 > 1000? No
        # premium gear: 1500 > 1000 AND premium? Yes
        # standard: 3000 > 1000 but no premium? No
        assert count == 1, f"[{backend_name}] Expected 1 (premium gear), got {count}"

    def test_null_fill_and_string_length(self, backend_name, backend_factory, get_result_count):
        """Null + comparison + string: fill_null then gt, AND string length > 0."""
        data = {
            "value": [10, None, 30, None],
            "label": ["yes", "no", "", "ok"],
            "threshold": [5, 5, 5, 5],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").fill_null(0).gt(ma.col("threshold")).and_(
            ma.col("label").str.len().gt(0)
        )
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: 10 > 5 AND len("yes") > 0 -> yes
        # Row 1: 0 > 5 -> no
        # Row 2: 30 > 5 AND len("") > 0 -> no (empty string)
        # Row 3: 0 > 5 -> no
        assert count == 1, f"[{backend_name}] Expected 1, got {count}"

    def test_arithmetic_rounding_comparison(self, backend_name, backend_factory, get_result_count):
        """Arithmetic + rounding + comparison: (price * 1.07).round(2) > 100."""
        # Data chosen so round(2) and round(0) produce DIFFERENT filter counts.
        # 93.5 * 1.07 = 100.045 → round(2) = 100.05 → yes (> 100)
        #                        → round(0) = 100    → no  (not > 100)
        # 95 * 1.07 = 101.65 → yes either way
        # 100 * 1.07 = 107.00 → yes either way
        # 50 * 1.07 = 53.50 → no either way
        data = {"price": [93.5, 95.0, 100.0, 50.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").multiply(ma.lit(1.07)).round(2).gt(ma.lit(100.0))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # With round(2): 100.05, 101.65, 107.00, 53.50 → 3 above 100
        # With round(0): 100, 102, 107, 54 → 2 above 100 (100 is NOT > 100)
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"

    def test_range_check_and_boolean(self, backend_name, backend_factory, get_result_count):
        """Range check + boolean: score in [60, 90] AND active."""
        data = {
            "score": [45, 65, 75, 85, 95],
            "min_score": [60, 60, 60, 60, 60],
            "max_score": [90, 90, 90, 90, 90],
            "active": [True, True, False, True, True],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").ge(ma.col("min_score")).and_(
            ma.col("score").le(ma.col("max_score"))
        ).and_(ma.col("active").eq(True))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 45: out of range
        # 65: in range, active -> yes
        # 75: in range, not active -> no
        # 85: in range, active -> yes
        # 95: out of range
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"
