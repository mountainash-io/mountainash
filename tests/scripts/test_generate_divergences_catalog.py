"""Render-only examples do not become executable or verified catalogue claims."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from generate_divergences_catalog import render_catalog

from mountainash.core.capabilities.capture import SourceOrigin
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, Domain, FactSource,
    QualifiedInformation, QualifiedInformationKey,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import CapabilityLevel, InformationKind, InformationLayer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK


def _information(dialect, *, issue=None, kinds=frozenset()):
    scope = Scope(CONST_BACKEND.IBIS, Dialect(dialect))
    assertion = CapabilityInformation(
        CapabilityKey(FK.TITLE, "*"),
        InformationLayer.NATIVE,
        CapabilityLevel.EXPR_CAPABLE,
        "2026-09-17",
        "Native Unicode title casing differs.",
        issue=issue,
        kinds=kinds,
    )
    origin = SourceOrigin(
        f"mountainash.expressions.backends.capabilities.ibis.dialects.{dialect.replace('-', '_')}.substrait.string",
        scope, FactSource.SUBSTRAIT, Domain.STRING, "information[0]",
    )
    return QualifiedInformation(QualifiedInformationKey(scope, assertion.key, assertion.layer), assertion, (origin,))


def _example(dialect, *, issue=None):
    example = {
        "backend": "ibis",
        "dialect": dialect,
        "target": "FKEY_SUBSTRAIT_SCALAR_STRING.TITLE",
        "title": "Unicode title casing",
        "text": 'Input: "ße"\nReference result: "SSe"\nContrasting result: "ẞe"',
    }
    if issue is not None:
        example["issue"] = issue
    return example


def test_catalogue_preserves_scope_and_joins_only_explicit_issue():
    information = (_information("ibis-duckdb", issue="IB-STR-11"), _information("ibis-sqlite"))
    examples = (_example("ibis-duckdb", issue="IB-STR-11"), _example("ibis-sqlite"))
    issues = [
        {"id": "IB-STR-11", "upstream_issue": "https://example.org/issue/11", "status": "open"},
        {"id": "IB-TYPE-04", "summary": "unbound upstream-watch claim", "status": "open"},
    ]
    output = render_catalog(information, (), examples, issues)
    assert "ibis-duckdb" in output and "ibis-sqlite" in output
    assert "SSe" in output and "ẞe" in output
    assert "Native Unicode title casing differs." in output
    assert output.count("https://example.org/issue/11") == 1
    assert "unbound upstream-watch claim" not in output
    assert "IB-TYPE-04" not in output


def test_catalogue_renders_multiple_information_kinds_once_in_sorted_order():
    information = (
        _information("ibis-duckdb", kinds=frozenset({InformationKind.SEMANTICS, InformationKind.PRECISION})),
    )
    examples = (_example("ibis-duckdb"),)

    output = render_catalog(information, (), examples, [])

    assert output.count("precision, semantics") == 1
    assert "unclassified" in render_catalog((_information("ibis-duckdb"),), (), examples, [])


def test_catalogue_rejects_unresolved_or_ambiguous_issue_join():
    examples = (_example("ibis-duckdb", issue="IB-STR-11"),)
    with pytest.raises(ValueError):
        render_catalog((), (), examples, [])
    with pytest.raises(ValueError):
        render_catalog((), (), examples, [{"id": "IB-STR-11"}, {"id": "IB-STR-11"}])


def test_example_without_description_does_not_invent_information_or_policy():
    output = render_catalog((), (), (_example("ibis-duckdb"),), [])
    assert "SSe" in output and "ẞe" in output
    assert "No matching catalogue description" in output
    assert "No retained executable policy" in output


def test_catalogue_order_is_independent_of_input_order():
    information = (_information("ibis-duckdb"), _information("ibis-sqlite"))
    examples = (_example("ibis-duckdb"), _example("ibis-sqlite"))
    assert render_catalog(information, (), examples, []) == render_catalog(
        tuple(reversed(information)), (), tuple(reversed(examples)), [],
    )
