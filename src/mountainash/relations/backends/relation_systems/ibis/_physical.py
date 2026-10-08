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
    from collections.abc import Iterator


def _refusal(dialect: str, reason: str) -> BackendCapabilityError:
    return BackendCapabilityError(
        f"Owned-copy transaction unavailable: {reason}",
        backend=f"ibis-{dialect}", function_key="OWNED_COPY",
    )


@contextmanager
def adopt_connection(connection: Any) -> Iterator[Any]:
    """Borrow an existing SQL connection; release only our wrapper on exit."""
    dialect = connection.name
    if dialect not in {"sqlite", "duckdb", "postgres"}:
        raise _refusal(dialect, "unsupported SQL dialect")
    backend = import_mountainash_data().IbisBackend.from_ibis_connection(
        connection, dialect=dialect, owns_connection=False,
    )
    try:
        yield backend
    except BaseException as original:
        try:
            backend.close()
        except BaseException as cleanup:
            original.add_note(f"Non-owning wrapper release failed: {type(cleanup).__name__}")
        raise
    else:
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
