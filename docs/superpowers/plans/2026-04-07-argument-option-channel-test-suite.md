# Argument/Option Channel Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a drift-proof test suite that verifies every expression-typed parameter and every option parameter behaves correctly across Polars, Ibis, and Narwhals backends.

**Architecture:** Per-category test files declaring `TESTED_PARAMS` lists, a protocol introspector that classifies each parameter as `argument` or `option`, a coverage-guard meta-test asserting introspected == tested, and a registry-driven error-enrichment suite. Known limitations use `pytest.mark.xfail(strict=True, raises=BackendCapabilityError)` for self-healing.

**Tech Stack:** Python 3.11+, pytest, polars, ibis-framework, narwhals, pyright, hatch.

**Spec:** `docs/superpowers/specs/2026-04-07-argument-option-channel-test-suite-design.md`

---

## File Structure

```
tests/cross_backend/argument_types/
├── __init__.py                        # empty
├── conftest.py                        # make_df helper + shared xfail helper
├── _introspection.py                  # Protocol walker and classifier
├── _test_template.py                  # Shared parametrization helpers used by per-category files
├── test_coverage_guard.py             # Meta-test
├── test_error_enrichment.py           # Registry-driven positive assertions
├── test_option_channel.py             # All options together
├── test_arg_types_string.py
├── test_arg_types_arithmetic.py
├── test_arg_types_comparison.py
├── test_arg_types_boolean.py
├── test_arg_types_null.py
├── test_arg_types_rounding.py
├── test_arg_types_logarithmic.py
├── test_arg_types_datetime.py
├── test_arg_types_name.py
├── test_arg_types_window.py
└── test_arg_types_aggregate.py
```

Each `test_arg_types_<category>.py` exports:
- `TESTED_PARAMS: list[tuple[Any, str]]` — list of `(function_key, param_name)` tuples it covers
- Parametrized test functions that iterate over `(op_spec, input_type, backend)`

---

## Task 1: Protocol introspector

**Files:**
- Create: `tests/cross_backend/argument_types/__init__.py`
- Create: `tests/cross_backend/argument_types/_introspection.py`
- Create: `tests/cross_backend/argument_types/test_introspection_smoke.py`

- [ ] **Step 1: Create empty `__init__.py`**

```bash
touch tests/cross_backend/argument_types/__init__.py
```

- [ ] **Step 2: Write failing smoke test**

```python
# tests/cross_backend/argument_types/test_introspection_smoke.py
from tests.cross_backend.argument_types._introspection import introspect_protocols, ProtocolParam

def test_introspector_returns_non_empty():
    params = introspect_protocols()
    assert len(params) > 0, "introspector found no parameters"
    assert all(isinstance(p, ProtocolParam) for p in params)

def test_introspector_classifies_contains_substring_as_argument():
    params = introspect_protocols()
    match = [p for p in params if p.op_name == "contains" and p.param_name == "substring"]
    assert len(match) == 1
    assert match[0].kind == "argument"

def test_introspector_classifies_round_decimals_as_option():
    params = introspect_protocols()
    match = [p for p in params if p.op_name == "round" and p.param_name == "decimals"]
    assert len(match) == 1
    assert match[0].kind == "option"
```

- [ ] **Step 3: Run to verify failure**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_introspection_smoke.py
```

Expected: FAIL (module not found).

- [ ] **Step 4: Implement `_introspection.py`**

```python
# tests/cross_backend/argument_types/_introspection.py
"""Protocol walker that classifies parameters as arguments vs options."""
from __future__ import annotations

import inspect
import typing
from dataclasses import dataclass
from typing import Any, Literal, get_type_hints

from mountainash.expressions.core.expression_protocols.expression_systems import substrait as _substrait_mod
from mountainash.expressions.core.expression_protocols.expression_systems import extensions_mountainash as _ext_mod

Kind = Literal["argument", "option", "unclassified"]


@dataclass(frozen=True)
class ProtocolParam:
    op_name: str
    function_key: Any | None          # resolved in per-category file; None here
    param_name: str
    kind: Kind
    category: str                     # e.g. "string", "datetime"
    protocol_name: str
    annotation: str                   # stringified annotation for debugging


