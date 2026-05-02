# Datacontracts Sub-Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `mountainash.datacontracts` as a new sub-module in the mountainash monorepo — unified validation using pandera, mountainash expressions for rules, TypeSpec for schema-driven contract generation.

**Architecture:** Three core concepts — `Rule` (named expression), `Validator` (binds contract + rules + data), `ValidationResultProcessor` (failure analysis). Rules are mountainash expression trees compiled to pandera `@dataframe_check` methods via ephemeral subclasses. TypeSpec optionally generates `BaseDataContract` (pandera `DataFrameModel`) classes.

**Tech Stack:** pandera[polars], polars, mountainash expressions, mountainash TypeSpec, pytest

**Design Spec:** `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-datacontracts/docs/superpowers/specs/2026-05-01-datacontracts-refactoring-design.md`

**Working Directory:** `/home/nathanielramm/git/mountainash-io/mountainash/mountainash`

---

## File Structure

### Source Files (all under `src/mountainash/datacontracts/`)

| File | Responsibility |
|---|---|
| `__init__.py` | Public API re-exports |
| `rule.py` | `Rule` frozen dataclass + `guarded()` combinator |
| `registry.py` | `RuleRegistry` — composable rule collection with version-aware exclusions |
| `contract.py` | `BaseDataContract` — thin `pa.DataFrameModel` subclass with `validate_datacontract()` / `validate_datacontract_quick()` |
| `compiler.py` | `compile_datacontract(TypeSpec)` → generates `BaseDataContract` subclass from TypeSpec |
| `result.py` | `ValidationResult` dataclass |
| `result_processor.py` | `ValidationResultProcessor` — unified failure case analysis |
| `validator.py` | `Validator` — unified validation orchestrator |

### Test Files (all under `tests/datacontracts/`)

| File | Tests |
|---|---|
| `__init__.py` | (empty) |
| `conftest.py` | Shared fixtures (sample DataFrames, TypeSpecs, Rules) |
| `test_rule.py` | Rule creation, guarded combinator, expression composition |
| `test_registry.py` | RuleRegistry composition, exclusions, resolve |
| `test_contract.py` | BaseDataContract validation (valid, invalid, lazy, quick) |
| `test_compiler.py` | TypeSpec → DataContract generation, all constraint mappings |
| `test_result_processor.py` | Failure case processing, metrics, pass/fail |
| `test_validator.py` | End-to-end: Validator with contract + rules + result processor |

---

## Task 1: Add pandera dependency

**Files:**
- Modify: `pyproject.toml`
- Modify: `hatch.toml`

- [ ] **Step 1: Add pandera[polars] as optional dependency**

In `pyproject.toml`, add to `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
pandas = ["pandas>=2.2.0"]
ibis = ["ibis-framework>=9.0.0"]
pyarrow = ["pyarrow>=15.0.0"]
datacontracts = ["pandera[polars]>=0.22.0"]
all = ["mountainash[pandas,ibis,pyarrow,datacontracts]"]
```

- [ ] **Step 2: Add pandera to test environment**

In `hatch.toml`, add `pandera[polars]>=0.22.0` to the test environment dependencies alongside existing optional deps (pandas, ibis, pyarrow).

- [ ] **Step 3: Sync the environment**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch env prune && hatch run test:test --co -q 2>&1 | tail -5`

Expected: environment creates successfully, test collection works.

- [ ] **Step 4: Verify pandera import**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:python -c "import pandera.polars as pa; print('pandera', pa.__version__)"`

Expected: prints pandera version ≥0.22.0.

- [ ] **Step 5: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add pyproject.toml hatch.toml
git commit -m "chore: add pandera[polars] as optional dependency for datacontracts"
```

---

## Task 2: Rule dataclass and guarded combinator

**Files:**
- Create: `src/mountainash/datacontracts/__init__.py` (minimal, just to make it a package)
- Create: `src/mountainash/datacontracts/rule.py`
- Create: `tests/datacontracts/__init__.py`
- Create: `tests/datacontracts/test_rule.py`

- [ ] **Step 1: Create package scaffolding**

Create `src/mountainash/datacontracts/__init__.py`:
```python
"""mountainash.datacontracts — Data contract validation with pandera."""
from __future__ import annotations
```

Create `tests/datacontracts/__init__.py`:
```python
```

- [ ] **Step 2: Write failing tests for Rule**

Create `tests/datacontracts/test_rule.py`:

```python
"""Tests for Rule dataclass and combinators."""
from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma
from mountainash.datacontracts.rule import Rule, guarded


