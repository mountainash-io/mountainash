"""Polars implementation of Substrait ProjectRel."""

from __future__ import annotations

from typing import Any

import polars as pl


class SubstraitPolarsProjectRelationSystem:
    """Projection operations on Polars LazyFrames."""

    def project_select(self, relation: pl.LazyFrame, columns: list[Any], /) -> pl.LazyFrame:
        return relation.select(columns)

    def project_with_columns(
        self, relation: pl.LazyFrame, expressions: list[Any], /
    ) -> pl.LazyFrame:
        return relation.with_columns(expressions)

    def project_drop(self, relation: pl.LazyFrame, columns: list[Any], /) -> pl.LazyFrame:
        return relation.drop(columns)

    def project_rename(
        self, relation: pl.LazyFrame, mapping: dict[str, str], /
    ) -> pl.LazyFrame:
        return relation.rename(mapping)
