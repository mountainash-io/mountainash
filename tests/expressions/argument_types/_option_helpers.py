"""Helpers for testing literal option channels across native backends.

``option_result`` accepts an uncompiled Mountainash expression and uses the
public relation egress path. ``native_option_probe`` deliberately uses a raw
expression visitor with capability enforcement disabled, allowing strict
xfails to turn into XPASS when a native backend gains support.
"""
from __future__ import annotations

from typing import Any, Callable, NamedTuple

import pytest

import mountainash as ma
from expressions.argument_types.conftest import make_df
from mountainash.core.capabilities import (
    CapabilityLevel,
    CapabilityRegistry,
    load_all_capability_declarations,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.expsys_base import (
    get_expression_system,
)
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


load_all_capability_declarations()

_GATING = (CapabilityLevel.UNSUPPORTED, CapabilityLevel.LITERAL_ONLY)
_FIXTURE_FAMILY = {
    "polars": CONST_BACKEND.POLARS,
    "ibis": CONST_BACKEND.IBIS,
    "narwhals-polars": CONST_BACKEND.NARWHALS,
    "narwhals-pandas": CONST_BACKEND.NARWHALS,
}
_FIXTURE_DIALECT = {
    "polars": "polars",
    "ibis": None,
    "narwhals-polars": "narwhals-polars",
    "narwhals-pandas": "narwhals-pandas",
}


def option_result(df: Any, expr: Any, backend: str) -> list[Any]:
    """Materialize an uncompiled expression through the public relation API."""
    return ma.relation(df).select(expr.name.alias("r")).to_dict()["r"]


def discrimination_probe(
    build_expr: Callable[[], Any],
    reference_expr: Callable[[], Any],
    df: Any,
    backend: str,
) -> bool:
    """Return whether two uncompiled expressions produce different values."""
    return option_result(df, build_expr(), backend) != option_result(
        df, reference_expr(), backend
    )


def xfail_option_unsupported(
    fkey: Any,
    option_param: str,
    option_value: str,
    backend: str,
    dialect: str | None = None,
):
    """Return a strict xfail marker for a gating value-scoped capability fact."""
    resolved_dialect = dialect if dialect is not None else _FIXTURE_DIALECT[backend]
    fact = CapabilityRegistry.capability_for(
        fkey,
        option_param,
        _FIXTURE_FAMILY[backend],
        resolved_dialect,
        option_value=option_value,
    )
    if fact is not None and fact.level in _GATING:
        return pytest.mark.xfail(
            strict=True,
            raises=BackendCapabilityError,
            reason=f"[{option_param}={option_value}] {fact.message}",
        )
    return pytest.mark.usefixtures()


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


class OptionProbeDidNotDiscriminateError(AssertionError):
    """The raw native path accepted an option but did not honor its semantics."""


def _extract_values(df: Any, compiled: Any, backend: str) -> list[Any]:
    """Select a compiled native expression with null-preserving extraction."""
    alias = "__option_probe_result__"
    if backend == "polars":
        import polars as pl

        result = df.select(compiled.alias(alias))
        if isinstance(result, pl.LazyFrame):
            result = result.collect()
        return result[alias].to_list()
    if backend == "ibis":
        result = df.select(compiled.name(alias))
        return result.to_pyarrow()[alias].to_pylist()
    if backend in ("narwhals-polars", "narwhals-pandas"):
        result = df.select(compiled.alias(alias))
        return result.to_arrow()[alias].to_pylist()
    raise ValueError(f"Unknown backend: {backend}")


def _materialize_native_values(df: Any, expr: Any, backend: str) -> list[Any]:
    """Compile and extract through the raw native path with the gate disabled."""
    system_cls = get_expression_system(_FIXTURE_FAMILY[backend])
    system = system_cls(dialect=_FIXTURE_DIALECT[backend])
    visitor = UnifiedExpressionVisitor(system, enforce_capabilities=False)
    compiled = visitor.visit(expr._node)
    return _extract_values(df, compiled, backend)


def native_option_probe(spec: OptionSpec, backend: str) -> None:
    """Assert an option expression discriminates on the ungated native path."""
    df = make_df(spec.data, backend, schema=spec.schema)
    got = _materialize_native_values(df, spec.build_expr(), backend)
    reference = _materialize_native_values(df, spec.reference_expr(), backend)
    if (got != reference) is not spec.expected_discriminates:
        raise OptionProbeDidNotDiscriminateError(
            f"{spec.fkey!r} {spec.option_param}={spec.option_value!r} did not "
            f"produce expected_discriminates={spec.expected_discriminates}"
        )
