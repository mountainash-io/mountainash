"""Tests for the shared categorical-values extraction helper.

Two kinds of tests live here:
- Genuinely RED-first unit tests for ``categorical_values`` (the helper did
  not exist before item 54 — these drive it into existence).
- A characterization (golden-master) test proving the conform call-site swap
  (item 54, task 9) is behavior-preserving: it records the output conform's
  OLD inline extraction produced for identical fixtures and asserts the shared
  helper matches, so a refactor regression shows up as a real failure rather
  than being asserted-away.
"""
from __future__ import annotations

from mountainash.typespec._categorical import categorical_values

# Baseline recorded from conform/expressions.py:958-964's inline extraction
# (pre-refactor, 2026-08-17): simple -> ['a', 'b']; object -> [0, 1];
# mixed -> [0, 'x']. Identical fixtures, asserted equal below.
_BASELINE = {
    "simple": ["a", "b"],
    "object": [{"value": 0, "label": "Low"}, {"value": 1, "label": "High"}],
    "mixed": [{"value": 0, "label": "Low"}, "x"],
}
_BASELINE_OUTPUT = {
    "simple": ["a", "b"],
    "object": [0, 1],
    "mixed": [0, "x"],
}


class TestCategoricalValues:
    def test_simple_form(self):
        assert categorical_values(["a", "b"]) == ["a", "b"]

    def test_object_form(self):
        assert categorical_values(
            [{"value": 0, "label": "Low"}, {"value": 1, "label": "High"}]
        ) == [0, 1]

    def test_mixed_form(self):
        assert categorical_values([{"value": 0, "label": "Low"}, "x"]) == [0, "x"]

    def test_empty(self):
        assert categorical_values([]) == []

    def test_returns_new_list(self):
        cats = ["a", "b"]
        result = categorical_values(cats)
        assert result == ["a", "b"]
        assert result is not cats  # never aliases the input


class TestMatchesConformStage5bBaseline:
    def test_categorical_values_matches_conform_stage_5b_extraction(self):
        """Characterization, NOT new-behavior assertion: the shared helper's
        output must equal what conform's old inline extraction produced for
        the identical fixtures (behavior-preserving refactor proof)."""
        for name, cats in _BASELINE.items():
            assert categorical_values(cats) == _BASELINE_OUTPUT[name], name
