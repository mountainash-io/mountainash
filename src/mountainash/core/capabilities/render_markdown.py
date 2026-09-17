"""Deterministic markdown + JSON renderers for the expression coverage report.

Pure over CoverageReport; input gathering + main() live at the bottom
(Task 5). No wall-clock reads anywhere (spec §4.4). The JSON renderer is
spec §4.6 — the machine-readable extract, the third committed artifact.
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


from mountainash.core.capabilities.gaps import InventoryWide
from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    CoverageReport,
    ImplementationRecord,
    ImplState,
    OpCoverage,
    OpRecord,
    fact_sort_key,  # canonical order
    is_dialect_scoped_whole_op,  # I-2b cell predicate + scoped-doc subheading
    is_whole_op,  # partition predicate (rev 6)
)
from mountainash.core.capabilities.schema import (
    CapabilityFact,
    CapabilityLevel,
    ClauseOp,
    Enforcement,  # summary stats
    ValueClass,
)

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.capabilities.gaps import VerificationSnapshot

_REGEN_CMD = "hatch -e test run python -m mountainash.core.capabilities.render_markdown"

_LEGEND = """\
Legend — cell states (by exception):

- `✓` **default-capable** — implemented and clean, no constraining fact. The
  presumption; the majority; not a gap. Routed / dialect-verified annotations
  still append (`✓ ↻ routed`, `✓ ✓ dialect-verified: …`).
- `✓ audited` — same as above, strengthened by an active physical segment
  covering this op's (backend, source, domain). **Scope of the claim:** the
  segment records the ownership surface; it is not evidence that this specific
  operation, or the segment itself, was exercised.
- `✓ᴴ` **implemented via handler** — same as `✓` / `✓ audited`, but reached
  through the visitor's `handler` dispatch path rather than a concrete
  protocol-method override on the backend leaf class (spec §3.6). The `ᴴ`
  superscript marks the dispatch shape, not a coverage grade.
- `◐ partial (…)` / `✗ unsupported` / `poly` — **CONSTRAINED**: at least one
  GATE constraint or runtime residue fact applies (counts are distinct
  selector keys, never raw fact counts).
- `—` **NOT_IMPLEMENTED** — the protocol-method override is absent (or only a
  bare `…` stub on the `*Protocol` carrier) and the cell has no facts and
  no applicable segment. The only true blank.
- `⚠ contradiction` — `NOT_IMPLEMENTED` AND the cell carries facts, a routed
  or refinement entry, or an applicable segment. Catalog and registry
  disagree; the suite-level `contradictions == 0` invariant guards this.
- `?` **UNKNOWN** — the registry has no definition for the op, or the
  definition carries neither `protocol_method` nor `handler`. The `audited`
  flag is stored on these cells but is **not rendered on `?` cells** —
  audited is stored but not rendered on `?` cells (the field is not dead
  state; the badge is suppressed because the registry's view of the op is
  too thin to anchor a claim).
- Annotations: `↻ routed` (router metadata — handled via an alternate path),
  `⚠ runtime` (materialize-residue failure), `✓ dialect-verified`
  (dialect-scoped EXPR_CAPABLE refinement).
- `fidelity` is None on all EXECUTE facts by registration validation and is
  omitted from detail rows.
