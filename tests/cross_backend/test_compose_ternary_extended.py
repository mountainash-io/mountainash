"""Cross-backend tests for extended ternary operations coverage."""

import pytest
import mountainash_expressions as ma


TERNARY_BACKENDS = [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
]

T_TRUE = 1
T_UNKNOWN = 0
T_FALSE = -1


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TERNARY_BACKENDS)
class TestComposeTernarySet:
    """Test ternary set operations: t_is_in, t_is_not_in."""

    def test_t_is_in(self, backend_name, backend_factory, select_and_extract):
        """Test t_is_in: ternary set membership."""
        data = {"val": [1, 2, None, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").t_is_in([1, 2, 3])
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert actual[0] == T_TRUE, f"[{backend_name}] 1 in [1,2,3]: {actual[0]}"
        assert actual[1] == T_TRUE, f"[{backend_name}] 2 in [1,2,3]: {actual[1]}"
        assert actual[2] == T_UNKNOWN, f"[{backend_name}] None in [1,2,3]: {actual[2]}"
        assert actual[3] == T_FALSE, f"[{backend_name}] 4 in [1,2,3]: {actual[3]}"

    def test_t_is_not_in(self, backend_name, backend_factory, select_and_extract):
        """Test t_is_not_in: ternary set exclusion."""
        data = {"val": [1, 2, None, 4]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").t_is_not_in([1, 2])
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert actual[0] == T_FALSE, f"[{backend_name}] 1 not in [1,2]: {actual[0]}"
        assert actual[2] == T_UNKNOWN, f"[{backend_name}] None not in [1,2]: {actual[2]}"
        assert actual[3] == T_TRUE, f"[{backend_name}] 4 not in [1,2]: {actual[3]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TERNARY_BACKENDS)
class TestComposeTernaryLogicMultiArg:
    """Test multi-arg ternary logic: t_and(*args), t_or(*args)."""

    def test_t_and_multi_arg(self, backend_name, backend_factory, select_and_extract):
        """Test t_and with multiple arguments."""
        data = {"a": [1, 1, 0, None], "b": [1, -1, 1, 1], "c": [1, 1, 1, 1]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_eq(ma.lit(1)).t_and(
            ma.col("b").t_eq(ma.lit(1)),
            ma.col("c").t_eq(ma.lit(1)),
        )
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert actual[0] == T_TRUE, f"[{backend_name}] Row 0: T AND T AND T"
        assert actual[1] == T_FALSE, f"[{backend_name}] Row 1: T AND F AND T"
        assert actual[2] == T_FALSE, f"[{backend_name}] Row 2: F AND T AND T"
        assert actual[3] == T_UNKNOWN, f"[{backend_name}] Row 3: U AND T AND T"

    def test_t_or_multi_arg(self, backend_name, backend_factory, select_and_extract):
        """Test t_or with multiple arguments."""
        data = {"a": [-1, -1, 0, None], "b": [-1, 1, -1, -1], "c": [-1, -1, -1, 1]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_eq(ma.lit(1)).t_or(
            ma.col("b").t_eq(ma.lit(1)),
            ma.col("c").t_eq(ma.lit(1)),
        )
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert actual[0] == T_FALSE, f"[{backend_name}] Row 0: F OR F OR F"
        assert actual[1] == T_TRUE, f"[{backend_name}] Row 1: F OR T OR F"
        assert actual[2] == T_FALSE, f"[{backend_name}] Row 2: U OR F OR F -> might be U"
        assert actual[3] == T_TRUE, f"[{backend_name}] Row 3: U OR F OR T"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TERNARY_BACKENDS)
class TestComposeTernaryXor:
    """Test t_xor."""

    def test_t_xor(self, backend_name, backend_factory, select_and_extract):
        """Test t_xor: exactly one TRUE."""
        data = {"a": [1, 1, -1, None], "b": [-1, 1, -1, 1]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").t_eq(ma.lit(1)).t_xor(ma.col("b").t_eq(ma.lit(1)))
        actual = select_and_extract(df, expr.compile(df, booleanizer=None), "result", backend_name)

        assert actual[0] == T_TRUE, f"[{backend_name}] Row 0: T XOR F -> T"
        assert actual[1] == T_FALSE, f"[{backend_name}] Row 1: T XOR T -> F"
        assert actual[2] == T_FALSE, f"[{backend_name}] Row 2: F XOR F -> F"
        assert actual[3] == T_UNKNOWN, f"[{backend_name}] Row 3: U XOR T -> U"
