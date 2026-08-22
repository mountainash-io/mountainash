# Final fix wave report

## Commit

- `fb1abcce934906cfa167787cb39e9b835829df6c` — `fix(typespec): align coverage manifest and Unit A boundary with spec`

All four final-review findings are included in this commit. The working tree was clean after the commit.

## Finding 1 — coverage attribution and fail-closed gate

### Manifest changes

`tests/fixtures/frictionless/v2/profiles/profile-coverage.json:29-87` now records the six upstream discrepancies against the capabilities named by the central item-113 ledger:

- `DP-V2-01` → `schema:fields[].type=value:"list"`; the profile omits the prose-defined list branch.
- `DP-V2-02` → `schema:fields[].type=value:"string"`; the pinned profile selects string when type is omitted.
- `DP-V2-03` → all four `$schema` paths via `affected_paths` (`package:$schema`, `resource:$schema`, `dialect:$schema`, `schema:$schema`).
- `DP-V2-04` → `schema:fields[].itemType`; the prose contains the `datetme` token.
- `DP-V2-05` → `resource:dialect`; the prose-supported dialect reference string is stored raw and resolved one hop.
- `DP-V2-06` → `package:contributors[].role`; singular role is the fallback when roles is absent.

Every exception keeps evidence commit `6a201af8ed2eacbb3a2440e82e4c55d5807f9c09`, review date `2026-08-20`, and a decision reference to `2026-08-20-frictionless-v2-descriptor-codec-design.md#source-exceptions-and-local-policy`. The affected prose-only capabilities for the list branch and dialect reference are documented in `prose_capabilities` and have corresponding manifest rows.

The stale upstream-exception dispositions were removed from the unrelated resource type/path, dialect enum, topojson format, license path, and year rows. Correct storage dispositions were added to the list branch, string branch, itemType, dialect reference, and contributor role rows. The four official `$schema` rows retain `local_policy` status and `MA-V2-01` references.

### Gate changes and regression

`tests/fixtures/frictionless_profile_coverage.py:20-38,713-799` now has a stable discrepancy-ID-to-capability-path map. It validates:

- every required discrepancy appears exactly once;
- evidence commit and review date remain pinned;
- affected paths match the semantic path set for that discrepancy (including all four DP-V2-03 paths);
- affected paths are known official, discovered, or documented prose capabilities;
- decision references point to the design spec.

`tests/typespec/test_frictionless_profile_coverage.py:357-369` mutates `DP-V2-06` to the incorrect `package:licenses[].path` path and proves the gate rejects the manifest. `tests/typespec/test_frictionless_profile_coverage.py:110-139` also checks the corrected MA-V2-01 wording and contributor-role disposition.

The test was first run against the old gate and failed because the incorrect attribution was accepted; after the gate change, it passed.

## Finding 2 — MA-V2-01 wording

`tests/fixtures/frictionless/v2/profiles/profile-coverage.json:91-102` now states that omitted `$schema` is interpreted as v2, not rejected or treated as v1; canonical output emits the corresponding standard v2 URI, and preserve output leaves an omitted value absent. The same behavior is repeated in each of the twelve dimension dispositions for the four official rows at the `$schema` row locations beginning at lines `107`, `428`, `789`, and `1106`, each with `MA-V2-01` references.

This wording was checked against `src/mountainash/typespec/frictionless_codec.py:1229-1275,1300-1318`: `_canonical_profile()` maps absent or standard values to the standard URI, `_canonicalize_dialect()` and `_canonicalize_schema()` apply nested URIs, and `_encode_package_canonical()` applies package and resource URIs. Preserve encoders leave absent values absent.

## Finding 3 — mapping-only TypeSpec adapter boundary

`src/mountainash/typespec/frictionless.py:16-22,232-233,301-321` now imports `Mapping` at runtime, removes `json`, `Path`, `Union`, and the JSON/path sniffing branches, accepts only resolved schema mappings, and raises a clear `TypeError` for JSON text or paths. The docstring now identifies the v2 codec as the resolver boundary.

The only production caller that still accepted a path (`src/mountainash/__init__.py:112-139`) was migrated to wrap path/text schema input through `DataPackage.from_descriptor()` and `DataResource.to_typespec()`, so the adapter receives a resolved mapping. Existing path behavior remains covered by `tests/datacontracts/test_datacontract_entrypoint.py::TestDatacontractFromFrictionlessPath` (2 passed).

`tests/typespec/test_frictionless.py:195-203` proves both `Path` and JSON text are rejected at the adapter boundary. The test was observed failing before the change and passing after it.

## Finding 4 — reference-backed schema inference

`src/mountainash/relations/schema_inference.py:222-244,293-298` adds TypeSpec-based canonical schema extraction and resolves any non-dict resource schema through `resource.to_typespec()`. The raw mapping path remains unchanged for DAG packaging.

`src/mountainash/relations/backends/relation_systems/polars/extensions_mountainash/relsys_pl_ext_ma_util.py:19-44,229` changes the declared-schema helper to receive the resource, keeps the raw dict adapter path, and resolves string/other schema values through `resource.to_typespec()` before calling `to_polars_schema()`.

`tests/relations/dag/test_resource_read_cross_backend.py:247-284` creates a resource with `schema="schema.json"`, compares its Polars declared schema with an equivalent inline mapping, and compares shared `infer_schema()` output. The regression passed with `{"id": pl.Int64}` and the same inferred `id` column/type on both paths.

## Ledger and design verification

I re-read the central design spec sections 9.1, 9.2, 10.2, and 14 and the authoritative item-113 ledger entry. The ledger records DP-V2-01 through DP-V2-06 as the list branch, omitted-type string selection, v1 `$schema` defaults, `datetme`, dialect reference strings, and contributor-role fallback respectively. It also states that MA-V2-01 applies to all four `$schema` paths and that canonical output emits the corresponding v2 URI. The committed manifest now matches those records and the codec implementation.

## Verification commands and outcomes

- `hatch run test:test-target-quick tests/typespec/test_frictionless_profile_coverage.py -v` — **29 passed**.
- `hatch run test:test-target-quick tests/typespec/test_frictionless.py::TestFromFrictionless::test_mapping_only_rejects_json_text_and_paths -v` — **1 passed**.
- `hatch run test:test-target-quick tests/relations/dag/test_resource_read_cross_backend.py::test_referenced_schema_inference_matches_inline_schema -v` — **1 passed**.
- `hatch run test:test-target-quick tests/datacontracts/test_datacontract_entrypoint.py::TestDatacontractFromFrictionlessPath -v` — **2 passed**.
- `hatch run test:test-target-quick tests/typespec tests/relations/backends/test_resource_files.py tests/relations/dag/test_resource_read_cross_backend.py tests/relations/dag/test_e2e_real_descriptor.py tests/relations/dag/cross_backend/test_datapackage_validation_loop.py tests/relations/dag/cross_backend/test_empty_resource_collect.py -v` — **790 passed**.
- `hatch run ruff:check` — **passed**.
- `git diff --check` — **passed** before commit.