class TestRule:
    """Rule is a frozen dataclass holding an id and an expression."""

    def test_create_simple_rule(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        assert rule.id == "VR01"
        assert rule.expr is not None

    def test_rule_is_frozen(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        with pytest.raises(AttributeError):
            rule.id = "VR02"

    def test_rule_with_metadata(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0), metadata={"severity": "error"})
        assert rule.metadata["severity"] == "error"

    def test_rule_metadata_defaults_empty(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        assert rule.metadata == {}

    def test_rule_expr_compiles_to_polars(self):
        rule = Rule("VR01", expr=ma.col("age").gt(0))
        df = pl.DataFrame({"age": [10, -1, 5]})
        result = df.select(rule.expr.compile(df))
        assert result.to_series().to_list() == [True, False, True]


class TestGuarded:
    """guarded(precondition, test) returns (~precondition) | test."""

    def test_guarded_passes_when_precondition_false(self):
        expr = guarded(
            precondition=ma.col("val").is_not_null(),
            test=ma.col("val").gt(0),
        )
        df = pl.DataFrame({"val": [None, 5, -1]})
        result = df.select(expr.compile(df))
        # row 0: precondition=False → True (skip test)
        # row 1: precondition=True, test=True → True
        # row 2: precondition=True, test=False → False
        assert result.to_series().to_list() == [True, True, False]

    def test_guarded_returns_expression_api(self):
        expr = guarded(
            precondition=ma.col("x").is_not_null(),
            test=ma.col("x").gt(0),
        )
        assert isinstance(expr, ma.BaseExpressionAPI)

    def test_guarded_composes_with_other_expressions(self):
        expr = guarded(
            precondition=ma.col("x").is_not_null(),
            test=ma.col("x").gt(0),
        ) & ma.col("y").eq(1)
        df = pl.DataFrame({"x": [5, -1], "y": [1, 1]})
        result = df.select(expr.compile(df))
        assert result.to_series().to_list() == [True, False]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_rule.py -v 2>&1 | tail -15`

Expected: FAIL — `ModuleNotFoundError: No module named 'mountainash.datacontracts.rule'`

- [ ] **Step 4: Implement Rule and guarded**

Create `src/mountainash/datacontracts/rule.py`:

```python
"""Rule — a named expression for data validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mountainash.expressions import BaseExpressionAPI


@dataclass(frozen=True)
class Rule:
    """A named validation rule backed by a mountainash expression.

    The expression must evaluate to a boolean series where True = pass, False = fail.
    """

    id: str
    expr: BaseExpressionAPI
    metadata: dict[str, Any] = field(default_factory=dict)


def guarded(
    precondition: BaseExpressionAPI,
    test: BaseExpressionAPI,
) -> BaseExpressionAPI:
    """Skip test when precondition is false. Returns (~precondition) | test."""
    return precondition.not_() | test
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_rule.py -v 2>&1 | tail -15`

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add src/mountainash/datacontracts/__init__.py src/mountainash/datacontracts/rule.py tests/datacontracts/__init__.py tests/datacontracts/test_rule.py
git commit -m "feat(datacontracts): add Rule dataclass and guarded combinator"
```

---

## Task 3: RuleRegistry

**Files:**
- Create: `src/mountainash/datacontracts/registry.py`
- Create: `tests/datacontracts/test_registry.py`

- [ ] **Step 1: Write failing tests**

Create `tests/datacontracts/test_registry.py`:

```python
"""Tests for RuleRegistry — composable rule collection with exclusions."""
from __future__ import annotations

import pytest
import mountainash as ma
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.registry import RuleRegistry


@pytest.fixture
def sample_rules() -> list[Rule]:
    return [
        Rule("VR01", expr=ma.col("a").gt(0)),
        Rule("VR02", expr=ma.col("b").gt(0)),
        Rule("VR03", expr=ma.col("c").gt(0)),
    ]


class TestRuleRegistry:

    def test_create_from_list(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        assert len(registry.resolve()) == 3

    def test_resolve_returns_all_rules_without_context(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        resolved = registry.resolve()
        assert [r.id for r in resolved] == ["VR01", "VR02", "VR03"]

    def test_get_rule_by_id(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        assert registry["VR02"].id == "VR02"

    def test_get_rule_by_id_missing_raises(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        with pytest.raises(KeyError):
            registry["VR99"]

    def test_contains(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        assert "VR01" in registry
        assert "VR99" not in registry


class TestRuleRegistryComposition:

    def test_add_registries(self):
        r1 = RuleRegistry([Rule("VR01", expr=ma.col("a").gt(0))])
        r2 = RuleRegistry([Rule("VR02", expr=ma.col("b").gt(0))])
        combined = r1 + r2
        assert len(combined.resolve()) == 2
        assert [r.id for r in combined.resolve()] == ["VR01", "VR02"]

    def test_add_does_not_mutate_originals(self):
        r1 = RuleRegistry([Rule("VR01", expr=ma.col("a").gt(0))])
        r2 = RuleRegistry([Rule("VR02", expr=ma.col("b").gt(0))])
        _ = r1 + r2
        assert len(r1.resolve()) == 1
        assert len(r2.resolve()) == 1

    def test_duplicate_rule_ids_raises(self):
        with pytest.raises(ValueError, match="Duplicate rule"):
            RuleRegistry([
                Rule("VR01", expr=ma.col("a").gt(0)),
                Rule("VR01", expr=ma.col("b").gt(0)),
            ])


class TestRuleRegistryExclusions:

    def test_exclude_rule_for_context(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR02", when={"version": "0102"})
        resolved = registry.resolve(context={"version": "0102"})
        assert [r.id for r in resolved] == ["VR01", "VR03"]

    def test_exclude_does_not_affect_other_contexts(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR02", when={"version": "0102"})
        resolved = registry.resolve(context={"version": "0300"})
        assert [r.id for r in resolved] == ["VR01", "VR02", "VR03"]

    def test_exclude_without_context_returns_all(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR02", when={"version": "0102"})
        resolved = registry.resolve()
        assert len(resolved) == 3

    def test_multiple_exclusions_same_context(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR01", when={"version": "0102"})
        registry.exclude("VR03", when={"version": "0102"})
        resolved = registry.resolve(context={"version": "0102"})
        assert [r.id for r in resolved] == ["VR02"]

    def test_exclude_nonexistent_rule_raises(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        with pytest.raises(KeyError):
            registry.exclude("VR99", when={"version": "0102"})

    def test_multi_key_context_matching(self, sample_rules):
        registry = RuleRegistry(sample_rules)
        registry.exclude("VR01", when={"version": "0102", "region": "AU"})
        # Partial match — rule not excluded
        resolved = registry.resolve(context={"version": "0102"})
        assert len(resolved) == 3
        # Full match — rule excluded
        resolved = registry.resolve(context={"version": "0102", "region": "AU"})
        assert [r.id for r in resolved] == ["VR02", "VR03"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_registry.py -v 2>&1 | tail -10`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement RuleRegistry**

Create `src/mountainash/datacontracts/registry.py`:

```python
"""RuleRegistry — composable rule collection with version-aware exclusions."""
from __future__ import annotations

from typing import Any, Iterable

from mountainash.datacontracts.rule import Rule


class RuleRegistry:
    """A composable collection of Rules with context-aware exclusions."""

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules: dict[str, Rule] = {}
        for rule in rules:
            if rule.id in self._rules:
                raise ValueError(f"Duplicate rule id: {rule.id!r}")
            self._rules[rule.id] = rule
        self._exclusions: list[tuple[str, dict[str, Any]]] = []

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

    def __getitem__(self, rule_id: str) -> Rule:
        return self._rules[rule_id]

    def __add__(self, other: RuleRegistry) -> RuleRegistry:
        combined = RuleRegistry(list(self._rules.values()) + list(other._rules.values()))
        combined._exclusions = list(self._exclusions) + list(other._exclusions)
        return combined

    def exclude(self, rule_id: str, *, when: dict[str, Any]) -> None:
        if rule_id not in self._rules:
            raise KeyError(f"Rule {rule_id!r} not in registry")
        self._exclusions.append((rule_id, when))

    def resolve(self, *, context: dict[str, Any] | None = None) -> list[Rule]:
        if context is None:
            return list(self._rules.values())

        excluded_ids: set[str] = set()
        for rule_id, when in self._exclusions:
            if all(context.get(k) == v for k, v in when.items()):
                excluded_ids.add(rule_id)

        return [r for r in self._rules.values() if r.id not in excluded_ids]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_registry.py -v 2>&1 | tail -15`

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add src/mountainash/datacontracts/registry.py tests/datacontracts/test_registry.py
git commit -m "feat(datacontracts): add RuleRegistry with composition and exclusions"
```

---

## Task 4: BaseDataContract

**Files:**
- Create: `src/mountainash/datacontracts/contract.py`
- Create: `tests/datacontracts/test_contract.py`

- [ ] **Step 1: Write failing tests**

Create `tests/datacontracts/test_contract.py`:

```python
"""Tests for BaseDataContract — pandera DataFrameModel wrapper."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa

from mountainash.datacontracts.contract import BaseDataContract


class SampleContract(BaseDataContract):
    """Test contract: id (int, >=1), name (str), score (float, nullable)."""

    id: int = pa.Field(ge=1)
    name: str
    score: float = pa.Field(nullable=True)


class TestBaseDataContract:

    def test_validate_valid_data(self):
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, None]})
        result = SampleContract.validate_datacontract(df)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 2

    def test_validate_invalid_data_raises(self):
        df = pl.DataFrame({"id": [0, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        with pytest.raises(pa.errors.SchemaErrors) as exc_info:
            SampleContract.validate_datacontract(df)
        fc = exc_info.value.failure_cases
        assert isinstance(fc, pl.DataFrame)
        assert "schema_context" in fc.columns

    def test_validate_quick_fails_on_first(self):
        df = pl.DataFrame({"id": [0, -1], "name": ["a", "b"], "score": [1.0, 2.0]})
        with pytest.raises(pa.errors.SchemaError):
            SampleContract.validate_datacontract_quick(df)

    def test_validate_accepts_pandas_input(self):
        import pandas as pd
        pdf = pd.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        result = SampleContract.validate_datacontract(pdf)
        assert isinstance(result, pl.DataFrame)

    def test_validate_returns_polars_regardless_of_input(self):
        import pandas as pd
        pdf = pd.DataFrame({"id": [1], "name": ["a"], "score": [1.0]})
        result = SampleContract.validate_datacontract(pdf)
        assert isinstance(result, pl.DataFrame)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_contract.py -v 2>&1 | tail -10`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement BaseDataContract**

Create `src/mountainash/datacontracts/contract.py`:

```python
"""BaseDataContract — pandera DataFrameModel with multi-framework input support."""
from __future__ import annotations

from typing import Any, Optional

import polars as pl
import pandera.polars as pa


class BaseDataContract(pa.DataFrameModel):
    """Base class for data contracts.

    Accepts polars or pandas DataFrames as input. All inputs are converted
    to Polars before validation. Always returns polars.DataFrame.
    """

    class Config:
        coerce = True

    @classmethod
    def _to_polars(cls, data: Any) -> pl.DataFrame:
        if isinstance(data, pl.DataFrame):
            return data
        if isinstance(data, pl.LazyFrame):
            return data.collect()
        # pandas
        try:
            import pandas as pd

            if isinstance(data, pd.DataFrame):
                return pl.from_pandas(data)
        except ImportError:
            pass
        raise TypeError(f"Unsupported data type: {type(data)}")

    @classmethod
    def validate_datacontract(
        cls,
        data: Any,
        *,
        head: Optional[int] = None,
        tail: Optional[int] = None,
        sample: Optional[int] = None,
        random_seed: Optional[int] = None,
    ) -> pl.DataFrame:
        """Validate data against this contract (lazy — collects all errors)."""
        df = cls._to_polars(data)
        if head is not None:
            df = df.head(head)
        if tail is not None:
            df = df.tail(tail)
        if sample is not None:
            df = df.sample(n=sample, seed=random_seed)
        return cls.validate(df, lazy=True)

    @classmethod
    def validate_datacontract_quick(
        cls,
        data: Any,
        *,
        head: Optional[int] = None,
        tail: Optional[int] = None,
        sample: Optional[int] = None,
        random_seed: Optional[int] = None,
    ) -> pl.DataFrame:
        """Validate data against this contract (eager — fails on first error)."""
        df = cls._to_polars(data)
        if head is not None:
            df = df.head(head)
        if tail is not None:
            df = df.tail(tail)
        if sample is not None:
            df = df.sample(n=sample, seed=random_seed)
        return cls.validate(df, lazy=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_contract.py -v 2>&1 | tail -15`

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add src/mountainash/datacontracts/contract.py tests/datacontracts/test_contract.py
git commit -m "feat(datacontracts): add BaseDataContract with multi-framework input"
```

---

## Task 5: TypeSpec-to-DataContract compiler

**Files:**
- Create: `src/mountainash/datacontracts/compiler.py`
- Create: `tests/datacontracts/test_compiler.py`

- [ ] **Step 1: Write failing tests**

Create `tests/datacontracts/test_compiler.py`:

```python
"""Tests for compile_datacontract — TypeSpec to pandera DataFrameModel."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa

from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints
from mountainash.typespec.universal_types import UniversalType
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.datacontracts.contract import BaseDataContract


def _make_spec(*fields: FieldSpec) -> TypeSpec:
    return TypeSpec(fields=list(fields))


class TestCompileDatacontract:

    def test_basic_string_field(self):
        spec = _make_spec(FieldSpec(name="name", type=UniversalType.STRING))
        Contract = compile_datacontract(spec)
        assert issubclass(Contract, BaseDataContract)
        df = pl.DataFrame({"name": ["alice", "bob"]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2

    def test_integer_field(self):
        spec = _make_spec(FieldSpec(name="age", type=UniversalType.INTEGER))
        Contract = compile_datacontract(spec)
        df = pl.DataFrame({"age": [25, 30]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2

    def test_custom_name(self):
        spec = _make_spec(FieldSpec(name="x", type=UniversalType.STRING))
        Contract = compile_datacontract(spec, name="MyContract")
        assert Contract.__name__ == "MyContract"

    def test_default_name_from_spec_title(self):
        spec = TypeSpec(
            fields=[FieldSpec(name="x", type=UniversalType.STRING)],
            title="AccountSchema",
        )
        Contract = compile_datacontract(spec)
        assert Contract.__name__ == "AccountSchema"

    def test_nullable_from_required_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="email",
                type=UniversalType.STRING,
                constraints=FieldConstraints(required=True),
            ),
        )
        Contract = compile_datacontract(spec)
        df_with_null = pl.DataFrame({"email": [None, "a@b.com"]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_with_null)

    def test_ge_from_minimum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="age",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(minimum=0),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"age": [-1, 5]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_le_from_maximum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="score",
                type=UniversalType.NUMBER,
                constraints=FieldConstraints(maximum=100.0),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"score": [50.0, 150.0]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_isin_from_enum_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="status",
                type=UniversalType.STRING,
                constraints=FieldConstraints(enum=["active", "inactive"]),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"status": ["active", "deleted"]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_pattern_from_pattern_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="code",
                type=UniversalType.STRING,
                constraints=FieldConstraints(pattern=r"^[A-Z]{3}$"),
            ),
        )
        Contract = compile_datacontract(spec)
        df_good = pl.DataFrame({"code": ["ABC", "XYZ"]})
        result = Contract.validate_datacontract(df_good)
        assert len(result) == 2
        df_bad = pl.DataFrame({"code": ["abc", "XY"]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_unique_constraint(self):
        spec = _make_spec(
            FieldSpec(
                name="id",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(unique=True),
            ),
        )
        Contract = compile_datacontract(spec)
        df_bad = pl.DataFrame({"id": [1, 1, 2]})
        with pytest.raises(pa.errors.SchemaErrors):
            Contract.validate_datacontract(df_bad)

    def test_multiple_fields(self):
        spec = _make_spec(
            FieldSpec(name="id", type=UniversalType.INTEGER, constraints=FieldConstraints(required=True, minimum=1)),
            FieldSpec(name="name", type=UniversalType.STRING),
            FieldSpec(name="score", type=UniversalType.NUMBER),
        )
        Contract = compile_datacontract(spec)
        df = pl.DataFrame({"id": [1, 2], "name": ["a", "b"], "score": [1.0, 2.0]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2

    def test_no_constraints_produces_nullable_field(self):
        spec = _make_spec(FieldSpec(name="val", type=UniversalType.STRING))
        Contract = compile_datacontract(spec)
        df = pl.DataFrame({"val": [None, "x"]})
        result = Contract.validate_datacontract(df)
        assert len(result) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_compiler.py -v 2>&1 | tail -10`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement compile_datacontract**

Create `src/mountainash/datacontracts/compiler.py`:

```python
"""Compile a TypeSpec into a pandera DataFrameModel (BaseDataContract subclass)."""
from __future__ import annotations

from typing import Any

import pandera.polars as pa

from mountainash.typespec.spec import TypeSpec, FieldSpec, FieldConstraints
from mountainash.typespec.universal_types import UniversalType
from mountainash.datacontracts.contract import BaseDataContract

UNIVERSAL_TYPE_TO_PANDERA: dict[UniversalType, type] = {
    UniversalType.STRING: str,
    UniversalType.INTEGER: int,
    UniversalType.NUMBER: float,
    UniversalType.BOOLEAN: bool,
    UniversalType.DATE: str,
    UniversalType.TIME: str,
    UniversalType.DATETIME: str,
    UniversalType.DURATION: str,
    UniversalType.YEAR: int,
    UniversalType.YEARMONTH: str,
    UniversalType.ANY: object,
}


def _constraints_to_field_kwargs(constraints: FieldConstraints | None) -> dict[str, Any]:
    if constraints is None:
        return {"nullable": True}

    kwargs: dict[str, Any] = {}
    kwargs["nullable"] = not constraints.required
    if constraints.unique:
        kwargs["unique"] = True
    if constraints.minimum is not None:
        kwargs["ge"] = constraints.minimum
    if constraints.maximum is not None:
        kwargs["le"] = constraints.maximum
    if constraints.enum is not None:
        kwargs["isin"] = constraints.enum
    if constraints.pattern is not None:
        kwargs["str_matches"] = constraints.pattern
    if constraints.min_length is not None or constraints.max_length is not None:
        length_kwargs: dict[str, int] = {}
        if constraints.min_length is not None:
            length_kwargs["min_value"] = constraints.min_length
        if constraints.max_length is not None:
            length_kwargs["max_value"] = constraints.max_length
        kwargs["str_length"] = length_kwargs
    return kwargs


def compile_datacontract(
    spec: TypeSpec,
    *,
    name: str | None = None,
) -> type[BaseDataContract]:
    """Generate a BaseDataContract subclass from a TypeSpec."""
    contract_name = name or spec.title or "CompiledDataContract"

    annotations: dict[str, type] = {}
    namespace: dict[str, Any] = {"__annotations__": annotations}

    for field_spec in spec.fields:
        python_type = UNIVERSAL_TYPE_TO_PANDERA.get(field_spec.type, object)
        annotations[field_spec.name] = python_type
        field_kwargs = _constraints_to_field_kwargs(field_spec.constraints)
        if field_kwargs:
            namespace[field_spec.name] = pa.Field(**field_kwargs)

    return type(contract_name, (BaseDataContract,), namespace)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_compiler.py -v 2>&1 | tail -20`

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add src/mountainash/datacontracts/compiler.py tests/datacontracts/test_compiler.py
git commit -m "feat(datacontracts): add TypeSpec-to-DataContract compiler"
```

---

## Task 6: ValidationResult and ValidationResultProcessor

**Files:**
- Create: `src/mountainash/datacontracts/result.py`
- Create: `src/mountainash/datacontracts/result_processor.py`
- Create: `tests/datacontracts/test_result_processor.py`

- [ ] **Step 1: Write failing tests**

Create `tests/datacontracts/test_result_processor.py`:

```python
"""Tests for ValidationResult and ValidationResultProcessor."""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor


@pytest.fixture
def sample_failure_cases() -> pl.DataFrame:
    """Failure cases in pandera's format."""
    return pl.DataFrame({
        "failure_case": ["0", "bad_val", "missing"],
        "schema_context": ["Column", "Column", "DataFrameSchema"],
        "column": ["age", "name", "TestContract"],
        "check": ["greater_than_or_equal_to(0)", "str_matches('^[a-z]+$')", "VR01"],
        "check_number": [0, 0, 0],
        "index": [0, 2, 1],
    })


@pytest.fixture
def empty_failure_cases() -> pl.DataFrame:
    return pl.DataFrame({
        "failure_case": [],
        "schema_context": [],
        "column": [],
        "check": [],
        "check_number": [],
        "index": [],
    }).cast({
        "failure_case": pl.Utf8,
        "schema_context": pl.Utf8,
        "column": pl.Utf8,
        "check": pl.Utf8,
        "check_number": pl.Int32,
        "index": pl.Int32,
    })


class TestValidationResult:

    def test_passing_result(self):
        result = ValidationResult(passes=True, validator_name="test")
        assert result.passes is True
        assert result.processor is None

    def test_failing_result_with_processor(self, sample_failure_cases):
        processor = ValidationResultProcessor(sample_failure_cases)
        result = ValidationResult(
            passes=False,
            validator_name="test",
            processor=processor,
        )
        assert result.passes is False
        assert result.processor is not None


class TestValidationResultProcessor:

    def test_failure_count(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.failure_count() == 3

    def test_passed_when_no_failures(self, empty_failure_cases):
        proc = ValidationResultProcessor(empty_failure_cases)
        assert proc.passed() is True

    def test_not_passed_when_failures(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed() is False

    def test_failure_cases_returns_all(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert len(proc.failure_cases()) == 3

    def test_failure_cases_for_column(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        age_failures = proc.failure_cases_for_column("age")
        assert len(age_failures) == 1
        assert age_failures["check"][0] == "greater_than_or_equal_to(0)"

    def test_failure_cases_for_rule(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        rule_failures = proc.failure_cases_for_rule("VR01")
        assert len(rule_failures) == 1

    def test_failure_count_by_column(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        by_col = proc.failure_count_by_column()
        assert isinstance(by_col, pl.DataFrame)
        assert len(by_col) >= 1

    def test_failure_count_by_rule(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        by_rule = proc.failure_count_by_rule()
        assert isinstance(by_rule, pl.DataFrame)
        assert len(by_rule) == 1

    def test_passed_for_column_true(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_column("score") is True

    def test_passed_for_column_false(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_column("age") is False

    def test_passed_for_rule_true(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_rule("VR99") is True

    def test_passed_for_rule_false(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_rule("VR01") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_result_processor.py -v 2>&1 | tail -10`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ValidationResult**

Create `src/mountainash/datacontracts/result.py`:

```python
"""ValidationResult — outcome of a validation run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.datacontracts.result_processor import ValidationResultProcessor


@dataclass
class ValidationResult:
    """Result of a Validator.validate() or Validator.validate_quick() call."""

    passes: bool
    validator_name: str
    datacontract_name: str | None = None
    processor: Optional[ValidationResultProcessor] = None
    message: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 4: Implement ValidationResultProcessor**

Create `src/mountainash/datacontracts/result_processor.py`:

```python
"""ValidationResultProcessor — unified failure case analysis."""
from __future__ import annotations

import polars as pl


class ValidationResultProcessor:
    """Processes pandera failure cases from a validation run."""

    def __init__(self, failure_cases: pl.DataFrame) -> None:
        self._failure_cases = failure_cases

    def failure_cases(self) -> pl.DataFrame:
        return self._failure_cases

    def failure_cases_for_column(self, column: str) -> pl.DataFrame:
        return self._failure_cases.filter(
            (pl.col("schema_context") == "Column") & (pl.col("column") == column)
        )

    def failure_cases_for_rule(self, rule_id: str) -> pl.DataFrame:
        return self._failure_cases.filter(
            (pl.col("schema_context") == "DataFrameSchema") & (pl.col("check") == rule_id)
        )

    def failure_count(self) -> int:
        return len(self._failure_cases)

    def failure_count_by_column(self) -> pl.DataFrame:
        return (
            self._failure_cases.filter(pl.col("schema_context") == "Column")
            .group_by("column")
            .agg(pl.len().alias("count"))
        )

    def failure_count_by_rule(self) -> pl.DataFrame:
        return (
            self._failure_cases.filter(pl.col("schema_context") == "DataFrameSchema")
            .group_by("check")
            .agg(pl.len().alias("count"))
        )

    def passed(self) -> bool:
        return len(self._failure_cases) == 0

    def passed_for_column(self, column: str) -> bool:
        return len(self.failure_cases_for_column(column)) == 0

    def passed_for_rule(self, rule_id: str) -> bool:
        return len(self.failure_cases_for_rule(rule_id)) == 0
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_result_processor.py -v 2>&1 | tail -20`

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add src/mountainash/datacontracts/result.py src/mountainash/datacontracts/result_processor.py tests/datacontracts/test_result_processor.py
git commit -m "feat(datacontracts): add ValidationResult and ValidationResultProcessor"
```

---

## Task 7: Unified Validator

**Files:**
- Create: `src/mountainash/datacontracts/validator.py`
- Create: `tests/datacontracts/test_validator.py`
- Create: `tests/datacontracts/conftest.py`

- [ ] **Step 1: Create shared test fixtures**

Create `tests/datacontracts/conftest.py`:

```python
"""Shared fixtures for datacontracts tests."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa
import mountainash as ma

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.rule import Rule, guarded
from mountainash.datacontracts.registry import RuleRegistry


class PersonContract(BaseDataContract):
    """Hand-built contract for testing."""

    name: str
    age: int = pa.Field(ge=0)
    email: str = pa.Field(nullable=True)


@pytest.fixture
def person_contract():
    return PersonContract


@pytest.fixture
def person_rules() -> RuleRegistry:
    return RuleRegistry([
        Rule("age_under_150", expr=ma.col("age").lt(150)),
        Rule("name_not_empty", expr=guarded(
            precondition=ma.col("name").is_not_null(),
            test=ma.col("name").str.len_chars().gt(0),
        )),
    ])


@pytest.fixture
def valid_person_df() -> pl.DataFrame:
    return pl.DataFrame({
        "name": ["alice", "bob", "charlie"],
        "age": [30, 25, 40],
        "email": ["a@b.com", None, "c@d.com"],
    })


@pytest.fixture
def invalid_person_df() -> pl.DataFrame:
    return pl.DataFrame({
        "name": ["alice", "", "charlie"],
        "age": [30, -1, 200],
        "email": ["a@b.com", None, "c@d.com"],
    })
```

- [ ] **Step 2: Write failing tests for Validator**

Create `tests/datacontracts/test_validator.py`:

```python
"""Tests for Validator — unified validation orchestrator."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa
import mountainash as ma

from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.rule import Rule, guarded
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.result import ValidationResult


class TestValidatorContractOnly:
    """Validator with contract but no rules — column-level validation only."""

    def test_valid_data_passes(self, person_contract, valid_person_df):
        v = Validator(name="person", contract=person_contract)
        result = v.validate(valid_person_df)
        assert isinstance(result, ValidationResult)
        assert result.passes is True

    def test_invalid_data_fails(self, person_contract):
        df = pl.DataFrame({"name": ["a"], "age": [-1], "email": [None]})
        v = Validator(name="person", contract=person_contract)
        result = v.validate(df)
        assert result.passes is False
        assert result.processor is not None
        assert result.processor.failure_count() > 0

    def test_validator_name_in_result(self, person_contract, valid_person_df):
        v = Validator(name="my_validator", contract=person_contract)
        result = v.validate(valid_person_df)
        assert result.validator_name == "my_validator"


class TestValidatorWithRules:
    """Validator with contract + expression-based rules."""

    def test_rules_applied_and_checked(self, person_contract, person_rules):
        df = pl.DataFrame({"name": ["alice"], "age": [200], "email": [None]})
        v = Validator(name="person", contract=person_contract, rules=person_rules)
        result = v.validate(df)
        assert result.passes is False
        assert result.processor.passed_for_rule("age_under_150") is False

    def test_all_rules_pass(self, person_contract, person_rules, valid_person_df):
        v = Validator(name="person", contract=person_contract, rules=person_rules)
        result = v.validate(valid_person_df)
        assert result.passes is True

    def test_contract_not_mutated_by_rules(self, person_contract, person_rules, valid_person_df):
        v = Validator(name="person", contract=person_contract, rules=person_rules)
        v.validate(valid_person_df)
        # The original contract class should have no _check_ methods
        check_methods = [m for m in dir(person_contract) if m.startswith("_check_")]
        assert len(check_methods) == 0


class TestValidatorContextExclusions:
    """Rules excluded by context are not applied."""

    def test_excluded_rule_not_checked(self, person_contract):
        rules = RuleRegistry([
            Rule("strict_age", expr=ma.col("age").lt(50)),
        ])
        rules.exclude("strict_age", when={"mode": "lenient"})
        v = Validator(name="person", contract=person_contract, rules=rules)
        df = pl.DataFrame({"name": ["a"], "age": [100], "email": [None]})

        # Without exclusion context — rule applies, fails
        result = v.validate(df)
        assert result.passes is False

        # With exclusion context — rule excluded, passes
        result = v.validate(df, context={"mode": "lenient"})
        assert result.passes is True


class TestValidatorPrepare:
    """Validator with prepare callable for multi-source data."""

    def test_prepare_called_with_data(self, person_contract):
        called_with = []

        def my_prepare(data):
            called_with.append(data)
            return data["people"]

        v = Validator(name="person", contract=person_contract, prepare=my_prepare)
        data = {"people": pl.DataFrame({"name": ["a"], "age": [30], "email": [None]})}
        result = v.validate(data)
        assert result.passes is True
        assert len(called_with) == 1

    def test_prepare_not_called_when_none(self, person_contract, valid_person_df):
        v = Validator(name="person", contract=person_contract)
        result = v.validate(valid_person_df)
        assert result.passes is True


class TestValidatorQuick:
    """validate_quick fails on first error."""

    def test_quick_validation_passes(self, person_contract, valid_person_df):
        v = Validator(name="person", contract=person_contract)
        result = v.validate_quick(valid_person_df)
        assert result.passes is True

    def test_quick_validation_fails(self, person_contract):
        df = pl.DataFrame({"name": ["a"], "age": [-1], "email": [None]})
        v = Validator(name="person", contract=person_contract)
        result = v.validate_quick(df)
        assert result.passes is False


class TestValidatorPandasInput:
    """Validator accepts pandas DataFrames."""

    def test_pandas_input(self, person_contract):
        import pandas as pd
        pdf = pd.DataFrame({"name": ["a", "b"], "age": [10, 20], "email": ["x", None]})
        v = Validator(name="person", contract=person_contract)
        result = v.validate(pdf)
        assert result.passes is True
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_validator.py -v 2>&1 | tail -10`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement Validator**

Create `src/mountainash/datacontracts/validator.py`:

```python
"""Validator — unified validation orchestrator."""
from __future__ import annotations

from typing import Any, Callable, Optional

import polars as pl
import pandera.polars as pa

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor


def _compile_contract_with_rules(
    contract: type[BaseDataContract],
    rules: list[Rule],
) -> type[BaseDataContract]:
    """Create an ephemeral subclass with compiled rules as @dataframe_check methods."""
    check_methods: dict[str, Any] = {}
    for rule in rules:
        def make_check(r: Rule) -> classmethod:
            def check_fn(cls: Any, data: pa.PolarsData) -> pl.LazyFrame:
                compiled_expr = r.expr.compile(data.lazyframe)
                return data.lazyframe.select(compiled_expr)
            return pa.dataframe_check(name=r.id)(check_fn)
        check_methods[f"_check_{rule.id}"] = make_check(rule)

    return type(
        f"{contract.__name__}_WithRules",
        (contract,),
        check_methods,
    )


class Validator:
    """Unified validation orchestrator binding contract + rules + data."""

    def __init__(
        self,
        *,
        name: str,
        contract: type[BaseDataContract],
        rules: RuleRegistry | None = None,
        natural_key: list[str] | None = None,
        prepare: Callable[[Any], Any] | None = None,
    ) -> None:
        self.name = name
        self.contract = contract
        self.rules = rules
        self.natural_key = natural_key
        self.prepare = prepare

    def _resolve_contract(self, context: dict[str, Any] | None) -> type[BaseDataContract]:
        if self.rules is None:
            return self.contract
        resolved = self.rules.resolve(context=context)
        if not resolved:
            return self.contract
        return _compile_contract_with_rules(self.contract, resolved)

    def _prepare_data(self, data: Any) -> Any:
        if self.prepare is not None:
            return self.prepare(data)
        return data

    def validate(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Full validation — collects all errors."""
        prepared = self._prepare_data(data)
        active_contract = self._resolve_contract(context)

        try:
            active_contract.validate_datacontract(prepared)
            return ValidationResult(
                passes=True,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
            )
        except pa.errors.SchemaErrors as e:
            processor = ValidationResultProcessor(e.failure_cases)
            return ValidationResult(
                passes=False,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
                processor=processor,
                message=str(e),
            )

    def validate_quick(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
        head: int | None = None,
        tail: int | None = None,
        sample: int | None = None,
        random_seed: int | None = None,
    ) -> ValidationResult:
        """Quick validation — fails on first error."""
        prepared = self._prepare_data(data)
        active_contract = self._resolve_contract(context)

        try:
            active_contract.validate_datacontract_quick(
                prepared, head=head, tail=tail, sample=sample, random_seed=random_seed,
            )
            return ValidationResult(
                passes=True,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
            )
        except pa.errors.SchemaError as e:
            fc = getattr(e, "failure_cases", None)
            processor = ValidationResultProcessor(fc) if fc is not None else None
            return ValidationResult(
                passes=False,
                validator_name=self.name,
                datacontract_name=active_contract.__name__,
                processor=processor,
                message=str(e),
            )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/test_validator.py -v 2>&1 | tail -25`

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add src/mountainash/datacontracts/validator.py tests/datacontracts/test_validator.py tests/datacontracts/conftest.py
git commit -m "feat(datacontracts): add unified Validator with ephemeral contract compilation"
```

---

## Task 8: Public API and top-level exports

**Files:**
- Modify: `src/mountainash/datacontracts/__init__.py`
- Modify: `src/mountainash/__init__.py`

- [ ] **Step 1: Write the datacontracts __init__.py**

Update `src/mountainash/datacontracts/__init__.py`:

```python
"""mountainash.datacontracts — Data contract validation with pandera."""
from __future__ import annotations

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.datacontracts.rule import Rule, guarded
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor

__all__ = [
    "BaseDataContract",
    "compile_datacontract",
    "Rule",
    "guarded",
    "RuleRegistry",
    "Validator",
    "ValidationResult",
    "ValidationResultProcessor",
]
```

- [ ] **Step 2: Add datacontracts to mountainash top-level __init__.py**

Add to the end of `src/mountainash/__init__.py` (before the final docstring), using lazy import to avoid hard pandera dependency:

```python
# Datacontracts — validation with pandera (optional, requires pandera[polars])
def datacontract(spec_or_columns: "dict | TypeSpec") -> "BaseDataContract":
    """Create a DataContract from a TypeSpec or simple dict."""
    from mountainash.datacontracts.compiler import compile_datacontract

    if isinstance(spec_or_columns, dict):
        _spec = TypeSpec.from_simple_dict(spec_or_columns)
    else:
        _spec = spec_or_columns
    return compile_datacontract(_spec)
```

- [ ] **Step 3: Verify imports work**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:python -c "from mountainash.datacontracts import Rule, RuleRegistry, Validator, BaseDataContract, compile_datacontract, guarded, ValidationResult, ValidationResultProcessor; print('All imports OK')"`

Expected: `All imports OK`

- [ ] **Step 4: Run the full test suite to check for regressions**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test tests/datacontracts/ -v 2>&1 | tail -30`

Expected: all datacontracts tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add src/mountainash/datacontracts/__init__.py src/mountainash/__init__.py
git commit -m "feat(datacontracts): wire up public API and top-level exports"
```

---

## Task 9: Run full mountainash test suite

This is a regression check — ensure the new sub-module doesn't break existing functionality.

- [ ] **Step 1: Run the complete test suite**

Run: `cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash && hatch run test:test -x -q 2>&1 | tail -20`

Expected: all existing tests PASS alongside new datacontracts tests.

- [ ] **Step 2: If failures, investigate and fix**

Any failures should be import-related (circular imports, pandera version conflicts). Fix without changing the datacontracts public API.

- [ ] **Step 3: Final commit if any fixes were needed**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash
git add -A
git commit -m "fix(datacontracts): resolve integration issues from regression testing"
```
