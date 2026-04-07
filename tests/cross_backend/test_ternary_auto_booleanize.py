"""
Cross-backend tests for automatic booleanization of ternary expressions.

Tests the automatic conversion of ternary expressions (-1/0/1 sentinels)
to boolean (True/False) when they exit "ternary land".

Features tested:
1. compile() auto-booleanization with default is_true()
2. compile() with explicit booleanizer parameter
3. compile() with booleanizer=None for raw sentinels
4. Namespace-level coercion (ternary → boolean when chaining)
5. Namespace-level coercion (boolean → ternary when chaining)
6. Edge cases (double-wrapping prevention, explicit booleanizers)

All tests run across backends: Polars, Narwhals, and Ibis (Polars/DuckDB).
"""

import pytest
import mountainash.expressions as ma


# Ternary constant values for raw sentinel assertions
T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1


# =============================================================================
# Test: Auto-Booleanization on compile()
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestAutoBooleanizeOnCompile:
    """Test automatic booleanization when compile() is called on ternary expressions."""

    def test_default_booleanizer_is_true(self, backend_name, backend_factory, select_and_extract):
        """Test that compile() defaults to is_true() booleanizer for ternary."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        # Ternary comparison without explicit booleanizer
        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df)  # Default: booleanizer="is_true"

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # is_true: TRUE(1) → True, else → False
        assert values[0] is True, f"[{backend_name}] 80 > 70 (TRUE) should be True"
        assert values[1] is False, f"[{backend_name}] NULL > 70 (UNKNOWN) should be False with is_true"
        assert values[2] is False, f"[{backend_name}] 60 > 70 (FALSE) should be False"

    def test_booleanizer_maybe_true(self, backend_name, backend_factory, select_and_extract):
        """Test compile() with booleanizer='maybe_true' (lenient)."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer="maybe_true")

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # maybe_true: TRUE or UNKNOWN → True, FALSE → False
        assert values[0] is True, f"[{backend_name}] TRUE should be True"
        assert values[1] is True, f"[{backend_name}] UNKNOWN should be True with maybe_true"
        assert values[2] is False, f"[{backend_name}] FALSE should be False"

    def test_booleanizer_is_false(self, backend_name, backend_factory, select_and_extract):
        """Test compile() with booleanizer='is_false'."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer="is_false")

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # is_false: FALSE(-1) → True, else → False
        assert values[0] is False, f"[{backend_name}] TRUE should be False"
        assert values[1] is False, f"[{backend_name}] UNKNOWN should be False"
        assert values[2] is True, f"[{backend_name}] FALSE should be True with is_false"

    def test_booleanizer_is_unknown(self, backend_name, backend_factory, select_and_extract):
        """Test compile() with booleanizer='is_unknown'."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer="is_unknown")

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # is_unknown: UNKNOWN(0) → True, else → False
        assert values[0] is False, f"[{backend_name}] TRUE should be False"
        assert values[1] is True, f"[{backend_name}] UNKNOWN should be True with is_unknown"
        assert values[2] is False, f"[{backend_name}] FALSE should be False"

    def test_booleanizer_is_known(self, backend_name, backend_factory, select_and_extract):
        """Test compile() with booleanizer='is_known'."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer="is_known")

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # is_known: TRUE or FALSE → True, UNKNOWN → False
        assert values[0] is True, f"[{backend_name}] TRUE should be True with is_known"
        assert values[1] is False, f"[{backend_name}] UNKNOWN should be False with is_known"
        assert values[2] is True, f"[{backend_name}] FALSE should be True with is_known"

    def test_booleanizer_maybe_false(self, backend_name, backend_factory, select_and_extract):
        """Test compile() with booleanizer='maybe_false'."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer="maybe_false")

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # maybe_false: FALSE or UNKNOWN → True, TRUE → False
        assert values[0] is False, f"[{backend_name}] TRUE should be False with maybe_false"
        assert values[1] is True, f"[{backend_name}] UNKNOWN should be True with maybe_false"
        assert values[2] is True, f"[{backend_name}] FALSE should be True with maybe_false"

    def test_booleanizer_none_returns_raw_sentinels(self, backend_name, backend_factory, select_and_extract):
        """Test compile() with booleanizer=None returns raw -1/0/1 values."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer=None)  # Raw sentinels

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Raw sentinel values
        assert values[0] == T_TRUE, f"[{backend_name}] 80 > 70 should be 1 (TRUE)"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] NULL > 70 should be 0 (UNKNOWN)"
        assert values[2] == T_FALSE, f"[{backend_name}] 60 > 70 should be -1 (FALSE)"

    def test_explicit_booleanizer_not_double_wrapped(self, backend_name, backend_factory, select_and_extract):
        """Test that explicit .is_true() is not double-wrapped."""
        data = {
            "score": [80, None, 60],
        }
        df = backend_factory.create(data, backend_name)

        # User explicitly calls is_true() - should not be wrapped again
        expr = ma.col("score").t_gt(70).is_true()
        backend_expr = expr.compile(df)  # Already terminal, no wrapping

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] is True
        assert values[1] is False
        assert values[2] is False

    def test_boolean_expression_not_booleanized(self, backend_name, backend_factory, select_and_extract):
        """Test that boolean expressions are not affected by booleanizer."""
        data = {
            "score": [80, 50, 60],
        }
        df = backend_factory.create(data, backend_name)

        # Boolean expression - not ternary
        expr = ma.col("score").gt(70)
        backend_expr = expr.compile(df)  # Should work normally

        values = select_and_extract(df, backend_expr, "result", backend_name)

        assert values[0] is True, f"[{backend_name}] 80 > 70 should be True"
        assert values[1] is False, f"[{backend_name}] 50 > 70 should be False"
        assert values[2] is False, f"[{backend_name}] 60 > 70 should be False"


# =============================================================================
# Test: Namespace-Level Coercion (Ternary → Boolean)
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTernaryToBooleanCoercion:
    """Test automatic ternary → boolean coercion when chaining operations."""

    def test_ternary_and_boolean_chained(self, backend_name, backend_factory, select_and_extract):
        """Test t_gt().and_(boolean_expr) auto-coerces ternary to boolean."""
        data = {
            "score": [80, None, 60, 90],
            "active": [True, True, True, False],
        }
        df = backend_factory.create(data, backend_name)

        # Ternary expression chained with boolean AND
        # t_gt(70) produces ternary, and_() expects boolean -> auto is_true()
        expr = ma.col("score").t_gt(70).and_(ma.col("active").eq(True))
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: is_true(TRUE) AND True = True AND True = True
        # Row 1: is_true(UNKNOWN) AND True = False AND True = False
        # Row 2: is_true(FALSE) AND True = False AND True = False
        # Row 3: is_true(TRUE) AND False = True AND False = False
        assert values[0] is True, f"[{backend_name}] TRUE AND active should be True"
        assert values[1] is False, f"[{backend_name}] UNKNOWN AND active should be False"
        assert values[2] is False, f"[{backend_name}] FALSE AND active should be False"
        assert values[3] is False, f"[{backend_name}] TRUE AND inactive should be False"

    def test_ternary_or_boolean_chained(self, backend_name, backend_factory, select_and_extract):
        """Test t_lt().or_(boolean_expr) auto-coerces ternary to boolean."""
        data = {
            "score": [80, None, 60],
            "active": [False, False, False],
        }
        df = backend_factory.create(data, backend_name)

        # t_lt(70) OR active
        expr = ma.col("score").t_lt(70).or_(ma.col("active").eq(True))
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: is_true(FALSE) OR False = False OR False = False
        # Row 1: is_true(UNKNOWN) OR False = False OR False = False
        # Row 2: is_true(TRUE) OR False = True OR False = True
        assert values[0] is False, f"[{backend_name}] FALSE OR inactive"
        assert values[1] is False, f"[{backend_name}] UNKNOWN OR inactive"
        assert values[2] is True, f"[{backend_name}] TRUE OR inactive"


# =============================================================================
# Test: Namespace-Level Coercion (Boolean → Ternary)
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestBooleanToTernaryCoercion:
    """Test automatic boolean → ternary coercion when chaining operations."""

    def test_boolean_t_and_ternary_chained(self, backend_name, backend_factory, select_and_extract):
        """Test boolean_expr.t_and(ternary_expr) auto-coerces boolean to ternary."""
        data = {
            "active": [True, True, False, True],
            "score": [80, None, 60, 60],
        }
        df = backend_factory.create(data, backend_name)

        # Boolean expression used in ternary context -> auto to_ternary()
        # active (bool) becomes ternary (1 or -1), then t_and with t_gt result
        expr = ma.col("active").eq(True).t_and(ma.col("score").t_gt(70))
        backend_expr = expr.compile(df, booleanizer=None)  # Get raw sentinels

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: to_ternary(True)=1 t_and TRUE=1 -> min(1,1) = 1 (TRUE)
        # Row 1: to_ternary(True)=1 t_and UNKNOWN=0 -> min(1,0) = 0 (UNKNOWN)
        # Row 2: to_ternary(False)=-1 t_and FALSE=-1 -> min(-1,-1) = -1 (FALSE)
        # Row 3: to_ternary(True)=1 t_and FALSE=-1 -> min(1,-1) = -1 (FALSE)
        assert values[0] == T_TRUE, f"[{backend_name}] True t_and TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] True t_and UNKNOWN"
        assert values[2] == T_FALSE, f"[{backend_name}] False t_and FALSE"
        assert values[3] == T_FALSE, f"[{backend_name}] True t_and FALSE"


# =============================================================================
# Test: Edge Cases
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestEdgeCases:
    """Test edge cases for auto-booleanization."""

    def test_nested_ternary_operations(self, backend_name, backend_factory, select_and_extract):
        """Test nested ternary operations are booleanized only at the top level."""
        data = {
            "a": [80, None, 60],
            "b": [70, 70, None],
        }
        df = backend_factory.create(data, backend_name)

        # (a > 70) t_and (b >= 70) - both comparisons are ternary
        expr = ma.col("a").t_gt(70).t_and(ma.col("b").t_ge(70))
        backend_expr = expr.compile(df)  # Default: is_true

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: TRUE t_and TRUE = TRUE -> is_true -> True
        # Row 1: UNKNOWN t_and TRUE = UNKNOWN -> is_true -> False
        # Row 2: FALSE t_and UNKNOWN = FALSE -> is_true -> False
        assert values[0] is True
        assert values[1] is False
        assert values[2] is False

    def test_custom_callable_booleanizer(self, backend_name, backend_factory, select_and_extract):
        """Test compile() with a custom callable booleanizer."""
        data = {
            "score": [80, None, 60],
        }
        df = backend_factory.create(data, backend_name)

        # Custom booleanizer that uses maybe_true
        def custom_booleanizer(api):
            return api.maybe_true()

        expr = ma.col("score").t_gt(70)
        backend_expr = expr.compile(df, booleanizer=custom_booleanizer)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Same as maybe_true
        assert values[0] is True
        assert values[1] is True
        assert values[2] is False

    def test_invalid_booleanizer_raises_error(self, backend_name, backend_factory):
        """Test that invalid booleanizer string raises ValueError."""
        data = {"score": [80]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(70)

        with pytest.raises(ValueError, match="Unknown booleanizer"):
            expr.compile(df, booleanizer="invalid_booleanizer")

    def test_complex_mixed_chain(self, backend_name, backend_factory, select_and_extract):
        """Test complex chain mixing ternary and boolean operations."""
        data = {
            "score": [80, None, 60, 90],
            "active": [True, True, True, True],
            "premium": [False, True, False, True],
        }
        df = backend_factory.create(data, backend_name)

        # Complex: (score > 70 in ternary) AND (active OR premium)
        # The ternary part should be auto-booleanized when combined with boolean
        ternary_part = ma.col("score").t_gt(70)
        boolean_part = ma.col("active").eq(True).or_(ma.col("premium").eq(True))
        expr = ternary_part.and_(boolean_part)
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: is_true(TRUE) AND (True OR False) = True AND True = True
        # Row 1: is_true(UNKNOWN) AND (True OR True) = False AND True = False
        # Row 2: is_true(FALSE) AND (True OR False) = False AND True = False
        # Row 3: is_true(TRUE) AND (True OR True) = True AND True = True
        assert values[0] is True
        assert values[1] is False
        assert values[2] is False
        assert values[3] is True


# =============================================================================
# Test: Additional Ternary → Boolean Coercion Cases
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTernaryToBooleanCoercionExtended:
    """Extended tests for ternary → boolean coercion."""

    def test_ternary_not_to_boolean(self, backend_name, backend_factory, select_and_extract):
        """Test ternary_expr.not_() auto-coerces ternary to boolean first."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        # t_gt(70) is ternary, .not_() is boolean -> auto-coerce with is_true first
        expr = ma.col("score").t_gt(70).not_()
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # is_true(TRUE) = True -> NOT True = False
        # is_true(UNKNOWN) = False -> NOT False = True
        # is_true(FALSE) = False -> NOT False = True
        assert values[0] is False, f"[{backend_name}] NOT is_true(TRUE)"
        assert values[1] is True, f"[{backend_name}] NOT is_true(UNKNOWN)"
        assert values[2] is True, f"[{backend_name}] NOT is_true(FALSE)"

    def test_ternary_xor_boolean_coercion(self, backend_name, backend_factory, select_and_extract):
        """Test ternary_expr.xor_(boolean_expr) auto-coerces ternary."""
        data = {
            "score": [80, None, 60, 90],
            "flag": [True, True, False, False],
        }
        df = backend_factory.create(data, backend_name)

        # t_gt(70) XOR flag
        expr = ma.col("score").t_gt(70).xor_(ma.col("flag").eq(True))
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: is_true(TRUE) XOR True = True XOR True = False
        # Row 1: is_true(UNKNOWN) XOR True = False XOR True = True
        # Row 2: is_true(FALSE) XOR False = False XOR False = False
        # Row 3: is_true(TRUE) XOR False = True XOR False = True
        assert values[0] is False, f"[{backend_name}] True XOR True"
        assert values[1] is True, f"[{backend_name}] False XOR True"
        assert values[2] is False, f"[{backend_name}] False XOR False"
        assert values[3] is True, f"[{backend_name}] True XOR False"

    def test_ternary_xor_parity_boolean_coercion(self, backend_name, backend_factory, select_and_extract):
        """Test ternary_expr.xor_parity() auto-coerces ternary."""
        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB XOR semantics differ for chained boolean parity")
        data = {
            "a": [80, None, 60],
            "b": [True, True, True],
            "c": [True, False, True],
        }
        df = backend_factory.create(data, backend_name)

        # xor_parity: True if odd number of operands are True
        expr = ma.col("a").t_gt(70).xor_parity(
            ma.col("b").eq(True),
            ma.col("c").eq(True)
        )
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: is_true(TRUE)=True, True, True -> 3 Trues (odd) -> True
        # Row 1: is_true(UNKNOWN)=False, True, False -> 1 True (odd) -> True
        # Row 2: is_true(FALSE)=False, True, True -> 2 Trues (even) -> False
        assert values[0] is True, f"[{backend_name}] 3 Trues (odd)"
        assert values[1] is True, f"[{backend_name}] 1 True (odd)"
        assert values[2] is False, f"[{backend_name}] 2 Trues (even)"


