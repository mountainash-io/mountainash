"""Polars implementation of Substrait ProjectRel."""

from __future__ import annotations

from typing import Any

import polars as pl

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitProjectRelationSystemProtocol,
)


def _is_row_scalar(expression: pl.Expr) -> bool:
    """Recognize row-independent expressions by their native expression tree."""
    metadata = expression.meta
    children = metadata.pop()
    if metadata.has_multiple_outputs():
        return (
            not metadata.is_column_selection()
            and bool(children)
            and all(_is_row_scalar(child) for child in children)
        )
    if children:
        return all(_is_row_scalar(child) for child in children) and metadata.is_row_separable()
    return metadata.is_scalar() and metadata.is_row_separable()


def _broadcast_scalar(expression: pl.Expr) -> pl.Expr:
    """Preserve names and expanded outputs, including zero input rows."""
    return expression.repeat_by(pl.len()).explode(empty_as_null=False)


class SubstraitPolarsProjectRelationSystem(SubstraitProjectRelationSystemProtocol[pl.LazyFrame, pl.Expr]):
    """Projection operations on Polars LazyFrames."""

    def project_select(self, relation: pl.LazyFrame, columns: list[Any], /) -> pl.LazyFrame:
        if columns and all(
            isinstance(column, pl.Expr) and _is_row_scalar(column)
            for column in columns
        ):
            columns = [_broadcast_scalar(column) for column in columns]
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
