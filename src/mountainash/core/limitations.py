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


def _routing_matches(fact: Any, fingerprint: Mapping[str, str]) -> bool:
    if fact.option_value is not None:
        return fingerprint.get(fact.param) == str(fact.option_value)
    if fact.predicate is None:
        return True
    from mountainash.core.capabilities.predicates import predicate_holds

    bindings = dict(fingerprint)
    return predicate_holds(fact.predicate, bindings, frozenset(bindings))


def _diagnostic_matches(
    diagnostic: Any,
    facts: Iterable[Any],
    *,
    signal: Any,
    error: BaseException | None = None,
) -> list[tuple[Any, Any]]:
    from mountainash.core.capabilities.schema import ResidueSignal

    matches: list[tuple[Any, Any]] = []
    family = diagnostic.backend_family
    for fact in facts:
        fact_family = getattr(fact.backend, "value", fact.backend)
        if fact_family != family:
            continue
        if fact.dialect is not None and fact.dialect != diagnostic.dialect:
            continue
        if fact.operation_key != diagnostic.function_key:
            continue
        if fact.residue_signal is not signal:
            continue
        if not _routing_matches(fact, dict(diagnostic.routing_fingerprint)):
            continue
        if signal is ResidueSignal.EXCEPTION and (
            error is None or not isinstance(error, fact.native_errors)
        ):
            continue
        if diagnostic.failure_behavior not in (None, "throw"):
            continue
        matches.append((diagnostic, fact))
    if not matches:
        return []
    winning_rank = max(_fact_specificity(fact) for _, fact in matches)
    return [match for match in matches if _fact_specificity(match[1]) == winning_rank]


def _fact_specificity(fact: Any) -> tuple[int, int, int]:
    return (
        int(fact.dialect is not None),
        int(fact.param != "*"),
        len(fact.predicate.clauses) if fact.predicate is not None else int(fact.option_value is not None),
    )


def _is_true_marker(result: Any, marker: str) -> bool:
    try:
        values = result[marker]
    except (KeyError, IndexError, TypeError):
        return False
    if hasattr(values, "any"):
        return bool(values.any())
    return any(bool(value) for value in values)


def _drop_markers(result: Any, markers: Iterable[str]) -> Any:
    names = tuple(dict.fromkeys(markers))
    if not names:
        return result
    if hasattr(result, "drop"):
        try:
            return result.drop(*names)
        except (TypeError, KeyError):
            return result.drop(columns=list(names))
    return result


def enrich_materialization(
    backend: Any,
    fn: Callable[[], Any],
    *,
    prefer_operation_keys: "frozenset | None" = None,
    dialect: "str | None" = None,
    diagnostic_trace: Any = None,
    residue_checks: Iterable[Any] = (),
) -> Any:
    """Enrich deterministic capability residue at a materialization boundary."""
    from mountainash.conform.errors import ConformError
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.schema import ResidueSignal
    from mountainash.core.errors import CapabilityResidueInvariantError
    from mountainash.core.types import BackendCapabilityError

    family = getattr(backend, "backend_type", None)
    active_dialect = dialect if dialect is not None else getattr(backend, "dialect", None)
    checks = tuple(residue_checks)
    if family is None:
        return fn()

    if diagnostic_trace is None and not checks:
        residue = CapabilityRegistry.residue_for(family, active_dialect)
        if not residue:
            return fn()
        try:
            return fn()
        except BackendCapabilityError:
            raise
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
            raise

    diagnostics = tuple(getattr(diagnostic_trace, "records", ()))
    facts = CapabilityRegistry.residue_candidates(family, active_dialect)
    try:
        result = fn()
    except BackendCapabilityError:
        raise
    except ConformError:
        raise
    except Exception as exc:
        matched: list[tuple[Any, Any]] = []
        for diagnostic in diagnostics:
            if prefer_operation_keys is not None and diagnostic.function_key not in prefer_operation_keys:
                continue
            matched.extend(
                _diagnostic_matches(
                    diagnostic,
                    facts,
                    signal=ResidueSignal.EXCEPTION,
                    error=exc,
                )
            )
        if not matched:
            raise
        fact_keys = tuple(sorted({fact.fact_key for _, fact in matched}))
        fields = tuple(sorted({diagnostic.field_name for diagnostic, _ in matched}))
        if len(fact_keys) == 1:
            winning_fact = next(fact for _, fact in matched if fact.fact_key == fact_keys[0])
            candidate_diagnostics = tuple(
                diagnostic for diagnostic, fact in matched if fact.fact_key == fact_keys[0]
            )
            context = None
            if len(candidate_diagnostics) == 1:
                candidate = candidate_diagnostics[0]
                context = {
                    "field_name": candidate.field_name,
                    "logical_type": candidate.logical_type,
                    "format": candidate.format,
                }
            message = winning_fact.message
            function_key = winning_fact.operation_key
            limitation = winning_fact
        else:
            message = "multiple conform operations failed during materialization"
            function_key = None
            limitation = None
            context = None
        raise BackendCapabilityError(
            message,
            backend=getattr(backend, "BACKEND_NAME", "unknown"),
            function_key=function_key,
            limitation=limitation,
            context=context,
            candidate_fields=fields,
            candidate_fact_keys=fact_keys,
        ) from exc

    true_checks = tuple(check for check in checks if _is_true_marker(result, check.marker))
    for check in true_checks:
        matching = []
        for diagnostic in diagnostics:
            if diagnostic.function_key != check.function_key:
                continue
            if diagnostic.field_name != check.field_name:
                continue
            matching.extend(
                _diagnostic_matches(
                    diagnostic,
                    facts,
                    signal=ResidueSignal.NON_NULL_TO_NULL,
                )
            )
        if not matching:
            raise CapabilityResidueInvariantError(
                f"materialization residue marker has no declared fact for field {check.field_name!r}"
            )
        fact_keys = tuple(sorted({fact.fact_key for _, fact in matching}))
        fields = tuple(sorted({diagnostic.field_name for diagnostic, _ in matching}))
        if len(fact_keys) == 1:
            fact = matching[0][1]
            message = fact.message
            function_key = fact.operation_key
            limitation = fact
            context = None
            diagnostics_for_fact = tuple(
                diagnostic
                for diagnostic, candidate_fact in matching
                if candidate_fact.fact_key == fact.fact_key
            )
            if len(diagnostics_for_fact) == 1:
                diagnostic = diagnostics_for_fact[0]
                context = {
                    "field_name": diagnostic.field_name,
                    "logical_type": diagnostic.logical_type,
                    "format": diagnostic.format,
                }
        else:
            message = "multiple conform operations produced null-emergence residue"
            function_key = None
            limitation = None
            context = None
        raise BackendCapabilityError(
            message,
            backend=getattr(backend, "BACKEND_NAME", "unknown"),
            function_key=function_key,
            limitation=limitation,
            context=context,
            candidate_fields=fields,
            candidate_fact_keys=fact_keys,
        )
    return _drop_markers(result, (check.marker for check in checks))
