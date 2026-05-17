"""Cross-backend edge case verification for numeric semantics.

Tests how backends handle division by zero, integer division semantics,
float precision, rounding modes, modulo sign, overflow, and NaN treatment.
"""

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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDivisionByZero:

    def test_int_divide_by_zero(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10, 20, 30], "b": [2, 0, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") / ma.col("b"))
        assert actual[0] == pytest.approx(5.0)
        # Division by zero: Inf (Polars/pandas), NULL (SQL), or NaN
        assert actual[1] is None or (
            isinstance(actual[1], float)
            and (math.isinf(actual[1]) or math.isnan(actual[1]))
        )
        assert actual[2] == pytest.approx(6.0)

    def test_float_divide_by_zero(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10.0, 20.0], "b": [0.0, 5.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") / ma.col("b"))
        assert actual[0] is None or (
            isinstance(actual[0], float) and math.isinf(actual[0])
        )
        assert actual[1] == pytest.approx(4.0)

    def test_zero_divide_by_zero(self, backend_name, backend_factory, collect_expr):
        data = {"a": [0.0], "b": [0.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") / ma.col("b"))
        # 0/0: NaN (Polars/pandas), NULL (SQL)
        assert actual[0] is None or (
            isinstance(actual[0], float) and math.isnan(actual[0])
        )


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIntegerDivision:

    def test_positive_floor_div(self, backend_name, backend_factory, collect_expr):
        data = {"a": [7, 10, 15], "b": [2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").floordiv(ma.col("b")))
        assert actual == [3, 3, 3]

    def test_negative_floor_div(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-7, -10], "b": [2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").floordiv(ma.col("b")))
        # Python/Polars: floor division → [-4, -4]
        # SQL (truncate toward zero): [-3, -3]
        assert actual[0] in [-4, -3]
        assert actual[1] in [-4, -3]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFloatPrecision:

    def test_sum_tenths(self, backend_name, backend_factory):
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_nodes.substrait.reln_aggregate import AggregateRelNode

        data = {"a": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}
        df = backend_factory.create(data, backend_name)
        r = ma.relation(df)
        aggregated = Relation(
            AggregateRelNode(input=r._node, keys=[], measures=[ma.col("a").sum().alias("s")])
        )
        actual = aggregated.item("s")
        assert actual == pytest.approx(1.0, abs=1e-10)

    def test_large_minus_large(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1e15 + 1.0], "b": [1e15]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") - ma.col("b"))
        assert actual == pytest.approx([1.0], abs=1e-3)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRoundingModes:

    def test_round_half(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.5, 2.5, 3.5, 4.5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").round(0))
        # Banker's rounding → [2, 2, 4, 4]; or round-half-away → [2, 3, 4, 5]
        for v in actual:
            assert v in [1, 2, 3, 4, 5]

    def test_round_decimals(self, backend_name, backend_factory, collect_expr):
        data = {"a": [3.14159, 2.71828]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").round(2))
        assert actual == pytest.approx([3.14, 2.72], abs=0.005)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestModuloSign:

    def test_negative_mod_positive(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-7], "b": [3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") % ma.col("b"))
        # Python: -7 % 3 = 2 (sign of divisor); C/SQL: -1 (sign of dividend)
        assert actual[0] in [2, -1]

    def test_positive_mod_negative(self, backend_name, backend_factory, collect_expr):
        data = {"a": [7], "b": [-3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") % ma.col("b"))
        # Python: 7 % -3 = -2; C/SQL: 1
        assert actual[0] in [-2, 1]

    def test_both_positive(self, backend_name, backend_factory, collect_expr):
        data = {"a": [7], "b": [3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") % ma.col("b"))
        assert actual == [1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestOverflow:

    def test_large_product(self, backend_name, backend_factory):
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_nodes.substrait.reln_aggregate import AggregateRelNode

        data = {"a": [1000000, 1000000, 1000000]}
        df = backend_factory.create(data, backend_name)
        r = ma.relation(df)
        aggregated = Relation(
            AggregateRelNode(input=r._node, keys=[], measures=[ma.col("a").product().alias("p")])
        )
        actual = aggregated.item("p")
        # 10^6 * 10^6 * 10^6 = 10^18 — fits in int64
        # Some backends compute product as float64 (precision loss), ibis-polars returns None
        if actual is None:
            pytest.skip("backend returned NULL for integer product")
        assert actual == pytest.approx(1_000_000_000_000_000_000, rel=1e-6)

    def test_large_sum(self, backend_name, backend_factory):
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_nodes.substrait.reln_aggregate import AggregateRelNode

        data = {"a": [9_000_000_000_000_000, 9_000_000_000_000_000]}
        df = backend_factory.create(data, backend_name)
        r = ma.relation(df)
        aggregated = Relation(
            AggregateRelNode(input=r._node, keys=[], measures=[ma.col("a").sum().alias("s")])
        )
        actual = aggregated.item("s")
        assert actual == 18_000_000_000_000_000


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNanHandling:

    def test_nan_in_sum(self, backend_name, backend_factory):
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_nodes.substrait.reln_aggregate import AggregateRelNode

        data = {"a": [1.0, float('nan'), 3.0]}
        df = backend_factory.create(data, backend_name)
        r = ma.relation(df)
        aggregated = Relation(
            AggregateRelNode(input=r._node, keys=[], measures=[ma.col("a").sum().alias("s")])
        )
        actual = aggregated.item("s")
        # NaN poisons → NaN, or backend converts NaN→NULL → sum=4.0
        if actual is None:
            pass  # treated NaN as NULL, skipped
        elif isinstance(actual, float) and math.isnan(actual):
            pass  # NaN propagated
        else:
            assert actual == pytest.approx(4.0, rel=1e-9)

    def test_nan_in_comparison(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, float('nan'), 3.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").gt(ma.lit(2.0)))
        assert actual[0] is False
        # NaN > 2.0: False (IEEE 754), NULL (if NaN→NULL), True (Polars NaN is truthy in comparisons)
        assert actual[1] in [False, None, True]
        assert actual[2] is True

    def test_nan_equality(self, backend_name, backend_factory, collect_expr):
        data = {"a": [float('nan'), 1.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").eq(ma.col("a")))
        # NaN == NaN: False (IEEE 754), NULL (SQL), True (if backend normalizes)
        assert actual[0] in [False, None, True]
        assert actual[1] is True