# =============================================================================
# Test: Additional Boolean → Ternary Coercion Cases
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestBooleanToTernaryCoercionExtended:
    """Extended tests for boolean → ternary coercion."""

    def test_boolean_t_or_ternary_chained(self, backend_name, backend_factory, select_and_extract):
        """Test boolean_expr.t_or(ternary_expr) auto-coerces boolean to ternary."""
        data = {
            "active": [False, False, True, False],
            "score": [80, None, 60, 60],
        }
        df = backend_factory.create(data, backend_name)

        # Boolean in ternary context -> auto to_ternary()
        expr = ma.col("active").eq(True).t_or(ma.col("score").t_gt(70))
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: to_ternary(False)=-1 t_or TRUE=1 -> max(-1,1) = 1 (TRUE)
        # Row 1: to_ternary(False)=-1 t_or UNKNOWN=0 -> max(-1,0) = 0 (UNKNOWN)
        # Row 2: to_ternary(True)=1 t_or FALSE=-1 -> max(1,-1) = 1 (TRUE)
        # Row 3: to_ternary(False)=-1 t_or FALSE=-1 -> max(-1,-1) = -1 (FALSE)
        assert values[0] == T_TRUE, f"[{backend_name}] False t_or TRUE"
        assert values[1] == T_UNKNOWN, f"[{backend_name}] False t_or UNKNOWN"
        assert values[2] == T_TRUE, f"[{backend_name}] True t_or FALSE"
        assert values[3] == T_FALSE, f"[{backend_name}] False t_or FALSE"

    def test_boolean_t_not_coercion(self, backend_name, backend_factory, select_and_extract):
        """Test boolean_expr.t_not() auto-coerces boolean to ternary."""
        data = {
            "active": [True, False],
        }
        df = backend_factory.create(data, backend_name)

        # Boolean expression in ternary NOT context
        expr = ma.col("active").eq(True).t_not()
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # to_ternary(True)=1 -> t_not -> -1 (FALSE)
        # to_ternary(False)=-1 -> t_not -> 1 (TRUE)
        assert values[0] == T_FALSE, f"[{backend_name}] t_not(True)"
        assert values[1] == T_TRUE, f"[{backend_name}] t_not(False)"

    def test_boolean_t_xor_coercion(self, backend_name, backend_factory, select_and_extract):
        """Test boolean_expr.t_xor(ternary_expr) coercion."""
        data = {
            "active": [True, False, True, False],
            "score": [80, 80, 60, 60],  # TRUE, TRUE, FALSE, FALSE for t_gt(70)
        }
        df = backend_factory.create(data, backend_name)

        # Boolean t_xor ternary
        expr = ma.col("active").eq(True).t_xor(ma.col("score").t_gt(70))
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # t_xor returns TRUE if exactly one operand is TRUE
        # Row 0: True(1) t_xor TRUE(1) -> both TRUE -> FALSE
        # Row 1: False(-1) t_xor TRUE(1) -> exactly one TRUE -> TRUE
        # Row 2: True(1) t_xor FALSE(-1) -> exactly one TRUE -> TRUE
        # Row 3: False(-1) t_xor FALSE(-1) -> no TRUE -> FALSE
        assert values[0] == T_FALSE, f"[{backend_name}] True t_xor TRUE"
        assert values[1] == T_TRUE, f"[{backend_name}] False t_xor TRUE"
        assert values[2] == T_TRUE, f"[{backend_name}] True t_xor FALSE"
        assert values[3] == T_FALSE, f"[{backend_name}] False t_xor FALSE"


