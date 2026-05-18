"""
Cross-backend tests for native expression passthrough.

Tests the "escape hatch" functionality that allows wrapping backend-native
expressions (e.g., pl.col("a") > 5) in the abstract expression system.

Key test cases:
- Native expression passthrough (compile returns the original expression)
- Combining native with abstract expressions via and_, or_, etc.
- Backend matching validation

IMPORTANT: Native expressions are backend-specific. A Polars expression
cannot be used with an Ibis table. These tests validate that native
expressions work correctly when the backend matches.
"""

import pytest
import mountainash.expressions as ma
import polars as pl
import narwhals as nw
import ibis


# =============================================================================
# Polars Native Expression Tests
# =============================================================================

@pytest.mark.cross_backend
class TestPolarsNativeExpressions:
    """Test native Polars expressions wrapped in the abstract API."""

    def test_native_polars_passthrough(self, backend_factory, get_result_count):
        """Native Polars expression should pass through unchanged."""
        data = {"a": [1, 5, 10, 15, 20], "b": ["x", "y", "z", "w", "v"]}
        df = backend_factory.create(data, "polars")

        # Create native Polars expression
        native_expr = pl.col("a") > 5

        # Wrap in abstract API
        ma_expr = ma.native(native_expr)

        # Compile and filter
        compiled = ma_expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        assert count == 3, f"Expected 3 rows where a > 5, got {count}"

    def test_native_polars_with_abstract_and(self, backend_factory, get_result_count):
        """Native expression combined with abstract via AND."""
        data = {"a": [1, 5, 10, 15, 20], "b": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, "polars")

        # Native: a > 5
        # Abstract: b < 45
        native_part = ma.native(pl.col("a") > 5)
        abstract_part = ma.col("b").lt(45)
        combined = native_part.and_(abstract_part)

        compiled = combined.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a > 5 gives [10, 15, 20], b < 45 gives [10, 20, 30, 40]
        # Intersection: rows where a=10,b=30 and a=15,b=40 → 2 rows
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_native_polars_with_abstract_or(self, backend_factory, get_result_count):
        """Native expression combined with abstract via OR."""
        data = {"a": [1, 5, 10, 15, 20], "b": [50, 40, 30, 20, 10]}
        df = backend_factory.create(data, "polars")

        # Native: a == 1
        # Abstract: b == 10
        native_part = ma.native(pl.col("a") == 1)
        abstract_part = ma.col("b").eq(10)
        combined = native_part.or_(abstract_part)

        compiled = combined.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a == 1 gives row 0, b == 10 gives row 4 → 2 rows
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_native_polars_complex_expression(self, backend_factory, get_result_count):
        """Native expression with complex Polars operations."""
        data = {"text": ["hello", "HELLO", "world", "WORLD", "test"]}
        df = backend_factory.create(data, "polars")

        # Use a complex Polars operation that might not be in abstract API
        native_expr = pl.col("text").str.to_uppercase() == "HELLO"

        ma_expr = ma.native(native_expr)
        compiled = ma_expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # "hello" and "HELLO" both become "HELLO" → 2 rows
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_native_polars_arithmetic(self, backend_factory, get_result_count):
        """Native Polars arithmetic expression."""
        data = {"a": [1, 2, 3, 4, 5], "b": [5, 4, 3, 2, 1]}
        df = backend_factory.create(data, "polars")

        # Native arithmetic: a + b == 6
        native_expr = (pl.col("a") + pl.col("b")) == 6

        ma_expr = ma.native(native_expr)
        compiled = ma_expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # All rows have a+b=6 → 5 rows
        assert count == 5, f"Expected 5 rows, got {count}"


# =============================================================================
# Narwhals Native Expression Tests
# =============================================================================

