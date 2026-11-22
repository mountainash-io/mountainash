"""The base and http-extra requirements on mountainash-transport must pin the same range."""

from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement

PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _transport(requirements: list[str], extras: set[str]) -> Requirement:
    matches = [
        r
        for r in map(Requirement, requirements)
        if r.name == "mountainash-transport" and r.extras == extras
    ]
    assert len(matches) == 1, matches
    return matches[0]


def test_transport_http_extra_has_same_specifier_as_base_requirement() -> None:
    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    base = _transport(project["dependencies"], set())
    http = _transport(project["optional-dependencies"]["http"], {"http"})
    assert str(base.specifier)
    assert base.specifier == http.specifier
