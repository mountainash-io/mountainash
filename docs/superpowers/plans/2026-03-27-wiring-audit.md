# Wiring Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated test that validates every ExpressionSystem protocol method is wired through all architecture layers, plus a manual matrix document in the principles repo.

**Architecture:** Protocol methods are the source of truth. The test introspects all 18 protocol classes, checks each method against the FunctionRegistry and backend composed classes, and reports gaps. Known aspirational gaps are xfailed. A separate markdown matrix in `mountainash-central` provides the human-readable overview.

**Tech Stack:** Python, pytest, `ExpressionFunctionRegistry` introspection, existing `test_protocol_alignment.py` infrastructure.

---

### Task 1: Add FunctionRegistry introspection helper

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py` (append after existing `_collect_classes_from_package` function, around line 921)

This task adds a helper function that checks whether a given protocol method has an `ExpressionFunctionDef` entry in the FunctionRegistry. The registry maps ENUM keys → `ExpressionFunctionDef` objects, and each `ExpressionFunctionDef` has a `protocol_method` attribute. We need to reverse-lookup: given a protocol class and method name, is there any registered function that references it?

- [ ] **Step 1: Write the failing test**

Add at the bottom of `tests/unit/test_protocol_alignment.py`:

```python
class TestWiringAuditHelpers:
    """Test the helper functions used by the wiring audit."""

    def test_check_function_registry_finds_registered_method(self):
        """A known registered method (e.g., equal) should be found."""
        found = _check_function_registry(
            SubstraitScalarComparisonExpressionSystemProtocol, "equal"
        )
        assert found is True

    def test_check_function_registry_rejects_unregistered_method(self):
        """A method not in the registry (e.g., is_not_distinct_from) should return False."""
        found = _check_function_registry(
            SubstraitScalarComparisonExpressionSystemProtocol, "is_not_distinct_from"
        )
        assert found is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers -v`
Expected: FAIL with `NameError: name '_check_function_registry' is not defined`

- [ ] **Step 3: Write the implementation**

Add the following function after the existing `_collect_classes_from_package` function (around line 921), before the `TestInheritanceIntegrity` class:

```python
def _check_function_registry(protocol_cls: type, method_name: str) -> bool:
    """Check if a FunctionRegistry entry exists that references this protocol method.

    Walks all registered ExpressionFunctionDef entries and checks if any
    has a protocol_method whose __name__ matches method_name and whose
    __qualname__ prefix matches the protocol class name.

    Returns True if a matching registration exists, False otherwise.
    """
    from mountainash_expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry

    # Ensure registry is initialized
    all_keys = ExpressionFunctionRegistry.list_all()

    for key in all_keys:
        func_def = ExpressionFunctionRegistry.get(key)
        if func_def.protocol_method is None:
            continue
        pm = func_def.protocol_method
        # protocol_method is an unbound function reference like
        # SubstraitScalarComparisonExpressionSystemProtocol.equal
        # Its __qualname__ is "ClassName.method_name"
        qualname = getattr(pm, "__qualname__", "")
        if "." in qualname:
            cls_part, method_part = qualname.rsplit(".", 1)
            if cls_part == protocol_cls.__name__ and method_part == method_name:
                return True
    return False
```

Also add the import at the top of the file (after existing imports, around line 31):

```python
from enum import Enum
```

(Note: `Enum` is already imported indirectly via the function key imports, but it's good to have it explicit for the later orphan enum test.)

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers -v`
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: add FunctionRegistry introspection helper for wiring audit"
```

---

### Task 2: Add `_get_all_enum_classes` helper

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`

This helper collects all FKEY_* enum classes for the orphan enum detection test.

- [ ] **Step 1: Write the failing test**

Add to `TestWiringAuditHelpers`:

```python
    def test_get_all_enum_classes_finds_enums(self):
        """Should discover all FKEY_* enum classes."""
        enums = _get_all_enum_classes()
        # We know at least these exist
        from mountainash_expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_COMPARISON,
            FKEY_MOUNTAINASH_SCALAR_TERNARY,
        )
        enum_types = {type(e) for e in enums}
        assert FKEY_SUBSTRAIT_SCALAR_COMPARISON in enum_types
        assert FKEY_MOUNTAINASH_SCALAR_TERNARY in enum_types
        # Should have both Substrait and Mountainash
        assert len(enums) > 50  # There are 100+ enum values total
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers::test_get_all_enum_classes_finds_enums -v`
Expected: FAIL with `NameError: name '_get_all_enum_classes' is not defined`

