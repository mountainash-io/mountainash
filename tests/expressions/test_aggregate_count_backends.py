"""Verify each backend's aggregate_generic.count_records implementation exists."""
from __future__ import annotations

import pytest


def test_polars_count_records_exists():
    from mountainash.expressions.backends.expression_systems.polars.substrait.expsys_pl_aggregate_generic import (
        SubstraitPolarsAggregateGenericExpressionSystem,
    )
    # Must be concretely implemented in the backend class, not just inherited from protocol stub
    assert "count_records" in SubstraitPolarsAggregateGenericExpressionSystem.__dict__, (
        "count_records must be implemented in SubstraitPolarsAggregateGenericExpressionSystem"
    )


def test_narwhals_count_records_exists():
    pytest.importorskip("narwhals")
    from mountainash.expressions.backends.expression_systems.narwhals.substrait.expsys_nw_aggregate_generic import (
        SubstraitNarwhalsAggregateGenericExpressionSystem,
    )
    assert "count_records" in SubstraitNarwhalsAggregateGenericExpressionSystem.__dict__, (
        "count_records must be implemented in SubstraitNarwhalsAggregateGenericExpressionSystem"
    )


def test_ibis_count_records_exists():
    pytest.importorskip("ibis")
    from mountainash.expressions.backends.expression_systems.ibis.substrait.expsys_ib_aggregate_generic import (
        SubstraitIbisAggregateGenericExpressionSystem,
    )
    assert "count_records" in SubstraitIbisAggregateGenericExpressionSystem.__dict__, (
        "count_records must be implemented in SubstraitIbisAggregateGenericExpressionSystem"
    )
