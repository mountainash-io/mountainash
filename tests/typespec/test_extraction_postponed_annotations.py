"""extract_from_dataclass resolves PEP 604 unions and postponed annotations.

Regression test for the gap filed in pointbreak's Phase 3a spec (P3A-D6 /
Codex 3a-8): under `from __future__ import annotations`, every dataclass
field's raw .type is a string; PEP 604 `X | Y` unions have no __origin__
the old Union-only unwrap could see. Both previously resolved to ANY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mountainash.typespec.extraction import extract_from_dataclass
from mountainash.typespec.universal_types import UniversalType


class Color(StrEnum):
    RED = "red"
    BLUE = "blue"


@dataclass
class Sample:
    name: str
    nickname: str | None
    count: int | None
    tags: list[str]
    metadata: dict[str, str] | None
    color: Color
    scores: list[int] = field(default_factory=list)


def test_pep604_optional_str_resolves_to_string_not_any():
    spec = extract_from_dataclass(Sample)
    f = spec.get_field("nickname")
    assert f is not None
    assert f.type == UniversalType.STRING
    assert f.constraints is None or f.constraints.required is False


def test_pep604_optional_int_resolves_to_integer_not_any():
    spec = extract_from_dataclass(Sample)
    f = spec.get_field("count")
    assert f.type == UniversalType.INTEGER


def test_bare_generic_list_resolves_to_array_not_any():
    spec = extract_from_dataclass(Sample)
    f = spec.get_field("tags")
    assert f.type == UniversalType.ARRAY


def test_pep604_optional_dict_does_not_resolve_to_any():
    spec = extract_from_dataclass(Sample)
    f = spec.get_field("metadata")
    assert f.type != UniversalType.ANY


def test_strenum_field_resolves_to_string_not_any():
    spec = extract_from_dataclass(Sample)
    f = spec.get_field("color")
    assert f.type == UniversalType.STRING


def test_default_factory_list_still_not_required():
    # Confirms the fix doesn't disturb the pre-existing (separately filed)
    # default_factory dead-code behaviour — still out of scope here.
    spec = extract_from_dataclass(Sample)
    f = spec.get_field("scores")
    assert f.constraints is None or f.constraints.required is False
