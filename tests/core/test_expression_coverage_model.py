"""Coverage report model tests for distinct information and policy inputs."""

from __future__ import annotations

import pytest

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    ImplementationRecord,
    ImplState,
    OpRecord,
    build_coverage_report,
)
from mountainash.core.capabilities.capture import SourceOrigin
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
from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
from mountainash.core.capabilities.schema import (
    CapabilityLevel,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _universe():
    return (OpRecord(FK_STR.LPAD, type(FK_STR.LPAD).__name__),)


def _implementations():
    return tuple(
        ImplementationRecord(FK_STR.LPAD, backend, ImplState.IMPLEMENTED, "lpad", "Fixture")
        for backend in RENDERED_BACKENDS
    )


def _origin(scope):
    return SourceOrigin("fixture.module", scope, FactSource.SUBSTRAIT, Domain.STRING, "information[0]")


def _information(scope, operation=FK_STR.LPAD, subject="input"):
    key = CapabilityKey(operation, subject)
    assertion = CapabilityInformation(
        key, InformationLayer.NATIVE, CapabilityLevel.UNSUPPORTED, "2026-09-18", "native limitation"
    )
    return QualifiedInformation(QualifiedInformationKey(scope, key, assertion.layer), assertion, (_origin(scope),))


def _policy(scope):
    key = CapabilityKey(FK_STR.LPAD, "input")
    assertion = CapabilityPolicyRule(
        key, CapabilityLevel.UNSUPPORTED, "2026-09-18", "public block", PolicyConsumer.GATE, PolicyAction.BLOCK
    )
    return QualifiedPolicy(QualifiedCapabilityKey(scope, key), assertion, (_origin(scope),))


def test_report_preserves_distinct_records_and_their_original_scopes():
    family = Scope(CONST_BACKEND.POLARS, FamilyWide())
    concrete = Scope(CONST_BACKEND.POLARS, Dialect("polars"))
    information = _information(family)
    policy = _policy(concrete)

    report = build_coverage_report(_universe(), (information,), (policy,), (), None, (), _implementations())
    cell = report.families[0].ops[0]

    assert report.information == (information,)
    assert report.policies == (policy,)
    assert cell.information == (information,)
    assert cell.policies == (policy,)
    assert cell.information[0].key.scope is family
    assert cell.policies[0].key.scope is concrete
    assert report.stats.information_total == 1
    assert report.stats.policies_total == 1


def test_report_rejects_unknown_operation_and_duplicate_implementation_cells():
    family = Scope(CONST_BACKEND.POLARS, FamilyWide())
    outside = _information(family, FK_STR.RPAD)
    with pytest.raises(ValueError, match="outside the registered universe"):
        build_coverage_report(_universe(), (outside,), (), (), None, (), _implementations())

    implementations = list(_implementations())
    implementations[-1] = implementations[0]
    with pytest.raises(ValueError, match="duplicate implementation record"):
        build_coverage_report(_universe(), (), (), (), None, (), tuple(implementations))

def test_report_orders_qualified_information_independent_of_input_order():
    scope = Scope(CONST_BACKEND.POLARS, FamilyWide())
    replacement = _information(scope, subject="replacement")
    input_value = _information(scope, subject="input")

    report = build_coverage_report(
        _universe(),
        (replacement, input_value),
        (),
        (),
        None,
        (),
        _implementations(),
    )

    assert tuple(record.key.local.subject for record in report.information) == ("input", "replacement")
