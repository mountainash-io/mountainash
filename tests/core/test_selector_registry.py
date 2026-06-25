import os
import pathlib
import subprocess
import pytest
from scripts.select_tests import load_registry

pytestmark = pytest.mark.contract

ROOT = pathlib.Path(__file__).resolve().parents[2]
REG = load_registry()


_COV_SUBPROCESS_ENV = (
    "COVERAGE_PROCESS_START", "COVERAGE_PROCESS_CONFIG", "COVERAGE_FILE",
    "COV_CORE_SOURCE", "COV_CORE_CONFIG", "COV_CORE_DATAFILE", "COV_CORE_CONTEXT",
)


def _coverage_free_env() -> dict[str, str]:
    # Strip coverage subprocess hooks so a collect-only `pytest` child does not
    # write statement-mode coverage data that can't combine with the parent's
    # branch data. pytest-cov enables subprocess coverage via COV_CORE_* (its
    # embed/.pth mechanism) and/or COVERAGE_PROCESS_START; clear the full set.
    env = dict(os.environ)
    for _k in _COV_SUBPROCESS_ENV:
        env.pop(_k, None)
    return env


def _collects_at_least_one(path: str) -> bool:
    proc = subprocess.run(
        ["python", "-m", "pytest", path, "--co", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, env=_coverage_free_env(),
    )
    return any("::" in ln for ln in proc.stdout.splitlines())


def test_every_rule_select_path_exists():
    for rule in REG.rules:
        for sel in rule["select"]:
            assert (ROOT / sel).exists(), f"selector points at missing path: {sel}"


def test_every_rule_select_path_collects_at_least_one_test():
    # A3: a selector pointing at a real but empty dir must not pass silently.
    for rule in REG.rules:
        for sel in rule["select"]:
            assert _collects_at_least_one(sel), f"selector collects zero tests: {sel}"


def test_every_top_level_test_dir_is_reachable():
    test_dirs = {p.name for p in (ROOT / "tests").iterdir()
                 if p.is_dir() and not p.name.startswith(("_", "."))}
    reachable = {sel.split("/", 1)[1] for rule in REG.rules for sel in rule["select"]
                 if sel.startswith("tests/")}
    # 'fixtures'/'selection' are cross-cutting (always full); contract tier
    # covers core/alignment/graph regardless of path selection.
    always_full = {"fixtures", "selection"}
    contract_covered = {"core", "alignment", "graph", "scripts"}
    unreachable = test_dirs - reachable - always_full - contract_covered
    assert not unreachable, f"test dirs not reachable from any selector: {unreachable}"