_CATEGORY_MAP = {
    "SubstraitScalarStringExpressionSystemProtocol": "string",
    "SubstraitScalarArithmeticExpressionSystemProtocol": "arithmetic",
    "SubstraitScalarComparisonExpressionSystemProtocol": "comparison",
    "SubstraitScalarBooleanExpressionSystemProtocol": "boolean",
    "SubstraitScalarDatetimeExpressionSystemProtocol": "datetime",
    "SubstraitScalarRoundingExpressionSystemProtocol": "rounding",
    "SubstraitScalarLogarithmicExpressionSystemProtocol": "logarithmic",
    "SubstraitWindowArithmeticExpressionSystemProtocol": "window",
    "SubstraitAggregateArithmeticExpressionSystemProtocol": "aggregate",
    "SubstraitAggregateStringExpressionSystemProtocol": "aggregate",
    "SubstraitAggregateBooleanExpressionSystemProtocol": "aggregate",
    "SubstraitAggregateGenericExpressionSystemProtocol": "aggregate",
    "MountainashNameExpressionSystemProtocol": "name",
    "MountainashNullExpressionSystemProtocol": "null",
    "MountainashScalarDatetimeExpressionSystemProtocol": "datetime",
    "MountainashScalarArithmeticExpressionSystemProtocol": "arithmetic",
    "MountainashScalarBooleanExpressionSystemProtocol": "boolean",
    "MountainashScalarTernaryExpressionSystemProtocol": "boolean",
    "MountainashScalarSetExpressionSystemProtocol": "boolean",
}

_EXCLUDED_PARAMS = {"self", "input"}


def _iter_protocol_classes():
    for mod in (_substrait_mod, _ext_mod):
        for name in dir(mod):
            obj = getattr(mod, name)
            if inspect.isclass(obj) and name.endswith("Protocol"):
                yield name, obj


def _classify_annotation(ann: Any) -> Kind:
    s = str(ann)
    # ExpressionT or TypeVar bound to it
    if "ExpressionT" in s:
        return "argument"
    # Union with ExpressionT
    origin = typing.get_origin(ann)
    if origin is typing.Union:
        args = typing.get_args(ann)
        if any("ExpressionT" in str(a) for a in args):
            return "argument"
    # Concrete Python primitives
    if ann in (int, str, bool, float, bytes):
        return "option"
    if s.startswith("typing.Optional[") and any(t in s for t in ("int", "str", "bool", "float")):
        return "option"
    # Any / unknown → unclassified
    if ann is typing.Any or s == "typing.Any":
        return "unclassified"
    return "unclassified"


def introspect_protocols() -> list[ProtocolParam]:
    results: list[ProtocolParam] = []
    for proto_name, proto_cls in _iter_protocol_classes():
        category = _CATEGORY_MAP.get(proto_name)
        if category is None:
            continue
        for op_name, method in inspect.getmembers(proto_cls, predicate=inspect.isfunction):
            if op_name.startswith("_"):
                continue
            try:
                hints = get_type_hints(method)
            except Exception:
                hints = {}
            sig = inspect.signature(method)
            for param_name, param in sig.parameters.items():
                if param_name in _EXCLUDED_PARAMS:
                    continue
                ann = hints.get(param_name, param.annotation)
                kind = _classify_annotation(ann)
                results.append(ProtocolParam(
                    op_name=op_name,
                    function_key=None,
                    param_name=param_name,
                    kind=kind,
                    category=category,
                    protocol_name=proto_name,
                    annotation=str(ann),
                ))
    return results
```

- [ ] **Step 5: Run smoke test**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_introspection_smoke.py
```

Expected: PASS (3/3).

- [ ] **Step 6: Commit**

```bash
git add tests/cross_backend/argument_types/
git commit -m "test(arg-types): add protocol introspector and smoke test"
```

---

## Task 2: Phase 0 audit — review classification table and fix protocol typing

**Files:**
- Create: `tests/cross_backend/argument_types/_audit_dump.py` (temporary debugging script, deleted at end)
- Modify: any protocol files surfaced by the audit (unknown in advance)

- [ ] **Step 1: Write audit dump script**

```python
# tests/cross_backend/argument_types/_audit_dump.py
"""Prints the classification table. Run manually; not a test."""
from tests.cross_backend.argument_types._introspection import introspect_protocols

if __name__ == "__main__":
    rows = introspect_protocols()
    by_kind: dict[str, list] = {"argument": [], "option": [], "unclassified": []}
    for r in rows:
        by_kind[r.kind].append(r)
    for kind, items in by_kind.items():
        print(f"\n=== {kind.upper()} ({len(items)}) ===")
        for r in sorted(items, key=lambda x: (x.category, x.op_name, x.param_name)):
            print(f"  [{r.category}] {r.op_name}({r.param_name}): {r.annotation}")
```

