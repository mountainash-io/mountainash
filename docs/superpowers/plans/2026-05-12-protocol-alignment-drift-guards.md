# Protocol Alignment Drift Guards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement closed-by-default protocol alignment and drift detection across expression protocols, function registry wiring, argument coverage, option coverage, and aspirational gaps.

**Architecture:** Add a focused coverage-resolution helper beside the argument-type tests, then update the coverage guard to compare category-qualified protocol params instead of lossy operation strings. Update the protocol-alignment test to discover all protocols, structure aspirational exceptions, and remove hardcoded protocol counts.

**Tech Stack:** Python 3, pytest, dataclasses, `inspect`, `warnings`, existing `ExpressionFunctionRegistry`, existing `cross_backend.argument_types._introspection`.

---

## File Structure

- Create: `tests/cross_backend/argument_types/_coverage_guard_helpers.py`
  - Owns `KnownGap`, `TestedParamRef`, tested-param collection, function-registry resolution, and protocol-param lookup helpers.
- Modify: `tests/cross_backend/argument_types/test_coverage_guard.py`
  - Uses helper records, adds bridge tests, option-param accounting, provenance checks, stale exception checks.
- Modify: `tests/unit/test_protocol_alignment.py`
  - Imports all expression-system protocols, expands `WIRING_PROTOCOL_REGISTRY`, converts `KNOWN_ASPIRATIONAL` to structured records, adds introspection completeness, staleness warning, and reconciliation tests.
- Modify: selected `tests/cross_backend/argument_types/test_arg_types_*.py`
  - Migrates safely resolvable string `TESTED_PARAMS` entries to enum keys where registry identity resolves the protocol method.
- Test: `tests/cross_backend/argument_types/test_introspection_smoke.py`
  - Add one focused smoke test for the resolver.

## Task 1: Coverage Helper Module

**Files:**
- Create: `tests/cross_backend/argument_types/_coverage_guard_helpers.py`
- Test: `tests/cross_backend/argument_types/test_introspection_smoke.py`

- [ ] **Step 1: Add failing resolver smoke tests**

Append these tests to `tests/cross_backend/argument_types/test_introspection_smoke.py`:

```python
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)
from cross_backend.argument_types._coverage_guard_helpers import (
    collect_tested_params,
    registry_protocol_ref,
)


def test_registry_protocol_ref_resolves_enum_to_protocol_method_name():
    ref = registry_protocol_ref(FK_ARITH.MODULO)
    assert ref is not None
    assert ref.protocol_name == "SubstraitScalarArithmeticExpressionSystemProtocol"
    assert ref.op_name == "modulus"


def test_collect_tested_params_preserves_category_provenance():
    refs = collect_tested_params(["test_arg_types_arithmetic"])
    add_refs = [
        ref for ref in refs
        if ref.protocol_name == "SubstraitScalarArithmeticExpressionSystemProtocol"
        and ref.op_name == "add"
        and ref.param_name == "x"
    ]
    assert len(add_refs) == 1
    assert add_refs[0].category == "arithmetic"
    assert add_refs[0].registry_wired is True
```

