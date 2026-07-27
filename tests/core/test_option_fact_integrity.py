"""Closed-by-default integrity for literal option disposition cells.

The populated matrix, executable probes, concrete facts, and family defaults
must remain bidirectionally exact. Synthetic self-checks exercise drift paths
without coupling to production keys.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from expressions.argument_types import option_disposition as disposition
from expressions.argument_types._option_helpers import OptionSpec
from expressions.argument_types.option_disposition import (
    OPTION_FAMILY_DEFAULT_FACT_KEYS,
    INVALID_OPTION_VALUE,
    OPTION_DISPOSITIONS,
    OPTION_DTYPES,
    REGISTERED_INVALID_OPTION_REJECTIONS,
    REGISTERED_OPTION_PROBES,
    InvalidOptionRejection,
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


def test_modulus_domain_probe_uses_pinned_integer_overload() -> None:
    assert OPTION_DTYPES[("modulus", "on_domain_error")] == ("int64",)


@pytest.fixture
def isolated_option_state():
    fact_snapshot = CapabilityRegistry.snapshot()
    cells = list(OPTION_DISPOSITIONS)
    probes = list(REGISTERED_OPTION_PROBES)
    invalid_rejections = list(REGISTERED_INVALID_OPTION_REJECTIONS)
    family_defaults = set(OPTION_FAMILY_DEFAULT_FACT_KEYS)
    try:
        CapabilityRegistry.reset()
        OPTION_DISPOSITIONS.clear()
        REGISTERED_OPTION_PROBES.clear()
        REGISTERED_INVALID_OPTION_REJECTIONS.clear()
        OPTION_FAMILY_DEFAULT_FACT_KEYS.clear()
        yield
    finally:
        CapabilityRegistry.restore(fact_snapshot)
        OPTION_DISPOSITIONS[:] = cells
        REGISTERED_OPTION_PROBES[:] = probes
        REGISTERED_INVALID_OPTION_REJECTIONS[:] = invalid_rejections
        OPTION_FAMILY_DEFAULT_FACT_KEYS.clear()
        OPTION_FAMILY_DEFAULT_FACT_KEYS.update(family_defaults)


def _option_fact_keys() -> set[tuple[object, str, str, CONST_BACKEND, str | None]]:
    return {
        fact_key(fact)
        for fact in CapabilityRegistry.facts()
        if fact.option_value is not None
        and fact.level in _GATING
        and fact.dialect is not None
    }


def test_dispositions_cover_exactly_the_expected_cells() -> None:
    disposition.validate_option_matrix_coverage()


def test_declared_cells_and_option_facts_are_mutually_backed() -> None:
    # 1. Exact Arm: exact-backed declared cells <-> exact value-scoped facts
    fact_keys = _option_fact_keys()
    exact_declared_keys = {
        cell_fact_key(cell)
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "declared_unsupported" and cell.backing_mode != "class"
    }
    assert fact_keys == exact_declared_keys, (
        f"exact fact/cell mismatch: facts-only={fact_keys - exact_declared_keys}; "
        f"cells-only={exact_declared_keys - fact_keys}"
    )

    # 2. Class Arm: class-backed declared cells <-> value-class capability facts
    class_declared_cells = [
        cell
        for cell in OPTION_DISPOSITIONS
        if cell.disposition == "declared_unsupported" and cell.backing_mode == "class"
    ]
    for cell in class_declared_cells:
        fact = disposition.resolve_cell_class_fact(cell)
        assert fact is not None, f"class-backed declared cell {cell} failed to resolve to a class fact"
        assert fact.value_class is not None, f"resolved fact for class cell {cell} has no value_class: {fact}"
        assert fact.level in _GATING, f"resolved class fact for cell {cell} has level {fact.level!r}, not in _GATING"

    registered_class_facts = {
        fact
        for fact in CapabilityRegistry.facts()
        if fact.value_class is not None
        and fact.level in _GATING
        and fact.dialect is not None
    }
    resolved_class_facts = {
        disposition.resolve_cell_class_fact(cell)
        for cell in class_declared_cells
        if disposition.resolve_cell_class_fact(cell) is not None
    }
    unexercised_class_facts = registered_class_facts - resolved_class_facts
    assert not unexercised_class_facts, (
        f"registered class fact(s) not exercised by any class-backed declared cell: {unexercised_class_facts}"
    )




def test_family_default_option_facts_are_mutually_backed() -> None:
    family_defaults = {
        fact_key(fact)
        for fact in CapabilityRegistry.facts()
        if fact.option_value is not None
        and fact.level in _GATING
        and fact.dialect is None
    }
    assert family_defaults == OPTION_FAMILY_DEFAULT_FACT_KEYS


def test_duckdb_refinement_precedes_ibis_family_default() -> None:
    fact = CapabilityRegistry.capability_for(
        FK_ARITH.ABS,
        "overflow",
        CONST_BACKEND.IBIS,
        "ibis-duckdb",
        option_value="ERROR",
    )

    assert fact is not None
    assert fact.level is CapabilityLevel.EXPR_CAPABLE
    assert fact.dialect == "ibis-duckdb"
    assert fact.probe_exempt
    for dialect in (None, "ibis-sqlite"):
        family_default = CapabilityRegistry.capability_for(
            FK_ARITH.ABS,
            "overflow",
            CONST_BACKEND.IBIS,
            dialect,
            option_value="ERROR",
        )
        assert family_default is not None
        assert family_default.level is CapabilityLevel.UNSUPPORTED
        assert family_default.dialect is None


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
        (FK_ARITH.MODULO, "division_type", "narwhals-polars", "INVALID", "int64"),
        (FK_ARITH.MODULO, "division_type", "narwhals-pandas", "FLOOR", "int64"),
        (FK_ARITH.MODULO, "division_type", "narwhals-pandas", "INVALID", "int64"),
    }


@pytest.mark.parametrize("mode", ["missing", "extra"])
def test_option_matrix_coverage_rejects_invalid_cell_drift(
    isolated_option_state, monkeypatch, mode
) -> None:
    cell = OptionCell(
        FK_ARITH.ABS,
        "SubstraitScalarArithmeticExpressionSystemProtocol",
        "abs",
        "overflow",
        "polars",
        "INVALID",
        "int8",
        "invalid",
        "canonical build-time rejection sentinel",
    )
    key = cell_key(cell)
    if mode == "missing":
        monkeypatch.setattr(disposition, "expected_option_cells", lambda: {key})
    else:
        monkeypatch.setattr(disposition, "expected_option_cells", set)
        OPTION_DISPOSITIONS.append(cell)

    with pytest.raises(AssertionError, match="option cell coverage mismatch"):
        disposition.validate_option_matrix_coverage()


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


def test_representative_dtype_policy_exactly_covers_option_domain_owners() -> None:
    # Every option param draws its legal value domain from exactly one owner:
    # the pinned enum domain OPTION_DOMAINS, the open-int representative domain
    # OPTION_VALUE_DOMAINS, or the MA-extension domain MA_OPTION_DOMAINS. All
    # three owners must carry a representative dtype declaration.
    owners = (
        set(disposition.OPTION_DOMAINS)
        | set(disposition.OPTION_VALUE_DOMAINS)
        | set(disposition.MA_OPTION_DOMAINS)
        | set(disposition._MA_OPTION_VALUE_DOMAINS)
    )
    expected = {
        key: (
            ("str",)
            if key[1]
            in {
                "case_sensitivity",
                "char_set",
                "multiline",
                "dotall",
                "padding",
                "negative_start",
                # Regexp positional int options operate on string data columns.
                "position",
                "occurrence",
                "group",
            }
            else ("int64",)
            if key == ("power", "overflow")
            else ("int8",)
            if key[1] == "overflow"
            else ("int64",)
            if key
            in {
                ("modulus", "division_type"),
                ("modulus", "on_domain_error"),
            }
            else ("datetime",)
            if key[1] in {"unit", "timezone", "offset", "format"}
            else ("float64",)
        )
        for key in owners
    }
    assert disposition.OPTION_DTYPES == expected
    assert set(disposition.OPTION_DTYPES) == owners



@pytest.mark.parametrize("value", ["ERROR", "SATURATE", "SILENT"])
def test_power_overflow_facts_give_i64_specific_guidance(value: str) -> None:
    fact = CapabilityRegistry.capability_for(
        FK_ARITH.POWER,
        "overflow",
        CONST_BACKEND.IBIS,
        None,
        option_value=value,
    )

    assert fact is not None
    assert "i64 power" in fact.message
    assert "wider" not in fact.workaround
    assert "base and exponent" in fact.workaround


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


def test_invalid_cells_require_rejection_coverage_but_no_backend_fact_or_probe(
    isolated_option_state,
) -> None:
    rejection = InvalidOptionRejection(
        FK_ARITH.ABS,
        "SubstraitScalarArithmeticExpressionSystemProtocol",
        "abs",
        "overflow",
        INVALID_OPTION_VALUE,
        "int8",
        lambda: None,
    )
    REGISTERED_INVALID_OPTION_REJECTIONS.append(rejection)
    OPTION_DISPOSITIONS.extend(
        OptionCell(
            rejection.fkey,
            rejection.protocol,
            rejection.op,
            rejection.param,
            fixture,
            rejection.value,
            rejection.dtype,
            "invalid",
        )
        for fixture in ("polars", "ibis", "narwhals-polars", "narwhals-pandas")
    )

    validate_option_registries()
    assert CapabilityRegistry.facts() == []
    assert REGISTERED_OPTION_PROBES == []


@pytest.mark.parametrize("mode", ["missing", "extra"])
def test_invalid_rejection_registry_rejects_owner_drift(
    isolated_option_state, mode
) -> None:
    rejection = InvalidOptionRejection(
        FK_ARITH.ABS,
        "SubstraitScalarArithmeticExpressionSystemProtocol",
        "abs",
        "overflow",
        INVALID_OPTION_VALUE,
        "int8",
        lambda: None,
    )
    if mode == "missing":
        OPTION_DISPOSITIONS.append(
            OptionCell(
                rejection.fkey,
                rejection.protocol,
                rejection.op,
                rejection.param,
                "polars",
                rejection.value,
                rejection.dtype,
                "invalid",
            )
        )
    else:
        REGISTERED_INVALID_OPTION_REJECTIONS.append(rejection)

    with pytest.raises(AssertionError, match="invalid rejection/cell mismatch"):
        validate_option_registries()


def test_probe_exempt_role_requires_exact_registration(isolated_option_state) -> None:
    spec = OptionSpec(
        FK_ARITH.ABS, "overflow", "ERROR", "int8", lambda: None, lambda: None, {}
    )
    OPTION_DISPOSITIONS.append(
        OptionCell(
            FK_ARITH.ABS,
            "P",
            "abs",
            "overflow",
            "polars",
            "ERROR",
            "int8",
            "probe_exempt",
        )
    )
    with pytest.raises(AssertionError, match="probe_exempt probe/cell mismatch"):
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


@pytest.mark.parametrize("broad_failure", [BaseException, Exception, AssertionError])
def test_probe_exempt_rejects_broad_intended_exception_types(
    isolated_option_state, broad_failure
) -> None:
    spec = OptionSpec(
        FK_ARITH.ABS,
        "overflow",
        "ERROR",
        "int8",
        lambda: None,
        lambda: None,
        {},
        expected_discriminates=False,
        expected_native_exception=broad_failure,
    )
    OPTION_DISPOSITIONS.append(
        OptionCell(
            FK_ARITH.ABS,
            "P",
            "abs",
            "overflow",
            "polars",
            "ERROR",
            "int8",
            "probe_exempt",
        )
    )
    REGISTERED_OPTION_PROBES.append(
        OptionProbeRegistration(spec, "polars", "probe_exempt")
    )

    with pytest.raises(AssertionError, match="specific intended exception"):
        validate_option_registries()


@pytest.mark.parametrize("role", ["honored", "declared_unsupported", "probe_exempt"])
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
        ((("invalid", ""),), "validation-only"),
        ((("declared_unsupported", ""),), "capability-declared"),
        ((("probe_exempt", ""), ("invalid", "")), "probe-exempt-honor"),
        (
            (
                ("probe_exempt", "intended-error-path"),
                ("probe_exempt", ""),
                ("invalid", ""),
            ),
            "probe-exempt-honor",
        ),
        (
            (
                ("probe_exempt", ""),
                ("declared_unsupported", ""),
                ("invalid", ""),
            ),
            "value-sensitive",
        ),
        ((("honored", ""), ("invalid", "")), "value-sensitive"),
        (
            (
                ("probe_exempt", "intended-error-path"),
                ("declared_unsupported", ""),
                ("invalid", ""),
            ),
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
