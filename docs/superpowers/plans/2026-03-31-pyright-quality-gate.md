# Pyright Quality Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish Pyright as a zero-error quality gate at `basic` mode with architectural noise rules disabled, fix genuine bugs found during triage, and create a ratchet mechanism for progressive strictness.

**Architecture:** Configure `pyrightconfig.json` with `basic` mode + 4 disabled architectural rules (bringing errors from 1,169 to 227). Triage the 227 errors by file, fix bugs, track architectural topics, suppress only where genuinely correct. Add a hatch env for `hatch run pyright:check`. Write a principle document.

**Tech Stack:** Pyright, hatch, uv

---

## File Structure

| File | Responsibility |
|------|---------------|
| `pyrightconfig.json` | Pyright config — basic mode + disabled rules |
| `hatch.toml` | New `[envs.pyright]` section |
| `src/mountainash/schema/schema_utils.py` | 70 errors — largest bug cluster |
| `src/mountainash/core/factories.py` | 37 errors — optional member access |
| `src/mountainash/expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_ternary.py` | 26 errors |
| `src/mountainash/expressions/core/expression_protocols/auto_gen/__init__.py` | 11 errors — broken imports |
| Various other files | Remaining ~83 errors across many files |
| `mountainash-central/01.principles/mountainash-expresions/g.development-practices/pyright-quality-practice.md` | Principle document |
| `CLAUDE.md` | Add principle to table |

---

### Task 1: Configure Pyright basic mode with disabled architectural rules

**Files:**
- Modify: `pyrightconfig.json`

- [ ] **Step 1: Update pyrightconfig.json**

Edit `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/pyrightconfig.json` to:

```json
{
  "venvPath": ".",
  "venv": ".venv",
  "typeCheckingMode": "basic",
  "reportAttributeAccessIssue": false,
  "reportRedeclaration": false,
  "reportOperatorIssue": false,
  "reportArgumentType": false
}
```

These 4 rules account for 791 errors that are architectural (Ibis dynamic API, protocol method shadowing, broad type aliases). They will be re-enabled as future architectural specs land.

- [ ] **Step 2: Verify error count dropped**

```bash
python -m pyright src/mountainash/ --outputjson 2>&1 | python -c "import sys,json; d=json.load(sys.stdin); print(f'Errors: {d[\"summary\"][\"errorCount\"]}')"
```

Expected: `Errors: 227` (down from 1,169)

- [ ] **Step 3: Commit**

```bash
git add pyrightconfig.json
git commit -m "chore: configure Pyright basic mode with architectural rules deferred

Disables reportAttributeAccessIssue, reportRedeclaration,
reportOperatorIssue, reportArgumentType — these are architectural
issues to be resolved by future type system specs.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Add hatch pyright environment

**Files:**
- Modify: `hatch.toml`

- [ ] **Step 1: Add pyright env to hatch.toml**

Add the following section to `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/hatch.toml` after the `[envs.mypy]` section at the end of the file:

```toml
#================
# Env: pyright
#================
# Pyright Type checks
[envs.pyright]
installer = "uv"
dependencies = ["pyright>=1.1.400"]
[envs.pyright.scripts]
check = "pyright src/mountainash/"
```

- [ ] **Step 2: Verify hatch env works**

```bash
hatch run pyright:check
```

Expected: Pyright runs and reports errors. It will not yet be zero — triage hasn't happened.

- [ ] **Step 3: Commit**

```bash
git add hatch.toml
git commit -m "chore: add hatch pyright environment for type checking

Run via: hatch run pyright:check
Sits alongside hatch run ruff:check and hatch run mypy:check.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Triage and fix errors — schema_utils.py (70 errors)

**Files:**
- Modify: `src/mountainash/schema/schema_utils.py`

- [ ] **Step 1: Get the specific errors**

```bash
python -m pyright src/mountainash/schema/schema_utils.py --outputjson 2>&1 | python -c "
import sys, json
d = json.load(sys.stdin)
for diag in d.get('generalDiagnostics', []):
    if diag['severity'] == 'error':
        line = diag['range']['start']['line'] + 1
        rule = diag.get('rule', 'unknown')
        msg = diag['message'].split(chr(10))[0][:100]
        print(f'  L{line} [{rule}] {msg}')
"
```

- [ ] **Step 2: Read the file and understand the errors**

Read `src/mountainash/schema/schema_utils.py` and categorise each error:
- **Bug**: Fix the code (e.g., `"fom"` typo on line 1, missing `__future__` import)
- **Architecture**: Note for future spec (e.g., type narrowing issues)
- **Suppress**: Add `# pyright: ignore[rule]` with comment

- [ ] **Step 3: Apply fixes**

Fix all Bug-category errors. For each fix, ensure existing tests still pass:

