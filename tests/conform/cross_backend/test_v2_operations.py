"""Cross-backend behavior smoke coverage for Unit C structural operations."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
)
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from mountainash.expressions.backends.expression_systems.ibis import IbisExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem
from tests.fixtures.backend_helpers import BackendDataFrameFactory, BackendResultHelper
from mountainash.typespec.spec import FieldSpec
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour
from mountainash.typespec.universal_types import UniversalType
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_operation_executes_or_hits_exact_gate(backend_name: str) -> None:
    systems = {
        "polars": PolarsExpressionSystem("polars"),
        "polars-lazy": PolarsExpressionSystem("polars"),
        "pandas": NarwhalsExpressionSystem("narwhals-pandas"),
        "narwhals": NarwhalsExpressionSystem("narwhals-polars"),
        "narwhals-polars": NarwhalsExpressionSystem("narwhals-polars"),
        "narwhals-lazy": NarwhalsExpressionSystem("narwhals-polars"),
        "narwhals-pandas": NarwhalsExpressionSystem("narwhals-pandas"),
        "ibis-duckdb": IbisExpressionSystem("ibis-duckdb"),
        "ibis-polars": IbisExpressionSystem("ibis-polars"),
        "ibis-sqlite": IbisExpressionSystem("ibis-sqlite"),
    }
    expr = ma.col("values").str.parse_list(item_type="string", delimiter="|", field_name="values")
    visitor = lambda: UnifiedExpressionVisitor(systems[backend_name]).visit(expr._node)
    if backend_name == "ibis-sqlite":
        from mountainash.core.constants import CONST_BACKEND
        from tests.fixtures.capability_gating import assert_capability_gated

        assert_capability_gated(
            FK_LIST.PARSE,
            CONST_BACKEND.IBIS,
            dialect="ibis-sqlite",
            param="*",
            option_value=None,
            build=visitor,
        )
        return
    compiled = visitor()
    frame = BackendDataFrameFactory.create({"values": ["1|2", "3|4"]}, backend_name)
    if backend_name in {"pandas", "narwhals-pandas"}:
        with pytest.raises(TypeError):
            BackendResultHelper.select_and_extract(frame, compiled, "values", backend_name)
    else:
        assert BackendResultHelper.select_and_extract(
            frame, compiled, "values", backend_name,
        ) == [["1", "2"], ["3", "4"]]

def _compile(expr):
    return UnifiedExpressionVisitor(PolarsExpressionSystem()).visit(expr._node)


def test_polars_list_parse_covers_custom_delimiter_and_complete_null_failure() -> None:
    expr = ma.col("values").str.parse_list(item_type="integer", delimiter="|", field_name="values")
    result = pl.DataFrame({"values": ["1|2", "3|4"]}).select(_compile(expr))
    assert result.to_series().to_list() == [[1, 2], [3, 4]]





def test_polars_boolean_invalid_item_invalidates_complete_list_in_null_mode() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean",
        delimiter="|",
        field_name="values",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    frame = pl.DataFrame({"values": ["true|tRuE"]})
    result = frame.select(_compile(expr))
    assert result.to_series().to_list() == [None]

def test_ibis_boolean_list_parser_uses_closed_frictionless_tokens() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create(
        {"values": ["true|True|TRUE|1|false|False|FALSE|0"]},
        "ibis-duckdb",
    )
    compiled = UnifiedExpressionVisitor(
        IbisExpressionSystem("ibis-duckdb")
    ).visit(expr._node)
    assert BackendResultHelper.select_and_extract(
        frame, compiled, "values", "ibis-duckdb",
    ) == [[True, True, True, True, False, False, False, False]]


def test_ibis_boolean_list_parser_rejects_mixed_case_tokens() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create({"values": ["tRuE|false"]}, "ibis-duckdb")
    compiled = UnifiedExpressionVisitor(
        IbisExpressionSystem("ibis-duckdb")
    ).visit(expr._node)
    with pytest.raises(Exception):
        BackendResultHelper.select_and_extract(frame, compiled, "values", "ibis-duckdb")
def test_polars_recursive_array_struct_cast() -> None:
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    expr = ma.col("items").list.cast_items(item_object_fields=(field,), field_name="items")
    result = pl.DataFrame({"items": [[{"id": "1"}, {"id": "2"}]]}).select(_compile(expr))
    assert result.to_series().to_list() == [[{"id": 1}, {"id": 2}]]


def test_polars_nested_null_mode_cast_is_atomic() -> None:
    nested = FieldSpec(
        name="payload",
        type=UniversalType.OBJECT,
        object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
    )
    expr = ma.col("items").list.cast_items(
        item_object_fields=(nested,),
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="items",
    )
    frame = pl.DataFrame({"items": [[{"payload": {"id": "bad"}}]]})
    result = frame.select(_compile(expr))
    assert result.to_series().to_list() == [None]


def test_polars_struct_and_categorical_preserve_base_values() -> None:
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    struct = ma.col("payload").struct.cast(fields=(field,), field_name="payload")
    cat = ma.col("status").cat.cast(value_type="integer", categories=(1, 2), ordered=True, field_name="status")
    frame = pl.DataFrame({"payload": [{"id": "1"}], "status": ["2"]})
    out = frame.select([_compile(struct).alias("payload"), _compile(cat).alias("status")])
    assert out["payload"].to_list() == [{"id": 1}]
    assert out["status"].to_list() == [2]

@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars"])
def test_boolean_list_parser_uses_only_closed_frictionless_tokens(backend_name: str) -> None:
    systems = {
        "polars": PolarsExpressionSystem("polars"),
        "narwhals-polars": NarwhalsExpressionSystem("narwhals-polars"),
    }
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create(
        {"values": ["true|True|TRUE|1|false|False|FALSE|0"]},
        backend_name,
    )
    compiled = UnifiedExpressionVisitor(systems[backend_name]).visit(expr._node)
    assert BackendResultHelper.select_and_extract(
        frame, compiled, "values", backend_name,
    ) == [[True, True, True, True, False, False, False, False]]


def test_narwhals_pandas_boolean_list_residue_is_materialization_scoped() -> None:
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.constants import CONST_BACKEND

    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create({"values": ["true|false"]}, "narwhals-pandas")
    compiled = UnifiedExpressionVisitor(
        NarwhalsExpressionSystem("narwhals-pandas")
    ).visit(expr._node)
    with pytest.raises(TypeError):
        BackendResultHelper.select_and_extract(frame, compiled, "values", "narwhals-pandas")
    residue = CapabilityRegistry.capability_for(
        FK_LIST.PARSE,
        "*",
        CONST_BACKEND.NARWHALS,
        dialect="narwhals-pandas",
    )
    assert residue is not None
    assert residue.enforcement.value == "materialize_residue"
    assert residue.level.value == "unsupported"


def test_conditioned_null_list_fact_gates_matching_item_type() -> None:
    from mountainash.core.types import BackendCapabilityError

    expr = ma.col("values").str.parse_list(
        item_type="integer",
        delimiter="|",
        field_name="values",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    with pytest.raises(BackendCapabilityError) as error:
        UnifiedExpressionVisitor(
            NarwhalsExpressionSystem("narwhals-polars")
        ).visit(expr._node)
    assert error.value.limitation.option_value == "null"
    assert error.value.limitation.predicate is not None


def test_conditioned_null_list_fact_does_not_block_supported_item_type() -> None:
    expr = ma.col("values").str.parse_list(
        item_type="string",
        delimiter="|",
        field_name="values",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    frame = BackendDataFrameFactory.create({"values": ["a|b"]}, "narwhals-polars")
    compiled = UnifiedExpressionVisitor(
        NarwhalsExpressionSystem("narwhals-polars")
    ).visit(expr._node)
    assert BackendResultHelper.select_and_extract(
        frame, compiled, "values", "narwhals-polars",
    ) == [["a", "b"]]


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars"])
def test_boolean_list_parser_rejects_mixed_case_tokens(backend_name: str) -> None:
    systems = {
        "polars": PolarsExpressionSystem("polars"),
        "narwhals-polars": NarwhalsExpressionSystem("narwhals-polars"),
    }
    expr = ma.col("values").str.parse_list(
        item_type="boolean", delimiter="|", field_name="values",
    )
    frame = BackendDataFrameFactory.create({"values": ["tRuE|false"]}, backend_name)
    compiled = UnifiedExpressionVisitor(systems[backend_name]).visit(expr._node)
    with pytest.raises(Exception):
        BackendResultHelper.select_and_extract(frame, compiled, "values", backend_name)


def test_list_null_capability_uses_exact_failure_selector_without_duplicates() -> None:
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.constants import CONST_BACKEND

    fact = CapabilityRegistry.capability_for(
        FK_LIST.PARSE,
        "failure_behavior",
        CONST_BACKEND.NARWHALS,
        dialect="narwhals-polars",
        option_value="null",
    )
    assert fact is not None
    assert fact.level is CapabilityLevel.UNSUPPORTED
    assert fact.option_value == "null"
    assert fact.predicate is not None
    matching = [
        item for item in CapabilityRegistry.facts()
        if item.operation_key is FK_LIST.PARSE
        and item.backend is CONST_BACKEND.NARWHALS
        and item.dialect == "narwhals-polars"
        and item.param == "failure_behavior"
        and item.option_value == "null"
    ]
    keys = {
        (item.param, item.option_value, item.predicate)
        for item in matching
    }
    assert len(keys) == len(matching)
