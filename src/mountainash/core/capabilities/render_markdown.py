"""Deterministic markdown + JSON renderers for the expression coverage report.

Pure over CoverageReport; input gathering + main() live at the bottom
(Task 5). No wall-clock reads anywhere (spec §4.4). The JSON renderer is
spec §4.6 — the machine-readable extract, the third committed artifact.
"""
from __future__ import annotations

import json
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
    is_dialect_scoped_whole_op,  # I-2b cell predicate + scoped-doc subheading
    is_whole_op,  # partition predicate (rev 6)
)
from mountainash.core.capabilities.schema import (
    CapabilityFact,
    CapabilityLevel,
    Enforcement,  # summary stats
)

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND

_ARTIFACT_PATH = "docs/reference/expression-coverage.md"
_SCOPED_ARTIFACT_PATH = "docs/reference/expression-coverage-scoped.md"
_JSON_ARTIFACT_PATH = "docs/reference/expression-coverage.json"
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
            partial = (
                f"◐ partial ({sc.params} params, {sc.option_selectors} option-selectors, "
                f"{sc.value_classes} value-classes, {sc.dialects} dialects)"
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
                parts = [
                    f"{lv} on {','.join(sorted(dialects))}"
                    for lv, dialects in sorted(by_level.items())
                ]
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
        f"Declarations: {len(report.declarations)} · Facts: {report.stats.facts_total} "
        f"· Registered operations: {report.stats.ops_total} "
        f"· Implementation records: {impl_total}",
        "",
        "Scoped deviations (dialect/param/option/value-class) live in "
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
    """Per-op detail holds ONLY function-level (whole-op) facts (spec §4.3
    rev 6). A pointer line under the section header names the scoped doc;
    cells whose facts are all scoped get no main-doc section at all.
    Partition is exact against the scoped doc — every input fact's detail
    body lives in exactly one of the two artifacts (§4.5 M-3)."""
    lines = ["## Per-op detail", ""]
    lines.append(
        "Cells whose facts are all scoped (dialect / parameter / option / "
        "value-class) have no section here — see "
        "[`expression-coverage-scoped.md`](expression-coverage-scoped.md) "
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
            lines.append(
                f"### `{oc.op.operation_key.name}` × {oc.backend.value} "
                f"({oc.op.family})"
            )
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
  detail for every fact with a dialect, parameter, option, or value-class
  selector. The two are byte-disjoint on detail bodies — every input fact
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
        "Scoped deviations — dialect, parameter, option, value-class; "
        "function-level coverage and matrices live in "
        "[`expression-coverage.md`](expression-coverage.md).",
        "",
        f"Declarations: {len(report.declarations)} · Facts: {report.stats.facts_total} "
        f"· Registered operations: {report.stats.ops_total} "
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
            lines.append(
                f"### `{oc.op.operation_key.name}` × {oc.backend.value} "
                f"({oc.op.family})"
            )
            lines.append("")
            dsw = tuple(f for f in scoped if is_dialect_scoped_whole_op(f))
            remaining = tuple(
                f for f in scoped if not is_dialect_scoped_whole_op(f)
            )
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
# JSON renderer — spec §4.6 (rev 6).
# The machine-readable extract: the FULL model, not a summary. No option
# collapse, no markdown glyphs, no per-field prose; every fact row uncollapsed
# and every value serializable as a plain JSON value. Determinism rests on
# insertion order (spec §4.4 M-6): every dict is populated by iterating
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


def _fact_dict(f: CapabilityFact) -> dict[str, Any]:
    """Serialize one CapabilityFact as a dict (spec §4.6 <fact> shape).

    `option_value` is None -> JSON `null`; `native_errors=()` -> JSON `[]`.
    `value_class` is None -> JSON `null`; the level/enforcement/boundary
    are serialized by .value. `condition`/`message` are always strings (the
    model's default is "" so absent-prose is "" not null here)."""
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


def _evidence_dict(evidence: Any) -> dict[str, Any] | None:
    """ProbeEvidence -> dict; null preserves the absence-of-evidence signal
    (vs. a `{}` empty record, which would mean 'evidence exists but is empty')."""
    if evidence is None:
        return None
    return {
        "probe_date": evidence.probe_date,
        "library_versions": [list(pair) for pair in evidence.library_versions],
        "fixtures": list(evidence.fixtures),
    }


def _declaration_dict(d: Any) -> dict[str, Any]:
    """One CapabilityDeclaration — carries its facts in the canonicalized order
    the model canonicalized at ingest (spec §4.4 I-3); this is what makes
    declarations JSON-recoverable per §4.6 / plan-review C2."""
    return {
        "backend": d.backend.value,
        "source": d.source.value,
        "domain": d.domain.value,
        "evidence": _evidence_dict(d.evidence),
        "facts": [_fact_dict(f) for f in d.facts],
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


def _gap_dict(g: Any) -> dict[str, Any]:
    """KnownGap + review_due = since + 183 days (spec §4.3 rule 7)."""
    return {
        "gap_kind": g.gap_kind.value,
        "reason": g.reason,
        "since": g.since,
        "review_due": (date.fromisoformat(g.since) + timedelta(days=183)).isoformat(),
    }


def _retired_dict(r: Any) -> dict[str, Any]:
    """RetiredFact — emitted newest-first (spec §4.3 rule 8); the model sorts
    ascending, the renderer reverses, mirroring the markdown retirements section."""
    return {
        "operation_key": _op_key(r.operation_key),
        "param": r.param,
        "backend": r.backend.value,
        "dialect": r.dialect,
        "option_value": r.option_value,
        "value_class": r.value_class.value if r.value_class is not None else None,
        "level": r.level.value,
        "since": r.since,
        "retired_on": r.retired_on,
        "fixed_in_versions": [list(pair) for pair in r.fixed_in_versions],
        "upstream_ref": r.upstream_ref,
        "note": r.note,
    }


def _stamp(report: CoverageReport) -> dict[str, int]:
    """Counts only — the model has no timestamps, so this is the regen-time
    visible-only summary, not a wall-clock stamp."""
    return {
        "declarations": len(report.declarations),
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
        by_impl_nested = {
            s.value: report.stats.by_impl.get((b, s), 0) for s in ImplState
        }
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
            for lv in CapabilityLevel if lv in report.stats.facts_by_level
        },
        "facts_by_enforcement": {
            e.value: report.stats.facts_by_enforcement.get(e, 0)
            for e in Enforcement if e in report.stats.facts_by_enforcement
        },
        "facts_by_backend": {
            b.value: report.stats.facts_by_backend.get(b, 0)
            for b in RENDERED_BACKENDS if b in report.stats.facts_by_backend
        },
        "facts_total": report.stats.facts_total,
    }


def render_json(report: CoverageReport) -> str:
    """Spec §4.6 — the canonical JSON export of the FULL model.

    Determinism: every dict is built by iterating already-sorted sequences;
    `sort_keys=False` (insertion order is the contract — review M-6). Every
    value is serializable as plain JSON: enum members by `.value`, dates as
    ISO strings, absent optionals as `null`, empty collections as `[]`. No
    option-collapse — the extract carries every fact row uncollapsed (the
    markdown's collapse is a readability device, not a model property)."""
    obj = {
        "stamp": _stamp(report),
        "stats": _stats_dict(report),
        "families": [_family_dict(f) for f in report.families],
        "declarations": [_declaration_dict(d) for d in report.declarations],
        "divergences": [_divergence_dict(dv) for dv in report.divergences],
        "gaps": [_gap_dict(g) for g in report.gaps],
        "retired": [_retired_dict(r) for r in reversed(report.retired)],
    }
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


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
