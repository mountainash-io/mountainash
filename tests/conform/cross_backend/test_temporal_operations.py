from __future__ import annotations

from datetime import date, datetime, time

import math

import pytest

import mountainash as ma
from mountainash.core.capabilities import Boundary, CapabilityLevel, Enforcement, ResidueSignal
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from tests.conform.cross_backend.test_v2_operations import _IDENTITIES, _SYSTEMS
from tests.fixtures.backend_helpers import BackendDataFrameFactory, BackendResultHelper
from tests.fixtures.backend_registry import ALL_BACKENDS
from tests.fixtures.capability_gating import assert_capability_gated, capability_gate


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


_XSD_CASES = (
    (
        FK_DT.PARSE_XSD_DURATION,
        None,
        lambda dt, failure: dt.parse_xsd_duration(
            field_name="value", failure_behavior=failure
        ),
        ["P1D"],
        ["P1DT"],
    ),
    (
        FK_DT.PARSE_XSD_PARTIAL_DATE,
        "year",
        lambda dt, failure: dt.parse_xsd_partial_date(
            kind="year", field_name="value", failure_behavior=failure
        ),
        ["2024"],
        ["2024+14:01"],
    ),
    (
        FK_DT.PARSE_XSD_PARTIAL_DATE,
        "yearmonth",
        lambda dt, failure: dt.parse_xsd_partial_date(
            kind="yearmonth", field_name="value", failure_behavior=failure
        ),
        ["2024-01"],
        ["2024-01-14:01"],
    ),
)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "failure_behavior",
    [CaseFailureBehaviour.NULL, CaseFailureBehaviour.THROW],
)
@pytest.mark.parametrize(
    "operation_key,kind,make_expr,valid_values,invalid_values",
    _XSD_CASES,
    ids=["xsd-duration", "xsd-year", "xsd-yearmonth"],
)
def test_xsd_operations_all_backends_execute_or_hit_exact_gate(
    backend_name: str,
    failure_behavior: CaseFailureBehaviour,
    operation_key,
    kind: str | None,
    make_expr,
    valid_values: list[str],
    invalid_values: list[str],
) -> None:
    expr = make_expr(ma.col("value").dt, failure_behavior)
    build = lambda: UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    backend, dialect = _IDENTITIES[backend_name]
    fact = capability_gate(
        operation_key, backend, dialect=dialect, param="*", option_value=None
    )
    if fact is not None and fact.enforcement is Enforcement.GATE:
        assert fact.level is CapabilityLevel.UNSUPPORTED
        assert fact.enforcement is Enforcement.GATE
        assert fact.boundary is Boundary.BUILD
        assert_capability_gated(
            operation_key,
            backend,
            dialect=dialect,
            param="*",
            option_value=None,
            build=build,
        )
        return

    frame = BackendDataFrameFactory.create(
        {"value": invalid_values if failure_behavior is CaseFailureBehaviour.NULL else valid_values},
        backend_name,
    )
    values = BackendResultHelper.select_and_extract(frame, build(), "value", backend_name)
    if failure_behavior is CaseFailureBehaviour.NULL:
        assert all(value is None or (isinstance(value, float) and math.isnan(value)) for value in values)
    else:
        assert values == valid_values


@pytest.mark.parametrize("kind", ["date", "time", "datetime"])
@pytest.mark.parametrize(
    "failure_behavior",
    [CaseFailureBehaviour.NULL, CaseFailureBehaviour.THROW],
)
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_temporal_any_all_backends_execute_or_hit_exact_gate(
    backend_name: str,
    failure_behavior: CaseFailureBehaviour,
    kind: str,
) -> None:
    expr = ma.col("value").dt.parse_temporal_any(
        kind,
        field_name="value",
        failure_behavior=failure_behavior,
    )
    build = lambda: UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    backend, dialect = _IDENTITIES[backend_name]
    fact = capability_gate(
        FK_DT.PARSE_TEMPORAL_ANY,
        backend,
        dialect=dialect,
        param="*",
        option_value=None,
    )
    if fact is not None:
        assert_capability_gated(
            FK_DT.PARSE_TEMPORAL_ANY,
            backend,
            dialect=dialect,
            param="*",
            option_value=None,
            build=build,
        )
        return

    valid_values = {
        "date": ["2024-01-02"],
        "time": ["03:04:05"],
        "datetime": ["2024-01-02 03:04:05"],
    }[kind]
    invalid_values = ["not-a-temporal"]
    frame = BackendDataFrameFactory.create(
        {"value": invalid_values if failure_behavior is CaseFailureBehaviour.NULL else valid_values},
        backend_name,
    )
    values = BackendResultHelper.select_and_extract(frame, build(), "value", backend_name)
    if failure_behavior is CaseFailureBehaviour.NULL:
        assert values == [None]
    elif kind == "date":
        assert values == [date(2024, 1, 2)]
    elif kind == "time":
        assert values == [time(3, 4, 5)]
    else:
        assert values == [datetime(2024, 1, 2, 3, 4, 5)]