- [ ] **Step 3: Write the implementation**

Add after `_check_function_registry`:

```python
def _get_all_enum_classes() -> list:
    """Collect all FKEY_* enum values from function_keys/enums.py.

    Returns a flat list of all enum members across all FKEY_SUBSTRAIT_*
    and FKEY_MOUNTAINASH_* enum classes.
    """
    import mountainash_expressions.core.expression_system.function_keys.enums as enums_module

    all_values = []
    for attr_name in dir(enums_module):
        if not attr_name.startswith("FKEY_"):
            continue
        attr = getattr(enums_module, attr_name)
        if isinstance(attr, type) and issubclass(attr, Enum):
            all_values.extend(attr)
    return all_values
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers::test_get_all_enum_classes_finds_enums -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: add enum discovery helper for wiring audit"
```

---

### Task 3: Build the `WIRING_PROTOCOL_REGISTRY` mapping

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`

This is the central data structure: a dict mapping each ExpressionSystem protocol class to its category label. This tells the wiring audit which protocols to walk.

- [ ] **Step 1: Add the registry constant**

Add after the existing `MOUNTAINASH_API_BUILDER_IMPLEMENTATIONS` dict (around line 604), before the `TestSubstraitProtocolAlignment` class:

```python
# =============================================================================
# Wiring Audit: Protocol Registry
# =============================================================================

# Maps each ExpressionSystem protocol to its category label.
# This is the source of truth for the wiring audit — every protocol
# listed here will have all its methods checked across all layers.
WIRING_PROTOCOL_REGISTRY = {
    # Substrait ExpressionSystem protocols
    SubstraitScalarComparisonExpressionSystemProtocol: "substrait_scalar_comparison",
    SubstraitScalarBooleanExpressionSystemProtocol: "substrait_scalar_boolean",
    SubstraitScalarArithmeticExpressionSystemProtocol: "substrait_scalar_arithmetic",
    SubstraitScalarStringExpressionSystemProtocol: "substrait_scalar_string",
    SubstraitScalarDatetimeExpressionSystemProtocol: "substrait_scalar_datetime",
    SubstraitScalarRoundingExpressionSystemProtocol: "substrait_scalar_rounding",
    SubstraitScalarLogarithmicExpressionSystemProtocol: "substrait_scalar_logarithmic",
    SubstraitScalarSetExpressionSystemProtocol: "substrait_scalar_set",
    SubstraitCastExpressionSystemProtocol: "substrait_cast",
    SubstraitConditionalExpressionSystemProtocol: "substrait_conditional",
    SubstraitFieldReferenceExpressionSystemProtocol: "substrait_field_reference",
    SubstraitLiteralExpressionSystemProtocol: "substrait_literal",
    # Mountainash Extension protocols
    MountainAshScalarTernaryExpressionSystemProtocol: "mountainash_scalar_ternary",
    MountainAshNullExpressionSystemProtocol: "mountainash_null",
    MountainAshNameExpressionSystemProtocol: "mountainash_name",
    MountainAshScalarDatetimeExpressionSystemProtocol: "mountainash_scalar_datetime",
    MountainAshScalarArithmeticExpressionSystemProtocol: "mountainash_scalar_arithmetic",
    MountainAshScalarBooleanExpressionSystemProtocol: "mountainash_scalar_boolean",
}
```

- [ ] **Step 2: Write a smoke test**

Add to `TestWiringAuditHelpers`:

```python
    def test_wiring_protocol_registry_complete(self):
        """Registry should contain all 18 protocol classes."""
        assert len(WIRING_PROTOCOL_REGISTRY) == 18
```

- [ ] **Step 3: Run test to verify it passes**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers::test_wiring_protocol_registry_complete -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: add WIRING_PROTOCOL_REGISTRY for wiring audit"
```

---

