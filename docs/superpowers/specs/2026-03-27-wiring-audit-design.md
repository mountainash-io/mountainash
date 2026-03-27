# Wiring Audit Design Spec

## Goal

Create a comprehensive audit of every operation's wiring path through the six-layer architecture, with an automated test as the enforcer and a manual matrix document in the principles repo as the readable overview.

## Deliverables

### 1. Automated Test: `TestWiringAudit`

**Location:** `tests/unit/test_protocol_alignment.py` (alongside existing `TestInheritanceIntegrity`)

**Starting point:** ExpressionSystem protocol methods are the source of truth. The test walks every protocol class, collects public methods, and verifies each is wired through all downstream layers.

**Protocol classes to audit (18 total):**

Substrait ExpressionSystem (12):
- `SubstraitScalarComparisonExpressionSystemProtocol` (24 methods)
- `SubstraitScalarBooleanExpressionSystemProtocol` (5 methods)
- `SubstraitScalarArithmeticExpressionSystemProtocol` (34 methods incl. bitwise)
- `SubstraitScalarStringExpressionSystemProtocol` (37 methods)
- `SubstraitScalarDatetimeExpressionSystemProtocol` (18 methods)
- `SubstraitScalarRoundingExpressionSystemProtocol` (3 methods)
- `SubstraitScalarLogarithmicExpressionSystemProtocol` (5 methods)
- `SubstraitScalarSetExpressionSystemProtocol` (1 method)
- `SubstraitCastExpressionSystemProtocol` (1 method)
- `SubstraitConditionalExpressionSystemProtocol` (1 method)
- `SubstraitFieldReferenceExpressionSystemProtocol` (1 method)
- `SubstraitLiteralExpressionSystemProtocol` (1 method)

Mountainash Extensions (6):
- `MountainAshScalarTernaryExpressionSystemProtocol` (24 methods)
- `MountainAshNullExpressionSystemProtocol` (3 methods)
- `MountainAshNameExpressionSystemProtocol` (5 methods)
- `MountainAshScalarDatetimeExpressionSystemProtocol` (50 methods)
- `MountainAshScalarArithmeticExpressionSystemProtocol` (1 method)
- `MountainAshScalarBooleanExpressionSystemProtocol` (1 method)

**Per protocol method, check 5 downstream layers:**

| Layer | How to check |
|-------|-------------|
| **ENUM** | Reverse-lookup: does a `FunctionRegistry` entry exist that references this protocol method? If yes, extract the ENUM. |
| **Function Mapping** | Is there an `ExpressionFunctionDef` in `definitions.py` that binds this protocol method to an ENUM? (Same check as ENUM, but confirms the binding exists.) |
| **API Builder** | Does an API builder class (Substrait or extension) expose a method that produces a `ScalarFunctionNode` with the corresponding ENUM key? Check via the `FunctionRegistry`: if an `ExpressionFunctionDef` exists for this protocol method, the API builder layer is considered wired. The AST construction tests (`test_ast_*.py`) separately verify that the builder actually produces the correct node. |
| **Backend: Polars** | Does `PolarsExpressionSystem` (composed class) have a method matching the protocol method name? |
| **Backend: Ibis** | Does `IbisExpressionSystem` (composed class) have a method matching the protocol method name? |
| **Backend: Narwhals** | Does `NarwhalsExpressionSystem` (composed class) have a method matching the protocol method name? |

**Also check the reverse:**
- Orphan ENUMs: any ENUM value in `FKEY_SUBSTRAIT_*` or `FKEY_MOUNTAINASH_*` that has no corresponding protocol method.

**Known aspirational gaps:** Operations that exist in the protocol but are intentionally not yet wired through all layers. These are collected in a `KNOWN_ASPIRATIONAL` dict mapping `(ProtocolClass, method_name)` to a reason string, and are xfailed.

**Initial known aspirational set (from current audit):**

Substrait Scalar Arithmetic:
- `factorial` — no ENUM, no function mapping, backends have stubs
- `bitwise_not`, `bitwise_and`, `bitwise_or`, `bitwise_xor`, `shift_left`, `shift_right`, `shift_right_unsigned` — ENUMs exist, API builder stubs exist, no function mapping, backend stubs exist

Substrait Scalar Comparison:
- `is_not_distinct_from`, `is_distinct_from` — in protocol + backends, no ENUM, no function mapping, no API builder

Substrait Scalar String:
- `regexp_match_substring_all`, `regexp_strpos`, `regexp_count_substring` — in protocol + backends, no function mapping

Substrait Scalar Datetime:
- `add`, `subtract`, `multiply`, `add_intervals`, `lt`, `lte`, `gt`, `gte`, `local_timestamp`, `strptime_time`, `strptime_date`, `strptime_timestamp`, `round_temporal`, `round_calendar` — most have no ENUM or function mapping (datetime uses extract-based dispatch)

Substrait Scalar Logarithmic:
- `log1p` — in protocol + backends, no ENUM, no function mapping

Mountainash Scalar Datetime:
- `today`, `now` — in protocol + backends, no ENUM or function mapping
- `diff_microseconds` — in backends but may not have ENUM

Mountainash Scalar Set:
- Narwhals missing `index_in` in extension set

**Test structure:**

