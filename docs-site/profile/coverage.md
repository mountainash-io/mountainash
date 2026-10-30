# Coverage Report

- **Generated:** 2026-10-30
- **Source:** `src/mountainash` at `1d32ab4a30c20bb2ec3bb11cc0a27636694ed3cd` (develop); previous profile `00e99834`
- **Behavior:** full refresh. 1208 commits and 695 changed source files since the previous profile, 13 new module boundaries, and the prior profile failed the current schema.

## Module coverage

| Status | Count | Details |
|---|---|---|
| Discovered | 40 | 38 profiled + 2 ignored |
| Ignored | 2 | `src/mountainash/__version__.py`, `src/mountainash/expressions/__version__.py` (version strings only) |
| Missing profiles | 0 | Every `.py` file under the package root maps to one module scope |
| Stale profiles | 0 | All records refreshed to the target hash |
| Orphaned profiles | 0 | All 25 prior module ids retained; 19 legacy filenames (`expressions-api.json`, etc.) replaced by `<id>.json` |

### Topology changes since `00e99834`

New module boundaries: `exceptions`, `core.capabilities`, `core.dtypes`, `validation`, `pydata`, `expressions`, `expressions.membership`, `expressions.backends.capabilities`, `relations`, `relations.core`, `relations.core.execution`, `relations.core.relation_system`, `relations.backends.capabilities`.

Ownership notes: `expressions/backends/expression_systems/base.py` belongs to `expressions.core.expression_system`. `relations/backends/relation_systems/base.py` and `resource_files.py` belong to `relations.core.relation_system`. `core` covers only the loose files directly in `core/`, and `relations.core` covers only the loose files directly in `relations/core/`. `src/mountainash/utils/graph/` contains no source files, only `__pycache__`.

## Classification summary

| Module | Role | Visibility | Priority | Confidence |
|---|---|---|---|---|
| `conform` | orchestration | semi-public | essential | high |
| `core.capabilities` | orchestration | semi-public | essential | medium |
| `core.dtypes` | model | semi-public | essential | high |
| `core` | orchestration | semi-public | useful | high |
| `datacontracts` | public-api | public | essential | high |
| `exceptions` | public-api | public | useful | high |
| `expressions.backends.capabilities` | backend | internal | useful | high |
| `expressions.backends.ibis` | backend | semi-public | useful | medium |
| `expressions.backends.narwhals` | backend | semi-public | useful | medium |
| `expressions.backends.polars` | backend | semi-public | useful | high |
| `expressions.core.expression_api` | api-builder | public | essential | high |
| `expressions.core.expression_nodes` | model | semi-public | useful | high |
| `expressions.core.expression_protocols` | protocol | semi-public | useful | high |
| `expressions.core.expression_system` | orchestration | semi-public | useful | high |
| `expressions.core.unified_visitor` | orchestration | semi-public | useful | medium |
| `expressions` | public-api | public | essential | high |
| `expressions.membership` | model | internal | reference-only | high |
| `graph` | model | public | reference-only | high |
| `pipelines` | orchestration | public | essential | medium |
| `pydata.egress` | io | public | useful | medium |
| `pydata.ingress` | io | public | useful | high |
| `pydata` | io | semi-public | useful | medium |
| `relations.backends.capabilities` | backend | internal | reference-only | medium |
| `relations.backends.ibis` | backend | internal | reference-only | high |
| `relations.backends.narwhals` | backend | internal | reference-only | high |
| `relations.backends.polars` | backend | internal | reference-only | high |
| `relations.core.execution` | orchestration | internal | useful | high |
| `relations.core` | orchestration | internal | reference-only | medium |
| `relations.core.relation_api` | public-api | public | essential | high |
| `relations.core.relation_nodes` | model | semi-public | useful | high |
| `relations.core.relation_protocols` | protocol | semi-public | useful | high |
| `relations.core.relation_system` | orchestration | semi-public | useful | high |
| `relations.core.unified_visitor` | orchestration | semi-public | useful | high |
| `relations.dag` | orchestration | public | essential | high |
| `relations` | public-api | public | essential | high |
| `toplevel` | public-api | public | essential | high |
| `typespec` | model | public | essential | high |
| `validation` | orchestration | semi-public | essential | medium |

## Low- and medium-confidence records

No module is `low` confidence. The `medium` records and their open questions:

- `core.capabilities`: dependency lists derived from import scans; not every symbol traced.
- `expressions.backends.ibis`: Exact set of exported names in __init__ __all__ was not audited item by item
- `expressions.backends.narwhals`: Exact mapping of every Narwhals provider to a tested configuration in CI was not verified
- `expressions.core.unified_visitor`: Exact semantics of the reusable-lowering cache and TypeContext scoping were skimmed, not traced end to end.
- `pipelines`: Is the referenced docs/guides/pipelines.md guide planned or removed? / Public stability of Runner internals beyond run(): plan/execute are public but their contract is lightly documented
- `pydata.egress`: Whether the egress classes are meant as a public entry point or are reached only through Relation.to_* methods is not documented.
- `pydata`: Whether mappers, sanitizers and utils are intended as public helpers or internal support is not stated; classified semi-public from tests only.
- `relations.backends.capabilities`: Which narwhals/polars family segments are intentionally empty versus pending population?
- `relations.core`: Whether any of these helpers are intended as semi-public documentation topics beyond maintainer notes
- `validation`: Which of the exported names are intended as stable public API versus semi-public internals is not stated in the module; classified semi-public from __init__ exports and tests only.

## Audience coverage

| Facet | Concepts | Featured | Modules referenced |
|---|---|---|---|
| backend-architecture | 6 | 7 | 22 |
| broader-hype | 2 | 4 | 4 |
| contributors | 6 | 6 | 24 |
| executives-marketing | 4 | 7 | 8 |
| extension-authors | 5 | 6 | 13 |
| maintainers | 8 | 7 | 21 |
| users | 9 | 9 | 22 |

Modules not referenced by any facet: none.

## Documentation gaps found in source

- `pipelines` module docstring links `docs/guides/pipelines.md`, which does not exist.
- The `expressions/__init__.py` docstring still lists Pandas as a supported backend, and the `expression_nodes` docstring says "6 core node types". Both are stale.
- The relational-ast principle says "10 core nodes", but the code has 8 Substrait nodes plus Mountainash extension nodes.
- `pydata.egress` still uses legacy aliases (`EgressPydataFromPolars`, `BaseEgressStrategy`).
- No `examples/` directory exists. Executive and hype facets need runnable, test-backed demos.
- Dependency/dependent lists come from import scans, including lazy and `TYPE_CHECKING` imports. `core` and `typespec` show non-eager back-edges, which are recorded as cycle risks.

## Out-of-scope observations

- `.hiivmind/package-profile/` holds an older, superseded profile at `b068ebae`. It is outside this profile root and was left untouched. Retire it.
- `docs-site/profile/README.md` (legacy positioning prose from the retired central `03.profile/mountainash`) was deleted at the user's direction. It is not a profile contract output.