### Task 4: Build the `KNOWN_ASPIRATIONAL` set

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`

This set contains `(ProtocolClass, method_name)` tuples for methods that are intentionally not fully wired. These get xfailed instead of hard-failing.

- [ ] **Step 1: Add the constant**

Add right after `WIRING_PROTOCOL_REGISTRY`:

```python
# Methods that exist in protocols but are intentionally not fully wired yet.
# Each entry maps (protocol_cls, method_name) → reason string.
# These are xfailed in the wiring audit, not hard failures.
KNOWN_ASPIRATIONAL: dict[tuple[type, str], str] = {
    # Substrait Scalar Arithmetic — bitwise operations
    (SubstraitScalarArithmeticExpressionSystemProtocol, "bitwise_not"): "Bitwise ops: no function mapping registered",
    (SubstraitScalarArithmeticExpressionSystemProtocol, "bitwise_and"): "Bitwise ops: no function mapping registered",
    (SubstraitScalarArithmeticExpressionSystemProtocol, "bitwise_or"): "Bitwise ops: no function mapping registered",
    (SubstraitScalarArithmeticExpressionSystemProtocol, "bitwise_xor"): "Bitwise ops: no function mapping registered",
    (SubstraitScalarArithmeticExpressionSystemProtocol, "shift_left"): "Bitwise ops: no function mapping registered",
    (SubstraitScalarArithmeticExpressionSystemProtocol, "shift_right"): "Bitwise ops: no function mapping registered",
    (SubstraitScalarArithmeticExpressionSystemProtocol, "shift_right_unsigned"): "Bitwise ops: no function mapping registered",
    (SubstraitScalarArithmeticExpressionSystemProtocol, "factorial"): "No backend support yet",
    # Substrait Scalar Comparison — distinct operations
    (SubstraitScalarComparisonExpressionSystemProtocol, "is_not_distinct_from"): "No ENUM, no function mapping, no API builder",
    (SubstraitScalarComparisonExpressionSystemProtocol, "is_distinct_from"): "No ENUM, no function mapping, no API builder",
    # Substrait Scalar String — advanced regex
    (SubstraitScalarStringExpressionSystemProtocol, "regexp_match_substring_all"): "No function mapping registered",
    (SubstraitScalarStringExpressionSystemProtocol, "regexp_strpos"): "No function mapping registered",
    (SubstraitScalarStringExpressionSystemProtocol, "regexp_count_substring"): "No function mapping registered",
    # Substrait Scalar Datetime — most methods use Mountainash extension dispatch
    (SubstraitScalarDatetimeExpressionSystemProtocol, "add"): "Datetime dispatch via Mountainash extensions",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "subtract"): "Datetime dispatch via Mountainash extensions",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "multiply"): "Datetime dispatch via Mountainash extensions",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "add_intervals"): "Datetime dispatch via Mountainash extensions",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "lt"): "Datetime comparisons handled by scalar_comparison",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "lte"): "Datetime comparisons handled by scalar_comparison",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "gt"): "Datetime comparisons handled by scalar_comparison",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "gte"): "Datetime comparisons handled by scalar_comparison",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "local_timestamp"): "No function mapping registered",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "strptime_time"): "No function mapping registered",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "strptime_date"): "No function mapping registered",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "strptime_timestamp"): "No function mapping registered",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "round_temporal"): "No function mapping registered",
    (SubstraitScalarDatetimeExpressionSystemProtocol, "round_calendar"): "No function mapping registered",
    # Substrait Scalar Logarithmic
    (SubstraitScalarLogarithmicExpressionSystemProtocol, "log1p"): "No ENUM, no function mapping",
    # Mountainash Scalar Datetime — today/now
    (MountainAshScalarDatetimeExpressionSystemProtocol, "today"): "No ENUM or function mapping",
    (MountainAshScalarDatetimeExpressionSystemProtocol, "now"): "No ENUM or function mapping",
}
```

- [ ] **Step 2: Write a smoke test**

Add to `TestWiringAuditHelpers`:

```python
    def test_known_aspirational_references_valid_protocols(self):
        """Every protocol class in KNOWN_ASPIRATIONAL must be in WIRING_PROTOCOL_REGISTRY."""
        for (protocol_cls, method_name), reason in KNOWN_ASPIRATIONAL.items():
            assert protocol_cls in WIRING_PROTOCOL_REGISTRY, (
                f"KNOWN_ASPIRATIONAL references {protocol_cls.__name__}.{method_name} "
                f"but that protocol is not in WIRING_PROTOCOL_REGISTRY"
            )

    def test_known_aspirational_references_real_methods(self):
        """Every method in KNOWN_ASPIRATIONAL must actually exist on the protocol."""
        for (protocol_cls, method_name), reason in KNOWN_ASPIRATIONAL.items():
            methods = get_protocol_methods(protocol_cls)
            assert method_name in methods, (
                f"KNOWN_ASPIRATIONAL references {protocol_cls.__name__}.{method_name} "
                f"but that method does not exist on the protocol"
            )
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAuditHelpers -v`
Expected: All PASS (the aspirational entries reference real protocol methods)

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: add KNOWN_ASPIRATIONAL set for wiring audit"
```

