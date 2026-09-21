"""Deterministic renderers for the descriptive expression coverage report.

The report lists independent implementation discovery, descriptive information,
executable policies, inventory gaps, and captured changes.  It never turns one
of those inputs into evidence for another.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from mountainash.core.generated_artifacts import write_text_if_changed
from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    CoverageReport,
    ImplementationRecord,
    ImplState,
    OpCoverage,
    OpRecord,
)
from mountainash.core.capabilities.gaps import GapInventory, InventoryWide

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionDef
    from mountainash.relations.core.relation_system.relation_mapping.registry import RelationOperationDef

_REGEN_CMD = "hatch -e test run python -m mountainash.core.capabilities.render_markdown"


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _scope_dict(scope: Any) -> dict[str, Any]:
    return {"backend": scope.backend.value, "dialect": scope.dialect}


def _capture_value(value: Any) -> Any:
    """Render immutable capture values without using them as current evidence."""
    if value is None or type(value) in (str, bool, int, float):
        return value
    if type(value) is bytes:
        return {"encoding": "hex", "value": value.hex()}
    if isinstance(value, Enum):
        return {
            "enum": f"{type(value).__module__}.{type(value).__qualname__}",
            "name": value.name,
            "value": _capture_value(value.value),
        }
    if isinstance(value, type):
        return {"type": f"{value.__module__}.{value.__qualname__}"}
    if type(value) is tuple:
        return [_capture_value(member) for member in value]
    if type(value) is frozenset:
        return sorted(
            (_capture_value(member) for member in value), key=lambda member: json.dumps(member, sort_keys=True)
        )
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _capture_value(getattr(value, field.name)) for field in fields(value)}
    return repr(value)


def _address_dict(address: Any) -> dict[str, Any]:
    return {
        "repository": address.repository,
        "path": address.path,
        "entry": address.entry,
        "revision": address.revision,
        "artifact": (
            {"encoding": "sha256", "value": hashlib.sha256(address.artifact).hexdigest()}
            if address.artifact is not None
            else None
        ),
    }


def _origin_dict(origin: Any) -> dict[str, Any]:
    result = {
        "module": origin.module,
        "scope": _scope_dict(origin.scope),
        "source": origin.source.value,
        "domain": origin.domain.value,
        "entry": origin.entry,
    }
    if origin.captured is not None:
        result["captured"] = _address_dict(origin.captured)
    return result


def _selector_dict(selector: Any) -> dict[str, Any]:
    return {"kind": selector.kind, "value": _capture_value(selector.value)}


def _information_dict(record: Any) -> dict[str, Any]:
    assertion = record.assertion
    return {
        "scope": _scope_dict(record.key.scope),
        "operation": {"family": type(record.key.local.operation).__name__, "op": record.key.local.operation.name},
        "subject": record.key.local.subject,
        "selector": _selector_dict(record.key.local.selector),
        "variant": record.key.local.variant,
        "layer": assertion.layer.value,
        "level": assertion.level.value,
        "message": assertion.message,
        "workaround": assertion.workaround,
        "issue": assertion.issue,
        "since": assertion.since,
        "kinds": sorted(kind.value for kind in assertion.kinds),
        "origins": [_origin_dict(origin) for origin in record.origins],
    }

def _policy_dict(record: Any) -> dict[str, Any]:
    assertion = record.assertion
    return {
        "scope": _scope_dict(record.key.scope),
        "operation": {"family": type(record.key.local.operation).__name__, "op": record.key.local.operation.name},
        "subject": record.key.local.subject,
        "selector": _selector_dict(record.key.local.selector),
        "variant": record.key.local.variant,
        "level": assertion.level.value,
        "message": assertion.message,
        "consumer": assertion.consumer.value,
        "action": assertion.action.value,
        "native_errors": [error.__name__ for error in assertion.native_errors],
        "native_issue": assertion.native_issue,
        "information": None
        if assertion.information is None
        else {
            "scope": _scope_dict(assertion.information.scope),
            "operation": {
                "family": type(assertion.information.local.operation).__name__,
                "op": assertion.information.local.operation.name,
            },
            "subject": assertion.information.local.subject,
            "selector": _selector_dict(assertion.information.local.selector),
            "variant": assertion.information.local.variant,
            "layer": assertion.information.layer.value,
        },
        "issue_classes": sorted(issue_class.value for issue_class in assertion.issue_classes),
        "since": assertion.since,
        "origins": [_origin_dict(origin) for origin in record.origins],
    }


def _cell_text(cell: OpCoverage) -> str:
    """Implementation discovery only; declarations do not alter this result."""
    return {
        ImplState.IMPLEMENTED: "implemented",
        ImplState.IMPLEMENTED_VIA_HANDLER: "implemented via handler",
        ImplState.NOT_IMPLEMENTED: "not implemented",
        ImplState.UNKNOWN: "unknown",
    }[cell.impl]


def _header(report: CoverageReport) -> list[str]:
    return [
        "# Expression Coverage",
        "",
        "<!-- GENERATED FILE — do not edit by hand. -->",
        f"<!-- Regenerate: {_REGEN_CMD} -->",
        "",
        f"Registered operations: {report.stats.ops_total} · Implementation records: {sum(report.stats.by_impl.values())} "
        f"· Information: {report.stats.information_total} · Policies: {report.stats.policies_total}",
        "",
        "This report keeps independent inputs separate. Information records are descriptive; policy records are executable "
        "only at their named consumer/action. Missing information or policy is **UNKNOWN**, not evidence of support, verification, or audit success.",
        "",
        "Scoped declaration detail is in [`expression-coverage-scoped.md`](expression-coverage-scoped.md); the machine-readable "
        "projection is [`expression-coverage.json`](expression-coverage.json).",
        "",
    ]


def _summary(report: CoverageReport) -> list[str]:
    lines = ["## Summary", "", "### Implementation discovery", ""]
    lines += [
        "| Backend | implemented | via handler | not implemented | unknown | registered operations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for backend in RENDERED_BACKENDS:
        stats = report.stats.by_impl
        lines.append(
            f"| {backend.value} | {stats[(backend, ImplState.IMPLEMENTED)]} | "
            f"{stats[(backend, ImplState.IMPLEMENTED_VIA_HANDLER)]} | {stats[(backend, ImplState.NOT_IMPLEMENTED)]} | "
            f"{stats[(backend, ImplState.UNKNOWN)]} | {report.stats.ops_total} |"
        )
    lines += ["", "### Declaration counts", "", "| Kind | Breakdown |", "| --- | --- |"]
    layers = ", ".join(
        f"{layer.value} {report.stats.information_by_layer.get(layer, 0)}"
        for layer in report.stats.information_by_layer
    )
    consumers = ", ".join(
        f"{consumer.value} {report.stats.policies_by_consumer.get(consumer, 0)}"
        for consumer in report.stats.policies_by_consumer
    )
    actions = ", ".join(
        f"{action.value} {report.stats.policies_by_action.get(action, 0)}" for action in report.stats.policies_by_action
    )
    lines += [
        f"| Information layers | {layers or '—'} |",
        f"| Policy consumers | {consumers or '—'} |",
        f"| Policy actions | {actions or '—'} |",
        "",
    ]
    return lines


def _family_matrices(report: CoverageReport) -> list[str]:
    lines = [
        "## Per-family implementation discovery",
        "",
        "Implementation discovery is separate from declaration presence.",
        "",
    ]
    for family in report.families:
        source_domain = (
            "unclassified"
            if family.declaration_domain is None
            else f"{family.declaration_domain[0].value} / {family.declaration_domain[1].value}"
        )
        lines += [
            f"### `{family.family}` ({source_domain})",
            "",
            "| Operation | " + " | ".join(backend.value for backend in RENDERED_BACKENDS) + " |",
            "| --- | --- | --- | --- |",
        ]
        by_operation: dict[str, dict[Any, OpCoverage]] = {}
        for cell in family.ops:
            by_operation.setdefault(cell.op.operation_key.name, {})[cell.backend] = cell
        for operation in sorted(by_operation):
            lines.append(
                f"| `{operation}` | "
                + " | ".join(_cell_text(by_operation[operation][backend]) for backend in RENDERED_BACKENDS)
                + " |"
            )
        lines.append("")
    return lines


def _declaration_rows(title: str, records: tuple[Any, ...], serializer: Callable[[Any], dict[str, Any]]) -> list[str]:
    lines = [title, ""]
    if not records:
        return lines + ["None recorded; absence remains unknown.", ""]
    lines += [
        "| Scope | Operation | Subject | Selector | Layer / consumer-action | Level | Categories | Message | Provenance |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        payload = serializer(record)
        scope = f"{payload['scope']['backend']}/{payload['scope']['dialect'] or 'family'}"
        operation = f"{payload['operation']['family']}.{payload['operation']['op']}"
        aspect = payload.get("layer") or f"{payload['consumer']} / {payload['action']}"
        provenance = ", ".join(
            f"{origin['scope']['backend']}/{origin['scope']['dialect'] or 'family'} "
            f"{origin['source']}/{origin['domain']} {origin['module']}:{origin['entry']}"
            for origin in payload["origins"]
        )
        selector = (
            f"{payload['selector']['kind']}: "
            f"{json.dumps(payload['selector']['value'], ensure_ascii=False, sort_keys=True)}"
        )
        categories = ", ".join(payload["kinds"]) if "kinds" in payload else "—"
        if categories == "":
            categories = "unclassified"
        lines.append(
            f"| {scope} | `{operation}` | {_escape(payload['subject'])} | {_escape(selector)} | {aspect} | "
            f"{payload['level']} | {categories} | {_escape(payload['message'])} | {_escape(provenance)} |"
        )
    lines.append("")
    return lines


def _gaps_section(report: CoverageReport) -> list[str]:
    lines = ["## Known gaps", ""]
    if report.gaps is None:
        return lines + ["Gap inventories were not acquired.", ""]
    if not report.gaps:
        return lines + ["Gap inventories were acquired and contained no gaps.", ""]
    lines += [
        "| Inventory | Target | Obligation | Scope | Kind | Reason | Since |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in report.gaps:
        scope = record.key.coverage_scope
        scope_text = (
            "inventory-wide"
            if isinstance(scope, InventoryWide)
            else f"{scope.backend.value}/{scope.dialect or 'family'}"
        )
        lines.append(
            f"| {_escape(record.key.inventory)} | {_escape(json.dumps(_capture_value(record.key.target), sort_keys=True))} | "
            f"{_escape(record.key.obligation)} | {scope_text} | {record.payload.gap_kind.value} | "
            f"{_escape(record.payload.reason)} | {record.payload.since} |"
        )
    lines.append("")
    return lines


def _changes_section(report: CoverageReport) -> list[str]:
    lines = ["## Assertion change history", ""]
    if not report.changes:
        return lines + ["None recorded.", ""]
    lines += ["| Recorded at | Disposition | Prior address | Reason |", "| --- | --- | --- | --- |"]
    for change in report.changes:
        lines.append(
            f"| {change.recorded_at} | {change.disposition.value} | "
            f"{_escape(json.dumps(_address_dict(change.prior.address), sort_keys=True))} | {_escape(change.reason)} |"
        )
    return lines + [""]


def render_markdown(report: CoverageReport) -> str:
    lines = _header(report)
    lines += _summary(report)
    lines += _family_matrices(report)
    lines += _declaration_rows("## Information", report.information, _information_dict)
    lines += _declaration_rows("## Policies", report.policies, _policy_dict)
    lines += _gaps_section(report)
    lines += _changes_section(report)
    return "\n".join(lines) + "\n"


def render_scoped(report: CoverageReport) -> str:
    lines = [
        "# Expression Coverage — Scoped Declarations",
        "",
        "<!-- GENERATED FILE — do not edit by hand. -->",
        f"<!-- Regenerate: {_REGEN_CMD} -->",
        "",
        "Native and public information are descriptive. Policies are listed separately with their explicit consumer/action; "
        "neither list is verification evidence.",
        "",
    ]
    lines += _declaration_rows("## Information", report.information, _information_dict)
    lines += _declaration_rows("## Policies", report.policies, _policy_dict)
    return "\n".join(lines) + "\n"


def _segment_dict(segment: Any) -> dict[str, Any]:
    return {
        "module": segment.module,
        "scope": _scope_dict(segment.scope),
        "source": segment.source.value,
        "domain": segment.segment.domain.value,
        "changes": [_address_dict(change.change_ref) for change in segment.segment.changes],
    }


def _gap_dict(record: Any) -> dict[str, Any]:
    scope = record.key.coverage_scope
    return {
        "inventory": record.key.inventory,
        "target": _capture_value(record.key.target),
        "obligation": record.key.obligation,
        "coverage_scope": {"kind": "inventory_wide"}
        if type(scope) is InventoryWide
        else {"kind": "scope", **_scope_dict(scope)},
        "original_key": _capture_value(record.original_key),
        "origins": [_address_dict(origin) for origin in record.origins],
        "reference_context": [_address_dict(address) for address in record.reference_context],
        "gap_kind": record.payload.gap_kind.value,
        "reason": record.payload.reason,
        "since": record.payload.since,
        "review_due": (date.fromisoformat(record.payload.since) + timedelta(days=183)).isoformat(),
    }


def _change_dict(change: Any) -> dict[str, Any]:
    return {
        "change_ref": _address_dict(change.change_ref),
        "prior": _capture_value(change.prior),
        "disposition": change.disposition.value,
        "recorded_at": change.recorded_at,
        "reason": change.reason,
        "successors": [_capture_value(successor) for successor in change.successors],
        "evidence_refs": [_address_dict(address) for address in change.evidence_refs],
    }


def _cell_dict(cell: OpCoverage) -> dict[str, Any]:
    return {
        "impl": cell.impl.value,
        "impl_method": cell.impl_method,
        "impl_protocol": cell.impl_protocol,
        "information": [_information_dict(record) for record in cell.information],
        "policies": [_policy_dict(record) for record in cell.policies],
    }


def _family_dict(family: Any) -> dict[str, Any]:
    source = domain = None
    if family.declaration_domain is not None:
        source, domain = family.declaration_domain[0].value, family.declaration_domain[1].value
    grouped: dict[Any, list[OpCoverage]] = {}
    for cell in family.ops:
        grouped.setdefault(cell.op.operation_key, []).append(cell)
    return {
        "family": family.family,
        "source": source,
        "domain": domain,
        "ops": [
            {
                "op": {"family": type(operation).__name__, "op": operation.name},
                "cells": {cell.backend.value: _cell_dict(cell) for cell in cells},
            }
            for operation, cells in sorted(grouped.items(), key=lambda item: item[0].name)
        ],
    }


def render_json(report: CoverageReport) -> str:
    """Stable JSON projection; records retain their original qualified scope."""
    payload = {
        "stamp": {
            "segments": len(report.segments),
            "operations": report.stats.ops_total,
            "implementation_records": sum(report.stats.by_impl.values()),
            "information": report.stats.information_total,
            "policies": report.stats.policies_total,
        },
        "stats": {
            "backends": {
                backend.value: {state.value: report.stats.by_impl[(backend, state)] for state in ImplState}
                for backend in RENDERED_BACKENDS
            },
            "information_by_layer": {layer.value: count for layer, count in report.stats.information_by_layer.items()},
            "policies_by_consumer": {
                consumer.value: count for consumer, count in report.stats.policies_by_consumer.items()
            },
            "policies_by_action": {action.value: count for action, count in report.stats.policies_by_action.items()},
        },
        "families": [_family_dict(family) for family in report.families],
        "segments": [_segment_dict(segment) for segment in report.segments],
        "information": [_information_dict(record) for record in report.information],
        "policies": [_policy_dict(record) for record in report.policies],
        "gaps": None if report.gaps is None else [_gap_dict(gap) for gap in report.gaps],
        "changes": [_change_dict(change) for change in report.changes],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def gather_coverage_inputs(*, inventories: tuple[GapInventory, ...] | None = None) -> dict[str, Any]:
    """Capture cold reporting inputs without test declarations or snapshots."""
    from mountainash.core.capabilities.catalogue import (
        CatalogueQuery,
        ChangeQuery,
        GapQuery,
        InformationQuery,
        PolicyQuery,
    )
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry
    from mountainash.relations.core.relation_system.relation_mapping.registry import RelationOperationRegistry

    if inventories is not None and (
        type(inventories) is not tuple or any(type(item) is not GapInventory for item in inventories)
    ):
        raise TypeError("inventories requires an immutable GapInventory tuple or None")
    capture = CapabilityRegistry.capture(inventories=inventories)
    records = capture.search(
        CatalogueQuery(
            information=InformationQuery(),
            policies=PolicyQuery(),
            gaps=GapQuery() if inventories is not None else None,
            changes=ChangeQuery(family="capability" if inventories is None else None),
        )
    )
    keys = list(ExpressionFunctionRegistry.list_all()) + list(RelationOperationRegistry.list_all())
    universe = tuple(
        sorted(
            (OpRecord(key, type(key).__name__) for key in keys),
            key=lambda record: (record.family, record.operation_key.name),
        )
    )
    return {
        "universe": universe,
        "information": records.information,
        "policies": records.policies,
        "segments": capture.segments,
        "gaps": records.gaps,
        "changes": records.changes,
        "implementations": gather_implementation_records(universe),
    }


def _resolve_concrete_owner(leaf: type, name: str) -> type | None:
    for klass in leaf.__mro__:
        if klass.__name__.endswith("Protocol"):
            continue
        if name in vars(klass):
            return klass
    return None


def gather_implementation_records(universe: tuple[OpRecord, ...]) -> tuple[ImplementationRecord, ...]:
    """Independently discover implementation ownership for each registry op."""
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.backends.expression_systems.ibis import IbisExpressionSystem
    from mountainash.expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem
    from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
    from mountainash.expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry
    from mountainash.relations.backends.relation_systems.ibis import IbisRelationSystem
    from mountainash.relations.backends.relation_systems.narwhals import NarwhalsRelationSystem
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
    from mountainash.relations.core.relation_system.relation_mapping.registry import RelationOperationRegistry

    expression_keys = frozenset(ExpressionFunctionRegistry.list_all())
    expression_leaves: dict[CONST_BACKEND, type] = {
        CONST_BACKEND.POLARS: PolarsExpressionSystem,
        CONST_BACKEND.NARWHALS: NarwhalsExpressionSystem,
        CONST_BACKEND.IBIS: IbisExpressionSystem,
    }
    relation_leaves: dict[CONST_BACKEND, type] = {
        CONST_BACKEND.POLARS: PolarsRelationSystem,
        CONST_BACKEND.NARWHALS: NarwhalsRelationSystem,
        CONST_BACKEND.IBIS: IbisRelationSystem,
    }
    records: list[ImplementationRecord] = []
    definition: ExpressionFunctionDef | RelationOperationDef
    for operation in universe:
        definition = (
            ExpressionFunctionRegistry.get(operation.operation_key)
            if operation.operation_key in expression_keys
            else RelationOperationRegistry.get(operation.operation_key)
        )
        leaves = expression_leaves if operation.operation_key in expression_keys else relation_leaves
        protocol_method = definition.protocol_method
        handler = getattr(definition, "handler", None)
        for backend, leaf in leaves.items():
            if protocol_method is not None:
                owner = _resolve_concrete_owner(leaf, protocol_method.__name__)
                records.append(
                    ImplementationRecord(
                        operation.operation_key,
                        backend,
                        ImplState.IMPLEMENTED if owner else ImplState.NOT_IMPLEMENTED,
                        protocol_method.__name__,
                        owner.__qualname__ if owner else protocol_method.__qualname__.rsplit(".", 1)[0],
                    )
                )
            elif handler is not None:
                records.append(
                    ImplementationRecord(
                        operation.operation_key,
                        backend,
                        ImplState.IMPLEMENTED_VIA_HANDLER,
                        handler.__qualname__,
                        "handler",
                    )
                )
            else:
                records.append(ImplementationRecord(operation.operation_key, backend, ImplState.UNKNOWN, None, None))
    return tuple(records)


_ARTIFACT_RENDERERS: tuple[tuple[str, Callable[[CoverageReport], str]], ...] = (
    ("docs/reference/expression-coverage.md", render_markdown),
    ("docs/reference/expression-coverage-scoped.md", render_scoped),
    ("docs/reference/expression-coverage.json", render_json),
)


def write_coverage_artifacts(base: Path, report: CoverageReport) -> tuple[Path, ...]:
    rendered = tuple((base / relative_path, renderer(report)) for relative_path, renderer in _ARTIFACT_RENDERERS)
    changed: list[Path] = []
    for path, content in rendered:
        if write_text_if_changed(path, content):
            changed.append(path)
    return tuple(changed)


def main() -> None:
    from mountainash.core.capabilities.coverage import build_coverage_report

    report = build_coverage_report(**gather_coverage_inputs())
    base = Path(__file__).resolve().parents[4]
    changed = write_coverage_artifacts(base, report)
    for relative_path, _renderer in _ARTIFACT_RENDERERS:
        path = base / relative_path
        print(f"{'wrote' if path in changed else 'unchanged'} {path}")


if __name__ == "__main__":
    main()
