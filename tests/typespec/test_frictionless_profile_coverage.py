from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

import mountainash.conform.expressions as conform_expressions
import mountainash.relations.backends.relation_systems.resource_files as resource_files
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


def test_local_ref_shape_drives_array_and_enum_capabilities() -> None:
    profile = {
        "$defs": {
            "tags": {
                "type": "array",
                "items": {"type": "string"},
            },
            "kind": {"enum": ["table", "file"]},
        },
        "properties": {
            "tags": {"$ref": "#/$defs/tags"},
            "kind": {"$ref": "#/$defs/kind"},
        },
    }
    capabilities = extract_profile_capabilities(profile, root_kind="resource")
    assert "resource:tags[]" in capabilities
    assert "resource:kind=value:\"table\"" in capabilities


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


def test_ma_v2_01_covers_all_schema_url_rows() -> None:
    manifest = load_json(PROFILE_DIR / "profile-coverage.json")
    rows = {
        row["capability"]: row
        for row in manifest["rows"]
        if row["capability"]
        in {"package:$schema", "resource:$schema", "dialect:$schema", "schema:$schema"}
    }
    assert set(rows) == {
        "package:$schema",
        "resource:$schema",
        "dialect:$schema",
        "schema:$schema",
    }
    for row in rows.values():
        assert all(
            row[dimension]["status"] == "local_policy"
            and row[dimension]["decision_reference"] == "MA-V2-01"
            for dimension in ("storage", "typed", "execution")
        )
    contributor_role = next(
        row for row in manifest["rows"]
        if row["capability"] == "package:contributors[].role"
    )
    assert contributor_role["storage"]["status"] == "implemented"


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
def test_missing_snapshot_provenance_record_is_named(tmp_path: Path) -> None:
    copied = tmp_path / "profiles"
    shutil.copytree(PROFILE_DIR, copied)
    sources = load_json(copied / "profile-sources.json")
    del sources["profiles"]["tabledialect.json"]
    (copied / "profile-sources.json").write_text(
        json.dumps(sources),
        encoding="utf-8",
    )
    assert verify_snapshot_digests(copied) == [
        "tabledialect.json: provenance record missing"
    ]


def test_unknown_reader_set_name_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        resource_files,
        "_IGNORED_DIALECT_FIELDS",
        frozenset({"future_reader_field"}),
    )
    with pytest.raises(ValueError, match="future_reader_field"):
        discover_dialect_reader_capabilities()


def test_absent_prose_overlap_with_official_capability_is_named() -> None:
    manifest = deepcopy(load_json(PROFILE_DIR / "profile-coverage.json"))
    manifest["prose_capabilities"].append(
        {
            "capability": "schema:fields[]",
            "source_url": "https://example.invalid",
            "section_anchor": "#fields",
            "quotation": "This is evidence.",
            "absent_from_profile": True,
        }
    )
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=manifest,
    )
    assert any(
        "schema:fields[]" in error and "overlaps official" in error
        for error in errors
    )


def test_dataclass_extensions_use_live_mountainash_namespace() -> None:
    discovered = discover_mountainash_capabilities()
    assert "x-mountainash:schema:fields[].backend_type" in discovered
    assert "x-mountainash:schema:fields[].custom_cast" in discovered
    assert "x-mountainash:schema:fields[].backendType" not in discovered


def test_unsupported_dialect_options_are_execution_deferred() -> None:
    manifest = load_json(PROFILE_DIR / "profile-coverage.json")
    unsupported = {
        "dialect:commentChar",
        "dialect:commentRows[]",
        "dialect:doubleQuote",
        "dialect:headerJoin",
        "dialect:headerRows[]",
        "dialect:itemKeys[]",
        "dialect:itemType",
        "dialect:itemType=value:\"array\"",
        "dialect:itemType=value:\"object\"",
        "dialect:lineTerminator",
        "dialect:property",
        "dialect:sheetName",
        "dialect:sheetNumber",
        "dialect:skipInitialSpace",
        "dialect:table",
    }
    assert all(
        next(row for row in manifest["rows"] if row["capability"] == capability)[
            "execution"
        ]["status"]
        == "deferred"
        for capability in unsupported
    )


def test_unsupported_constraints_are_unit_b_deferred() -> None:
    manifest = load_json(PROFILE_DIR / "profile-coverage.json")
    unsupported = {
        "schema:fields[].constraints.exclusiveMaximum",
        "schema:fields[].constraints.exclusiveMinimum",
        "schema:fields[].constraints.jsonSchema",
    }
    for capability in unsupported:
        row = next(
            row for row in manifest["rows"] if row["capability"] == capability
        )
        for dimension in ("storage", "typed", "execution"):
            assert row[dimension]["status"] == "deferred"
            assert row[dimension]["owner_unit"] == "B"


def test_evidence_commit_mutation_is_named() -> None:
    manifest = deepcopy(load_json(PROFILE_DIR / "profile-coverage.json"))
    manifest["upstream_exceptions"][0]["evidence_commit"] = "0" * 40
    errors = validate_profile_coverage(
        profiles=load_profile_set(PROFILE_DIR),
        manifest=manifest,
    )
    assert any("evidence_commit" in error for error in errors)