```bash
hatch run test:test-quick -- tests/ -x -q
```

- [ ] **Step 4: Verify errors resolved**

```bash
python -m pyright src/mountainash/schema/schema_utils.py --outputjson 2>&1 | python -c "import sys,json; d=json.load(sys.stdin); print(f'Errors: {d[\"summary\"][\"errorCount\"]}')"
```

Expected: `Errors: 0`

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/schema/schema_utils.py
git commit -m "fix: resolve Pyright errors in schema_utils.py

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Triage and fix errors — factories.py (37 errors)

**Files:**
- Modify: `src/mountainash/core/factories.py`

- [ ] **Step 1: Get the specific errors**

```bash
python -m pyright src/mountainash/core/factories.py --outputjson 2>&1 | python -c "
import sys, json
d = json.load(sys.stdin)
for diag in d.get('generalDiagnostics', []):
    if diag['severity'] == 'error':
        line = diag['range']['start']['line'] + 1
        rule = diag.get('rule', 'unknown')
        msg = diag['message'].split(chr(10))[0][:100]
        print(f'  L{line} [{rule}] {msg}')
"
```

Known: 37 `reportOptionalMemberAccess` errors — accessing attributes on a constant that Pyright thinks could be `None`.

- [ ] **Step 2: Read the file, understand the pattern, and fix**

Read `src/mountainash/core/factories.py` around lines 186-200. The constants (`CONST_BACKEND`, etc.) are likely conditionally defined or their types aren't narrowed. Fix with type narrowing (assert, if-check) or correct the type definition.

- [ ] **Step 3: Verify**

```bash
python -m pyright src/mountainash/core/factories.py --outputjson 2>&1 | python -c "import sys,json; d=json.load(sys.stdin); print(f'Errors: {d[\"summary\"][\"errorCount\"]}')"
```

Expected: `Errors: 0`

- [ ] **Step 4: Run tests**

```bash
hatch run test:test-quick -- tests/ -x -q
```

- [ ] **Step 5: Commit**

```bash
git add src/mountainash/core/factories.py
git commit -m "fix: resolve Pyright optional member access errors in factories.py

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Triage and fix errors — remaining files (~120 errors across ~30 files)

**Files:**
- Modify: Various files (see error list from Task 1 Step 2)

- [ ] **Step 1: Get full error list grouped by file**

```bash
python -m pyright src/mountainash/ --outputjson 2>&1 | python -c "
import sys, json
from collections import defaultdict
d = json.load(sys.stdin)
by_file = defaultdict(list)
for diag in d.get('generalDiagnostics', []):
    if diag['severity'] == 'error':
        f = diag['file'].split('mountainash-expressions/')[-1]
        line = diag['range']['start']['line'] + 1
        rule = diag.get('rule', 'unknown')
        msg = diag['message'].split(chr(10))[0][:80]
        by_file[f].append(f'  L{line} [{rule}] {msg}')
for f in sorted(by_file, key=lambda x: -len(by_file[x])):
    print(f'\n{f} ({len(by_file[f])} errors):')
    for e in by_file[f]:
        print(e)
"
```

- [ ] **Step 2: Work through each file**

For each file with errors, apply the triage discipline:
- **Bug**: Fix immediately
- **Architecture**: Note the topic (do not fix — future spec)
- **Suppress**: `# pyright: ignore[rule]  # reason` only as last resort

Key files to expect:
- `expsys_ib_ext_ma_scalar_ternary.py` (26 errors) — likely `reportUndefinedVariable` from Ibis dynamic API
- `auto_gen/__init__.py` (11 errors) — broken relative imports
- `dataframe_system.py` (4 errors) — return type / override issues
- `deprecated/` protocols (8 errors) — may warrant removal if truly deprecated
- `egress_pydata_from_polars.py` (4 errors) — undefined `SchemaConfig`

- [ ] **Step 3: Run full test suite after all fixes**

```bash
hatch run test:test-quick -- tests/ -x -q
```

- [ ] **Step 4: Verify zero Pyright errors**

```bash
python -m pyright src/mountainash/ --outputjson 2>&1 | python -c "import sys,json; d=json.load(sys.stdin); print(f'Errors: {d[\"summary\"][\"errorCount\"]}')"
```

Expected: `Errors: 0`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix: resolve remaining Pyright basic-mode errors across codebase

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Write pyright quality practice principle

**Files:**
- Create: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/g.development-practices/pyright-quality-practice.md`
- Modify: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/CLAUDE.md`

- [ ] **Step 1: Create the principle document**

Create `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/g.development-practices/pyright-quality-practice.md`:

