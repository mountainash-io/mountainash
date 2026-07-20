"""CapabilityRegistry — registration validation, resolution order, queries."""
import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Fidelity,
    TargetKind,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


@pytest.fixture(autouse=True)
def _isolated_registry():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    yield
    CapabilityRegistry.restore(snapshot)


def _fact(**overrides):
    base = dict(
        operation_key=FK_STR.LPAD,
        param="characters",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.POLARS,
        message="literal fill character required",
        since="2026-07-05",
    )
    base.update(overrides)
    return CapabilityFact(**base)


class TestRegistrationValidation:
    def test_unknown_param_rejected(self):
        with pytest.raises(ValueError, match="no parameter 'nope'"):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.POLARS, [_fact(param="nope")]
            )

    def test_wildcard_param_accepted(self):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [_fact(param=WILDCARD_PARAM, level=CapabilityLevel.UNSUPPORTED)],
        )

    def test_unknown_dialect_rejected(self):
        with pytest.raises(ValueError, match="dialect"):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.POLARS, [_fact(dialect="polars-quantum")]
            )

    def test_backend_mismatch_rejected(self):
        with pytest.raises(ValueError, match="backend"):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.IBIS, [_fact(backend=CONST_BACKEND.POLARS)]
            )

    def test_unknown_operation_key_rejected(self):
        class FakeKey:  # not in any registry
            name = "BOGUS"
        with pytest.raises(ValueError, match="operation_key"):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.POLARS, [_fact(operation_key=FakeKey())]
            )

    def test_duplicate_key_rejected(self):
        CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [_fact()])
        with pytest.raises(ValueError, match="duplicate"):
            CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [_fact()])

    def test_literal_only_on_option_param_rejected(self):
        # contains' case_sensitivity is annotated Optional[str], not
        # ExpressionT (prtcl_expsys_scalar_string.py:157) — LITERAL_ONLY on
        # an option-typed param is meaningless and must be rejected.
        with pytest.raises(ValueError, match="option-typed param"):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.POLARS,
                [_fact(operation_key=FK_STR.CONTAINS, param="case_sensitivity")],
            )

    def test_literal_only_on_expression_typed_param_accepted(self):
        # SUBSTRING's start is annotated ExpressionT even though the
        # function def lists it under options — the annotation is the
        # classifier, so this must register (Task 8 declares exactly this).
        CapabilityRegistry.register_backend(
            CONST_BACKEND.NARWHALS,
            [_fact(backend=CONST_BACKEND.NARWHALS,
                   operation_key=FK_STR.SUBSTRING, param="start")],
        )

    def test_str_backend_rejected_on_register_backend(self):
        # CapabilityFact.backend is CONST_BACKEND | str, but str families are
        # legal only via register_target (spec 2026-07-06). On the EXECUTE
        # path the family-identity check rejects them — "polars" == the
        # StrEnum member but is not it.
        with pytest.raises(ValueError, match="backend"):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.POLARS, [_fact(backend="polars")]
            )

    def test_fidelity_on_execute_fact_rejected(self):
        # fidelity is reserved for SERIALIZE-target facts (spec 2026-07-06);
        # register_backend is the EXECUTE path and must reject it.
        with pytest.raises(ValueError, match="fidelity"):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.POLARS, [_fact(fidelity=Fidelity.NATIVE)]
            )

    def test_serialize_family_namespace_disjoint(self):
        # A SERIALIZE identity may never collide with CONST_BACKEND, and a
        # family may not change kind (spec 2026-07-06). register_target()
        # arrives with the serialization workstream; the identity helper is
        # the forward-compat surface it will call.
        with pytest.raises(ValueError, match="collides"):
            CapabilityRegistry._register_identity("polars", TargetKind.SERIALIZE)
        try:
            CapabilityRegistry._register_identity("substrait", TargetKind.SERIALIZE)
            with pytest.raises(ValueError, match="already registered"):
                CapabilityRegistry._register_identity("substrait", TargetKind.EXECUTE)
        finally:
            CapabilityRegistry._kinds.pop("substrait", None)

    def test_ungateable_relation_param_rejected(self):
        # JOIN_ASOF is handler-routed; a param outside gate_params can never
        # gate. (Passes trivially before Task 10 adds gate_params — 'nonsense'
        # is also not a protocol param, so either error is acceptable; assert
        # ValueError only.)
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_MOUNTAINASH_REL,
        )
        with pytest.raises(ValueError):
            CapabilityRegistry.register_backend(
                CONST_BACKEND.NARWHALS,
                [_fact(backend=CONST_BACKEND.NARWHALS,
                       operation_key=RKEY_MOUNTAINASH_REL.JOIN_ASOF,
                       param="strategy", level=CapabilityLevel.UNSUPPORTED)],
            )


