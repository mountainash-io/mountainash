# PyPI Readiness 0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `mountainash` installable from pypi.org as a clean 0.1.0 release with minimal dependencies.

**Architecture:** Slim dependencies to polars+narwhals core, make everything else optional extras, fix license to MIT, rewrite README, drop backward-compat shim, manual publish via twine.

**Tech Stack:** hatch (build), twine (upload), pyproject.toml + hatch.toml (config)

---

## File Map

| Action | Path | What Changes |
|--------|------|-------------|
| Modify | `pyproject.toml` | Dependencies, version source, license, classifiers, extras, URLs |
| Modify | `hatch.toml` | Drop shim from wheel, clean dead deps from envs |
| Modify | `src/mountainash/__version__.py` | Version → 0.1.0 |
| Replace | `LICENSE` | Proprietary → MIT |
| Rewrite | `README.md` | Full rewrite with accurate description and examples |
| Modify | `src/mountainash/core/lazy_imports.py` | Update install hints for new extras |

---

### Task 1: Fix license and version

**Files:**
- Modify: `LICENSE`
- Modify: `src/mountainash/__version__.py`

- [ ] **Step 1: Replace LICENSE with MIT text**

Replace the entire contents of `LICENSE` with:

```
MIT License

Copyright (c) 2024-present Nathaniel Ramm, Mountain Ash Solutions Pty. Ltd.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Update version to 0.1.0**

In `src/mountainash/__version__.py`, change:

```python
__version__ = "0.1.0"
```

Keep the existing SPDX header.

- [ ] **Step 3: Commit**

```bash
git add LICENSE src/mountainash/__version__.py
git commit -m "chore: set MIT license and version 0.1.0"
```

---

### Task 2: Slim dependencies in pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Replace the entire `[project]` section**

Replace the current `[project]` section (lines 5-42) with:

```toml
[project]
name = "mountainash"
dynamic = ["version"]
description = "Unified cross-backend DataFrame expressions, relations, and schema management"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [
    { name = "Nathaniel Ramm", email = "nathaniel.ramm@discretedatascience.com" },
]
keywords = ["dataframe", "expressions", "polars", "pandas", "ibis", "cross-backend"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: Implementation :: CPython",
    "Topic :: Scientific/Engineering",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Typing :: Typed",
]
dependencies = [
    "polars>=1.35.1",
    "narwhals>=1.0.0",
]
```

- [ ] **Step 2: Replace the `[project.optional-dependencies]` section**

Replace the current optional-dependencies section with:

```toml
[project.optional-dependencies]
pandas = ["pandas>=2.2.0"]
ibis = ["ibis-framework>=9.0.0"]
pyarrow = ["pyarrow>=15.0.0"]
pydantic = ["pydantic>=2.0.0"]
all = ["mountainash[pandas,ibis,pyarrow,pydantic]"]
```

- [ ] **Step 3: Update `[project.urls]`**

```toml
[project.urls]
Homepage = "https://github.com/mountainash-io/mountainash"
Documentation = "https://github.com/mountainash-io/mountainash#readme"
Issues = "https://github.com/mountainash-io/mountainash/issues"
Source = "https://github.com/mountainash-io/mountainash"
```

- [ ] **Step 4: Remove the pyright local venvPath**

Remove these lines (machine-specific):

```toml
[tool.pyright]
venvPath = "/home/nathanielramm/git/mountainash-ide/mountainash-dev-local/.venv"
venv = ".venv"
```

- [ ] **Step 5: Verify the file parses**

Run: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml
git commit -m "chore: slim dependencies to polars+narwhals core, add optional extras"
```

---

### Task 3: Update hatch.toml — drop shim, clean envs

**Files:**
- Modify: `hatch.toml`

- [ ] **Step 1: Drop shim from wheel build**

Change line 8 from:

```toml
packages = ["src/mountainash", "src/mountainash_expressions"]
```

To:

```toml
packages = ["src/mountainash"]
```

- [ ] **Step 2: Clean up dev environment**

Replace the `[envs.dev]` section (lines 13-27) with:

```toml
[envs.dev]
python = "3.12"
installer = "uv"
dependencies = []
```

- [ ] **Step 3: Clean up build_github environment**

Replace the `[envs.build_github]` section (lines 32-48) with:

```toml
[envs.build_github]
installer = "uv"
dependencies = [
    "cyclonedx-bom==4.5.0",
]
[envs.build_github.scripts]
sbom-all = "cyclonedx-py environment > ./sbom-full.xml"
sbom-direct = "cyclonedx-py requirements > ./sbom-direct.xml"
export-requirements = "hatch dep show requirements > ./requirements.txt"
```

- [ ] **Step 4: Clean up default environment**

Replace the `[envs.default]` section (lines 53-61) with:

```toml
[envs.default]
installer = "uv"
dependencies = []
```

- [ ] **Step 5: Clean up test_github environment**

