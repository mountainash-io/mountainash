from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

import mountainash.conform.expressions as conform_expressions
from tests.fixtures.frictionless_profile_coverage import (
    discover_mountainash_capabilities,
    discover_code_field_capabilities,
    discover_dialect_reader_capabilities,
    extract_profile_capabilities,
    discover_validation_rule_capabilities,
    load_json,
    load_official_profile_capabilities,
    load_profile_set,
    validate_profile_coverage,
    verify_snapshot_digests,
)

PROFILE_DIR = Path(__file__).parents[1] / "fixtures" / "frictionless" / "v2" / "profiles"


def test_profile_snapshot_digests_match_provenance() -> None:
    assert verify_snapshot_digests(PROFILE_DIR) == []


def test_snapshot_commit_matches_discrepancy_evidence() -> None:
    sources = load_json(PROFILE_DIR / "profile-sources.json")
    coverage = load_json(PROFILE_DIR / "profile-coverage.json")
    commits = {
        row["evidence_commit"]
        for row in coverage["upstream_exceptions"]
    }
    assert commits == {sources["commit"]}


def test_instance_paths_follow_properties_and_items() -> None:
    profile = {
        "properties": {
            "fields": {
                "type": "array",
                "items": {"properties": {"name": {"type": "string"}}},
            }
        }
    }
    capabilities = extract_profile_capabilities(profile, root_kind="schema")
    assert "schema:fields[].name" in capabilities


def test_branch_duplicates_merge_all_provenance() -> None:
    profile = {
        "oneOf": [
            {"properties": {"name": {"type": "string"}}},
            {"properties": {"name": {"minLength": 1}}},
        ]
    }
    capability = extract_profile_capabilities(
        profile, root_kind="resource"
    )["resource:name"]
    assert len(capability.source_pointers) == 2
    assert len(capability.branch_predicates) == 2


def test_enum_variants_have_stable_ids() -> None:
    profile = {"properties": {"type": {"enum": ["table", "file"]}}}
    capabilities = extract_profile_capabilities(profile, root_kind="resource")
    assert "resource:type=value:\"table\"" in capabilities
    assert "resource:type=value:\"file\"" in capabilities


def test_embedded_boundaries_rebase_to_standalone_kinds() -> None:
    capabilities = load_official_profile_capabilities(PROFILE_DIR)
    assert "resource:name" in capabilities
    assert "schema:fields[]" in capabilities
    assert "package:resources[].name" not in capabilities


def test_committed_profile_coverage_is_closed() -> None:
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=load_json(PROFILE_DIR / "profile-coverage.json"),
    )
    assert errors == []


def test_unknown_snapshot_path_fails_closed() -> None:
    profiles = deepcopy(load_profile_set(PROFILE_DIR))
    profiles["datapackage.json"]["properties"]["futureProperty"] = {"type": "string"}
    errors = validate_profile_coverage(
        profiles=profiles,
        manifest=load_json(PROFILE_DIR / "profile-coverage.json"),
    )
    assert any("package:futureProperty" in error for error in errors)


def test_unmatched_manifest_row_is_named() -> None:
    manifest = deepcopy(load_json(PROFILE_DIR / "profile-coverage.json"))
    orphan = deepcopy(manifest["rows"][0])
    orphan["capability"] = "resource:not-real"
    manifest["rows"].append(orphan)
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=manifest,
    )
    assert any("resource:not-real" in error and "orphan" in error for error in errors)


@pytest.mark.parametrize(
    ("status", "missing_key"),
    [
        ("deferred", "owner_unit"),
        ("upstream_exception", "discrepancy_id"),
        ("local_policy", "decision_reference"),
    ],
)
def test_incomplete_disposition_is_named(status: str, missing_key: str) -> None:
    manifest = deepcopy(load_json(PROFILE_DIR / "profile-coverage.json"))
    row = next(
        row
        for row in manifest["rows"]
        if row["storage"]["status"] == status
    )
    del row["storage"][missing_key]
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=manifest,
    )
    assert any(row["capability"] in error and missing_key in error for error in errors)


def test_evidence_complete_prose_capability_is_not_orphaned() -> None:
    manifest = load_json(PROFILE_DIR / "profile-coverage.json")
    prose_id = next(
        row["capability"]
        for row in manifest["rows"]
        if row.get("absent_from_profile") is True
    )
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=manifest,
    )
    assert not any(prose_id in error and "orphan" in error for error in errors)


def test_unmapped_model_alias_fails_closed() -> None:
    discovered = discover_mountainash_capabilities() | {"resource:futureAlias"}
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=load_json(PROFILE_DIR / "profile-coverage.json"),
        discovered_capabilities=discovered,
    )
    assert any("resource:futureAlias" in error for error in errors)


def test_typespec_schema_level_aliases_enter_discovery() -> None:
    discovered = discover_mountainash_capabilities()
    assert {
        "schema:$schema",
        "schema:fields[]",
        "schema:primaryKey",
        "schema:foreignKeys[]",
        "schema:missingValues[]",
    } <= discovered


def test_conform_code_fields_enter_discovery() -> None:
    assert "schema:fields[].type" in discover_code_field_capabilities(
        conform_expressions
    )


def test_validation_rule_kinds_enter_discovery() -> None:
    assert (
        "x-mountainash:validation.rule.row"
        in discover_validation_rule_capabilities()
    )


def test_dialect_reader_fields_enter_discovery() -> None:
    assert "dialect:delimiter" in discover_dialect_reader_capabilities()


def test_snapshot_digest_mutation_is_named(tmp_path: Path) -> None:
    copied = tmp_path / "profiles"
    shutil.copytree(PROFILE_DIR, copied)
    sources = load_json(copied / "profile-sources.json")
    sources["profiles"]["datapackage.json"]["sha256"] = "0" * 64
    (copied / "profile-sources.json").write_text(
        json.dumps(sources),
        encoding="utf-8",
    )
    assert verify_snapshot_digests(copied) == [
        "datapackage.json: snapshot digest mismatch"
    ]


def test_evidence_commit_mutation_is_named() -> None:
    manifest = deepcopy(load_json(PROFILE_DIR / "profile-coverage.json"))
    manifest["upstream_exceptions"][0]["evidence_commit"] = "0" * 40
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=manifest,
    )
    assert any("evidence_commit" in error for error in errors)
