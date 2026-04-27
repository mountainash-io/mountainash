"""Narwhals backend for mountainash extension window operations."""

from __future__ import annotations

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem


class MountainAshNarwhalsWindowExpressionSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of mountainash window extensions."""

    def diff(self, x, /, *, n: int = 1):
        """Consecutive difference: value[i] - value[i-n]."""
        if n != 1:
            raise NotImplementedError(
                "Narwhals diff() only supports n=1. "
                "Use Polars or Ibis backend for n > 1."
            )
        return x.diff()
