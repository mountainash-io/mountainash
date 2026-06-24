"""Map changed source paths to pytest selectors (deterministic, fail-safe)."""
from __future__ import annotations

import dataclasses
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_REG = ROOT / "tests" / "selection" / "selectors.yaml"
FULL = ["tests"]


@dataclasses.dataclass
class Registry:
    rules: list[dict]
    cross_cutting: list[str]


def load_registry(path: pathlib.Path | None = None) -> Registry:
    data = yaml.safe_load((path or DEFAULT_REG).read_text())
    return Registry(
        rules=data.get("rules", []),
        cross_cutting=data.get("cross_cutting", []),
    )


def select(changed: list[str], reg: Registry) -> list[str]:
    """Return affected test PATHS (deps unioned), or the full suite (fail-safe).

    Returns plain paths only — never a `-m` filter. The contract tier is run as
    a SEPARATE invocation by the caller, so it is unioned with these paths
    rather than filtering them (a single `-m contract` would drop the affected
    tests). Cross-cutting or unmatched paths → ["tests"] (full).
    """
    if not changed:
        return list(FULL)
    if any(any(c.startswith(cc) or cc in c for cc in reg.cross_cutting) for c in changed):
        return list(FULL)
    selected: list[str] = []
    for c in changed:
        matched = False
        for rule in reg.rules:
            if rule["match"] in c:
                for s in rule["select"]:
                    if s not in selected:
                        selected.append(s)
                matched = True
        if not matched:
            return list(FULL)  # unmapped path → fail-safe full run
    return selected


def _changed_paths(base: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def main() -> int:
    base = "origin/develop"
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1]
    sel = select(_changed_paths(base), load_registry())
    print(" ".join(sel))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
