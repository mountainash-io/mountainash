"""Explicit eager ingestion into native Relation sources."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.errors import UnresolvedExecutionLocationError
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
    from mountainash.relations.core.materialization import coerce_to_polars
    from mountainash.relations.core.owned_copy import owned_arrow_table
    from mountainash.relations.core.relation_api.relation import relation

    location = LocationResolver(IdentityTokens()).resolve_target(target)
    if location is None or location.family is CONST_BACKEND.POLARS:
        return relation(coerce_to_polars(None, table))
    if location.family is CONST_BACKEND.IBIS and location.connection is None:
        raise UnresolvedExecutionLocationError("from_arrow needs target=<connection> for Ibis")
    if location.family is not CONST_BACKEND.IBIS:
        # Removed by the transfer-contract task, which routes every target
        # through prepared execution.
        raise NotImplementedError(f"from_arrow(target={target!r}) is not yet supported")
    copy = owned_arrow_table(table, location.connection)
    try:
        return relation(copy.value)
    except BaseException as original:
        try:
            copy.release()
        except BaseException as cleanup:
            original.add_note(f"Owned import cleanup also failed: {type(cleanup).__name__}")
        raise
