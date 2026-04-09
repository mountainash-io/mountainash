"""Positively assert that BackendCapabilityError carries registry metadata."""
from __future__ import annotations

import pytest

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem

REGISTRIES = {
    "polars": PolarsBaseExpressionSystem.KNOWN_EXPR_LIMITATIONS,
    "ibis": IbisBaseExpressionSystem.KNOWN_EXPR_LIMITATIONS,
    "narwhals": NarwhalsBaseExpressionSystem.KNOWN_EXPR_LIMITATIONS,
}


@pytest.mark.parametrize("backend,registry", [(k, v) for k, v in REGISTRIES.items()])
def test_registry_entries_have_required_fields(backend: str, registry):
    for (fkey, pname), limitation in registry.items():
        assert limitation.message, f"{backend}:{fkey}:{pname} missing message"
        assert limitation.native_errors, f"{backend}:{fkey}:{pname} missing native_errors"
        assert isinstance(limitation.native_errors, tuple)
        for e in limitation.native_errors:
            assert isinstance(e, type) and issubclass(e, Exception)


def test_backend_capability_error_preserves_limitation_message():
    """When triggered, BackendCapabilityError carries the registry's message and workaround.

    Directly invokes _call_with_expr_support on the narwhals backend to simulate
    the native-side failure that a known limitation would produce. This avoids
    depending on whether the underlying library raises synchronously at build
    time vs lazily at execution time.
    """
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING,
    )

    sys = NarwhalsBaseExpressionSystem()
    fkey = FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH
    limitation = sys.KNOWN_EXPR_LIMITATIONS[(fkey, "substring")]
    exc_cls = limitation.native_errors[0]

    def simulated_native_failure():
        raise exc_cls("simulated native backend failure")

    with pytest.raises(BackendCapabilityError) as exc_info:
        sys._call_with_expr_support(
            simulated_native_failure,
            function_key=fkey,
            substring="not_a_literal",
        )
    err = exc_info.value
    assert err.limitation is not None
    assert err.limitation.message in str(err)
    if err.limitation.workaround:
        assert err.limitation.workaround in str(err)
