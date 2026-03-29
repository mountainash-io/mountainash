# ADR-004: Function Mapping Registry Alignment

**Status**: ACCEPTED
**Date**: 2025-12-21
**Deciders**: @nathanielramm

## Context

The mountainash-expressions package has three related systems that must stay aligned:

1. **Function Mapping Definitions** (`expression_system/function_mapping/definitions.py`)
   - Registry of function metadata (ExpressionFunctionDef instances)
   - Maps function_key → substrait_uri → substrait_name → protocol_method
   - Currently: 47 functions registered, ~50+ commented out

2. **ExpressionProtocol Classes** (`expression_protocols/substrait/prtcl_*.py`)
   - Backend method signatures for 13 protocols
   - Total: 139+ methods defining backend primitives

3. **Function Key Enums** (`expression_system/function_keys/`)
   - Unique identifiers for compile-time safety
   - 113 Substrait + 27 Mountainash = 140 total values

### Current Alignment Gaps

| Category | Protocol Methods | Registered | Gap |
|----------|-----------------|------------|-----|
| Comparison | 23 | 18 | 5 |
| Boolean | 5 | 4 | 1 |
| Arithmetic | 7 | 6 | 1 |
| String | 35+ | 17 | 18+ |
| DateTime | 2 | 2 | 0 |
| Rounding | 3 | 0 | 3 |
| Logarithmic | 4 | 0 | 4 |
| Set | 1 | 1 (wrong URI) | 0 |
| Aggregate | 3 | 0 | 3 |
| Cast | 1 | 0 | 1 |
| Conditional | 1 | 0 | 1 |

### Critical Bugs Identified

1. **SET function uses wrong URI (line 426-432)**: Uses SCALAR_DATETIME instead of SCALAR_SET
2. **Registration list missing SET functions (line 883-894)**: SCALAR_SET_FUNCTIONS never added to all_functions
3. **Variable name mismatch (line 884)**: Uses COMPARISON_FUNCTIONS but variable is SCALAR_COMPARISON_FUNCTIONS

## Decision

Perform full alignment between all three systems in 5 phases:

### Phase 1: Fix Critical Bugs
- Fix SET function URI from SCALAR_DATETIME to SCALAR_SET
- Fix registration list variable name
- Add SCALAR_SET_FUNCTIONS to all_functions

### Phase 2: Add Missing Categories
- Rounding: ceil, floor, round (3 functions)
- Logarithmic: ln, log10, log2, logb (4 functions)
- Aggregate: count, count_all, any_value (3 functions)
- Cast: cast (1 function)
- Conditional: if_then_else (1 function)

### Phase 3: Complete Existing Categories
- Comparison: nullif, least_skip_null, greatest_skip_null
- Boolean: and_not
- Arithmetic: negate, abs, sign, sqrt, exp
- String: 18+ methods (swapcase, capitalize, title, lpad, rpad, etc.)

### Phase 4: Update Registration
- Update all_functions concatenation to include all category lists

### Phase 5: Verify Enum Alignment
- Ensure function_keys/enums.py has all needed enum values

## Consequences

### Positive

- Complete alignment enables reliable function dispatch
- All protocol methods have corresponding registry entries
- Fixes data corruption bugs (wrong URIs)
- Enables future Substrait serialization
- Compile-time safety via enum-based function keys

### Negative

- ~100 new function definitions to maintain
- ~500 lines of changes to definitions.py
- Increased code size in registry

### Neutral

- Does not change public API
- Existing functionality unchanged
- Registry pattern remains same

## Alternatives Considered

1. **Minimal fix (bugs only)**: Only fix critical bugs
   - Rejected: Leaves large alignment gap, defers technical debt

2. **Partial alignment (active categories only)**: Only align actively used categories
   - Rejected: Inconsistent state, harder to maintain

3. **Full alignment (selected)**: Complete registry for all protocols
   - Selected: Clean slate, enables all operations, single maintenance effort

## References

- [Substrait Extensions](https://substrait.io/extensions/)
- [ADR-002: Substrait BuilderProtocol Migration](./ADR-002-substrait-builder-protocols.md)
- [ADR-003: Namespace BuilderProtocol Implementation](./ADR-003-namespace-builderprotocol-implementation.md)

## Tasks

GitHub Issues created in [mountainash-io/mountainash-expressions](https://github.com/mountainash-io/mountainash-expressions):
- [x] [Issue #26](https://github.com/mountainash-io/mountainash-expressions/issues/26): Fix critical bugs in function definitions
- [x] [Issue #27](https://github.com/mountainash-io/mountainash-expressions/issues/27): Add missing function categories
- [x] [Issue #28](https://github.com/mountainash-io/mountainash-expressions/issues/28): Complete existing function categories
- [x] [Issue #29](https://github.com/mountainash-io/mountainash-expressions/issues/29): Create ADR-004

**Milestone**: [Substrait Alignment Phase 3 - Function Registry](https://github.com/mountainash-io/mountainash-expressions/milestone/4)

## Completion Criteria

- [x] All critical bugs fixed
- [x] All missing categories added
- [x] All existing categories completed
- [x] Registration list updated
- [x] Enum alignment verified
- [x] Syntax check passes
- [x] ADR status updated to ACCEPTED
