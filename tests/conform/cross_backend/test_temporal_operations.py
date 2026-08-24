from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from tests.conform.cross_backend.test_v2_operations import _IDENTITIES, _SYSTEMS
from tests.fixtures.backend_registry import ALL_BACKENDS
from tests.fixtures.capability_gating import assert_capability_gated


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_default_datetime_all_backends_executes_or_gates(backend_name: str) -> None:
    expr = ma.col("value").dt.parse_default(field_name="value")
    build = lambda: UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    if backend_name == "polars":
        result = pl.DataFrame({"value": ["2024-01-02T03:04:05"]}).select(build())
        assert result["value"].item().year == 2024
        return
    backend, dialect = _IDENTITIES[backend_name]
    assert_capability_gated(
        FK_DT.PARSE_DEFAULT, backend, dialect=dialect, param="*", option_value=None, build=build
    )


@pytest.mark.parametrize("kind", ["date", "time", "datetime"])
def test_polars_temporal_any_null_mode_returns_typed_null(kind: str) -> None:
    expr = ma.col("value").dt.parse_temporal_any(
        kind, field_name="value", failure_behavior=CaseFailureBehaviour.NULL
    )
    compiled = UnifiedExpressionVisitor(_SYSTEMS["polars"]).visit(expr._node)
    result = pl.DataFrame({"value": ["not-a-temporal"]}).select(compiled)
    assert result["value"].item() is None


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite", "narwhals-polars", "narwhals-pandas"])
def test_xsd_throw_mode_is_exactly_gated_on_non_polars(backend_name: str) -> None:
    expr = ma.col("value").dt.parse_xsd_duration(
        field_name="value", failure_behavior=CaseFailureBehaviour.THROW
    )
    build = lambda: UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    backend, dialect = _IDENTITIES[backend_name]
    assert_capability_gated(
        FK_DT.PARSE_XSD_DURATION, backend, dialect=dialect, param="failure_behavior", option_value="throw", build=build
    )
