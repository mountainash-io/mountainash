"""Information-kind labels are immutable descriptive metadata only."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilitySegment
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK


@pytest.fixture(autouse=True)
def isolated_registry():
    from mountainash.core.capabilities.registry import _LoadState, _empty_state

    before = CapabilityRegistry.snapshot()
    CapabilityRegistry.restore(_empty_state(_LoadState.LOADED))
    try:
        yield
    finally:
        CapabilityRegistry.restore(before)


def _segment(information):
    from mountainash.core.capabilities.declarations import Domain

    scope = Scope(CONST_BACKEND.POLARS, Dialect("polars"))
    return BoundSegment(
        "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.string.kinds",
        scope,
        CapabilitySegment(Domain.STRING, information=(information,)),
    )


def test_one_information_record_has_two_descriptive_kind_views_without_execution_effect():
    from mountainash.core.capabilities.catalogue import InformationQuery
    from mountainash.core.capabilities.declarations import CapabilityInformation
    from mountainash.core.capabilities.schema import CapabilityIssueClass, InformationLayer

    information = CapabilityInformation(
        key=CapabilityKey(FK.CONTAINS, "substring"),
        layer=InformationLayer.NATIVE,
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-18",
        message="Classified descriptive claim",
        kinds=frozenset({CapabilityIssueClass.PRECISION, CapabilityIssueClass.SEMANTICS}),
    )
    segment = _segment(information)
    CapabilityRegistry.register_segment(segment)

    capture = CapabilityRegistry.capture()
    semantic = capture.reader(segment.scope).search(InformationQuery(kind=CapabilityIssueClass.SEMANTICS))
    precision = capture.reader(segment.scope).search(InformationQuery(kind=CapabilityIssueClass.PRECISION))
    composed = capture.composed_information(segment.scope)

    assert semantic == precision == composed
    assert semantic[0] is precision[0] is composed[0]
    assert semantic[0].key.scope is segment.scope
    assert semantic[0].key.local is information.key
    assert semantic[0].assertion.kinds == frozenset({CapabilityIssueClass.PRECISION, CapabilityIssueClass.SEMANTICS})
    assert CapabilityRegistry.capability_for(FK.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars") is None


@pytest.mark.parametrize("kinds", ({"semantics"}, frozenset({"semantics"})))
def test_information_kinds_require_an_exact_typed_frozenset(kinds):
    from mountainash.core.capabilities.declarations import CapabilityInformation
    from mountainash.core.capabilities.schema import InformationLayer

    with pytest.raises(TypeError, match="kinds"):
        CapabilityInformation(
            key=CapabilityKey(FK.CONTAINS, "substring"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-09-18",
            message="Invalid category payload",
            kinds=kinds,
        )


def test_information_kind_query_requires_information_kind():
    from mountainash.core.capabilities.catalogue import InformationQuery

    with pytest.raises(TypeError, match="kind"):
        InformationQuery(kind="semantics")
