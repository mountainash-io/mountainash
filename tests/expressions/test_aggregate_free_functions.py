"""Multi-arg aggregates exposed as free functions."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation


@pytest.mark.xfail(
    reason=(
        "corr() requires struct context in Polars and raises NotImplementedError. "
        "The AST node and free-function wiring are correct; Polars backend "
        "does not support per-expression corr(). "
        "Tracked as a known-divergences-level gap."
    ),
    strict=True,
)
def test_corr_polars():
    df = pl.DataFrame({
        "g": ["a", "a", "a", "a"],
        "x": [1.0, 2.0, 3.0, 4.0],
        "y": [2.0, 4.0, 6.0, 8.0],
    })
    result = (
        relation(df)
        .group_by("g")
        .agg(ma.corr(ma.col("x"), ma.col("y")).alias("c"))
        .to_polars()
    )
    assert result["c"].to_list()[0] == pytest.approx(1.0)


@pytest.mark.xfail(
    reason=(
        "The Substrait median(precision, x) signature passes 2 positional args, "
        "but the Polars backend protocol is median(x) — precision is not supported. "
        "The AST node and free-function wiring are correct; backend alignment is "
        "a known-divergences-level gap."
    ),
    strict=True,
)
def test_median_polars():
    df = pl.DataFrame({"g": ["a", "a", "a"], "x": [1, 2, 3]})
    result = (
        relation(df)
        .group_by("g")
        .agg(ma.median(ma.lit(0.5), ma.col("x")).alias("m"))
        .to_polars()
    )
    assert result["m"].to_list()[0] == pytest.approx(2.0)


@pytest.mark.xfail(
    reason=(
        "The Substrait quantile(boundaries, precision, n, distribution) signature "
        "passes 4 positional args, but the Polars backend protocol is "
        "quantile(x, q=0.5, interpolation='nearest') — multi-arg form not supported. "
        "The AST node and free-function wiring are correct; backend alignment is "
        "a known-divergences-level gap."
    ),
    strict=True,
)
def test_quantile_polars():
    df = pl.DataFrame({"g": ["a", "a", "a", "a", "a"], "x": [1.0, 2.0, 3.0, 4.0, 5.0]})
    # quantile signature per protocol: (boundaries, precision, n, distribution)
    # Concrete shape verified via the existing protocol method.
    result = (
        relation(df)
        .group_by("g")
        .agg(
            ma.quantile(
                ma.lit(0.5),   # boundaries
                ma.lit(0.01),  # precision
                ma.lit(1),     # n
                ma.lit("linear"),  # distribution
            ).alias("q")
        )
        .to_polars()
    )
    # Median of 1..5 is 3
    assert result["q"].to_list()[0] == pytest.approx(3.0)


def test_corr_importable_from_top_level():
    assert ma.corr is not None


def test_median_importable_from_top_level():
    assert ma.median is not None


def test_quantile_importable_from_top_level():
    assert ma.quantile is not None