# =============================================================================
# Test: Multiple Operands with Auto-Coercion
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestMultipleOperandsCoercion:
    """Test auto-coercion with multiple operands in and_/or_/t_and/t_or."""

    def test_boolean_and_multiple_ternary_operands(self, backend_name, backend_factory, select_and_extract):
        """Test and_(ternary1, ternary2) coerces all ternary operands."""
        data = {
            "a": [80, 80, 60],  # TRUE, TRUE, FALSE for t_gt(70)
            "b": [90, 60, 90],  # TRUE, FALSE, TRUE for t_gt(70)
            "base": [True, True, True],
        }
        df = backend_factory.create(data, backend_name)

        # base AND a>70 AND b>70 - both ternary operands should be coerced
        expr = ma.col("base").and_(
            ma.col("a").t_gt(70),
            ma.col("b").t_gt(70)
        )
        backend_expr = expr.compile(df)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: True AND True AND True = True
        # Row 1: True AND True AND False = False
        # Row 2: True AND False AND True = False
        assert values[0] is True
        assert values[1] is False
        assert values[2] is False

    def test_ternary_t_and_multiple_boolean_operands(self, backend_name, backend_factory, select_and_extract):
        """Test t_and(boolean1, boolean2) coerces all boolean operands."""
        data = {
            "score": [80, None, 60],  # TRUE, UNKNOWN, FALSE for t_gt(70)
            "a": [True, True, True],
            "b": [True, False, True],
        }
        df = backend_factory.create(data, backend_name)

        # score>70 t_and a t_and b
        expr = ma.col("score").t_gt(70).t_and(
            ma.col("a").eq(True),
            ma.col("b").eq(True)
        )
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: TRUE t_and 1 t_and 1 = min(1,1,1) = 1
        # Row 1: UNKNOWN t_and 1 t_and -1 = min(0,1,-1) = -1
        # Row 2: FALSE t_and 1 t_and 1 = min(-1,1,1) = -1
        assert values[0] == T_TRUE
        assert values[1] == T_FALSE  # min includes -1
        assert values[2] == T_FALSE

    def test_ternary_t_or_multiple_mixed_operands(self, backend_name, backend_factory, select_and_extract):
        """Test t_or with mix of boolean and ternary operands."""
        data = {
            "score": [60, None, 80],  # FALSE, UNKNOWN, TRUE for t_gt(70)
            "active": [False, False, False],
            "premium": [True, False, False],
        }
        df = backend_factory.create(data, backend_name)

        # score>70 t_or active t_or premium
        expr = ma.col("score").t_gt(70).t_or(
            ma.col("active").eq(True),
            ma.col("premium").eq(True)
        )
        backend_expr = expr.compile(df, booleanizer=None)

        values = select_and_extract(df, backend_expr, "result", backend_name)

        # Row 0: FALSE t_or -1 t_or 1 = max(-1,-1,1) = 1 (TRUE)
        # Row 1: UNKNOWN t_or -1 t_or -1 = max(0,-1,-1) = 0 (UNKNOWN)
        # Row 2: TRUE t_or -1 t_or -1 = max(1,-1,-1) = 1 (TRUE)
        assert values[0] == T_TRUE
        assert values[1] == T_UNKNOWN
        assert values[2] == T_TRUE