"""


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _collapse_identity(f: CapabilityFact) -> tuple:
    """Full semantic identity EXCLUDING option_value (spec §4.3)."""
    return (
        f.operation_key,
        f.backend,
        f.param,
        f.level,
        f.enforcement,
        f.boundary,
        f.dialect,
        f.value_class,
        f.predicate,
        f.condition,
        f.message,
        f.workaround,
        f.upstream_ref,
        f.since,
        f.native_errors,
        f.probe_exempt,
    )


def _collapse_groups(
    facts: tuple[CapabilityFact, ...],
) -> list[tuple[CapabilityFact, list[str]]]:
    groups: dict[tuple, list[CapabilityFact]] = {}
    for f in sorted(facts, key=fact_sort_key):
        groups.setdefault(_collapse_identity(f), []).append(f)
    out: list[tuple[CapabilityFact, list[str]]] = []
    for members in groups.values():
        values = sorted(m.option_value for m in members if m.option_value is not None)
        if len(members) >= 3 and len(values) == len(members):
            # Collapse ONLY when every member carries an option_value; a mixed
            # group (value-agnostic + exact-value facts sharing the remaining
            # identity) renders per-fact — that is the defined handling.
            out.append((members[0], values))
        else:
            out.extend((m, [m.option_value] if m.option_value else []) for m in members)
    out.sort(key=lambda pair: fact_sort_key(pair[0]))
    return out


def _cell_text(oc: OpCoverage) -> str:
    """Spec §3.3 render map, if/elif chain in table order.

    Order is load-bearing: `contradiction` is only reachable when
    `impl is NOT_IMPLEMENTED`, so the contradiction check must come before
    the bare NOT_IMPLEMENTED branch — reordering misrenders edge cells
    (the matrix would silently downgrade contradictions to `—`).
    """
    # 1. UNKNOWN -> `?` (no glyph change, no annotations; the audited field
    # is stored but never rendered on `?` cells per spec §3.3).
    if oc.impl is ImplState.UNKNOWN:
        return "?"
    # 2. NOT_IMPLEMENTED + any facts / routed / refinement / audited -> ⚠ contradiction
    if oc.contradiction:
        return "⚠ contradiction"
    # 3. NOT_IMPLEMENTED clean -> `—` (the only true blank).
    if oc.impl is ImplState.NOT_IMPLEMENTED:
        return "—"
    # 4. implemented* + constrained -> existing composition (UNCHANGED across rev 5).
    if oc.constrained:
        status: list[str] = []
        if oc.whole_op is CapabilityLevel.UNSUPPORTED:
            status.append("✗ unsupported")
        elif oc.whole_op is CapabilityLevel.POLYMORPHIC:
            status.append("poly")
        sc = oc.selector_counts
        if any(
            (
                sc.params,
                sc.option_selectors,
                sc.metadata_selectors,
                sc.value_classes,
                sc.dialects,
            )
        ):
            partial = (
                f"◐ partial ({sc.params} params, {sc.option_selectors} option-selectors, "
                f"{sc.metadata_selectors} metadata-selectors, {sc.value_classes} value-classes, "
                f"{sc.dialects} dialects)"
            )
            # I-2b (spec §4.3 rev 6): a dialect-scoped whole-op gate names its
            # level+dialect in the matrix cell, so a whole-op-for-a-dialect
            # severity is visible in the matrix, not hidden behind a
            # '1 dialects' count in another file. Suffix attaches to the
            # partial annotation, mirroring the spec example
            # `◐ partial (…) · unsupported on ibis-duckdb`. Group by level
            # so multiple distinct levels render as separate suffixes.
            dsw = [f for f in oc.constraints if is_dialect_scoped_whole_op(f)]
            if dsw:
                by_level: dict[str, set[str]] = {}
                for f in dsw:
                    by_level.setdefault(f.level.value, set()).add(f.dialect or "")
                parts = [f"{lv} on {','.join(sorted(dialects))}" for lv, dialects in sorted(by_level.items())]
                partial = f"{partial} · {' · '.join(parts)}"
            status.append(partial)
        text = " + ".join(status)  # spec §3.5: `poly + ◐ partial (…)`
    else:
        # 5. implemented* + clean -> base mark (`✓` or `✓ᴴ` for handler),
        # then `audited` badge if applicable, then annotations.
        text = "✓ᴴ" if oc.impl is ImplState.IMPLEMENTED_VIA_HANDLER else "✓"
        if oc.audited:
            text = f"{text} audited"
    # Annotations: same composition as before (routed / runtime / dialect-verified).
    notes: list[str] = []
    if oc.routed:
        notes.append("↻ routed")
    if oc.residue:
        notes.append("⚠ runtime")
    if oc.refinements:
        dialects = ", ".join(sorted({f.dialect for f in oc.refinements if f.dialect}))
        notes.append(f"✓ dialect-verified: {dialects}")
    return " ".join([text, *notes])


def _header(report: CoverageReport) -> list[str]:
    impl_total = sum(report.stats.by_impl.values())
    return [
        "# Expression Coverage",
        "",
        "<!-- GENERATED FILE — do not edit by hand. -->",
        f"<!-- Regenerate: {_REGEN_CMD} -->",
        "",
        f"Segments: {len(report.segments)} · Historical bundles: {len(report.bundles)} "
        f"· Facts: {report.stats.facts_total} · Registered operations: {report.stats.ops_total} "
        f"· Implementation records: {impl_total}",
        "",
        "Scoped deviations (dialect/param/option/metadata/value-class) live in "
        "[`expression-coverage-scoped.md`](expression-coverage-scoped.md).",
        "",
        "Parquet recipe: flatten `families[].ops[].cells` from "
        "[`expression-coverage.json`](expression-coverage.json) into rows, "
        "then `pl.DataFrame(rows).write_parquet(...)`.",
        "",
        _LEGEND,
    ]


def _summary(report: CoverageReport) -> list[str]:
    lines = ["## Summary", ""]
    lines.append("### Per-backend counts")
    lines.append("")
    lines.append(
        "| Backend | default_capable | audited_clean | constrained " "| NOT_IMPLEMENTED | UNKNOWN | ops_total |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for b in RENDERED_BACKENDS:
        s = report.stats
        lines.append(
            f"| {b.value} | {s.default_capable[b]} | {s.audited_clean[b]} "
            f"| {s.constrained[b]} | {s.by_impl[(b, ImplState.NOT_IMPLEMENTED)]} "
            f"| {s.by_impl[(b, ImplState.UNKNOWN)]} | {s.ops_total} |"
        )
    # Both invariants visible even when 0 (symmetric with the per-backend
    # sum law above): a count of 0 is the test-passing state, not a missing
    # line. Spec §3.3 / §4.1.
    lines.append("")
    lines.append(f"contradictions: {report.stats.contradictions}")
    lines.append(f"audited_unknown: " f"{sum(report.stats.audited_unknown.values())}")
    lines.append("")
    lines.append("### Fact statistics")
    lines.append("")
    lines.append("| Axis | Breakdown |")
    lines.append("| --- | --- |")
    level_bits = ", ".join(
        f"{lv.value} {report.stats.facts_by_level[lv]}" for lv in CapabilityLevel if lv in report.stats.facts_by_level
    )
    enf_bits = ", ".join(
        f"{e.value} {report.stats.facts_by_enforcement[e]}"
        for e in Enforcement
        if e in report.stats.facts_by_enforcement
    )
    backend_bits = ", ".join(
        f"{b.value} {report.stats.facts_by_backend[b]}" for b in RENDERED_BACKENDS if b in report.stats.facts_by_backend
    )
    lines.append(f"| Level | {level_bits or '—'} |")
    lines.append(f"| Enforcement | {enf_bits or '—'} |")
    lines.append(f"| Backend | {backend_bits or '—'} |")
    lines.append("")
    lines.append(
        "`pandas` / `pyarrow` are routed input types (they execute via the "
        "narwhals path) and are not independent coverage columns."
    )
    lines.append("")
    lines.append("### Active segments")
    lines.append("")
    lines.append("| Module | Backend | Scope | Source | Domain | Evidence references |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for segment in report.segments:
        scope = segment.scope.dialect or "family"
        evidence = ", ".join(reference.entry for reference in segment.segment.evidence_refs) or "—"
        lines.append(
            f"| `{segment.module}` | {segment.scope.backend.value} | {scope} "
            f"| {segment.source.value} | {segment.segment.domain.value} | {_escape(evidence)} |"
        )
    lines.append("")
    lines.append("### Captured historical waves")
    lines.append("")
    lines.append(
        "These retained source captures preserve provenance, including empty bundles. "
        "They are historical records, not current native-support claims."
    )
    lines.append("")
    lines.append("| Backend | Source | Domain | Probe date | Library versions | Fixtures |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for bundle in report.bundles:
        if bundle.evidence is None:
            probe, versions, fixtures = "—", "—", "—"
        else:
            probe = bundle.evidence.probe_date
            versions = ", ".join(f"{name} {version}" for name, version in bundle.evidence.library_versions)
            fixtures = ", ".join(bundle.evidence.fixtures)
        lines.append(
            f"| {bundle.backend.value} | {bundle.source.value} | {bundle.domain.value} "
            f"| {probe} | {_escape(versions)} | {_escape(fixtures)} |"
        )
    lines.append("")
    return lines


def _family_matrices(report: CoverageReport) -> list[str]:
    lines = ["## Per-family coverage", ""]
    backends_header = " | ".join(b.value for b in RENDERED_BACKENDS)
    for fam in report.families:
        if fam.audit_domain is None:
            continue  # unmapped families render in their own section (Task 5)
        source, domain = fam.audit_domain
        lines.append(f"### `{fam.family}` ({source.value} / {domain.value})")
        lines.append("")
        lines.append(f"| Operation | {backends_header} |")
        lines.append("| --- | --- | --- | --- |")
        by_op: dict[str, dict] = {}
        for oc in fam.ops:
            by_op.setdefault(oc.op.operation_key.name, {})[oc.backend] = oc
        for op_name in sorted(by_op):
            cells = " | ".join(_cell_text(by_op[op_name][b]) for b in RENDERED_BACKENDS)
            lines.append(f"| `{op_name}` | {cells} |")
        lines.append("")
    return lines


def _unmapped_families(report: CoverageReport) -> list[str]:
    unmapped = [f for f in report.families if f.audit_domain is None]
    if not unmapped:
        return []
    lines = [
        "## Unmapped families",
        "",
        "No declaration domain exists for these enum classes yet; no audit "
        "applies (every cell carries only the implementation axis). "
        "Extending coverage here starts at `classify_domain`/"
        "`_DOMAIN_SUFFIXES` (spec §3.2).",
        "",
    ]
    for fam in unmapped:
        names = sorted({oc.op.operation_key.name for oc in fam.ops})
        n_ops = len(names)
        # §3.6 stamp (spec §4.3): the impl summary restricted to this family's
        # ops. Per-backend cell counts of implemented* cells. Uniform means
        # every backend has full coverage for all N ops; the split otherwise
        # shows per-backend coverage out of N.
        by_backend: dict[CONST_BACKEND, int] = {b: 0 for b in RENDERED_BACKENDS}
        for oc in fam.ops:
            if oc.impl in {ImplState.IMPLEMENTED, ImplState.IMPLEMENTED_VIA_HANDLER}:
                by_backend[oc.backend] += 1
        if all(by_backend[b] == n_ops for b in RENDERED_BACKENDS):
            stamp = f"{n_ops} ops — all implemented on " f"{len(RENDERED_BACKENDS)}/{len(RENDERED_BACKENDS)} backends"
        else:
            stamp = f"{n_ops} ops — " + " · ".join(f"{by_backend[b]}/{n_ops} {b.value}" for b in RENDERED_BACKENDS)
        lines.append(f"- `{fam.family}` ({stamp}): " + ", ".join(f"`{n}`" for n in names))
    lines.append("")
    return lines


def _predicate_text(fact: CapabilityFact) -> str:
    """Render a fact's executable predicate conjunction for report consumers."""
    if fact.predicate is None:
        return "—"

    def clause_text(clause: Any) -> str:
        if clause.op is ClauseOp.EQ:
            return f"{clause.path} == {clause.operand!r}"
        if clause.op is ClauseOp.IN:
            values = ", ".join(sorted(map(repr, clause.operand)))
            return f"{clause.path} in {{{values}}}"
        if clause.op is ClauseOp.IS_SET:
            return f"{clause.path} is set"
        if clause.op is ClauseOp.IS_NULL:
            return f"{clause.path} is null"
        if clause.op is ClauseOp.IS_LITERAL:
            return f"{clause.path} is literal"
        if clause.op is ClauseOp.MATCHES_CLASS:
            return f"{clause.path} matches {clause.operand!r}"
        raise ValueError(f"unknown clause operator {clause.op!r}")

    return " AND ".join(clause_text(clause) for clause in fact.predicate.clauses)


