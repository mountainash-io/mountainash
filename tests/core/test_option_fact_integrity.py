"""Closed-by-default integrity for literal option disposition cells.

The production matrix is deliberately empty until the arithmetic slice drains
its named gaps.  Synthetic self-checks below prove the helpers do not become
vacuous while that is true.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from expressions.argument_types import option_disposition as disposition
from expressions.argument_types._option_helpers import OptionSpec
from expressions.argument_types.option_disposition import (
    OPTION_DISPOSITIONS,
    REGISTERED_OPTION_PROBES,
    OptionCell,
    OptionProbeRegistration,
    cell_fact_key,
    cell_key,
    expected_option_cells,
    fact_key,
    probe_key,
    resolve_cell_fact,
    validate_option_registries,
)
from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    load_all_capability_declarations,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)


# Consumers that enumerate facts must bootstrap declarations first (F8).
load_all_capability_declarations()

_GATING = (CapabilityLevel.UNSUPPORTED, CapabilityLevel.LITERAL_ONLY)


@pytest.fixture
def isolated_option_state():
    fact_snapshot = CapabilityRegistry.snapshot()
    cells = list(OPTION_DISPOSITIONS)
    probes = list(REGISTERED_OPTION_PROBES)
    try:
        yield
    finally:
        CapabilityRegistry.restore(fact_snapshot)
        OPTION_DISPOSITIONS[:] = cells
        REGISTERED_OPTION_PROBES[:] = probes


def _option_fact_keys() -> set[tuple[object, str, str, CONST_BACKEND, str | None]]:
    return {
        fact_key(fact)
        for fact in CapabilityRegistry.facts()
        if fact.option_value is not None and fact.level in _GATING
    }


def test_dispositions_cover_exactly_the_expected_cells() -> None:
    expected = expected_option_cells()
    dispositioned = {cell_key(cell) for cell in OPTION_DISPOSITIONS}
    assert dispositioned == expected, (
        f"missing: {expected - dispositioned}; extra: {dispositioned - expected}"
    )


def test_declared_cells_and_option_facts_are_mutually_backed() -> None:
    fact_keys = _option_fact_keys()
    declared_keys = {
        cell_fact_key(cell)
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "declared_unsupported"
    }
    assert fact_keys == declared_keys, (
        f"fact/cell mismatch: facts-only={fact_keys - declared_keys}; "
        f"cells-only={declared_keys - fact_keys}"
    )


def test_honored_cells_and_discriminator_probes_are_mutually_backed() -> None:
    honored = {
        cell_key(cell)
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "honored"
    }
    registered = {
        probe_key(probe)
        for probe in REGISTERED_OPTION_PROBES
        if probe.disposition == "honored"
    }
    assert registered == honored, (
        f"probe/cell mismatch: probes-only={registered - honored}; "
        f"cells-only={honored - registered}"
    )


def test_declared_cells_and_native_failure_probes_are_mutually_backed() -> None:
    declared = {
        cell_key(cell)
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "declared_unsupported"
    }
    registered = {
        probe_key(probe)
        for probe in REGISTERED_OPTION_PROBES
        if probe.disposition == "declared_unsupported"
    }
    assert registered == declared, (
        f"probe/cell mismatch: probes-only={registered - declared}; "
        f"cells-only={declared - registered}"
    )


def test_option_registries_are_well_formed() -> None:
    validate_option_registries()


def test_probe_exempt_cells_have_dialect_scoped_expr_capable_facts() -> None:
    cell_keys = {
        cell_fact_key(cell)
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "probe_exempt"
    }
    fact_keys = {
        fact_key(fact)
        for fact in CapabilityRegistry.facts()
        if fact.option_value is not None
        and fact.level is CapabilityLevel.EXPR_CAPABLE
        and fact.probe_exempt
    }
    assert cell_keys == fact_keys, (
        f"probe-exempt fact/cell mismatch: facts-only={fact_keys - cell_keys}; "
        f"cells-only={cell_keys - fact_keys}"
    )
    for cell in OPTION_DISPOSITIONS:
        if cell.disposition != "probe_exempt":
            continue
        fact = resolve_cell_fact(cell)
        assert fact is not None, cell
        assert fact.level is CapabilityLevel.EXPR_CAPABLE, cell
        assert fact.dialect == cell_fact_key(cell)[4], cell
        assert fact.probe_exempt, cell


def test_unreasoned_introspected_param_enters_expected_cells(monkeypatch) -> None:
    """Removing a gap grows expectations without consulting dispositions."""
    param = SimpleNamespace(
        protocol_name="SubstraitScalarArithmeticExpressionSystemProtocol",
        op_name="modulus",
        param_name="division_type",
        kind="option",
    )
    monkeypatch.setattr(disposition, "introspect_protocols", lambda: [param])
    monkeypatch.setattr(disposition, "_KNOWN_UNTESTED_OPTION_PARAMS", {})
    monkeypatch.setattr(
        disposition,
        "OPTION_DOMAINS",
        {("modulus", "division_type"): frozenset({"FLOOR"})},
    )
    monkeypatch.setattr(
        disposition,
        "OPTION_DTYPES",
        {("modulus", "division_type"): frozenset({"int64"})},
    )
    monkeypatch.setattr(disposition, "ALL_BACKENDS", ["narwhals-polars", "narwhals-pandas"])

    assert expected_option_cells() == {
        (FK_ARITH.MODULO, "division_type", "narwhals-polars", "FLOOR", "int64"),
        (FK_ARITH.MODULO, "division_type", "narwhals-pandas", "FLOOR", "int64"),
    }


def test_reasoned_introspected_param_is_the_only_expected_exclusion(monkeypatch) -> None:
    param = SimpleNamespace(
        protocol_name="SubstraitScalarArithmeticExpressionSystemProtocol",
        op_name="modulus",
        param_name="division_type",
        kind="option",
    )
    monkeypatch.setattr(disposition, "introspect_protocols", lambda: [param])
    monkeypatch.setattr(
        disposition,
        "_KNOWN_UNTESTED_OPTION_PARAMS",
        {(param.protocol_name, param.op_name, param.param_name): object()},
    )
    monkeypatch.setattr(disposition, "OPTION_DOMAINS", {})
    monkeypatch.setattr(disposition, "OPTION_DTYPES", {})

    assert expected_option_cells() == set()


def test_representative_dtype_policy_exactly_covers_arithmetic_domain_owners() -> None:
    expected = {
        key: (
            ("int8",)
            if key[1] == "overflow"
            else ("int64",)
            if key == ("modulus", "division_type")
            else ("float64",)
        )
        for key in disposition.OPTION_DOMAINS
    }
    assert disposition.OPTION_DTYPES == expected
    assert set(disposition.OPTION_DTYPES) == set(disposition.OPTION_DOMAINS)


def test_cell_and_fact_keys_preserve_fkey_fixture_and_narwhals_dialect(
    isolated_option_state,
) -> None:
    cells = [
        OptionCell(
            FK_ARITH.ABS,
            "SubstraitScalarArithmeticExpressionSystemProtocol",
            "abs",
            "overflow",
            fixture,
            "ERROR",
            "int8",
            "declared_unsupported",
        )
        for fixture in ("narwhals-polars", "narwhals-pandas")
    ]
    for cell in cells:
        _, _, option_value, family, dialect = cell_fact_key(cell)
        CapabilityRegistry.register_backend(
            family,
            [
                CapabilityFact(
                    operation_key=cell.fkey,
                    param=cell.param,
                    option_value=option_value,
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=family,
                    dialect=dialect,
                    message="synthetic per-fixture gate",
                    since="2026-07-21",
                    condition="options['overflow'] == 'ERROR'",
                )
            ],
        )

    assert {cell_key(cell) for cell in cells} == {
        (FK_ARITH.ABS, "overflow", "narwhals-polars", "ERROR", "int8"),
        (FK_ARITH.ABS, "overflow", "narwhals-pandas", "ERROR", "int8"),
    }
    assert {cell_fact_key(cell) for cell in cells} == _option_fact_keys()
    assert all(resolve_cell_fact(cell) is not None for cell in cells)


def test_honored_probe_registration_remains_per_fixture(isolated_option_state) -> None:
    cells = [
        OptionCell(
            FK_ARITH.MODULO,
            "SubstraitScalarArithmeticExpressionSystemProtocol",
            "modulus",
            "division_type",
            fixture,
            "FLOOR",
            "int64",
            "honored",
        )
        for fixture in ("narwhals-polars", "narwhals-pandas")
    ]
    OPTION_DISPOSITIONS.extend(cells)
    for cell in cells:
        spec = OptionSpec(
            fkey=cell.fkey,
            option_param=cell.param,
            option_value=cell.value,
            dtype=cell.dtype,
            build_expr=lambda: None,
            reference_expr=lambda: None,
            data={},
        )
        REGISTERED_OPTION_PROBES.append(
            OptionProbeRegistration(spec, cell.fixture, "honored")
        )

    honored = {
        cell_key(cell)
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "honored"
    }
    assert honored == {probe_key(probe) for probe in REGISTERED_OPTION_PROBES} == {
        (FK_ARITH.MODULO, "division_type", "narwhals-polars", "FLOOR", "int64"),
        (FK_ARITH.MODULO, "division_type", "narwhals-pandas", "FLOOR", "int64"),
    }


@pytest.mark.parametrize("bad_disposition", ["", "supported", "arbitrary"])
def test_disposition_registry_rejects_unknown_labels(
    isolated_option_state, bad_disposition
) -> None:
    OPTION_DISPOSITIONS.append(
        OptionCell(
            FK_ARITH.ABS, "P", "abs", "overflow", "polars", "ERROR", "int8",
            bad_disposition,
        )
    )
    with pytest.raises(AssertionError, match="invalid option disposition"):
        validate_option_registries()


def test_disposition_registry_rejects_duplicate_cell_keys(isolated_option_state) -> None:
    cell = OptionCell(
        FK_ARITH.ABS, "P", "abs", "overflow", "polars", "ERROR", "int8", "invalid"
    )
    OPTION_DISPOSITIONS.extend([cell, cell])
    with pytest.raises(AssertionError, match="duplicate option disposition"):
        validate_option_registries()


def test_probe_registry_rejects_unknown_roles(isolated_option_state) -> None:
    spec = OptionSpec(
        FK_ARITH.ABS, "overflow", "ERROR", "int8", lambda: None, lambda: None, {}
    )
    REGISTERED_OPTION_PROBES.append(
        OptionProbeRegistration(spec, "polars", "probe_exempt")
    )
    with pytest.raises(AssertionError, match="invalid option probe disposition"):
        validate_option_registries()


def test_probe_registry_rejects_duplicate_cell_keys(isolated_option_state) -> None:
    spec = OptionSpec(
        FK_ARITH.ABS, "overflow", "ERROR", "int8", lambda: None, lambda: None, {}
    )
    probe = OptionProbeRegistration(spec, "polars", "honored")
    REGISTERED_OPTION_PROBES.extend([probe, probe])
    with pytest.raises(AssertionError, match="duplicate option probe"):
        validate_option_registries()


def test_declared_probe_requires_bounded_native_failure(isolated_option_state) -> None:
    spec = OptionSpec(
        FK_ARITH.ABS, "overflow", "ERROR", "int8", lambda: None, lambda: None, {}
    )
    REGISTERED_OPTION_PROBES.append(
        OptionProbeRegistration(spec, "polars", "declared_unsupported")
    )
    with pytest.raises(AssertionError, match="expected_native_failure"):
        validate_option_registries()


@pytest.mark.parametrize("broad_failure", [BaseException, Exception, AssertionError])
def test_declared_probe_rejects_broad_native_failure_types(
    isolated_option_state, broad_failure
) -> None:
    spec = OptionSpec(
        FK_ARITH.ABS, "overflow", "ERROR", "int8", lambda: None, lambda: None, {}
    )
    REGISTERED_OPTION_PROBES.append(
        OptionProbeRegistration(
            spec, "polars", "declared_unsupported", broad_failure
        )
    )
    with pytest.raises(AssertionError, match="specific native exception"):
        validate_option_registries()


@pytest.mark.parametrize("role", ["honored", "declared_unsupported"])
def test_probe_role_coverage_fails_when_registration_is_missing(
    isolated_option_state, role
) -> None:
    OPTION_DISPOSITIONS.append(
        OptionCell(
            FK_ARITH.ABS, "P", "abs", "overflow", "polars", "ERROR", "int8", role
        )
    )
    with pytest.raises(AssertionError, match=rf"{role} probe/cell mismatch"):
        validate_option_registries()


@pytest.mark.parametrize(
    ("dispositions", "expected"),
    [
        ((('invalid', ''),), "validation-only"),
        ((('declared_unsupported', ''),), "capability-declared"),
        ((('probe_exempt', ''),), "probe-exempt-honor"),
        ((('honored', ''),), "value-sensitive"),
        (
            (("declared_unsupported", ""), ("honored", "intended-error-path")),
            "error-sensitive",
        ),
    ],
)
def test_param_taxonomy_precedence(isolated_option_state, dispositions, expected) -> None:
    protocol, op, param = "P", "op", "choice"
    OPTION_DISPOSITIONS.extend(
        OptionCell(
            FK_ARITH.ABS,
            protocol,
            op,
            param,
            "polars",
            str(index),
            "int8",
            disposition_name,
            disposition_reason,
        )
        for index, (disposition_name, disposition_reason) in enumerate(dispositions)
    )

    assert disposition.param_taxonomy(protocol, op, param) == expected
