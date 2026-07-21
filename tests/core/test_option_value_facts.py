"""Value-scoped option facts: keyed by option_value, value-specific lookup
falls back to value-agnostic; registration rejects malformed value facts."""

import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
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


def test_value_specific_lookup_falls_back_to_value_agnostic_fact():
    CapabilityRegistry._facts.pop(  # noqa: SLF001
        (FK_ARITH.ABS, "overflow", CONST_BACKEND.POLARS, None, None),
        None,
    )
    fallback = CapabilityFact(
        operation_key=FK_ARITH.ABS,
        param="overflow",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.POLARS,
        message="all overflow modes unsupported",
        since="2026-07-21",
    )
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fallback])

    assert (
        CapabilityRegistry.capability_for(
            FK_ARITH.ABS,
            "overflow",
            CONST_BACKEND.POLARS,
            option_value="ERROR",
        )
        is fallback
    )


def test_value_specific_fact_takes_precedence_over_value_agnostic_fact():
    for option_value in (None, "ERROR"):
        CapabilityRegistry._facts.pop(  # noqa: SLF001
            (FK_ARITH.ABS, "overflow", CONST_BACKEND.POLARS, None, option_value),
            None,
        )
    fallback = CapabilityFact(
        operation_key=FK_ARITH.ABS,
        param="overflow",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.POLARS,
        message="all overflow modes unsupported",
        since="2026-07-21",
    )
    specific = CapabilityFact(
        operation_key=FK_ARITH.ABS,
        param="overflow",
        option_value="ERROR",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.POLARS,
        message="error mode has a specific limitation",
        since="2026-07-21",
    )
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fallback, specific])

    assert (
        CapabilityRegistry.capability_for(
            FK_ARITH.ABS,
            "overflow",
            CONST_BACKEND.POLARS,
            option_value="ERROR",
        )
        is specific
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


def test_value_scoped_non_build_fact_is_rejected():
    with pytest.raises(ValueError, match="must use the BUILD boundary"):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [
                CapabilityFact(
                    operation_key=FK_ARITH.ABS,
                    param="overflow",
                    option_value="ERROR",
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=CONST_BACKEND.POLARS,
                    boundary=Boundary.MATERIALIZE,
                    native_errors=(RuntimeError,),
                    since="2026-07-21",
                ),
            ],
        )


def test_value_scoped_relation_fact_is_rejected():
    with pytest.raises(ValueError, match="require an expression operation"):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [
                CapabilityFact(
                    operation_key=RKEY_SUBSTRAIT_REL.FETCH,
                    param="count",
                    option_value="10",
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=CONST_BACKEND.POLARS,
                    since="2026-07-21",
                ),
            ],
        )