def _fact_detail_row(f: CapabilityFact, values: list[str]) -> str:
    option = _escape(", ".join(values)) if values else "—"  # values are escaped, no code spans
    native = ", ".join(e.__name__ for e in f.native_errors) or "—"
    return (
        f"| {f.dialect or '*'} | {_escape(f.param)} | {option} "
        f"| {f.value_class.value if f.value_class else '—'} "
        f"| {f.level.value} | {f.enforcement.value} | {f.boundary.value} "
        f"| {_escape(f.condition or '—')} | {_escape(_predicate_text(f))} "
        f"| {_escape(f.message or '—')} | {_escape(f.workaround or '—')} "
        f"| {f.upstream_ref or '—'} | {f.since or '—'} | {native} "
        f"| {_escape(f.probe_exempt or '—')} |"
    )


_DETAIL_HEADER = (
    "| Dialect | Param | Option values | Value class | Level | Enforcement "
    "| Boundary | Condition | Predicate | Message | Workaround | Upstream | Since "
    "| Native errors | Probe-exempt |"
)
_DETAIL_RULE = "| " + " | ".join(["---"] * 15) + " |"


def _detail_sections(report: CoverageReport) -> list[str]:
    """Per-op detail holds ONLY function-level (whole-op) facts (spec §4.3
    rev 6). A pointer line under the section header names the scoped doc;
    cells whose facts are all scoped get no main-doc section at all.
    Partition is exact against the scoped doc — every input fact's detail
    body lives in exactly one of the two artifacts (§4.5 M-3)."""
    lines = ["## Per-op detail", ""]
    lines.append(
        "Cells whose facts are all scoped (dialect / parameter / option / "
        "metadata / value-class) have no section here — see "
        "[Scoped Deviations](expression-coverage-scoped.md) "
        "for the scoped detail. `refinements` (EXPR_CAPABLE + dialect) are "
        "scoped by construction; `dialect-scoped whole-op` facts appear "
        "under that doc's `Dialect-scoped whole-op` subheading."
    )
    lines.append("")
    wrote_any = False
    for fam in report.families:
        for oc in fam.ops:
            function_level = tuple(f for f in oc.all_facts if is_whole_op(f))
            if not function_level:
                continue
            wrote_any = True
            lines.append(f"### `{oc.op.operation_key.name}` × {oc.backend.value} " f"({oc.op.family})")
            lines.append("")
            lines.append(_DETAIL_HEADER)
            lines.append(_DETAIL_RULE)
            for f, values in _collapse_groups(function_level):
                lines.append(_fact_detail_row(f, values))
            lines.append("")
    if not wrote_any:
        lines.append("No function-level facts registered.")
        lines.append("")
    return lines


