"""Focused contracts for the argument-matrix's spine-derived xfail expectations.

These tests pin the mechanism `_test_template.py` uses to derive strict xfail
markers from the exact bound AST each matrix cell compiles — see backlog
arg-matrix-xfail-blind-to-value-class-facts and spec
2026-08-09-argument-matrix-value-class-facts-design.
"""
from __future__ import annotations

import pytest

from expressions.argument_types.conftest import ALL_BACKENDS, make_df, matrix_identity


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_matrix_identity_matches_production_backend_detection(backend: str) -> None:
    from tests.fixtures.capability_gating import resolve_identity

    df = make_df({"x": [1]}, backend)
    assert matrix_identity(backend) == resolve_identity(df)
