"""Cross-backend result verification for comparison and arithmetic extensions."""

from __future__ import annotations

import math

import pytest

import mountainash as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

NARWHALS_BACKENDS = {"pandas", "narwhals-polars", "narwhals-pandas"}
IBIS_BACKENDS = {"ibis-polars", "ibis-duckdb", "ibis-sqlite"}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIsBetween:
    def test_is_between_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(5, 15))
        assert actual == [False, True, True, True, False]

    def test_is_between_boundary(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 15]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(5, 15))
        assert actual == [True, True]

    def test_is_between_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 10]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(0, 20))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is True


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIsIn:
    def test_is_in_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([2, 4]))
        assert actual == [False, True, False, True, False]

    def test_is_in_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([1, 3]))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is True

    def test_is_in_no_match(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([99, 100]))
        assert actual == [False, False, False]

    def test_is_in_strings(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["apple", "banana", "cherry"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in(["banana", "cherry"]))
        assert actual == [False, True, True]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestAbs:
    def test_abs_positive(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").abs())
        assert actual == [1, 2, 3]

    def test_abs_negative(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-5, -10, 0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").abs())
        assert actual == [5, 10, 0]

    def test_abs_floats(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-1.5, 2.5, -3.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").abs())
        assert actual == pytest.approx([1.5, 2.5, 3.0])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSign:
    def test_sign_mixed(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("sign() not supported by Narwhals backend")
        data = {"a": [-5.0, 0.0, 3.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").sign())
        assert actual == pytest.approx([-1.0, 0.0, 1.0])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSqrt:
    def test_sqrt_perfect_squares(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("sqrt() not supported by Narwhals backend")
        data = {"a": [4.0, 9.0, 16.0, 25.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").sqrt())
        assert actual == pytest.approx([2.0, 3.0, 4.0, 5.0])

    def test_sqrt_zero(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("sqrt() not supported by Narwhals backend")
        data = {"a": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").sqrt())
        assert actual == pytest.approx([0.0, 1.0])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCbrt:
    def test_cbrt_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [8.0, 27.0, 64.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").cbrt())
        assert actual == pytest.approx([2.0, 3.0, 4.0], rel=1e-6)

    def test_cbrt_negative(self, backend_name, backend_factory, collect_expr):
        pytest.xfail("cbrt of negative values returns NaN on all backends")
        data = {"a": [-8.0, -27.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").cbrt())
        assert actual == pytest.approx([-2.0, -3.0], rel=1e-6)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExp:
    def test_exp_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("exp() not supported by Narwhals backend")
        data = {"a": [0.0, 1.0, 2.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").exp())
        assert actual == pytest.approx([1.0, math.e, math.e**2], rel=1e-9)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLog:
    def test_log_base10(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, 10.0, 100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").log(10))
        assert actual == pytest.approx([0.0, 1.0, 2.0, 3.0], rel=1e-9)

    def test_log_base_e(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, math.e, math.e**2]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").log(math.e))
        assert actual == pytest.approx([0.0, 1.0, 2.0], rel=1e-6)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestClip:
    def test_clip_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").clip(5, 15))
        assert actual == [5, 5, 10, 15, 15]

    def test_clip_floats(self, backend_name, backend_factory, collect_expr):
        data = {"a": [0.5, 1.5, 2.5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").clip(1.0, 2.0))
        assert actual == pytest.approx([1.0, 1.5, 2.0])

    def test_clip_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 20]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").clip(5, 15))
        assert actual[0] == 5
        assert actual[1] is None
        assert actual[2] == 15


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCot:
    def test_cot_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_BACKENDS:
            pytest.xfail("tan() not supported by Narwhals backend (cot = 1/tan)")
        if backend_name in IBIS_BACKENDS:
            pytest.xfail("Ibis deferred type inference error in cot (1/tan) division")
        data = {"a": [math.pi / 4, math.pi / 2]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").cot())
        assert actual[0] == pytest.approx(1.0, rel=1e-6)
        assert actual[1] == pytest.approx(0.0, abs=1e-10)
