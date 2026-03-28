"""Substrait-aligned relation system protocols."""

from .prtcl_relsys_read import SubstraitReadRelationSystemProtocol
from .prtcl_relsys_project import SubstraitProjectRelationSystemProtocol
from .prtcl_relsys_filter import SubstraitFilterRelationSystemProtocol
from .prtcl_relsys_sort import SubstraitSortRelationSystemProtocol
from .prtcl_relsys_fetch import SubstraitFetchRelationSystemProtocol
from .prtcl_relsys_join import SubstraitJoinRelationSystemProtocol
from .prtcl_relsys_aggregate import SubstraitAggregateRelationSystemProtocol
from .prtcl_relsys_set import SubstraitSetRelationSystemProtocol

__all__ = [
    "SubstraitReadRelationSystemProtocol",
    "SubstraitProjectRelationSystemProtocol",
    "SubstraitFilterRelationSystemProtocol",
    "SubstraitSortRelationSystemProtocol",
    "SubstraitFetchRelationSystemProtocol",
    "SubstraitJoinRelationSystemProtocol",
    "SubstraitAggregateRelationSystemProtocol",
    "SubstraitSetRelationSystemProtocol",
]