```markdown
# Pyright as an Ongoing Quality Practice

> **Status:** ENFORCED

## The Principle

Pyright type checking is a first-class quality gate alongside ruff (linting) and pytest (testing). It runs at the current configured strictness level before every commit. Pyright findings drive architectural improvements — the response to a category of type errors is to improve the type system, not suppress the errors or weaken the configuration.

## Rationale

Static type checking catches bugs that tests miss — undefined variables, missing imports, incorrect return types, attribute access on wrong types. But type checking is only useful if the error count is zero; a codebase with 1,000 type errors effectively has no type checking because real bugs are invisible in the noise. The ratchet mechanism ensures the project moves from a clean baseline toward full strictness, locking in gains from each architectural improvement.

## Examples

### Three quality gates

| Gate | Command | Catches |
|------|---------|---------|
| Ruff | `hatch run ruff:check` | Style issues, lint errors, unused imports |
| Pytest | `hatch run test:test-quick` | Behavioral regressions, logic errors |
| Pyright | `hatch run pyright:check` | Type errors, missing imports, structural issues |

All three are required before committing.

### The ratchet

```json
// Start: basic mode, architectural rules deferred
{
  "typeCheckingMode": "basic",
  "reportAttributeAccessIssue": false,
  "reportRedeclaration": false,
  "reportOperatorIssue": false,
  "reportArgumentType": false
}

// After generic protocols spec lands:
{
  "typeCheckingMode": "basic",
  "reportAttributeAccessIssue": false,
  "reportRedeclaration": false,
  "reportOperatorIssue": false,
  "reportArgumentType": true  // re-enabled
}

// End state:
{
  "typeCheckingMode": "standard"
}
```

### Triage buckets

When new Pyright errors appear (from upgrading Pyright, enabling rules, or code changes):

| Bucket | Action |
|--------|--------|
| **Bug** | Fix the code |
| **Architecture** | Create a spec for the type system improvement |
| **Suppress** | `# pyright: ignore[rule]  # reason` — last resort only |

## Anti-Patterns

| Anti-Pattern | Why It's Wrong |
|-------------|---------------|
| Disabling a rule because it has too many errors | Fix the root cause or track it as an architectural spec |
| Suppressing errors without comments | Future developers won't know if the suppression is still needed |
| Running Pyright but ignoring the output | A quality gate that nobody checks is not a gate |
| Moving the ratchet backward | Once a rule passes at zero errors, it stays enabled |
| Treating Pyright as a one-off cleanup | Type checking is continuous, like testing |

## Technical Reference

| File | Role |
|------|------|
| `pyrightconfig.json` | Pyright configuration — strictness level and rule overrides |
| `hatch.toml` `[envs.pyright]` | Hatch environment for running Pyright |
| `.venv/` | Virtual environment Pyright resolves imports against |
| `src/mountainash/core/types.py` | Central type aliases (`SupportedExpressions`, `ExpressionT`, etc.) |

## Future Considerations

- As architectural specs land (generic protocols, Ibis type refinement, Polars LazyFrame typing), re-enable the deferred rules one at a time.
- The end state is `typeCheckingMode: "standard"` with zero errors and no deferred rules.
- Consider adding Pyright to CI alongside ruff and pytest once the baseline is stable.
```

- [ ] **Step 2: Add principle to CLAUDE.md table**

Edit `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/CLAUDE.md`. Find the `g. Development Practices` table and add after the `python-environment-setup.md` row:

```markdown
| pyright-quality-practice.md | ENFORCED | Pyright is a first-class quality gate; findings drive architecture, not suppressions; ratchet only moves forward |
```

- [ ] **Step 3: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central && git add 01.principles/mountainash-expresions/g.development-practices/pyright-quality-practice.md && git commit -m "docs: add Pyright quality practice principle

Establishes Pyright as a first-class quality gate alongside
ruff and pytest. Codifies the ratchet mechanism and triage
discipline.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"

cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions && git add CLAUDE.md && git commit -m "docs: reference pyright-quality-practice principle in CLAUDE.md

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Final verification

- [ ] **Step 1: Run all three quality gates**

```bash
hatch run pyright:check
```

Expected: Zero errors.

```bash
hatch run ruff:check
```

Expected: Zero errors (pre-existing).

```bash
hatch run test:test-quick -- tests/ -x -q
```

Expected: All tests pass.

- [ ] **Step 2: Verify CLAUDE.md has both new principles**

```bash
grep -n "pyright-quality-practice\|python-environment-setup" CLAUDE.md
```

Expected: Both principles appear in the Development Practices table.

- [ ] **Step 3: Document architectural improvement topics discovered during triage**

Create a summary comment or note listing all Architecture-bucket items found during Tasks 3-5. These become future spec candidates. Do not commit this as a file — just report it in the task output so the user can decide which to spec next.
