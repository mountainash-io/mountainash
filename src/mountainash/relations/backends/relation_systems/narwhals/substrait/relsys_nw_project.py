"""Narwhals implementation of Substrait ProjectRel."""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitProjectRelationSystemProtocol,
)


class SubstraitNarwhalsProjectRelationSystem(
    SubstraitProjectRelationSystemProtocol[nw.DataFrame | nw.LazyFrame, nw.Expr]
):
    """Projection operations on Narwhals DataFrames."""

    def project_select(self, relation: Any, columns: list[Any], /) -> Any:
        if not columns or not all(isinstance(column, nw.Expr) for column in columns):
            return relation.select(columns)
        # Reuse Narwhals' compiled expression metadata, not source-schema probes.
        expressions = relation._flatten_and_extract(columns)
        scalar = [expression._metadata.is_scalar_like for expression in expressions]
        if expressions and all(scalar) and all(
            expression._metadata.is_elementwise for expression in expressions
        ):
            if relation.implementation.is_polars():
                from mountainash.relations.backends.relation_systems.polars.substrait.relsys_pl_project import _broadcast_scalar

                expressions = [
                    expression._with_native(_broadcast_scalar(expression.native))
                    for expression in expressions
                ]
                return relation._with_compliant(relation._compliant_frame.select(*expressions))
            names = [
                name for expression in expressions
                for name in expression._evaluate_aliases(None)
            ]
            result = relation._compliant_frame.with_columns(
                *(expression.broadcast() for expression in expressions)
            )
            return relation._with_compliant(result.simple_select(*names))
        # Preserve the native aggregate/mixed-expression dispatch without
        # compiling the same expressions a second time.
        if expressions and all(scalar):
            return relation._with_compliant(relation._compliant_frame.aggregate(*expressions))
        return relation._with_compliant(relation._compliant_frame.select(*(
            expression.broadcast() if is_scalar else expression
            for expression, is_scalar in zip(expressions, scalar)
        )))

    def project_with_columns(self, relation: Any, expressions: list[Any], /) -> Any:
        return relation.with_columns(expressions)

    def project_drop(self, relation: Any, columns: list[Any], /) -> Any:
        return relation.drop(columns)

    def project_rename(self, relation: Any, mapping: dict[str, str], /) -> Any:
        return relation.rename(mapping)
