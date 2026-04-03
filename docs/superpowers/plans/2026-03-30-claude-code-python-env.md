# Claude Code Python Environment Alignment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure a local `.venv` with editable install, Pyright config, and Claude Code PATH so that LSP and Bash tool calls share the correct Python environment.

**Architecture:** Three independent pieces — a `.venv` created by `uv`, a `pyrightconfig.json` for LSP, and a PATH prepend in `.claude/settings.local.json`. Each piece is verified independently before moving on.

**Tech Stack:** uv, Pyright, Claude Code settings

---

### Task 1: Create local `.venv` with editable install

**Files:**
- Create: `.venv/` (not committed — already in `.gitignore`)

- [ ] **Step 1: Create the venv**

```bash
uv venv .venv --python 3.12 --system-site-packages
```

Expected: `.venv/` directory created, output includes `Using CPython 3.12.x` and `Activate with: source .venv/bin/activate`

- [ ] **Step 2: Install mountainash in editable mode with all extras**

```bash
uv pip install -e ".[all]" --python .venv/bin/python
```

Expected: Installs `mountainash` plus `polars`, `narwhals`, `pydantic`, `typing_extensions`, `lazy_loader`, `pandas`, `ibis-framework`, `pyarrow`. Output shows `Installed X packages`.

- [ ] **Step 3: Install local ibis fork**

```bash
uv pip install -e /home/nathanielramm/git/ibis --python .venv/bin/python
```

Expected: Replaces the PyPI `ibis-framework` with the editable local fork. Output shows `Installed X packages`.

- [ ] **Step 4: Verify the venv works**

```bash
.venv/bin/python -c "import mountainash; print(mountainash.__file__)"
```

Expected: Prints a path under `src/mountainash/__init__.py` (editable install resolves to source tree).

```bash
.venv/bin/python -c "import ibis; print(ibis.__file__)"
```

Expected: Prints a path under `/home/nathanielramm/git/ibis/` (local fork, not PyPI).

- [ ] **Step 5: Verify system-site-packages fallthrough**

```bash
.venv/bin/python -c "import sys; print(any('site-packages' in p and '.venv' not in p for p in sys.path))"
```

Expected: `True` — confirms global site-packages are on the path.

---

### Task 2: Add `pyrightconfig.json`

**Files:**
- Create: `pyrightconfig.json` (project root)

- [ ] **Step 1: Create `pyrightconfig.json`**

Create `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/pyrightconfig.json`:

```json
{
  "venvPath": ".",
  "venv": ".venv"
}
```

- [ ] **Step 2: Verify Pyright resolves mountainash**

```bash
.venv/bin/python -m pyright --version 2>/dev/null || uv pip install pyright --python .venv/bin/python && .venv/bin/python -m pyright --outputjson src/mountainash/__init__.py 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Errors: {d[\"summary\"][\"errorCount\"]}, Warnings: {d[\"summary\"][\"warningCount\"]}')"
```

Expected: Low or zero error count. Previously, Pyright against system Python would report many `import could not be resolved` errors. If errors persist, they should be real type errors — not missing-import false positives.

- [ ] **Step 3: Commit**

```bash
git add pyrightconfig.json
git commit -m "chore: add pyrightconfig.json pointing Pyright at local .venv"
```

---

### Task 3: Update `.claude/settings.local.json` with PATH prepend

**Files:**
- Modify: `.claude/settings.local.json`

- [ ] **Step 1: Add env block to settings**

Edit `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/.claude/settings.local.json` to add the `env` key at the top level, alongside the existing `permissions` key:

```json
{
  "env": {
    "PATH": "/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/.venv/bin:${PATH}"
  },
  "permissions": {
    "allow": [
      ... existing entries unchanged ...
    ],
    "deny": [],
    "ask": []
  }
}
```

Only the `"env"` block is new. The `"permissions"` block stays exactly as-is.

- [ ] **Step 2: Verify PATH prepend works (requires Claude Code restart)**

After restarting Claude Code (`claude` from project dir), run:

```bash
which python
```

Expected: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/.venv/bin/python`

```bash
python -c "import mountainash; print(mountainash.__file__)"
```

Expected: Path under `src/mountainash/__init__.py`

- [ ] **Step 3: Verify global tools still accessible**

```bash
which hatch && which uv && which gh
```

Expected: All three resolve (to their global paths, not blocked by `.venv`).

- [ ] **Step 4: Commit**

```bash
git add .claude/settings.local.json
git commit -m "chore: prepend .venv/bin to PATH in Claude Code project settings"
```

---

### Task 4: End-to-end verification

- [ ] **Step 1: Restart Claude Code**

Exit and re-launch `claude` from the project directory.

- [ ] **Step 2: Verify LSP resolution**

Use Claude Code's LSP tool to check a mountainash import:

```
LSP hover over: src/mountainash/__init__.py — any exported symbol
```

Expected: Pyright returns type information (not "could not be resolved").

- [ ] **Step 3: Verify Bash Python**

```bash
python -c "from mountainash import col; print(type(col('x')))"
```

Expected: Prints the Expression type (not `ModuleNotFoundError`).

- [ ] **Step 4: Verify global tools**

```bash
hatch --version && uv --version && gh --version
```

Expected: All return version info.

- [ ] **Step 5: Verify editable install is live**

Make no-op check — confirm that the mountainash `__init__.py` Pyright sees is the actual source file, not a copy:

```bash
python -c "import mountainash; import os; print(os.path.realpath(mountainash.__file__))"
```

Expected: Resolves to `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/src/mountainash/__init__.py`
