"""Static integrity guards for the capability spine (spec Section 2, guards 1-4).

Guard 1 (declaration resolves to a real protocol param) and guard 4
(MATERIALIZE facts declare native_errors) are registration-time — these
tests exist to fail loudly if registration is bypassed or empty.
Guard 2 (probe-or-exempt) lives with the probes
(tests/expressions/argument_types/test_capability_probes.py).
Guard 3 (upstream_ref -> YAML) lands in Phase 2.
Guard 5 (gap staleness) lands in Phase 3.
"""
import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityLevel,
    CapabilityRegistry,
    load_all_capability_declarations,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_MA_TERN,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)

load_all_capability_declarations()


_GATING_LEVELS = (
    CapabilityLevel.LITERAL_ONLY,
    CapabilityLevel.UNSUPPORTED,
    CapabilityLevel.POLYMORPHIC,
)

# Per-op existence anchors: a representative gating fact each backend's
# migration MUST have registered. Named (op, param) pairs test the real
# migration contract — NOT a fact count, which is brittle and encodes a
# production-feature tally (testing-philosophy: no count-based validation).
_REPRESENTATIVE_FACTS = [
    (CONST_BACKEND.POLARS, FK_STR.LIKE, "match"),
    (CONST_BACKEND.POLARS, FK_STR.REPLACE, "substring"),
    (CONST_BACKEND.IBIS, FK_STR.TRIM, "characters"),
    (CONST_BACKEND.IBIS, FK_DT.ADD_DAYS, "days"),
    (CONST_BACKEND.NARWHALS, FK_MA_TERN.T_IS_IN, "collection"),
    (CONST_BACKEND.NARWHALS, FK_DT.ADD_DAYS, "days"),
]


@pytest.mark.parametrize(
    "family,op,param",
    _REPRESENTATIVE_FACTS,
    ids=[f"{b.value}-{op.name}-{p}" for b, op, p in _REPRESENTATIVE_FACTS],
)
def test_representative_migration_facts_registered(family, op, param):
    """Each backend migration registered its known gating facts (existence,
    not count — a lost migration surfaces as a specific missing fact)."""
    fact = CapabilityRegistry.capability_for(op, param, family)
    assert fact is not None, (
        f"{family.value}: no capability fact for {op.name}/{param} — "
        "did that backend's migration stop registering?"
    )
    assert fact.level in _GATING_LEVELS, (
        f"{family.value}: {op.name}/{param} registered as {fact.level.name}, "
        "expected a gating level"
    )


@pytest.mark.parametrize(
    "family",
    [CONST_BACKEND.POLARS, CONST_BACKEND.IBIS, CONST_BACKEND.NARWHALS],
    ids=lambda f: f.value,
)
def test_backend_registered_some_facts(family):
    """Non-empty: each migrated family registered facts (structure, not a
    count — asserts migration actually ran, without a magic number)."""
    assert CapabilityRegistry.facts(backend=family), (
        f"{family.value}: zero registered capability facts"
    )


def _all_subclasses(cls) -> set[type]:
    """Recursive — direct __subclasses__() misses composed/intermediate
    backend classes (the concrete systems are multi-inheritance compositions
    several levels below the base)."""
    out: set[type] = set()
    for sub in cls.__subclasses__():
        out.add(sub)
        out |= _all_subclasses(sub)
    return out


def test_no_legacy_registries_remain():
    """The per-backend dicts are gone — the spine is the only source."""
    from mountainash.expressions.backends.expression_systems.base import (
        BaseExpressionSystem,
    )
    from mountainash.relations.backends.relation_systems.base import (
        BaseRelationSystem,
    )

    for cls in (
        BaseExpressionSystem,
        BaseRelationSystem,
        *_all_subclasses(BaseExpressionSystem),
        *_all_subclasses(BaseRelationSystem),
    ):
        assert not getattr(cls, "KNOWN_EXPR_LIMITATIONS", None), cls
        assert not getattr(cls, "KNOWN_REL_LIMITATIONS", None), cls


def test_no_extractor_heuristics_remain():
    from mountainash.expressions.backends.expression_systems.polars.base import (
        PolarsBaseExpressionSystem,
    )
    from mountainash.expressions.backends.expression_systems.narwhals.base import (
        NarwhalsBaseExpressionSystem,
    )

    for cls in (PolarsBaseExpressionSystem, NarwhalsBaseExpressionSystem):
        assert "_extract_literal_if_possible" not in cls.__dict__, (
            f"{cls.__name__} still overrides _extract_literal_if_possible"
        )
    # Ibis keeps its override: replace() extraction-without-narrowing
    # (permanent exception, spec Disposition table / param-width A3).


def test_materialize_facts_declare_native_errors():
    for fact in CapabilityRegistry.facts(boundary=Boundary.MATERIALIZE):
        assert fact.native_errors, fact


def test_conditioned_facts_are_enumerable():
    """Spec Section 1: the conditioned residue is a registry query."""
    conditioned = CapabilityRegistry.facts(conditioned=True)
    keys = {(f.operation_key.name, f.param) for f in conditioned}
    assert ("JOIN_ASOF", "tolerance") in keys