# =============================================================================
# Test: Filtering with Auto-Booleanization
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestFilteringWithAutoBooleanization:
    """Test that auto-booleanization works correctly in filter operations."""

    def test_filter_ternary_default_strict(self, backend_name, backend_factory, get_result_count):
        """Test filtering with ternary expression uses strict is_true by default."""
        data = {
            "score": [80, None, 90, 60, None],
        }
        df = backend_factory.create(data, backend_name)

        # Filter using ternary comparison - default is_true (strict)
        expr = ma.col("score").t_gt(70)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Only TRUE values: 80 > 70 and 90 > 70 (NULLs become False)
        assert count == 2, f"[{backend_name}] Expected 2 with is_true, got {count}"

    def test_filter_ternary_lenient(self, backend_name, backend_factory, get_result_count):
        """Test filtering with maybe_true includes UNKNOWN rows."""
        data = {
            "score": [80, None, 90, 60, None],
        }
        df = backend_factory.create(data, backend_name)

        # Filter using ternary with maybe_true (lenient)
        expr = ma.col("score").t_gt(70)
        result = df.filter(expr.compile(df, booleanizer="maybe_true"))

        count = get_result_count(result, backend_name)
        # TRUE and UNKNOWN: 80, None, 90, None = 4 rows
        assert count == 4, f"[{backend_name}] Expected 4 with maybe_true, got {count}"

    def test_filter_complex_ternary_chain(self, backend_name, backend_factory, get_result_count):
        """Test filtering with complex ternary chain auto-booleanizes correctly."""
        data = {
            "income": [80000, 90000, None, 60000, 75000],
            "credit": [750, None, 720, 650, 700],
        }
        df = backend_factory.create(data, backend_name)

        # Complex: income > 70000 AND credit >= 700
        expr = ma.col("income").t_gt(70000).t_and(ma.col("credit").t_ge(700))
        result = df.filter(expr.compile(df))  # Default: is_true

        count = get_result_count(result, backend_name)
        # Row 0: T AND T = T -> include
        # Row 1: T AND U = U -> exclude (is_true)
        # Row 2: U AND T = U -> exclude (is_true)
        # Row 3: F AND F = F -> exclude
        # Row 4: T AND T = T -> include
        assert count == 2, f"[{backend_name}] Expected 2 strictly eligible, got {count}"


