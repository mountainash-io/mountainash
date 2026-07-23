"""Guard packaged option domains against a deliberately pinned Substrait file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


PIN_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "substrait"


def _option_items(options: object) -> list[tuple[str, object]]:
    """Normalize current mapping and historical list option encodings."""
    if isinstance(options, dict):
        return list(options.items())
    if isinstance(options, list):
        return [(option["name"], option) for option in options]
    raise TypeError(f"unsupported Substrait options encoding: {type(options).__name__}")


def _option_values(option: object) -> list[object]:
    if isinstance(option, dict):
        return option.get("values", [])
    if isinstance(option, list):
        return option
    raise TypeError(f"unsupported Substrait option encoding: {type(option).__name__}")


def _domains(data: dict[str, Any]) -> dict[tuple[str, str], frozenset[str]]:
    out: dict[tuple[str, str], frozenset[str]] = {}
    for group in data.get("scalar_functions", []):
        op_name = group["name"]
        for impl in group.get("impls", []):
            for option_name, option in _option_items(impl.get("options", {})):
                key = (op_name, option_name)
                values = frozenset(str(value) for value in _option_values(option))
                out[key] = out.get(key, frozenset()) | values
    return out


def _fixture_domains(filename: str, topic: str) -> dict[tuple[str, str], frozenset[str]]:
    commit = (PIN_ROOT / f"PIN_{topic}.txt").read_text().strip()
    data = yaml.safe_load((PIN_ROOT / commit / filename).read_text())
    return _domains(data)


def test_arithmetic_domains_match_pin_exactly() -> None:
    from mountainash.expressions.core.expression_api.api_builders.substrait._option_domains import (
        OPTION_DOMAINS,
    )

    fixture = _fixture_domains("functions_arithmetic.yaml", "arithmetic")
    packaged = {key: values for key, values in OPTION_DOMAINS.items() if key in fixture}
    assert packaged == fixture, (
        "packaged domains diverge from pin: "
        f"{set(packaged.items()) ^ set(fixture.items())}"
    )


def test_fixture_parser_accepts_historical_list_encoding() -> None:
    data = {
        "scalar_functions": [
            {
                "name": "add",
                "impls": [
                    {
                        "options": [
                            {"name": "overflow", "values": ["SILENT", "ERROR"]}
                        ]
                    }
                ],
            }
        ]
    }

    assert _domains(data) == {
        ("add", "overflow"): frozenset({"SILENT", "ERROR"})
    }


def test_validate_option_returns_string_for_legal_known_domain() -> None:
    from mountainash.expressions.core.expression_api.api_builders.substrait._option_domains import (
        validate_option,
    )

    assert validate_option("add", "overflow", "ERROR") == "ERROR"


def test_validate_option_rejects_invalid_known_domain_value() -> None:
    from mountainash.core.errors import InvalidOptionValueError
    from mountainash.expressions.core.expression_api.api_builders.substrait._option_domains import (
        validate_option,
    )

    with pytest.raises(
        InvalidOptionValueError,
        match=r"invalid overflow='WRAP' for add; legal: \['ERROR', 'SATURATE', 'SILENT'\]",
    ):
        validate_option("add", "overflow", "WRAP")


@pytest.mark.parametrize(
    ("op_name", "option_name"),
    [("custom_op", "overflow"), ("add", "custom_option")],
)
def test_validate_option_passes_through_unknown_domains(
    op_name: str, option_name: str
) -> None:
    from mountainash.expressions.core.expression_api.api_builders.substrait._option_domains import (
        validate_option,
    )

    assert validate_option(op_name, option_name, 7) == "7"


def test_invalid_option_value_error_hierarchy_and_facade() -> None:
    from mountainash.core.errors import InvalidOptionValueError, MountainashError
    from mountainash.exceptions import InvalidOptionValueError as FacadeError

    assert issubclass(InvalidOptionValueError, MountainashError)
    assert issubclass(InvalidOptionValueError, ValueError)
    assert FacadeError is InvalidOptionValueError
