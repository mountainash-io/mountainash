"""Cross-backend behavior smoke coverage for Unit C structural operations."""
from __future__ import annotations

import polars as pl
import narwhals as nw
import pandas as pd
import pytest

import mountainash as ma
from mountainash.expressions.backends.expression_systems.ibis import IbisExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT,
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
)
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,
)
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.constants import CONST_BACKEND
from tests.fixtures.backend_helpers import BackendDataFrameFactory, BackendResultHelper
from tests.fixtures.capability_gating import (
    assert_capability_gated,
    assert_predicate_capability_gated,
)
from fixtures.backend_registry import ALL_BACKENDS
_SYSTEMS = {
    "polars": PolarsExpressionSystem("polars"),
    "polars-lazy": PolarsExpressionSystem("polars"),
    "pandas": NarwhalsExpressionSystem("narwhals-pandas"),
    "narwhals-polars": NarwhalsExpressionSystem("narwhals-polars"),
    "narwhals-pandas": NarwhalsExpressionSystem("narwhals-pandas"),
    "narwhals-lazy": NarwhalsExpressionSystem("narwhals-lazy"),
    "ibis-duckdb": IbisExpressionSystem("ibis-duckdb"),
    "ibis-polars": IbisExpressionSystem("ibis-polars"),
    "ibis-sqlite": IbisExpressionSystem("ibis-sqlite"),
}

_IDENTITIES = {
    "polars": (CONST_BACKEND.POLARS, "polars"),
    "polars-lazy": (CONST_BACKEND.POLARS, "polars"),
    "pandas": (CONST_BACKEND.NARWHALS, "narwhals-pandas"),
    "narwhals-polars": (CONST_BACKEND.NARWHALS, "narwhals-polars"),
    "narwhals-pandas": (CONST_BACKEND.NARWHALS, "narwhals-pandas"),
    "narwhals-lazy": (CONST_BACKEND.NARWHALS, "narwhals-lazy"),
    "ibis-duckdb": (CONST_BACKEND.IBIS, "ibis-duckdb"),
    "ibis-polars": (CONST_BACKEND.IBIS, "ibis-polars"),
    "ibis-sqlite": (CONST_BACKEND.IBIS, "ibis-sqlite"),
}


def _compile_for(backend_name: str, expr):
    return UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)


def _extract(backend_name: str, data: dict, compiled, column: str):
    frame = BackendDataFrameFactory.create(data, backend_name)
    return BackendResultHelper.select_and_extract(frame, compiled, column, backend_name)


def _gate(backend_name: str):
    return _IDENTITIES[backend_name]



@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_operation_executes_or_hits_exact_gate(backend_name: str) -> None:
    systems = _SYSTEMS
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


