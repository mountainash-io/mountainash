---
title: Contributing and testing
---

# Contributing and testing

Work on mountainash happens in a source checkout with Hatch environments. A change follows the package's naming, import and error conventions, and is proven by cross-backend tests that run the same assertion on every backend in the test registry, with any backend-specific failure declared per backend and strictly. Contributors mostly reach for three commands: a targeted test run, the linter, and the reports that track known gaps and upstream issues.

Assumes: [Installation and the package surface](../02-installation-and-package-surface/index.md), [Architecture](../17-architecture/index.md), [Backends](../21-backends/index.md) and [Backend support and known limits](../16-backend-support-and-limits/index.md).

The `test` environment in `hatch.toml` (Python 3.12, installed with uv) holds every optional backend at the versions the capability declarations were checked against: pandas, Ibis with DuckDB and SQLite, Dask, PyArrow, and exact or bounded pins for Narwhals and DuckDB. It also installs the sibling packages from local checkouts next to this one (`../mountainash-files`, `../mountainash-transport`, `../mountainash-settings`, `../mountainash-auth-client` and `../mountainash-data`), which is how a checkout works while those packages are not published (see [Where mountainash sits](../02-installation-and-package-surface/index.md#where-mountainash-sits)). The `test_github` environment is the same set with the siblings in `temp/`, where CI clones them.

```bash
# siblings cloned beside the mountainash checkout, then:
hatch run test:test-target-quick tests/expressions/cross_backend/test_null_nan_clip.py
hatch run test:test-target tests/core/test_protocol_alignment.py   # with coverage
hatch run ruff:check                                               # ruff over src/
```

## Naming and import conventions

<!-- concept:549 -->
File and class names encode the layer, the origin (Substrait or mountainash extension), the backend and the category, so a file can be found by constructing its name. This is how the [three layers](../17-architecture/index.md#three-layer-separation) appear on disk:

| Prefix or part | Meaning | Example |
|---|---|---|
| `exn_` | Expression AST node | `exn_scalar_function.py` |
| `prtcl_expsys_` | Expression-system protocol | `prtcl_expsys_scalar_comparison.py` |
| `prtcl_api_bldr_` | API builder protocol | `prtcl_api_bldr_scalar_comparison.py` |
| `api_bldr_` | API builder | `api_bldr_scalar_comparison.py` |
| `expsys_pl_`, `expsys_nw_`, `expsys_ib_` | Expression system for Polars, Narwhals, Ibis | `expsys_ib_scalar_comparison.py` |
| `reln_` | Relation AST node | `reln_join.py` |
| `prtcl_relsys_` | Relation-system protocol | `prtcl_relsys_join.py` |
| `relsys_pl_`, `relsys_nw_`, `relsys_ib_` | Relation system per backend | `relsys_pl_join.py` |
| `ext_ma_` infix | mountainash extension, not Substrait | `expsys_pl_ext_ma_null.py` |
| leading `_` | Private module | `_sqlite_compat.py` |

Substrait and extension code sit in parallel `substrait/` and `extensions_mountainash/` directories at every layer (the expression-node extension directory is named `mountainash_extensions/`). Enums follow the same split, `FKEY_SUBSTRAIT_*` and `FKEY_MOUNTAINASH_*` for functions and `RKEY_SUBSTRAIT_REL` and `RKEY_MOUNTAINASH_REL` for relations, and so do classes: `SubstraitPolarsScalarComparisonExpressionSystem`, `MountainAshPolarsNullExpressionSystem`, composed into `PolarsExpressionSystem`. Every file of one category can be listed by its suffix:

```python
from pathlib import Path
import mountainash

root = Path(mountainash.__file__).parent / "expressions"
for path in sorted(root.rglob("*ext_ma_null.py")):
    print(path.relative_to(root))
```

```text
backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_null.py
backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_null.py
backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_null.py
core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_null.py
core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_null.py
core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_null.py
```

<!-- concept:550 -->
Imports keep the package cheap to import, as described in [The top-level namespace](../02-installation-and-package-surface/index.md#the-top-level-namespace). Each import is one of four kinds:

- Standard library: imported at the top.
- Used at run time: imported at the top. Non-backend code that calls an optional library imports it through `mountainash.core.lazy_imports` (`import_narwhals()`, `import_ibis()` and so on), which raises a message naming the missing extra.
- Annotation only: imported under `if TYPE_CHECKING:`, with `from __future__ import annotations` as the file's first import.
- Package re-export: a package `__init__.py` with heavy submodules uses `lazy_loader.attach()`.

A symbol is never imported both ways, and no module installs stub modules for missing libraries. Backend files under `expressions/backends/` and `relations/backends/` import their library unconditionally because they run only once that backend is detected; node and relation-protocol files import types at run time for Pydantic fields. Ruff enforces this through the `FA` and `TCH` rules (with per-file exemptions for those directories) alongside `E` and `F`, configured in `pyproject.toml` and run on `src/` by `hatch run ruff:check`. A subprocess shows the result:

```python
import subprocess
import sys

probe = ("import sys, mountainash as ma; "
         "heavy = ('polars', 'pandas', 'ibis', 'narwhals', 'pyarrow', 'mountainash.exceptions'); "
         "print([m for m in heavy if m in sys.modules]); ma.col; "
         "print([m for m in heavy if m in sys.modules])")
print(subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True).stdout)
```

```text
[]
['polars', 'ibis', 'narwhals']

```

## Typed error conventions

<!-- concept:554 -->
Every error mountainash raises deliberately belongs to the [`MountainashError` hierarchy](../02-installation-and-package-surface/index.md#errors). The rules for adding one:

- Define it in the owning subsystem's `errors.py` (`core/errors.py`, `conform/errors.py`, `relations/dag/errors.py`, `pipelines/errors.py` and so on). The root in `core/errors.py` is a bare marker class with no constructor, so subclasses construct exactly like the builtin they replace.
- Give a subsystem a domain base only when it has two or more errors; a single error derives from the root directly. When a second error arrives, add the base then.
- Keep builtin compatibility through multiple inheritance, mountainash base first and builtin second: `class DtypeError(MountainashError, ValueError)`. When all children share one builtin, put it on the domain base; when they differ, put it on each leaf (`RelationDAGRequired(DAGError, RuntimeError)`, `MissingResourceSchema(DAGError, ValueError)`). Moving an existing error into the hierarchy never drops the builtin it had.
- Re-export it from `mountainash/exceptions.py`, the public facade, which defines nothing. Re-export domain bases from the subsystem package too (`DAGError` from `mountainash.relations.dag`, `DtypeError` from `mountainash.core.dtypes`). The package `__init__` exports only the root and must not import the facade; `tests/test_exceptions_facade.py` checks this in a fresh subprocess.

Converting old bare raises is a ratchet, not a sweep. New code never raises a bare `ValueError`, `KeyError`, `TypeError`, `IndexError` or `RuntimeError`; a change to a file converts that file's bare raises; public API paths (relations, DAG, entry points) come first. There is deliberately no test counting the remaining bare raises. Compatibility is tested in `tests/core/test_errors.py` and the `test_error_hierarchy.py` files under `tests/conform/`, `tests/core/dtypes/` and `tests/pipelines/`.

The facade can drift from the definitions, and one audit finds both kinds of gap: typed errors the facade does not re-export, and exception classes outside the hierarchy.

```python
import importlib
import inspect
import mountainash as ma
import mountainash.exceptions as facade

exported = {obj for obj in vars(facade).values() if inspect.isclass(obj)}
for name in ["conform", "core.dtypes", "graph", "pipelines", "relations.core", "relations.dag"]:
    module = importlib.import_module(f"mountainash.{name}.errors")
    defined = [c for c in vars(module).values()
               if inspect.isclass(c) and c.__module__ == module.__name__ and issubclass(c, Exception)]
    print(name, sorted(c.__name__ for c in defined
                       if issubclass(c, ma.MountainashError) and c not in exported),
          sorted(c.__name__ for c in defined if not issubclass(c, ma.MountainashError)))
```

```text
conform ['DecimalConversionRequiredError'] []
core.dtypes ['InvalidBackendTypeError'] []
graph [] ['CycleError', 'DuplicateNodeError', 'UnknownNodeError']
pipelines ['AmbiguousWrite', 'EmptyUnitOutput', 'IncompatibleResume', 'IncompleteCoverage', 'NonRetryable', 'PipelineError', 'UnhashableIdentityInput', 'UnitFailed', 'UnsupportedValueKind'] []
relations.core ['CompileRequiresExecutionError', 'ConflictingExecutionTargetError', 'MaterializationScopeClosedError', 'UnregisteredRelationNodeError', 'UnresolvedExecutionLocationError', 'UnsupportedRelationTransportError'] []
relations.dag ['MissingFilesDependency', 'ResourceSchemaCastError', 'UnknownRelationRef'] []
```

The first list per module is typed errors to add to the facade; the second is errors still outside the hierarchy (the graph kernel's errors derive only from `KeyError` and `ValueError`). Both are open migration work under the ratchet.

## Cross-backend testing

<!-- concept:551 -->
The cross-backend suite is the primary test suite: one test per behaviour, parametrised over backends, with the same assertion for each. The backends are defined once, in `tests/fixtures/backend_registry.py`. Each `BackendSpec` names a family, a materialisation (eager, lazy or deferred) and a builder for the native object. `ALL_BACKENDS` lists every registry entry; `MATRIX_BACKENDS` adds two backends used only as sources and destinations in the operand-transfer matrix; `PR_BACKENDS` picks one backend per engine family ([Polars](../21-backends/index.md#polars), [Narwhals](../21-backends/index.md#narwhals-and-its-providers) and [Ibis](../21-backends/index.md#ibis-and-sql-dialects)).

```python
sys.path.insert(0, "tests")  # run from the repository root
from fixtures.backend_registry import ALL_BACKENDS, MATRIX_BACKENDS, PR_BACKENDS

print(ALL_BACKENDS)
print(sorted(set(MATRIX_BACKENDS) - set(ALL_BACKENDS)))
print(PR_BACKENDS)
```

```text
['polars', 'polars-lazy', 'pandas', 'narwhals-polars', 'narwhals-pandas', 'ibis-duckdb', 'ibis-sqlite', 'narwhals-lazy']
['ibis-polars', 'narwhals-pyarrow']
['polars', 'narwhals-polars', 'ibis-duckdb']
```

A test creates its frame with `backend_factory.create(data, backend_name)` and extracts results with `collect_expr(df, expr)` or `collect_col(df, name)`. Both go through the relation API's egress, the path users take, rather than ad hoc `.execute()` or `.to_list()` calls that confuse null with NaN. `select_and_extract` is kept only for tests that pass an explicit booleanizer to `.compile()`. A test file looks like this:

```python
import pytest
import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRound:
    def test_round_two_places(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create({"val": [1.555, 2.345, 3.789]}, backend_name)
        assert collect_expr(df, ma.col("val").round(2)) == [1.56, 2.35, 3.79]
```

The data is discriminating: had the `2` been dropped or defaulted, the assertion would fail. An operation with parameters is tested with a non-default value and an extracted result, not just a filter count. The minimum backend set for a new expression test is `polars`, `narwhals-polars` and `ibis-duckdb`; a Polars-only test is allowed only for Polars-internal wiring, with the reason in its docstring. Tests are never skipped, never mock a backend, and are never edited to match a wrong result.

Run tests by target, never the whole suite during development; this is the project's standing guidance, because the full suite runs every test against eight backends. Name the file or directory a change touches with `hatch run test:test-target-quick <path>` (or `test-target` for coverage). `MA_BACKEND_SCOPE=pr` (or `--ma-backend-scope pr`) deselects out-of-scope backend cases at collection, and `hatch run test:affected` selects tests from the diff against `develop`. The full run is for CI and a single pre-merge gate; the default CI script runs the compile smoke suite (`tests/core/test_compile_smoke.py`). Markers are strict: tier markers (`unit`, `cross_backend`, `integration`, `contract`) are declared in `pytest.ini`, and unmarked tests receive a tier at collection.

<!-- concept:553 -->
Protocol alignment tests keep the [protocols](../17-architecture/index.md#protocols-as-contracts) and their implementations in step. They discover what to check by introspection and fail on anything they cannot place, so a new protocol, method, key or parameter fails until it is wired or listed as a known gap with a reason and a date:

| File | Checks |
|---|---|
| `tests/core/test_protocol_alignment.py` | Every expression-system and API-builder protocol method is implemented by every backend with matching parameter names, with no backend method lacking a protocol; Substrait and extension classes do not cross-inherit or share names; `TestWiringAudit` requires a key, a mapping and three backend implementations per method, and `test_no_orphan_enums` rejects keys with no protocol method; `TestNativeAdapterAlignment` checks the dtype and schema adapters |
| `tests/relations/protocol_alignment/` | The same symmetry for relation systems |
| `tests/relations/test_rel_wiring_audit.py` | Every concrete relation node is dispatchable by key or by a registered handler |
| `tests/relations/dag/test_dag_protocol_alignment.py` | The DAG relation surface |
| `tests/expressions/argument_types/test_coverage_guard.py` | Every expression parameter appears in some category's `TESTED_PARAMS`, exercised by `OpSpec` cases with raw, `ma.lit`, `ma.col` and compound inputs |

Known gaps in `KNOWN_ASPIRATIONAL` run as strict expected failures, so wiring one makes its case pass unexpectedly and fail until the entry is removed. These files are load-bearing and are never disabled.

## Known divergences and per-backend xfail

<!-- concept:552 -->
A backend that fails a cross-backend test stays in the parametrisation; the failure is declared for that backend only, strictly, with a reason that names the cause. Omitting a backend hides the difference, a blanket expected failure on every backend hides which ones pass, and a non-strict marker keeps passing when the behaviour changes. What a backend [cannot do or does differently](../16-backend-support-and-limits/index.md#known-divergences) is owned by the capability declarations; tests consume them instead of keeping their own backend lists. The tests use four mechanisms:

- A gated call is asserted as a refusal: `pytest.raises(BackendCapabilityError)` around `compile()`, then checks on the error's `function_key`.
- A wrong result or native error on named backends uses `expect_call_failure` from `tests/fixtures/call_expectations.py`. Only the call and its assertion run inside it; fixture setup stays outside. It turns into an expected failure only for the exact exception types listed (subtypes and unrelated errors propagate), and when the call succeeds it fails the test as a strict unexpected pass.
- A whole test that fails on one backend carries `pytest.param("ibis-duckdb", marks=pytest.mark.xfail(strict=True, reason=...))` in its parametrize list.
- Protocol gaps live in `KNOWN_ASPIRATIONAL`. A last-resort marker for a gap with no declaration yet must be recorded in `tests/_sp2b_park_registry.yaml`; `tests/core/test_sp2b_park_registry.py` rejects one that is unrecorded, not strict, or (for a gate) missing `raises=BackendCapabilityError`. The registry is currently empty.

`fill_nan` on Ibis DuckDB, from `tests/expressions/cross_backend/test_null_nan_clip.py`:

```python
expr = ma.col("val").fill_nan(0.0)
with expect_call_failure(
    when=backend_name == "ibis-duckdb",
    reason="is_nan/fill_nan/NaN comparisons diverge on SQL engines.",
    errors=(AssertionError,),
):
    actual = collect_expr(df, expr)
    assert actual == [1.0, 0.0, 3.0, 0.0, 5.0], f"[{backend_name}] got {actual}"
```

A strict unexpected pass means behaviour changed. Find out why before touching the test: narrow or retire the capability declaration if the backend now behaves correctly, then remove the expectation, and keep the ordinary assertion as the regression. An expected upstream fix is not a reason for `strict=False`.

Upstream causes are tracked in `registry/upstream-issues.yaml`, one entry per issue with an ID such as `IB-STR-01`, the affected backends, the upstream link, a status and a last-verified date. Capability information records refer to an entry through their `issue` field. `tests/core/test_upstream_registry_join.py` fails when a reference has no entry, or when an open entry has no reference and no status that allows that. Three scripts serve maintainers:

```bash
python scripts/validate_upstream_registry.py      # schema of upstream-issues.yaml
python scripts/audit_upstream_issues.py --skip-github             # local registry report only
python scripts/audit_upstream_issues.py --report-file report.md   # live GitHub issue states and candidates
python scripts/report_drift_guards.py --report-file drift.md      # aspirational gaps, literal-only declarations, manual xfail blocks
```

A closed upstream issue or a dependency upgrade starts a check, not a removal: exercise the affected operation on each declared backend and version, then update the declaration, the test expectations and the registry entry together.
