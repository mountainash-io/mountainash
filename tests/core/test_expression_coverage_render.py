"""Pure renderer tests for separated capability information and policies."""

from __future__ import annotations

import json

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    ImplementationRecord,
    ImplState,
    OpRecord,
    build_coverage_report,
)
from mountainash.core.capabilities.capture import CapturedAddress, CapturedAssertion, SourceOrigin
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    Domain,
    FactSource,
    QualifiedCapabilityKey,
    QualifiedInformation,
    QualifiedInformationKey,
    QualifiedPolicy,
)
from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition
from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
from mountainash.core.capabilities.render_markdown import (
    _resolve_concrete_owner,
    render_json,
    render_markdown,
    render_scoped,
)
from mountainash.core.capabilities.schema import CapabilityLevel, CapabilityIssueClass, InformationLayer, PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR


def _report(*, gaps=None, changes=(), kinds=frozenset(), captured=None):
    family = Scope(CONST_BACKEND.POLARS, FamilyWide())
    concrete = Scope(CONST_BACKEND.POLARS, Dialect("polars"))
    origin = SourceOrigin(
        "fixture.module", family, FactSource.SUBSTRAIT, Domain.STRING, "information[0]", captured=captured
    )
    information_key = CapabilityKey(FK_STR.LPAD, "input")
    information_assertion = CapabilityInformation(
        information_key,
        InformationLayer.NATIVE,
        CapabilityLevel.UNSUPPORTED,
        "2026-09-18",
        "native limitation",
        kinds=kinds,
    )
    information = QualifiedInformation(
        QualifiedInformationKey(family, information_key, InformationLayer.NATIVE), information_assertion, (origin,)
    )
    policy_key = CapabilityKey(FK_STR.LPAD, "input")
    policy_assertion = CapabilityPolicyRule(
        policy_key, CapabilityLevel.UNSUPPORTED, "2026-09-18", "public block", PolicyConsumer.GATE, PolicyAction.BLOCK
    )
    policy = QualifiedPolicy(
        QualifiedCapabilityKey(concrete, policy_key), policy_assertion,
        (SourceOrigin("fixture.module", concrete, FactSource.SUBSTRAIT, Domain.STRING, "policies[0]"),),
    )
    implementations = tuple(
        ImplementationRecord(FK_STR.LPAD, backend, ImplState.IMPLEMENTED, "lpad", "Fixture")
        for backend in RENDERED_BACKENDS
    )
    return build_coverage_report(
        (OpRecord(FK_STR.LPAD, type(FK_STR.LPAD).__name__),),
        (information,),
        (policy,),
        (),
        gaps,
        changes,
        implementations,
    )


def test_markdown_renders_descriptions_and_policies_in_separate_sections():
    document = render_markdown(_report())
    information = document.split("## Information", 1)[1].split("## Policies", 1)[0]
    policies = document.split("## Policies", 1)[1].split("## Known gaps", 1)[0]

    assert "native limitation" in information
    assert "public block" not in information
    assert "public block" in policies
    assert "gate / block" in policies


def test_json_keeps_information_and_policies_separate_with_provenance():
    payload = json.loads(render_json(_report()))
    cell = payload["families"][0]["ops"][0]["cells"]["polars"]

    assert set(payload) == {"stamp", "stats", "families", "segments", "information", "policies", "gaps", "changes"}
    assert cell["information"][0]["scope"]["dialect"] is None
    assert cell["policies"][0]["scope"]["dialect"] == "polars"
    assert cell["information"][0]["origins"][0]["module"] == "fixture.module"
    assert cell["policies"][0]["consumer"] == "gate"
    assert cell["policies"][0]["action"] == "block"
    assert payload["information"][0]["layer"] == "native"


