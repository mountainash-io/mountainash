"""Verify option channel: accepts raw Python values, rejects expressions at API builder level."""
from __future__ import annotations

import pytest

import mountainash as ma
from cross_backend.argument_types._introspection import introspect_protocols

# Build a list of (op_name, param_name, annotation) for every option-kind param
_OPTION_PARAMS = [
    (p.op_name, p.param_name, p.annotation)
    for p in introspect_protocols()
    if p.kind == "option"
]


def _example_raw_value(annotation: str):
    """Pick a representative raw value based on the parameter's type annotation."""
    if "int" in annotation:
        return 2
    if "str" in annotation:
        return "x"
    if "bool" in annotation:
        return True
    if "float" in annotation:
        return 1.5
    if "FrozenSet" in annotation or "frozenset" in annotation:
        return frozenset()
    if "Collection" in annotation or "Sequence" in annotation or "Iterable" in annotation or "List" in annotation or "list" in annotation:
        return []
    if "dtype" in annotation.lower() or "object" in annotation or "Any" in annotation:
        return object()
    return None


@pytest.mark.parametrize("op_name,param_name,annotation", _OPTION_PARAMS)
def test_option_has_example_value(op_name: str, param_name: str, annotation: str):
    """Smoke check: every option parameter has a derivable example value."""
    raw = _example_raw_value(annotation)
    assert raw is not None, f"No example value for {op_name}({param_name}: {annotation})"


def test_option_rejects_expression_on_round_decimals():
    """round() decimals is an option — passing an expression should fail at the API builder level."""
    with pytest.raises((TypeError, ValueError, AttributeError)):
        ma.col("x").round(ma.col("n"))  # type: ignore[arg-type]


def test_option_rejects_expression_on_alias():
    """name.alias takes a str option — passing an expression should fail."""
    with pytest.raises((TypeError, ValueError, AttributeError)):
        ma.col("x").name.alias(ma.col("y"))  # type: ignore[arg-type]
