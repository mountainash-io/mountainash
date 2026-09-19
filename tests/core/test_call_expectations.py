"""Case-local expectations must not swallow unrelated or fixture failures."""

from pathlib import Path

import pytest

pytest_plugins = ["pytester"]
pytestmark = pytest.mark.contract


def test_known_call_failure_preserves_xpass_and_unrelated_errors(pytester, monkeypatch):
    """Wrong phase, exception subtype, or successful call cannot satisfy a defect."""
    for name in (
        "COVERAGE_PROCESS_START",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_FILE",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
        "COV_CORE_CONTEXT",
    ):
        monkeypatch.delenv(name, raising=False)
    tests_root = str(Path(__file__).resolve().parents[1])
    pytester.makeconftest(f"import sys\nsys.path.insert(0, {tests_root!r})\n")
    pytester.makepyfile(
        test_cases="""
import pytest
from fixtures.call_expectations import expect_call_failure


class DeclaredError(Exception):
    pass


class DerivedError(DeclaredError):
    pass


@pytest.mark.parametrize("selected", [True, False])
def test_call(selected):
    with expect_call_failure(
        when=selected, reason="known wrong result", errors=(AssertionError,)
    ):
        assert 1 == 2


def test_unrelated_error():
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        raise RuntimeError("unrelated execution error")


def test_subclass_error():
    with expect_call_failure(reason="known native issue", errors=(DeclaredError,)):
        raise DerivedError("different native error subtype")


def test_corrected_result():
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        assert 2 + 2 == 4


@pytest.fixture
def broken_setup():
    raise AssertionError("unrelated setup error")


def test_setup_error(broken_setup):
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        assert 1 == 2


@pytest.fixture
def broken_teardown():
    yield
    raise AssertionError("unrelated teardown error")


def test_teardown_error(broken_teardown):
    with expect_call_failure(reason="known wrong result", errors=(AssertionError,)):
        assert 1 == 2
"""
    )
    result = pytester.runpytest_subprocess("-q", "--tb=short")
    result.assert_outcomes(xfailed=2, failed=4, errors=2)
    result.stdout.fnmatch_lines(
        [
            "*unrelated setup error*",
            "*unrelated teardown error*",
            "*unrelated execution error*",
            "*different native error subtype*",
            "*XPASS(strict)*",
        ]
    )