def _divergences_section(report: CoverageReport) -> list[str]:
    lines = ["## Divergence register", ""]
    if not report.divergences:
        return lines + ["None recorded.", ""]
    lines.append("| Id | Kind | Backends | Operations | Summary | Impact " "| Workaround | Upstream | Since |")
    lines.append("| " + " | ".join(["---"] * 9) + " |")
    for dv in report.divergences:
        ops = ", ".join(f"`{k.name}`" for k in dv.operation_keys) or "—"
        lines.append(
            f"| {dv.id} | {dv.kind.value} | {', '.join(dv.backends)} | {ops} "
            f"| {_escape(dv.summary)} | {_escape(dv.impact)} "
            f"| {_escape(dv.workaround or '—')} | {dv.upstream_ref or '—'} "
            f"| {dv.since or '—'} |"
        )
    lines.append("")
    return lines


def _gaps_section(report: CoverageReport) -> list[str]:
    lines = ["## Known gaps", ""]
    if report.gaps is None:
        return lines + ["Verification inventories not requested.", ""]
    if not report.gaps:
        return lines + ["None recorded.", ""]
    lines.append("| Inventory | Target | Obligation | Kind | Reason | Since | Review due |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for record in report.gaps:
        gap = record.payload
        due = (date.fromisoformat(gap.since) + timedelta(days=183)).isoformat()
        target = _escape(_compact_json(_capture_value(record.key.target)))
        lines.append(
            f"| {_escape(record.key.inventory)} | {target} | {_escape(record.key.obligation)} "
            f"| {gap.gap_kind.value} | {_escape(gap.reason)} | {gap.since} | {due} |"
        )
    lines.append("")
    return lines


def _capture_value(value: Any) -> Any:
    """Diagnostic projection of immutable captures; not a lossless codec."""
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
            (_capture_value(member) for member in value),
            key=lambda member: json.dumps(member, sort_keys=True, ensure_ascii=False),
        )
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _capture_value(getattr(value, field.name))
            for field in fields(value)
        }
    raise TypeError(f"unsupported captured value {type(value).__name__}")


def _captured_address_dict(address: Any) -> dict[str, Any]:
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


def _captured_assertion_dict(assertion: Any) -> dict[str, Any]:
    return {
        "family": assertion.family,
        "key": _capture_value(assertion.key),
        "payload": _capture_value(assertion.payload),
        "address": _captured_address_dict(assertion.address),
        "reference_context": [
            _captured_address_dict(address) for address in assertion.reference_context
        ],
    }


def _environment_dict(environment: Any) -> dict[str, Any] | None:
    if environment is None:
        return None
    return {
        "coordinates": [
            {
                "kind": coordinate.kind,
                "name": coordinate.name,
                "version": coordinate.version,
                "original_label": coordinate.original_label,
            }
            for coordinate in environment.coordinates
        ]
    }


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _fixed_versions_text(environment: Any) -> str:
    if environment is None:
        return "unknown"
    if not environment.coordinates:
        return "observed environment (no version coordinates)"
    return "; ".join(
        f"{coordinate.kind}:{coordinate.name}={coordinate.version or 'unknown'}"
        f" (imported as {coordinate.original_label})"
        for coordinate in environment.coordinates
    )


def _changes_section(report: CoverageReport) -> list[str]:
    lines = ["## Assertion change history", ""]
    if not report.changes:
        return lines + ["None recorded.", ""]
    lines += [
        "Diagnostic projection of captured records; this report is not a lossless "
        "serialization format.",
        "",
        "| Recorded at | Disposition | Prior address | Prior payload | Successor addresses "
        "| Evidence addresses | Fixed-version coordinates | Reason |",
        "| " + " | ".join(["---"] * 8) + " |",
    ]
    for change in reversed(report.changes):
        successors = [_captured_address_dict(successor.address) for successor in change.successors]
        evidence = [_captured_address_dict(address) for address in change.evidence_refs]
        lines.append(
            f"| {change.recorded_at} | {change.disposition.value} "
            f"| {_escape(_compact_json(_captured_address_dict(change.prior.address)))} "
            f"| {_escape(_compact_json(_capture_value(change.prior.payload)))} "
            f"| {_escape(_compact_json(successors))} "
            f"| {_escape(_compact_json(evidence))} "
            f"| {_escape(_fixed_versions_text(change.fixed_versions))} "
            f"| {_escape(change.reason)} |"
        )
    lines.append("")
    return lines


