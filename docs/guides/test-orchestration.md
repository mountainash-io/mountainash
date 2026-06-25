# Test Orchestration

This is the contributor-facing how-to for running and extending mountainash's
test suite. The suite is large (~17.9k tests, dominated by the cross-backend
matrix), so CI does **not** run everything on every change — it runs a surgical
subset selected from what you changed, and a full run guards merges. This guide
explains the machinery and how to drive it, both on the CLI and in CI.

The design principles behind it: `f.development-practices/testing-philosophy.md`,
`cross-backend-test-coverage.md`, and `closed-by-default-verification.md` in the
principles directory.

## Mental model: two axes + two filters

A test has two orthogonal coordinates and is run through two independent filters:

| Axis / filter | Values | Set by | Purpose |
|---|---|---|---|
| **Module** (axis) | folder under `tests/` | where the file lives | what subsystem it covers |
| **Tier** (axis) | exactly one of `unit` / `cross_backend` / `integration` / `contract` | auto-assigned at collection from the nodeid | how/when to run it |
| **Backend scope** (filter) | `full` (9 backends) or `pr` (3) | `MA_BACKEND_SCOPE` env / `--ma-backend-scope` | which backends the cross-backend matrix runs |
| **Change selection** (filter) | affected test paths | `scripts/select_tests.py` from your diff | which test dirs are relevant to a change |

You rarely set the tier yourself — it's assigned automatically. You *do* choose
backend scope and change selection when you want a faster local run, and CI sets
them for you.

## Tiers

Every collected test carries **exactly one** tier marker, applied automatically
at collection by `tests/conftest.py::pytest_collection_modifyitems` via the pure
resolver `tests/selection/tiers.py::resolve_tier(nodeid)`.

| Tier | Meaning |
|---|---|
| `unit` | fast, isolated; no backend or a single backend |
| `cross_backend` | parametrised over the backend matrix (the bulk of the suite) |
| `integration` | multi-component / end-to-end (e.g. the DAG, `tests/integration/`) |
| `contract` | verification harnesses that must **always** run (signature/taxonomy/selector audits) |

Two **orthogonal flags** (not tiers) can also be attached and deselected:
`slow` (long-running) and `perf` (benchmarks; nightly only).

Run a single tier (or a boolean combination) with `-m`:

```bash
hatch run test:test-target-quick tests -- -m cross_backend
hatch run test:test-target-quick tests -- -m "unit or contract"
hatch run test:test-target-quick tests -- -m "cross_backend and not slow"
```

**Closed-by-default.** `resolve_tier` returns `None` for any nodeid it can't
classify, and the taxonomy audit (below) *fails* on that — so a test under a
brand-new path is never silently skipped. If you add tests under a new top-level
directory, you must teach the resolver about it (see *Extending the system*).

## Backend scope

The canonical backend list is `tests/fixtures/backend_registry.ALL_BACKENDS` —
**always the full 9** backends (`polars`, `polars-lazy`, `pandas`,
`narwhals-polars`, `narwhals-pandas`, `narwhals-lazy`, `ibis-duckdb`,
`ibis-polars`, `ibis-sqlite`). Cross-backend tests parametrise over it.

`MA_BACKEND_SCOPE` controls which backends actually **run**:

- `full` (default, and any unrecognised value — fail-safe): all 9.
- `pr`: one representative per engine family — `polars`, `narwhals-polars`,
  `ibis-duckdb`.

Scoping is applied by **deselecting** out-of-scope parametrized cases at
collection — `ALL_BACKENDS` is *not* shrunk. This keeps it meaningful as the
canonical registry (structural tests assert against it) while still cutting the
matrix ~3× for PR runs.

```bash
# env var (applies to the whole run)
MA_BACKEND_SCOPE=pr hatch run test:test-target-quick tests/expressions/cross_backend

# or the CLI flag (mirrors the env var; CLI wins)
hatch run test:test-target-quick tests/expressions/cross_backend -- --ma-backend-scope pr
```

A cross-backend file that collects 198 cases at `full` collects 66 at `pr`
(the other 132 are deselected).

> **Writing a cross-backend test:** parametrise over `ALL_BACKENDS` and name the
> parameter `backend_name` (the convention; `backend` is also recognised). The
> deselection hook reads that param to decide what to drop, so a differently
> named backend param will run on all 9 regardless of scope.

## Change selection (the "affected" subset)

`scripts/select_tests.py` maps the source paths you changed to the test paths
worth running, using the registry in `tests/selection/selectors.yaml`:

- A changed `src/mountainash/<module>/…` path selects that module's tests **plus
  its declared downstream dependents** (e.g. `expressions/` →
  `tests/expressions tests/relations tests/conform tests/integration`, because
  relations and conform embed expression compilation).
- A **cross-cutting** path (`core/dtypes`, `core/constants`, `conftest.py`,
  `fixtures/`, `selection/`, `pyproject.toml`, `hatch.toml`, `pytest.ini`) or an
  **unmatched** path falls back to the **full** suite (fail-safe — never runs
  fewer tests than it should).
