from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from mountainash import relation
from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.conform.errors import ConformTransformError
from mountainash.conform.expressions import MaterializationResidueCheck
from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
    ResidueSignal,
)
from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import CapabilityResidueInvariantError
from mountainash.core.limitations import enrich_materialization
from mountainash.core.types import BackendCapabilityError
from mountainash.exceptions import CapabilityResidueInvariantError as PublicInvariantError
from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST,
)
from mountainash.typespec.spec import FieldDefinition, TableSchema
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
        )


def test_true_marker_with_fact_enriches_and_context() -> None:
    snapshot = CapabilityRegistry.snapshot()
    try:
        from mountainash.core.capabilities.declarations import (
            BoundSegment,
            CapabilityKey,
            CapabilityPolicyRule,
            CapabilitySegment,
            Domain,
        )
        from mountainash.core.capabilities.identity import Dialect, Scope
        from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer

        policy = CapabilityPolicyRule(
            CapabilityKey(KEY, "x"),
            CapabilityLevel.UNSUPPORTED,
            "null residue",
            PolicyConsumer.RESULT_PROTECTION,
            PolicyAction.DETECT_NON_NULL_TO_NULL,
            applicability=unbounded,
        )
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pandas.extensions_mountainash.list.trace_case",
                Scope(BACKEND, Dialect("narwhals-pandas")),
                CapabilitySegment(Domain.LIST, policies=(policy,)),
            )
        )
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
            enrich_materialization(Backend(), lambda: frame, diagnostic_trace=trace, residue_checks=checks)
        assert raised.value.context == {
            "field_name": "values",
            "logical_type": "list",
            "format": "default",
        }
    finally:
        CapabilityRegistry.restore(snapshot)