def render_markdown(report: CoverageReport) -> str:
    lines: list[str] = []
    lines += _header(report)
    lines += _summary(report)
    lines += _family_matrices(report)
    lines += _unmapped_families(report)
    lines += _detail_sections(report)
    lines += _divergences_section(report)
    lines += _gaps_section(report)
    lines += _changes_section(report)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Scoped-deviations doc — spec §4.3 rev 6 (multi-artifact rendering).
# The companion to render_markdown: every input fact's detail body appears
# in exactly one of the two markdown artifacts. Function-level (whole-op)
# coverage and the matrices live in the main doc; everything else lives
# here, with dialect-scoped whole-op facts FIRST under a dedicated
# subheading and the option-collapse rule on the remainder.
# ---------------------------------------------------------------------------

_SCOPED_LEGEND = """\
Legend — scoped deviations:

- The main doc (`expression-coverage.md`) carries matrices, function-level
  coverage, and the by-exception render map. This doc carries the per-op
  detail for every fact with a dialect, parameter, option, metadata, or
  value-class selector. The two are byte-disjoint on detail bodies — every input fact
  appears in exactly one artifact's detail body (§4.5 M-3).
- **Dialect-scoped whole-op facts** (wildcard param + a dialect, no
  option_value or value_class) render FIRST under a `Dialect-scoped
  whole-op` subheading within each (op, backend) section. The main doc's
  matrix cell surfaces the level + dialect via the I-2b suffix
  (e.g. `◐ partial (…) · unsupported on ibis-duckdb`).
- All other scoped facts render with the §4.3 option-collapse rule:
  groups of ≥3 facts sharing every semantic field except `option_value`
  collapse to a single row with the sorted `option_value` list; smaller
  groups render per-fact.
- Annotations seen in the main doc's matrix (`↻ routed`, `⚠ runtime`,
  `✓ dialect-verified: …`) describe the same cells; this doc carries
  the underlying fact rows, not the annotations.
- `fidelity` is None on all EXECUTE facts by registration validation and
  is omitted from detail rows.
"""


def _scoped_header(report: CoverageReport) -> list[str]:
    impl_total = sum(report.stats.by_impl.values())
    return [
        "# Expression Coverage — Scoped Deviations",
        "",
        "<!-- GENERATED FILE — do not edit by hand. -->",
        f"<!-- Regenerate: {_REGEN_CMD} -->",
        "",
        "Scoped deviations — dialect, parameter, option, metadata, value-class; "
        "function-level coverage and matrices live in "
        "[`expression-coverage.md`](expression-coverage.md).",
        "",
        f"Segments: {len(report.segments)} · Historical bundles: {len(report.bundles)} "
        f"· Facts: {report.stats.facts_total} · Registered operations: {report.stats.ops_total} "
        f"· Implementation records: {impl_total}",
        "",
        _SCOPED_LEGEND,
    ]


def _scoped_detail_sections(report: CoverageReport) -> list[str]:
    """Per-op detail for every (op, backend) cell holding ≥1 scoped
    (non-whole-op) fact. Dialect-scoped whole-op facts render FIRST under
    a `Dialect-scoped whole-op` subheading; the remainder gets the
    option-collapse rule."""
    lines = ["## Per-op detail (scoped)", ""]
    wrote_any = False
    for fam in report.families:
        for oc in fam.ops:
            scoped = tuple(f for f in oc.all_facts if not is_whole_op(f))
            if not scoped:
                continue
            wrote_any = True
            lines.append(f"### `{oc.op.operation_key.name}` × {oc.backend.value} " f"({oc.op.family})")
            lines.append("")
            dsw = tuple(f for f in scoped if is_dialect_scoped_whole_op(f))
            remaining = tuple(f for f in scoped if not is_dialect_scoped_whole_op(f))
            if dsw:
                lines.append("#### Dialect-scoped whole-op")
                lines.append("")
                lines.append(_DETAIL_HEADER)
                lines.append(_DETAIL_RULE)
                # No option-collapse on the dialect-scoped subheading: every
                # fact here has option_value=None, value_class=None,
                # param=WILDCARD_PARAM — only `dialect` varies, so each
                # fact is a distinct row already.
                for f in sorted(dsw, key=fact_sort_key):
                    lines.append(_fact_detail_row(f, []))
                lines.append("")
            if remaining:
                lines.append(_DETAIL_HEADER)
                lines.append(_DETAIL_RULE)
                for f, values in _collapse_groups(remaining):
                    lines.append(_fact_detail_row(f, values))
                lines.append("")
    if not wrote_any:
        lines.append("No scoped facts registered.")
        lines.append("")
    return lines


def render_scoped(report: CoverageReport) -> str:
    """Spec §4.3 rev 6 — the scoped-deviations markdown. Companion to
    `render_markdown`; together they satisfy the §4.5 M-3 partition-
    exactness invariant. Pure; no registry calls, no wall clock, no
    environment strings."""
    lines: list[str] = []
    lines += _scoped_header(report)
    lines += _scoped_detail_sections(report)
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# JSON renderer — diagnostic coverage projection.
# Fact rows remain uncollapsed. Assertion-change rows carry their complete
# in-memory captured fields, but this report is not a lossless capture codec.
# Determinism rests on insertion order: every dict is populated by iterating
# already-sorted sequences; no `set` iteration.
# ---------------------------------------------------------------------------