@pytest.mark.cross_backend
class TestNarwhalsNativeExpressions:
    """Test native Narwhals expressions wrapped in the abstract API."""

    def test_native_narwhals_passthrough(self, backend_factory, get_result_count):
        """Native Narwhals expression should pass through unchanged."""
        data = {"a": [1, 5, 10, 15, 20], "b": ["x", "y", "z", "w", "v"]}
        df = backend_factory.create(data, "narwhals")

        # Create native Narwhals expression
        native_expr = nw.col("a") > 5

        # Wrap in abstract API
        ma_expr = ma.native(native_expr)

        # Compile and filter
        compiled = ma_expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "narwhals")
        assert count == 3, f"Expected 3 rows where a > 5, got {count}"

    def test_native_narwhals_with_abstract_and(self, backend_factory, get_result_count):
        """Native Narwhals expression combined with abstract via AND."""
        data = {"a": [1, 5, 10, 15, 20], "b": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, "narwhals")

        # Native: a > 5
        # Abstract: b < 45
        native_part = ma.native(nw.col("a") > 5)
        abstract_part = ma.col("b").lt(45)
        combined = native_part.and_(abstract_part)

        compiled = combined.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "narwhals")
        assert count == 2, f"Expected 2 rows, got {count}"


# =============================================================================
# Ibis Native Expression Tests
# =============================================================================

@pytest.mark.cross_backend
class TestIbisNativeExpressions:
    """Test native Ibis expressions wrapped in the abstract API."""

    def test_native_ibis_polars_passthrough(self, backend_factory, get_result_count):
        """Native Ibis expression should pass through unchanged (Polars backend)."""
        data = {"a": [1, 5, 10, 15, 20], "b": ["x", "y", "z", "w", "v"]}
        df = backend_factory.create(data, "ibis-polars")

        # Create native Ibis expression using the table's column
        native_expr = df.a > 5

        # Wrap in abstract API
        ma_expr = ma.native(native_expr)

        # Compile and filter
        compiled = ma_expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "ibis-polars")
        assert count == 3, f"Expected 3 rows where a > 5, got {count}"

    def test_native_ibis_duckdb_passthrough(self, backend_factory, get_result_count):
        """Native Ibis expression should pass through unchanged (DuckDB backend)."""
        data = {"a": [1, 5, 10, 15, 20], "b": ["x", "y", "z", "w", "v"]}
        df = backend_factory.create(data, "ibis-duckdb")

        # Create native Ibis expression
        native_expr = df.a > 5

        # Wrap in abstract API
        ma_expr = ma.native(native_expr)

        # Compile and filter
        compiled = ma_expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "ibis-duckdb")
        assert count == 3, f"Expected 3 rows where a > 5, got {count}"

    def test_native_ibis_with_abstract_and(self, backend_factory, get_result_count):
        """Native Ibis expression combined with abstract via AND."""
        data = {"a": [1, 5, 10, 15, 20], "b": [10, 20, 30, 40, 50]}
        df = backend_factory.create(data, "ibis-polars")

        # Native: a > 5
        # Abstract: b < 45
        native_part = ma.native(df.a > 5)
        abstract_part = ma.col("b").lt(45)
        combined = native_part.and_(abstract_part)

        compiled = combined.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "ibis-polars")
        assert count == 2, f"Expected 2 rows, got {count}"


# =============================================================================
# Automatic Native Expression Recognition (No ma.native() wrapper needed)
# =============================================================================

