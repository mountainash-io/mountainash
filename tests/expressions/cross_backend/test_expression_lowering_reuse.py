"""Shared lowering must reduce work without crossing semantic contexts."""
from __future__ import annotations

import weakref
from functools import wraps

import pytest
from ibis.common.deferred import Deferred

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.capabilities.policy import _new_execution_context
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_shared_arithmetic_reduces_lowering_work(backend_name, backend_factory, monkeypatch):
    frame = backend_factory.create({"x": [1, 2]}, backend_name)
    shared = ma.col("x") + 1
    left, right = ma.col("x") + 1, ma.col("x") + 1
    calls = {"shared": 0, "distinct": 0}
    original = ScalarFunctionNode.accept

    def observe(node, visitor):
        if node is shared.node:
            calls["shared"] += 1
        elif node is left.node or node is right.node:
            calls["distinct"] += 1
        return original(node, visitor)

    monkeypatch.setattr(ScalarFunctionNode, "accept", observe)
    for expression in (shared + shared, left + right):
        result = ma.relation(frame).select(expression.alias("out")).to_polars()
        assert result["out"].to_list() == [4, 6]
    assert calls["shared"] < calls["distinct"]


def _visitor_for(source):
    identity = identify_backend_identity(source)
    context = _new_execution_context(source)
    system = get_expression_system(identity.family)(dialect=identity.dialect, execution_context=context)
    return UnifiedExpressionVisitor(system, input_data=source, execution_context=context)


def _values_for(source, native):
    if isinstance(native, Deferred):
        native = native.resolve(source)
    return ma.relation(source).select(ma.native(native).alias("out")).to_dict()["out"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_shared_window_preserves_values_refusals_and_binding(backend_name, backend_factory):
    source = backend_factory.create({"g": [1, 1, 1], "a": [1, 2, 3]}, backend_name)
    left, right = ma.col("a").lag().is_null(), ma.col("a").lag().is_null()
    distinct = left.over("g", order_by="a") | right.over("g", order_by="-a")
    shared = left.over("g", order_by="a") | left.over("g", order_by="-a")

    def outcome(expression):
        try:
            actual = ma.relation(source).select("a", expression.alias("out")).sort("a").to_dict()["out"]
        except BackendCapabilityError as error:
            return type(error), str(error)
        assert actual == [True, False, True]
        return actual

    with ma.capability_policy(ma.CapabilityPolicy.checked()):
        assert outcome(shared) == outcome(distinct)
        with pytest.raises(ValueError):
            ma.relation(source).select(
                left.over("g", order_by="a").alias("valid"),
                left.alias("unbound"),
            ).to_polars()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_nested_scope_failure_releases_nodes_and_restores_input(backend_name, backend_factory):
    integers = backend_factory.create({"x": [1, 2]}, backend_name)
    strings = backend_factory.create({"x": ["a", "b"]}, backend_name)
    booleans = backend_factory.create({"x": [True, False]}, backend_name)
    visitor = _visitor_for(integers)
    shared = ma.col("x").value_kind()
    outer_ref = weakref.ref(shared.node)
    with visitor.input_scope(integers):
        assert _values_for(integers, visitor.visit(shared.node)) == ["integer", "integer"]
        with pytest.raises(ValueError):
            with visitor.input_scope(strings):
                ephemeral = ma.col("x").value_kind()
                inner_ref = weakref.ref(ephemeral.node)
                visitor.visit(ephemeral.node)
                del ephemeral
                assert _values_for(strings, visitor.visit(shared.node)) == ["text", "text"]
                visitor.visit(ma.col("x").lag().node)
        assert inner_ref() is None
        assert _values_for(integers, visitor.visit(shared.node)) == ["integer", "integer"]
    with pytest.raises(BackendCapabilityError):
        visitor.resolve_operand_type(shared.node)
    with visitor.input_scope(booleans):
        assert _values_for(booleans, visitor.visit(shared.node)) == ["boolean", "boolean"]
    del shared
    assert outer_ref() is None


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_tracing_after_cached_lowering_keeps_occurrences(backend_name, backend_factory):
    source = backend_factory.create({"x": [1, 2]}, backend_name)
    visitor = _visitor_for(source)
    shared = ma.col("x") + 1
    first, second = OperationDiagnosticTrace(), OperationDiagnosticTrace()
    with visitor.input_scope(source):
        for trace, owner in [
            (None, None), (first, "first"), (first, "first"), (None, None), (second, "second"),
        ]:
            visitor.diagnostic_trace = trace
            visitor.conform_node_id = owner
            assert _values_for(source, visitor.visit(shared.node)) == [2, 3]
    assert [record.conform_node_id for record in first.records] == ["first", "first"]
    assert [record.conform_node_id for record in second.records] == ["second"]
    assert all(record.function_key.name == "ADD" for record in first.records + second.records)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_occurrence_failure_keeps_diagnostic(backend_name, backend_factory, monkeypatch):
    source = backend_factory.create({"x": [1, 2]}, backend_name)
    visitor = _visitor_for(source)
    system = type(visitor.backend)
    original_add = system.add
    calls = 0

    @wraps(original_add)
    def add(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise ValueError("occurrence failed")
        return original_add(self, *args, **kwargs)

    monkeypatch.setattr(system, "add", add)
    shared = ma.col("x") + 1
    with visitor.input_scope(source):
        assert _values_for(source, visitor.visit((ma.col("x") * 2).node)) == [2, 4]
        assert _values_for(source, visitor.visit(shared.node)) == [2, 3]
        for _ in range(2):
            with pytest.raises(ValueError, match="occurrence failed"):
                visitor.visit(shared.node)
        trace = OperationDiagnosticTrace()
        visitor.diagnostic_trace = trace
        visitor.conform_node_id = "failing"
        with pytest.raises(ValueError, match="occurrence failed"):
            visitor.visit(shared.node)
        assert visitor.raising_diagnostic is trace.records[-1]
        assert visitor.raising_diagnostic.conform_node_id == "failing"
        assert visitor.raising_diagnostic.function_key.name == "ADD"
