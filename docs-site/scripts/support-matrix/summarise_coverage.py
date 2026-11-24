"""Deterministic summary of the generated capability coverage report and divergences catalogue.

Inputs (all produced by the package's own generators, see generate.sh; GEN is the output directory given as argv[1]):
  gen/docs/reference/expression-coverage.json   (python -m mountainash.core.capabilities.render_markdown --output gen)
  gen/known-divergences.md                       (scripts/generate_divergences_catalog.py --report-file ...)
  tests/fixtures/backend_registry.py             (cross-backend test registry, for the test-suite column)

Output: markdown fragments written to gen/summary/*.md, inserted verbatim into chapter 16.

Text normalisation applied to generated strings (and nothing else):
  * " (backlog N)" suffixes are removed from messages (internal tracker references);
  * an em dash or en dash surrounded by spaces becomes "; " (house style forbids dashes);
  * "|" is escaped for table cells.
Counts are never edited.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = Path(sys.argv[1]).resolve()
REPO = HERE.parents[2]
OUT = GEN / "summary"

FAMILY_ORDER = ["polars", "narwhals", "ibis"]
LEVELS = ["unsupported", "literal_only", "polymorphic", "expr_capable"]


def clean(text: str) -> str:
    text = re.sub(r"\s*\(backlog \d+\)", "", text)
    text = re.sub(r"\s[–—]\s", "; ", text)
    text = text.replace("\\|", "|").replace("|", "\\|")
    return text.replace("\n", " ")


def load_report() -> dict:
    return json.loads((GEN / "docs/reference/expression-coverage.json").read_text())


def test_registry() -> tuple[set[str], set[str]]:
    """Dialects exercised by the full cross-backend suite and by the transfer matrix only."""
    sys.path.insert(0, str(REPO / "tests"))
    from fixtures.backend_registry import MATRIX_BACKENDS, REGISTRY  # noqa: E402

    from mountainash.core.backend_detection import native_identity

    def dialect(name, spec):
        table = spec.build({"x": [1]}, f"probe_{name.replace('-', '_')}")
        return native_identity(table).dialect

    full = {dialect(n, s) for n, s in REGISTRY.items()}
    matrix = {dialect(n, s) for n, s in MATRIX_BACKENDS.items() if n not in REGISTRY} - full
    return full, matrix


def scope_key(record: dict) -> tuple[str, str | None]:
    return record["scope"]["backend"], record["scope"]["dialect"]


def scopes(report: dict) -> list[tuple[str, str | None]]:
    from mountainash.core.capabilities import KNOWN_DIALECTS

    rows = []
    for family in FAMILY_ORDER:
        rows.append((family, None))
        members = [d for f, ds in KNOWN_DIALECTS.items() if f.value == family for d in ds]
        rows.extend((family, d) for d in sorted(members))
    return rows


def dialect_table(report: dict, full: set, matrix: set) -> str:
    segs = collections.Counter(scope_key(s) for s in report["segments"])
    info = collections.Counter((scope_key(i), i["layer"], i["level"]) for i in report["information"])
    gates = collections.Counter(
        scope_key(p) for p in report["policies"] if p["consumer"] == "gate" and p["action"] == "block"
    )
    others = collections.defaultdict(collections.Counter)
    for p in report["policies"]:
        if not (p["consumer"] == "gate" and p["action"] == "block"):
            others[scope_key(p)][f"{p['consumer'].replace('_', ' ')}"] += 1
    lines = [
        "| Family | Dialect | Cross-backend test suite | Declaration segments | Native information | Public information | Gate refusals | Other policies |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for family, dialect in scopes(report):
        key = (family, dialect)
        if dialect is None:
            suite = "n/a"
        elif dialect in full:
            suite = "full suite"
        elif dialect in matrix:
            suite = "transfer matrix only"
        else:
            suite = "not in test registry"
        other = ", ".join(f"{name} {count}" for name, count in sorted(others[key].items())) or "0"
        cells = [family, dialect or "family-wide", suite, str(segs[key])]
        cells += [" / ".join(str(info[(key, layer, level)]) for level in LEVELS) for layer in ("native", "public")]
        cells += [str(gates[key]), other]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def implementation_table(report: dict) -> str:
    lines = [
        f"Registered operations: {report['stamp']['operations']}",
        "",
        "| Family | implemented | implemented via handler | not implemented | unknown |",
        "| --- | --- | --- | --- | --- |",
    ]
    for family in FAMILY_ORDER:
        s = report["stats"]["backends"][family]
        lines.append(
            f"| {family} | {s['implemented']} | {s['implemented_via_handler']} | {s['not_implemented']} | {s['unknown']} |"
        )
    return "\n".join(lines) + "\n"


def domain_table(report: dict) -> str:
    domain_of = {f["family"]: (f["domain"] or "unclassified") for f in report["families"]}
    ops = collections.Counter()
    for f in report["families"]:
        ops[domain_of[f["family"]]] += len(f["ops"])
    info = collections.Counter(
        (domain_of.get(i["operation"]["family"], "unclassified"), i["scope"]["backend"]) for i in report["information"]
    )
    gates = collections.Counter(
        (domain_of.get(p["operation"]["family"], "unclassified"), p["scope"]["backend"])
        for p in report["policies"] if p["consumer"] == "gate" and p["action"] == "block"
    )
    header = "| Domain | Registered operations | " + " | ".join(
        f"{f}: information / gate refusals" for f in FAMILY_ORDER
    ) + " |"
    lines = [header, "| --- | --- | " + " | ".join("---" for _ in FAMILY_ORDER) + " |"]
    for domain in sorted(ops):
        cells = [domain, str(ops[domain])]
        cells += [f"{info[(domain, f)]} / {gates[(domain, f)]}" for f in FAMILY_ORDER]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def condition(selector: dict, subject: str) -> str:
    kind, value = selector["kind"], selector["value"]
    if kind == "unconditioned":
        return "always"
    if kind == "exact":
        return f"`{subject}` = `{value}`"
    if kind == "value_class":
        return f"`{subject}` is {value}"
    if kind == "predicate":
        parts = []
        for clause in value["clauses"]:
            op = clause["op"]["value"].replace("_", " ")
            operand = clause["operand"]
            parts.append(f"`{clause['path']}` {op}" + ("" if operand is None else f" `{operand}`"))
        return " and ".join(parts)
    return kind


def applies(applicability: dict) -> str:
    regions = applicability.get("regions")
    if not regions:
        return "any version"
    out = []
    for region in regions:
        out.append(", ".join(f"{c['name']}{c['specifier']}" for c in region["constraints"]))
    return "; ".join(out)


def policy_details(report: dict) -> str:
    by_scope = collections.defaultdict(list)
    for p in report["policies"]:
        by_scope[scope_key(p)].append(p)
    lines = []
    for family, dialect in scopes(report):
        records = by_scope.get((family, dialect))
        if not records:
            continue
        records.sort(key=lambda p: (p["consumer"] != "gate", p["operation"]["family"], p["operation"]["op"], p["subject"], json.dumps(p["selector"], sort_keys=True)))
        gates = sum(1 for p in records if p["consumer"] == "gate")
        lines.append(f'??? note "{dialect or family} (gate refusals: {gates}; other policies: {len(records) - gates})"')
        lines.append("")
        lines.append("    | Operation | Consumer / action | Condition | Applies when | Message |")
        lines.append("    | --- | --- | --- | --- | --- |")
        for p in records:
            op = f"`{p['operation']['family']}.{p['operation']['op']}`"
            ca = f"{p['consumer'].replace('_', ' ')} / {p['action'].replace('_', ' ')}"
            lines.append(
                f"    | {op} | {ca} | {clean(condition(p['selector'], p['subject']))} | {clean(applies(p['applicability']))} | {clean(p['message'])} |"
            )
        lines.append("")
    return "\n".join(lines)


def divergences() -> tuple[str, str]:
    text = (GEN / "known-divergences.md").read_text()
    total = re.search(r"Illustrative examples: \*\*(\d+)\*\*", text).group(1)
    entries = re.findall(r"^## (\S+)/(\S+) — (.*)$", text, re.M)
    targets = re.findall(r"^Target: `([^`]*)`$", text, re.M)
    assert len(entries) == len(targets) == int(total), (len(entries), len(targets), total)
    per_scope = collections.OrderedDict()
    raw = collections.Counter()
    for (family, dialect, title), target in zip(entries, targets):
        raw[(family, dialect)] += 1
        per_scope.setdefault((family, dialect), collections.OrderedDict()).setdefault(clean(title), set()).add(target)
    order = {f: i for i, f in enumerate(FAMILY_ORDER)}
    keys = sorted(per_scope, key=lambda k: (order[k[0]], k[1] != "family", k[1]))
    summary = [f"Illustrated divergences: {total}", "", "| Family | Scope | Illustrations | Distinct descriptions |", "| --- | --- | --- | --- |"]
    details = []
    for key in keys:
        titles = per_scope[key]
        count = raw[key]
        scope = "family-wide" if key[1] == "family" else key[1]
        summary.append(f"| {key[0]} | {scope} | {count} | {len(titles)} |")
        details.append(f'??? note "{scope if scope != "family-wide" else key[0] + ", family-wide"} (descriptions: {len(titles)})"')
        details.append("")
        details.append("    | Description | Distinct operations illustrated |")
        details.append("    | --- | --- |")
        for title in sorted(titles):
            details.append(f"    | {title} | {len(titles[title])} |")
        details.append("")
    return "\n".join(summary) + "\n", "\n".join(details)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = load_report()
    full, matrix = test_registry()
    (OUT / "dialects.md").write_text(dialect_table(report, full, matrix))
    (OUT / "implementation.md").write_text(implementation_table(report))
    (OUT / "domains.md").write_text(domain_table(report))
    (OUT / "policies.md").write_text(policy_details(report))
    summary, details = divergences()
    (OUT / "divergences-summary.md").write_text(summary)
    (OUT / "divergences-details.md").write_text(details)
    for path in sorted(OUT.iterdir()):
        print(path.name, len(path.read_text().splitlines()), "lines")


if __name__ == "__main__":
    main()
