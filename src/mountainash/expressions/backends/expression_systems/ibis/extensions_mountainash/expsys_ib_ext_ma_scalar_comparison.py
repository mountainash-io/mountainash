"""Ibis MountainAsh comparison extension implementation.

Implements is_duplicated for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarComparisonExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


class MountainAshIbisScalarComparisonExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarComparisonExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of MountainAsh comparison extensions."""


    def is_duplicated(self, x: IbisValueExpr, /) -> IbisValueExpr:
        """Whether the value appears more than once in the column.

        Ibis has no native is_duplicated; a per-partition row count > 1 over
        a window grouped by ``x`` is the portable idiom. NULLs are treated
        as equal to each other (consistent with Polars/Narwhals
        ``is_duplicated``): repeated NULLs are duplicates of one another.

        This requires counting all rows in the partition, not just non-null
        ``x`` values — SQL's ``COUNT(x)`` excludes NULLs, which would make
        the null partition always count as 0 regardless of how many NULL
        rows it contains. ``x.notnull()`` is itself a boolean expression
        that is *never* null (every row is either True or False), so
        ``.count()`` on it counts every row in the partition, giving the
        correct size for the NULL group while leaving non-null partitions
        (which never contain nulls to begin with) unaffected.
        """
        import ibis

        return x.notnull().count().over(ibis.window(group_by=x)) > 1
