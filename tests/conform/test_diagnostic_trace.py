from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.conform.errors import ConformError, ConformTransformError
from mountainash.conform.expressions import MaterializationResidueCheck
from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Clause,
    ClauseOp,
    Enforcement,
    Predicate,
    ResidueSignal,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import CapabilityResidueInvariantError
from mountainash.core.limitations import enrich_materialization
from mountainash.core.types import BackendCapabilityError
from mountainash.exceptions import CapabilityResidueInvariantError as PublicInvariantError
from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST,
)
from mountainash import relation
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


KEY = FKEY_MOUNTAINASH_SCALAR_LIST.LEN
BACKEND = CONST_BACKEND.NARWHALS


@dataclass
class Backend:
    backend_type: CONST_BACKEND = BACKEND
    dialect: str = "narwhals-pandas"
    BACKEND_NAME: str = "narwhals"


def _fact(**overrides):
    values = dict(
        operation_key=KEY,
        param="x",
        level=CapabilityLevel.UNSUPPORTED,
        backend=BACKEND,
        dialect="narwhals-pandas",
        boundary=Boundary.MATERIALIZE,
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        native_errors=(TypeError,),
        message="list parse is unsupported",
        since="2026-08-21",
    )
    values.update(overrides)
    return CapabilityFact(**values)


def _node(*, field: str = "values", item_type: str = "integer", failure_behavior: str = "throw"):
    return ScalarFunctionNode(
        function_key=KEY,
        arguments=[FieldReferenceNode(field="raw")],
        options={"item_type": item_type, "failure_behavior": failure_behavior},
        diagnostic_context={"field_name": field, "logical_type": "list", "format": "default"},
    )


def test_diagnostic_context_serializes_but_does_not_enter_options() -> None:
    node = _node()
    dumped = node.model_dump(mode="json")
    assert dumped["diagnostic_context"]["field_name"] == "values"
    assert "field_name" not in node.options
def test_diagnostic_context_is_immutable() -> None:
    node = _node()
    with pytest.raises(TypeError):
        node.diagnostic_context["field_name"] = "other"


def test_diagnostic_context_union_cannot_mutate_trace_attribution() -> None:
    node = _node()
    trace = OperationDiagnosticTrace()
    trace.record(
        node,
        backend_family=BACKEND.value,
        dialect=Backend().dialect,
        conform_node_id="immutable",
    )
    with pytest.raises(TypeError):
        node.diagnostic_context |= {"field_name": "other"}
    assert trace.records[0].field_name == "values"






def test_fact_key_namespaces_operation_enum_type() -> None:
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )

    first = _fact(operation_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM)
    second = _fact(operation_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM)
    assert first.fact_key != second.fact_key






def test_trace_fingerprint_uses_only_safe_routing_options() -> None:
    node = ScalarFunctionNode(
        function_key=KEY,
        arguments=[FieldReferenceNode(field="raw")],
        options={
            "item_type": "integer",
            "failure_behavior": "throw",
            "format": "default",
            "source_representation": "lexical",
            "kind": "array",
            "value_type": "integer",
            "categories": ("private", "values"),
            "nested_fields": (("secret", "schema"),),
        },
        diagnostic_context={"field_name": "values", "logical_type": "list", "format": "default"},
    )
    trace = OperationDiagnosticTrace()
    trace.record(node, backend_family="narwhals", dialect="narwhals-pandas", conform_node_id="node-1")
    assert trace.records[0].routing_fingerprint == (
        ("failure_behavior", "throw"),
        ("format", "default"),
        ("item_type", "integer"),
        ("kind", "array"),
        ("source_representation", "lexical"),
        ("value_type", "integer"),
    )


def test_null_residue_requires_empty_native_errors() -> None:
    with pytest.raises(ValueError):
        _fact(residue_signal=ResidueSignal.NON_NULL_TO_NULL, native_errors=(TypeError,))
    _fact(residue_signal=ResidueSignal.NON_NULL_TO_NULL, native_errors=())


def test_exception_residue_requires_native_errors() -> None:
    with pytest.raises(ValueError):
        _fact(native_errors=())


def test_non_null_residue_requires_materialize_residue() -> None:
    with pytest.raises(ValueError):
        CapabilityFact(
            operation_key=KEY,
            param="item_type",
            level=CapabilityLevel.UNSUPPORTED,
            backend=BACKEND,
            boundary=Boundary.BUILD,
            enforcement=Enforcement.GATE,
            residue_signal=ResidueSignal.NON_NULL_TO_NULL,
            since="2026-08-21",
        )