class TestResolutionOrder:
    def test_dialect_exact_beats_family(self):
        family = _fact(backend=CONST_BACKEND.NARWHALS,
                       operation_key=FK_STR.CONTAINS, param="substring")
        refinement = _fact(
            backend=CONST_BACKEND.NARWHALS, operation_key=FK_STR.CONTAINS,
            param="substring", dialect="narwhals-polars",
            level=CapabilityLevel.EXPR_CAPABLE,
            message="fixed upstream at narwhals 2.19.0",
        )
        CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, [family, refinement])
        got = CapabilityRegistry.capability_for(
            FK_STR.CONTAINS, "substring", CONST_BACKEND.NARWHALS, "narwhals-polars"
        )
        assert got.level is CapabilityLevel.EXPR_CAPABLE
        got_pd = CapabilityRegistry.capability_for(
            FK_STR.CONTAINS, "substring", CONST_BACKEND.NARWHALS, "narwhals-pandas"
        )
        assert got_pd.level is CapabilityLevel.LITERAL_ONLY

    def test_param_beats_wildcard(self):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [_fact(),
             _fact(param=WILDCARD_PARAM, level=CapabilityLevel.UNSUPPORTED)],
        )
        got = CapabilityRegistry.capability_for(
            FK_STR.LPAD, "characters", CONST_BACKEND.POLARS, "polars"
        )
        assert got.level is CapabilityLevel.LITERAL_ONLY

    def test_no_fact_returns_none(self):
        assert CapabilityRegistry.capability_for(
            FK_STR.LOWER, "input", CONST_BACKEND.POLARS, "polars"
        ) is None


class TestQueries:
    def test_facts_filters_and_residue(self):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [_fact(),
             _fact(param="length", boundary=Boundary.MATERIALIZE,
                   native_errors=(TypeError,))],
        )
        assert len(CapabilityRegistry.facts(backend=CONST_BACKEND.POLARS)) == 2
        assert len(CapabilityRegistry.facts(boundary=Boundary.MATERIALIZE)) == 1
        residue = CapabilityRegistry.residue_for(CONST_BACKEND.POLARS, "polars")
        assert (FK_STR.LPAD, "length") in residue

    def test_validate_plan_capabilities(self):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [_fact(param=WILDCARD_PARAM, level=CapabilityLevel.UNSUPPORTED)],
        )
        violations = CapabilityRegistry.validate_plan_capabilities(
            [FK_STR.LPAD, FK_STR.LOWER], CONST_BACKEND.POLARS, "polars"
        )
        assert len(violations) == 1
        assert violations[0].operation_key is FK_STR.LPAD

    def test_snapshot_restore_round_trips_kinds(self):
        # snapshot/restore must cover _kinds too (symmetric with reset), else a
        # test that registers a SERIALIZE identity leaks into the next module.
        snap = CapabilityRegistry.snapshot()
        CapabilityRegistry._register_identity("substrait", TargetKind.SERIALIZE)
        assert CapabilityRegistry._kinds.get("substrait") is TargetKind.SERIALIZE
        CapabilityRegistry.restore(snap)
        assert "substrait" not in CapabilityRegistry._kinds
