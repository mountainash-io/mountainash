"""Closed audit for the lexical LIST/native ARRAY boundary."""
from __future__ import annotations

import ast
import json
from pathlib import Path


TEST_ROOTS = (Path(__file__).parents[1], Path(__file__).parents[2] / "src")


def _is_array_expr(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "ARRAY"


def _is_field_spec_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Name)
        and node.func.id == "FieldSpec"
    ) or (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "FieldSpec"
    )


def _lexical_array_constructor_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_field_spec_call(node):
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
        if _is_array_expr(keywords.get("type")) and {
            "item_type",
            "delimiter",
        } & keywords.keys():
            violations.append(f"{path}:{node.lineno}")
    return violations


def _inline_raw_descriptor_violations(tree: ast.AST, path: Path) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        values = {
            key.value: value
            for key, value in zip(node.keys, node.values)
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
        if (
            isinstance(values.get("type"), ast.Constant)
            and values["type"].value == "array"
            and {"itemType", "delimiter"} & values.keys()
        ):
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
    constructor_violations: list[str] = []
    inline_descriptor_violations: list[str] = []
    descriptor_violations: list[str] = []
    for root in TEST_ROOTS:
        for path in root.rglob("*.py"):
            if path == Path(__file__):
                continue
            tree = ast.parse(path.read_text(), filename=str(path))
            constructor_violations.extend(_lexical_array_constructor_violations(path))
            inline_descriptor_violations.extend(
                _inline_raw_descriptor_violations(tree, path)
            )
        for path in root.rglob("*.json"):
            try:
                descriptor = json.loads(path.read_text())
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            descriptor_violations.extend(_raw_descriptor_violations(descriptor, str(path)))

    assert not constructor_violations, "lexical properties on ARRAY FieldSpec: " + ", ".join(
        constructor_violations
    )
    assert not inline_descriptor_violations, (
        "lexical properties on inline raw ARRAY descriptor: "
        + ", ".join(inline_descriptor_violations)
    )
    assert not descriptor_violations, "lexical properties on raw ARRAY descriptor: " + ", ".join(
        descriptor_violations
    )
