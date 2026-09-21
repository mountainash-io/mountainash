"""Cold catalogue views retain explicit information and policies separately."""
from __future__ import annotations
from dataclasses import replace

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import InformationLayer, PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))


@pytest.fixture
def isolated():
    from mountainash.core.capabilities.registry import _empty_state, _LoadState

    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.restore(_empty_state(_LoadState.LOADED))
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def _information(message):
    return CapabilityInformation(
        CapabilityKey(FK_STR.CENTER, "length"), InformationLayer.PUBLIC,
        CapabilityLevel.UNSUPPORTED, "2026-09-18", message,
    )


def _policy(message="literal length required"):
    return CapabilityPolicyRule(
        CapabilityKey(FK_STR.CENTER, "length"), CapabilityLevel.LITERAL_ONLY,
        "2026-09-18", message, PolicyConsumer.GATE, PolicyAction.BLOCK,
    )


def _segment(*, information=(), policies=(), suffix=""):
    return BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string" + suffix,
        _SCOPE,
        CapabilitySegment(Domain.STRING, information=information, policies=policies),
    )


def test_reader_is_exact_scope_and_retains_its_generation(isolated):
    from mountainash.core.capabilities.catalogue import InformationQuery

    first = _segment(information=(_information("initial description"),), policies=(_policy(),))
    CapabilityRegistry.register_segment(first)
    old = CapabilityRegistry.capture()

    assert old.reader(_SCOPE).policy(_policy().key).assertion.message == "literal length required"
    later = replace(_information("later native note"), layer=InformationLayer.NATIVE)
    CapabilityRegistry.register_segment(_segment(information=(later,), suffix=".later"))

    assert tuple(record.assertion.message for record in old.reader(_SCOPE).search(
        InformationQuery()
    )) == ("initial description",)
    assert {record.assertion.message for record in CapabilityRegistry.capture().reader(_SCOPE).search(
        InformationQuery()
    )} == {"initial description", "later native note"}


def test_catalogue_queries_leave_unrequested_namespaces_absent(isolated):
    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery, PolicyQuery

    CapabilityRegistry.register_segment(_segment(information=(_information("description"),), policies=(_policy(),)))
    capture = CapabilityRegistry.capture()

    information_only = capture.search(CatalogueQuery(information=InformationQuery()))
    assert tuple(record.assertion.message for record in information_only.information) == ("description",)
    assert information_only.policies is None
    both = capture.search(CatalogueQuery(information=InformationQuery(), policies=PolicyQuery()))
    assert both.policies == (capture.reader(_SCOPE).policy(_policy().key),)


def test_issue_snapshot_is_retained_and_missing_metadata_stays_distinct(isolated):
    from mountainash.core.capabilities.capture import CapturedAddress
    from mountainash.core.capabilities.catalogue import IssueSnapshot, UncapturedNamespaceError
    from mountainash.core.capabilities.schema import CaptureValue

    source = CapturedAddress("mountainash", "registry/upstream-issues.yaml", "issues", artifact=b"issues: []")
    snapshot = IssueSnapshot(source, (("IB-STR-01", CaptureValue.of({"id": "IB-STR-01", "status": "open"})),))
    captured = CapabilityRegistry.capture(issues=snapshot)
    assert dict(captured.issue("IB-STR-01").value)["status"] == CaptureValue("text", "open")
    with pytest.raises(UncapturedNamespaceError):
        CapabilityRegistry.capture().issue("IB-STR-01")


def test_version_conditioned_residue_requires_observed_context(isolated):
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer

    version_conditioned_residue = CapabilityPolicyRule(
        CapabilityKey(FK_STR.CENTER, "length", variant="ibis-10"),
        CapabilityLevel.UNSUPPORTED,
        "2026-09-18",
        "Version-conditioned residue policy requires an observed execution context",
        PolicyConsumer.MATERIALIZATION_ERROR,
        PolicyAction.ENRICH,
        native_errors=(RuntimeError,),
        native_issue="IB-STR-01",
        applicability=Applicability((
            Region((
                CoordinateConstraint(
                    "package",
                    "ibis-framework",
                    ComparisonScheme.PEP440,
                    lower="10.0.0",
                ),
            )),
        )),
    )
    CapabilityRegistry.register_segment(_segment(policies=(version_conditioned_residue,)))

    assert CapabilityRegistry.residue_candidates(CONST_BACKEND.IBIS, "ibis-duckdb") == ()
    assert CapabilityRegistry.residue_for(CONST_BACKEND.IBIS, "ibis-duckdb") == {}