- [ ] **Step 2: Run smoke tests and verify import failure**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_introspection_smoke.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'cross_backend.argument_types._coverage_guard_helpers'`.

- [ ] **Step 3: Create helper module**

Create `tests/cross_backend/argument_types/_coverage_guard_helpers.py`:

```python
"""Shared helpers for expression argument/option coverage guards."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import importlib
from typing import Any, Iterable

from cross_backend.argument_types._introspection import ProtocolParam, introspect_protocols
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)


@dataclass(frozen=True)
class KnownGap:
    reason: str
    since: str


@dataclass(frozen=True)
class ProtocolMethodRef:
    protocol_name: str
    op_name: str


@dataclass(frozen=True)
class TestedParamRef:
    module_name: str
    category: str
    original_key: Any
    protocol_name: str | None
    op_name: str
    param_name: str
    registry_wired: bool

    @property
    def protocol_param_key(self) -> tuple[str, str, str] | None:
        if self.protocol_name is None:
            return None
        return (self.protocol_name, self.op_name, self.param_name)

    @property
    def operation_key(self) -> tuple[str, str] | None:
        if self.protocol_name is None:
            return None
        return (self.protocol_name, self.op_name)


def category_from_module_name(module_name: str) -> str:
    if module_name.startswith("test_arg_types_"):
        return module_name.removeprefix("test_arg_types_")
    return module_name


def registry_protocol_ref(function_key: object) -> ProtocolMethodRef | None:
    if not isinstance(function_key, Enum):
        return None
    try:
        func_def = ExpressionFunctionRegistry.get(function_key)
    except KeyError:
        return None
    protocol_method = func_def.protocol_method
    if protocol_method is None:
        return None
    qualname = getattr(protocol_method, "__qualname__", "")
    if "." not in qualname:
        return None
    protocol_name, op_name = qualname.rsplit(".", 1)
    return ProtocolMethodRef(protocol_name=protocol_name, op_name=op_name)


def protocol_params_by_category() -> dict[str, list[ProtocolParam]]:
    by_category: dict[str, list[ProtocolParam]] = {}
    for param in introspect_protocols():
        by_category.setdefault(param.category, []).append(param)
    return by_category


def resolve_string_protocol_ref(
    op_name: str,
    category: str,
    params_by_category: dict[str, list[ProtocolParam]] | None = None,
) -> ProtocolMethodRef | None:
    params_by_category = params_by_category or protocol_params_by_category()
    matches = {
        (param.protocol_name, param.op_name)
        for param in params_by_category.get(category, [])
        if param.op_name == op_name
    }
    if len(matches) != 1:
        return None
    protocol_name, resolved_op_name = next(iter(matches))
    return ProtocolMethodRef(protocol_name=protocol_name, op_name=resolved_op_name)


def canonicalize_tested_param(
    module_name: str,
    original_key: object,
    param_name: str,
    params_by_category: dict[str, list[ProtocolParam]] | None = None,
) -> TestedParamRef:
    category = category_from_module_name(module_name)
    registry_ref = registry_protocol_ref(original_key)
    if registry_ref is not None:
        return TestedParamRef(
            module_name=module_name,
            category=category,
            original_key=original_key,
            protocol_name=registry_ref.protocol_name,
            op_name=registry_ref.op_name,
            param_name=param_name,
            registry_wired=True,
        )

    op_name = str(original_key)
    protocol_ref = resolve_string_protocol_ref(op_name, category, params_by_category)
    return TestedParamRef(
        module_name=module_name,
        category=category,
        original_key=original_key,
        protocol_name=protocol_ref.protocol_name if protocol_ref else None,
        op_name=protocol_ref.op_name if protocol_ref else op_name,
        param_name=param_name,
        registry_wired=False,
    )


def collect_tested_params(module_names: Iterable[str]) -> set[TestedParamRef]:
    tested: set[TestedParamRef] = set()
    params_by_category = protocol_params_by_category()
    for module_name in module_names:
        try:
            mod = importlib.import_module(f"cross_backend.argument_types.{module_name}")
        except ImportError:
            continue
        for original_key, param_name in getattr(mod, "TESTED_PARAMS", []):
            tested.add(
                canonicalize_tested_param(
                    module_name=module_name,
                    original_key=original_key,
                    param_name=param_name,
                    params_by_category=params_by_category,
                )
            )
    return tested
```

- [ ] **Step 4: Run smoke tests and verify pass**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_introspection_smoke.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/cross_backend/argument_types/_coverage_guard_helpers.py tests/cross_backend/argument_types/test_introspection_smoke.py
git commit -m "test: add coverage guard resolution helpers"
```

## Task 2: Registry Bridge Guard

**Files:**
- Modify: `tests/cross_backend/argument_types/test_coverage_guard.py`
- Test: `tests/cross_backend/argument_types/test_coverage_guard.py`

- [ ] **Step 1: Replace local collector imports**

In `tests/cross_backend/argument_types/test_coverage_guard.py`, replace the `importlib` import and local `_collect_tested_params()` function with:

```python
from cross_backend.argument_types._coverage_guard_helpers import (
    KnownGap,
    TestedParamRef,
    collect_tested_params,
)
```

Then add this compatibility helper near `_CATEGORY_MODULES`:

```python
def _collect_tested_param_refs() -> set[TestedParamRef]:
    return collect_tested_params(_CATEGORY_MODULES)


def _collect_tested_params() -> set[tuple[str, str]]:
    return {(ref.op_name, ref.param_name) for ref in _collect_tested_param_refs()}
```

- [ ] **Step 2: Add known unwired operation registry**

Add below `_KNOWN_UNTESTED_ARGUMENT_PARAMS`:

```python
_KNOWN_UNWIRED_TESTED_OPS: dict[tuple[str, str], KnownGap] = {
    ("SubstraitFieldReferenceExpressionSystemProtocol", "col"): KnownGap(
        reason="Special node type (FieldReferenceNode), not dispatched through scalar function registry",
        since="2026-05-12",
    ),
    ("SubstraitLiteralExpressionSystemProtocol", "lit"): KnownGap(
        reason="Special node type (LiteralNode), not dispatched through scalar function registry",
        since="2026-05-12",
    ),
}
```

- [ ] **Step 3: Add failing bridge test**

Add after `test_every_argument_param_is_tested`:

```python
def test_tested_params_have_registry_wiring_or_named_gap():
    tested = _collect_tested_param_refs()
    unwired = {
        ref.operation_key
        for ref in tested
        if ref.operation_key is not None
        and not ref.registry_wired
        and ref.operation_key not in _KNOWN_UNWIRED_TESTED_OPS
    }
    unresolved = {
        (ref.op_name, ref.param_name)
        for ref in tested
        if ref.operation_key is None
    }
    stale_known = {
        key for key in _KNOWN_UNWIRED_TESTED_OPS
        if key not in {ref.operation_key for ref in tested}
    }
    assert not unresolved, f"TESTED_PARAMS entries with no protocol match: {sorted(unresolved)}"
    assert not unwired, (
        "TESTED_PARAMS operations with no function registry wiring "
        f"(add enum/registry wiring or _KNOWN_UNWIRED_TESTED_OPS entry): {sorted(unwired)}"
    )
    assert not stale_known, (
        "Entries in _KNOWN_UNWIRED_TESTED_OPS no longer referenced by TESTED_PARAMS "
        f"(remove them): {sorted(stale_known)}"
    )
```

- [ ] **Step 4: Run bridge test and collect failures**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py::test_tested_params_have_registry_wiring_or_named_gap
```

Expected: FAIL listing current unwired or unresolved tested entries.

- [ ] **Step 5: Add dated known gaps for current legitimate unwired entries**

For entries that are not registry-wired by design or are not yet implemented, add records to `_KNOWN_UNWIRED_TESTED_OPS` with this form:

```python
("ProtocolClassName", "method_name"): KnownGap(
    reason="No function mapping registered yet; argument channel coverage exists before registry wiring",
    since="2026-05-12",
),
```

Use the protocol and method names exactly as printed by the failing assertion. Do not add entries for enum keys that should already resolve through `ExpressionFunctionRegistry`; those must be fixed by enum migration in Task 6.

- [ ] **Step 6: Run bridge test and verify pass**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py::test_tested_params_have_registry_wiring_or_named_gap
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tests/cross_backend/argument_types/test_coverage_guard.py
git commit -m "test: bridge tested params to function registry"
```

## Task 3: Structured Argument And Option Exception Accounting

**Files:**
- Modify: `tests/cross_backend/argument_types/test_coverage_guard.py`
- Test: `tests/cross_backend/argument_types/test_coverage_guard.py`

- [ ] **Step 1: Convert argument known gaps to structured records**

Replace `_KNOWN_UNTESTED_ARGUMENT_PARAMS: set[tuple[str, str]]` with:

```python
_KNOWN_UNTESTED_ARGUMENT_PARAMS: dict[tuple[str, str, str], KnownGap] = {
    ("MountainAshScalarListExpressionSystemProtocol", "list_all", "x"): KnownGap(
        reason="List argument expression support is backend-specific",
        since="2026-05-12",
    ),
}
```

Then convert each existing two-part entry to its protocol-qualified three-part key by matching `introspect_protocols()` output. Use the same `reason` text for list entries and duration extraction entries:

```python
KnownGap(reason="Ibis has no total_* duration extraction methods", since="2026-05-12")
```

- [ ] **Step 2: Add option gap registry**

Add below `_KNOWN_UNTESTED_ARGUMENT_PARAMS`:

```python
_KNOWN_UNTESTED_OPTION_PARAMS: dict[tuple[str, str, str], KnownGap] = {}
```

- [ ] **Step 3: Update argument coverage test to use protocol keys**

Replace `test_every_argument_param_is_tested` with:

```python
def test_every_argument_param_is_tested():
    introspected = {
        (p.protocol_name, p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "argument"
    }
    tested = {
        ref.protocol_param_key
        for ref in _collect_tested_param_refs()
        if ref.protocol_param_key is not None
    }
    known = set(_KNOWN_UNTESTED_ARGUMENT_PARAMS)
    newly_missing = introspected - tested - known
    extra = tested - introspected
    stale_known = known - introspected
    overlap = known & tested
    assert not newly_missing, (
        "New argument params with no test "
        f"(add test or register in _KNOWN_UNTESTED_ARGUMENT_PARAMS): {sorted(newly_missing)}"
    )
    assert not extra, f"Tested params with no protocol: {sorted(extra)}"
    assert not stale_known, (
        "Entries in _KNOWN_UNTESTED_ARGUMENT_PARAMS that no longer exist in protocols "
        f"(remove them): {sorted(stale_known)}"
    )
    assert not overlap, (
        "Entries in _KNOWN_UNTESTED_ARGUMENT_PARAMS that are already tested "
        f"(remove from _KNOWN_UNTESTED_ARGUMENT_PARAMS): {sorted(overlap)}"
    )
```

- [ ] **Step 4: Add failing option accounting test**

Add after the argument coverage test:

```python
def test_every_option_param_is_tested_or_registered():
    introspected = {
        (p.protocol_name, p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "option"
    }
    tested_options: set[tuple[str, str, str]] = set()
    known = set(_KNOWN_UNTESTED_OPTION_PARAMS)
    newly_missing = introspected - tested_options - known
    stale_known = known - introspected
    overlap = known & tested_options
    assert not newly_missing, (
        "Option params with no behavior test or known-gap entry "
        f"(add tests or _KNOWN_UNTESTED_OPTION_PARAMS entries): {sorted(newly_missing)}"
    )
    assert not stale_known, (
        "Entries in _KNOWN_UNTESTED_OPTION_PARAMS that no longer exist in protocols "
        f"(remove them): {sorted(stale_known)}"
    )
    assert not overlap, (
        "Entries in _KNOWN_UNTESTED_OPTION_PARAMS that are already tested "
        f"(remove from _KNOWN_UNTESTED_OPTION_PARAMS): {sorted(overlap)}"
    )
```

- [ ] **Step 5: Run coverage guard and capture missing option keys**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py::test_every_option_param_is_tested_or_registered
```

Expected: FAIL listing current option params.

- [ ] **Step 6: Populate current option debt**

Populate `_KNOWN_UNTESTED_OPTION_PARAMS` with every key from the failing output. Use this value for entries unless a more precise local reason is obvious from the protocol signature:

```python
KnownGap(
    reason="Option behavior coverage is not implemented yet; tracked explicitly by option-param guard",
    since="2026-05-12",
)
```

- [ ] **Step 7: Run targeted coverage guard and verify pass**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py::test_every_argument_param_is_tested tests/cross_backend/argument_types/test_coverage_guard.py::test_every_option_param_is_tested_or_registered
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tests/cross_backend/argument_types/test_coverage_guard.py
git commit -m "test: account for argument and option parameter gaps"
```

## Task 4: Protocol Registry Completeness

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`
- Test: `tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers`

- [ ] **Step 1: Import missing protocol classes**

In `tests/unit/test_protocol_alignment.py`, extend the protocol imports to include all expression-system protocols that are already exposed by package `__init__` modules:

```python
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateArithmeticExpressionSystemProtocol,
    SubstraitAggregateBooleanExpressionSystemProtocol,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateStringExpressionSystemProtocol,
    SubstraitScalarGeometryExpressionSystemProtocol,
    SubstraitWindowArithmeticExpressionSystemProtocol,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarListExpressionSystemProtocol,
    MountainAshScalarSetExpressionSystemProtocol,
    MountainAshScalarStringExpressionSystemProtocol,
    MountainAshScalarStructExpressionSystemProtocol,
    MountainashExtensionAggregateExpressionSystemProtocol,
    MountainashWindowExpressionSystemProtocol,
)
```

- [ ] **Step 2: Add failing completeness assertion**

Replace `test_wiring_protocol_registry_complete` with:

```python
def test_wiring_protocol_registry_complete(self):
    """Wiring audit registry should include every discovered expression-system protocol."""
    from cross_backend.argument_types._introspection import _iter_protocol_classes

    discovered = {protocol_cls for _, protocol_cls in _iter_protocol_classes()}
    registered = set(WIRING_PROTOCOL_REGISTRY)
    missing = discovered - registered
    extra = registered - discovered
    assert not missing, (
        "Protocols missing from WIRING_PROTOCOL_REGISTRY "
        f"(add them with aspirational entries for unwired methods): "
        f"{sorted(cls.__name__ for cls in missing)}"
    )
    assert not extra, (
        "WIRING_PROTOCOL_REGISTRY contains protocols not discovered by introspection: "
        f"{sorted(cls.__name__ for cls in extra)}"
    )
```

- [ ] **Step 3: Run completeness test and verify failure**

Run:

```bash
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers::test_wiring_protocol_registry_complete
```

Expected: FAIL listing the missing protocols.

- [ ] **Step 4: Expand wiring registry**

Add the missing protocols to `WIRING_PROTOCOL_REGISTRY` with stable ids:

```python
SubstraitAggregateArithmeticExpressionSystemProtocol: "substrait_aggregate_arithmetic",
SubstraitAggregateBooleanExpressionSystemProtocol: "substrait_aggregate_boolean",
SubstraitAggregateGenericExpressionSystemProtocol: "substrait_aggregate_generic",
SubstraitAggregateStringExpressionSystemProtocol: "substrait_aggregate_string",
SubstraitScalarGeometryExpressionSystemProtocol: "substrait_scalar_geometry",
SubstraitWindowArithmeticExpressionSystemProtocol: "substrait_window_arithmetic",
MountainAshScalarListExpressionSystemProtocol: "mountainash_scalar_list",
MountainAshScalarSetExpressionSystemProtocol: "mountainash_scalar_set",
MountainAshScalarStringExpressionSystemProtocol: "mountainash_scalar_string",
MountainAshScalarStructExpressionSystemProtocol: "mountainash_scalar_struct",
MountainashExtensionAggregateExpressionSystemProtocol: "mountainash_aggregate",
MountainashWindowExpressionSystemProtocol: "mountainash_window",
```

- [ ] **Step 5: Run wiring audit and collect new gaps**

Run:

```bash
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAudit::test_all_protocol_methods_wired
```

Expected: FAIL listing wiring gaps for newly included protocols.

- [ ] **Step 6: Add aspirational entries for current gaps**

For each gap from Step 5 that is not fully wired today, add a `KNOWN_ASPIRATIONAL` record in Task 5's structured format. Use `since="2026-05-12"` and specific reasons such as:

```python
KnownGap(reason="No function mapping registered yet", since="2026-05-12")
KnownGap(reason="No backend support yet", since="2026-05-12")
KnownGap(reason="Special node type, not dispatched through scalar function registry", since="2026-05-12")
```

- [ ] **Step 7: Run completeness test and verify pass**

Run:

```bash
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers::test_wiring_protocol_registry_complete
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: cover all protocols in wiring audit"
```

## Task 5: Structured Aspirational Records And Aging

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`
- Test: `tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers`

- [ ] **Step 1: Add KnownGap dataclass import**

Near the top of `tests/unit/test_protocol_alignment.py`, add:

```python
from datetime import date
import warnings

from cross_backend.argument_types._coverage_guard_helpers import KnownGap
```

- [ ] **Step 2: Convert `KNOWN_ASPIRATIONAL` values**

Change each value from a string to `KnownGap`. Example:

```python
KNOWN_ASPIRATIONAL: dict[tuple[type, str], KnownGap] = {
    (SubstraitScalarArithmeticExpressionSystemProtocol, "factorial"): KnownGap(
        reason="No backend support yet",
        since="2026-05-12",
    ),
}
```

- [ ] **Step 3: Update aspirational parametrization**

Replace the `pytest.param` builder in `test_aspirational_method` parametrization with:

```python
pytest.param(cls, method, gap, id=f"{cls.__name__}.{method}")
for (cls, method), gap in KNOWN_ASPIRATIONAL.items()
```

Update the test body signature and assertion message:

```python
def test_aspirational_method(self, protocol_cls, method_name, gap):
    ...
    assert not missing, (
        f"{protocol_cls.__name__}.{method_name} ({gap.reason}; since {gap.since}):\n"
        f"  missing [{', '.join(missing)}]"
    )
```

- [ ] **Step 4: Update known-aspirational helper tests**

In `test_known_aspirational_references_valid_protocols` and `test_known_aspirational_references_real_methods`, rename unused `reason` loop values to `gap`:

```python
for (protocol_cls, method_name), gap in KNOWN_ASPIRATIONAL.items():
```

Then add:

```python
def test_known_aspirational_entries_have_reason_and_since(self):
    for (protocol_cls, method_name), gap in KNOWN_ASPIRATIONAL.items():
        assert gap.reason.strip(), f"{protocol_cls.__name__}.{method_name} has no reason"
        date.fromisoformat(gap.since)
```

- [ ] **Step 5: Add staleness warning test**

Add:

```python
def test_known_aspirational_staleness_warns(self):
    today = date(2026, 5, 12)
    threshold_days = 183
    for (protocol_cls, method_name), gap in KNOWN_ASPIRATIONAL.items():
        age_days = (today - date.fromisoformat(gap.since)).days
        if age_days > threshold_days:
            warnings.warn(
                (
                    f"{protocol_cls.__name__}.{method_name} has been aspirational "
                    f"for {age_days} days: {gap.reason}"
                ),
                UserWarning,
                stacklevel=2,
            )
```

- [ ] **Step 6: Run helper tests**

Run:

```bash
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: structure aspirational wiring gaps"
```

## Task 6: Enum-Key Migration For Safe String Entries

**Files:**
- Modify: `tests/cross_backend/argument_types/test_arg_types_arithmetic.py`
- Modify: `tests/cross_backend/argument_types/test_arg_types_string.py`
- Modify: `tests/cross_backend/argument_types/test_arg_types_misc.py`
- Modify: `tests/cross_backend/argument_types/test_arg_types_datetime.py`
- Test: `tests/cross_backend/argument_types/test_coverage_guard.py`

- [ ] **Step 1: Migrate arithmetic modulus**

In `tests/cross_backend/argument_types/test_arg_types_arithmetic.py`, replace:

```python
("modulus", "x"),
("modulus", "y"),
```

with:

```python
(FK_ARITH.MODULO, "x"),
(FK_ARITH.MODULO, "y"),
```

Also change the modulus `OpSpec` field:

```python
function_key=FK_ARITH.MODULO,
```

- [ ] **Step 2: Migrate misc cast and if_then_else**

In `tests/cross_backend/argument_types/test_arg_types_misc.py`, import:

```python
FKEY_SUBSTRAIT_CAST as FK_CAST,
FKEY_SUBSTRAIT_CONDITIONAL as FK_COND,
FKEY_SUBSTRAIT_FIELD_REFERENCE as FK_FIELD,
```

Then replace:

```python
("cast", "x"),
("col", "x"),
("if_then_else", "condition"),
("if_then_else", "if_false"),
("if_then_else", "if_true"),
```

with:

```python
(FK_CAST.CAST, "x"),
(FK_FIELD.COL, "x"),
(FK_COND.IF_THEN_ELSE, "condition"),
(FK_COND.IF_THEN_ELSE, "if_false"),
(FK_COND.IF_THEN_ELSE, "if_true"),
```

- [ ] **Step 3: Migrate string strip suffix**

In `tests/cross_backend/argument_types/test_arg_types_string.py`, import the Mountainash string enum:

```python
FKEY_MOUNTAINASH_SCALAR_STRING as FK_MA_STR,
```

Replace:

```python
("strip_suffix", "x"),
```

with:

```python
(FK_MA_STR.STRIP_SUFFIX, "x"),
```

Change the `strip_suffix` `OpSpec` field:

```python
function_key=FK_MA_STR.STRIP_SUFFIX,
```

- [ ] **Step 4: Migrate datetime extraction and comparisons where enum names diverge**

In `tests/cross_backend/argument_types/test_arg_types_datetime.py`, replace string entries that already have registered enum keys:

```python
("day", "x")
("hour", "x")
("month", "x")
("minute", "x")
("second", "x")
("gt", "x")
("gt", "y")
("gte", "x")
("gte", "y")
("lt", "x")
("lt", "y")
("lte", "x")
("lte", "y")
```

with the matching enum entries from `FK_DT` or comparison enum imports. If comparison enum keys are not already imported, add:

```python
FKEY_SUBSTRAIT_SCALAR_COMPARISON as FK_CMP,
```

Use:

```python
(FK_CMP.GT, "x")
(FK_CMP.GT, "y")
(FK_CMP.GTE, "x")
(FK_CMP.GTE, "y")
(FK_CMP.LT, "x")
(FK_CMP.LT, "y")
(FK_CMP.LTE, "x")
(FK_CMP.LTE, "y")
```

Only migrate datetime extraction entries whose enum exists in `FKEY_SUBSTRAIT_SCALAR_DATETIME` and whose registry `protocol_method` points to the same protocol method. Leave unresolved strings for Task 2's dated unwired registry.

- [ ] **Step 5: Run bridge and argument coverage tests**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py::test_tested_params_have_registry_wiring_or_named_gap tests/cross_backend/argument_types/test_coverage_guard.py::test_every_argument_param_is_tested
```

Expected: PASS. If a migrated enum maps to a different protocol than the old string entry, revert that specific migration and keep the dated string exception.

- [ ] **Step 6: Commit**

```bash
git add tests/cross_backend/argument_types/test_arg_types_arithmetic.py tests/cross_backend/argument_types/test_arg_types_string.py tests/cross_backend/argument_types/test_arg_types_misc.py tests/cross_backend/argument_types/test_arg_types_datetime.py
git commit -m "test: migrate resolvable tested params to enum keys"
```

## Task 7: Category Provenance Guard

**Files:**
- Modify: `tests/cross_backend/argument_types/test_coverage_guard.py`
- Test: `tests/cross_backend/argument_types/test_coverage_guard.py`

- [ ] **Step 1: Add allowed cross-category registry**

Add near the known gap registries:

```python
_ALLOWED_CROSS_CATEGORY_TESTED_PARAMS: dict[tuple[str, str, str], KnownGap] = {
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "gt", "x"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "gt", "y"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "gte", "x"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "gte", "y"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "lt", "x"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "lt", "y"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "lte", "x"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
    ("SubstraitScalarDatetimeExpressionSystemProtocol", "lte", "y"): KnownGap(
        reason="Datetime comparison dispatch is implemented by scalar comparison registry/backend methods",
        since="2026-05-12",
    ),
}
```

- [ ] **Step 2: Add category provenance test**

Add:

```python
def test_tested_params_match_protocol_category_or_named_dispatch_gap():
    params_by_key = {
        (p.protocol_name, p.op_name, p.param_name): p
        for p in introspect_protocols()
    }
    mismatches = []
    for ref in _collect_tested_param_refs():
        key = ref.protocol_param_key
        if key is None or key in _ALLOWED_CROSS_CATEGORY_TESTED_PARAMS:
            continue
        protocol_param = params_by_key.get(key)
        if protocol_param is None:
            continue
        if protocol_param.category != ref.category:
            mismatches.append(
                f"{key}: tested in {ref.category}, protocol category is {protocol_param.category}"
            )
    stale_known = set(_ALLOWED_CROSS_CATEGORY_TESTED_PARAMS) - set(params_by_key)
    assert not mismatches, "Category provenance mismatches:\n  " + "\n  ".join(mismatches)
    assert not stale_known, (
        "Stale _ALLOWED_CROSS_CATEGORY_TESTED_PARAMS entries: "
        f"{sorted(stale_known)}"
    )
```

- [ ] **Step 3: Run provenance test**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py::test_tested_params_match_protocol_category_or_named_dispatch_gap
```

Expected: PASS after the known datetime dispatch entries are complete. If the assertion lists additional legitimate dispatch overlaps, add dated records with specific reasons.

- [ ] **Step 4: Commit**

```bash
git add tests/cross_backend/argument_types/test_coverage_guard.py
git commit -m "test: enforce category provenance for tested params"
```

## Task 8: Aspirational Versus Tested Reconciliation

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`
- Test: `tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers`

- [ ] **Step 1: Import tested-param collector**

Extend the helper import in `tests/unit/test_protocol_alignment.py`:

```python
from cross_backend.argument_types._coverage_guard_helpers import (
    KnownGap,
    collect_tested_params,
)
```

- [ ] **Step 2: Add explicit reconciliation exceptions**

Near `KNOWN_ASPIRATIONAL`, add:

```python
KNOWN_ASPIRATIONAL_AND_TESTED: dict[tuple[type, str], KnownGap] = {
    (SubstraitFieldReferenceExpressionSystemProtocol, "col"): KnownGap(
        reason="Argument channel is tested, but expression node is intentionally not registry-dispatched",
        since="2026-05-12",
    ),
    (SubstraitLiteralExpressionSystemProtocol, "lit"): KnownGap(
        reason="Argument channel is tested, but literal node is intentionally not registry-dispatched",
        since="2026-05-12",
    ),
}
```

- [ ] **Step 3: Add reconciliation test**

Add to `TestWiringAuditHelpers`:

```python
def test_aspirational_methods_are_not_claimed_tested_without_exception(self):
    from cross_backend.argument_types.test_coverage_guard import _CATEGORY_MODULES

    tested_ops = {
        (ref.protocol_name, ref.op_name)
        for ref in collect_tested_params(_CATEGORY_MODULES)
        if ref.protocol_name is not None
    }
    aspirational_ops = {
        (protocol_cls.__name__, method_name)
        for (protocol_cls, method_name) in KNOWN_ASPIRATIONAL
    }
    allowed = {
        (protocol_cls.__name__, method_name)
        for (protocol_cls, method_name) in KNOWN_ASPIRATIONAL_AND_TESTED
    }
    contradictions = (tested_ops & aspirational_ops) - allowed
    stale_allowed = allowed - (tested_ops & aspirational_ops)
    assert not contradictions, (
        "Methods are both aspirational and TESTED_PARAMS-covered without an explicit exception: "
        f"{sorted(contradictions)}"
    )
    assert not stale_allowed, (
        "KNOWN_ASPIRATIONAL_AND_TESTED entries no longer need exceptions: "
        f"{sorted(stale_allowed)}"
    )
```

- [ ] **Step 4: Run reconciliation test**

Run:

```bash
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers::test_aspirational_methods_are_not_claimed_tested_without_exception
```

Expected: PASS after legitimate exceptions are listed. If the assertion reveals current contradictions, either remove the stale aspirational entry because the method is now wired, or add a specific dated exception explaining why argument coverage and aspirational wiring status can coexist.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: reconcile aspirational methods with coverage"
```

## Task 9: Full Verification

**Files:**
- No code changes expected.

- [ ] **Step 1: Run targeted coverage guard**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py
```

Expected: PASS.

- [ ] **Step 2: Run introspection smoke tests**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_introspection_smoke.py
```

Expected: PASS.

- [ ] **Step 3: Run protocol alignment tests**

Run:

```bash
hatch run test:test-target-quick tests/unit/test_protocol_alignment.py
```

Expected: PASS, with expected xfails for aspirational methods.

- [ ] **Step 4: Run full argument-types target**

Run:

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types
```

Expected: PASS, with existing expected xfails unchanged.

- [ ] **Step 5: Review git diff**

Run:

```bash
git diff --stat
git diff -- tests/cross_backend/argument_types/_coverage_guard_helpers.py tests/cross_backend/argument_types/test_coverage_guard.py tests/unit/test_protocol_alignment.py
```

Expected: Diff is limited to coverage guard helpers, coverage guard tests, protocol alignment tests, and enum-key test metadata migrations.

- [ ] **Step 6: Commit verification-only cleanup if needed**

If verification required small cleanup edits:

```bash
git add tests/cross_backend/argument_types tests/unit/test_protocol_alignment.py
git commit -m "test: finalize protocol drift guard verification"
```

If no cleanup edits were needed, do not create an empty commit.
