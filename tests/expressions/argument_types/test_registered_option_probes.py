"""Execute every disposition discriminator registered by option slices."""
from __future__ import annotations

import importlib

import pytest

from expressions.argument_types._option_helpers import (
    OptionProbeDidNotDiscriminateError,
    native_option_probe,
)
from expressions.argument_types.option_disposition import (
    REGISTERED_OPTION_PROBES,
    OptionProbeRegistration,
    probe_key,
    validate_option_probe_registration,
)

_CATEGORY_MODULES = (
    "test_arg_types_aggregate", "test_arg_types_arithmetic",
    "test_arg_types_boolean", "test_arg_types_comparison",
    "test_arg_types_datetime", "test_arg_types_list",
    "test_arg_types_logarithmic", "test_arg_types_misc",
    "test_arg_types_name", "test_arg_types_null", "test_arg_types_rounding",
    "test_arg_types_string", "test_arg_types_struct", "test_arg_types_window",
)


def _load_option_probe_registrations() -> None:
    """Deterministically trigger every category's registration side effects."""
    for module_name in _CATEGORY_MODULES:
        importlib.import_module(f"expressions.argument_types.{module_name}")


def _probe_params(
    registrations: list[OptionProbeRegistration] | None = None,
) -> list[object]:
    if registrations is None:
        registrations = REGISTERED_OPTION_PROBES
    params = []
    for registration in registrations:
        validate_option_probe_registration(registration)
        marks = []
        if registration.disposition == "declared_unsupported":
            marks.append(
                pytest.mark.xfail(
                    strict=True,
                    raises=registration.expected_native_failure,
                    reason=(
                        "raw native option path is expected to fail "
                        "(XPASS => native support was added; flip the disposition)"
                    ),
                )
            )
        params.append(
            pytest.param(
                registration,
                id="-".join(str(part) for part in probe_key(registration)),
                marks=marks,
            )
        )
    return params or [pytest.param(None, id="no-registered-option-probes")]


_load_option_probe_registrations()


@pytest.mark.parametrize("registration", _probe_params())
def test_registered_option_probe(registration: OptionProbeRegistration | None) -> None:
    if registration is None:
        assert REGISTERED_OPTION_PROBES == []
        return
    native_option_probe(registration.spec, registration.fixture)


def test_declared_probe_params_use_bounded_strict_native_xfail() -> None:
    from expressions.argument_types._option_helpers import OptionSpec
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    )

    registration = OptionProbeRegistration(
        OptionSpec(
            FK_ARITH.ABS,
            "overflow",
            "ERROR",
            "int8",
            lambda: None,
            lambda: None,
            {},
            expected_discriminates=False,
        ),
        "polars",
        "declared_unsupported",
        OptionProbeDidNotDiscriminateError,
    )
    [param] = _probe_params([registration])
    [marker] = param.marks
    assert marker.name == "xfail"
    assert marker.kwargs == {
        "strict": True,
        "raises": OptionProbeDidNotDiscriminateError,
        "reason": marker.kwargs["reason"],
    }


def test_probe_exempt_params_execute_without_xfail() -> None:
    from expressions.argument_types._option_helpers import OptionSpec
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    )

    registration = OptionProbeRegistration(
        OptionSpec(
            FK_ARITH.ABS,
            "overflow",
            "ERROR",
            "int8",
            lambda: None,
            lambda: None,
            {},
            expected_discriminates=False,
        ),
        "ibis",
        "probe_exempt",
    )

    [param] = _probe_params([registration])
    assert param.marks == []
