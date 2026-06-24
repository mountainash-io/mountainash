"""Closed-by-default taxonomy audit.

Asserts every test resolves to exactly one tier and every used marker is
registered. Emits a module×tier report (counts are informational only).
"""
from __future__ import annotations

import configparser
import dataclasses
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from selection.tiers import TIERS, resolve_tier  # noqa: E402

# Markers registered in pytest.ini that intentionally have no current use.
# Format: name -> "reason (Since YYYY-MM-DD)". Keep empty unless justified.
KNOWN_UNUSED_MARKERS: dict[str, str] = {
    "argument_types": "Applied programmatically by tests/expressions/argument_types/conftest.py via item.add_marker(); not detectable by static @pytest.mark scan (Since 2026-06-24)",
    "slow": "Reserved taxonomy flag — spec Global Constraints; orthogonal flag not yet applied to any test (Since 2026-06-24)",
    "perf": "Reserved taxonomy flag — spec Global Constraints; used by Task 9 merge-queue CI job (-m 'not perf'); not yet applied to any test (Since 2026-06-24)",
}


@dataclasses.dataclass
class AuditResult:
    untagged: list[str]
    unregistered_markers: set[str]
    unused_registered: set[str]
    matrix: dict[tuple[str, str], int]


def _coverage_free_env() -> dict[str, str]:
    # Strip coverage subprocess hooks so a collect-only `pytest` child does not
    # write statement-mode coverage data that can't combine with the parent's
    # branch data (pytest-cov + parallel=true sets COVERAGE_PROCESS_START).
    env = dict(os.environ)
    env.pop("COVERAGE_PROCESS_START", None)
    env.pop("COVERAGE_FILE", None)
    return env


def _collect_nodeids() -> list[str]:
    proc = subprocess.run(
        ["python", "-m", "pytest", "tests", "--co", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, env=_coverage_free_env(),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"pytest collection failed (exit {proc.returncode}); refusing to audit "
            f"a partial suite.\n{proc.stderr[-2000:]}"
        )
    return [ln.strip() for ln in proc.stdout.splitlines() if "::" in ln]


def _registered_markers() -> set[str]:
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / "pytest.ini")
    block = cfg.get("pytest", "markers", fallback="")
    return {ln.split(":", 1)[0].strip() for ln in block.splitlines() if ":" in ln}


def _used_markers(nodeids: list[str]) -> set[str]:
    # Heuristic static scan of @pytest.mark.<name> across the test tree.
    used = set()
    pat = re.compile(r"@pytest\.mark\.([a-z_]+)|pytest\.mark\.([a-z_]+)")
    for p in (ROOT / "tests").rglob("test_*.py"):
        for m in pat.finditer(p.read_text()):
            used.add(m.group(1) or m.group(2))
    used.discard("parametrize")  # builtin
    used.discard("xfail")        # builtin
    used.discard("skipif")       # builtin
    used.discard("skip")         # builtin
    return used


def _module_of(nodeid: str) -> str:
    parts = nodeid.split("/")
    return parts[1] if len(parts) > 1 else "?"


def audit(nodeids: list[str] | None = None) -> AuditResult:
    nodeids = nodeids if nodeids is not None else _collect_nodeids()
    untagged: list[str] = []
    matrix: dict[tuple[str, str], int] = {}
    for nid in nodeids:
        tier = resolve_tier(nid)
        if tier is None:
            untagged.append(nid)
            continue
        key = (_module_of(nid), tier)
        matrix[key] = matrix.get(key, 0) + 1
    used = _used_markers(nodeids)
    registered = _registered_markers()
    unregistered = used - registered
    unused_registered = registered - used - set(KNOWN_UNUSED_MARKERS)
    return AuditResult(untagged, unregistered, unused_registered, matrix)


def _print_report(r: AuditResult) -> None:
    print("== module × tier ==")
    for (mod, tier), n in sorted(r.matrix.items()):
        print(f"  {mod:18} {tier:14} {n}")
    print(f"untagged: {len(r.untagged)}")
    print(f"unregistered markers: {sorted(r.unregistered_markers)}")
    print(f"unused registered markers: {sorted(r.unused_registered)}")


def main() -> int:
    strict = "--strict" in sys.argv
    r = audit()
    _print_report(r)
    if strict and (r.untagged or r.unregistered_markers or r.unused_registered):
        print("FAIL: taxonomy not closed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
