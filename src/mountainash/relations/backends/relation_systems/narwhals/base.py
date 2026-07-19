"""Narwhals relation system — base class with backend type."""

from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.limitations import WILDCARD_PARAM
from mountainash.core.types import KnownLimitation
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


class NarwhalsBaseRelationSystem(BaseRelationSystem):
    """Base mixin that identifies this relation system as Narwhals."""

    BACKEND_NAME = "narwhals"

    KNOWN_REL_LIMITATIONS = {
        (RKEY_MOUNTAINASH_REL.UNNEST, WILDCARD_PARAM): KnownLimitation(
            message=(
                "unnest() is not supported by the Narwhals backend — "
                "narwhals has no struct-unnest operation."
            ),
            native_errors=(NotImplementedError,),
            workaround="Use the Polars backend for unnest.",
        ),
        (RKEY_MOUNTAINASH_REL.JOIN_ASOF, WILDCARD_PARAM): KnownLimitation(
            message=(
                "join_asof(tolerance=...) is not supported by the Narwhals "
                "backend; narwhals join_asof has no tolerance parameter."
            ),
            native_errors=(NotImplementedError,),
            workaround="Drop tolerance= or use the Polars backend.",
        ),
    }

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.NARWHALS