# =============================================================================
# Test: All Ternary Comparison Operators
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestAllTernaryComparisonOperators:
    """Test that all ternary comparison operators work with auto-booleanization."""

    def test_t_eq_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test t_eq with default auto-booleanization."""
        data = {"a": [1, None, 2]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_eq(1)
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert values[0] is True   # 1 == 1 -> TRUE -> is_true -> True
        assert values[1] is False  # NULL == 1 -> UNKNOWN -> is_true -> False
        assert values[2] is False  # 2 == 1 -> FALSE -> is_true -> False

    def test_t_ne_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test t_ne with default auto-booleanization."""
        data = {"a": [1, None, 2]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_ne(1)
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert values[0] is False  # 1 != 1 -> FALSE -> is_true -> False
        assert values[1] is False  # NULL != 1 -> UNKNOWN -> is_true -> False
        assert values[2] is True   # 2 != 1 -> TRUE -> is_true -> True

    def test_t_ge_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test t_ge with default auto-booleanization."""
        data = {"a": [80, 70, None, 60]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_ge(70)
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert values[0] is True   # 80 >= 70 -> TRUE
        assert values[1] is True   # 70 >= 70 -> TRUE
        assert values[2] is False  # NULL >= 70 -> UNKNOWN -> False
        assert values[3] is False  # 60 >= 70 -> FALSE

    def test_t_le_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test t_le with default auto-booleanization."""
        data = {"a": [60, 70, None, 80]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_le(70)
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert values[0] is True   # 60 <= 70 -> TRUE
        assert values[1] is True   # 70 <= 70 -> TRUE
        assert values[2] is False  # NULL <= 70 -> UNKNOWN -> False
        assert values[3] is False  # 80 <= 70 -> FALSE


# =============================================================================
# Test: Ternary Constants with Auto-Booleanization
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestTernaryConstantsAutoBooleanization:
    """Test ternary constants with auto-booleanization."""

    def test_always_true_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test always_true() is auto-booleanized to True."""
        data = {"id": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.always_true()
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        for val in values:
            assert val is True, f"[{backend_name}] always_true should become True"

    def test_always_false_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test always_false() is auto-booleanized to False."""
        data = {"id": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.always_false()
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        for val in values:
            assert val is False, f"[{backend_name}] always_false should become False"

    def test_always_unknown_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test always_unknown() is auto-booleanized to False with is_true."""
        data = {"id": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.always_unknown()
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        for val in values:
            assert val is False, f"[{backend_name}] always_unknown should become False with is_true"

    def test_always_unknown_maybe_true(self, backend_name, backend_factory, select_and_extract):
        """Test always_unknown() becomes True with maybe_true booleanizer."""
        data = {"id": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.always_unknown()
        values = select_and_extract(df, expr.compile(df, booleanizer="maybe_true"), "result", backend_name)

        for val in values:
            assert val is True, f"[{backend_name}] always_unknown should become True with maybe_true"


# =============================================================================
# Test: Collection Operations with Auto-Booleanization
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestCollectionOperationsAutoBooleanization:
    """Test ternary collection operations with auto-booleanization."""

    def test_t_is_in_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test t_is_in() is auto-booleanized correctly."""
        data = {"status": ["A", "B", None, "C"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("status").t_is_in(["A", "B"])
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert values[0] is True   # "A" in [A,B] -> TRUE -> True
        assert values[1] is True   # "B" in [A,B] -> TRUE -> True
        assert values[2] is False  # NULL in [A,B] -> UNKNOWN -> False
        assert values[3] is False  # "C" in [A,B] -> FALSE -> False

    def test_t_is_not_in_auto_booleanize(self, backend_name, backend_factory, select_and_extract):
        """Test t_is_not_in() is auto-booleanized correctly."""
        data = {"status": ["A", "B", None, "C"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("status").t_is_not_in(["A", "B"])
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert values[0] is False  # "A" not in [A,B] -> FALSE -> False
        assert values[1] is False  # "B" not in [A,B] -> FALSE -> False
        assert values[2] is False  # NULL not in [A,B] -> UNKNOWN -> False
        assert values[3] is True   # "C" not in [A,B] -> TRUE -> True


# =============================================================================
# Test: Deep Nesting and Complex Chains
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
])
class TestDeepNestingAndComplexChains:
    """Test deeply nested and complex expression chains."""

    def test_deeply_nested_ternary(self, backend_name, backend_factory, select_and_extract):
        """Test deeply nested ternary operations."""
        data = {
            "a": [80, None, 60, 90],
            "b": [70, 70, None, 70],
            "c": [1, 2, 3, 4],
        }
        df = backend_factory.create(data, backend_name)

        # ((a > 70) t_and (b >= 70)) t_or (c == 3)
        inner = ma.col("a").t_gt(70).t_and(ma.col("b").t_ge(70))
        expr = inner.t_or(ma.col("c").t_eq(3))
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Row 0: (T t_and T) t_or F = T t_or F = T -> True
        # Row 1: (U t_and T) t_or F = U t_or F = U -> False
        # Row 2: (F t_and U) t_or T = F t_or T = T -> True (c==3)
        # Row 3: (T t_and T) t_or F = T t_or F = T -> True
        assert values[0] is True
        assert values[1] is False
        assert values[2] is True
        assert values[3] is True

    def test_alternating_ternary_boolean_chain(self, backend_name, backend_factory, select_and_extract):
        """Test chain that alternates between ternary and boolean contexts."""
        data = {
            "score": [80, None, 60],
            "active": [True, True, True],
        }
        df = backend_factory.create(data, backend_name)

        # Start ternary, go boolean, back to ternary, then boolean again
        # t_gt(70) -> and_(active) -> t_and(t_eq(True)) -> or_(False)
        expr = (
            ma.col("score").t_gt(70)  # ternary
            .and_(ma.col("active").eq(True))  # coerce to bool, do boolean AND
            .t_and(ma.col("active").eq(True))  # coerce back to ternary
            .or_(ma.lit(False))  # coerce to bool for final OR
        )
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Complex chain - verify it compiles and runs without error
        # The exact values depend on coercion semantics
        assert values[0] is True   # All conditions true
        assert values[1] is False  # UNKNOWN becomes False
        assert values[2] is False  # FALSE in ternary

    def test_ternary_in_both_operand_positions(self, backend_name, backend_factory, select_and_extract):
        """Test ternary expressions on both sides of boolean operation."""
        data = {
            "a": [80, None, 60, 90],
            "b": [70, 80, None, 60],
        }
        df = backend_factory.create(data, backend_name)

        # (a > 70) AND (b > 70) - both are ternary, combined with boolean AND
        expr = ma.col("a").t_gt(70).and_(ma.col("b").t_gt(70))
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Row 0: is_true(T) AND is_true(F) = True AND False = False
        # Row 1: is_true(U) AND is_true(T) = False AND True = False
        # Row 2: is_true(F) AND is_true(U) = False AND False = False
        # Row 3: is_true(T) AND is_true(F) = True AND False = False
        assert values[0] is False  # 80>70=T, 70>70=F
        assert values[1] is False  # UNKNOWN
        assert values[2] is False  # UNKNOWN
        assert values[3] is False  # 90>70=T, 60>70=F

    def test_triple_ternary_t_and(self, backend_name, backend_factory, select_and_extract):
        """Test three ternary comparisons combined with t_and."""
        data = {
            "a": [80, 80, 80, 60],
            "b": [90, 90, None, 90],
            "c": [100, 50, 100, 100],
        }
        df = backend_factory.create(data, backend_name)

        # a > 70 AND b > 70 AND c > 70 (all ternary)
        expr = ma.col("a").t_gt(70).t_and(
            ma.col("b").t_gt(70),
            ma.col("c").t_gt(70)
        )
        values = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Row 0: T t_and T t_and T = T -> True
        # Row 1: T t_and T t_and F = F -> False
        # Row 2: T t_and U t_and T = U -> False
        # Row 3: F t_and T t_and T = F -> False
        assert values[0] is True
        assert values[1] is False
        assert values[2] is False
        assert values[3] is False