Replace the `[envs.test_github]` section (lines 75-99) with:

```toml
[[envs.test_github.matrix]]
python = ["3.12"]

[envs.test_github]
installer = "uv"
dependencies = [
    "pytest==8.3.5",
    "pytest-check==2.5.3",
    "pytest-cov==6.1.1",
]
[envs.test_github.scripts]
test = "pytest"
test-cov = "pytest --cov --junitxml=junit.xml -o junit_family=legacy --cov-report=xml"
```

- [ ] **Step 6: Clean up test environment — remove dead deps, keep all optional backends**

In the `[envs.test]` dependencies (lines 111-137), replace with:

```toml
[envs.test]
type = "virtual"
installer = "uv"
dependencies = [
    "coverage[toml]>=6.5",
    "pytest==8.3.5",
    "pytest-asyncio>=0.23.0",
    "pytest-check==2.5.3",
    "pytest-mock==3.12.0",
    "pytest-json-report>=1.5.0",
    "pytest-metadata>=2.0.0",
    "pytest-benchmark>=4.0.0",
    "pytest-cov>=4.1.0",
    "pytest-clarity>=1.0.1",
    "pytest-timeout>=2.1.0",
    "pytest-picked>=0.5.0",
    # All optional backends for testing
    "pandas>=2.2.0",
    "ibis-framework[duckdb,sqlite]>=9.0.0",
    "pyarrow>=15.0.0",
    "pydantic>=2.0.0",
    "xarray==2024.11.0",
]
```

- [ ] **Step 7: Remove the large commented-out test env block**

Delete lines 206-267 (the entire commented-out duplicate test environment).

- [ ] **Step 8: Commit**

```bash
git add hatch.toml
git commit -m "chore: drop shim from wheel, clean hatch environments"
```

---

### Task 4: Update lazy_imports install hints

**Files:**
- Modify: `src/mountainash/core/lazy_imports.py`

- [ ] **Step 1: Update INSTALL_COMMANDS to use extras syntax**

Replace the `INSTALL_COMMANDS` dict with:

```python
INSTALL_COMMANDS = {
    "pandas": "pip install 'mountainash[pandas]'",
    "polars": "pip install polars>=1.35.1",
    "pyarrow": "pip install 'mountainash[pyarrow]'",
    "ibis": "pip install 'mountainash[ibis]'",
    "ibis.expr.types": "pip install 'mountainash[ibis]'",
    "narwhals": "pip install narwhals",
    "pydantic": "pip install 'mountainash[pydantic]'",
}
```

- [ ] **Step 2: Update convenience function hints**

Update `import_pandas()`:
```python
def import_pandas() -> Any:
    """Lazy import of pandas."""
    return require_module("pandas", "pip install 'mountainash[pandas]'")
```

Update `import_pyarrow()`:
```python
def import_pyarrow() -> Any:
    """Lazy import of pyarrow."""
    return require_module("pyarrow", "pip install 'mountainash[pyarrow]'")
```

Update `import_ibis()`:
```python
def import_ibis() -> Any:
    """Lazy import of ibis."""
    return require_module("ibis", "pip install 'mountainash[ibis]'")
```

Update `import_ibis_expr_types()` and `import_ibis_expr_ops()` similarly — change the hint strings to `"pip install 'mountainash[ibis]'"`.

Update `import_pydantic()`:
```python
def import_pydantic() -> Any:
    """Lazy import of pydantic."""
    return require_module("pydantic", "pip install 'mountainash[pydantic]'")
```

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/core/lazy_imports.py
git commit -m "chore: update lazy import hints for mountainash extras syntax"
```

---

### Task 5: Rewrite README.md

**Files:**
- Rewrite: `README.md`

- [ ] **Step 1: Replace README.md with full rewrite**

Replace the entire contents of `README.md` with:

```markdown
# mountainash

