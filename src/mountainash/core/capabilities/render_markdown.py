"""Deterministic markdown renderer for the expression coverage report.

Pure over CoverageReport; input gathering + main() live at the bottom
(Task 5). No wall-clock reads anywhere (spec §4.4).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    CoverageReport,
    ImplementationRecord,
    ImplState,
    OpCoverage,
    OpRecord,
    fact_sort_key,  # canonical order
)
from mountainash.core.capabilities.schema import (
    CapabilityFact,
    CapabilityLevel,
    Enforcement,  # summary stats
)

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND

_ARTIFACT_PATH = "docs/reference/expression-coverage.md"
_REGEN_CMD = "hatch -e test run python -m mountainash.core.capabilities.render_markdown"

_LEGEND = """\
Legend — cell states (by exception):

- `✓` **default-capable** — implemented and clean, no constraining fact. The
  presumption; the majority; not a gap. Routed / dialect-verified annotations
  still append (`✓ ↻ routed`, `✓ ✓ dialect-verified: …`).
- `✓ audited` — same as above, strengthened by a probe wave covering this
  op's (backend, source, domain). **Scope of the claim:** the probe wave
  declared the backend×domain surface and recorded nothing against this op.
  Declarations carry no per-op probe manifest, so this is
  domain-wave-level evidence, not proof the specific op was exercised.
- `✓ᴴ` **implemented via handler** — same as `✓` / `✓ audited`, but reached
  through the visitor's `handler` dispatch path rather than a concrete
  protocol-method override on the backend leaf class (spec §3.6). The `ᴴ`
  superscript marks the dispatch shape, not a coverage grade.
- `◐ partial (…)` / `✗ unsupported` / `poly` — **CONSTRAINED**: at least one
  GATE constraint or runtime residue fact applies (counts are distinct
  selector keys, never raw fact counts).
- `—` **NOT_IMPLEMENTED** — the protocol-method override is absent (or only a
  bare `…` stub on the `*Protocol` carrier) and the cell has no facts and
  no declaration. The only true blank.
- `⚠ contradiction` — `NOT_IMPLEMENTED` AND the cell carries facts, a routed
  or refinement entry, or an applicable declaration. Catalog and registry
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
        if any((sc.params, sc.option_selectors, sc.value_classes, sc.dialects)):
            status.append(
                f"◐ partial ({sc.params} params, {sc.option_selectors} option-selectors, "
                f"{sc.value_classes} value-classes, {sc.dialects} dialects)"
            )
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
        f"Declarations: {len(report.declarations)} · Facts: {report.stats.facts_total} "
        f"· Registered operations: {report.stats.ops_total} "
        f"· Implementation records: {impl_total}",
        "",
        _LEGEND,
    ]


