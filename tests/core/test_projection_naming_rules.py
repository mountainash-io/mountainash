"""Backend-independent authoring contracts for projection declarations."""

from dataclasses import replace

import pytest

from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)


def test_registered_operations_declare_projection_semantics():
    missing = [
        key
        for key in ExpressionFunctionRegistry.list_all()
        if getattr(ExpressionFunctionRegistry.get(key), "projection_rule", None) is None
    ]
    assert not missing, f"Missing projection semantics: {missing}"


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"name_kind": "guess"}, "Unknown projection rule kind"),
        ({"cardinality_kind": "guess"}, "Unknown projection rule kind"),
        ({"operand": -1}, "operand index"),
        ({"operand": True}, "operand index"),
        ({"operand": 1.5}, "operand index"),
        ({"name_kind": "fixed"}, "requires a value"),
        ({"name_kind": "option"}, "requires a value"),
        ({"name_kind": "requires_alias"}, "requires a reason"),
        ({"name_kind": "internal", "reason": ""}, "requires a reason"),
    ],
)
def test_projection_rule_rejects_invalid_declarations(kwargs, message):
    from mountainash.expressions.core.expression_system.function_mapping.output_rules import (
        ProjectionRule,
    )

    arguments = {"name_kind": "operand", "cardinality_kind": "propagate", **kwargs}
    with pytest.raises(ValueError, match=message):
        ProjectionRule(**arguments)


def test_function_definition_validates_optional_projection_rule():
    definition = ExpressionFunctionRegistry.get(ExpressionFunctionRegistry.list_all()[0])
    with pytest.raises(TypeError, match="projection_rule must be"):
        replace(definition, projection_rule="operand")
    # Custom/temporary definitions may still compile without projection metadata.
    assert replace(definition, projection_rule=None).projection_rule is None