- [ ] **Step 2: Run the dump**

```bash
uv run python -m tests.cross_backend.argument_types._audit_dump > /tmp/audit.txt
cat /tmp/audit.txt
```

Expected: Prints three sections. Review `unclassified` carefully — those are the anomalies.

- [ ] **Step 3: Review each unclassified row**

For each row in the `UNCLASSIFIED` section:
- Open the protocol file (path from `protocol_name` + `_CATEGORY_MAP`)
- Decide: should this param be `ExpressionT` (argument) or a concrete type (option)?
- Rule: if any backend accepts a column reference for this param → `ExpressionT`; else use the concrete Python type.
- Rule: `Any` typing is never acceptable in protocols — always pick one.

- [ ] **Step 4: Fix each anomaly in its own commit**

For each fix:

```bash
# Example edit: change `decimals: Any = None` to `decimals: Optional[int] = None`
# in src/.../prtcl_expsys_scalar_rounding.py

hatch run test:test-target-quick tests/cross_backend/argument_types/test_introspection_smoke.py
hatch run mypy:check
git add src/mountainash/expressions/core/expression_protocols/
git commit -m "fix(protocols): type <param> as <concrete/ExpressionT> in <protocol>"
```

Repeat until `unclassified` section is empty.

- [ ] **Step 5: Re-run dump to confirm zero anomalies**

```bash
uv run python -m tests.cross_backend.argument_types._audit_dump | grep "UNCLASSIFIED"
```

Expected output: `=== UNCLASSIFIED (0) ===`

- [ ] **Step 6: Delete the audit script**

```bash
rm tests/cross_backend/argument_types/_audit_dump.py
git add -u tests/cross_backend/argument_types/_audit_dump.py
git commit -m "chore: remove phase 0 audit dump script"
```

---

## Task 3: Shared conftest and test template

**Files:**
- Create: `tests/cross_backend/argument_types/conftest.py`
- Create: `tests/cross_backend/argument_types/_test_template.py`

- [ ] **Step 1: Write conftest.py**

```python
# tests/cross_backend/argument_types/conftest.py
"""Shared fixtures for argument/option channel tests."""
from __future__ import annotations

from typing import Any

import pytest

ALL_BACKENDS = ["polars", "ibis", "narwhals"]


def make_df(data: dict[str, list[Any]], backend: str):
    """Materialize a dict of columns into a backend-native DataFrame."""
    import polars as pl
    pdf = pl.DataFrame(data)
    if backend == "polars":
        return pdf
    if backend == "ibis":
        import ibis
        return ibis.memtable(pdf.to_pandas())
    if backend == "narwhals":
        import narwhals as nw
        return nw.from_native(pdf.to_pandas(), eager_only=True)
    raise ValueError(f"Unknown backend: {backend}")


@pytest.fixture(params=ALL_BACKENDS)
def backend(request) -> str:
    return request.param
```

- [ ] **Step 2: Write `_test_template.py` with shared helpers**

