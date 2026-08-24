"""Cross-backend behavior smoke coverage for Unit C structural operations."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_MOUNTAINASH_SCALAR_CATEGORICAL as FK_CAT,
    FKEY_MOUNTAINASH_SCALAR_STRUCT as FK_STRUCT,
)
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_operation_ast_surface_is_reachable_for_every_backend(backend_name: str) -> None:
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    assert ma.col("values").str.parse_list(field_name="values")._node.arguments
    assert ma.col("items").list.cast_items(item_object_fields=(field,), field_name="items")._node.arguments
    assert ma.col("status").cat.cast(value_type="string", categories=("a",), ordered=False, field_name="status")._node.arguments
    assert ma.col("payload").struct.cast(fields=(field,), field_name="payload")._node.arguments

def _compile(expr):
    return UnifiedExpressionVisitor(PolarsExpressionSystem()).visit(expr._node)


def test_polars_list_parse_covers_custom_delimiter_and_complete_null_failure() -> None:
    expr = ma.col("values").str.parse_list(item_type="integer", delimiter="|", field_name="values")
    result = pl.DataFrame({"values": ["1|2", "3|4"]}).select(_compile(expr))
    assert result.to_series().to_list() == [[1, 2], [3, 4]]


def test_polars_recursive_array_struct_cast() -> None:
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    expr = ma.col("items").list.cast_items(item_object_fields=(field,), field_name="items")
    result = pl.DataFrame({"items": [[{"id": "1"}, {"id": "2"}]]}).select(_compile(expr))
    assert result.to_series().to_list() == [[{"id": 1}, {"id": 2}]]


def test_polars_struct_and_categorical_preserve_base_values() -> None:
    field = FieldSpec(name="id", type=UniversalType.INTEGER)
    struct = ma.col("payload").struct.cast(fields=(field,), field_name="payload")
    cat = ma.col("status").cat.cast(value_type="integer", categories=(1, 2), ordered=True, field_name="status")
    frame = pl.DataFrame({"payload": [{"id": "1"}], "status": ["2"]})
    out = frame.select([_compile(struct).alias("payload"), _compile(cat).alias("status")])
    assert out["payload"].to_list() == [{"id": 1}]
    assert out["status"].to_list() == [2]