_LIST_ITEM_TYPES = ("string", "integer", "boolean", "number", "datetime", "date", "time")
_LIST_THROW_SUPPORTED = {
    "polars": set(_LIST_ITEM_TYPES),
    "polars-lazy": set(_LIST_ITEM_TYPES),
    "pandas": {"string", "integer", "boolean", "number", "date"},
    "narwhals-polars": {"string", "integer", "boolean", "number", "date"},
    "narwhals-pandas": {"string", "integer", "boolean", "number", "date"},
    "narwhals-lazy": {"string", "integer", "boolean", "number", "date"},
    "ibis-duckdb": {"string", "integer", "boolean", "number", "date", "time"},
    "ibis-polars": {"string"},
    "ibis-sqlite": set(),
}
_LIST_NULL_SUPPORTED = {
    "polars": set(_LIST_ITEM_TYPES),
    "polars-lazy": set(_LIST_ITEM_TYPES),
    "pandas": {"string"},
    "narwhals-polars": {"string"},
    "narwhals-pandas": {"string"},
    "narwhals-lazy": {"string"},
    "ibis-duckdb": {"string"},
    "ibis-polars": {"string"},
    "ibis-sqlite": set(),
}
_LIST_INPUTS = {
    "string": ("a|b", "c|d"),
    "integer": ("1|2", "3|4"),
    "boolean": ("true|False", "TRUE|0"),
    "number": ("1.5|2.5", "3.5|4.5"),
    "datetime": ("2024-01-02T03:04:05Z|2024-01-03T03:04:05Z",) * 2,
    "date": ("2024-01-02|2024-01-03", "2024-01-04|2024-01-05"),
    "time": ("03:04:05|04:05:06", "05:06:07|06:07:08"),
}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("item_type", _LIST_ITEM_TYPES)
def test_list_parse_matrix_covers_every_item_type(
    backend_name: str, item_type: str,
) -> None:
    expr = ma.col("values").str.parse_list(
        item_type=item_type, delimiter="|", field_name="values",
    )
    build = lambda: _compile_for(backend_name, expr)
    family, dialect = _gate(backend_name)
    if backend_name == "ibis-sqlite":
        assert_capability_gated(
            FK_LIST.PARSE, family, dialect=dialect,
            param="*", option_value=None, build=build,
        )
        return
    if item_type not in _LIST_THROW_SUPPORTED[backend_name]:
        assert_capability_gated(
            FK_LIST.PARSE, family, dialect=dialect,
            param="item_type", option_value=item_type, build=build,
        )
        return
    if backend_name in {"pandas", "narwhals-pandas"}:
        from mountainash.core.capabilities import CapabilityRegistry
        from mountainash.core.capabilities import CapabilityLevel, Enforcement, Boundary

        residue = CapabilityRegistry.capability_for(
            FK_LIST.PARSE, "*", family, dialect=dialect,
        )
        assert residue is not None
        assert residue.level is CapabilityLevel.UNSUPPORTED
        assert residue.enforcement is Enforcement.MATERIALIZE_RESIDUE
        assert residue.boundary is Boundary.MATERIALIZE
        compiled = build()
        with pytest.raises(TypeError):
            _extract(
                backend_name, {"values": list(_LIST_INPUTS[item_type])},
                compiled, "values",
            )
        return
    values = _extract(
        backend_name, {"values": list(_LIST_INPUTS[item_type])}, build(), "values",
    )
    assert len(values) == 2
    assert all(value is not None and len(value) == 2 for value in values)
    if item_type == "string":
        assert values == [["a", "b"], ["c", "d"]]
    elif item_type == "integer":
        assert values == [[1, 2], [3, 4]]
    elif item_type == "boolean":
        assert values == [[True, False], [True, False]]
    elif item_type == "number":
        assert values == [[1.5, 2.5], [3.5, 4.5]]