```python
class TestWiringAudit:
    """Validate every protocol method is wired through all 6 layers."""

    # Map: ExpressionSystemProtocol → (ENUM class, API builder class, category label)
    PROTOCOL_REGISTRY = {
        SubstraitScalarComparisonExpressionSystemProtocol: {
            "enum_class": FKEY_SUBSTRAIT_SCALAR_COMPARISON,
            "category": "substrait_scalar_comparison",
        },
        # ... all 18 protocols
    }

    KNOWN_ASPIRATIONAL: dict[tuple[type, str], str] = {
        (SubstraitScalarArithmeticExpressionSystemProtocol, "factorial"): "No backend support yet",
        (SubstraitScalarArithmeticExpressionSystemProtocol, "bitwise_not"): "Bitwise ops aspirational",
        # ... etc
    }

    def _get_protocol_methods(self, protocol_cls) -> list[str]:
        """Extract public methods from a protocol class."""
        return [
            name for name in dir(protocol_cls)
            if not name.startswith("_")
            and callable(getattr(protocol_cls, name, None))
        ]

    def _check_function_registry(self, protocol_cls, method_name) -> bool:
        """Check if a FunctionDef exists binding this protocol method."""
        # Introspect FunctionRegistry entries
        ...

    def _check_backend(self, backend_cls, method_name) -> bool:
        """Check if the composed backend class has this method."""
        return hasattr(backend_cls, method_name)

    @pytest.mark.parametrize("protocol_cls", PROTOCOL_REGISTRY.keys())
    def test_all_protocol_methods_wired(self, protocol_cls):
        """For each protocol method, verify all downstream layers exist."""
        methods = self._get_protocol_methods(protocol_cls)
        gaps = []
        for method_name in methods:
            key = (protocol_cls, method_name)
            if key in self.KNOWN_ASPIRATIONAL:
                continue  # Handled by separate xfail test
            missing = []
            if not self._check_function_registry(protocol_cls, method_name):
                missing.append("Function Mapping")
            if not self._check_backend(PolarsExpressionSystem, method_name):
                missing.append("Polars")
            if not self._check_backend(IbisExpressionSystem, method_name):
                missing.append("Ibis")
            if not self._check_backend(NarwhalsExpressionSystem, method_name):
                missing.append("Narwhals")
            if missing:
                gaps.append(f"{method_name}: missing [{', '.join(missing)}]")
        assert not gaps, f"\n{protocol_cls.__name__} wiring gaps:\n" + "\n".join(gaps)

    def test_no_orphan_enums(self):
        """Every ENUM value should map to a protocol method."""
        # Walk all FKEY_* enums, check each has a FunctionDef
        # that references a protocol method
        ...

    @pytest.mark.parametrize("protocol_cls,method_name,reason",
        [(cls, m, r) for (cls, m), r in KNOWN_ASPIRATIONAL.items()])
    @pytest.mark.xfail(reason="Aspirational — not yet wired")
    def test_aspirational_method(self, protocol_cls, method_name, reason):
        """Document and track aspirational methods."""
        # Same checks as above, but xfailed
        ...
```

### 2. Manual Matrix Document

**Location:** `mountainash-central/01.principles/mountainash-expresions/a.architecture/wiring-matrix.md`

**Follows standard principles template:** Status (ADOPTED), The Principle, Rationale, Examples (the matrix), Anti-Patterns, Technical Reference, Future Considerations.

**Matrix format:** One table per category, protocol method as row key, 7 columns:

```markdown
### Substrait Scalar Comparison

| Protocol Method       | ENUM | Fn Map | API Bldr | Polars | Ibis | Narwhals |
|-----------------------|------|--------|----------|--------|------|----------|
| equal                 | ✓    | ✓      | ✓        | ✓      | ✓    | ✓        |
| not_equal             | ✓    | ✓      | ✓        | ✓      | ✓    | ✓        |
| is_not_distinct_from  | -    | -      | -        | ✓      | ✓    | ✓        |
| is_distinct_from      | -    | -      | -        | ✓      | ✓    | ✓        |
| lt                    | ✓    | ✓      | ✓        | ✓      | ✓    | ✓        |
...
```

Legend: `✓` = present, `-` = missing (aspirational), `✗` = should exist but doesn't (bug)

**Known Gaps / Aspirational section:** Separate table listing all methods from `KNOWN_ASPIRATIONAL` with their reasons and which layers are missing.

**Categories covered (18 tables):**
- Substrait: Scalar Comparison, Scalar Boolean, Scalar Arithmetic, Scalar String, Scalar Datetime, Scalar Rounding, Scalar Logarithmic, Scalar Set, Cast, Conditional, Field Reference, Literal
- Mountainash: Ternary, Null, Name, Scalar Datetime, Scalar Arithmetic, Scalar Boolean

## Scope Boundaries

**In scope:**
- All operations with an ExpressionSystem protocol method defined
- Orphan ENUM detection (ENUMs without protocol methods)
- Known aspirational gaps documented with reasons

**Out of scope:**
- API builder aliases (these are tested separately in `test_ast_*.py`)
- API builder protocol alignment (already covered by existing `TestProtocolAlignment`)
- Namespace wiring (`_FLAT_NAMESPACES`, `.str`/`.dt`/`.name` descriptors)
- Cross-backend behavioral differences (covered by `tests/cross_backend/`)

## How It Stays Current

- **Automated test fails** when a new protocol method is added without wiring through all layers
- **Automated test fails** when a new ENUM is added without a protocol method
- **Manual matrix** is updated alongside the principles when operations are added (the `adding-operations.md` principle already describes the 5-step process)
- Moving an operation from aspirational to wired means removing it from `KNOWN_ASPIRATIONAL` and updating the matrix