def test_true_marker_with_fact_enriches_and_context() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        from mountainash.core.capabilities.declarations import (
            BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
        )
        from mountainash.core.capabilities.identity import Dialect, Scope
        from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer

        policy = CapabilityPolicyRule(
            CapabilityKey(KEY, "x"), CapabilityLevel.UNSUPPORTED, "2026-09-18",
            "null residue", PolicyConsumer.RESULT_PROTECTION,
            PolicyAction.DETECT_NON_NULL_TO_NULL,
        )
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pandas.extensions_mountainash.list.trace_case",
            Scope(BACKEND, Dialect("narwhals-pandas")),
            CapabilitySegment(Domain.LIST, policies=(policy,)),
        ))
        frame = pd.DataFrame({"values": [None], "__ma_residue_0": [True]})
        trace = OperationDiagnosticTrace()
        trace.record(
            _node(),
            backend_family=BACKEND.value,
            dialect=Backend().dialect,
            conform_node_id="n1",
        )
        checks = (MaterializationResidueCheck(KEY, "values", "__ma_residue_0"),)
        with pytest.raises(BackendCapabilityError) as raised:
            enrich_materialization(
                Backend(), lambda: frame, diagnostic_trace=trace, residue_checks=checks
            )
        assert raised.value.context == {
            "field_name": "values",
            "logical_type": "list",
            "format": "default",
        }
    finally:
        CapabilityRegistry.restore(snapshot)










def test_null_markers_are_removed_when_false() -> None:
    frame = pd.DataFrame(
        {"values": [1], "__ma_residue_0": [False], "__ma_residue_1": [False]}
    )
    trace = OperationDiagnosticTrace()
    trace.record(
        _node(),
        backend_family=BACKEND.value,
        dialect=Backend().dialect,
        conform_node_id="n1",
    )
    checks = (
        MaterializationResidueCheck(KEY, "values", "__ma_residue_0"),
        MaterializationResidueCheck(KEY, "values", "__ma_residue_1"),
    )
    result = enrich_materialization(
        Backend(), lambda: frame, diagnostic_trace=trace, residue_checks=checks
    )
    assert list(result.columns) == ["values"]


def test_true_marker_without_winning_fact_raises_invariant() -> None:
    frame = pd.DataFrame({"values": [None], "__ma_residue_0": [True]})
    trace = OperationDiagnosticTrace()
    trace.record(_node(), backend_family=BACKEND.value, dialect=Backend().dialect, conform_node_id="n1")
    checks = (MaterializationResidueCheck(KEY, "values", "__ma_residue_0"),)
    with pytest.raises(CapabilityResidueInvariantError):
        enrich_materialization(Backend(), lambda: frame, diagnostic_trace=trace, residue_checks=checks)
    assert PublicInvariantError is CapabilityResidueInvariantError

def test_relation_terminal_enriches_temporal_null_residue() -> None:
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="duration", type=UniversalType.DURATION)],
    )
    with pytest.raises(BackendCapabilityError) as raised:
        relation(pd.DataFrame({"duration": ["not-a-duration"]})).conform(spec).collect()
    assert "not-a-duration" not in str(raised.value)
    assert raised.value.context == {
        "field_name": "duration",
        "logical_type": "parse_xsd_duration",
        "format": "default",
    }

def test_relation_terminal_removes_collision_safe_residue_marker() -> None:
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="duration", type=UniversalType.DURATION)],
    )
    result = relation(
        pd.DataFrame(
            {
                "duration": ["P1D"],
                "__ma_residue_conform_0_0": ["keep"],
            }
        )
    ).conform(spec).collect()
    assert list(result.columns) == ["duration", "__ma_residue_conform_0_0"]

def test_polars_throw_mode_temporal_failure_is_transform_error() -> None:
    import polars as pl

    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="duration", type=UniversalType.DURATION)],
    )
    with pytest.raises(ConformTransformError) as raised:
        relation(pl.DataFrame({"duration": ["not-a-duration"]})).conform(spec).collect()
    assert raised.value.candidates[0].field_name == "duration"

def test_relation_lazy_terminal_removes_residue_markers() -> None:
    import polars as pl

    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="duration", type=UniversalType.DURATION)],
    )
    result = relation(
        pl.DataFrame({"duration": ["P1D"]}).lazy()
    ).conform(spec).collect()
    assert result.columns == ["duration"]


def test_dag_collect_owns_residue_terminal_and_preserves_lazy_shape() -> None:
    import polars as pl
    from mountainash.relations.dag.dag import RelationDAG

    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="duration", type=UniversalType.DURATION)],
    )
    dag = RelationDAG()
    dag.add("durations", relation(pl.DataFrame({"duration": ["P1D"]})).conform(spec))
    result = dag.collect("durations")
    assert isinstance(result, pl.LazyFrame)
    assert result.collect().columns == ["duration"]
