# SDD ledger — plan: /home/ubuntu/git/mountainash-io/mountainash-central/04.planning/mountainash/superpowers/plans/2026-10-28-path-confinement-by-default.md

Spec: /home/ubuntu/git/mountainash-io/mountainash-central/04.planning/mountainash/superpowers/specs/2026-10-27-path-confinement-by-default-design.md
Worktrees (feature/381-location-confinement from origin/develop, 2026-10-28):
- transport: /home/ubuntu/git/mountainash-io/mountainash-transport-381 @ 80e8e04 (Tasks 1–4)
- files:     /home/ubuntu/git/mountainash-io/mountainash-files-381 @ 1e541a4 (Task 5)
- mountainash: /home/ubuntu/git/mountainash-io/mountainash-381 @ c617c79a (Tasks 6–9)
Mode: subagent-driven (security-gate work, cross-repo interfaces).

## Pre-flight scan

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 → T2 | T1 `location.py`, `_schemes.py`; T2 stdlib-only import test | Consistent (import test moved to T2). |
| T1 → T3/T4 | `LocationPolicy`, `confine_local`, `allow_remote(scheme, host, policy, *, profile_host)`, `url_host`, `require_known_scheme` | Signatures consistent across tasks. |
| T3 → T4 | T3 sets `_policy`/`_profile_*` "after the backend is created"; T4 needs `_policy` before backend construction (engine `location_check`) and says "reorder the constructor" | Conflict in order. Ruling 1. |
| T3 self | Test body uses `StorageFacade("local", LocalStorageProfile(ROOT_PATH=...))`; the note says use `local_profile(...)` and the enum | Self-inconsistent text, resolved by the note. Ruling 2. |
| T4 → T5 | transport 0.1.1 with `policy=` on `from_path`; files consumes | Consistent; files env needs editable transport worktree during dev. |
| T5 self | Fake backend now has `read_to_bytes` + `read_to_stream`; `_s3_profile` helper copied from T4 | Consistent. |
| T6 self vs spec | T6 "store the captured working directory as the context `base_uri`" when omitted; spec §5 (R3-A4) and T8 keep `MissingDescriptorBase` for references when no base | Conflict: a cwd `base_uri` would silently make relative schema/dialect references resolve against cwd. Ruling 3. |
| T6 → T7/T8 | `resource_policy`, `resolve_resource_location` | Consistent signatures. |
| T7 self | `confined_local_paths` both with and without policy; routing on base-resolved path | Consistent after delta fixes. |
| T7 → T9 | SCHEMA Ibis directory limitation recorded; support matrix note in T9 | Consistent. |
| T8 self | Resolver with `policy=None` denies remote (today); custom resolvers get `policy` kwarg | `DescriptorResolver.resolve` protocol gains a kwarg: custom resolvers without it would break. Ruling 4. |
| T9 self | Installed-build qualification from local wheels (0.1.1 unpublished) | Consistent. |

Ruling 1: T3 sets `_policy`, `_profile_host`, `_profile_any` **before** `get_storage_backend(...)` is called (the values depend only on the arguments), so T4 only adds `location_check` to `backend_kwargs` without reordering — prevents T4 rewriting T3's constructor — cost if wrong: one constructor reshuffle in T4.
Ruling 2: T3 tests build every local profile via `local_profile(...)` (PROVIDER_TYPE enum + `NoAuthProfile`) and facades via `CONST_STORAGE_PROVIDER_TYPE.LOCAL`; the bare `"local"` spelling in the test sketch is illustrative — cost if wrong: none (test construction only).
Ruling 3: loaders do NOT store the working directory as `base_uri`; `base_uri` stays `None` when omitted (references keep `MissingDescriptorBase`, spec §5). `loader_policy` puts the captured cwd in `policy.root` (set even under `allow_unconfined`, via `with_declared_root`). `resolve_resource_location` joins relative **resource** paths against `ctx.base_uri`, else against `ctx.policy.root` when the context carries a loader policy (active or not); programmatic contexts (policy `None`) keep raw paths — spec authority over plan text — cost if wrong: an omitted-base loader's relative references would need a base, as today.
Ruling 4: `resolve(..., policy=None)` is added as an optional keyword; the default resolver uses it; `resolve_descriptor_mapping` passes `policy=` only when the resolver's signature accepts it (inspect once), so existing custom resolvers keep working unchanged and remain caller-trusted (spec threat model) — cost if wrong: a custom resolver silently not confined, which the spec already permits.

