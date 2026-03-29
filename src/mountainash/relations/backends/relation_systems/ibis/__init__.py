"""Ibis relation system — composed from all substrait and extension mixins."""

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_protocols.relsys_base import register_relation_system

from .base import IbisBaseRelationSystem
from .substrait import (
    SubstraitIbisReadRelationSystem,
    SubstraitIbisProjectRelationSystem,
    SubstraitIbisFilterRelationSystem,
    SubstraitIbisSortRelationSystem,
    SubstraitIbisFetchRelationSystem,
    SubstraitIbisJoinRelationSystem,
    SubstraitIbisAggregateRelationSystem,
    SubstraitIbisSetRelationSystem,
)
from .extensions_mountainash import (
    MountainashIbisExtensionRelationSystem,
)


@register_relation_system(CONST_BACKEND.IBIS)
class IbisRelationSystem(
    IbisBaseRelationSystem,
    SubstraitIbisReadRelationSystem,
    SubstraitIbisProjectRelationSystem,
    SubstraitIbisFilterRelationSystem,
    SubstraitIbisSortRelationSystem,
    SubstraitIbisFetchRelationSystem,
    SubstraitIbisJoinRelationSystem,
    SubstraitIbisAggregateRelationSystem,
    SubstraitIbisSetRelationSystem,
    MountainashIbisExtensionRelationSystem,
):
    """Ibis relation system — all operations composed via multiple inheritance."""

    pass
