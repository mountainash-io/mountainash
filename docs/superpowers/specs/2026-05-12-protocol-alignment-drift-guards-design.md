# Protocol Alignment And Drift Guards Design

## Context

The expression pipeline has three independent verification systems:

- `tests/cross_backend/argument_types/test_coverage_guard.py` checks protocol argument params against `TESTED_PARAMS`.
- `tests/unit/test_protocol_alignment.py` checks protocol methods against the function registry and composed backends.
- `tests/unit/test_protocol_alignment.py` also checks protocol signatures against backend signatures.

These systems currently join on different identifiers: string operation names, protocol method identity, and backend `hasattr` checks. The result is silent drift risk: protocols can be discovered by one guard but skipped by another, string-based `TESTED_PARAMS` entries can look covered without registry wiring, and duplicated operation names across categories can hide missing category-specific tests.

This design implements all phases from `coverage-guard-architecture-gaps.md`: close protocol blind spots, bridge coverage to registry wiring, converge on enum-backed identifiers, enforce category provenance, track aspirational debt with dates, and make option params visible.

## Goals

- Every discovered expression-system protocol is represented in the wiring audit.
- Every tested operation is registry-wired or explicitly listed as an unwired tested gap.
- Argument param coverage is matched by protocol/category provenance, not only by `(op_name, param_name)`.
- Option params are either behavior-tested or explicitly listed as untested option debt.
- String `TESTED_PARAMS` entries are reduced by resolving enum keys through the function registry.
- Aspirational wiring exceptions carry reasons and `since` dates, and are reconciled against coverage claims.

## Non-Goals

- This change does not require wiring every aspirational operation.
- This change does not require writing full behavior tests for all currently untested option params.
- This change does not replace the expression function registry or backend architecture.

## Architecture

Keep the existing ownership split, but make the joins explicit.

`tests/cross_backend/argument_types/_introspection.py` remains the protocol-param discovery source. It already discovers all expression-system protocols and returns `ProtocolParam` records with `protocol_name`, `category`, `op_name`, `param_name`, and `kind`.

`tests/unit/test_protocol_alignment.py` remains the wiring-audit owner. `WIRING_PROTOCOL_REGISTRY` expands to every protocol discovered by `_iter_protocol_classes()`. The completeness assertion becomes a set comparison against discovered protocols instead of a hardcoded count. `KNOWN_ASPIRATIONAL` changes from raw reason strings to structured records.

`tests/cross_backend/argument_types/test_coverage_guard.py` becomes the bridge owner. It canonicalizes `TESTED_PARAMS` entries using `ExpressionFunctionRegistry` where possible, enforces argument-param coverage by source protocol, enforces option-param explicitness, and checks that tested operations are either registry-wired or listed in a dated exception registry.

The intended verification chain is:

```text
Protocol method discovery
  -> Function registry protocol_method identity
  -> Canonical operation key
  -> Backend method presence
  -> Category-qualified argument/option coverage
```

## Components

### `KnownGap`

Add a small structured record for exception registries:

```python
@dataclass(frozen=True)
class KnownGap:
    reason: str
    since: str
```

Use this shape for:

- `KNOWN_ASPIRATIONAL`
- `_KNOWN_UNWIRED_TESTED_OPS`
- `_KNOWN_UNTESTED_ARGUMENT_PARAMS`
- `_KNOWN_UNTESTED_OPTION_PARAMS`

Existing exception tests must also validate stale entries: referenced protocols, methods, params, and operations must still exist.

### `TestedParamRef`

Add a record for collected `TESTED_PARAMS` entries:

```python
@dataclass(frozen=True)
class TestedParamRef:
    module_name: str
    category: str
    original_key: object
    protocol_name: str | None
    op_name: str
    param_name: str
    registry_wired: bool
```

This preserves enough provenance to distinguish datetime `add.x` from arithmetic `add.x`, while still allowing legacy string keys during migration.

### Canonical Name Resolver

Resolution order:

1. If a key is an enum member and is registered in `ExpressionFunctionRegistry`, resolve via `func_def.protocol_method`.
2. If a key is a string, resolve against introspected protocol methods in the same category module first.
3. If a string maps to multiple protocol methods within the same category, fail and require enum migration or a category-qualified exception.
4. If no registry/protocol match exists, classify it as unwired and require `_KNOWN_UNWIRED_TESTED_OPS`.

