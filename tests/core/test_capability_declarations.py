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
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
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


def test_probe_evidence_validates_date():
    with pytest.raises(ValueError, match="probe_date"):
        ProbeEvidence(probe_date="not-a-date", library_versions=(), fixtures=())