def _op_key(operation_key: Any) -> dict[str, str]:
    """Two-part op key (spec §4.6): the enum class name + member name.
    Accepts either an enum member OR an OpRecord (which carries the enum
    member as `.operation_key`). This is the same identity the markdown
    uses; never `str(enum)`."""
    if isinstance(operation_key, OpRecord):
        operation_key = operation_key.operation_key
    return {"family": type(operation_key).__name__, "op": operation_key.name}


def _operand_json(operand: Any) -> dict[str, Any]:
    """JSON-safe tagged encoding of a predicate clause operand, mirroring
    schema._operand_key's own kind tagging (0=None, 1=frozenset, 2=ValueClass,
    3=other Enum, 4=scalar) so the committed JSON round-trips the exact same
    identity tuple test_json_completeness compares against the live model."""
    if operand is None:
        return {"kind": 0, "value": None}
    if isinstance(operand, frozenset):
        return {"kind": 1, "value": sorted(str(m) for m in operand)}
    if isinstance(operand, ValueClass):
        return {"kind": 2, "value": operand.value}
    if isinstance(operand, Enum):
        return {"kind": 3, "type": type(operand).__name__, "value": operand.value}
    return {"kind": 4, "value": operand}


def _clause_dict(clause: Any) -> dict[str, Any]:
    return {"path": clause.path, "op": clause.op.name, "operand": _operand_json(clause.operand)}


def _fact_dict(f: CapabilityFact) -> dict[str, Any]:
    """Serialize one CapabilityFact as a dict (spec §4.6 <fact> shape).

    `option_value` is None -> JSON `null`; `native_errors=()` -> JSON `[]`.
    `value_class` is None -> JSON `null`; the level/enforcement/boundary
    are serialized by .value. `condition`/`message` are always strings (the
    model's default is "" so absent-prose is "" not null here). `predicate`
    is None for the vast majority of facts (no predicate); item 108 adds the
    first production predicate fact, so this field is no longer vestigial."""
    return {
        "dialect": f.dialect,
        "param": f.param,
        "option_value": f.option_value,
        "value_class": f.value_class.value if f.value_class is not None else None,
        "level": f.level.value,
        "enforcement": f.enforcement.value,
        "boundary": f.boundary.value,
        "condition": f.condition,
        "message": f.message,
        "workaround": f.workaround,
        "upstream_ref": f.upstream_ref,
        "since": f.since,
        "native_errors": [e.__name__ for e in f.native_errors],
        "probe_exempt": f.probe_exempt,
        "predicate": [_clause_dict(c) for c in f.predicate.clauses] if f.predicate is not None else None,
    }


def _cell_dict(oc: OpCoverage) -> dict[str, Any]:
    """One (op, backend) cell — the cell composition §4.6 pins.

    `impl_method` and `impl_protocol` are None iff impl is UNKNOWN. `whole_op`
    is None for non-whole-op cells (no wildcard gate present). `constrained`
    and `contradiction` are derived but INCLUDED so consumers need no §3.4
    precedence knowledge (spec §4.6 <fact>/cell note)."""
    return {
        "impl": oc.impl.value,
        "impl_method": oc.impl_method,
        "impl_protocol": oc.impl_protocol,
        "audited": oc.audited,
        "whole_op": oc.whole_op.value if oc.whole_op is not None else None,
        "constrained": oc.constrained,
        "contradiction": oc.contradiction,
        "selector_counts": {
            "params": oc.selector_counts.params,
            "option_selectors": oc.selector_counts.option_selectors,
            "metadata_selectors": oc.selector_counts.metadata_selectors,
            "value_classes": oc.selector_counts.value_classes,
            "dialects": oc.selector_counts.dialects,
        },
        "constraints": [_fact_dict(f) for f in oc.constraints],
        "residue": [_fact_dict(f) for f in oc.residue],
        "routed": [_fact_dict(f) for f in oc.routed],
        "refinements": [_fact_dict(f) for f in oc.refinements],
    }


def _family_dict(fam: Any) -> dict[str, Any]:
    """One FamilyCoverage: op-name-major, backend display order. `source` and
    `domain` are None for unmapped families (no enum-class-suffix match) —
    these fields are JSON `null`, never omitted."""
    if fam.audit_domain is None:
        source: str | None = None
        domain: str | None = None
    else:
        source, domain = fam.audit_domain[0].value, fam.audit_domain[1].value
    # Group OpCoverages by op identity; the model already emits op-name-major
    # with backend display order, so the existing sort is preserved.
    by_op: dict[Any, list[OpCoverage]] = {}
    for oc in fam.ops:
        by_op.setdefault(oc.op.operation_key, []).append(oc)
    ops_out: list[dict[str, Any]] = []
    for op_key in sorted(by_op, key=lambda k: k.name):
        ocs = by_op[op_key]
        # The three backends in display order; RENDERED_BACKENDS iteration is
        # the same order the model built fam.ops in.
        cells = {oc.backend.value: _cell_dict(oc) for oc in ocs}
        ops_out.append({"op": _op_key(ocs[0].op), "cells": cells})
    return {
        "family": fam.family,
        "source": source,
        "domain": domain,
        "ops": ops_out,
    }


def _scope_dict(scope: Any) -> dict[str, Any]:
    return {"backend": scope.backend.value, "dialect": scope.dialect}


def _segment_dict(segment: Any) -> dict[str, Any]:
    return {
        "module": segment.module,
        "scope": _scope_dict(segment.scope),
        "source": segment.source.value,
        "domain": segment.segment.domain.value,
        "facts": [_fact_dict(fact) for fact in sorted(segment.facts, key=fact_sort_key)],
        "evidence_refs": [
            _captured_address_dict(address) for address in segment.segment.evidence_refs
        ],
        "changes": [
            _captured_address_dict(change.change_ref) for change in segment.segment.changes
        ],
    }


