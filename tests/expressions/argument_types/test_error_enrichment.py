"""Positively assert that BackendCapabilityError carries capability-fact metadata.

Migrated to the capability spine (spec 2026-07-05): backend limitations now live
as CapabilityFacts in CapabilityRegistry, not per-backend KNOWN_EXPR_LIMITATIONS
dicts. Two fact boundaries matter here:

- BUILD facts (LITERAL_ONLY/UNSUPPORTED) gate at the visitor before the native
  call, so they carry no ``native_errors``.
- MATERIALIZE facts (conditioned, value/dtype-dependent) are enriched by
  ``_call_with_expr_support`` when the native op raises — these carry
  ``native_errors``.
"""
from __future__ import annotations

import pytest

# Importing the backend systems triggers their module-bottom register_backend()
# calls, so CapabilityRegistry is populated by collection time.
from mountainash.core.capabilities import Boundary, CapabilityRegistry
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import (  # noqa: F401
    IbisBaseExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.narwhals.base import (
    NarwhalsBaseExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.polars.base import (  # noqa: F401
    PolarsBaseExpressionSystem,
)

_ALL_FACTS = CapabilityRegistry.facts()


def _fact_id(fact) -> str:
    op = getattr(fact.operation_key, "name", fact.operation_key)
    backend = getattr(fact.backend, "value", fact.backend)
    dialect = f"@{fact.dialect}" if fact.dialect else ""
    return f"{backend}{dialect}:{op}:{fact.param}"


@pytest.mark.parametrize("fact", _ALL_FACTS, ids=[_fact_id(f) for f in _ALL_FACTS])
def test_capability_facts_have_required_fields(fact):
    """Every registered CapabilityFact is well-formed for its boundary.

    Parametrized over the live registry so it validates the migrated facts of
    every registered backend (never vacuous; auto-covers backends as they
    migrate). It does NOT assert a fact *count* — completeness of the migration
    is the job of the closed-by-default integrity guards (Task 11/12).
    """
    assert fact.message, f"{_fact_id(fact)} missing message"
    if fact.boundary is Boundary.MATERIALIZE:
        # Enriched at _call_with_expr_support — must declare the native errors it catches.
        assert fact.native_errors, f"{_fact_id(fact)} MATERIALIZE fact missing native_errors"
        assert isinstance(fact.native_errors, tuple)
        for e in fact.native_errors:
            assert isinstance(e, type) and issubclass(e, Exception)
    else:
        # BUILD facts gate at the visitor before the native call, so by design
        # they carry no native_errors (schema keeps them empty).
        assert fact.native_errors == ()


def test_backend_capability_error_preserves_limitation_message():
    """When triggered, BackendCapabilityError carries the fact's message and workaround.

    Exercises the enrichment path directly on ``_call_with_expr_support`` using a
    MATERIALIZE-boundary fact (Narwhals ``list.t_contains`` storage-residue fact on
    narwhals-pandas, which narwhals rejects with ``TypeError``). Sourcing the fact from the
    registry — rather than a class dict — is the whole point of the migration;
    BUILD-gated string ops like ``starts_with`` no longer reach this path.
    """
    from mountainash.core.capabilities import WILDCARD_PARAM
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    )

    sys = NarwhalsBaseExpressionSystem(dialect="narwhals-pandas")
    fkey = FK_LIST.T_CONTAINS
    fact = CapabilityRegistry.capability_for(
        fkey, WILDCARD_PARAM, CONST_BACKEND.NARWHALS, sys.dialect
    )
    assert fact is not None and fact.native_errors, (
        "expected a MATERIALIZE-enriched list.t_contains fact with native_errors"
    )
    exc_cls = fact.native_errors[0]

    def simulated_native_failure():
        raise exc_cls("simulated native backend failure")

    with pytest.raises(BackendCapabilityError) as exc_info:
        sys._call_with_expr_support(
            simulated_native_failure,
            function_key=fkey,
            item="not_a_literal",
        )
    err = exc_info.value
    assert err.limitation is not None
    assert err.limitation.message in str(err)
    if err.limitation.workaround:
        assert err.limitation.workaround in str(err)