---

### Task 5: Build `TestWiringAudit.test_all_protocol_methods_wired`

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`

This is the core test: for each protocol in `WIRING_PROTOCOL_REGISTRY`, it walks every method, skips known aspirational ones, and checks function registry + all 3 backends.

- [ ] **Step 1: Add the backend composed class imports**

Add to the imports section (after the Narwhals backend imports, around line 354):

```python
# Composed backend classes (for wiring audit hasattr checks)
from mountainash_expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash_expressions.backends.expression_systems.ibis import IbisExpressionSystem
from mountainash_expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem
```

- [ ] **Step 2: Write the test class**

Add at the very end of the file, after `TestInheritanceIntegrity`:

```python
# =============================================================================
# Wiring Audit
# =============================================================================

class TestWiringAudit:
    """Validate every protocol method is wired through all architecture layers.

    Starting point: ExpressionSystem protocol methods are the source of truth.
    For each protocol method, checks:
    1. Function Registry (ENUM + ExpressionFunctionDef binding)
    2. Backend: Polars (method exists on composed PolarsExpressionSystem)
    3. Backend: Ibis (method exists on composed IbisExpressionSystem)
    4. Backend: Narwhals (method exists on composed NarwhalsExpressionSystem)

    Known aspirational gaps (methods intentionally not yet wired) are
    tested separately with xfail markers.
    """

    BACKENDS = {
        "Polars": PolarsExpressionSystem,
        "Ibis": IbisExpressionSystem,
        "Narwhals": NarwhalsExpressionSystem,
    }

    @pytest.mark.parametrize(
        "protocol_cls",
        list(WIRING_PROTOCOL_REGISTRY.keys()),
        ids=list(WIRING_PROTOCOL_REGISTRY.values()),
    )
    def test_all_protocol_methods_wired(self, protocol_cls):
        """For each protocol, verify all non-aspirational methods are fully wired."""
        methods = get_protocol_methods(protocol_cls)
        gaps = []

        for method_name in sorted(methods):
            key = (protocol_cls, method_name)
            if key in KNOWN_ASPIRATIONAL:
                continue  # Handled by test_aspirational_methods

            missing = []

            # Check function registry
            if not _check_function_registry(protocol_cls, method_name):
                missing.append("FunctionRegistry")

            # Check backends
            for backend_name, backend_cls in self.BACKENDS.items():
                if not hasattr(backend_cls, method_name):
                    missing.append(backend_name)

            if missing:
                gaps.append(f"  {method_name}: missing [{', '.join(missing)}]")

        assert not gaps, (
            f"\n{protocol_cls.__name__} wiring gaps:\n" + "\n".join(gaps)
        )
```

- [ ] **Step 3: Run the test**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAudit::test_all_protocol_methods_wired -v`
Expected: All 18 parametrized tests PASS. If any fail, that means a non-aspirational method has a wiring gap — add it to `KNOWN_ASPIRATIONAL` with a reason, or fix the gap.

- [ ] **Step 4: Fix any unexpected failures**

If a protocol method is missing from a backend or the function registry and it's NOT a genuine bug, add it to `KNOWN_ASPIRATIONAL` with a clear reason. The initial aspirational set may be incomplete — this run will discover any additional gaps.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: add wiring audit for protocol-to-backend completeness"
```

---

### Task 6: Add `test_aspirational_methods`

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`