def _evidence_dict(evidence: Any) -> dict[str, Any] | None:
    if evidence is None:
        return None
    return {
        "probe_date": evidence.probe_date,
        "library_versions": [list(pair) for pair in evidence.library_versions],
        "fixtures": list(evidence.fixtures),
    }


def _bundle_dict(bundle: Any) -> dict[str, Any]:
    return {
        "address": _captured_address_dict(bundle.address),
        "backend": bundle.backend.value,
        "source": bundle.source.value,
        "domain": bundle.domain.value,
        "members": [_captured_assertion_dict(member) for member in bundle.members],
        "evidence": _evidence_dict(bundle.evidence),
    }


def _divergence_dict(dv: Any) -> dict[str, Any]:
    """DivergenceFact — backends are verbatim dialect/family-name strings
    (spec §4.6 M-5); the .value rule does NOT apply. operation_keys use the
    {family, op} convention."""
    return {
        "id": dv.id,
        "kind": dv.kind.value,
        "operation_keys": [_op_key(k) for k in dv.operation_keys],
        "backends": list(dv.backends),
        "summary": dv.summary,
        "impact": dv.impact,
        "workaround": dv.workaround,
        "upstream_ref": dv.upstream_ref,
        "since": dv.since,
    }


def _gap_dict(record: Any) -> dict[str, Any]:
    gap = record.payload
    return {
        "inventory": record.key.inventory,
        "target": _capture_value(record.key.target),
        "obligation": record.key.obligation,
        "coverage_scope": (
            {"kind": "inventory_wide"}
            if type(record.key.coverage_scope) is InventoryWide
            else {"kind": "scope", **_scope_dict(record.key.coverage_scope)}
        ),
        "original_key": _capture_value(record.original_key),
        "origins": [_captured_address_dict(origin) for origin in record.origins],
        "reference_context": [
            _captured_address_dict(address) for address in record.reference_context
        ],
        "gap_kind": gap.gap_kind.value,
        "reason": gap.reason,
        "since": gap.since,
        "review_due": (date.fromisoformat(gap.since) + timedelta(days=183)).isoformat(),
    }


def _change_dict(change: Any) -> dict[str, Any]:
    """Diagnostic projection of an AssertionChange, not a lossless codec."""
    return {
        "change_ref": _captured_address_dict(change.change_ref),
        "prior": _captured_assertion_dict(change.prior),
        "disposition": change.disposition.value,
        "recorded_at": change.recorded_at,
        "reason": change.reason,
        "successors": [
            _captured_assertion_dict(successor) for successor in change.successors
        ],
        "evidence_refs": [
            _captured_address_dict(address) for address in change.evidence_refs
        ],
        "fixed_versions": _environment_dict(change.fixed_versions),
    }


def _stamp(report: CoverageReport) -> dict[str, int]:
    """Counts only — the model has no timestamps, so this is the regen-time
    visible-only summary, not a wall-clock stamp."""
    return {
        "segments": len(report.segments),
        "historical_bundles": len(report.bundles),
        "facts": report.stats.facts_total,
        "operations": report.stats.ops_total,
        "implementation_records": sum(report.stats.by_impl.values()),
    }


def _stats_dict(report: CoverageReport) -> dict[str, Any]:
    """Per-backend NESTED under the backend key (plan-review C3 — the model's
    tuple-keyed by_impl Mapping has no legal JSON key form). facts_by_*
    stats are keyed by .value, present-only (matches the model's Mapping,
    not the universe of all enum values — empty is empty, not zero-padded)."""
    backends: dict[str, dict[str, Any]] = {}
    for b in RENDERED_BACKENDS:
        by_impl_nested = {s.value: report.stats.by_impl.get((b, s), 0) for s in ImplState}
        backends[b.value] = {
            "by_impl": by_impl_nested,
            "default_capable": report.stats.default_capable[b],
            "audited_clean": report.stats.audited_clean[b],
            "constrained": report.stats.constrained[b],
            "audited_unknown": report.stats.audited_unknown[b],
        }
    return {
        "backends": backends,
        "contradictions": report.stats.contradictions,
        "ops_total": report.stats.ops_total,
        "facts_by_level": {
            lv.value: report.stats.facts_by_level.get(lv, 0)
            for lv in CapabilityLevel
            if lv in report.stats.facts_by_level
        },
        "facts_by_enforcement": {
            e.value: report.stats.facts_by_enforcement.get(e, 0)
            for e in Enforcement
            if e in report.stats.facts_by_enforcement
        },
        "facts_by_backend": {
            b.value: report.stats.facts_by_backend.get(b, 0)
            for b in RENDERED_BACKENDS
            if b in report.stats.facts_by_backend
        },
        "facts_total": report.stats.facts_total,
    }


def render_json(report: CoverageReport) -> str:
    """Diagnostic JSON projection of the coverage report.

    The change rows expose complete in-memory captures, but this existing report
    projection is not a lossless serialization format. Determinism comes from
    already-sorted model sequences and insertion-ordered dictionaries.
    """
    obj = {
        "stamp": _stamp(report),
        "stats": _stats_dict(report),
        "families": [_family_dict(f) for f in report.families],
        "segments": [_segment_dict(segment) for segment in report.segments],
        "historical_bundles": [_bundle_dict(bundle) for bundle in report.bundles],
        "divergences": [_divergence_dict(dv) for dv in report.divergences],
        "gaps": None if report.gaps is None else [_gap_dict(gap) for gap in report.gaps],
        "changes": [_change_dict(change) for change in reversed(report.changes)],
    }
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def gather_coverage_inputs(*, verification: VerificationSnapshot | None = None) -> dict:
    """Acquire one immutable reporting state and cold historical provenance."""
    from mountainash.core.capabilities.coverage import OpRecord
    from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES
    from mountainash.core.capabilities.evidence.legacy_bundles import BUNDLES
    from mountainash.core.capabilities.gaps import VerificationSnapshot
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    if verification is not None and type(verification) is not VerificationSnapshot:
        raise TypeError("verification requires an explicit VerificationSnapshot")
    facts, segments = CapabilityRegistry._report_inputs()
    keys = list(ExpressionFunctionRegistry.list_all()) + list(RelationOperationRegistry.list_all())
    universe = tuple(
        sorted(
            (OpRecord(key, type(key).__name__) for key in keys),
            key=lambda record: (record.family, record.operation_key.name),
        )
    )
    inputs = dict(
        universe=universe,
        facts=facts,
        segments=segments,
        bundles=BUNDLES,
        divergences=KNOWN_DIVERGENCES,
        gaps=None if verification is None else verification.gaps,
        changes=(
            tuple(change for segment in segments for change in segment.segment.changes)
            + (() if verification is None else verification.changes)
        ),
    )
    inputs["implementations"] = gather_implementation_records(universe)
    return inputs


