"""Explicit eager ingestion into native Relation sources."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    import pyarrow as pa

    from mountainash.relations.core.relation_api.relation import Relation


def from_arrow(table: pa.Table, *, target: Any = None) -> Relation:
    """Import an Arrow table now and return a normal, composable Relation.

    ``target`` uses the shared execution-target vocabulary. With no target,
    use in-process Polars. A supplied Ibis connection receives one owned
    temporary table, without Polars ingress. The caller retains connection
    ownership and must keep it open; SQL import requires an idle connection
    and uses existing owner-thread cleanup. Derived native plans retain the
    imported table until their final release.

    Preserve logical types and values, including typed empty tables. Native
    datetime conversions and Polars large-string/list representations apply.
    Polars may share Arrow buffers; use snapshot() for an independent copy.
    """
    from mountainash.relations.core.errors import UnresolvedExecutionLocationError
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
    from mountainash.relations.core.relation_api.relation import relation

    location = LocationResolver(IdentityTokens()).resolve_target("polars" if target is None else target)
    if location.family is CONST_BACKEND.IBIS and location.connection is None:
        raise UnresolvedExecutionLocationError("from_arrow needs target=<connection> for Ibis")
    # The import is the relation's own prepared transfer: preparation decides
    # whether it anchors an owned table; the transport session owns its lifetime.
    native, visitor = relation(table)._compile_and_execute_with_visitor(
        target=target if target is not None else "polars", retain_execution_scope=True,
    )
    try:
        result = relation(native)
    except BaseException:
        visitor._execution_session.close(release_owned=True)
        raise
    visitor._execution_session.close(release_owned=False)
    return result
