"""Contracts for declarative expression operand metadata."""
from __future__ import annotations

from enum import Enum, auto

import pytest

from mountainash.core.dtypes.metadata import (
    FixedResultType,
    OperandType,
    PreserveResultType,
)
from mountainash.core.types import ExpressionT
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionDef,
)


class _FunctionKey(Enum):
    UNARY = auto()


def _unary(x: ExpressionT, /, *, label: str) -> ExpressionT:
    raise NotImplementedError


def _reserved_metadata_argument(__operand_types__: ExpressionT, /) -> ExpressionT:
    raise NotImplementedError




@pytest.mark.parametrize(
    ("logical_kind", "storage_kind", "nullable", "message"),
    [
        ("binary", "native", False, "logical_kind"),
        ("boolean", "arrow", False, "storage_kind"),
        ("boolean", "native", 1, "nullable"),
        ("unknown", "native", False, "unknown"),
    ],
)
def test_operand_type_rejects_ambiguous_or_invalid_descriptor(
    logical_kind: str,
    storage_kind: str,
    nullable: object,
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        OperandType(logical_kind, storage_kind, nullable)  # type: ignore[arg-type]




@pytest.mark.parametrize(
    "build_rule",
    [
        lambda: FixedResultType("binary", False),
        lambda: FixedResultType("boolean", "yes"),  # type: ignore[arg-type]
        lambda: PreserveResultType("x", require_kind="binary"),
    ],
)
def test_result_rules_reject_invalid_declared_domains(build_rule: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        build_rule()  # type: ignore[operator]


@pytest.mark.parametrize(
    "definition",
    [
        lambda: ExpressionFunctionDef(
            function_key=_FunctionKey.UNARY,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=_reserved_metadata_argument,
        ),
        lambda: ExpressionFunctionDef(
            function_key=_FunctionKey.UNARY,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=_unary,
            options=("__operand_types__",),
        ),
    ],
)
def test_function_def_reserves_operand_metadata_namespace(definition: object) -> None:
    with pytest.raises(ValueError, match="__operand_types__"):
        definition()  # type: ignore[operator]


def test_result_rule_references_must_be_expression_parameters() -> None:
    with pytest.raises(ValueError, match="expression parameter"):
        ExpressionFunctionDef(
            function_key=_FunctionKey.UNARY,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=_unary,
            result_type=PreserveResultType("label"),
            type_arguments=("label",),
        )




def test_fixed_rule_rejects_unknown_type_argument() -> None:
    with pytest.raises(ValueError, match="does not name"):
        ExpressionFunctionDef(
            function_key=_FunctionKey.UNARY,
            substrait_uri=None,
            substrait_name=None,
            protocol_method=_unary,
            result_type=FixedResultType("boolean", True),
            type_arguments=("missing",),
        )




