"""Non-owning SQL physical boundary for owned-copy materialization.

Mountainash admits idle connections; mountainash-data owns transaction state,
completion and protected physical operations. Callers use the yielded backend's
public methods, not direct Ibis calls, inside the transaction.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from mountainash.core.lazy_imports import import_mountainash_data
from mountainash.core.types import BackendCapabilityError

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


def _refusal(dialect: str, reason: str) -> BackendCapabilityError:
    return BackendCapabilityError(
        f"Owned-copy transaction unavailable: {reason}",
        backend=f"ibis-{dialect}", function_key="OWNED_COPY",
    )


def owned_adoption_refusal(dialect: str) -> str | None:
    """Why owned-copy adoption is refused on this Ibis connection, or ``None``.

    Unknown dialects are refused; known ones consult their ``IMPORT_INTO``
    GATE declaration.
    """
    from mountainash.core.capabilities.identity import KNOWN_DIALECTS
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from mountainash.core.capabilities.schema import PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

    identity = f"ibis-{dialect}"
    if identity not in KNOWN_DIALECTS[CONST_BACKEND.IBIS]:
        return "unsupported SQL dialect"
    fact = CapabilityRegistry.capability_for(
        RKEY_MOUNTAINASH_REL.IMPORT_INTO, "*", CONST_BACKEND.IBIS, identity,
        consumer=PolicyConsumer.GATE,
    )
    return fact.message if fact is not None else None


@contextmanager
def adopt_connection(connection: Any) -> Iterator[Any]:
    """Borrow an existing SQL connection for the duration of this scope.

    Upstream forbids close() while a public transaction is registered on the
    handle, even for a non-owner. In that case discard this resource-free wrapper
    without closing it; the caller retains connection and transaction ownership.
    The yielded wrapper must not be retained beyond this scope.
    """
    dialect = connection.name
    reason = owned_adoption_refusal(dialect)
    if reason is not None:
        raise _refusal(dialect, reason)
    backend = import_mountainash_data().IbisBackend.from_ibis_connection(
        connection, dialect=dialect, owns_connection=False,
    )
    try:
        yield backend
    except BaseException as original:
        try:
            if not backend.in_transaction():
                backend.close()
        except BaseException as cleanup:
            original.add_note(f"Non-owning wrapper release failed: {type(cleanup).__name__}")
        raise
    else:
        if not backend.in_transaction():
            backend.close()


def require_idle(backend: Any) -> None:
    """Refuse active or unobservable state without changing caller ownership."""
    try:
        state = backend.native_transaction_open()
    except Exception as exc:
        raise _refusal(backend.dialect, "native state observation failed") from exc
    if state is not False:
        raise _refusal(backend.dialect, f"native transaction state is {state!r}")


@contextmanager
def owned_transaction(backend: Any) -> Iterator[Any]:
    """Require idle state, then delegate the unit and its errors to upstream.

    Single-connection sequential use only. No retries or compensating rollback
    are attempted if transaction completion fails.
    """
    require_idle(backend)
    with backend.transaction(required=True):
        yield backend


def drop_owned_tables(connection: Any, names: Sequence[str]) -> bool:
    """Delete unique owned identifiers, acknowledging only committed cleanup.

    False means native state could not admit cleanup. Operation and completion
    errors propagate. The caller must retain pending names on False or error;
    force=True permits a later retry after an ambiguous transaction outcome.
    """
    if not names:
        return True
    with adopt_connection(connection) as backend:
        try:
            state = backend.native_transaction_open()
        except Exception:
            return False
        if state is not False:
            return False
        try:
            require_idle(backend)
        except BackendCapabilityError:
            return False
        # Admission failures defer; errors from the physical unit must not.
        with backend.transaction(required=True):
            for name in names:
                backend.drop_table(name, force=True)
    return True
