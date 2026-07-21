"""Value-scoped option facts: keyed by option_value, value-specific lookup
falls back to value-agnostic; registration rejects malformed value facts."""

import pytest

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    snap = CapabilityRegistry.snapshot()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snap)


def test_value_specific_fact_gates_only_its_value():
    # Remove the production key Task 7 may register. The autouse snapshot
    # restores it after this test; this branch does not yet contain that fact.
    CapabilityRegistry._facts.pop(  # noqa: SLF001
        (FK_ARITH.ABS, "overflow", CONST_BACKEND.NARWHALS, None, "ERROR"),
        None,
    )
    CapabilityRegistry.register_backend(
        CONST_BACKEND.NARWHALS,
        [
            CapabilityFact(
                operation_key=FK_ARITH.ABS,
                param="overflow",
                option_value="ERROR",
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.NARWHALS,
                message="no checked-overflow abs",
                since="2026-07-21",
                condition="options['overflow'] == 'ERROR'",
            ),
        ],
    )
    assert (
        CapabilityRegistry.capability_for(
            FK_ARITH.ABS,
            "overflow",
            CONST_BACKEND.NARWHALS,
            option_value="ERROR",
        ).level
        is CapabilityLevel.UNSUPPORTED
    )
    assert (
        CapabilityRegistry.capability_for(
            FK_ARITH.ABS,
            "overflow",
            CONST_BACKEND.NARWHALS,
            option_value="SATURATE",
        )
        is None
    )


def test_value_scoped_wildcard_fact_is_rejected():
    with pytest.raises(ValueError):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [
                CapabilityFact(
                    operation_key=FK_ARITH.ABS,
                    param=WILDCARD_PARAM,
                    option_value="ERROR",
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=CONST_BACKEND.POLARS,
                    since="2026-07-21",
                ),
            ],
        )
