"""Retired-fact catalog (spec rev 3, §4).

Retirement is a MOVE, not a deletion: when a backend release fixes a
declared limitation, the CapabilityFact leaves its declaration module and a
RetiredFact is appended here. Like ``divergences.py``, this catalog is
core-owned audit data — never registered into the registry, never gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from mountainash.core.capabilities.schema import (
    CapabilityLevel,
    ValueClass,
    _validate_since,
)

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND


@dataclass(frozen=True)
class RetiredFact:
    operation_key: Any
    param: str
    backend: "CONST_BACKEND"
    dialect: str | None
    option_value: str | None
    value_class: ValueClass | None   # mirrors CapabilityFact; value-class
                                     # retirements are NOT squeezed into
                                     # option_value (disjoint keyspaces)
    level: CapabilityLevel
    since: str                       # original declaration date
    retired_on: str
    fixed_in_versions: tuple[tuple[str, str], ...]  # (("narwhals","2.19.0"),)
    upstream_ref: str | None
    note: str

    def __post_init__(self) -> None:
        owner = f"RetiredFact({self.operation_key}, {self.param})"
        _validate_since(self.since, owner)
        _validate_since(self.retired_on, f"{owner}.retired_on")
        if self.retired_on < self.since:
            raise ValueError(
                f"{owner}: retired_on ({self.retired_on}) precedes since "
                f"({self.since}) — a fact cannot be retired before it was declared "
                "(both are zero-padded YYYY-MM-DD, so the compare is chronological)"
            )
        if self.option_value is not None and self.value_class is not None:
            raise ValueError(f"{owner}: option_value and value_class are exclusive")


RETIRED_FACTS: tuple[RetiredFact, ...] = ()


def assert_no_active_retired_overlap(registry: Any) -> None:
    """Guard: no fact key is simultaneously active and retired.

    Checks BOTH active keyspaces (spec §4): option-value facts against
    ``_facts`` and value-class facts against ``_value_class_facts``.
    """
    active_option = set(registry._facts)
    active_vclass = {
        (f.operation_key, f.param, f.backend, f.dialect, f.value_class)
        for bucket in registry._value_class_facts.values()
        for f in (bucket if isinstance(bucket, tuple) else (bucket,))
    }
    for r in RETIRED_FACTS:
        if r.value_class is not None:
            key_vclass = (r.operation_key, r.param, r.backend, r.dialect, r.value_class)
            assert key_vclass not in active_vclass, (
                f"{key_vclass} is simultaneously active and retired"
            )
        else:
            key_option = (r.operation_key, r.param, r.backend, r.dialect, r.option_value)
            assert key_option not in active_option, (
                f"{key_option} is simultaneously active and retired"
            )