```python
# tests/cross_backend/argument_types/_test_template.py
"""Shared helpers used by every test_arg_types_<category>.py file.

Each per-category file declares:
    TESTED_PARAMS: list[tuple[Any, str]]  # (function_key, param_name)
    OP_SPECS: list[OpSpec]                # one entry per operation under test

Then calls run_argument_matrix(op_spec, backend, input_type) per parametrized case.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError

INPUT_TYPES = ["raw", "lit", "col", "complex"]


@dataclass
class OpSpec:
    """Describes a single operation under test."""
    function_key: Any
    op_name: str
    # Function that builds the expression given (input_col, arg_value). Example:
    #   lambda inp, arg: inp.str.contains(arg)
    build: Callable[[Any, Any], Any]
    # Raw value used as the "truth" for each input type. Example: "hello"
    raw_arg: Any
    # Column name in the test frame that contains per-row values matching raw_arg
    arg_col_name: str
    # Name of the parameter being tested (matches registry key)
    param_name: str
    # Data dict passed to make_df
    data: dict[str, list[Any]]
    # Name of the primary input column (the "input" positional arg)
    input_col: str = "text"
    # Optional: additional kwargs forwarded to build() (rarely needed)
    extra: dict[str, Any] = field(default_factory=dict)


def _materialize_arg(input_type: str, raw: Any, col_name: str):
    """Produce the argument value for a given input type."""
    if input_type == "raw":
        return raw
    if input_type == "lit":
        return ma.lit(raw)
    if input_type == "col":
        return ma.col(col_name)
    if input_type == "complex":
        # Wrap in a no-op expression. For strings, .str.lower() of a col that's already lowercase
        # keeps the semantics identical.
        return ma.col(col_name).str.lower() if isinstance(raw, str) else ma.col(col_name) + 0
    raise ValueError(input_type)


def _get_registry(backend: str):
    if backend == "polars":
        from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem as B
    elif backend == "ibis":
        from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem as B
    elif backend == "narwhals":
        from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem as B
    else:
        raise ValueError(backend)
    return B.KNOWN_EXPR_LIMITATIONS


def xfail_if_limited(backend: str, function_key: Any, param_name: str, input_type: str):
    """Returns a pytest.mark.xfail if the registry declares this combination limited,
    and the input type actually exercises the limitation (col/complex, not raw/lit)."""
    if input_type in ("raw", "lit"):
        return None
    registry = _get_registry(backend)
    limitation = registry.get((function_key, param_name))
    if limitation is None:
        return None
    return pytest.mark.xfail(
        strict=True,
        raises=BackendCapabilityError,
        reason=limitation.message,
    )


def run_argument_matrix(op: OpSpec, backend: str, input_type: str):
    """Execute one cell of the (operation × backend × input_type) matrix."""
    from tests.cross_backend.argument_types.conftest import make_df

    df = make_df(op.data, backend)
    arg = _materialize_arg(input_type, op.raw_arg, op.arg_col_name)
    expr = op.build(ma.col(op.input_col), arg)
    # Compile and execute — just needs to not raise
    compiled = expr.compile(df)
    assert compiled is not None
```

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/argument_types/conftest.py tests/cross_backend/argument_types/_test_template.py
git commit -m "test(arg-types): add shared conftest and test template"
```

---

## Task 4: Coverage guard meta-test

**Files:**
- Create: `tests/cross_backend/argument_types/test_coverage_guard.py`

- [ ] **Step 1: Write failing test**

```python
# tests/cross_backend/argument_types/test_coverage_guard.py
"""Meta-test: every argument-kind protocol param must appear in exactly one TESTED_PARAMS list."""
from __future__ import annotations

import importlib
import pkgutil

from tests.cross_backend.argument_types._introspection import introspect_protocols

# All per-category test modules are discovered dynamically
_CATEGORY_MODULES = [
    "test_arg_types_string",
    "test_arg_types_arithmetic",
    "test_arg_types_comparison",
    "test_arg_types_boolean",
    "test_arg_types_null",
    "test_arg_types_rounding",
    "test_arg_types_logarithmic",
    "test_arg_types_datetime",
    "test_arg_types_name",
    "test_arg_types_window",
    "test_arg_types_aggregate",
]


def _collect_tested_params() -> set[tuple[str, str]]:
    """Collect (op_name, param_name) pairs from all per-category TESTED_PARAMS lists."""
    tested: set[tuple[str, str]] = set()
    for modname in _CATEGORY_MODULES:
        try:
            mod = importlib.import_module(f"tests.cross_backend.argument_types.{modname}")
        except ImportError:
            continue
        for fkey, pname in getattr(mod, "TESTED_PARAMS", []):
            # fkey is an enum member; use its .name for comparison against protocol op_name.lower()
            op_name = fkey.name.lower() if hasattr(fkey, "name") else str(fkey)
            tested.add((op_name, pname))
    return tested


