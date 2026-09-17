"""The divergence catalogue uses scoped claims, not issue metadata, as authority."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from generate_divergences_catalog import render_catalog

from mountainash.core.capabilities.capture import SourceOrigin
from mountainash.core.capabilities.declarations import (
    DivergenceManifestation,
    Domain,
    FactSource,
    ManifestationKey,
    QualifiedManifestation,
    QualifiedManifestationKey,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import CaptureValue, DivergenceKind, OperationTarget, Scenario
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK


def _claim(dialect, *, issue=None):
    scope = Scope(CONST_BACKEND.IBIS, Dialect(dialect))
    claim = DivergenceManifestation(
        ManifestationKey(OperationTarget(FK.TITLE), Scenario(arguments=(("input", CaptureValue.of("ße")),))),
        DivergenceKind.SEMANTICS,
        CaptureValue.of("SSe"),
        CaptureValue.of("ẞe"),
        "Exact Unicode title differs.",
        "2026-09-17",
        issue=issue,
    )
    origin = SourceOrigin(
        f"mountainash.expressions.backends.capabilities.ibis.dialects.{dialect.replace('-', '_')}.substrait.string",
        scope,
        FactSource.SUBSTRAIT,
        Domain.STRING,
        "manifestations[0]",
    )
    return QualifiedManifestation(QualifiedManifestationKey(scope, claim.key), claim, (origin,))


def test_catalogue_keeps_scopes_and_joins_only_explicit_issue():
    records = (_claim("ibis-duckdb", issue="IB-STR-11"), _claim("ibis-sqlite"))
    issues = [
        {"id": "IB-STR-11", "upstream_issue": "https://example.org/issue/11", "status": "open"},
        {"id": "IB-TYPE-04", "summary": "unbound upstream-watch claim", "status": "open"},
    ]
    output = render_catalog(records, issues)
    assert "ibis-duckdb" in output and "ibis-sqlite" in output
    assert "SSe" in output and "ẞe" in output
    assert output.count("https://example.org/issue/11") == 1
    assert "unbound upstream-watch claim" not in output
    assert "IB-TYPE-04" not in output
    assert render_catalog((), issues).count("Exact Unicode title differs.") == 0


def test_catalogue_rejects_unresolved_or_ambiguous_issue_join():
    records = (_claim("ibis-duckdb", issue="IB-STR-11"),)
    with pytest.raises(ValueError, match="IB-STR-11"):
        render_catalog(records, [])
    with pytest.raises(ValueError, match="duplicate"):
        render_catalog(records, [{"id": "IB-STR-11"}, {"id": "IB-STR-11"}])


def test_catalogue_order_does_not_depend_on_input_order():
    records = (_claim("ibis-duckdb"), _claim("ibis-sqlite"))
    assert render_catalog(records, []) == render_catalog(tuple(reversed(records)), [])