- The output is plain test **paths** only. The `contract` tier always runs as a
  separate invocation (a single `-m contract` would *filter* the affected paths
  down to only contract tests, so it's never folded in).

```bash
# what would run for your current diff vs develop?
python scripts/select_tests.py --base develop

# run exactly that subset (full backend scope) — the convenience wrapper:
hatch run test:affected
```

## CLI cheat-sheet

```bash
# fastest iteration — no coverage
hatch run test:test-quick                         # whole suite, no cov
hatch run test:test-target-quick <path>           # a file/dir/nodeid, no cov

# with coverage (slower)
hatch run test:test                               # whole suite + cov reports
hatch run test:test-target <path>                 # targeted + cov

# only what your change affects (vs develop)
hatch run test:affected

# fast PR-like run: affected paths at the 3-backend PR scope
MA_BACKEND_SCOPE=pr hatch run test:affected

# slice by tier / flag
hatch run test:test-target-quick tests -- -m cross_backend
hatch run test:test-target-quick tests -- -m "not (slow or perf)"

# the guard audits (see below)
hatch run test:audit-taxonomy                     # tiers + markers closure (strict)
hatch run test:test-target-quick tests/core/test_selector_registry.py   # selector closure
```

Pass pytest args after `--` for the `test-target*` scripts; `test-target`/
`test-target-quick` take the path/args directly.

## CI tiers

Three tiers, in `.github/workflows/`:

| Trigger | Job | What runs | Scope |
|---|---|---|---|
| **PR push** (`pull_request`) | `test` in `python-run-pytest.yml` | `select_tests.py` affected subset | `pr` (3 backends) |
| **Merge queue** (`merge_group`) | `full-on-merge-queue` | full suite, `-m "not perf"` | `full` (9) |
| **Nightly** (cron 14:00 UTC) + manual | `full` in `python-nightly-tests.yml` | full suite | `full` (9) |

- The PR job derives the base ref, runs `python scripts/select_tests.py --base
  origin/<base>` to compute the paths, and runs them with `MA_BACKEND_SCOPE=pr`.
- `workflow_dispatch` on the PR workflow takes a `test_scope` input
  (`pr` | `full`) to force a full run on demand.
- The PR job is guarded `if: github.event_name != 'merge_group'` and the
  full job `if: github.event_name == 'merge_group'`, so a PR push gets the fast
  affected+`pr` run and the merge queue gets the full matrix.

> **Operational requirement (one-time, repo settings):** the pre-merge full
> matrix only fires via the **GitHub merge queue**. It must be enabled in branch
> protection for `develop` with **`full-on-merge-queue` as a required status
> check**. The workflow file alone cannot turn the merge queue on.

## The guard tests (closed-by-default)

These `contract`-tier tests keep the system honest — they fail loudly rather
than letting coverage silently erode. They run in every full run and whenever
`tests/` or the selection infra changes.

| Guard | Fails when | Fix |
|---|---|---|
| `tests/selection/test_auto_tier_marking.py` | a collected test resolves to no tier, or carries >1 tier | add a rule/override in `tiers.py`, or remove the duplicate marker |
| `tests/core/test_taxonomy_audit.py` (+ `scripts/audit_test_taxonomy.py`) | any untagged test, an unregistered marker in use, or a registered-but-unused marker | classify the test, register/remove the marker, or add a dated `KNOWN_UNUSED_MARKERS` entry |
| `tests/core/test_selector_registry.py` | a `selectors.yaml` path is missing/empty, or a test dir is unreachable from any selector | fix the selector entry / add a rule |

Counts are reported for humans; the tests assert the *violation sets are empty*,
never specific counts.

## Extending the system

**You added tests under a brand-new top-level `tests/<dir>/`.** `resolve_tier`
returns `None` → the taxonomy audit fails. Add a rule (or override) in
`tests/selection/tiers.py` — a directory rule in `_PATH_RULES`, or an exact-file
entry in `_TIER_OVERRIDES` with a dated comment. Choose the *correct* tier; don't
default everything to `unit`.

**You added a new source module `src/mountainash/<module>/` with its own
tests.** Add a rule to `tests/selection/selectors.yaml` mapping the source path
to its test dir(s) plus any genuine downstream dependents. `test_selector_registry`
checks every selector points at a real, non-empty path and that every test dir
is reachable.

**You added a marker** (e.g. a new flag). Register it in `pytest.ini` (the single
source of truth — `--strict-markers` is on). If it's registered but not yet used,
add it to `KNOWN_UNUSED_MARKERS` in `scripts/audit_test_taxonomy.py` with a dated
reason, or the audit will flag it.

**You wrote a test that shells out to `pytest` in a subprocess.** Under coverage
(`parallel = true` + `branch = true`), a child `pytest` can inherit pytest-cov's
subprocess hooks and write statement-mode data that won't combine with the
parent's branch data (`DataError: Can't combine statement coverage data with
branch data`). Pass a coverage-free environment to the subprocess — strip
`COVERAGE_PROCESS_START`, `COVERAGE_PROCESS_CONFIG`, `COVERAGE_FILE`, and
`COV_CORE_SOURCE`/`COV_CORE_CONFIG`/`COV_CORE_DATAFILE`/`COV_CORE_CONTEXT`. See
`_coverage_free_env()` in `scripts/audit_test_taxonomy.py` for the pattern.

## Troubleshooting

- **"`N` untagged tests" / audit fails** — a test lives under a path with no
  tier rule. Add the rule/override in `tiers.py`; re-run `hatch run
  test:audit-taxonomy`.
- **A backend-specific failure disappears at `pr` scope** — that backend isn't in
  the PR set, so its parametrized case is deselected. Reproduce at full scope:
  `MA_BACKEND_SCOPE=full hatch run test:test-target-quick <path>`.
- **`'<marker>' not found in markers configuration`** — the marker isn't in
  `pytest.ini`. Register it (or remove the stray `@pytest.mark.<x>`).
- **`select_tests.py` returns `tests`** — your change touched a cross-cutting path
  (or one with no rule), so the full suite is selected on purpose (fail-safe).
- **CI ran the whole suite on a PR** — same reason: a cross-cutting/unmapped path
  in the diff. Expected.
