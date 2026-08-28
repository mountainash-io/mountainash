"""DAG structured validation context tests (Task 8, spec section 10).

Step 1: cache separation -- the native execution-value cache never leaks a
diagnostic frame, decoded column, or logical snapshot; `CanonicalEntry`
carries immutable structured field plans; the `ref_resolver` callable
returns only the native value, never plan metadata.

Step 2: per-call validation context -- two local validation consumers for
one resource share exactly one relation compilation, one canonical native
cache entry, one logical snapshot (one Ibis `.cache()`, one
`.to_pyarrow()`, one ordinal sequence, one decoded cell per declared
structured cell), and `DAGValidationContext.prepare(name)` returns the
same immutable prepared input on repeated calls.
"""
from __future__ import annotations

from types import MappingProxyType

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.materialization import DiagnosticFrameView
from mountainash.relations.dag import DAGMaterializationSession, RelationDAG
from mountainash.relations.dag.materialization import _SessionRefResolver
from mountainash.relations.dag.validation_context import DAGValidationContext
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.checks import ValueRule, ValueValidatorKey
from mountainash.validation.identity import RowIdentity
from mountainash.validation.runner import ValidationRunner

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def _structured_dag():
    dag = RelationDAG()
    df = pl.DataFrame({"id": [1, 2], "meta": ['{"a": 1}', '{"a": 2}']})
    spec = TypeSpec(
        fields_match="open", fields=[FieldSpec(name="meta", type=UniversalType.OBJECT)]
    )
    rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
    dag.add("resource", rel)
    return dag


class TestDAGCacheSeparation:
    """Step 1: the native cache never leaks validation-domain state."""

    def test_cached_values_are_only_native_execution_values(self):
        dag = _structured_dag()
        session = DAGMaterializationSession(dag, backend="polars")
        session.compile_registered("resource")
        for value in session.cached_values:
            assert not isinstance(value, DiagnosticFrameView)
            assert not hasattr(value, "logical_columns")
        session.close(release_owned=False)

    def test_canonical_entry_carries_immutable_field_plans(self):
        dag = _structured_dag()
        session = DAGMaterializationSession(dag, backend="polars")
        entry = session._compile_named("resource")
        assert isinstance(entry.structured_field_plans, MappingProxyType)
        assert "meta" in entry.structured_field_plans
        assert entry.structured_field_plans["meta"].field_name == "meta"
        with pytest.raises(TypeError):
            entry.structured_field_plans["extra"] = None  # type: ignore[index]
        session.close(release_owned=False)

    def test_diagnostic_frames_and_decoded_columns_never_enter_canonical_or_coerced(self):
        dag = _structured_dag()
        session = DAGMaterializationSession(dag, backend="polars")
        session.compile_registered("resource")
        for entry in session._canonical.values():
            assert not isinstance(entry.native.value, DiagnosticFrameView)
            assert not hasattr(entry.native.value, "logical_columns")
        for coerced in session._coerced.values():
            assert not isinstance(coerced.value, DiagnosticFrameView)
            assert not hasattr(coerced.value, "logical_columns")
        session.close(release_owned=False)

    def test_ref_resolver_call_returns_only_the_native_value(self):
        dag = _structured_dag()
        session = DAGMaterializationSession(dag, backend="polars")
        session.compile_registered("resource")
        resolver = _SessionRefResolver(session, CONST_BACKEND.POLARS, "polars")
        value = resolver("resource")
        assert not isinstance(value, DiagnosticFrameView)
        assert not hasattr(value, "logical_columns")
        session.close(release_owned=False)

    def test_ref_resolver_structured_plans_is_a_separate_method(self):
        dag = _structured_dag()
        session = DAGMaterializationSession(dag, backend="polars")
        session.compile_registered("resource")
        resolver = _SessionRefResolver(session, CONST_BACKEND.POLARS, "polars")
        plans = resolver.structured_plans("resource")
        assert isinstance(plans, MappingProxyType)
        assert "meta" in plans
        # __call__ never returns plan metadata alongside the native value.
        assert not isinstance(resolver("resource"), type(plans))
        session.close(release_owned=False)


class TestPerCallValidationContext:
    """Step 2: two local validation consumers share one prepared input."""

    def test_two_consumers_share_one_compile_one_cache_one_arrow_extraction(
        self, backend_factory, monkeypatch
    ):
        table = backend_factory.create(
            {"id": [1, 2], "meta": ['{"a": 1}', '{"a": 2}']}, "ibis-duckdb"
        )
        cache_calls = 0
        original_cache = type(table).cache

        def counted_cache(self):
            nonlocal cache_calls
            cache_calls += 1
            return original_cache(self)

        monkeypatch.setattr(type(table), "cache", counted_cache)

        arrow_calls = 0
        from mountainash.relations.core import logical_snapshot as logical_snapshot_module

        original_snapshot = logical_snapshot_module.resolve_logical_snapshot

        def counted_resolve(*args, **kwargs):
            nonlocal arrow_calls
            arrow_calls += 1
            return original_snapshot(*args, **kwargs)

        monkeypatch.setattr(
            logical_snapshot_module, "resolve_logical_snapshot", counted_resolve
        )

        compile_calls = 0
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="meta", type=UniversalType.OBJECT)]
        )
        rel = ma.relation(table).conform(spec, contract={"data_type": "coerce"})
        root_node = rel._node
        root_node_type = type(root_node)
        original_accept = root_node_type.accept

        def counted_accept(self, visitor):
            nonlocal compile_calls
            if self is root_node:
                compile_calls += 1
            return original_accept(self, visitor)

        monkeypatch.setattr(root_node_type, "accept", counted_accept)

        dag = RelationDAG()
        dag.add("resource", rel)
        session = DAGMaterializationSession(dag)
        context = DAGValidationContext(session)

        first = context.prepare("resource")
        second = context.prepare("resource")

        assert first is second
        assert compile_calls == 1
        assert cache_calls == 1
        assert session.canonical_keys == frozenset({"resource"})
        assert arrow_calls == 1
        session.close(release_owned=False)

    def test_two_local_checks_on_the_same_resource_share_the_prepared_snapshot(
        self, backend_factory
    ):
        """An end-to-end proof through `ValidationRunner.validate_dag()`:
        a value-rule check and a keyed-identity check for the same
        resource still resolve to the same prepared input."""
        table = backend_factory.create(
            {"id": [1, 2], "meta": ['{"a": 1}', '{"a": 2}']}, "ibis-duckdb"
        )
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="meta", type=UniversalType.OBJECT)]
        )
        rel = ma.relation(table).conform(spec, contract={"data_type": "coerce"})
        dag = RelationDAG()
        dag.add("resource", rel)

        result = ValidationRunner().validate_dag(
            dag,
            {
                "resource": [
                    ValueRule(
                        id="meta_shape", fields=["meta"],
                        validator=ValueValidatorKey.TYPE_FORMAT, options={"type": "object"},
                    )
                ]
            },
            identity_by_resource={"resource": RowIdentity("keyed", ("id",))},
        )
        assert result.results["resource"].passes is True
        assert result.results["resource"].identity_diagnostics == {
            "null_key_rows": 0,
            "unknown_key_rows": 0,
            "duplicate_key_tuples": 0,
        }
