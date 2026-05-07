"""Ibis implementation of Substrait ReadRel."""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitReadRelationSystemProtocol,
)


class SubstraitIbisReadRelationSystem(SubstraitReadRelationSystemProtocol):
    """Read / scan a data source into an Ibis table expression.

    Ibis tables are already deferred, so this is essentially a pass-through
    with a type check.
    """

    def read(self, dataframe: Any, /) -> ir.Table:
        if isinstance(dataframe, ir.Table):
            return dataframe
        raise TypeError(
            f"Ibis backend cannot read {type(dataframe).__name__}. "
            f"Expected ibis.expr.types.Table."
        )
