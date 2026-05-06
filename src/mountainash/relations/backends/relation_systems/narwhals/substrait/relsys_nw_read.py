"""Narwhals implementation of Substrait ReadRel."""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitReadRelationSystemProtocol,
)


class SubstraitNarwhalsReadRelationSystem(SubstraitReadRelationSystemProtocol):
    """Read / scan a data source into a Narwhals DataFrame."""

    def read(self, dataframe: Any, /) -> Any:
        # If already a Narwhals DataFrame, return as-is.
        if hasattr(dataframe, "_compliant_frame"):
            return dataframe
        return nw.from_native(dataframe, eager_only=True)
