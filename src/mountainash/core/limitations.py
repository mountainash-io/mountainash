"""Shared limitation-enrichment machinery (spec relations-dispatch-parity §3.8).

Extracted from expressions' BaseExpressionSystem._call_with_expr_support so
both subsystems enrich known backend quirks identically. Lookup order per
failure: each named arg's ``(operation_key, param)`` entry, then the
``(operation_key, "*")`` wildcard (how handler-routed relation operations
and the materialization boundary participate). The *limitations* mapping
holds :class:`CapabilityFact` entries (the spine's MATERIALIZE residue).
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Any, Callable, Iterable, Mapping

from mountainash.core.types import BackendCapabilityError

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
    limitations: Mapping[tuple, Any],
    backend_name: str,
    operation_key: Any,
    named_args: Iterable[str],
) -> Any:
    """Call *fn*, enriching known-limitation failures into
    :class:`BackendCapabilityError`.

    Args:
        fn: Zero-arg callable invoking the native backend operation.
        limitations: A ``(operation_key, param) -> CapabilityFact`` table
            (the spine's MATERIALIZE residue).
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


def enrich_materialization(
    backend: Any,
    fn: Callable[[], Any],
    *,
    prefer_operation_keys: "frozenset | None" = None,
) -> Any:
    """Materialization-boundary enrichment: consult the spine's MATERIALIZE
    residue (matched by native exception type — residue facts keep their
    real operation keys).

    Args:
        backend: Relation/expression system carrying ``backend_type``
            (family) and ``dialect``.
        fn: Zero-arg callable invoking the native backend operation.
        prefer_operation_keys: When given (even empty), narrows candidates
            to residue facts whose operation key is in this set *before*
            matching by exception type — the caller's structural evidence
            for which operation(s) were actually being compiled. ``None``
            (the default) considers every residue fact for the backend,
            matching the legacy backend-wide behaviour. In both cases, a
            raised error is enriched only when **exactly one** candidate
            matches the exception's type; zero or multiple matches leave
            the original exception to propagate raw rather than guessing.
    """
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.types import BackendCapabilityError

    family = getattr(backend, "backend_type", None)
    residue = (
        CapabilityRegistry.residue_for(family, getattr(backend, "dialect", None))
        if family is not None
        else {}
    )
    if not residue:
        return fn()
    try:
        return fn()
    except BackendCapabilityError:
        raise  # already enriched — never re-wrap
    except Exception as exc:
        candidates = residue.items()
        if prefer_operation_keys is not None:
            candidates = [
                item for item in candidates
                if item[0][0] in prefer_operation_keys
            ]
        matches = [
            (op_key, fact) for (op_key, _param), fact in candidates
            if isinstance(exc, fact.native_errors)
        ]
        if len(matches) == 1:
            op_key, fact = matches[0]
            raise BackendCapabilityError(
                fact.message,
                backend=getattr(backend, "BACKEND_NAME", "unknown"),
                function_key=op_key,
                limitation=fact,
            ) from exc
        raise  # 0 or >=2 matches: never guess -- raw exception wins