@pytest.mark.cross_backend
class TestAutomaticNativeRecognition:
    """Test that native expressions are automatically recognized without ma.native().

    The ExpressionParameter class should automatically detect and handle
    backend-native expressions when passed as operands to abstract expressions.
    This means users don't always need to wrap with ma.native().
    """

    def test_polars_native_auto_recognized_in_and(self, backend_factory, get_result_count):
        """Polars native expression auto-recognized in and_() operand."""
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, "polars")

        # Pass native Polars expression directly WITHOUT ma.native()
        expr = ma.col("a").gt(5).and_(pl.col("a") < 18)

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a > 5 AND a < 18: [10, 15] → 2 rows
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_polars_native_auto_recognized_in_or(self, backend_factory, get_result_count):
        """Polars native expression auto-recognized in or_() operand."""
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, "polars")

        # Pass native Polars expression directly WITHOUT ma.native()
        expr = ma.col("a").eq(1).or_(pl.col("a") == 20)

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a == 1 OR a == 20: [1, 20] → 2 rows
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_narwhals_native_auto_recognized(self, backend_factory, get_result_count):
        """Narwhals native expression auto-recognized in operand."""
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, "narwhals")

        # Pass native Narwhals expression directly WITHOUT ma.native()
        expr = ma.col("a").gt(5).and_(nw.col("a") < 18)

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "narwhals")
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_ibis_native_auto_recognized(self, backend_factory, get_result_count):
        """Ibis native expression auto-recognized in operand."""
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, "ibis-polars")

        # Pass native Ibis expression directly WITHOUT ma.native()
        # Note: Ibis columns are accessed via table.column
        expr = ma.col("a").gt(5).and_(df.a < 18)

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "ibis-polars")
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_multiple_native_operands_auto_recognized(self, backend_factory, get_result_count):
        """Multiple native expressions auto-recognized in chain."""
        data = {"a": [1, 5, 10, 15, 20], "b": [100, 80, 60, 40, 20]}
        df = backend_factory.create(data, "polars")

        # Chain with multiple native expressions WITHOUT ma.native()
        expr = ma.col("a").gt(5).and_(pl.col("a") < 18).and_(pl.col("b") > 30)

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a > 5: [10, 15, 20], a < 18: [1, 5, 10, 15], b > 30: [100, 80, 60, 40]
        # Combined: a=10 (b=60), a=15 (b=40) → 2 rows
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_native_in_complex_boolean_tree(self, backend_factory, get_result_count):
        """Native expressions work in complex boolean expression trees."""
        data = {"a": [1, 5, 10, 15, 20], "b": [20, 15, 10, 5, 1]}
        df = backend_factory.create(data, "polars")

        # (a > 5 AND native(a < 18)) OR (native(b > 10))
        left = ma.col("a").gt(5).and_(pl.col("a") < 18)
        right = ma.col("b").gt(10)
        expr = left.or_(right)

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # left: a=10,15 → 2 rows (indices 2,3)
        # right: b>10 → b=20,15 → 2 rows (indices 0,1)
        # Combined (OR): indices 0,1,2,3 → 4 rows
        assert count == 4, f"Expected 4 rows, got {count}"


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

