"""Polars MountainAsh string extension implementation.

Implements regex_contains natively using Polars' str.contains with literal=False.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsScalarStringExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of MountainAsh string extensions."""

    def regex_contains(
        self,
        input: PolarsExpr,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Regex containment via Polars str.contains(literal=False).

        Polars str.contains propagates null on null input, returning a
        true boolean (no extract/null-mismatch hack needed).
        """
        return input.str.contains(pattern, literal=False)

    def strip_suffix(self, x, /, *, suffix: str):
        return x.str.strip_suffix(suffix)

    def to_time(self, x, /, format: str):
        return x.str.to_time(format)

    def to_integer(self, x, /, base: int = 10):
        return x.str.to_integer(base=base)

    def json_decode(self, x, /, dtype=None):
        return x.str.json_decode(dtype)

    def json_path_match(self, x, /, json_path: str):
        return x.str.json_path_match(json_path)

    def encode(self, x, /, encoding: str):
        return x.str.encode(encoding)

    def decode(self, x, /, encoding: str, strict: bool = True):
        return x.str.decode(encoding, strict=strict)

    def extract_groups(self, x, /, pattern: str):
        return x.str.extract_groups(pattern)
