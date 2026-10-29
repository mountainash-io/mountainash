"""Coverage artifact wiring tests independent of installed-package imports."""

from __future__ import annotations

import mountainash.core.capabilities.render_markdown as render_module
from mountainash.core.capabilities.render_markdown import _ARTIFACT_RENDERERS, write_coverage_artifacts


def test_coverage_renders_all_outputs_before_first_write(tmp_path, monkeypatch):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("old first")
    second.write_text("old second")

    def render_first(report):
        return "new first"

    def render_second(report):
        raise RuntimeError("second renderer failed")

    monkeypatch.setattr(render_module, "_ARTIFACT_RENDERERS", (("first.txt", render_first), ("second.txt", render_second)))

    try:
        write_coverage_artifacts(tmp_path, object())
    except RuntimeError as error:
        assert str(error) == "second renderer failed"
    else:
        raise AssertionError("write must not begin until every artifact is rendered")
    assert first.read_text() == "old first"
    assert second.read_text() == "old second"


def test_artifact_paths_remain_the_public_report_interface():
    assert tuple(path for path, _ in _ARTIFACT_RENDERERS) == (
        "docs/reference/expression-coverage.md",
        "docs/reference/expression-coverage-scoped.md",
        "docs/reference/expression-coverage.json",
    )
