# Claude Code Python Environment Alignment

**Date:** 2026-03-30
**Status:** Approved
**Goal:** Ensure Claude Code's Pyright LSP and Bash tool calls share the same Python environment as the project, with live edits and no disruption to global tools.

## Problem

When running `claude` from the project directory, the system Python (`~/.rye/tools/uv/bin/python3`) is used. This Python has no knowledge of `mountainash` or its dependencies. Pyright LSP analyses against this wrong environment, producing false import errors and missing type information. Bash tool calls (`python`, `python3`) also resolve to the system Python.

Meanwhile, the hatch test environment at a hashed path (`~/.local/share/hatch/env/virtual/mountainash/fzI3Cv0h/test.py3.12`) has the package installed but is not visible to Claude Code or Pyright.

## Constraints

- Must not break global CLI tools (`hatch`, `uv`, `gh`, etc.)
- Must not break global Python packages (e.g., hiivmind-corpus dependencies)
- Must support editable install so `src/mountainash/` changes are live
- Zero workflow change — user runs `claude` from project dir as before
- Local ibis fork must be installed from `/home/nathanielramm/git/ibis`

## Solution

Three coordinated pieces:

### 1. Local `.venv` with editable install

Create a `.venv` in the project root using `uv`, with `--system-site-packages` to allow fallthrough to globally installed Python packages:

```bash
uv venv .venv --python 3.12 --system-site-packages
uv pip install -e ".[all]" --python .venv/bin/python
uv pip install -e /home/nathanielramm/git/ibis --python .venv/bin/python
```

The editable install (`-e`) means changes to `src/mountainash/` are immediately visible without reinstalling. The `--system-site-packages` flag ensures global packages (needed by plugins like hiivmind-corpus) remain importable.

### 2. `pyrightconfig.json` in project root

```json
{
  "venvPath": ".",
  "venv": ".venv"
}
```

Tells Pyright to resolve imports from `.venv`. While Pyright can auto-discover `.venv`, being explicit avoids ambiguity from coexisting hatch environments.

### 3. `.claude/settings.local.json` env block

Prepend `.venv/bin` to `PATH` in the project-level Claude Code settings. This is merged with the existing `permissions` block:

```json
{
  "env": {
    "PATH": "/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/.venv/bin:${PATH}"
  },
  "permissions": {
    "allow": [...]
  }
}
```

Key decisions:
- **No `VIRTUAL_ENV`** — setting it would signal full isolation and could hide global packages
- **PATH prepend only** — `.venv/bin` is first, so `python`/`python3` resolve there; everything else falls through to the global PATH

## What changes

| Component | Before | After |
|-----------|--------|-------|
| `python` in Bash | `~/.rye/tools/uv/bin/python3` (no mountainash) | `.venv/bin/python` (editable mountainash + deps) |
| Pyright LSP | System Python (false errors) | `.venv` (correct resolution) |
| Global CLI tools | Available | Still available (PATH fallthrough) |
| Global Python packages | Available | Still available (`--system-site-packages`) |
| Workflow | `cd project && claude` | Same, no change |

## What does NOT change

- Hatch environments (still used for `hatch run test:test`, linting, etc.)
- Global Claude Code settings
- Launch workflow
- `.gitignore` (`.venv/` is conventionally ignored)

## Files touched

1. **New:** `pyrightconfig.json` (project root)
2. **Modified:** `.claude/settings.local.json` (add `env` block)
3. **New:** `.venv/` directory (not committed, gitignored)
