"""Scope-bound operand metadata regressions for type-sensitive expressions."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes.metadata import OperandType
from mountainash.core.types import BackendCapabilityError
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


def _visitor() -> UnifiedExpressionVisitor:
    return UnifiedExpressionVisitor(PolarsExpressionSystem(dialect="polars"))


def test_input_scope_resolves_field_metadata_without_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Schema resolution must not execute a projection just to identify a field."""
    frame = pl.DataFrame({"amount": [1, 2]})
    visitor = _visitor()

    def fail_select(*args: object, **kwargs: object) -> object:
        raise AssertionError("type resolution must not select data")

    monkeypatch.setattr(frame, "select", fail_select)
    with visitor.input_scope(frame):
        assert visitor.resolve_operand_type(ma.col("amount").node) == OperandType(
            "integer", "native", None
        )


def test_polars_computed_metadata_uses_lazy_schema_without_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reliable computed result infers from lazy schema, never frame evaluation."""
    frame = pl.DataFrame({"amount": [1, 2]})
    visitor = _visitor()
    expression = ma.col("amount") + 1

    monkeypatch.setattr(
        frame,
        "select",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("computed type resolution must not select data")
        ),
    )
    with visitor.input_scope(frame):
        assert visitor.resolve_operand_type(expression.node) == OperandType(
            "integer", "native", None
        )


def test_input_scope_restores_metadata_after_an_exception() -> None:
    """A failed scoped compilation cannot leak its frame metadata to the next call."""
    visitor = _visitor()
    with pytest.raises(RuntimeError):
        with visitor.input_scope(pl.DataFrame({"x": [1]})):
            assert visitor.resolve_operand_type(ma.col("x").node).logical_kind == "integer"
            raise RuntimeError("intentional failure")

    with pytest.raises(BackendCapabilityError, match="metadata"):
        visitor.resolve_operand_type(ma.col("x").node)


def test_declared_and_preserved_result_types_compose_without_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fixed parser output and naming preservation require metadata, not evaluation."""
    frame = pl.DataFrame({"text": ["true", "false"]})
    visitor = _visitor()
    expression = ma.col("text").parse_boolean(
        true_values=("true",), false_values=("false",), field_name="text"
    ).name.alias("parsed")

    monkeypatch.setattr(
        frame,
        "select",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("type resolution must not select data")
        ),
    )
    with visitor.input_scope(frame):
        assert visitor.resolve_operand_type(expression.node) == OperandType(
            "boolean", "native", True
        )

def test_fixed_value_result_composes_without_selecting_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fixed result descriptor feeds another type-sensitive operation lazily."""
    frame = pl.DataFrame({"value": [1, 2]})
    visitor = _visitor()
    expression = ma.col("value").value_kind().text_value()

    monkeypatch.setattr(
        frame,
        "select",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("type resolution must not select data")
        ),
    )
    with visitor.input_scope(frame):
        assert visitor.resolve_operand_type(expression.node) == OperandType(
            "text", "native", True
        )



@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_fixed_value_result_compiles_in_every_backend_scope(
    backend_name: str, backend_factory: object
) -> None:
    """A nested consumer receives the fixed text output in every backend."""
    frame = backend_factory.create({"value": [1, 2]}, backend_name)
    result = ma.relation(frame).select(
        ma.col("value").value_kind().text_value().name.alias("kind")
    ).to_dict()
    assert result == {"kind": ["integer", "integer"]}


def test_null_branches_do_not_make_homogeneous_result_ambiguous() -> None:
    """If/then and coalesce retain a concrete kind when another branch is null-only."""
    frame = pl.DataFrame({"flag": [True], "text": ["value"]})
    visitor = _visitor()
    conditional = ma.when(ma.col("flag")).then(ma.col("text")).otherwise(ma.lit(None))
    coalesced = ma.coalesce(conditional, ma.lit(None))

    with visitor.input_scope(frame):
        assert visitor.resolve_operand_type(conditional.node) == OperandType(
            "text", "native", True
        )
        assert visitor.resolve_operand_type(coalesced.node) == OperandType(
            "text", "native", True
        )
