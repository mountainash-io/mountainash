"""Protocol contract for capability declaration modules (spec rev 3, §1)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities import CapabilityRegistry
from mountainash.core.capabilities.predicates import BoundCall
from mountainash.core.capabilities.schema import ClauseOp, Enforcement
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


def _fact(op, backend, **kw):
    return CapabilityFact(
        operation_key=op, param="*", level=CapabilityLevel.UNSUPPORTED,
        backend=backend, message="t", since="2026-08-07",
        probe_exempt="test fact", **kw,
    )


def test_classify_source():
    assert classify_source(FK_STR.CENTER) is FactSource.SUBSTRAIT
    assert classify_source(FK_DT.ADD_DAYS) is FactSource.MOUNTAINASH
    assert classify_source(RKEY_MOUNTAINASH_REL.UNNEST) is FactSource.MOUNTAINASH


def test_classify_domain():
    assert classify_domain(FK_STR.CENTER) is Domain.STRING
    assert classify_domain(FK_DT.ADD_DAYS) is Domain.DATETIME
    assert classify_domain(RKEY_MOUNTAINASH_REL.UNNEST) is Domain.RELATION


def test_declaration_accepts_homogeneous_facts():
    d = CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=(_fact(FK_STR.CENTER, CONST_BACKEND.IBIS),),
    )
    assert d.evidence is None  # legal: the fact is probe_exempt


def test_declaration_rejects_backend_mismatch():
    with pytest.raises(ValueError, match="backend"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.POLARS, domain=Domain.STRING,
            source=FactSource.SUBSTRAIT,
            facts=(_fact(FK_STR.CENTER, CONST_BACKEND.IBIS),),
        )


def test_declaration_rejects_source_mismatch():
    with pytest.raises(ValueError, match="source"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.IBIS, domain=Domain.DATETIME,
            source=FactSource.SUBSTRAIT,  # FK_DT is MOUNTAINASH
            facts=(_fact(FK_DT.ADD_DAYS, CONST_BACKEND.IBIS),),
        )


def test_declaration_rejects_domain_mismatch():
    with pytest.raises(ValueError, match="domain"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.IBIS, domain=Domain.STRING,  # FK_DT is DATETIME
            source=FactSource.MOUNTAINASH,
            facts=(_fact(FK_DT.ADD_DAYS, CONST_BACKEND.IBIS),),
        )


def test_declaration_requires_evidence_for_probed_facts():
    probed = CapabilityFact(
        operation_key=FK_STR.CENTER, param="*",
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.IBIS,
        message="t", since="2026-08-07",  # no probe_exempt
    )
    with pytest.raises(ValueError, match="evidence"):
        CapabilityDeclaration(
            backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
            source=FactSource.SUBSTRAIT, facts=(probed,),
        )
    # and with evidence it is accepted
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=(probed,),
        evidence=ProbeEvidence(
            probe_date="2026-08-07",
            library_versions=(("ibis", "12.0.0"),),
            fixtures=("ibis-duckdb",),
        ),
    )


def test_every_unit_c_matrix_cell_has_one_winning_fact() -> None:
    """Every declared Unit C gate/residue cell resolves through its consumer."""
    unit_c_keys = (
        set(FK_CAT)
        | set(FK_DT)
        | set(FK_GEO)
        | set(FK_LIST)
        | set(FK_STRUCT)
        | {
            FK_DT.PARSE_DEFAULT,
            FK_DT.PARSE_XSD_DURATION,
            FK_DT.PARSE_XSD_PARTIAL_DATE,
            FK_DT.PARSE_TEMPORAL_ANY,
        }
    )
    cells = [
        fact
        for fact in CapabilityRegistry.facts()
        if fact.operation_key in unit_c_keys
        and fact.level is CapabilityLevel.UNSUPPORTED
        and fact.enforcement in {
            Enforcement.GATE,
            Enforcement.MATERIALIZE_RESIDUE,
        }
    ]
    for fact in cells:
        if fact.enforcement is Enforcement.MATERIALIZE_RESIDUE:
            winner = CapabilityRegistry.residue_for(
                fact.backend, fact.dialect
            ).get((fact.operation_key, fact.param))
            assert winner is fact, fact.fact_key
            continue
        if fact.predicate is not None:
            bindings = {}
            predicate_facts = (
                fact,
                *CapabilityRegistry.facts(backend=fact.backend),
            )
            for candidate in predicate_facts:
                if (
                    candidate.operation_key != fact.operation_key
                    or candidate.predicate is None
                    or (
                        candidate.dialect is not None
                        and candidate.dialect != fact.dialect
                    )
                ):
                    continue
                for clause in candidate.predicate.clauses:
                    if clause.path in bindings:
                        continue
                    if clause.op is ClauseOp.EQ:
                        bindings[clause.path] = clause.operand
                    elif clause.op is ClauseOp.IN:
                        bindings[clause.path] = sorted(clause.operand, key=str)[0]
                    elif clause.op is ClauseOp.IS_SET:
                        bindings[clause.path] = "set"
                    elif clause.op is ClauseOp.IS_NULL:
                        bindings[clause.path] = None
                    else:
                        raise AssertionError(f"unhandled Unit C selector: {clause.op}")
            winners = CapabilityRegistry.violations_for(
                BoundCall(
                    fact.operation_key,
                    fact.backend,
                    fact.dialect,
                    bindings,
                    frozenset(bindings),
                )
            )
            winners = {
                winner
                for winner in winners
                if winner.dialect == fact.dialect
            }
            assert winners == {fact}, fact.fact_key
            continue
        if fact.value_class is not None:
            samples = {
                "duration_multiplier": "2d",
                "iana_timezone": "UTC",
                "polars_offset": "2d",
            }
            option_value = samples[fact.value_class.value]
        else:
            option_value = fact.option_value
        winner = CapabilityRegistry.capability_for(
            fact.operation_key,
            fact.param,
            fact.backend,
            dialect=fact.dialect,
            option_value=option_value,
        )
        assert winner is fact, fact.fact_key


def test_probe_evidence_validates_date():
    with pytest.raises(ValueError, match="probe_date"):
        ProbeEvidence(probe_date="not-a-date", library_versions=(), fixtures=())