This test documents all known aspirational gaps as xfailed tests, making them visible in test output.

- [ ] **Step 1: Add the xfail parametrized test**

Add to the `TestWiringAudit` class:

```python
    @pytest.mark.parametrize(
        "protocol_cls,method_name,reason",
        [
            pytest.param(cls, method, reason, id=f"{cls.__name__}.{method}")
            for (cls, method), reason in KNOWN_ASPIRATIONAL.items()
        ],
    )
    @pytest.mark.xfail(reason="Aspirational — not yet fully wired")
    def test_aspirational_method(self, protocol_cls, method_name, reason):
        """Aspirational methods: document and track wiring gaps."""
        missing = []

        if not _check_function_registry(protocol_cls, method_name):
            missing.append("FunctionRegistry")

        for backend_name, backend_cls in self.BACKENDS.items():
            if not hasattr(backend_cls, method_name):
                missing.append(backend_name)

        assert not missing, (
            f"{protocol_cls.__name__}.{method_name} ({reason}):\n"
            f"  missing [{', '.join(missing)}]"
        )
```

- [ ] **Step 2: Run the test**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAudit::test_aspirational_method -v`
Expected: All xfailed (shown as `XFAIL`). If any XPASS, that means the method is now fully wired and should be removed from `KNOWN_ASPIRATIONAL`.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: add xfail tracking for aspirational wiring gaps"
```

---

### Task 7: Add `test_no_orphan_enums`

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py`

This test checks the reverse direction: every ENUM value that's registered in the FunctionRegistry should reference a protocol method.

- [ ] **Step 1: Add the test**

Add to the `TestWiringAudit` class:

```python
    def test_no_orphan_enums(self):
        """Every registered ENUM should reference a protocol method."""
        from mountainash_expressions.core.expression_system.function_mapping.registry import ExpressionFunctionRegistry

        all_keys = ExpressionFunctionRegistry.list_all()
        orphans = []

        for key in all_keys:
            func_def = ExpressionFunctionRegistry.get(key)
            if func_def.protocol_method is None:
                orphans.append(f"  {key}: registered but protocol_method is None")

        assert not orphans, (
            f"\nOrphan ENUM values (no protocol method reference):\n"
            + "\n".join(orphans)
        )
```

- [ ] **Step 2: Run the test**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAudit::test_no_orphan_enums -v`
Expected: PASS (all current registrations include protocol_method references)

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: add orphan ENUM detection to wiring audit"
```

---

### Task 8: Run full test suite and stabilize

**Files:**
- Modify: `tests/unit/test_protocol_alignment.py` (if needed)

- [ ] **Step 1: Run all wiring audit tests**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py -v`
Expected: All existing tests still pass. New wiring audit tests pass (non-aspirational) or xfail (aspirational). No regressions.

- [ ] **Step 2: Run the full test suite**

Run: `hatch run test:test-quick`
Expected: No regressions across the full suite.

- [ ] **Step 3: Fix any issues found**

If new wiring gaps are discovered that aren't already in `KNOWN_ASPIRATIONAL`, decide:
- Is it a genuine bug? → Leave it as a hard failure (to be fixed separately)
- Is it aspirational? → Add to `KNOWN_ASPIRATIONAL` with reason

- [ ] **Step 4: Commit any stabilization fixes**

```bash
git add tests/unit/test_protocol_alignment.py
git commit -m "test: stabilize wiring audit — finalize aspirational set"
```

---

### Task 9: Write the manual matrix document

**Files:**
- Create: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/a.architecture/wiring-matrix.md`

This is the human-readable matrix in the principles repo. It follows the standard principles document template.

- [ ] **Step 1: Run the wiring audit with verbose output to capture current state**

Run: `hatch run test:test-target-quick tests/unit/test_protocol_alignment.py::TestWiringAudit -v`
Use the output to populate the matrix — passed tests = fully wired, xfailed = aspirational gaps.

- [ ] **Step 2: Write the document**

Create `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/a.architecture/wiring-matrix.md` with:

```markdown
# Operation Wiring Matrix

