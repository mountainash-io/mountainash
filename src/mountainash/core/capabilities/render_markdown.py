"""Deterministic markdown renderer for the expression coverage report.

Pure over CoverageReport; input gathering + main() live at the bottom
(Task 5). No wall-clock reads anywhere (spec §4.4).
"""
from __future__ import annotations

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    CoverageReport,
    CoverageState,
    OpCoverage,
    fact_sort_key,  # canonical order
)
from mountainash.core.capabilities.schema import (
    CapabilityFact,
    CapabilityLevel,
    Enforcement,  # summary stats
)

_ARTIFACT_PATH = "docs/reference/expression-coverage.md"
_REGEN_CMD = "hatch -e test run python -m mountainash.core.capabilities.render_markdown"

_LEGEND = """\
Legend — cell states:

- `✅` **DECLARED_CLEAN** — at least one capability declaration covers this
  op's (backend, source, domain) and no constraining fact exists for the op.
  Scope of the claim: the probe wave declared the backend×domain surface and
  recorded nothing against this op. Declarations carry no per-op probe
  manifest, so this is domain-wave-level evidence, not proof the specific op was exercised.
- `◐ partial (…)` / `✗ unsupported` / `poly` — **CONSTRAINED**: at least one
  GATE constraint or runtime residue fact applies (counts are distinct
  selector keys, never raw fact counts).
- `—` **UNDECLARED** — no declaration covers the coordinates; absence of
  facts means nothing here.
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
    if oc.state is CoverageState.UNDECLARED:
        return "—"
    status: list[str] = []
    if oc.whole_op is CapabilityLevel.UNSUPPORTED:
        status.append("✗ unsupported")
    elif oc.whole_op is CapabilityLevel.POLYMORPHIC:
        status.append("poly")
    sc = oc.selector_counts
    if any((sc.params, sc.option_selectors, sc.value_classes, sc.dialects)):
        status.append(
            f"◐ partial ({sc.params} params, {sc.option_selectors} option-selectors, "
            f"{sc.value_classes} value-classes, {sc.dialects} dialects)"
        )
    text = " + ".join(status) if status else "✅"  # spec §3.5: `poly + ◐ partial (…)`
    notes: list[str] = []
    if oc.routed:
        notes.append("↻ routed")
    if oc.residue:
        notes.append("⚠ runtime")
    if oc.refinements:
        dialects = ", ".join(sorted({f.dialect for f in oc.refinements if f.dialect}))
        notes.append(f"✓ dialect-verified: {dialects}")  # spec §3.4 footnote form
    return " ".join([text, *notes])


def _header(report: CoverageReport) -> list[str]:
    return [
        "# Expression Coverage",
        "",
        "<!-- GENERATED FILE — do not edit by hand. -->",
        f"<!-- Regenerate: {_REGEN_CMD} -->",
        "",
        f"Declarations: {len(report.declarations)} · Facts: {report.stats.facts_total} "
        f"· Registered operations: {report.stats.ops_total}",
        "",
        _LEGEND,
    ]


def _summary(report: CoverageReport) -> list[str]:
    lines = ["## Summary", ""]
    lines.append("| Backend | ✅ declared-clean | ◐ constrained | — undeclared |")
    lines.append("| --- | --- | --- | --- |")
    for b in RENDERED_BACKENDS:
        row = [str(report.stats.by_state.get((b, s), 0)) for s in CoverageState]
        lines.append(f"| {b.value} | {row[0]} | {row[1]} | {row[2]} |")
    lines.append("")
    lines.append("### Fact statistics")
    lines.append("")
    lines.append("| Axis | Breakdown |")
    lines.append("| --- | --- |")
    level_bits = ", ".join(
        f"{lv.value} {report.stats.facts_by_level[lv]}"
        for lv in CapabilityLevel if lv in report.stats.facts_by_level
    )
    enf_bits = ", ".join(
        f"{e.value} {report.stats.facts_by_enforcement[e]}"
        for e in Enforcement if e in report.stats.facts_by_enforcement
    )
    backend_bits = ", ".join(
        f"{b.value} {report.stats.facts_by_backend[b]}"
        for b in RENDERED_BACKENDS if b in report.stats.facts_by_backend
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
    lines.append("### Audited pairs")
    lines.append("")
    lines.append(
        "| Backend | Source | Domain | Probe date | Library versions | Fixtures |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for d in report.declarations:
        if d.evidence is None:
            probe, versions, fixtures = "—", "—", "—"
        else:
            probe = d.evidence.probe_date
            versions = ", ".join(f"{n} {v}" for n, v in d.evidence.library_versions)
            fixtures = ", ".join(d.evidence.fixtures)
        lines.append(
            f"| {d.backend.value} | {d.source.value} | {d.domain.value} "
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
            cells = " | ".join(
                _cell_text(by_op[op_name][b]) for b in RENDERED_BACKENDS
            )
            lines.append(f"| `{op_name}` | {cells} |")
        lines.append("")
    return lines


def render_markdown(report: CoverageReport) -> str:
    lines: list[str] = []
    lines += _header(report)
    lines += _summary(report)
    lines += _family_matrices(report)
    # Task 5 appends: _unmapped_families, _detail_sections, _divergences,
    # _gaps, _retirements.
    return "\n".join(lines) + "\n"
