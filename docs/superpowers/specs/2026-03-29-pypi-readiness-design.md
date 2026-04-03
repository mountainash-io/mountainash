# PyPI Readiness for mountainash 0.1.0 — Design Spec

**Roadmap item:** #17 (Layer 6.1-6.3)
**Branch:** `feature/substrait_alignment`
**Date:** 2026-03-29

## Goal

Make the `mountainash` package installable from pypi.org as a clean, minimal, public open-source release. Version 0.1.0 signals "early but usable, API may change."

---

## 1. Package Identity

**Name:** `mountainash`
**Version:** `0.1.0`
**License:** MIT (resolve current conflict — `LICENSE` file says Proprietary, `__version__.py` says MIT)
**Python:** `>=3.10`

### Changes

- Update `src/mountainash/__version__.py` to `__version__ = "0.1.0"`
- Replace `LICENSE` file with MIT license text
- Update `pyproject.toml` description to reflect unified package
- Add `license = "MIT"` to `[project]` section
- Update classifiers: add Python 3.12, set license classifier
- Drop `mountainash_expressions` shim from wheel: update `hatch.toml` `[build.targets.wheel]` to `packages = ["src/mountainash"]` only

---

## 2. Dependencies

### Required (core)

```toml
dependencies = [
    "polars>=1.35.1",
    "narwhals>=1.0.0",
]
```

Polars is the default backend (PydataIngress produces Polars, SourceRelNode defaults to Polars). Narwhals provides cross-backend abstraction.

### Optional extras

```toml
[project.optional-dependencies]
pandas = ["pandas>=2.2.0"]
ibis = ["ibis-framework>=9.0.0"]
pyarrow = ["pyarrow>=15.0.0"]
pydantic = ["pydantic>=2.0.0"]
all = ["mountainash[pandas,ibis,pyarrow,pydantic]"]
```

### Removed entirely

These dependencies are imported nowhere in the source:
- `rich`
- `openlineage-python`
- `sqlalchemy`
- `duckdb`
- `psutil`
- `universal_pathlib`
- `pyarrow-hotfix`
- `numpy` (transitive via polars/pandas, not needed as explicit dep)

### Ibis fork → official PyPI

Switch from local fork (`path = "/home/nathanielramm/git/ibis"`) to official `ibis-framework>=9.0.0` from PyPI. Accept the Polars calendar interval limitation — document in `e.cross-backend/known-divergences.md`.

---

## 3. README Rewrite

Full rewrite of `README.md`. Structure:

### 3.1 Hook (1 paragraph)

What mountainash is: a unified cross-backend DataFrame expression and relation system. Build expressions and query plans once, execute on Polars, Pandas, Ibis, or Narwhals. Includes schema management and Python data ingress/egress.

### 3.2 Installation

```
pip install mountainash                    # Core (Polars + Narwhals)
pip install mountainash[pandas]            # + Pandas backend
pip install mountainash[ibis]              # + Ibis backend (SQL databases)
pip install mountainash[pyarrow]           # + PyArrow backend
pip install mountainash[pydantic]          # + Pydantic model support
pip install mountainash[all]               # Everything
```

### 3.3 Quickstart Examples

**Expressions** — build once, compile to any backend:
```python
import mountainash as ma

expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
polars_expr = expr.compile(polars_df)
pandas_expr = expr.compile(pandas_df)
```

**Relations** — fluent query plans:
```python
result = (
    ma.relation(df)
    .filter(ma.col("age").gt(30))
    .sort("name")
    .head(10)
    .to_polars()
)
```

**Python data in/out** — no DataFrame needed:
```python
result = (
    ma.relation([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
    .filter(ma.col("age").gt(25))
    .to_dicts()
)
# [{"name": "Alice", "age": 30}]
```

**Schema** — deferred definition and application:
```python
schema = ma.schema({
    "age": {"cast": "integer"},
    "name": {"rename": "full_name"},
})
result = schema.apply(df)
```

### 3.4 Backend Support Matrix

| Backend | Install | Expressions | Relations | Schema |
|---------|---------|-------------|-----------|--------|
| Polars | (included) | Full | Full | Full |
| Narwhals | (included) | Full | Full | Full |
| Pandas | `[pandas]` | Full | Via Narwhals | Full |
| Ibis | `[ibis]` | Full | Full | Partial |
| PyArrow | `[pyarrow]` | Via Narwhals | Via Narwhals | Partial |

### 3.5 Architecture Link

Brief mention of the design principles (Substrait-aligned, minimal AST, build-then-execute pattern) with link to principles repo for deeper reading.

### 3.6 License

MIT

---

## 4. Cleanup

### pyproject.toml

- Remove all dead dependencies from `[project.dependencies]`
- Remove commented-out mountainash_constants/settings/utils references from `hatch.toml`
- Update `project.urls` — verify GitHub repo URLs are correct
- Remove `pyproject.toml` pyright venvPath (local machine-specific)
- Add `license = "MIT"` field

### hatch.toml

- Update `[build.targets.wheel]` packages to `["src/mountainash"]` only (drop shim)
- Clean up commented-out dependency blocks in dev/build environments
- Keep test environment with all optional deps installed (tests need all backends)

### Project metadata

- Update classifiers: add Python 3.12
- Verify `project.urls` point to correct repo

---

## 5. Release Process (Manual for 0.1.0)

1. Create release branch from `feature/substrait_alignment` (or merge to main first)
2. All changes from this spec committed
3. `hatch build` — produces wheel + sdist in `dist/`
4. `twine check dist/*` — validates package metadata
5. Test install in clean venv: `pip install dist/mountainash-0.1.0-py3-none-any.whl`
6. Verify: `python -c "import mountainash as ma; print(ma.__version__)"` → `0.1.0`
7. `twine upload dist/*` — publish to pypi.org
8. `git tag v0.1.0` and push tag

CI automation (GitHub Actions trusted publishing) deferred to 0.2.0.

---

## 6. Test Validation

Before release:

### Core-only install test
Install with only `polars` + `narwhals`. Verify:
- `import mountainash as ma` succeeds
- `ma.col("x").gt(5)` builds without error
- `ma.relation(polars_df).filter(...)` works
- `ma.schema({...}).apply(polars_df)` works
- Importing Pandas backend without pandas installed gives helpful error

### Full install test
`pip install mountainash[all]`. Verify:
- Full test suite passes (same results as current: 3859 passed, 7 pre-existing failures)

### Package validation
- `twine check` passes
- Wheel contains only `mountainash` package (no `mountainash_expressions`)
- No local path dependencies in metadata
- License file included in wheel

---

## 7. Known-Divergences Update

Add to `e.cross-backend/known-divergences.md`:
- Ibis calendar interval limitation (was fixed in local fork, not in official release)

---

## Out of Scope

- CI/CD automation for publishing (deferred to 0.2.0)
- Full documentation site (API docs, tutorials)
- `mountainash_expressions` shim on PyPI as a separate redirect package
- Deprecating `ma.table()` / dataframes module (#16 — separate task)
