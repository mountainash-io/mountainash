"""Targeted execution retains logical lineage and source attribution."""

from __future__ import annotations

import pytest
from fixtures.backend_registry import REGISTRY

import mountainash as ma
from mountainash.conform.errors import UnsupportedStructuredTransportUse
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK,
)
from mountainash.relations.core.errors import LogicalTerminalRequired
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL as RS
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


@pytest.mark.parametrize("source_name", list(REGISTRY))
@pytest.mark.parametrize("destination_name", ["polars", "ibis-duckdb", "narwhals-polars"])
def test_transported_structured_field_keeps_terminal_guard(source_name, destination_name):
    source_frame = REGISTRY[source_name].build({"id": [1, 2], "payload": ["[1,2]", "[3]"]}, "source")
    destination_frame = REGISTRY[destination_name].build({"id": [1, 2]}, "target")
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    source = ma.relation(source_frame).conform(spec, contract={"data_type": "coerce"})
    rel = source.join(destination_frame, on="id", execute_on="right").rename({"payload": "body"})
    with pytest.raises(LogicalTerminalRequired):
        rel.collect()
    assert rel.sort("id").to_dict()["body"] == [[1, 2], [3]]


def test_targeted_join_and_parent_gate_at_destination_but_source_filter_stays_at_source(monkeypatch):
    a = REGISTRY["ibis-duckdb"].build({"id": [1, 2]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    real = CapabilityRegistry.capability_for
    calls = []

    def observed(*args, **kwargs):
        calls.append((args, kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(CapabilityRegistry, "capability_for", observed)
    rel = ma.relation(a).filter(ma.col("id") > 0).join(b, on="id", execute_on="right").filter(ma.col("id") > 1)
    result = rel.collect()
    assert result._find_backend(use_default=False) is b._find_backend(use_default=False)
    assert ma.relation(result).to_dict() == {"id": [2]}
    seen = {
        (arg[0], arg[3] if len(arg) > 3 else kw.get("dialect"))
        for arg, kw in calls
        if arg and arg[0] in {RS.JOIN, RS.FILTER}
    }
    assert (RS.FILTER, "ibis-duckdb") in seen
    assert (RS.FILTER, "ibis-sqlite") in seen
    assert (RS.JOIN, "ibis-sqlite") in seen


def test_source_xsd_error_after_join_suffix_keeps_source_field_and_operation():
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
                Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
                CapabilitySegment(
                    Domain.DATETIME,
                    policies=(
                        CapabilityPolicyRule(
                            key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"),
                            level=CapabilityLevel.UNSUPPORTED,
                            message="Invalid lexical year became null",
                            consumer=PolicyConsumer.RESULT_PROTECTION,
                            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
        a = REGISTRY["ibis-duckdb"].build({"id": [1], "year": ["invalid"]}, "source")
        b = REGISTRY["ibis-sqlite"].build({"id": [1], "year": ["2024"]}, "destination")
        spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="year", type=UniversalType.YEAR)])
        rel = ma.relation(a).conform(spec).join(b, on="id", execute_on="right", suffix="_source")
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            with pytest.raises(BackendCapabilityError) as caught:
                rel.collect()
        assert caught.value.context["field_name"] == "year"
        assert caught.value.function_key is FK.PARSE_XSD_PARTIAL_DATE
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("backend_name", list(REGISTRY))
def test_two_conform_children_retain_distinct_origins_after_suffix_and_rename(backend_name, backend_factory):
    first, second = backend_factory.create_pair(
        {"id": [1], "payload": ["[1]"]},
        {"id": [1], "payload": ["[2]"]},
        backend_name,
    )
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    rel = (
        ma.relation(first)
        .conform(spec)
        .join(ma.relation(second).conform(spec), on="id", suffix="_other")
        .rename({"payload": "body"})
    )
    native, visitor = rel._compile_and_execute_with_visitor()
    assert set(visitor.structured_field_plans) == {"body", "payload_other"}
    assert (
        visitor.structured_field_plans["body"].origin_node_id
        != visitor.structured_field_plans["payload_other"].origin_node_id
    )
    assert all(not name.startswith("__ma_residue_") for name in ma.relation(native).to_dict())
    assert rel.select("id", "body", "payload_other").to_dicts() == [{"id": 1, "body": [1], "payload_other": [2]}]


def test_source_check_markers_do_not_leak_through_same_connection_join_suffix_and_select(backend_factory):
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
                Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
                CapabilitySegment(
                    Domain.DATETIME,
                    policies=(
                        CapabilityPolicyRule(
                            key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"),
                            level=CapabilityLevel.UNSUPPORTED,
                            message="Invalid lexical year became null",
                            consumer=PolicyConsumer.RESULT_PROTECTION,
                            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
        left, right = backend_factory.create_pair(
            {"id": [1], "year": ["2024"]}, {"id": [1], "year": ["2025"]}, "ibis-duckdb"
        )
        spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="year", type=UniversalType.YEAR)])
        rel = ma.relation(left).join(ma.relation(right).conform(spec), on="id", suffix="_right")
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            result = rel.collect()
            projected = rel.select("id", "year_right").collect()
        assert ma.relation(result).to_dict() == {"id": [1], "year": ["2024"], "year_right": ["2025"]}
        assert ma.relation(projected).to_dict() == {"id": [1], "year_right": ["2025"]}
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("backend_name", list(REGISTRY))
@pytest.mark.parametrize("distinct", [False, True])
def test_union_rejects_structured_tag_only_on_later_input(backend_name, backend_factory, distinct):
    left, right = backend_factory.create_pair(
        {"id": [1], "payload": ["[1]"]},
        {"id": [2], "payload": ["[2]"]},
        backend_name,
    )
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    rel = ma.concat([ma.relation(left), ma.relation(right).conform(spec)], distinct=distinct)
    with pytest.raises(UnsupportedStructuredTransportUse):
        rel.collect()


@pytest.mark.parametrize(
    "backend_name",
    [
        pytest.param(
            name,
            marks=pytest.mark.xfail(
                strict=True,
                reason="Ibis-Polars repeated structured-plan union panics in Polars CSE optimizer",
            ),
        )
        if name == "ibis-polars"
        else name
        for name in REGISTRY
    ],
)
def test_union_all_of_matching_origin_keeps_logical_array(backend_name, backend_factory):
    frame = backend_factory.create({"id": [1], "payload": ["[1,2]"]}, backend_name)
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    child = ma.relation(frame).conform(spec)
    rel = ma.concat([child, child.filter(ma.col("id") > 0)])
    result = rel.to_dict()
    assert result["id"] == [1, 1]
    assert result["payload"] == [[1, 2], [1, 2]]


def test_union_checks_source_residue_before_set_discards_marker(backend_factory):
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
                Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
                CapabilitySegment(
                    Domain.DATETIME,
                    policies=(
                        CapabilityPolicyRule(
                            key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"),
                            level=CapabilityLevel.UNSUPPORTED,
                            message="Invalid lexical year became null",
                            consumer=PolicyConsumer.RESULT_PROTECTION,
                            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
        left, right = backend_factory.create_pair(
            {"id": [1], "year": ["invalid"]}, {"id": [2], "year": ["2024"]}, "ibis-duckdb"
        )
        spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="year", type=UniversalType.YEAR)])
        rel = ma.concat([ma.relation(left).conform(spec), ma.relation(right).conform(spec)])
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            with pytest.raises(BackendCapabilityError) as caught:
                rel.collect()
        assert caught.value.context["field_name"] == "year"
        assert caught.value.function_key is FK.PARSE_XSD_PARTIAL_DATE
    finally:
        CapabilityRegistry.restore(snapshot)


def test_union_discards_checked_marker_from_valid_source(backend_factory):
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
                Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
                CapabilitySegment(
                    Domain.DATETIME,
                    policies=(
                        CapabilityPolicyRule(
                            key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"),
                            level=CapabilityLevel.UNSUPPORTED,
                            message="Invalid lexical year became null",
                            consumer=PolicyConsumer.RESULT_PROTECTION,
                            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
        left, right = backend_factory.create_pair(
            {"id": [1], "year": ["2024"]}, {"id": [2], "year": ["2025"]}, "ibis-duckdb"
        )
        spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="year", type=UniversalType.YEAR)])
        rel = ma.concat([ma.relation(left).conform(spec), ma.relation(right).conform(spec)])
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            out = rel.collect()
        assert ma.relation(out).sort("id").to_dict() == {"id": [1, 2], "year": ["2024", "2025"]}
    finally:
        CapabilityRegistry.restore(snapshot)
