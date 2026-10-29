"""Small public-path helpers for explicit option test cases."""
from __future__ import annotations

from typing import Any, Callable, NamedTuple

import mountainash as ma


def option_result(df: Any, expr: Any, backend: str) -> list[Any]:
    """Materialize an uncompiled expression through the public relation API."""
    return ma.relation(df).select(expr.name.alias("r")).to_dict()["r"]


def discrimination_probe(
    build_expr: Callable[[], Any],
    reference_expr: Callable[[], Any],
    df: Any,
    backend: str,
) -> bool:
    """Return whether two explicit option expressions produce different values."""
    return option_result(df, build_expr(), backend) != option_result(
        df, reference_expr(), backend
    )



class OptionSpec(NamedTuple):
    """A discriminating option-value probe case."""

    fkey: Any
    option_param: str
    option_value: str
    dtype: str
    build_expr: Callable[[], Any]
    reference_expr: Callable[[], Any]
    data: dict[str, list[Any]]
    schema: dict[str, Any] | None = None
    expected_discriminates: bool = True
    expected_native_exception: type[BaseException] | None = None


class OptionProbeDidNotDiscriminateError(AssertionError):
    """The raw native path accepted an option but did not honor its semantics."""


