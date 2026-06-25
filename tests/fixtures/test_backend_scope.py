pytest_plugins = ["pytester"]

import pytest
from fixtures.backend_registry import (
    REGISTRY,
    PR_BACKENDS,
    ALL_BACKENDS,
    resolve_backend_scope,
    deselect_backend_under_scope,
)

pytestmark = pytest.mark.contract


def test_full_scope_is_entire_registry():
    assert resolve_backend_scope("full") == list(REGISTRY)


def test_pr_scope_is_one_per_family():
    pr = resolve_backend_scope("pr")
    assert pr == ["polars", "narwhals-polars", "ibis-duckdb"]
    families = {REGISTRY[name].family for name in pr}
    assert families == {"polars-eager", "narwhals", "ibis"}


def test_pr_backends_constant_matches_resolver():
    assert PR_BACKENDS == resolve_backend_scope("pr")


def test_unknown_scope_falls_back_to_full():
    assert resolve_backend_scope("nonsense") == list(REGISTRY)


def test_all_backends_is_full_canonical_registry():
    # ALL_BACKENDS is the canonical full list (always 9) regardless of scope —
    # scoping is applied by DESELECTION at collection, not by shrinking this.
    assert ALL_BACKENDS == list(REGISTRY)


def test_deselect_logic_pr_scope():
    # In 'pr' scope: registered backends outside PR_BACKENDS are deselected;
    # PR backends and non-backend / unknown params are always kept (fail-safe).
    assert deselect_backend_under_scope("polars-lazy", "pr") is True
    assert deselect_backend_under_scope("ibis-sqlite", "pr") is True
    assert deselect_backend_under_scope("polars", "pr") is False
    assert deselect_backend_under_scope("narwhals-polars", "pr") is False
    assert deselect_backend_under_scope("ibis-duckdb", "pr") is False
    # full scope keeps everything; unknown/None params never deselected
    assert deselect_backend_under_scope("polars-lazy", "full") is False
    assert deselect_backend_under_scope("not-a-backend", "pr") is False
    assert deselect_backend_under_scope(None, "pr") is False


def test_pr_scope_deselects_out_of_scope_backend_params(pytester, monkeypatch):
    # End-to-end: with the deselection hook active, a cross-backend matrix
    # parametrized over the full ALL_BACKENDS runs only the PR backends, and a
    # backend-specific xfail stays attached to the right (kept) param — whole
    # items are dropped, params are never reindexed, so no misattribution.
    # Strip coverage subprocess hooks so the inner pytest child does not write
    # statement-mode coverage data that can't combine with the parent's branch
    # data. pytest-cov enables subprocess coverage via COV_CORE_* (embed/.pth)
    # and/or COVERAGE_PROCESS_START; clear the full set.
    for _k in (
        "COVERAGE_PROCESS_START", "COVERAGE_PROCESS_CONFIG", "COVERAGE_FILE",
        "COV_CORE_SOURCE", "COV_CORE_CONFIG", "COV_CORE_DATAFILE", "COV_CORE_CONTEXT",
    ):
        monkeypatch.delenv(_k, raising=False)
    tests_dir = str(__import__("pathlib").Path(__file__).parent.parent)
    pytester.makeconftest(
        """
import sys; sys.path.insert(0, r'%s')
import os, sys as _sys
for _i, _a in enumerate(_sys.argv):
    if _a == '--ma-backend-scope' and _i + 1 < len(_sys.argv):
        os.environ['MA_BACKEND_SCOPE'] = _sys.argv[_i + 1]
    elif _a.startswith('--ma-backend-scope='):
        os.environ['MA_BACKEND_SCOPE'] = _a.split('=', 1)[1]

def pytest_addoption(parser):
    parser.addoption('--ma-backend-scope', action='store', default=None,
        choices=['pr', 'full'], help='Backend matrix scope')

def pytest_collection_modifyitems(config, items):
    from fixtures.backend_registry import partition_items_by_scope
    kept, des = partition_items_by_scope(
        items, os.environ.get('MA_BACKEND_SCOPE', 'full'))
    if des:
        config.hook.pytest_deselected(items=des)
        items[:] = kept
""" % tests_dir
    )
    pytester.makepyfile(
        """
        import pytest
        from fixtures.backend_registry import ALL_BACKENDS

        @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
        def test_matrix(backend_name):
            if backend_name == "ibis-duckdb":
                pytest.xfail("known: ibis-duckdb")
            assert backend_name
        """
    )
    result = pytester.runpytest_subprocess("--ma-backend-scope", "pr", "-q")
    # 3 PR backends kept (6 deselected): polars + narwhals-polars pass,
    # ibis-duckdb xfails. The xfail stayed attached to ibis-duckdb specifically.
    result.assert_outcomes(passed=2, xfailed=1, deselected=6)