[![PyPI](https://img.shields.io/pypi/v/mountainash.svg)](https://pypi.org/project/mountainash/)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Build DataFrame expressions and query plans once, execute on any backend. Mountainash provides a unified API for expressions, relations, schema management, and Python data ingress/egress across Polars, Pandas, Ibis, Narwhals, and PyArrow.

## Installation

```bash
pip install mountainash                    # Core (Polars + Narwhals)
pip install 'mountainash[pandas]'          # + Pandas backend
pip install 'mountainash[ibis]'            # + Ibis backend (SQL databases)
pip install 'mountainash[pyarrow]'         # + PyArrow backend
pip install 'mountainash[pydantic]'        # + Pydantic model support
pip install 'mountainash[all]'             # Everything
```

## Quick Start

### Expressions — build once, compile to any backend

```python
import mountainash as ma

# Build a backend-agnostic expression
expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))

# Compile to any backend — auto-detected from DataFrame type
polars_expr = expr.compile(polars_df)
pandas_expr = expr.compile(pandas_df)
ibis_expr = expr.compile(ibis_table)
```

### Relations — fluent query plans

```python
result = (
    ma.relation(df)
    .filter(ma.col("age").gt(30))
    .sort("name")
    .head(10)
    .to_polars()
)
```

### Python data — no DataFrame needed

```python
# Python data in, Python data out
result = (
    ma.relation([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ])
    .filter(ma.col("age").gt(25))
    .to_dicts()
)
# [{"name": "Alice", "age": 30}]
```

### Schema — deferred definition and application

```python
schema = ma.schema({
    "age": {"cast": "integer"},
    "name": {"rename": "full_name"},
    "score": {"null_fill": 0.0},
})
result = schema.apply(df)  # Backend auto-detected
```

## Features

- **Cross-backend expressions** — same expression compiles to Polars, Pandas, Ibis, Narwhals, or PyArrow
- **Relational query plans** — filter, sort, join, group_by, window functions — all backend-agnostic
- **Schema management** — define, extract, validate, and apply schemas across backends
- **Python data support** — ingest lists, dicts, dataclasses, Pydantic models; output to any format
- **Ternary logic** — three-valued TRUE/FALSE/UNKNOWN semantics for real-world data with missing values
- **Automatic backend detection** — no manual configuration; backend determined from DataFrame type
- **Substrait-aligned** — expression and relation ASTs follow the [Substrait](https://substrait.io/) specification

## Backend Support

| Backend | Install | Expressions | Relations | Schema |
|---------|---------|:-----------:|:---------:|:------:|
| Polars | *(included)* | Full | Full | Full |
| Narwhals | *(included)* | Full | Full | Full |
| Pandas | `[pandas]` | Full | Via Narwhals | Full |
| Ibis | `[ibis]` | Full | Full | Partial |
| PyArrow | `[pyarrow]` | Via Narwhals | Via Narwhals | Partial |

## Architecture

Mountainash separates **building** from **execution**. Expressions, relations, and schemas are defined as backend-agnostic AST nodes. Execution happens when a terminal method is called (`.compile()`, `.collect()`, `.apply()`), which auto-detects the backend and produces native operations.

```
Build phase (no backend needed)     Execute phase (backend auto-detected)
─────────────────────────────────   ──────────────────────────────────────
ma.col("x").gt(5)                   .compile(polars_df) → pl.col("x") > 5
ma.relation(df).filter(...)         .to_polars()        → pl.DataFrame
ma.schema({"x": {"cast": "int"}})  .apply(df)          → transformed df
```

For deeper architectural details, see the [design principles](https://github.com/mountainash-io/mountainash-central/tree/main/01.principles/mountainash-expresions).

## Development

```bash
git clone https://github.com/mountainash-io/mountainash.git
cd mountainash

# Run tests
hatch run test:test              # Full suite with coverage
hatch run test:test-quick        # Fast iteration (no coverage)

# Linting
hatch run ruff:check
hatch run ruff:fix

# Type checking
hatch run mypy:check
```

## License

MIT License. See [LICENSE](LICENSE) for details.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for public PyPI release"
```

---

### Task 6: Build, validate, and test install

- [ ] **Step 1: Build the package**

Run: `hatch build`
Expected: Creates `dist/mountainash-0.1.0-py3-none-any.whl` and `dist/mountainash-0.1.0.tar.gz`

- [ ] **Step 2: Validate with twine**

Run: `pip install twine && twine check dist/*`
Expected: `PASSED` for both wheel and sdist.

- [ ] **Step 3: Verify wheel contents — no shim**

Run: `python -m zipfile -l dist/mountainash-0.1.0-py3-none-any.whl | head -20`
Expected: Only `mountainash/` entries, no `mountainash_expressions/`.

- [ ] **Step 4: Test install in clean venv**

```bash
python -m venv /tmp/test-ma-install
/tmp/test-ma-install/bin/pip install dist/mountainash-0.1.0-py3-none-any.whl
/tmp/test-ma-install/bin/python -c "import mountainash as ma; print(ma.__version__); print(ma.col('x'))"
```

Expected: Prints `0.1.0` and an expression object.

- [ ] **Step 5: Test optional backend error message**

```bash
/tmp/test-ma-install/bin/python -c "
import mountainash as ma
try:
    from mountainash.core.lazy_imports import import_pandas
    import_pandas()
except ImportError as e:
    print('Good:', e)
"
```

Expected: Prints helpful error mentioning `pip install 'mountainash[pandas]'`.

- [ ] **Step 6: Clean up test venv**

```bash
rm -rf /tmp/test-ma-install
```

- [ ] **Step 7: Run full test suite to verify nothing broke**

Run: `hatch run test:test-quick`
Expected: Same results as before (3859 passed, 7 pre-existing failures).

- [ ] **Step 8: Commit any fixups**

```bash
git add -A
git commit -m "chore: build validation fixups for 0.1.0"
```

Note: Only commit if there were fixups needed. Skip if everything passed clean.
