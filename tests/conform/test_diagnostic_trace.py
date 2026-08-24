from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd
import pytest

from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.conform.errors import ConformError
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


def test_legacy_residue_fallback_survives_unmatched_trace() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_backend(
            BACKEND, [_fact(native_errors=(KeyError,))]
        )
        trace = OperationDiagnosticTrace()
        trace.record(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM,
                arguments=[FieldReferenceNode(field="raw")],
                diagnostic_context={
                    "field_name": "other",
                    "logical_type": "list",
                    "format": "default",
                },
            ),
            backend_family=BACKEND.value,
            dialect=Backend().dialect,
            conform_node_id="other",
        )
        with pytest.raises(BackendCapabilityError) as raised:
            enrich_materialization(
                Backend(),
                lambda: (_ for _ in ()).throw(KeyError("native")),
                diagnostic_trace=trace,
            )
        assert raised.value.function_key == KEY
    finally:
        CapabilityRegistry.restore(snapshot)


def test_fact_key_namespaces_operation_enum_type() -> None:
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    )

    first = _fact(operation_key=FKEY_MOUNTAINASH_SCALAR_LIST.SUM)
    second = _fact(operation_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM)
    assert first.fact_key != second.fact_key


def test_fact_key_accepts_mixed_predicate_set_operands() -> None:
    fact = _fact(
        param="item_type",
        boundary=Boundary.BUILD,
        enforcement=Enforcement.GATE,
        predicate=Predicate(
            (
                Clause("item_type", ClauseOp.IN, frozenset({"integer", 1})),
            )
        ),
    )
    assert fact.fact_key




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

def test_build_fact_keeps_exception_signal() -> None:
    fact = CapabilityFact(
        operation_key=KEY,
        param="item_type",
        level=CapabilityLevel.UNSUPPORTED,
        backend=BACKEND,
        since="2026-08-21",
    )
    assert fact.residue_signal is ResidueSignal.EXCEPTION


def test_one_winning_exception_fact_enriches_with_context() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        fact = _fact()
        CapabilityRegistry.register_backend(BACKEND, [fact])
        trace = OperationDiagnosticTrace()
        trace.record(_node(), backend_family=BACKEND.value, dialect=Backend().dialect, conform_node_id="n1")
        with pytest.raises(BackendCapabilityError) as raised:
            enrich_materialization(Backend(), lambda: (_ for _ in ()).throw(TypeError("native")), diagnostic_trace=trace)
        assert raised.value.function_key == KEY
        assert raised.value.context == {"field_name": "values", "logical_type": "list", "format": "default"}
    finally:
        CapabilityRegistry.restore(snapshot)


def test_true_marker_with_fact_enriches_and_context() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        fact = _fact(
            residue_signal=ResidueSignal.NON_NULL_TO_NULL,
            native_errors=(),
            message="null residue",
        )
        CapabilityRegistry.register_backend(BACKEND, [fact])
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


def test_multiple_fields_share_fact_key_and_are_sorted() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_backend(BACKEND, [_fact()])
        trace = OperationDiagnosticTrace()
        trace.record(
            _node(field="z_values"),
            backend_family=BACKEND.value,
            dialect=Backend().dialect,
            conform_node_id="z",
        )
        trace.record(
            _node(field="a_values"),
            backend_family=BACKEND.value,
            dialect=Backend().dialect,
            conform_node_id="a",
        )
        with pytest.raises(BackendCapabilityError) as raised:
            enrich_materialization(
                Backend(),
                lambda: (_ for _ in ()).throw(TypeError("native")),
                diagnostic_trace=trace,
            )
        assert raised.value.candidate_fields == ("a_values", "z_values")
        assert raised.value.context is None
    finally:
        CapabilityRegistry.restore(snapshot)


def test_multiple_fact_keys_use_generic_message() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        other_key = FKEY_MOUNTAINASH_SCALAR_LIST.SUM
        CapabilityRegistry.register_backend(
            BACKEND,
            [_fact(), _fact(operation_key=other_key, message="other residue")],
        )
        trace = OperationDiagnosticTrace()
        trace.record(
            _node(field="values"),
            backend_family=BACKEND.value,
            dialect=Backend().dialect,
            conform_node_id="one",
        )
        trace.record(
            ScalarFunctionNode(
                function_key=other_key,
                arguments=[FieldReferenceNode(field="raw")],
                options={"failure_behavior": "throw"},
                diagnostic_context={
                    "field_name": "other",
                    "logical_type": "list",
                    "format": "default",
                },
            ),
            backend_family=BACKEND.value,
            dialect=Backend().dialect,
            conform_node_id="two",
        )
        with pytest.raises(BackendCapabilityError) as raised:
            enrich_materialization(
                Backend(),
                lambda: (_ for _ in ()).throw(TypeError("native")),
                diagnostic_trace=trace,
            )
        assert raised.value.function_key is None
        assert raised.value.candidate_fields == ("other", "values")
        assert "multiple conform operations" in str(raised.value)
        assert "integer" not in str(raised.value)
    finally:
        CapabilityRegistry.restore(snapshot)


def test_unmatched_exception_passes_through() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_backend(BACKEND, [_fact()])
        trace = OperationDiagnosticTrace()
        trace.record(
            _node(),
            backend_family=BACKEND.value,
            dialect=Backend().dialect,
            conform_node_id="n1",
        )
        original = ValueError("unmatched")
        with pytest.raises(ValueError) as raised:
            enrich_materialization(
                Backend(),
                lambda: (_ for _ in ()).throw(original),
                diagnostic_trace=trace,
            )
        assert raised.value is original
    finally:
        CapabilityRegistry.restore(snapshot)


def test_existing_capability_and_conform_errors_pass_through() -> None:
    trace = OperationDiagnosticTrace()
    trace.record(_node(), backend_family=BACKEND.value, dialect=Backend().dialect, conform_node_id="n1")
    capability_error = BackendCapabilityError("already enriched", backend="narwhals", function_key=KEY)
    conform_error = ConformError("already conform error")
    for original in (capability_error, conform_error):
        with pytest.raises(type(original)) as raised:
            enrich_materialization(Backend(), lambda original=original: (_ for _ in ()).throw(original), diagnostic_trace=trace)
        assert raised.value is original


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