## Progress
Note: harness accepts no per-agent model selection (task tool rejects `model`); all implementers/reviewers run on the default model.
Task 1: implemented 2638789 (base 80e8e04); review: 2 Important (plan-mandated): malformed-URL redaction/parse errors; host normalization asymmetric.
Ruling: fix both plan-mandated findings — spec §1 rules 5–6 (normalized host comparison; errors never carry secrets/underlying text) bind over the plan's sketch — cost if wrong: a few extra lines in location.py.
Task 1: minor (deferred): docs-site/profile/modules/storage-registry.json still names path_helpers.scheme (generated doc).
Task 1: fix round 1/5 (1 addressed, 1 open — P1 redaction misses scheme-relative "//user:pw@" and control-char-split "https:\n//"; commits 2638789..a208251)
Task 1: fix round 2/5 (production P1 addressed; 1 open — boundary tests accept normal returns for malformed forms; commits a208251..d20a6c5)
Task 1: fix round 3/5 (1 addressed, 0 open; commits d20a6c5..dae7c1b)
Task 1: complete (commits 80e8e04..dae7c1b, review clean)
Task 2: implemented b509ca2 (base dae7c1b); review: 1 Important — first-lookup backend loading overwrites a caller registration made before first lookup.
Task 2: fix round 1/5 (1 addressed, 0 open; commits b509ca2..538458b)
Task 2: complete (commits dae7c1b..538458b, review clean)
Task 3: complete (commits 538458b..ff6b3ec, review clean)
Task 4: implemented d285fa9 (base ff6b3ec); review: 2 Important — injected engine silently drops location_check; S3 parse/translation runs with inactive policy (changes ValueError).
Task 4: fix round 1/5 (2 addressed, 0 open; commits d285fa9..73766a0)
Task 4: complete (commits ff6b3ec..73766a0, review clean)
Task 4: minor (deferred, final-review triage): require_known_scheme parses before the inactive-policy return; a malformed URL with NO policy may now raise LocationNotAllowed("invalid location") instead of today's error — check against decision 2.
Task 5: complete (commits 1e541a4..4b04951, review clean)
Ruling 5: during development the files/mountainash Hatch envs cannot resolve the new >=0.1.1 floors against the 0.1.0 sibling checkouts named in hatch.toml; implementers install the transport/files FEATURE worktrees into the env with `uv pip install -e` and run pytest with the env python; hatch.toml is not changed — the floors are correct for release and CI resolves once transport/files merge first (merge order transport → files → mountainash) — cost if wrong: CI for files/mountainash PRs stays red until upstream PRs merge.
Task 6: implemented e18c6eec (base c617c79a); review: 1 Important — loader_policy runs before normalize_base_uri, changing the malformed-base error from InvalidDescriptorStructure to LocationNotAllowed.
Task 6: fix round 1/5 (1 addressed, 0 open; commits e18c6eec..f3155048)
Task 6: complete (commits c617c79a..f3155048, review clean)
Carry to Task 8: loader_policy now also calls _local_path_from_uri (descriptor_context); Task 8 must migrate that callsite too before deleting the helper, keeping normalize_base_uri first.
Task 7: implemented 60c91410 (base f3155048); review: 1 Important — allow-any-http fixture used a non-empty host set; the empty-set any-host case is untested.
Task 7: fix round 1/5 (1 addressed, 0 open; commits 60c91410..7e834618)
Task 7: complete (commits f3155048..7e834618, review clean)
Note for Task 9: test_e2e_real_descriptor.py already migrated in Task 7 (policy root=tmp_path).
Task 8: implemented 0f0ae848 (base 7e834618); review: 2 Important — (1) programmatic remote ResourceRef reads not denied without policy; (2) unknown scheme under active policy reaches confine_local/local open.
Ruling 6: Task 8 finding 1 rejected — decision 2 (no root → today) governs ResourceRef: today a programmatic remote ResourceRef.read_bytes reads via the facade, so it stays allowed; the "remote denied with no policy" rule applies only to descriptor references because the old default resolver already denied them — cost if wrong: programmatic remote byte reads stay unconfined, which decision 2 explicitly permits.
Task 8: fix round 1/5 (1 addressed, 1 ruled out by Ruling 6; commits 0f0ae848..f1e42a23)
Task 8: complete (commits 7e834618..f1e42a23, review clean)
Task 9: implemented a87bb6ec (base f1e42a23); review: 2 Important doc claims (datacontract policy=; absolute paths "outside the root").
Ruling 7: the full-suite run without coverage flags satisfies Task 9 qualification — coverage output was a by-product of `hatch run test:test`, not an acceptance criterion, and Hatch cannot run under Ruling 5; PR evidence is attached by the controller after the final review — cost if wrong: one coverage run before merge.
Task 9: fix round 1/5 (2 addressed, 0 open; commits a87bb6ec..2bb56b67)
Task 9: complete (commits f1e42a23..2bb56b67, review clean)
Final review: Fix before merge — 4 Important (CREATE_PATH makedirs before policy check; suffix inference before _check leaks credentials (transport+files); policy-only validation runs when inactive incl. copy dir error; relative explicit loader root applied twice). Deferred minor: Task 1 docs-site JSON accepted; Task 4 minor promoted to Important 3. Cleanups: obsolete _ensure_storage_facade advice; files extras floors.
Final fix wave: commits transport 73766a0..0661f49, files 4b04951..b0f0387, mountainash 2bb56b67..e781c256. Re-review: #2,#5,#6 fixed; residual — R1 [P1] relative ROOT_PATH: check targets /safe/x but makedirs creates cwd/x; R2 [P2] inactive LOCAL still runs confine_local(path, None) (file:// converted, file://otherhost rejected) and from_path calls require_known_scheme unconditionally; R3 [P1, new] loader_policy abspath collapses ".." before symlink resolution, moving the root.
Residuals R1–R3 are load-bearing (security boundary / decision 2) and surface to the owner per the one-fix-wave rule; workspace kept.
Second fix round (owner-approved): transport 0661f49..44dc4c6, mountainash e781c256..b7592e35.