@pytest.mark.cross_backend
class TestNativeExpressionEdgeCases:
    """Test edge cases for native expressions."""

    def test_native_chained_with_multiple_abstracts(self, backend_factory, get_result_count):
        """Native expression chained with multiple abstract operations."""
        data = {"a": [1, 5, 10, 15, 20], "b": [100, 80, 60, 40, 20], "c": [1, 1, 2, 2, 3]}
        df = backend_factory.create(data, "polars")

        # Chain: native(a > 5) AND b > 30 AND c < 3
        expr = (
            ma.native(pl.col("a") > 5)
            .and_(ma.col("b").gt(30))
            .and_(ma.col("c").lt(3))
        )

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a>5: [10,15,20], b>30: [100,80,60,40], c<3: [1,1,2,2]
        # Row with a=10,b=60,c=2 and a=15,b=40,c=2 → 2 rows
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_native_with_not(self, backend_factory, get_result_count):
        """Native expression can be negated."""
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, "polars")

        # NOT (a > 10) → a <= 10
        expr = ma.native(pl.col("a") > 10).not_()

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a <= 10: [1, 5, 10] → 3 rows
        assert count == 3, f"Expected 3 rows, got {count}"

    def test_abstract_with_native_operand(self, backend_factory, get_result_count):
        """Abstract expression with native expression as operand."""
        data = {"a": [1, 5, 10, 15, 20], "b": [5, 5, 5, 5, 5]}
        df = backend_factory.create(data, "polars")

        # Abstract AND with native on the right side
        # a < 15 AND native(b == 5)
        expr = ma.col("a").lt(15).and_(ma.native(pl.col("b") == 5))

        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # a < 15: [1, 5, 10], b == 5: all rows → 3 rows
        assert count == 3, f"Expected 3 rows, got {count}"

    def test_native_preserves_expression_type(self, backend_factory):
        """Native expression should preserve the original expression type."""
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, "polars")

        native_expr = pl.col("a") * 2
        ma_expr = ma.native(native_expr)
        compiled = ma_expr.compile(df)

        # The compiled expression should be a Polars Expr
        assert isinstance(compiled, pl.Expr), f"Expected pl.Expr, got {type(compiled)}"

    def test_backend_mismatch_polars_native_with_ibis_fails(self, backend_factory):
        """Polars native expression with Ibis DataFrame should fail."""
        data = {"a": [1, 5, 10, 15, 20]}
        df_ibis = backend_factory.create(data, "ibis-polars")

        # Create a Polars native expression
        polars_native = pl.col("a") > 5

        # Combine with abstract expression
        expr = ma.col("a").gt(3).and_(polars_native)

        # Should fail at compile time with clear backend mismatch error
        with pytest.raises(TypeError, match="Backend mismatch.*polars.*ibis"):
            expr.compile(df_ibis)

    def test_backend_mismatch_ibis_native_with_polars_fails(self, backend_factory):
        """Ibis native expression with Polars DataFrame should fail."""
        data = {"a": [1, 5, 10, 15, 20]}
        df_polars = backend_factory.create(data, "polars")
        df_ibis = backend_factory.create(data, "ibis-polars")

        # Create an Ibis native expression (requires the table reference)
        ibis_native = df_ibis.a > 5

        # Combine with abstract expression
        expr = ma.col("a").gt(3).and_(ibis_native)

        # Should fail at compile time with clear backend mismatch error
        with pytest.raises(TypeError, match="Backend mismatch.*ibis.*polars"):
            expr.compile(df_polars)

    def test_backend_mismatch_narwhals_native_with_ibis_fails(self, backend_factory):
        """Narwhals native expression with Ibis DataFrame should fail."""
        data = {"a": [1, 5, 10, 15, 20]}
        df_ibis = backend_factory.create(data, "ibis-polars")

        # Create a Narwhals native expression
        narwhals_native = nw.col("a") > 5

        # Combine with abstract expression
        expr = ma.col("a").gt(3).and_(narwhals_native)

        # Should fail at compile time with clear backend mismatch error
        with pytest.raises(TypeError, match="Backend mismatch.*narwhals.*ibis"):
            expr.compile(df_ibis)


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.cross_backend
class TestNativeIntegration:
    """Integration tests for native expressions with real use cases."""

    def test_escape_hatch_for_unsupported_operation(self, backend_factory, get_result_count):
        """Use native as escape hatch for operations not in abstract API."""
        data = {"values": [1, 2, None, 4, None]}
        df = backend_factory.create(data, "polars")

        # Use native for fill_null which might have specific behavior
        # Combine with abstract comparison
        native_filled = pl.col("values").fill_null(0)
        native_check = native_filled > 0

        expr = ma.native(native_check)
        compiled = expr.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # After fill_null(0): [1,2,0,4,0], > 0: [1,2,4] → 3 rows
        assert count == 3, f"Expected 3 rows, got {count}"

    def test_mixed_native_and_abstract_pipeline(self, backend_factory, get_result_count):
        """Complex pipeline mixing native and abstract expressions."""
        data = {
            "category": ["A", "B", "A", "B", "C"],
            "value": [10, 20, 30, 40, 50],
            "active": [True, True, False, True, False]
        }
        df = backend_factory.create(data, "polars")

        # Build complex filter:
        # (category in ["A", "B"]) AND (value > 15 OR active == True)
        category_filter = ma.col("category").is_in(["A", "B"])
        value_filter = ma.native(pl.col("value") > 15)
        active_filter = ma.col("active").eq(True)

        combined = category_filter.and_(value_filter.or_(active_filter))

        compiled = combined.compile(df)
        result = df.filter(compiled)

        count = get_result_count(result, "polars")
        # category in [A,B]: rows 0,1,2,3
        # value > 15 OR active: row 0 (active), row 1 (both), row 2 (value>15), row 3 (both)
        # Combined: rows 0, 1, 3 (row 2 has active=False and value=30>15 but category=A is fine)
        # Actually let me recalculate:
        # Row 0: cat=A (yes), value=10>15? no, active=True (yes) → yes
        # Row 1: cat=B (yes), value=20>15 (yes), active=True (yes) → yes
        # Row 2: cat=A (yes), value=30>15 (yes), active=False (no) → yes (value passes)
        # Row 3: cat=B (yes), value=40>15 (yes), active=True (yes) → yes
        # Row 4: cat=C (no) → no
        # Result: 4 rows
        assert count == 4, f"Expected 4 rows, got {count}"