def _resolve_concrete_owner(leaf: type, name: str) -> type | None:
    """First non-Protocol MRO class defining `name` in vars(); Protocol-suffixed
    classes are stub carriers, not implementations, and are SKIPPED rather than
    terminating the walk - the conformance suite's `_resolve_backend_method`
    convention (spec §3.6 / review C-2, final-review M-3)."""
    for klass in leaf.__mro__:
        if klass.__name__.endswith("Protocol"):
            continue
        if name in vars(klass):
            return klass
    return None


def gather_implementation_records(
    universe: tuple[OpRecord, ...],
) -> tuple[ImplementationRecord, ...]:
    """Derive the implementation axis (spec §3.6): for every universe op, probe
    `protocol_method` / `handler` against the three composed backend leaf
    classes. Returns exactly len(universe) * 3 records (one per backend),
    cardinalially required by the model's multiset ingest guard."""
    from mountainash.core.capabilities.coverage import (
        ImplState,
        ImplementationRecord,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.expressions.backends.expression_systems.polars import (
        PolarsExpressionSystem,
    )
    from mountainash.expressions.backends.expression_systems.narwhals import (
        NarwhalsExpressionSystem,
    )
    from mountainash.expressions.backends.expression_systems.ibis import (
        IbisExpressionSystem,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )
    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.relations.backends.relation_systems.narwhals import (
        NarwhalsRelationSystem,
    )
    from mountainash.relations.backends.relation_systems.ibis import (
        IbisRelationSystem,
    )

    expression_keys = frozenset(ExpressionFunctionRegistry.list_all())
    expr_leaves = {
        CONST_BACKEND.POLARS: PolarsExpressionSystem,
        CONST_BACKEND.NARWHALS: NarwhalsExpressionSystem,
        CONST_BACKEND.IBIS: IbisExpressionSystem,
    }
    rel_leaves = {
        CONST_BACKEND.POLARS: PolarsRelationSystem,
        CONST_BACKEND.NARWHALS: NarwhalsRelationSystem,
        CONST_BACKEND.IBIS: IbisRelationSystem,
    }

    records: list[ImplementationRecord] = []
    for op in universe:
        if op.operation_key in expression_keys:
            defn: Any = ExpressionFunctionRegistry.get(op.operation_key)
            leaves: Any = expr_leaves
        else:
            defn = RelationOperationRegistry.get(op.operation_key)
            leaves = rel_leaves
        protocol_method = defn.protocol_method
        handler = getattr(defn, "handler", None)
        for backend, leaf in leaves.items():
            if protocol_method is not None:
                method_name = protocol_method.__name__
                owner = _resolve_concrete_owner(leaf, method_name)
                if owner is not None:
                    records.append(
                        ImplementationRecord(
                            operation_key=op.operation_key,
                            backend=backend,
                            state=ImplState.IMPLEMENTED,
                            method_name=method_name,
                            protocol_name=owner.__qualname__,
                        )
                    )
                else:
                    records.append(
                        ImplementationRecord(
                            operation_key=op.operation_key,
                            backend=backend,
                            state=ImplState.NOT_IMPLEMENTED,
                            method_name=method_name,
                            protocol_name=protocol_method.__qualname__.rsplit(".", 1)[0],
                        )
                    )
            elif handler is not None:
                records.append(
                    ImplementationRecord(
                        operation_key=op.operation_key,
                        backend=backend,
                        state=ImplState.IMPLEMENTED_VIA_HANDLER,
                        method_name=handler.__qualname__,
                        protocol_name="handler",
                    )
                )
            else:
                records.append(
                    ImplementationRecord(
                        operation_key=op.operation_key,
                        backend=backend,
                        state=ImplState.UNKNOWN,
                        method_name=None,
                        protocol_name=None,
                    )
                )
    return tuple(records)


# Pinned (path, renderer) pairing — the single source of truth for both
# `main()` and the parametrized drift gate, so the gate's failure message
# names the drifted artifact from this same constant (spec §4.6 / review M-4).
# Defined after the three renderer functions so the callables resolve.
_ARTIFACT_RENDERERS: tuple[tuple[str, Callable[[CoverageReport], str]], ...] = (
    ("docs/reference/expression-coverage.md", render_markdown),
    ("docs/reference/expression-coverage-scoped.md", render_scoped),
    ("docs/reference/expression-coverage.json", render_json),
)


def write_coverage_artifacts(base: Path, report: CoverageReport) -> tuple[Path, ...]:
    rendered = tuple((base / rel_path, renderer(report)) for rel_path, renderer in _ARTIFACT_RENDERERS)
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
    for rel_path, _renderer in _ARTIFACT_RENDERERS:
        out = base / rel_path
        if out in changed:
            print(f"wrote {out}")
        else:
            print(f"unchanged {out}")


if __name__ == "__main__":
    main()
