"""Contract tests for the option-channel helper surface."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
import polars as pl

import mountainash as ma
from expressions.argument_types._option_helpers import (
    OptionSpec,
    discrimination_probe,
    native_option_probe,
    option_result,
    xfail_option_unsupported,
)
from expressions.argument_types.conftest import ALL_BACKENDS, make_df
from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ROUNDING,
)


_FIXTURE_IDENTITY = {
    "polars": (CONST_BACKEND.POLARS, "polars"),
    "ibis": (CONST_BACKEND.IBIS, None),
    "narwhals-polars": (CONST_BACKEND.NARWHALS, "narwhals-polars"),
    "narwhals-pandas": (CONST_BACKEND.NARWHALS, "narwhals-pandas"),
}


@pytest.fixture
def isolated_capability_registry():
    snapshot = CapabilityRegistry.snapshot()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_option_result_takes_uncompiled_expr(backend):
    df = make_df({"t": ["Ab", "cd"]}, backend)

    assert option_result(df, ma.col("t").str.to_uppercase(), backend) == ["AB", "CD"]


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_discrimination_probe_detects_difference(backend):
    df = make_df({"t": ["Ab"]}, backend)

    assert discrimination_probe(
        lambda: ma.col("t").str.to_uppercase(),
        lambda: ma.col("t").str.to_lowercase(),
        df,
        backend,
    ) is True


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_discrimination_probe_reports_equal_results(backend):
    df = make_df({"t": ["Ab"]}, backend)

    assert discrimination_probe(
        lambda: ma.col("t").str.to_uppercase(),
        lambda: ma.col("t").str.to_uppercase(),
        df,
        backend,
    ) is False


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_xfail_option_unsupported_uses_fixture_family_and_dialect(monkeypatch, backend):
    expected_family, expected_dialect = _FIXTURE_IDENTITY[backend]
    calls = []

    def fake_lookup(
        operation_key, param, family, dialect=None, option_value=None
    ):
        calls.append((operation_key, param, family, dialect, option_value))
        return SimpleNamespace(
            level=CapabilityLevel.UNSUPPORTED,
            message="unsupported option value",
        )

    monkeypatch.setattr(CapabilityRegistry, "capability_for", fake_lookup)

    marker = xfail_option_unsupported(
        FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
        "s",
        "1",
        backend,
    )

    assert calls == [
        (
            FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
            "s",
            expected_family,
            expected_dialect,
            "1",
        )
    ]
    assert marker.name == "xfail"
    assert marker.kwargs["strict"] is True
    assert marker.kwargs["raises"] is BackendCapabilityError
    assert "[s=1]" in marker.kwargs["reason"]


def test_xfail_option_unsupported_is_noop_without_gating_fact(monkeypatch):
    monkeypatch.setattr(CapabilityRegistry, "capability_for", lambda *args, **kwargs: None)

    marker = xfail_option_unsupported(
        FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
        "s",
        "1",
        "polars",
    )

    assert marker.name == "usefixtures"


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_native_option_probe_bypasses_value_gate_and_compares_values(
    backend, isolated_capability_registry
):
    family, dialect = _FIXTURE_IDENTITY[backend]
    key = (
        FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
        "s",
        family,
        dialect,
        "1",
    )
    CapabilityRegistry._facts.pop(key, None)  # noqa: SLF001
    CapabilityRegistry.register_backend(
        family,
        [
            CapabilityFact(
                operation_key=FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
                param="s",
                option_value="1",
                level=CapabilityLevel.UNSUPPORTED,
                backend=family,
                dialect=dialect,
                message="temporary self-check gate",
                since="2026-07-21",
                condition="options['s'] == 1",
            )
        ],
    )
    spec = OptionSpec(
        fkey=FKEY_SUBSTRAIT_SCALAR_ROUNDING.ROUND,
        option_param="s",
        option_value="1",
        dtype="float64",
        build_expr=lambda: ma.col("v").round(1),
        reference_expr=lambda: ma.col("v").round(0),
        data={"v": [1.25, None]},
        schema={"v": pl.Float64},
    )

    gated_df = make_df(spec.data, backend, schema=spec.schema)
    with pytest.raises(BackendCapabilityError):
        option_result(gated_df, spec.build_expr(), backend)
    assert native_option_probe(spec, backend) is None
