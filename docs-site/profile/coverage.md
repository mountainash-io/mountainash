# Coverage Report

**Generated:** 2026-06-02
**Source hash:** 00e99834097053e30395b1943913b8b4a74a6e28
**Mode:** full-refresh (14/25 modules changed — exceeded one-third threshold)

## Module Coverage

| Status | Count | Details |
|--------|-------|---------|
| Profiled | 25 | All discovered modules have profiles |
| Missing profiles | 0 | — |
| Stale profiles | 0 | All updated to current hash |
| Orphan profiles | 0 | — |

## Facet Coverage

| Facet | Modules Featured | Coverage |
|-------|-----------------|----------|
| users | 8 | Complete |
| maintainers | 7 | Complete |
| contributors | 7 | Complete |
| backend-architecture | 5 | Complete |
| extension-authors | 6 | Complete |
| executives-marketing | 6 | Complete |
| broader-hype | 5 | Complete |

## Key Changes Since Last Profile (b068ebae → 00e99834)

### Major Architectural Changes
- **ConformRelNode rearchitecture**: Relation.conform() now defers to ConformRelNode, which calls apply_conform() at compile time with column information. Full Frictionless transform pipeline (7 stages) implemented.
- **Egress terminal expansion**: 11 new terminal methods added to Relation (to_dicts, to_tuples, to_dataclasses, to_pydantic, to_named_tuples, to_typed_named_tuples, to_pyarrow, to_narwhals, to_ibis, to_dict_of_series_*, to_index_of_*). Total: 18 terminals.
- **Egress delegation**: Terminal methods now delegate to pydata.egress module instead of inline implementation.

### New Functionality
- `today()` and `now()` free functions in expression API
- ConformResult dataclass with fieldsMatch-driven dispatch
- ConformError hierarchy (5 specific error types)
- fieldsMatch defaults to 'open' when unset (bugfix PR #179)
- Column name sanitization for namedtuple extraction
- Narwhals backend fixes for cross-backend matrix clusters 2-8

### Modules with Significant Changes
1. **conform** — Major rearchitecture: ConformRelNode, error hierarchy, 7-stage pipeline
2. **relations-api** — 11 new terminal methods, conform delegation
3. **relations-nodes** — ConformRelNode added (13th node type)
4. **relations-visitor** — _visit_conform_rel handler, apply_conform method
5. **relations-protocols** — 18 terminal method signatures
6. **pydata-egress** — Column sanitization, delegation target for terminals
7. **expressions-api** — today(), now() free functions
8. **expressions-backend-narwhals** — Cross-backend matrix cluster fixes
9. **typespec** — fieldsMatch default to 'exact' per Frictionless spec

## Public API Without User Facet Coverage
None — all public modules are represented in the users facet.

## Internal Without Maintainer Facet Coverage
None — all internal architecture modules are represented in maintainers facet.

## Low Confidence Classifications
None — all modules classified with high confidence.

## Next Recommended Documentation Work
1. **Terminal method catalogue** — Document all 18 terminal methods with examples
2. **Conform pipeline guide** — Document the 7-stage Frictionless transform pipeline and fieldsMatch modes
3. **Updated architecture diagram** — Reflect ConformRelNode in the relation AST
4. **Cross-backend matrix documentation** — Document the narwhals fixes and remaining known divergences
