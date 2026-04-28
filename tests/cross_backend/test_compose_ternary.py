"""Cross-backend tests for ternary fluent composition."""

import pytest
import mountainash.expressions as ma


# Ternary tests use reduced backend set — same as test_ternary.py
TERNARY_BACKENDS = [
    "polars",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
]

T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TERNARY_BACKENDS)
class TestComposeTernary:
    """Test ternary expressions with composed operands."""

    def test_ternary_with_null_safe_operand(self, backend_name, backend_factory, select_and_extract):
        """t_gt with fill_null operand: score.t_gt(threshold.fill_null(0))."""
        if backend_name == "polars":
            pytest.xfail(
                "Polars type mismatch: fill_null on nullable i64 column produces i64, "
                "but ternary comparison intermediate expects Boolean schema."
            )
        data = {
            "score": [80, None, 60],
            "threshold": [70, 50, None],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").t_gt(ma.col("threshold").fill_null(0))
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: 80 > 70 -> TRUE (1)
        # Row 1: NULL > 50 -> UNKNOWN (0)
        # Row 2: 60 > 0 (filled) -> TRUE (1)
        assert actual[0] == T_TRUE, f"[{backend_name}] Row 0: {actual[0]}"
        assert actual[1] == T_UNKNOWN, f"[{backend_name}] Row 1: {actual[1]}"
        assert actual[2] == T_TRUE, f"[{backend_name}] Row 2: {actual[2]}"

    def test_ternary_logical_chain(self, backend_name, backend_factory, select_and_extract):
        """Ternary chain: t_eq AND t_gt."""
        data = {"a": [1, 1, 0, None], "b": [5, -1, 5, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_eq(ma.lit(1)).t_and(ma.col("b").t_gt(ma.lit(0)))
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        # Row 0: (1==1)=T AND (5>0)=T -> T
        # Row 1: (1==1)=T AND (-1>0)=F -> F
        # Row 2: (0==1)=F AND ... -> F
        # Row 3: (NULL==1)=U AND (5>0)=T -> U
        assert actual[0] == T_TRUE, f"[{backend_name}] Row 0"
        assert actual[1] == T_FALSE, f"[{backend_name}] Row 1"
        assert actual[2] == T_FALSE, f"[{backend_name}] Row 2"
        assert actual[3] == T_UNKNOWN, f"[{backend_name}] Row 3"

    def test_t_col_with_composition(self, backend_name, backend_factory, get_result_count):
        """t_col with custom unknown then filter with is_true booleanizer."""
        data = {"value": [100, -999, 50, -999, 80], "active": [True, True, False, True, True]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("value", unknown={-999}).t_gt(ma.lit(60)).t_and(
            ma.col("active").t_eq(ma.lit(True))
        )
        result = df.filter(expr.compile(df, booleanizer="t_is_true"))

        count = get_result_count(result, backend_name)
        # Row 0: 100 > 60 = T AND active=T -> T (pass is_true)
        # Row 1: -999 -> UNKNOWN AND active=T -> U (fail is_true)
        # Row 2: 50 > 60 = F -> F (fail)
        # Row 3: -999 -> UNKNOWN AND active=T -> U (fail)
        # Row 4: 80 > 60 = T AND active=T -> T (pass)
        assert count == 2, f"[{backend_name}] Expected 2 with is_true, got {count}"

    def test_booleanizer_maybe_true(self, backend_name, backend_factory, get_result_count):
        """Same expression with maybe_true gives more rows."""
        data = {"value": [100, -999, 50, -999, 80], "active": [True, True, False, True, True]}
        df = backend_factory.create(data, backend_name)

        expr = ma.t_col("value", unknown={-999}).t_gt(ma.lit(60)).t_and(
            ma.col("active").t_eq(ma.lit(True))
        )
        result = df.filter(expr.compile(df, booleanizer="t_maybe_true"))

        count = get_result_count(result, backend_name)
        # maybe_true: TRUE and UNKNOWN pass
        # Row 0: T (pass), Row 1: U (pass), Row 2: F (fail), Row 3: U (pass), Row 4: T (pass)
        assert count == 4, f"[{backend_name}] Expected 4 with maybe_true, got {count}"