The resolver must prefer registry protocol identity over enum-name string matching. This is what allows enum keys such as `MODULO`, `EXTRACT_DAY`, or `COUNT_DISTINCT` to map to protocol methods such as `modulus`, `day`, and `n_unique`.

## Enforcement

### Wiring Audit

Add all protocols discovered by `_iter_protocol_classes()` to `WIRING_PROTOCOL_REGISTRY`, including the 12 currently missing protocols. Methods not yet wired must be added to `KNOWN_ASPIRATIONAL` with a concrete reason and `since`.

Replace `assert len(WIRING_PROTOCOL_REGISTRY) == 18` with a set comparison:

```python
discovered = {cls for _, cls in _iter_protocol_classes()}
registered = set(WIRING_PROTOCOL_REGISTRY)
assert discovered <= registered
```

The wiring audit continues to hard-fail for non-aspirational methods that lack registry/backend wiring. Aspirational methods continue to use `xfail(strict=True)`.

### Coverage Guard Bridge

Add a bridge test that verifies each collected `TESTED_PARAMS` operation resolves to registry wiring unless it is listed in `_KNOWN_UNWIRED_TESTED_OPS`.

Special node types such as `col` and `lit` may remain exception entries because they are intentionally not scalar function registry dispatches. Their exception records must name that reason.

### Argument Coverage Provenance

Change argument coverage comparison from:

```python
(op_name, param_name)
```

to:

```python
(protocol_name, op_name, param_name)
```

The category recorded from the test module must match the category discovered from `_introspection.py`, except for explicitly listed cross-category dispatch cases. This prevents one category's test from accidentally satisfying another category's protocol param.

### Option Param Accounting

Add `_KNOWN_UNTESTED_OPTION_PARAMS` and a guard test:

- Every discovered option param must be behavior-tested or listed as a known untested option param.
- Every known untested option param must still exist.
- A param cannot be both option-tested and listed as untested.

The first implementation may populate the known-option registry for current gaps. Full cross-backend option behavior tests are follow-on work and should remove entries from that registry over time.

### Aspirational Aging And Reconciliation

`KNOWN_ASPIRATIONAL` entries include `since` dates. Add a staleness test that emits warnings for entries older than the chosen threshold, initially six months. This should not fail CI on first introduction.

Add reconciliation between aspirational entries and collected tested params. If the same `(protocol_name, method_name)` is both aspirational and covered by `TESTED_PARAMS`, fail unless an explicit bridge exception explains why that combination is valid.

## Rollout

### Phase 1: Close Blind Spots

- Add missing protocols to `WIRING_PROTOCOL_REGISTRY`.
- Replace hardcoded wiring-registry counts with introspection-derived set checks.
- Add coverage-to-registry bridge test.
- Add option-param explicit tracking.

### Phase 2: Enum-Key Convergence

- Implement canonical name resolution through `ExpressionFunctionRegistry`.
- Migrate safely resolvable string `TESTED_PARAMS` entries to enum keys.
- Require remaining unresolved strings to be protocol-resolvable or listed as dated unwired exceptions.

### Phase 3: Provenance And Aspirational Debt

- Thread category/protocol provenance through tested-param collection.
- Match argument coverage by `(protocol_name, op_name, param_name)`.
- Convert aspirational entries to structured records with `since`.
- Add staleness warnings and aspirational-vs-tested reconciliation.

### Phase 4: Option Param Testing

- Keep every option param accounted for.
- Add behavior tests first for high-risk options such as string case sensitivity/null handling, datetime timezone/unit/format, and arithmetic rounding/overflow.
- Remove entries from `_KNOWN_UNTESTED_OPTION_PARAMS` as behavior coverage lands.

## Verification

Run targeted checks first:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py
hatch run test:test-target-quick tests/cross_backend/argument_types/test_introspection_smoke.py
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py
```

Then run the broader affected surface:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py tests/cross_backend/argument_types
```

If enum-key migration changes argument test metadata, run the affected cross-backend argument files as well.

## Risks

- The current exception sets may be large. That is acceptable if each entry is explicit, dated, and self-pruning.
- String resolution can be ambiguous across categories. Ambiguity must fail rather than guessing.
- Staleness warnings should not become noisy CI failures until the team chooses an aging policy.
- The option-param guard makes hidden debt visible before all option behavior tests exist. The first implementation should treat visibility as success, not require immediate zero debt.
