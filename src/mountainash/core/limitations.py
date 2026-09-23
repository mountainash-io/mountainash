"""Attribute identified native issues independently of silent-result protection."""
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

_UNSPECIFIED_DIALECT = object()


def call_with_limitation_enrichment(
    fn: Callable[[], Any],
    *,
    limitations: Mapping[tuple, Any],
    backend_name: str,
    operation_key: Any,
    named_args: Mapping[str, Any],
    identify_issue: Callable[..., str | None] | None,
    execution_context: Any,
) -> Any:
    """Enrich an identified native issue, never a merely matching error class."""
    from mountainash.core.capabilities.schema import PolicyConsumer

    if not execution_context.policy.has_demand(PolicyConsumer.IMMEDIATE_ERROR):
        return fn()
    try:
        return fn()
    except BackendCapabilityError:
        raise  # already enriched (e.g. by a nested visit) — never re-wrap
    except Exception as exc:
        issue = (
            identify_issue(exc, operation_key=operation_key, arguments=named_args)
            if identify_issue is not None else None
        )
        if issue is None:
            raise
        matches = [
            fact for (key, param), fact in limitations.items()
            if key == operation_key and (param in named_args or param == WILDCARD_PARAM)
            and fact.consumer is PolicyConsumer.IMMEDIATE_ERROR
            and fact.native_issue == issue and isinstance(exc, fact.native_errors)
            and _routing_matches(fact, named_args)
        ]
        if len(matches) == 1:
            fact = matches[0]
            raise BackendCapabilityError(
                fact.message, backend=backend_name, function_key=operation_key, limitation=fact,
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
    native_issue: str | None = None,
) -> list[tuple[Any, Any]]:
    from mountainash.core.capabilities.schema import PolicyConsumer, ResidueSignal

    matches: list[tuple[Any, Any]] = []
    family = diagnostic.backend_family
    for fact in facts:
        fact_family = getattr(fact.backend, "value", fact.backend)
        if fact_family != family:
            continue
        if fact.dialect != diagnostic.dialect:
            continue
        if fact.operation_key != diagnostic.function_key:
            continue
        if fact.residue_signal is not signal:
            continue
        if not _routing_matches(fact, dict(diagnostic.routing_fingerprint)):
            continue
        if signal is ResidueSignal.EXCEPTION and (
            error is None or not isinstance(error, fact.native_errors)
            or native_issue is None or fact.native_issue != native_issue
            or fact.consumer is not PolicyConsumer.MATERIALIZATION_ERROR
        ):
            continue
        if signal is ResidueSignal.EXCEPTION and diagnostic.failure_behavior != "throw":
            continue
        matches.append((diagnostic, fact))
    return matches


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
    dialect: Any = _UNSPECIFIED_DIALECT,
    diagnostic_trace: Any = None,
    residue_checks: Iterable[Any] = (),
    execution_context: Any = None,
) -> Any:
    """Enrich deterministic capability residue at a materialization boundary."""
    from mountainash.conform.errors import ConformError
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.schema import PolicyConsumer, ResidueSignal
    from mountainash.core.errors import CapabilityResidueInvariantError
    from mountainash.core.types import BackendCapabilityError

    family = getattr(backend, "backend_type", None)
    active_dialect = getattr(backend, "dialect", None) if dialect is _UNSPECIFIED_DIALECT else dialect
    checks = tuple(residue_checks)
    if family is None:
        return fn()

    diagnostics = tuple(getattr(diagnostic_trace, "records", ()))
    # Registry access is itself a demanded-loading trigger (bootstrap
    # autoload from UNINITIALIZED) -- skip it entirely when neither residue
    # consumer this function serves is demanded, so a trusted()/no-demand
    # caller never forces a cold registry to load its optional declaration
    # source (T08 item 13, mirrors the GATE-demand check in _dispatch).
    if execution_context is not None and not (
        execution_context.policy.has_demand(PolicyConsumer.MATERIALIZATION_ERROR)
        or execution_context.policy.has_demand(PolicyConsumer.RESULT_PROTECTION)
    ):
        facts = ()
    else:
        facts = CapabilityRegistry.residue_candidates(
            family, active_dialect, execution_context=execution_context,
        )
    if not facts and not diagnostics and not checks:
        return fn()
    try:
        result = fn()
    except BackendCapabilityError:
        raise
    except ConformError:
        raise
    except Exception as exc:
        if execution_context is not None and not execution_context.policy.has_demand(
            PolicyConsumer.MATERIALIZATION_ERROR
        ):
            raise
        identify = getattr(backend, "identify_native_issue", None)
        native_issue = identify(exc) if identify is not None else None
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
                    native_issue=native_issue,
                )
            )
        if not matched and native_issue is not None and prefer_operation_keys:
            identified = [
                fact for fact in facts
                if fact.operation_key in prefer_operation_keys
                and fact.dialect == active_dialect
                and fact.consumer is PolicyConsumer.MATERIALIZATION_ERROR
                and fact.native_issue == native_issue
                and isinstance(exc, fact.native_errors)
                and fact.option_value is None and fact.predicate is None and fact.value_class is None
            ]
            if len(identified) == 1:
                fact = identified[0]
                raise BackendCapabilityError(
                    fact.message, backend=getattr(backend, "BACKEND_NAME", "unknown"),
                    function_key=fact.operation_key, limitation=fact,
                ) from exc
        if not matched:
            from mountainash.relations.core.unified_visitor.relation_visitor import (
                CONFORM_TRANSFORM_KEYS,
            )
            eligible = tuple(
                diagnostic
                for diagnostic in diagnostics
                if diagnostic.backend_family == getattr(family, "value", family)
                and (
                    diagnostic.dialect is None
                    or diagnostic.dialect == active_dialect
                )
                and diagnostic.failure_behavior == "throw"
                and diagnostic.function_key in CONFORM_TRANSFORM_KEYS
                and (
                    prefer_operation_keys is None
                    or diagnostic.function_key in prefer_operation_keys
                )
            )
            if eligible:
                from mountainash.conform.errors import ConformTransformError

                raise ConformTransformError(
                    original_error=exc,
                    candidates=eligible,
                ) from exc
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
    marker_result = result
    if checks:
        from mountainash.core.types import is_ibis_table

        if is_ibis_table(result):
            from mountainash.core.capabilities.identity import BackendIdentity
            from mountainash.relations.core.materialization import (
                MaterializationPurpose,
                diagnostic_polars_view,
                materialize_native,
            )

            # Aggregate all markers in one query without transporting data columns.
            marker_summary = result.aggregate(**{
                check.marker: result[check.marker].any() for check in checks
            })
            marker_native = materialize_native(
                marker_summary,
                BackendIdentity(family, active_dialect),
                MaterializationPurpose.DIAGNOSTIC_VIEW,
                execution_context=execution_context,
            )
            marker_result = diagnostic_polars_view(marker_native).frame
    true_checks = tuple(check for check in checks if _is_true_marker(marker_result, check.marker))
    if not true_checks:
        return _drop_markers(result, (check.marker for check in checks))

    matched = []
    for check in true_checks:
        check_matches = []
        for diagnostic in diagnostics:
            if diagnostic.function_key != check.function_key:
                continue
            if diagnostic.field_name != check.field_name:
                continue
            check_matches.extend(
                _diagnostic_matches(
                    diagnostic,
                    facts,
                    signal=ResidueSignal.NON_NULL_TO_NULL,
                )
            )
        if not check_matches:
            raise CapabilityResidueInvariantError(
                f"materialization residue marker has no declared fact for field {check.field_name!r}"
            )
        matched.extend(check_matches)

    fact_keys = tuple(sorted({fact.fact_key for _, fact in matched}))
    fields = tuple(sorted({diagnostic.field_name for diagnostic, _ in matched}))
    diagnostics_for_fact = tuple(
        diagnostic for diagnostic, fact in matched if fact.fact_key == fact_keys[0]
    ) if len(fact_keys) == 1 else ()
    if len(true_checks) == 1 and len(fact_keys) == 1 and len(diagnostics_for_fact) == 1:
        fact = next(fact for _, fact in matched if fact.fact_key == fact_keys[0])
        diagnostic = diagnostics_for_fact[0]
        message = fact.message
        function_key = fact.operation_key
        limitation = fact
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