def _summary(report: CoverageReport) -> list[str]:
    lines = ["## Summary", ""]
    lines.append("### Per-backend counts")
    lines.append("")
    lines.append(
        "| Backend | default_capable | audited_clean | constrained "
        "| NOT_IMPLEMENTED | UNKNOWN | ops_total |"
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
    lines.append(f"audited_unknown: "
                 f"{sum(report.stats.audited_unknown.values())}")
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


def _unmapped_families(report: CoverageReport) -> list[str]:
    unmapped = [f for f in report.families if f.audit_domain is None]
    if not unmapped:
        return []
    lines = ["## Unmapped families", "",
             "No declaration domain exists for these enum classes yet; no audit "
             "applies (every cell carries only the implementation axis). "
             "Extending coverage here starts at `classify_domain`/"
             "`_DOMAIN_SUFFIXES` (spec §3.2).", ""]
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
            stamp = (f"{n_ops} ops — all implemented on "
                     f"{len(RENDERED_BACKENDS)}/{len(RENDERED_BACKENDS)} backends")
        else:
            stamp = (f"{n_ops} ops — " + " · ".join(
                f"{by_backend[b]}/{n_ops} {b.value}" for b in RENDERED_BACKENDS))
        lines.append(f"- `{fam.family}` ({stamp}): "
                     + ", ".join(f"`{n}`" for n in names))
    lines.append("")
    return lines


def _fact_detail_row(f: CapabilityFact, values: list[str]) -> str:
    option = _escape(", ".join(values)) if values else "—"  # values are escaped, no code spans
    native = ", ".join(e.__name__ for e in f.native_errors) or "—"
    return (
        f"| {f.dialect or '*'} | {_escape(f.param)} | {option} "
        f"| {f.value_class.value if f.value_class else '—'} "
        f"| {f.level.value} | {f.enforcement.value} | {f.boundary.value} "
        f"| {_escape(f.condition or '—')} | {_escape(f.message or '—')} "
        f"| {_escape(f.workaround or '—')} | {f.upstream_ref or '—'} "
        f"| {f.since or '—'} | {native} | {_escape(f.probe_exempt or '—')} |"
    )


_DETAIL_HEADER = (
    "| Dialect | Param | Option values | Value class | Level | Enforcement "
    "| Boundary | Condition | Message | Workaround | Upstream | Since "
    "| Native errors | Probe-exempt |"
)
_DETAIL_RULE = "| " + " | ".join(["---"] * 14) + " |"


def _detail_sections(report: CoverageReport) -> list[str]:
    lines = ["## Per-op detail", ""]
    wrote_any = False
    for fam in report.families:
        for oc in fam.ops:
            if not oc.all_facts:
                continue
            wrote_any = True
            lines.append(
                f"### `{oc.op.operation_key.name}` × {oc.backend.value} "
                f"({oc.op.family})"
            )
            lines.append("")
            lines.append(_DETAIL_HEADER)
            lines.append(_DETAIL_RULE)
            for f, values in _collapse_groups(oc.all_facts):
                lines.append(_fact_detail_row(f, values))
            lines.append("")
    if not wrote_any:
        lines.append("No facts registered.")
        lines.append("")
    return lines


def _divergences_section(report: CoverageReport) -> list[str]:
    lines = ["## Divergence register", ""]
    if not report.divergences:
        return lines + ["None recorded.", ""]
    lines.append("| Id | Kind | Backends | Operations | Summary | Impact "
                 "| Workaround | Upstream | Since |")
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
    if not report.gaps:
        return lines + ["None recorded.", ""]
    lines.append("| Kind | Reason | Since | Review due |")
    lines.append("| --- | --- | --- | --- |")
    for g in report.gaps:
        due = (date.fromisoformat(g.since) + timedelta(days=183)).isoformat()
        lines.append(
            f"| {g.gap_kind.value} | {_escape(g.reason)} | {g.since} | {due} |"
        )
    lines.append("")
    return lines


def _retirements_section(report: CoverageReport) -> list[str]:
    lines = ["## Retirement changelog", ""]
    if not report.retired:
        return lines + ["None recorded.", ""]
    lines.append("| Retired on | Operation | Param | Backend | Dialect "
                 "| Option value | Value class | Level | Since | Fixed in "
                 "| Upstream | Note |")
    lines.append("| " + " | ".join(["---"] * 12) + " |")
    for r in reversed(report.retired):  # model sorts ascending; render newest-first
        fixed = ", ".join(f"{n} {v}" for n, v in r.fixed_in_versions) or "—"
        lines.append(
            f"| {r.retired_on} | `{r.operation_key.name}` | {_escape(r.param)} "
            f"| {str(r.backend)} | {r.dialect or '—'} | {r.option_value or '—'} "
            f"| {r.value_class.value if r.value_class else '—'} | {r.level.value} "
            f"| {r.since} | {fixed} | {r.upstream_ref or '—'} | {_escape(r.note)} |"
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
    lines += _retirements_section(report)
    return "\n".join(lines) + "\n"


def gather_coverage_inputs() -> dict:
    """Impure input gathering — the only registry-touching code (spec §4).

    Universe is built first (spec §3.1 / §4.3) and the implementation records
    are derived from it (`gather_implementation_records` is the spec §3.6
    derivation; the model receives them as an explicit input and stays pure).
    """
    from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
    from mountainash.core.capabilities.coverage import OpRecord
    from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES
    from mountainash.core.capabilities.gaps import KNOWN_GAPS
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from mountainash.core.capabilities.retired import RETIRED_FACTS
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    load_all_capability_declarations()
    keys = list(ExpressionFunctionRegistry.list_all()) + list(
        RelationOperationRegistry.list_all()
    )
    universe = tuple(
        sorted(
            (OpRecord(k, type(k).__name__) for k in keys),
            key=lambda r: (r.family, r.operation_key.name),
        )
    )
    inputs = dict(
        universe=universe,
        facts=tuple(CapabilityRegistry.facts()),
        declarations=tuple(CapabilityRegistry.declarations()),
        divergences=KNOWN_DIVERGENCES,
        gaps=KNOWN_GAPS,
        retired=RETIRED_FACTS,
    )
    inputs["implementations"] = gather_implementation_records(universe)
    return inputs


def _resolve_concrete_owner(leaf: type, name: str) -> type | None:
    """First MRO class defining `name` in vars(); Protocol-suffixed classes are
    stub carriers, not implementations (spec §3.6 / review C-2)."""
    for klass in leaf.__mro__:
        if name in vars(klass):
            return None if klass.__name__.endswith("Protocol") else klass
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
                    records.append(ImplementationRecord(
                        operation_key=op.operation_key,
                        backend=backend,
                        state=ImplState.IMPLEMENTED,
                        method_name=method_name,
                        protocol_name=owner.__qualname__,
                    ))
                else:
                    records.append(ImplementationRecord(
                        operation_key=op.operation_key,
                        backend=backend,
                        state=ImplState.NOT_IMPLEMENTED,
                        method_name=method_name,
                        protocol_name=protocol_method.__qualname__.rsplit(".", 1)[0],
                    ))
            elif handler is not None:
                records.append(ImplementationRecord(
                    operation_key=op.operation_key,
                    backend=backend,
                    state=ImplState.IMPLEMENTED_VIA_HANDLER,
                    method_name=handler.__qualname__,
                    protocol_name="handler",
                ))
            else:
                records.append(ImplementationRecord(
                    operation_key=op.operation_key,
                    backend=backend,
                    state=ImplState.UNKNOWN,
                    method_name=None,
                    protocol_name=None,
                ))
    return tuple(records)


def main() -> None:
    from pathlib import Path

    from mountainash.core.capabilities.coverage import build_coverage_report

    report = build_coverage_report(**gather_coverage_inputs())
    out = Path(__file__).resolve().parents[4] / _ARTIFACT_PATH
    out.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
