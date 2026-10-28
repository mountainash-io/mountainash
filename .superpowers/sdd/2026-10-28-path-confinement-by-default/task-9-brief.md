### Task 9 (mountainash): migrate unconfined tests, docs, changelog; full qualification

**Files:**
- Tests to move onto the opt-out, allow-list or no-root path (never delete; spec Acceptance):
  - (Decode-only tests such as `tests/typespec/test_frictionless_codec.py:137-139,215-217` never open the location and need no migration.)
  - `tests/relations/dag/test_resource_read_cross_backend.py:215,258,493-497,777-790`;
  - `tests/relations/test_resource_schema_discovery.py:37-41`;
  - `tests/relations/dag/test_e2e_real_descriptor.py:53,68-183` (paths assigned after load → pass `base_uri=tmp_path` or construct programmatically);
  - `tests/relations/dag/cross_backend/test_empty_resource_collect.py:58`.
- Docs: `CHANGELOG.md` (`## Unreleased` → Breaking/Added entries per spec "Release notes"), `docs/reference/datapackage.md` (Location policy section), `docs/reference/resource-read-support-matrix.md` (policy column; Ibis directory exception; native allow-list).
- Backlog: update item 381 Status/evidence and the infrastructure index row (central `main`).

- [ ] **Step 1:** Run `hatch run test:test-quick` and list the failures. Every failure must be one of the files above or a direct consequence of Tasks 6–8. Anything else is a defect: stop and fix it in the owning task.
- [ ] **Step 2:** Migrate each failing test to the appropriate path (`policy=LocationPolicy(allow_unconfined=True)`, `allowed_remote={"http": frozenset({"127.0.0.1"})}`, `base_uri=tmp_path`, or programmatic construction), keeping its original assertion.
- [ ] **Step 3:** Write the docs and changelog.
- [ ] **Step 4:** `hatch run test:test` (full, with coverage) and `hatch run ruff:check` → PASS. Then installed-build qualification:
  1. Build wheels for transport and files from their PR branches (`hatch build`).
  2. Create a fresh venv; install those wheels, then mountainash with `[ibis]` from this branch (non-editable).
  3. Run a runtime smoke there covering the Task 7 case table on all four targets plus `ResourceRef`, references and the opt-out.

  Record the smoke output and the installed versions in the PR.
- [ ] **Step 5: Commit** `test,docs: migrate unconfined fixtures; document LocationPolicy (381)`. Open the PR to `develop`, depending on the transport and files PRs.

---

## Execution mode

The owner's default is `executing-plans` (batched, owner checkpoints). This item is security-relevant, so `subagent-driven-development` (fresh implementer plus reviewer per task) is the alternative. The choice is the owner's at hand-off. Either way: a post-implementation adversarial review plus a complexity review per PR, then the owner's acceptance.

## Self-review record

- **Plan review round 1 (2026-10-28), dispositions:**
  - C1/F9 (stdlib import checkpoint): moved to Task 2.
  - C2/F4 (bucketless S3 profile): `_profile_any`; constructor-boundary tests.
  - C3: auth-flow, shortcut-attack, different-profile stream and files profile tests added; private `__new__` tests replaced.
  - C4: root-equality retention; cwd change; post-load assignment; remote-base resource; dialect; strict `..` reference expectations.
  - C5: `.` remainder no longer refused.
  - F1 (factory default/annotation): fixed in Task 2.
  - F2 (hierarchical join for non-HTTP schemes): fixed in Task 6.
  - F3 (base joining under opt-out): fixed in Task 7.
  - F5 (unknown scheme before provider detection): `require_known_scheme` in `from_path`.
  - F6 (SCHEMA test): replaced by SCHEMA execution.
  - F7: existing Ibis SCHEMA directory limitation recorded (probed); no new route.
  - F8: version floors.
  - Complexity cuts applied: duplicate remote check in the fallback; repeated full-suite runs; decode-only migrations.

- **Plan delta review (2026-10-28), dispositions:**
  - D1: `require_known_scheme` also at the start of `_check`, with an operation-time test.
  - D2: native routing classifies the base-resolved path; an opt-out remote-base test was added.
  - D3: the fakes implement `read_to_bytes`.
  - D4: the remote join reuses `_normalize_remote_path` for dot segments.
- **Spec coverage:** §1 → T1; §2 → T2; §3 local and copy → T3; §3 remote and engine → T4; §4 → T5; §5 carriage and loaders → T6; §5 readers and decision 7 → T7; §5 references, `ResourceRef` and resolver → T8; acceptance migrations and release notes → T9. Threat-model limits are documented in T4 Step 6 (no code).
- **Out of scope by design:** SFTP URL conversion (transport 34), install slimming (transport 33), native remote engine reads (387), files bundle.
- **Placeholders:** none. Every task carries concrete test code.
- **Name consistency:** `LocationPolicy`, `LocationNotAllowed`, `confine_local`, `allow_remote`, `url_host`, `identify_scheme`, `local_path`, `with_declared_root`, `resource_policy`, `resolve_resource_location`, `confined_local_paths`, `escape_duckdb_glob`, `ensure_backends_loaded`, `location_check`.