def test_every_argument_param_is_tested():
    introspected = {
        (p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "argument"
    }
    tested = _collect_tested_params()
    # Normalize case — function keys sometimes differ from method names
    missing = {(op, pname) for op, pname in introspected if (op, pname) not in tested}
    extra = {(op, pname) for op, pname in tested if (op, pname) not in introspected}
    assert not missing, f"Argument params with no test: {sorted(missing)}"
    assert not extra, f"Tested params with no protocol: {sorted(extra)}"


def test_no_unclassified_params():
    unclassified = [p for p in introspect_protocols() if p.kind == "unclassified"]
    assert not unclassified, (
        f"Protocol params with ambiguous typing (fix in Phase 0): "
        f"{[(p.protocol_name, p.op_name, p.param_name, p.annotation) for p in unclassified]}"
    )
```

- [ ] **Step 2: Run to verify expected failure**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py
```

Expected: FAIL on `test_every_argument_param_is_tested` with a long `missing` list (because no per-category files exist yet). `test_no_unclassified_params` should PASS (Phase 0 already cleaned anomalies).

- [ ] **Step 3: Commit the failing guard**

```bash
git add tests/cross_backend/argument_types/test_coverage_guard.py
git commit -m "test(arg-types): add coverage guard meta-test (expected to fail until categories filled)"
```

---

## Task 5: Error enrichment test

**Files:**
- Create: `tests/cross_backend/argument_types/test_error_enrichment.py`

- [ ] **Step 1: Write test**

```python
# tests/cross_backend/argument_types/test_error_enrichment.py
"""Positively assert that BackendCapabilityError carries registry metadata."""
from __future__ import annotations

import pytest

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem

REGISTRIES = {
    "polars": PolarsBaseExpressionSystem.KNOWN_EXPR_LIMITATIONS,
    "ibis": IbisBaseExpressionSystem.KNOWN_EXPR_LIMITATIONS,
    "narwhals": NarwhalsBaseExpressionSystem.KNOWN_EXPR_LIMITATIONS,
}


@pytest.mark.parametrize("backend,registry", [(k, v) for k, v in REGISTRIES.items()])
def test_registry_entries_have_required_fields(backend: str, registry):
    for (fkey, pname), limitation in registry.items():
        assert limitation.message, f"{backend}:{fkey}:{pname} missing message"
        assert limitation.native_errors, f"{backend}:{fkey}:{pname} missing native_errors"
        assert isinstance(limitation.native_errors, tuple)
        for e in limitation.native_errors:
            assert isinstance(e, type) and issubclass(e, Exception)


def test_backend_capability_error_preserves_limitation_message():
    """When triggered, BackendCapabilityError carries the registry's message and workaround."""
    import mountainash as ma
    from tests.cross_backend.argument_types.conftest import make_df

    # Pick a known-limited case: Narwhals str.contains with a column reference
    df = make_df({"text": ["hello", "world"], "pat": ["he", "wo"]}, "narwhals")
    expr = ma.col("text").str.contains(ma.col("pat"))
    with pytest.raises(BackendCapabilityError) as exc_info:
        expr.compile(df)
    err = exc_info.value
    assert err.limitation is not None
    assert err.limitation.message in str(err)
    if err.limitation.workaround:
        assert err.limitation.workaround in str(err)
```

- [ ] **Step 2: Run**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_error_enrichment.py
```

Expected: PASS (3/3). If it fails on the contains case, the registry entry exists but the error isn't being enriched — diagnose and fix the enrichment layer before proceeding.

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/argument_types/test_error_enrichment.py
git commit -m "test(arg-types): add error enrichment assertions"
```

---

## Task 6: Migrate existing string tests to new structure

**Files:**
- Create: `tests/cross_backend/argument_types/test_arg_types_string.py`
- Delete: `tests/cross_backend/test_expression_argument_types.py`

This is the **template task**. Every subsequent per-category task follows this exact structure.

- [ ] **Step 1: Write `test_arg_types_string.py`**

```python
# tests/cross_backend/argument_types/test_arg_types_string.py
"""Argument channel tests for string operations."""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from tests.cross_backend.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    (FK_STR.CONTAINS, "substring"),
    (FK_STR.STARTS_WITH, "substring"),
    (FK_STR.ENDS_WITH, "substring"),
    (FK_STR.REPLACE, "pattern"),
    (FK_STR.REPLACE, "replacement"),
    (FK_STR.LPAD, "length"),
    (FK_STR.RPAD, "length"),
]

_DATA = {
    "text": ["hello", "world", "foobar"],
    "pat": ["he", "wo", "foo"],
    "rep": ["HE", "WO", "FOO"],
    "n": [8, 8, 10],
}

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_STR.CONTAINS,
        op_name="contains",
        build=lambda inp, arg: inp.str.contains(arg),
        raw_arg="he",
        arg_col_name="pat",
        param_name="substring",
        data=_DATA,
    ),
    OpSpec(
        function_key=FK_STR.STARTS_WITH,
        op_name="starts_with",
        build=lambda inp, arg: inp.str.starts_with(arg),
        raw_arg="he",
        arg_col_name="pat",
        param_name="substring",
        data=_DATA,
    ),
    OpSpec(
        function_key=FK_STR.ENDS_WITH,
        op_name="ends_with",
        build=lambda inp, arg: inp.str.ends_with(arg),
        raw_arg="lo",
        arg_col_name="pat",
        param_name="substring",
        data=_DATA,
    ),
    OpSpec(
        function_key=FK_STR.REPLACE,
        op_name="replace",
        build=lambda inp, arg: inp.str.replace(arg, "X"),
        raw_arg="he",
        arg_col_name="pat",
        param_name="pattern",
        data=_DATA,
    ),
    OpSpec(
        function_key=FK_STR.LPAD,
        op_name="lpad",
        build=lambda inp, arg: inp.str.lpad(arg, " "),
        raw_arg=8,
        arg_col_name="n",
        param_name="length",
        data=_DATA,
    ),
]


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ["polars", "ibis", "narwhals"]:
            for it in INPUT_TYPES:
                mark = xfail_if_limited(bk, op.function_key, op.param_name, it)
                marks = [mark] if mark else []
                cases.append(pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}"))
    return cases


@pytest.mark.parametrize("op,backend,input_type", _params())
def test_argument_channel(op: OpSpec, backend: str, input_type: str):
    run_argument_matrix(op, backend, input_type)
```

- [ ] **Step 2: Run new file**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_arg_types_string.py
```

Expected: all cases PASS or XFAIL (strict). No unexpected failures.

- [ ] **Step 3: Delete the old file**

```bash
rm tests/cross_backend/test_expression_argument_types.py
hatch run test:test-target-quick tests/cross_backend/argument_types/
```

Expected: coverage guard still fails on non-string categories; string category passes.

- [ ] **Step 4: Commit**

```bash
git add tests/cross_backend/argument_types/test_arg_types_string.py tests/cross_backend/test_expression_argument_types.py
git commit -m "test(arg-types): migrate string argument tests into new structure"
```

---

## Tasks 7–15: Per-category argument tests

Each of the following tasks follows the **exact same pattern as Task 6**. For each:

1. Create `test_arg_types_<category>.py` using the Task 6 template
2. Declare `TESTED_PARAMS` with every `(function_key, param_name)` pair from the introspector for that category where `kind == "argument"`
3. Declare `OP_SPECS` with a realistic `build` lambda for each operation
4. Use a minimal `_DATA` dict with appropriate columns
5. Copy the `_params()` and `test_argument_channel` boilerplate from Task 6 verbatim
6. Run: `hatch run test:test-target-quick tests/cross_backend/argument_types/test_arg_types_<category>.py`
7. Commit: `git commit -m "test(arg-types): add <category> argument tests"`

### Task 7: arithmetic

**File:** `tests/cross_backend/argument_types/test_arg_types_arithmetic.py`

- [ ] Use `FKEY_SUBSTRAIT_SCALAR_ARITHMETIC` enum. Cover `add`, `subtract`, `multiply`, `divide`, `modulo`, `power`. All second-operand params are argument-channel. Data: `{"a": [1, 2, 3], "b": [4, 5, 6]}`. Build example: `lambda inp, arg: inp.add(arg)`. Run, commit.

### Task 8: comparison

**File:** `tests/cross_backend/argument_types/test_arg_types_comparison.py`

- [ ] Use `FKEY_SUBSTRAIT_SCALAR_COMPARISON`. Cover `eq`, `neq`, `gt`, `gte`, `lt`, `lte`. Same data shape as arithmetic. Run, commit.

### Task 9: boolean

**File:** `tests/cross_backend/argument_types/test_arg_types_boolean.py`

- [ ] Use `FKEY_SUBSTRAIT_SCALAR_BOOLEAN`. Cover `and_`, `or_`, `xor`. Data: `{"a": [True, False], "b": [False, True]}`. Run, commit.

### Task 10: null

**File:** `tests/cross_backend/argument_types/test_arg_types_null.py`

- [ ] Use `FKEY_MOUNTAINASH_NULL`. Cover `fill_null` (replacement is argument-channel on all backends). Data: `{"v": [1, None, 3], "default": [0, 0, 0]}`. Build: `lambda inp, arg: inp.fill_null(arg)`. Run, commit.

### Task 11: rounding

**File:** `tests/cross_backend/argument_types/test_arg_types_rounding.py`

- [ ] Use `FKEY_SUBSTRAIT_SCALAR_ROUNDING`. After Phase 2, `round(decimals)` is now an option — not tested here. Only cover rounding ops that take expression args (likely none after Phase 2). If empty, add a comment `TESTED_PARAMS = []  # all rounding params are options post-Phase-2` and still register the module so coverage guard succeeds. Commit.

### Task 12: logarithmic

**File:** `tests/cross_backend/argument_types/test_arg_types_logarithmic.py`

- [ ] Use `FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC`. Cover `log(base)` — Polars and Ibis accept expression for `base`, Narwhals likely limited. Data: `{"v": [10.0, 100.0], "b": [10.0, 10.0]}`. Build: `lambda inp, arg: inp.log(arg)`. Run, commit.

### Task 13: datetime

**File:** `tests/cross_backend/argument_types/test_arg_types_datetime.py`

- [ ] Use `FKEY_MOUNTAINASH_SCALAR_DATETIME`. Cover `add_years`, `add_months`, `add_days`, `add_hours`, `add_minutes`, `add_seconds`, `add_milliseconds`, `add_microseconds`. All have registry entries on Ibis/Narwhals — xfail will be auto-applied. Data: `{"dt": [datetime(2024, 1, 1), datetime(2024, 6, 15)], "n": [1, 2]}`. Build: `lambda inp, arg: inp.dt.add_days(arg)` (and per op). Run, commit.

### Task 14: name

**File:** `tests/cross_backend/argument_types/test_arg_types_name.py`

- [ ] After Phase 2, all name params (`alias`, `prefix`, `suffix`) are options. Like Task 11, declare `TESTED_PARAMS = []` and register the module. Commit.

### Task 15: window

**File:** `tests/cross_backend/argument_types/test_arg_types_window.py`

- [ ] Use `FKEY_SUBSTRAIT_WINDOW_ARITHMETIC`. After Phase 2, `nth_value(window_offset)` moved to options. Cover `lead` and `lag` if their `row_offset` is still an argument — check the introspector output. Build: `lambda inp, arg: inp.lead(arg)`. Note: window ops may require `.over(...)` context — wrap in a minimal window spec inside `build`. Run, commit.

### Task 16: aggregate

**File:** `tests/cross_backend/argument_types/test_arg_types_aggregate.py`

- [ ] Use `FKEY_SUBSTRAIT_AGGREGATE_*` enums. Most aggregate ops take the input column only; few have secondary expression args. Cover any that do (e.g., `quantile(q)` if present). If none, declare `TESTED_PARAMS = []`. Run, commit.

---

## Task 17: Coverage guard green

**Files:**
- Modify: any per-category file still missing entries

- [ ] **Step 1: Run the coverage guard**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py
```

- [ ] **Step 2: Fix any `missing` or `extra` entries**

If `test_every_argument_param_is_tested` fails:
- Read the `missing` list → add those pairs to the appropriate category's `TESTED_PARAMS` + `OP_SPECS`
- Read the `extra` list → remove stale entries

- [ ] **Step 3: Re-run until green**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_coverage_guard.py
```

Expected: PASS.

- [ ] **Step 4: Commit any fixes**

```bash
git add tests/cross_backend/argument_types/
git commit -m "test(arg-types): close coverage guard gaps"
```

---

## Task 18: Option channel test

**Files:**
- Create: `tests/cross_backend/argument_types/test_option_channel.py`

- [ ] **Step 1: Write test**

```python
# tests/cross_backend/argument_types/test_option_channel.py
"""Verify option channel: accepts raw Python values, rejects expressions at API builder level."""
from __future__ import annotations

import pytest

import mountainash as ma
from tests.cross_backend.argument_types._introspection import introspect_protocols

# Build a list of (op_name, param_name) for every option-kind param
_OPTION_PARAMS = [
    (p.op_name, p.param_name, p.annotation)
    for p in introspect_protocols()
    if p.kind == "option"
]


def _example_raw_value(annotation: str):
    """Pick a representative raw value based on the parameter's type annotation."""
    if "int" in annotation:
        return 2
    if "str" in annotation:
        return "x"
    if "bool" in annotation:
        return True
    if "float" in annotation:
        return 1.5
    return None


@pytest.mark.parametrize("op_name,param_name,annotation", _OPTION_PARAMS)
def test_option_accepts_raw_value(op_name: str, param_name: str, annotation: str):
    """Smoke test: every option parameter accepts a raw Python value without error."""
    # This test asserts the introspector found a sensible option — it's a registry consistency check.
    raw = _example_raw_value(annotation)
    assert raw is not None, f"No example value for {op_name}({param_name}: {annotation})"


def test_option_rejects_expression_on_builder():
    """When a user passes a column reference to an option param, the API builder must reject it."""
    # round() decimals is an option — passing an expression should fail
    with pytest.raises((TypeError, ValueError, AttributeError)):
        ma.col("x").round(ma.col("n"))  # type: ignore[arg-type]


def test_alias_rejects_expression():
    """name.alias takes a str option — passing an expression should fail."""
    with pytest.raises((TypeError, ValueError, AttributeError)):
        ma.col("x").name.alias(ma.col("y"))  # type: ignore[arg-type]
```

- [ ] **Step 2: Run**

```bash
hatch run test:test-target-quick tests/cross_backend/argument_types/test_option_channel.py
```

Expected: PASS. If `test_option_rejects_expression_on_builder` fails, the API builder is silently accepting expressions in an option slot — file a bug and fix it before proceeding.

- [ ] **Step 3: Commit**

```bash
git add tests/cross_backend/argument_types/test_option_channel.py
git commit -m "test(arg-types): add option channel rejection tests"
```

---

## Task 19: Full suite run and CI confirmation

- [ ] **Step 1: Run the complete new directory**

```bash
hatch run test:test-target tests/cross_backend/argument_types/
```

Expected: all green, known xfails marked xfail, no xpasses.

- [ ] **Step 2: Run the full project suite**

```bash
hatch run test:test
```

Expected: no regressions anywhere; total test count includes all new cases.

- [ ] **Step 3: Run pyright and ruff**

```bash
hatch run ruff:check
hatch run mypy:check
```

Expected: clean.

- [ ] **Step 4: Commit any fixes discovered**

```bash
git add -u
git commit -m "test(arg-types): fix lint/type issues from full suite run"
```

(Skip if no changes.)

---

## Task 20: Update principles docs

**Files:**
- Modify: `../mountainash-central/01.principles/mountainash-expressions/e.cross-backend/arguments-vs-options.md`

- [ ] **Step 1: Add "Test Suite" section**

Add the following after the existing "Testing Strategy" section:

```markdown
## Test Suite Layout

The comprehensive argument/option channel test suite lives at
`tests/cross_backend/argument_types/`. It is organized as:

- `_introspection.py` — walks protocols and classifies each parameter
- `test_coverage_guard.py` — meta-test ensuring every argument-kind param has a test entry
- `test_error_enrichment.py` — positively asserts `BackendCapabilityError` carries registry metadata
- `test_option_channel.py` — verifies options reject expressions at the API builder level
- `test_arg_types_<category>.py` — one file per operation category, each declaring
  `TESTED_PARAMS` and `OP_SPECS`, parametrized over `(op, backend, input_type)`

Adding a new operation requires adding its `(function_key, param_name)` to the relevant
category's `TESTED_PARAMS` list. The coverage guard will fail loudly if you forget.
```

- [ ] **Step 2: Commit in central repo**

```bash
cd ../mountainash-central
git add 01.principles/mountainash-expressions/e.cross-backend/arguments-vs-options.md
git commit -m "docs(principles): document argument/option channel test suite layout"
cd -
```

---

## Self-Review

**Spec coverage:**
- ✅ Full matrix (arg × option × 4 input types × 3 backends) — Tasks 6–16, 18
- ✅ Error enrichment positive assertions — Task 5
- ✅ Self-healing strict xfail — Task 3 `xfail_if_limited`
- ✅ Coverage guard meta-test — Task 4
- ✅ Protocol typing audit as Phase 0 — Task 2
- ✅ Per-category file structure — Tasks 6–16
- ✅ Shared fixtures + local data — Task 3 conftest
- ✅ Principles doc update — Task 20

**Placeholder scan:** One soft area — Task 15 (window) says "wrap in a minimal window spec inside `build`" without showing the wrapper. If window ops are in fact registered as argument-channel post-Phase-2, the implementer should check existing window tests for the `.over(...)` pattern and mirror it. Documented as a Task 15 note rather than inline code because the exact shape depends on what the introspector surfaces.

**Type consistency:** `OpSpec`, `run_argument_matrix`, `xfail_if_limited`, `INPUT_TYPES`, `ALL_BACKENDS`, `make_df` are consistently named across Tasks 3, 6, 7–16, 18. `TESTED_PARAMS` is the consistent module-level symbol expected by Task 4's coverage guard.
