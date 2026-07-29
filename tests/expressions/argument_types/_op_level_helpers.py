"""Materialize a scalar op through the raw visitor with the gate disabled, so a
strict-xfail self-healing probe can compare native output to the ASCII oracle."""
from __future__ import annotations
from typing import Any, Callable

from expressions.argument_types.conftest import make_df
from expressions.argument_types._option_helpers import _extract_values, _FIXTURE_FAMILY, _FIXTURE_DIALECT
from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


def op_level_result(build_expr: Callable[[], Any], data: dict, backend: str) -> list:
    df = make_df(data, backend)
    system = get_expression_system(_FIXTURE_FAMILY[backend])(dialect=_FIXTURE_DIALECT[backend])
    visitor = UnifiedExpressionVisitor(system, enforce_capabilities=False)
    return _extract_values(df, visitor.visit(build_expr()._node), backend)
