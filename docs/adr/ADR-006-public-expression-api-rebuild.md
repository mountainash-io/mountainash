# ADR-006: Public Expression API Rebuild

## Status

PROPOSED

## Context

The mountainash-expressions package has completed significant architectural work to align with the Substrait specification:

- **Phase 1-3**: Created Substrait-aligned expression nodes (`exn_*.py`), function key ENUMs, and protocol definitions
- **Phase 4**: Implemented complete backend expression systems for Polars, Narwhals, and Ibis

However, the public API (`BooleanExpressionAPI`) still uses deprecated components:
- Legacy namespaces from `core/namespaces/` that create deprecated expression nodes
- Deprecated expression nodes (`BooleanComparisonExpressionNode`, etc.) instead of `ScalarFunctionNode`
- Mixed compilation paths through legacy visitors

New Substrait-aligned components exist but are not wired together:
- New namespaces in `core/expression_api/api_namespaces/core/` (13 namespaces)
- New expression nodes in `core/expression_nodes/exn_*.py` (6 node types)
- `UnifiedExpressionVisitor` for compilation
- `FunctionRegistry` for function definitions
- Backend expression systems implementing all protocols

## Decision

Rebuild `BooleanExpressionAPI` from scratch to use new Substrait-aligned components:

1. **Replace namespace composition** - Use new namespaces from `api_namespaces/core/` instead of deprecated `namespaces/`

2. **Create missing namespaces** - Add TernaryNamespace, NullNamespace, NameNamespace, NativeNamespace

3. **Preserve the public API contract** - Keep all existing method names and Python operator overloads

4. **Wire compilation to UnifiedExpressionVisitor** - New nodes compile through the unified visitor path

5. **Maintain entry points** - `col()`, `lit()`, `when()`, `coalesce()`, etc. continue to work unchanged

### Namespace Layout

**Flat Namespaces** (direct access via `api.method()`):
- TernaryNamespace (t_*, is_true, is_false, etc.)
- ScalarComparisonNamespace (eq, ne, gt, lt, is_null, between, etc.)
- ScalarBooleanNamespace (and_, or_, not_, xor_)
- ScalarArithmeticNamespace (add, subtract, multiply, divide, etc.)
- ScalarRoundingNamespace (ceil, floor, round)
- ScalarLogarithmicNamespace (log, sqrt, abs, exp)
- CastNamespace (cast)
- ScalarSetNamespace (is_in, is_not_in)
- NullNamespace (fill_null)
- NativeNamespace (native passthrough)

**Explicit Namespaces** (via `.accessor`):
- `.str` → StringNamespace
- `.dt` → DateTimeNamespace
- `.name` → NameNamespace

## Consequences

### Positive

- **Full Substrait alignment** - All operations create Substrait-compatible AST nodes
- **Clean separation** - Deprecated code can be removed without affecting new API
- **Consistent compilation** - Single visitor handles all node types
- **Backend flexibility** - Same AST compiles to any registered backend
- **Future serialization** - Nodes are ready for Substrait protobuf serialization (Phase 6)

### Negative

- **Breaking change for internals** - Any code accessing internal APIs (namespaces, nodes) will break
- **Test updates may be needed** - Tests using internal APIs need adjustment
- **Temporary dual paths** - During transition, both old and new paths exist

### Neutral

- **Public API unchanged** - `ma.col("x").gt(30).and_(...)` continues to work
- **Performance neutral** - No significant performance change expected

## Implementation

See GitHub Milestone "Substrait Alignment Phase 5 - Public API" for tracking issues.

## References

- ADR-005: Backend Expression System Rebuild (Phase 4)
- ADR-004: Function Mapping Registry Alignment
- ADR-002: Substrait Builder Protocols
- Substrait Specification: https://substrait.io/
