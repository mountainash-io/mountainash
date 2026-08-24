"""Closed audit for the lexical LIST/native ARRAY boundary."""
from __future__ import annotations

import ast
import json
from pathlib import Path


TESTS_ROOT = Path(__file__).parents[1]


def _is_array_expr(node: ast.AST | None) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "UniversalType"
        and node.attr == "ARRAY"
    )


def _lexical_array_constructor_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_field_spec = isinstance(func, ast.Name) and func.id == "FieldSpec"
        if not is_field_spec:
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
        if _is_array_expr(keywords.get("type")) and {
            "item_type",
            "delimiter",
        } & keywords.keys():
            violations.append(f"{path}:{node.lineno}")
    return violations


def _raw_descriptor_violations(value: object, location: str) -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        if value.get("type") == "array" and ({"itemType", "delimiter"} & value.keys()):
            violations.append(location)
        for key, child in value.items():
            violations.extend(_raw_descriptor_violations(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(_raw_descriptor_violations(child, f"{location}[{index}]"))
    return violations


def test_no_lexical_properties_on_native_array_declarations() -> None:
    """Every lexical declaration is LIST; ARRAY is reserved for native shape."""
    constructor_violations = [
        violation
        for path in TESTS_ROOT.rglob("*.py")
        if path.name != Path(__file__).name
        for violation in _lexical_array_constructor_violations(path)
    ]

    descriptor_violations: list[str] = []
    for path in TESTS_ROOT.rglob("*.json"):
        try:
            descriptor = json.loads(path.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        descriptor_violations.extend(_raw_descriptor_violations(descriptor, str(path)))

    assert not constructor_violations, "lexical properties on ARRAY FieldSpec: " + ", ".join(
        constructor_violations
    )
    assert not descriptor_violations, "lexical properties on raw ARRAY descriptor: " + ", ".join(
        descriptor_violations
    )