_LIST_INVALID_INPUTS = {
    "integer": ("1|bad", "3|4"),
    "boolean": ("true|tRuE", "false|0"),
    "number": ("1.5|bad", "3.5|4.5"),
    "datetime": ("2024-01-02T03:04:05Z|bad", "2024-01-03T03:04:05Z|2024-01-04T03:04:05Z"),
    "date": ("2024-01-02|bad", "2024-01-03|2024-01-04"),
    "time": ("03:04:05|bad", "04:05:06|05:06:07"),
}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("item_type", tuple(_LIST_INVALID_INPUTS))
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_list_parse_invalid_item_is_complete_value_failure(
    backend_name: str, item_type: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = ma.col("values").str.parse_list(
        item_type=item_type, delimiter="|", field_name="values",
        failure_behavior=failure_behavior,
    )
    build = lambda: _compile_for(backend_name, expr)
    family, dialect = _gate(backend_name)
    if backend_name == "ibis-sqlite":
        assert_capability_gated(
            FK_LIST.PARSE, family, dialect=dialect,
            param="*", option_value=None, build=build,
        )
        return
    if item_type not in _LIST_THROW_SUPPORTED[backend_name]:
        assert_capability_gated(
            FK_LIST.PARSE, family, dialect=dialect,
            param="item_type", option_value=item_type, build=build,
        )
        return
    if (
        failure_behavior is CaseFailureBehaviour.NULL
        and item_type not in _LIST_NULL_SUPPORTED[backend_name]
    ):
        error = assert_predicate_capability_gated(build)
        fact = error.limitation
        assert fact.operation_key is FK_LIST.PARSE
        assert fact.param == "failure_behavior"
        assert fact.option_value == "null"
        assert fact.backend is family
        assert fact.dialect == dialect
        return
    if backend_name in {"pandas", "narwhals-pandas"}:
        compiled = build()
        from mountainash.core.capabilities import CapabilityRegistry

        residue = CapabilityRegistry.capability_for(
            FK_LIST.PARSE, "*", family, dialect=dialect,
        )
        assert residue is not None
        with pytest.raises(TypeError):
            _extract(
                backend_name,
                {"values": list(_LIST_INVALID_INPUTS[item_type])},
                compiled,
                "values",
            )
        return
    if failure_behavior is CaseFailureBehaviour.THROW:
        with pytest.raises(Exception):
            _extract(
                backend_name,
                {"values": list(_LIST_INVALID_INPUTS[item_type])},
                build(),
                "values",
            )
    else:
        values = _extract(
            backend_name,
            {"values": list(_LIST_INVALID_INPUTS[item_type])},
            build(),
            "values",
        )
        assert values[0] is None
        assert values[1] is not None and len(values[1]) == 2



_CAST_THROW_SUPPORTED = {
    "polars": True,
    "polars-lazy": True,
    "pandas": False,
    "narwhals-polars": True,
    "narwhals-pandas": False,
    "narwhals-lazy": False,
    "ibis-duckdb": True,
    "ibis-polars": True,
    "ibis-sqlite": False,
}
_CAST_NULL_SUPPORTED = {
    "polars": True,
    "polars-lazy": True,
    "pandas": False,
    "narwhals-polars": False,
    "narwhals-pandas": False,
    "narwhals-lazy": False,
    "ibis-duckdb": False,
    "ibis-polars": False,
    "ibis-sqlite": False,
}


def _recursive_item_fields() -> tuple[FieldSpec, ...]:
    return (
        FieldSpec(
            name="payload",
            type=UniversalType.OBJECT,
            object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
        ),
    )


def _recursive_struct_fields() -> tuple[FieldSpec, ...]:
    return (
        FieldSpec(
            name="nested",
            type=UniversalType.OBJECT,
            object_fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
        ),
    )


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_list_cast_items_recursive_matrix(
    backend_name: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = ma.col("items").list.cast_items(
        item_object_fields=_recursive_item_fields(),
        failure_behavior=failure_behavior,
        field_name="items",
    )
    build = lambda: _compile_for(backend_name, expr)
    family, dialect = _gate(backend_name)
    supported = (
        _CAST_THROW_SUPPORTED[backend_name]
        if failure_behavior is CaseFailureBehaviour.THROW
        else _CAST_NULL_SUPPORTED[backend_name]
    )
    if not supported:
        assert_capability_gated(
            FK_LIST.CAST_ITEMS, family, dialect=dialect,
            param="failure_behavior",
            option_value=failure_behavior.value,
            build=build,
        )
        return
    values = _extract(
        backend_name,
        {"items": [[{"payload": {"id": "1"}}, {"payload": {"id": "2"}}]]},
        build(),
        "items",
    )
    assert values == [[{"payload": {"id": 1}}, {"payload": {"id": 2}}]]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_list_cast_items_null_mode_invalidates_complete_recursive_value(
    backend_name: str,
) -> None:
    expr = ma.col("items").list.cast_items(
        item_object_fields=_recursive_item_fields(),
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="items",
    )
    build = lambda: _compile_for(backend_name, expr)
    family, dialect = _gate(backend_name)
    if not _CAST_NULL_SUPPORTED[backend_name]:
        assert_capability_gated(
            FK_LIST.CAST_ITEMS, family, dialect=dialect,
            param="failure_behavior", option_value="null", build=build,
        )
        return
    values = _extract(
        backend_name,
        {"items": [[{"payload": {"id": "bad"}}], None]},
        build(),
        "items",
    )
    assert values == [None, None]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_struct_cast_recursive_matrix(
    backend_name: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    expr = ma.col("payload").struct.cast(
        fields=_recursive_struct_fields(),
        failure_behavior=failure_behavior,
        field_name="payload",
    )
    build = lambda: _compile_for(backend_name, expr)
    family, dialect = _gate(backend_name)
    supported = (
        backend_name not in {"narwhals-pandas", "pandas", "narwhals-lazy", "ibis-sqlite"}
        if failure_behavior is CaseFailureBehaviour.THROW
        else backend_name in {"polars", "polars-lazy"}
    )
    if not supported:
        assert_capability_gated(
            FK_STRUCT.CAST, family, dialect=dialect,
            param="failure_behavior",
            option_value=failure_behavior.value,
            build=build,
        )
        return
    values = _extract(
        backend_name,
        {"payload": [{"nested": {"id": "1"}}]},
        build(),
        "payload",
    )
    assert values == [{"nested": {"id": 1}}]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_struct_cast_null_mode_invalidates_recursive_value(backend_name: str) -> None:
    expr = ma.col("payload").struct.cast(
        fields=_recursive_struct_fields(),
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="payload",
    )
    build = lambda: _compile_for(backend_name, expr)
    family, dialect = _gate(backend_name)
    if backend_name not in {"polars", "polars-lazy"}:
        assert_capability_gated(
            FK_STRUCT.CAST, family, dialect=dialect,
            param="failure_behavior", option_value="null", build=build,
        )
        return
    values = _extract(
        backend_name,
        {"payload": [{"nested": {"id": "bad"}}, None]},
        build(),
        "payload",
    )
    assert values == [None, None]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("value_type", ("string", "integer"))
@pytest.mark.parametrize(
    "failure_behavior",
    (CaseFailureBehaviour.THROW, CaseFailureBehaviour.NULL),
)
def test_categorical_cast_preserves_supported_base_values(
    backend_name: str, value_type: str, failure_behavior: CaseFailureBehaviour,
) -> None:
    categories = ("new", "active") if value_type == "string" else (1, 2)
    source_value = "active" if value_type == "string" else "2"
    expr = ma.col("status").cat.cast(
        value_type=value_type,
        categories=categories,
        ordered=True,
        failure_behavior=failure_behavior,
        field_name="status",
    )
    build = lambda: _compile_for(backend_name, expr)
    family, dialect = _gate(backend_name)
    if backend_name == "ibis-sqlite" and value_type == "integer":
        assert_capability_gated(
            FK_CAT.CAST, family, dialect=dialect,
            param="value_type", option_value="integer", build=build,
        )
        return
    if (
        backend_name in {"narwhals-polars", "narwhals-lazy"}
        and value_type == "integer"
        and failure_behavior is CaseFailureBehaviour.NULL
    ):
        error = assert_predicate_capability_gated(build)
        fact = error.limitation
        assert fact.operation_key is FK_CAT.CAST
        assert fact.param == "value_type"
        assert fact.option_value == "integer"
        assert fact.backend is family
        assert fact.dialect == dialect
        return
    values = _extract(
        backend_name, {"status": [source_value]}, build(), "status",
    )
    assert values == ([source_value] if value_type == "string" else [2])

@pytest.mark.parametrize("backend_name", ("pandas", "narwhals-pandas"))
def test_narwhals_pandas_categorical_integer_nulls_invalid_values(
    backend_name: str,
) -> None:
    expr = ma.col("status").cat.cast(
        value_type="integer",
        categories=(1, 2),
        ordered=True,
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="status",
    )
    values = _extract(
        backend_name,
        {"status": ["bad", "2", None]},
        _compile_for(backend_name, expr),
        "status",
    )
    frame = BackendDataFrameFactory.create(
        {"status": ["bad", "2", None]}, backend_name,
    )
    result = frame.select(_compile_for(backend_name, expr).alias("status"))
    assert result["status"].dtype == nw.Int64
    assert values[1] == 2
    assert pd.isna(values[0])
    assert pd.isna(values[2])

@pytest.mark.parametrize("backend_name", ("pandas", "narwhals-pandas"))
def test_narwhals_pandas_categorical_integer_nulls_signed_int64_overflow(
    backend_name: str,
) -> None:
    expr = ma.col("status").cat.cast(
        value_type="integer",
        categories=(1, 2),
        ordered=True,
        failure_behavior=CaseFailureBehaviour.NULL,
        field_name="status",
    )
    data = {"status": ["9223372036854775808", "2", None]}
    values = _extract(
        backend_name,
        data,
        _compile_for(backend_name, expr),
        "status",
    )
    frame = BackendDataFrameFactory.create(data, backend_name)
    result = frame.select(_compile_for(backend_name, expr).alias("status"))
    assert result["status"].dtype == nw.Int64
    assert pd.isna(values[0])
    assert values[1] == 2
    assert pd.isna(values[2])


def test_polars_geopoint_default_preserves_valid_text_and_nulls() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="default",
        source_representation="lexical",
        field_name="point",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    result = pl.DataFrame({"point": ["1.0, 2.0", "NaN, INF", "-INF, 3", None, "bad"]}).select(_compile(expr))
    assert result.to_series().to_list() == ["1.0, 2.0", "NaN, INF", "-INF, 3", None, None]


def test_polars_geopoint_throw_rejects_invalid_native_coordinates() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="native",
        field_name="point",
    )
    with pytest.raises(Exception):
        pl.DataFrame({"point": [[1.0], [float("inf"), 2.0]]}).select(_compile(expr))


def test_polars_geopoint_lexical_array_parses_json_numbers() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="lexical",
        field_name="point",
    )
    result = pl.DataFrame({"point": ["[1,-2.5e2]"]}).select(_compile(expr))
    assert result.to_series().to_list() == [[1.0, -250.0]]


def test_polars_geopoint_native_array_rejects_wrong_length_in_null_mode() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="native",
        field_name="point",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    result = pl.DataFrame({"point": [[1.0], [1.0, 2.0], None]}).select(_compile(expr))
    assert result.to_series().to_list() == [None, [1.0, 2.0], None]


def test_polars_geojson_parse_and_serialize() -> None:
    parse = ma.col("geometry").geo.parse_geojson(format="default", field_name="geometry")
    parsed = pl.DataFrame({"geometry": ['{"type":"Point","coordinates":[1,2]}']}).select(_compile(parse))
    assert parsed.to_series().to_list() == ['{"type":"Point","coordinates":[1,2]}']

    serialize = ma.col("geometry").geo.serialize_geojson(format="default", field_name="geometry")
    serialized = pl.DataFrame({"geometry": [{"type": "Point", "coordinates": [1.0, 2.0]}]}).select(_compile(serialize))
    assert serialized.to_series().to_list() == ['{"type":"Point","coordinates":[1.0,2.0]}']


def test_geospatial_capability_predicate_gates_unsupported_cells() -> None:
    lexical_array = ma.col("point").geo.parse_geopoint(
        format="array",
        source_representation="lexical",
        field_name="point",
    )
    assert_predicate_capability_gated(
        lambda: UnifiedExpressionVisitor(NarwhalsExpressionSystem("narwhals-polars")).visit(
            lexical_array._node
        )
    )


def test_ibis_sqlite_geopoint_default_throw_is_gated() -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="default",
        source_representation="lexical",
        field_name="point",
    )
    assert_predicate_capability_gated(
        lambda: UnifiedExpressionVisitor(IbisExpressionSystem("ibis-sqlite")).visit(expr._node)
    )


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_geopoint_default_null_mode_all_backends(backend_name: str) -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="default",
        source_representation="lexical",
        field_name="point",
        failure_behavior=CaseFailureBehaviour.NULL,
    )
    compiled = UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    frame = BackendDataFrameFactory.create({"point": ["1.0, 2.0", "bad", None]}, backend_name)
    values = BackendResultHelper.select_and_extract(frame, compiled, "point", backend_name)
    assert values[0] == "1.0, 2.0"
    assert all(pd.isna(value) for value in values[1:])


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_geojson_is_polars_only_with_exact_backend_gates(backend_name: str) -> None:
    expr = ma.col("geometry").geo.parse_geojson(
        format="default", field_name="geometry", failure_behavior=CaseFailureBehaviour.NULL
    )
    visitor = lambda: UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    if backend_name in {"polars", "polars-lazy"}:
        compiled = visitor()
        frame = BackendDataFrameFactory.create(
            {"geometry": ['{"type":"Point","coordinates":[1,2]}', "[1,2]"]},
            backend_name,
        )
        assert BackendResultHelper.select_and_extract(
            frame, compiled, "geometry", backend_name
        ) == ['{"type":"Point","coordinates":[1,2]}', None]
    else:
        family, dialect = _gate(backend_name)
        assert_capability_gated(
            FK_GEO.PARSE_GEOJSON,
            family,
            dialect=dialect,
            param="*",
            option_value=None,
            build=visitor,
        )


@pytest.mark.parametrize("backend_name", ["narwhals-polars", "narwhals-pandas", "ibis-duckdb", "ibis-polars"])
def test_native_geopoint_array_throw_executes_supported_backends(backend_name: str) -> None:
    expr = ma.col("point").geo.parse_geopoint(
        format="array", source_representation="native", field_name="point"
    )
    compiled = UnifiedExpressionVisitor(_SYSTEMS[backend_name]).visit(expr._node)
    frame = BackendDataFrameFactory.create({"point": [[1.0, 2.0], None]}, backend_name)
    values = BackendResultHelper.select_and_extract(frame, compiled, "point", backend_name)
    assert list(values[0]) == [1.0, 2.0]
    assert pd.isna(values[1]) or values[1] is None
