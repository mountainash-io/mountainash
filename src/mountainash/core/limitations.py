"""Shared limitation-enrichment machinery (spec relations-dispatch-parity §3.8).

Extracted from expressions' BaseExpressionSystem._call_with_expr_support so
both subsystems enrich known backend quirks identically. Lookup order per
failure: each named arg's ``(operation_key, param)`` entry, then the
``(operation_key, "*")`` wildcard (how handler-routed relation operations
and the materialization boundary participate).
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Any, Callable, Iterable, Mapping

from mountainash.core.types import BackendCapabilityError, KnownLimitation

WILDCARD_PARAM = "*"


class _Boundary(Enum):
    """Sentinel operation keys for non-operation enrichment sites."""

    MATERIALIZE = auto()


#: Key for limitations that only surface when a lazy plan materializes
#: (Relation.collect / to_polars). Register entries as
#: ``(MATERIALIZE_BOUNDARY, "*")``.
MATERIALIZE_BOUNDARY = _Boundary.MATERIALIZE


def call_with_limitation_enrichment(
    fn: Callable[[], Any],
    *,
    limitations: Mapping[tuple, "KnownLimitation"],
    backend_name: str,
    operation_key: Any,
    named_args: Iterable[str],
) -> Any:
    """Call *fn*, enriching known-limitation failures into
    :class:`BackendCapabilityError`.

    Args:
        fn: Zero-arg callable invoking the native backend operation.
        limitations: The backend's ``(operation_key, param) -> KnownLimitation``
            table (``KNOWN_EXPR_LIMITATIONS`` / ``KNOWN_REL_LIMITATIONS``).
        backend_name: Backend identifier for the raised error.
        operation_key: FKEY/RKEY enum member (or a boundary sentinel).
        named_args: Parameter names that may identify the failing entry;
            the ``"*"`` wildcard is always consulted last.
    """
    try:
        return fn()
    except BackendCapabilityError:
        raise  # already enriched (e.g. by a nested visit) — never re-wrap
    except Exception as exc:
        for param_name in (*named_args, WILDCARD_PARAM):
            limitation = limitations.get((operation_key, param_name))
            if limitation and isinstance(exc, limitation.native_errors):
                raise BackendCapabilityError(
                    limitation.message,
                    backend=backend_name,
                    function_key=operation_key,
                    limitation=limitation,
                ) from exc
        raise
