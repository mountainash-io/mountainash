from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from tests.conform.cross_backend.test_v2_operations import _IDENTITIES, _SYSTEMS
from tests.fixtures.backend_helpers import BackendDataFrameFactory, BackendResultHelper
from tests.fixtures.backend_registry import ALL_BACKENDS
from tests.fixtures.capability_gating import assert_capability_gated


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_default_datetime_all_backends_executes_or_gates(backend_name: str) -> None:
    expr = ma.col("value").dt.parse_default(field_name="value")
    build = lambda: UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    if backend_name in {"polars", "polars-lazy"}:
        frame = BackendDataFrameFactory.create({"value": ["2024-01-02T03:04:05"]}, backend_name)
        values = BackendResultHelper.select_and_extract(frame, build(), "value", backend_name)
        assert values[0].year == 2024
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


def test_polars_xsd_duration_null_mode_validates_fractional_and_trailing_t() -> None:
    expr = ma.col("value").dt.parse_xsd_duration(
        field_name="value", failure_behavior=CaseFailureBehaviour.NULL
    )
    compiled = UnifiedExpressionVisitor(_SYSTEMS["polars"]).visit(expr._node)
    result = pl.DataFrame({"value": ["PT.5S", "P1DT"]}).select(compiled)
    assert result["value"].to_list() == ["PT.5S", None]
@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "narwhals-polars", "narwhals-pandas"])
def test_xsd_throw_mode_has_exact_residue_fact(backend_name: str) -> None:
    from mountainash.core.capabilities import CapabilityRegistry, Enforcement, ResidueSignal

    backend, dialect = _IDENTITIES[backend_name]
    fact = CapabilityRegistry.capability_for(FK_DT.PARSE_XSD_DURATION, "*", backend, dialect)
    assert fact is not None
    assert fact.enforcement is Enforcement.MATERIALIZE_RESIDUE
    assert fact.residue_signal is ResidueSignal.NON_NULL_TO_NULL
    assert not fact.native_errors