def test_null_markers_are_removed_when_false() -> None:
    frame = pd.DataFrame({"values": [1], "__ma_residue_0": [False], "__ma_residue_1": [False]})
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
    result = enrich_materialization(Backend(), lambda: frame, diagnostic_trace=trace, residue_checks=checks)
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
    spec = TableSchema(
        fields_match="open",
        fields={"duration": FieldDefinition(type=UniversalType.DURATION)},
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
    spec = TableSchema(
        fields_match="open",
        fields={"duration": FieldDefinition(type=UniversalType.DURATION)},
    )
    result = (
        relation(
            pd.DataFrame(
                {
                    "duration": ["P1D"],
                    "__ma_residue_conform_0_0": ["keep"],
                }
            )
        )
        .conform(spec)
        .collect()
    )
    assert list(result.columns) == ["duration", "__ma_residue_conform_0_0"]


def test_polars_throw_mode_temporal_failure_propagates_native_error() -> None:
    import polars as pl

    spec = TableSchema(
        fields_match="open",
        fields={"duration": FieldDefinition(type=UniversalType.DURATION)},
    )
    with pytest.raises(pl.exceptions.PolarsError) as raised:
        relation(pl.DataFrame({"duration": ["not-a-duration"]})).conform(spec).collect()
    assert not isinstance(raised.value, ConformTransformError)


def test_relation_lazy_terminal_removes_residue_markers() -> None:
    import polars as pl

    spec = TableSchema(
        fields_match="open",
        fields={"duration": FieldDefinition(type=UniversalType.DURATION)},
    )
    result = relation(pl.DataFrame({"duration": ["P1D"]}).lazy()).conform(spec).collect()
    assert result.columns == ["duration"]


def test_dag_collect_owns_residue_terminal_and_preserves_lazy_shape() -> None:
    import polars as pl

    from mountainash.relations.dag.dag import RelationDAG

    spec = TableSchema(
        fields_match="open",
        fields={"duration": FieldDefinition(type=UniversalType.DURATION)},
    )
    dag = RelationDAG()
    dag.add("durations", relation(pl.DataFrame({"duration": ["P1D"]})).conform(spec))
    result = dag.collect("durations")
    assert isinstance(result, pl.LazyFrame)
    assert result.collect().columns == ["duration"]


def _unrelated_replacement_query(lazy: bool, conform_first: bool, other: int):
    import polars as pl

    import mountainash as ma

    source = pl.DataFrame({"other": [other], "flag": ["true"]})
    source = source.lazy() if lazy else source
    schema = TableSchema(
        fields={
            "other": FieldDefinition(type=UniversalType.INTEGER),
            "flag": FieldDefinition(type=UniversalType.BOOLEAN),
        },
        missing_values=[],
    )
    replacement = ma.native(pl.col("other").replace_strict({0: 0})).name.alias("other")
    if conform_first:
        return ma.relation(source).conform(schema).with_columns(replacement)
    return ma.relation(source).with_columns(replacement).conform(schema)


@pytest.mark.parametrize("conform_first", [True, False], ids=["conform-first", "conform-last"])
@pytest.mark.parametrize("lazy", [False, True], ids=["eager", "lazy"])
def test_unrelated_native_error_is_not_a_conform_failure(lazy, conform_first) -> None:
    """Polars native-error attribution wiring; portable boundary suites remain."""
    import polars as pl

    query = _unrelated_replacement_query(lazy, conform_first, other=1)
    with pytest.raises(pl.exceptions.InvalidOperationError):
        query.to_polars()


@pytest.mark.parametrize("conform_first", [True, False], ids=["conform-first", "conform-last"])
@pytest.mark.parametrize("lazy", [False, True], ids=["eager", "lazy"])
def test_valid_replacement_beside_boolean_conversion_succeeds(lazy, conform_first) -> None:
    """Control: same queries succeed with a mapped value, including flag=True."""
    import polars as pl

    result = _unrelated_replacement_query(lazy, conform_first, other=0).to_polars()
    if isinstance(result, pl.LazyFrame):
        result = result.collect()
    assert result.to_dicts() == [{"other": 0, "flag": True}]


_ROUTES = [
    pytest.param("direct-select", True, id="select-cast-first"),
    pytest.param("direct-select", False, id="select-replacement-first"),
    pytest.param("direct-with_columns", True, id="with_columns-cast-first"),
    pytest.param("direct-with_columns", False, id="with_columns-replacement-first"),
    pytest.param("conform-first", True, id="conform-then-replacement"),
    pytest.param("conform-last", True, id="replacement-then-conform"),
]
_INPUTS = {
    "all-valid": (0, 1.5),
    "cast-only": (0, 1e100),
    "replacement-only": (1, 1.5),
    "both-failing": (1, 1e100),
}


def _attribution_query(route: str, cast_first: bool, lazy: bool, other: int, big: float):
    """One fp32 cast and one unrelated native replacement, via every route.

    Direct routes apply both operations to the source without conform. Conform
    routes let the schema perform the fp32 conversion and the Boolean flag
    conversion, with the replacement before or after the conform.
    """
    import polars as pl

    import mountainash as ma
    from mountainash.core.dtypes import MountainashDtype

    source = pl.DataFrame({"other": [other], "big": [big], "flag": ["true"]})
    source = source.lazy() if lazy else source
    replacement = ma.native(pl.col("other").replace_strict({0: 0})).name.alias("other")
    cast = ma.col("big").cast("fp32").name.alias("big")
    relation_ = ma.relation(source)
    if route.startswith("direct"):
        exprs = (cast, replacement) if cast_first else (replacement, cast)
        if route == "direct-select":
            return relation_.select(*exprs, ma.col("flag"))
        return relation_.with_columns(*exprs)
    schema = TableSchema(
        fields={
            "other": FieldDefinition(type=UniversalType.INTEGER),
            "big": FieldDefinition(type=UniversalType.NUMBER, dtype=MountainashDtype.FP32),
            "flag": FieldDefinition(type=UniversalType.BOOLEAN),
        },
        missing_values=[],
    )
    if route == "conform-first":
        return relation_.conform(schema).with_columns(replacement)
    return relation_.with_columns(replacement).conform(schema)


@pytest.mark.parametrize("lazy", [False, True], ids=["eager", "lazy"])
@pytest.mark.parametrize(("route", "cast_first"), _ROUTES)
@pytest.mark.parametrize("case", list(_INPUTS))
def test_native_failures_are_attributed_only_to_their_own_operation(
    case, route, cast_first, lazy
) -> None:
    """Valid, cast-only, replacement-only and both-failing inputs: native errors stay raw.

    Conform routes order the operations by placing the conform before or after
    the replacement; ``cast_first`` orders the direct routes.
    """
    import polars as pl

    other, big = _INPUTS[case]
    query = _attribution_query(route, cast_first, lazy, other, big)
    if case == "all-valid":
        result = query.to_polars()
        if isinstance(result, pl.LazyFrame):
            result = result.collect()
        flag = "true" if route.startswith("direct") else True
        assert result.to_dicts() == [{"other": 0, "big": 1.5, "flag": flag}]
        assert result.schema["big"] == pl.Float32
        assert result.schema["other"] == pl.Int64
        assert result.schema["flag"] == (pl.String if route.startswith("direct") else pl.Boolean)
        return
    with pytest.raises(pl.exceptions.PolarsError) as raised:
        query.to_polars()
    assert not isinstance(raised.value, ConformTransformError)