def test_json_provenance_uses_source_digest_without_embedding_source_bytes():
    artifact = b"captured source\n" * 4096
    captured = CapturedAddress("fixture", "history.py", "information[0]", artifact=artifact)

    document = render_json(_report(captured=captured))

    assert len(document.encode()) < len(artifact)
    payload = json.loads(document)
    expected = {
        "repository": "fixture",
        "path": "history.py",
        "entry": "information[0]",
        "revision": None,
        "artifact": {
            "encoding": "sha256",
            "value": "9964ee80e8459cbd94d14d90dde564dacf6b21cf9bafe68df054cc4fb9d22490",
        },
    }
    assert payload["information"][0]["origins"][0]["captured"] == expected
    cell = payload["families"][0]["ops"][0]["cells"]["polars"]
    assert cell["information"][0]["origins"][0]["captured"] == expected


def test_scoped_renderer_keeps_policy_rows_out_of_the_information_section():
    scoped = render_scoped(_report())
    information, policies = scoped.split("## Policies", 1)

    assert "native limitation" in information
    assert "gate / block" not in information
    assert "public block" in policies


def test_reports_keep_multiple_information_kinds_on_one_record():
    classified = _report(kinds=frozenset({CapabilityIssueClass.PRECISION, CapabilityIssueClass.SEMANTICS}))

    scoped = render_scoped(classified)
    assert scoped.count("precision, semantics") == 1
    assert "unclassified" in render_scoped(_report())

    information = json.loads(render_json(classified))["information"]
    assert len(information) == 1
    assert information[0]["kinds"] == ["precision", "semantics"]


def test_gap_absence_and_acquired_empty_inventory_remain_distinct():
    assert "Gap inventories were not acquired." in render_markdown(_report(gaps=None))
    assert "Gap inventories were acquired and contained no gaps." in render_markdown(_report(gaps=()))


def test_change_history_is_rendered_in_canonical_order():
    information = CapabilityInformation(
        CapabilityKey(FK_STR.LPAD, "input"),
        InformationLayer.NATIVE,
        CapabilityLevel.UNSUPPORTED,
        "2026-09-18",
        "historic limitation",
    )

    def change(recorded_at, entry):
        address = CapturedAddress("fixture", "history.py", entry, artifact=entry.encode())
        prior = CapturedAssertion("capability", information.key, information, address)
        return AssertionChange(
            CapturedAddress("fixture", "changes.py", entry, artifact=f"change:{entry}".encode()),
            prior,
            ChangeDisposition.INCORRECT_DECLARATION,
            recorded_at,
            "historic correction",
        )

    newer = change("2026-09-18T12:00:00", "newer")
    older = change("2026-09-17T12:00:00", "older")
    document = render_markdown(_report(changes=(newer, older)))
    assert document.index("2026-09-17T12:00:00") < document.index("2026-09-18T12:00:00")

def test_implementation_discovery_ignores_protocol_carriers():
    class CarrierProtocol:
        def lpad(self):
            raise NotImplementedError

    class Leaf(CarrierProtocol):
        pass

    class Concrete(Leaf):
        def lpad(self):
            return "implemented"

    assert _resolve_concrete_owner(Leaf, "lpad") is None
    assert _resolve_concrete_owner(Concrete, "lpad") is Concrete


def test_markdown_distinguishes_variants_and_renders_policy_issue_classes():
    from dataclasses import replace

    report = _report()
    information = report.information[0]
    policy = report.policies[0]

    def named_information(variant):
        local = replace(information.key.local, variant=variant)
        return replace(
            information,
            key=replace(information.key, local=local),
            assertion=replace(information.assertion, key=local),
        )

    policy_local = replace(policy.key.local, variant="policy-variant")
    named_policy = replace(
        policy,
        key=replace(policy.key, local=policy_local),
        assertion=replace(
            policy.assertion,
            key=policy_local,
            issue_classes=frozenset({CapabilityIssueClass.SEMANTICS}),
        ),
    )
    rendered = render_scoped(replace(
        report,
        information=(named_information("first-variant"), named_information("second-variant")),
        policies=(named_policy,),
    ))

    assert "first-variant" in rendered
    assert "second-variant" in rendered
    assert "policy-variant" in rendered
    assert "semantics" in rendered