> **Status:** ADOPTED

## The Principle

Every operation in the expression system must be wired through six architecture layers: (1) ExpressionSystem Protocol, (2) ENUM in function_keys, (3) ExpressionFunctionDef in function mapping, (4) API Builder, (5) Backend implementations (Polars, Ibis, Narwhals). The protocol layer is the source of truth — an operation that exists only as an ENUM or only as a backend method is incompletely wired.

## Rationale

The three-layer architecture (protocols → API builders → backend expression systems) plus the function mapping registry creates multiple points where wiring can break. A protocol method without a function mapping registration compiles to an AST node that silently fails at dispatch. A backend method without a protocol has no contract enforcing consistency across backends. The wiring matrix makes the completeness state visible at a glance, and the automated `TestWiringAudit` (in `tests/unit/test_protocol_alignment.py`) enforces it.

## Examples

Legend: `✓` = present, `-` = missing (aspirational/planned)

### Substrait Scalar Comparison

| Protocol Method      | ENUM | Fn Map | Polars | Ibis | Narwhals |
|----------------------|------|--------|--------|------|----------|
| equal                | ✓    | ✓      | ✓      | ✓    | ✓        |
| not_equal            | ✓    | ✓      | ✓      | ✓    | ✓        |
| lt                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| gt                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| lte                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| gte                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| between              | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_true              | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_not_true          | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_false             | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_not_false         | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_null              | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_not_null          | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_nan               | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_finite            | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_infinite          | ✓    | ✓      | ✓      | ✓    | ✓        |
| nullif               | ✓    | ✓      | ✓      | ✓    | ✓        |
| coalesce             | ✓    | ✓      | ✓      | ✓    | ✓        |
| least                | ✓    | ✓      | ✓      | ✓    | ✓        |
| least_skip_null      | ✓    | ✓      | ✓      | ✓    | ✓        |
| greatest             | ✓    | ✓      | ✓      | ✓    | ✓        |
| greatest_skip_null   | ✓    | ✓      | ✓      | ✓    | ✓        |
| is_not_distinct_from | -    | -      | ✓      | ✓    | ✓        |
| is_distinct_from     | -    | -      | ✓      | ✓    | ✓        |

### Substrait Scalar Boolean

| Protocol Method | ENUM | Fn Map | Polars | Ibis | Narwhals |
|-----------------|------|--------|--------|------|----------|
| and_            | ✓    | ✓      | ✓      | ✓    | ✓        |
| or_             | ✓    | ✓      | ✓      | ✓    | ✓        |
| not_            | ✓    | ✓      | ✓      | ✓    | ✓        |
| xor             | ✓    | ✓      | ✓      | ✓    | ✓        |
| and_not         | ✓    | ✓      | ✓      | ✓    | ✓        |

### Substrait Scalar Arithmetic

| Protocol Method       | ENUM | Fn Map | Polars | Ibis | Narwhals |
|-----------------------|------|--------|--------|------|----------|
| add                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| subtract              | ✓    | ✓      | ✓      | ✓    | ✓        |
| multiply              | ✓    | ✓      | ✓      | ✓    | ✓        |
| divide                | ✓    | ✓      | ✓      | ✓    | ✓        |
| modulus               | ✓    | ✓      | ✓      | ✓    | ✓        |
| power                 | ✓    | ✓      | ✓      | ✓    | ✓        |
| negate                | ✓    | ✓      | ✓      | ✓    | ✓        |
| abs                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| sign                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| sqrt                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| exp                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| sin                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| cos                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| tan                   | ✓    | ✓      | ✓      | ✓    | ✓        |
| asin                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| acos                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| atan                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| atan2                 | ✓    | ✓      | ✓      | ✓    | ✓        |
| sinh                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| cosh                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| tanh                  | ✓    | ✓      | ✓      | ✓    | ✓        |
| asinh                 | ✓    | ✓      | ✓      | ✓    | ✓        |
| acosh                 | ✓    | ✓      | ✓      | ✓    | ✓        |
| atanh                 | ✓    | ✓      | ✓      | ✓    | ✓        |
| radians               | ✓    | ✓      | ✓      | ✓    | ✓        |
| degrees               | ✓    | ✓      | ✓      | ✓    | ✓        |
| factorial             | -    | -      | ✓      | ✓    | ✓        |
| bitwise_not           | -    | -      | ✓      | ✓    | ✓        |
| bitwise_and           | -    | -      | ✓      | ✓    | ✓        |
| bitwise_or            | -    | -      | ✓      | ✓    | ✓        |
| bitwise_xor           | -    | -      | ✓      | ✓    | ✓        |
| shift_left            | -    | -      | ✓      | ✓    | ✓        |
| shift_right           | -    | -      | ✓      | ✓    | ✓        |
| shift_right_unsigned  | -    | -      | ✓      | ✓    | ✓        |

