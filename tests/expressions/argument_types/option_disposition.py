"""Test-owned option cases and their local coverage labels.

These declarations describe only the concrete option tests in this directory.
They neither query capability information nor select execution expectations.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from expressions.argument_types._option_helpers import OptionSpec


INVALID_OPTION_VALUE = "INVALID"
FactKey = tuple[Any, str, str, Any, str | None]


class OptionCell(NamedTuple):
    fkey: Any
    protocol: str
    op: str
    param: str
    fixture: str
    value: str
    dtype: str
    disposition: str
    reason: str = ""
    backing_mode: str = "absence"


class OptionProbeRegistration(NamedTuple):
    """A concrete native witness retained with its owning option case."""

    spec: OptionSpec
    fixture: str
    disposition: str
    expected_native_failure: type[BaseException] | tuple[type[BaseException], ...] | None = None


class InvalidOptionRejection(NamedTuple):
    """A concrete invalid option case asserted at API-build time."""

    fkey: Any
    protocol: str
    op: str
    param: str
    value: str
    dtype: str
    build_expr: Callable[[], Any]


OPTION_DISPOSITIONS: list[OptionCell] = []
REGISTERED_OPTION_PROBES: list[OptionProbeRegistration] = []
REGISTERED_INVALID_OPTION_REJECTIONS: list[InvalidOptionRejection] = []
OPTION_FAMILY_DEFAULT_FACT_KEYS: set[FactKey] = set()


def param_taxonomy(protocol: str, op: str, param: str) -> str:
    """Summarize local option cases for the independent coverage guard."""
    cases = [
        cell
        for cell in OPTION_DISPOSITIONS
        if (cell.protocol, cell.op, cell.param) == (protocol, op, param)
    ]
    if not cases:
        return "no-op"
    legal = [cell for cell in cases if cell.disposition != "invalid"]
    if not legal:
        return "validation-only"
    if all(cell.disposition == "probe_exempt" for cell in legal):
        return "probe-exempt-honor"
    if any(
        cell.disposition in {"honored", "probe_exempt"}
        and cell.reason == "intended-error-path"
        for cell in legal
    ):
        return "error-sensitive"
    if any(cell.disposition in {"honored", "probe_exempt"} for cell in legal):
        return "value-sensitive"
    return "capability-declared"
