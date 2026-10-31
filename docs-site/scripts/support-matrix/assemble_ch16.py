"""Fill ch16_template.md with the generated fragments; write chapter 16."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
GEN = Path(sys.argv[1]).resolve()
OUT = HERE.parents[1] / "site/docs/chapters/16-backend-support-and-limits/index.md"
s = (HERE / "ch16_template.md").read_text()
frag = lambda name: (GEN / "summary" / f"{name}.md").read_text().rstrip("\n")
lines = lambda p: str(len(p.read_text().splitlines()))
values = {
    "dialects": frag("dialects"),
    "implementation": frag("implementation"),
    "domains": frag("domains"),
    "policies": frag("policies"),
    "divergences_summary": frag("divergences-summary"),
    "divergences_details": frag("divergences-details"),
    "full_md_lines": lines(GEN / "docs/reference/expression-coverage.md"),
    "full_scoped_lines": lines(GEN / "docs/reference/expression-coverage-scoped.md"),
    "full_json_lines": lines(GEN / "docs/reference/expression-coverage.json"),
    "catalogue_lines": lines(GEN / "known-divergences.md"),
}
for key, value in values.items():
    s = s.replace("{{" + key + "}}", value)
assert "{{" not in s
OUT.write_text(s)
print(OUT, len(s), "bytes")