*(Remaining categories: Scalar String, Scalar Datetime, Scalar Rounding, Scalar Logarithmic, Scalar Set, Cast, Conditional, Field Reference, Literal, and all 6 Mountainash extension categories follow the same format. Populate from `TestWiringAudit` output.)*

## Known Gaps / Aspirational

| Category | Method | Missing Layers | Reason |
|----------|--------|---------------|--------|
| Substrait Arithmetic | factorial | ENUM, Fn Map | No backend support yet |
| Substrait Arithmetic | bitwise_* (7) | Fn Map | API builder stubs exist, no dispatch |
| Substrait Comparison | is_[not_]distinct_from | ENUM, Fn Map, API Bldr | Protocol + backend only |
| Substrait String | regexp_match_substring_all | Fn Map | Protocol + backend only |
| Substrait String | regexp_strpos | Fn Map | Protocol + backend only |
| Substrait String | regexp_count_substring | Fn Map | Protocol + backend only |
| Substrait Datetime | add, subtract, multiply, ... (14) | ENUM, Fn Map | Dispatch via Mountainash extensions |
| Substrait Logarithmic | log1p | ENUM, Fn Map | Protocol + backend only |
| Mountainash Datetime | today, now | ENUM, Fn Map | Protocol + backend only |

## Anti-Patterns

- **Adding an ENUM without a protocol method.** The automated `TestWiringAudit.test_no_orphan_enums` catches this.
- **Adding a protocol method without wiring through all layers.** `TestWiringAudit.test_all_protocol_methods_wired` catches this as a hard failure (not xfail).
- **Leaving a method in `KNOWN_ASPIRATIONAL` after it's been fully wired.** The xfail test will XPASS, signaling it should be removed from the aspirational set.
- **Updating the matrix without running the audit test.** The test is the source of truth; the matrix is the communication tool.

## Technical Reference

- `tests/unit/test_protocol_alignment.py` — `TestWiringAudit` class (automated enforcer)
- `src/mountainash_expressions/core/expression_protocols/expression_systems/` — Protocol definitions
- `src/mountainash_expressions/core/expression_system/function_keys/enums.py` — ENUM definitions
- `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py` — Function registry bindings
- `src/mountainash_expressions/backends/expression_systems/{polars,ibis,narwhals}/` — Backend implementations
- `mountainash-central/01.principles/mountainash-expresions/f.extension-model/adding-operations.md` — 5-step process for adding new operations

## Future Considerations

- A code generator could produce the markdown matrix directly from `TestWiringAudit` output, reducing manual maintenance.
- As aspirational methods are implemented, they should be removed from `KNOWN_ASPIRATIONAL` and the matrix updated.
- Window functions and aggregate functions will add new protocol categories to the registry.
```

- [ ] **Step 3: Commit to principles repo**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/a.architecture/wiring-matrix.md
git commit -m "docs: add operation wiring matrix principle (ADOPTED)"
```

---

### Task 10: Update principles README

**Files:**
- Modify: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/a.architecture/` — check if there's an index or README to update

- [ ] **Step 1: Check for existing README**

Run: `cat /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/README.md`
Check if it lists documents in `a.architecture/`.

- [ ] **Step 2: Add the new document to the README**

Add `wiring-matrix.md` to the appropriate section of the README, following the existing pattern. The one-line description should be: `Every operation must be wired through all six architecture layers — protocol, ENUM, function mapping, API builder, backends.`

- [ ] **Step 3: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/README.md
git commit -m "docs: add wiring-matrix to principles README"
```