@pytest.mark.parametrize("kind", ["year", "yearmonth"])
@pytest.mark.parametrize(
    "failure_behavior",
    [CaseFailureBehaviour.NULL, CaseFailureBehaviour.THROW],
)
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "offset",
    ["-14:01", "+14:10", "-14:20", "+14:09", "+14:50"],
)
def test_partial_date_rejects_signed_fourteen_hour_offsets(
    backend_name: str,
    failure_behavior: CaseFailureBehaviour,
    kind: str,
    offset: str,
) -> None:
    value = f"2024{('-01' if kind == 'yearmonth' else '')}{offset}"
    expr = ma.col("value").dt.parse_xsd_partial_date(
        kind=kind,
        field_name="value",
        failure_behavior=failure_behavior,
    )
    build = lambda: UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    backend, dialect = _IDENTITIES[backend_name]
    fact = capability_gate(
        FK_DT.PARSE_XSD_PARTIAL_DATE,
        backend,
        dialect=dialect,
        param="*",
        option_value=None,
    )
    if fact is not None and fact.enforcement is Enforcement.GATE:
        assert_capability_gated(
            FK_DT.PARSE_XSD_PARTIAL_DATE,
            backend,
            dialect=dialect,
            param="*",
            option_value=None,
            build=build,
        )
        return

    frame = BackendDataFrameFactory.create({"value": [value]}, backend_name)
    if backend_name in {"polars", "polars-lazy"} and failure_behavior is CaseFailureBehaviour.THROW:
        with pytest.raises((ValueError, RuntimeError)):
            BackendResultHelper.select_and_extract(frame, build(), "value", backend_name)
        return
    values = BackendResultHelper.select_and_extract(frame, build(), "value", backend_name)
    assert all(value is None or (isinstance(value, float) and math.isnan(value)) for value in values)


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "narwhals-polars", "narwhals-pandas"])
@pytest.mark.parametrize("operation_key", [FK_DT.PARSE_XSD_DURATION, FK_DT.PARSE_XSD_PARTIAL_DATE])
def test_xsd_throw_mode_keeps_exact_residue_facts(backend_name: str, operation_key) -> None:
    from mountainash.core.capabilities import CapabilityRegistry

    backend, dialect = _IDENTITIES[backend_name]
    fact = CapabilityRegistry.capability_for(operation_key, "*", backend, dialect)
    assert fact is not None
    assert fact.level is CapabilityLevel.UNSUPPORTED
    assert fact.enforcement is Enforcement.MATERIALIZE_RESIDUE
    assert fact.boundary is Boundary.MATERIALIZE
    assert fact.residue_signal is ResidueSignal.NON_NULL_TO_NULL
    assert not fact.native_errors


@pytest.mark.parametrize("operation_key", [FK_DT.PARSE_XSD_DURATION, FK_DT.PARSE_XSD_PARTIAL_DATE])
@pytest.mark.parametrize("failure_behavior", [CaseFailureBehaviour.NULL, CaseFailureBehaviour.THROW])
def test_xsd_sqlite_has_exact_wildcard_gate(operation_key, failure_behavior) -> None:
    expr = (
        ma.col("value").dt.parse_xsd_duration(
            field_name="value", failure_behavior=failure_behavior
        )
        if operation_key is FK_DT.PARSE_XSD_DURATION
        else ma.col("value").dt.parse_xsd_partial_date(
            kind="year", field_name="value", failure_behavior=failure_behavior
        )
    )
    build = lambda: UnifiedExpressionVisitor(_SYSTEMS["ibis-sqlite"]).visit(expr._node)
    fact = capability_gate(
        operation_key,
        CONST_BACKEND.IBIS,
        dialect="ibis-sqlite",
        param="*",
        option_value=None,
    )
    assert fact is not None
    assert fact.level is CapabilityLevel.UNSUPPORTED
    assert fact.enforcement is Enforcement.GATE
    assert fact.boundary is Boundary.BUILD
    assert_capability_gated(
        operation_key,
        CONST_BACKEND.IBIS,
        dialect="ibis-sqlite",
        param="*",
        option_value=None,
        build=build,
    )
