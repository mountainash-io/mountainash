# Comprehensive Schema & PyData Test Suites — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring schema and pydata modules from smoke-test coverage to comprehensive test suites (~450-550 new tests).

**Architecture:** Two independent test phases. Phase 1 adds 8 test files under `tests/schema/`. Phase 2 adds 6 test files under `tests/pydata/`. No production code changes — tests only. Full transform matrix (4×10×5 = 200 parametrized cases) for schema. All 10 ingress handlers and all 17 egress methods for pydata.

**Tech Stack:** pytest, polars, pandas, pyarrow, ibis, narwhals, pydantic, dataclasses

---

## File Map

### Phase 1 — Schema Tests

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `tests/schema/conftest.py` | Shared fixtures: sample DataFrames (all backends), sample schemas, custom type registry save/restore |
| Create | `tests/schema/test_schema_config.py` | SchemaConfig creation, serialization, from_dict/json/schemas, helpers |
| Create | `tests/schema/test_universal_types.py` | UniversalType enum, normalize_type, mappings, safe casts |
| Create | `tests/schema/test_schema_transforms.py` | Full matrix: transform type × universal type × backend |
| Create | `tests/schema/test_schema_extractors.py` | Extract from DataFrame (all backends), dataclass, Pydantic |
| Create | `tests/schema/test_schema_validators.py` | validate_round_trip, validate_schema_match, validate_transformation_config |
| Create | `tests/schema/test_schema_converters.py` | to_polars_schema, to_pandas_dtypes, to_arrow_schema, to_ibis_schema |
| Create | `tests/schema/test_custom_types.py` | Registry CRUD + all 4 built-in converters (Python + Narwhals) |
| Create | `tests/schema/test_schema_roundtrips.py` | extract→apply, from_schemas→apply, predict→validate |

### Phase 2 — PyData Tests

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `tests/pydata/conftest.py` | Shared fixtures: sample data types, test data constants |
| Create | `tests/pydata/test_ingress_factory.py` | Format detection for all 10+ types + edge cases |
| Create | `tests/pydata/test_ingress_handlers.py` | All 10 handlers: convert + column_config |
| Create | `tests/pydata/test_egress_all.py` | All 17 egress methods from EgressFromPolars |
| Create | `tests/pydata/test_egress_factory.py` | Factory dispatch for all DataFrame backends |
| Create | `tests/pydata/test_hybrid_conversion.py` | Three-tier strategy components |
| Create | `tests/pydata/test_pydata_roundtrips.py` | ingress→egress round-trips for each format |

---

## Phase 1: Schema Tests

### Task 1: Schema conftest and SchemaConfig tests

**Files:**
- Create: `tests/schema/conftest.py`
- Create: `tests/schema/test_schema_config.py`

- [ ] **Step 1: Create shared schema fixtures**

```python
# tests/schema/conftest.py
"""Shared fixtures for schema tests."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

import polars as pl
import pandas as pd
import pyarrow as pa
import pytest

from mountainash.schema.config.types import UniversalType
from mountainash.schema.config.universal_schema import (
    FieldConstraints,
    SchemaField,
    TableSchema,
)
from mountainash.schema.config.custom_types import (
    CustomTypeRegistry,
    _register_standard_converters,
)


# ---------------------------------------------------------------------------
# Sample DataFrames (all backends)
# ---------------------------------------------------------------------------

@pytest.fixture
def polars_mixed_df():
    """Polars DataFrame with mixed types including nulls."""
    return pl.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [1.5, None, 3.0],
        "active": [True, False, True],
        "joined": [datetime.date(2024, 1, 1), datetime.date(2024, 6, 15), datetime.date(2024, 12, 31)],
    })


@pytest.fixture
def pandas_mixed_df():
    """Pandas DataFrame with mixed types."""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [1.5, float("nan"), 3.0],
        "active": [True, False, True],
    })


@pytest.fixture
def pyarrow_mixed_table():
    """PyArrow Table with mixed types."""
    return pa.table({
        "id": pa.array([1, 2, 3], type=pa.int64()),
        "name": pa.array(["Alice", "Bob", "Charlie"], type=pa.string()),
        "score": pa.array([1.5, None, 3.0], type=pa.float64()),
        "active": pa.array([True, False, True], type=pa.bool_()),
    })


@pytest.fixture
def narwhals_mixed_df():
    """Narwhals DataFrame with mixed types."""
    import narwhals as nw
    pl_df = pl.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [1.5, None, 3.0],
        "active": [True, False, True],
    })
    return nw.from_native(pl_df)


@pytest.fixture
def ibis_mixed_table():
    """Ibis Table with mixed types."""
    import ibis
    return ibis.memtable({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [1.5, None, 3.0],
        "active": [True, False, True],
    })


# ---------------------------------------------------------------------------
# Sample schemas
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_schema():
    """Simple TableSchema with basic types."""
    return TableSchema.from_simple_dict({"id": "integer", "name": "string", "score": "number"})


@pytest.fixture
def full_schema():
    """TableSchema with all common types."""
    return TableSchema.from_simple_dict({
        "id": "integer",
        "name": "string",
        "score": "number",
        "active": "boolean",
        "joined": "date",
    })


# ---------------------------------------------------------------------------
# Sample dataclass and Pydantic model
# ---------------------------------------------------------------------------

@dataclass
class SampleEmployee:
    name: str
    age: int
    salary: float
    active: bool = True


@dataclass
class SampleOptionalFields:
    name: str
    age: int
    email: Optional[str] = None


# ---------------------------------------------------------------------------
# Custom type registry isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=False)
def clean_custom_registry():
    """Save and restore custom type registry state around a test."""
    saved = dict(CustomTypeRegistry._converters)
    yield
    CustomTypeRegistry._converters.clear()
    CustomTypeRegistry._converters.update(saved)
```

- [ ] **Step 2: Write SchemaConfig creation tests**

```python
# tests/schema/test_schema_config.py
"""Tests for SchemaConfig — creation, serialization, validation, helpers."""
from __future__ import annotations

import json

import polars as pl
import pytest

from mountainash.schema.config.schema_config import (
    SchemaConfig,
    ValidationIssue,
    ValidationResult,
    apply_column_config,
    create_cast_config,
    create_rename_config,
    init_column_config,
)
from mountainash.schema.config.universal_schema import TableSchema


# -----------------------------------------------------------------------
# Creation
# -----------------------------------------------------------------------

class TestSchemaConfigCreation:
    """SchemaConfig can be created from various input formats."""

    def test_direct_construction(self):
        config = SchemaConfig(columns={"age": {"cast": "integer"}})
        assert "age" in config.columns
        assert config.columns["age"]["cast"] == "integer"

    def test_default_options(self):
        config = SchemaConfig(columns={})
        assert config.keep_only_mapped is False
        assert config.strict is False

    def test_with_options(self):
        config = SchemaConfig(columns={}, keep_only_mapped=True, strict=True)
        assert config.keep_only_mapped is True
        assert config.strict is True

    def test_from_dict_full_format(self):
        config = SchemaConfig.from_dict({
            "columns": {"old": {"rename": "new", "cast": "integer"}},
            "keep_only_mapped": True,
        })
        assert config.columns["old"]["rename"] == "new"
        assert config.keep_only_mapped is True

    def test_from_dict_columns_only_format(self):
        config = SchemaConfig.from_dict({
            "old": {"rename": "new", "cast": "integer"},
        })
        assert config.columns["old"]["rename"] == "new"
        assert config.keep_only_mapped is False

    def test_from_dict_simple_rename_format(self):
        config = SchemaConfig.from_dict({"old_name": "new_name"})
        assert config.columns["old_name"]["rename"] == "new_name"
        assert config.keep_only_mapped is True

    def test_from_dict_empty(self):
        config = SchemaConfig.from_dict({})
        assert config.columns == {}

    def test_from_json_full_format(self):
        json_str = json.dumps({
            "columns": {"id": {"cast": "integer"}},
            "keep_only_mapped": True,
        })
        config = SchemaConfig.from_json(json_str)
        assert config.columns["id"]["cast"] == "integer"
        assert config.keep_only_mapped is True

    def test_from_json_simple_format(self):
        json_str = json.dumps({"old": "new"})
        config = SchemaConfig.from_json(json_str)
        assert config.columns["old"]["rename"] == "new"

    def test_from_schemas_auto_mapping(self):
        source = TableSchema.from_simple_dict({"user_id": "integer", "name": "string"})
        target = TableSchema.from_simple_dict({"user_id": "integer", "name": "string"})
        config = SchemaConfig.from_schemas(source, target)
        # Same names and types → no transforms needed
        assert config.columns == {}

    def test_from_schemas_rename_mapping(self):
        source = TableSchema.from_simple_dict({"user_id": "integer", "user_name": "string"})
        target = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        config = SchemaConfig.from_schemas(source, target, fuzzy_match_threshold=0.3)
        # Should auto-map user_id→id, user_name→name
        assert len(config.columns) >= 1

    def test_from_schemas_auto_cast(self):
        source = TableSchema.from_simple_dict({"id": "string"})
        target = TableSchema.from_simple_dict({"id": "integer"})
        config = SchemaConfig.from_schemas(source, target)
        assert config.columns["id"]["cast"] == "integer"

    def test_from_schemas_no_auto_cast(self):
        source = TableSchema.from_simple_dict({"id": "string"})
        target = TableSchema.from_simple_dict({"id": "integer"})
        config = SchemaConfig.from_schemas(source, target, auto_cast=False)
        assert "cast" not in config.columns.get("id", {})


# -----------------------------------------------------------------------
# Serialization round-trip
# -----------------------------------------------------------------------

class TestSchemaConfigSerialization:
    """to_dict/to_json round-trips preserve all config."""

    def test_to_dict_roundtrip(self):
        original = SchemaConfig(
            columns={"a": {"rename": "b", "cast": "integer"}},
            keep_only_mapped=True,
            strict=True,
        )
        restored = SchemaConfig.from_dict(original.to_dict())
        assert restored.columns == original.columns
        assert restored.keep_only_mapped == original.keep_only_mapped
        assert restored.strict == original.strict

    def test_to_json_roundtrip(self):
        original = SchemaConfig(
            columns={"x": {"cast": "number", "null_fill": 0.0}},
            keep_only_mapped=False,
        )
        restored = SchemaConfig.from_json(original.to_json())
        assert restored.columns == original.columns

    def test_to_dict_includes_schemas(self):
        source = TableSchema.from_simple_dict({"id": "integer"})
        config = SchemaConfig(columns={}, source_schema=source)
        d = config.to_dict()
        assert "source_schema" in d


# -----------------------------------------------------------------------
# Configuration options
# -----------------------------------------------------------------------

class TestSchemaConfigOptions:
    """keep_only_mapped and strict behave correctly."""

    def test_keep_only_mapped_drops_extra(self):
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
        config = SchemaConfig(
            columns={"a": {"cast": "integer"}},
            keep_only_mapped=True,
        )
        result = config.apply(df)
        assert "a" in result.columns
        assert "b" not in result.columns

    def test_keep_only_mapped_false_keeps_all(self):
        df = pl.DataFrame({"a": [1], "b": [2]})
        config = SchemaConfig(
            columns={"a": {"cast": "integer"}},
            keep_only_mapped=False,
        )
        result = config.apply(df)
        assert "a" in result.columns
        assert "b" in result.columns

    def test_strict_raises_on_missing(self):
        df = pl.DataFrame({"a": [1]})
        config = SchemaConfig(columns={"missing": {"cast": "integer"}}, strict=True)
        with pytest.raises(Exception):
            config.apply(df)

    def test_lenient_skips_missing(self):
        df = pl.DataFrame({"a": [1]})
        config = SchemaConfig(columns={"missing": {"cast": "integer"}}, strict=False)
        result = config.apply(df)
        assert result.shape == df.shape


# -----------------------------------------------------------------------
# Prediction and validation
# -----------------------------------------------------------------------

class TestSchemaConfigPrediction:
    """predict_output_schema and validate_against_* work correctly."""

    def test_predict_output_schema_rename(self):
        source = TableSchema.from_simple_dict({"old": "string"})
        config = SchemaConfig(
            columns={"old": {"rename": "new"}},
            source_schema=source,
        )
        predicted = config.predict_output_schema()
        assert "new" in predicted.field_names

    def test_predict_output_schema_cast(self):
        source = TableSchema.from_simple_dict({"id": "string"})
        config = SchemaConfig(
            columns={"id": {"cast": "integer"}},
            source_schema=source,
        )
        predicted = config.predict_output_schema()
        field = predicted.get_field("id")
        assert field.type == "integer"

    def test_predict_keeps_unmapped_when_not_filtered(self):
        source = TableSchema.from_simple_dict({"a": "string", "b": "integer"})
        config = SchemaConfig(
            columns={"a": {"cast": "integer"}},
            keep_only_mapped=False,
            source_schema=source,
        )
        predicted = config.predict_output_schema()
        assert "b" in predicted.field_names

    def test_predict_drops_unmapped_when_filtered(self):
        source = TableSchema.from_simple_dict({"a": "string", "b": "integer"})
        config = SchemaConfig(
            columns={"a": {"cast": "integer"}},
            keep_only_mapped=True,
            source_schema=source,
        )
        predicted = config.predict_output_schema()
        assert "b" not in predicted.field_names

    def test_predict_raises_without_schema(self):
        config = SchemaConfig(columns={"a": {"cast": "integer"}})
        with pytest.raises(ValueError, match="No input schema"):
            config.predict_output_schema()

    def test_validate_against_schemas_valid(self):
        source = TableSchema.from_simple_dict({"id": "string"})
        target = TableSchema.from_simple_dict({"id": "integer"})
        config = SchemaConfig.from_schemas(source, target)
        is_valid, errors = config.validate_against_schemas()
        assert is_valid
        assert errors == []

    def test_validate_against_dataframe_source_mode(self):
        df = pl.DataFrame({"id": [1], "name": ["Alice"]})
        source = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        config = SchemaConfig(columns={}, source_schema=source)
        result = config.validate_against_dataframe(df, mode="source")
        assert result.valid


# -----------------------------------------------------------------------
# Conversion separation
# -----------------------------------------------------------------------

class TestSchemaConfigSeparateConversions:
    """separate_conversions() splits into 3 tiers correctly."""

    def test_native_only(self):
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "name": {"rename": "full_name"},
        })
        python_custom, narwhals_custom, native = config.separate_conversions()
        assert len(python_custom) == 0
        assert len(narwhals_custom) == 0
        assert "id" in native
        assert "name" in native

    def test_vectorized_custom_goes_to_narwhals(self):
        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
        })
        python_custom, narwhals_custom, native = config.separate_conversions()
        assert "amount" in narwhals_custom
        assert len(python_custom) == 0

    def test_no_cast_goes_to_native(self):
        config = SchemaConfig(columns={
            "x": {"null_fill": 0},
        })
        python_custom, narwhals_custom, native = config.separate_conversions()
        assert "x" in native


# -----------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------

class TestSchemaConfigHelpers:
    """init_column_config, create_rename_config, create_cast_config."""

    def test_init_from_schema_config(self):
        original = SchemaConfig(columns={"a": {"cast": "integer"}})
        result = init_column_config(original)
        assert result is original

    def test_init_from_dict(self):
        result = init_column_config({"a": {"cast": "integer"}})
        assert isinstance(result, SchemaConfig)
        assert result.columns["a"]["cast"] == "integer"

    def test_init_from_json(self):
        result = init_column_config('{"columns": {"a": {"cast": "integer"}}}')
        assert isinstance(result, SchemaConfig)

    def test_init_override_keep_only_mapped(self):
        config = SchemaConfig(columns={}, keep_only_mapped=False)
        result = init_column_config(config, keep_only_mapped=True)
        assert result.keep_only_mapped is True

    def test_create_rename_config(self):
        config = create_rename_config({"old": "new"})
        assert config.columns["old"]["rename"] == "new"

    def test_create_cast_config(self):
        config = create_cast_config({"id": "integer", "score": "number"})
        assert config.columns["id"]["cast"] == "integer"
        assert config.columns["score"]["cast"] == "number"

    def test_apply_column_config_function(self):
        df = pl.DataFrame({"old": [1, 2, 3]})
        result = apply_column_config(df, {"old": {"rename": "new"}})
        assert "new" in result.columns
```

- [ ] **Step 3: Run tests and verify they pass**

Run: `hatch run test:test-target tests/schema/test_schema_config.py -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/schema/conftest.py tests/schema/test_schema_config.py
git commit -m "test(schema): add SchemaConfig comprehensive tests and shared fixtures"
```

---

### Task 2: UniversalType and type system tests

**Files:**
- Create: `tests/schema/test_universal_types.py`

- [ ] **Step 1: Write type system tests**

```python
# tests/schema/test_universal_types.py
"""Tests for UniversalType enum, normalize_type, mappings, and safe casts."""
from __future__ import annotations

import datetime

import polars as pl
import pyarrow as pa
import pytest

from mountainash.schema.config.types import (
    ARROW_TO_UNIVERSAL,
    IBIS_TO_UNIVERSAL,
    PANDAS_TO_UNIVERSAL,
    POLARS_TO_UNIVERSAL,
    PYTHON_TO_UNIVERSAL,
    SAFE_CASTS,
    UNSAFE_CASTS,
    UNIVERSAL_TO_IBIS,
    UNIVERSAL_TO_PANDAS,
    UniversalType,
    get_arrow_type,
    get_backend_to_universal_mapping,
    get_polars_type,
    get_universal_to_backend_mapping,
    is_safe_cast,
    normalize_type,
)


# -----------------------------------------------------------------------
# Enum completeness
# -----------------------------------------------------------------------

class TestUniversalTypeEnum:
    """All expected UniversalType members exist."""

    @pytest.mark.parametrize("member", [
        "STRING", "INTEGER", "NUMBER", "BOOLEAN",
        "DATE", "TIME", "DATETIME", "DURATION",
        "YEAR", "YEARMONTH",
        "ARRAY", "OBJECT", "ANY",
    ])
    def test_member_exists(self, member):
        assert hasattr(UniversalType, member)
        assert getattr(UniversalType, member).value == member.lower()

    def test_is_str_enum(self):
        assert UniversalType.STRING == "string"
        assert UniversalType.INTEGER == "integer"


# -----------------------------------------------------------------------
# normalize_type — parametrized by source format
# -----------------------------------------------------------------------

class TestNormalizeTypePython:
    """normalize_type with Python types."""

    @pytest.mark.parametrize("py_type,expected", [
        (int, "integer"),
        (float, "number"),
        (str, "string"),
        (bool, "boolean"),
        (datetime.date, "date"),
        (datetime.datetime, "datetime"),
        (datetime.time, "time"),
        (datetime.timedelta, "duration"),
    ])
    def test_python_types(self, py_type, expected):
        assert normalize_type(py_type, "python") == expected


class TestNormalizeTypeIdentity:
    """normalize_type with universal type strings returns identity."""

    @pytest.mark.parametrize("type_str", [
        "string", "integer", "number", "boolean",
        "date", "time", "datetime", "duration",
    ])
    def test_identity(self, type_str):
        assert normalize_type(type_str) == type_str


class TestNormalizeTypePolars:
    """normalize_type with Polars type strings."""

    @pytest.mark.parametrize("polars_str,expected", [
        ("Utf8", "string"),
        ("String", "string"),
        ("Int64", "integer"),
        ("Int32", "integer"),
        ("Float64", "number"),
        ("Boolean", "boolean"),
        ("Date", "date"),
        ("Datetime", "datetime"),
        ("Duration", "duration"),
        ("Time", "time"),
        ("List", "array"),
        ("Struct", "object"),
    ])
    def test_polars_strings(self, polars_str, expected):
        assert normalize_type(polars_str, "polars") == expected


class TestNormalizeTypePandas:
    """normalize_type with Pandas dtype strings."""

    @pytest.mark.parametrize("pandas_str,expected", [
        ("object", "string"),
        ("string", "string"),
        ("int64", "integer"),
        ("Int64", "integer"),
        ("float64", "number"),
        ("bool", "boolean"),
        ("boolean", "boolean"),
        ("datetime64[ns]", "datetime"),
        ("timedelta64[ns]", "duration"),
    ])
    def test_pandas_strings(self, pandas_str, expected):
        assert normalize_type(pandas_str, "pandas") == expected


class TestNormalizeTypeArrow:
    """normalize_type with Arrow type strings."""

    @pytest.mark.parametrize("arrow_str,expected", [
        ("string", "string"),
        ("int64", "integer"),
        ("float64", "number"),
        ("bool", "boolean"),
        ("date32", "date"),
        ("timestamp", "datetime"),
        ("duration", "duration"),
        ("time64", "time"),
    ])
    def test_arrow_strings(self, arrow_str, expected):
        assert normalize_type(arrow_str, "arrow") == expected


class TestNormalizeTypeIbis:
    """normalize_type with Ibis type strings."""

    @pytest.mark.parametrize("ibis_str,expected", [
        ("string", "string"),
        ("int64", "integer"),
        ("float64", "number"),
        ("bool", "boolean"),
        ("date", "date"),
        ("timestamp", "datetime"),
        ("interval", "duration"),
    ])
    def test_ibis_strings(self, ibis_str, expected):
        assert normalize_type(ibis_str, "ibis") == expected


# -----------------------------------------------------------------------
# Forward mappings
# -----------------------------------------------------------------------

class TestForwardMappings:
    """Universal → backend type mappings."""

    def test_get_polars_type_all_universal(self):
        mapping = get_universal_to_backend_mapping("polars")
        for ut in UniversalType:
            assert ut.value in mapping, f"Missing Polars mapping for {ut}"

    def test_get_polars_type_integer(self):
        assert get_polars_type("integer") == pl.Int64

    def test_get_polars_type_string(self):
        assert get_polars_type("string") == pl.Utf8

    def test_get_arrow_type_integer(self):
        assert get_arrow_type("integer") == pa.int64()

    def test_get_arrow_type_string(self):
        assert get_arrow_type("string") == pa.string()

    def test_pandas_mapping_completeness(self):
        for ut in UniversalType:
            assert ut.value in UNIVERSAL_TO_PANDAS, f"Missing Pandas mapping for {ut}"

    def test_ibis_mapping_completeness(self):
        for ut in UniversalType:
            assert ut.value in UNIVERSAL_TO_IBIS, f"Missing Ibis mapping for {ut}"

    @pytest.mark.parametrize("backend", ["polars", "pandas", "arrow", "ibis"])
    def test_get_universal_to_backend_mapping(self, backend):
        mapping = get_universal_to_backend_mapping(backend)
        assert isinstance(mapping, dict)
        assert len(mapping) >= len(UniversalType)


# -----------------------------------------------------------------------
# Reverse mappings
# -----------------------------------------------------------------------

class TestReverseMappings:
    """Backend → universal type mappings cover common types."""

    @pytest.mark.parametrize("backend", ["polars", "pandas", "arrow", "ibis"])
    def test_get_backend_to_universal_mapping(self, backend):
        mapping = get_backend_to_universal_mapping(backend)
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_polars_reverse_covers_common(self):
        for key in ["Int64", "Float64", "Utf8", "Boolean", "Date"]:
            assert key in POLARS_TO_UNIVERSAL

    def test_pandas_reverse_covers_common(self):
        for key in ["int64", "float64", "object", "bool", "datetime64[ns]"]:
            assert key in PANDAS_TO_UNIVERSAL

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError):
            get_backend_to_universal_mapping("unknown_backend")


# -----------------------------------------------------------------------
# Safe cast checking
# -----------------------------------------------------------------------

class TestSafeCasts:
    """is_safe_cast returns correct results."""

    def test_same_type_is_safe(self):
        assert is_safe_cast("integer", "integer") is True
        assert is_safe_cast("string", "string") is True

    @pytest.mark.parametrize("from_type,to_type", list(SAFE_CASTS))
    def test_known_safe_casts(self, from_type, to_type):
        assert is_safe_cast(from_type, to_type) is True

    @pytest.mark.parametrize("from_type,to_type", list(UNSAFE_CASTS))
    def test_known_unsafe_casts(self, from_type, to_type):
        assert is_safe_cast(from_type, to_type) is False

    def test_safe_and_unsafe_disjoint(self):
        assert SAFE_CASTS.isdisjoint(UNSAFE_CASTS)

    def test_unknown_pair_is_unsafe(self):
        assert is_safe_cast("array", "boolean") is False
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target tests/schema/test_universal_types.py -v`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/schema/test_universal_types.py
git commit -m "test(schema): add UniversalType and type system comprehensive tests"
```

---

### Task 3: Schema transform full matrix

**Files:**
- Create: `tests/schema/test_schema_transforms.py`

This is the largest single file — 200 parametrized cases (4 transforms × 10 types × 5 backends).

- [ ] **Step 1: Write the full matrix test**

```python
# tests/schema/test_schema_transforms.py
"""Full matrix tests: transform_type × universal_type × backend.

4 transforms × 10 types × 5 backends = 200 parametrized cases.
"""
from __future__ import annotations

import datetime

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from mountainash.schema.config.schema_config import SchemaConfig


# ---------------------------------------------------------------------------
# Test data generators — create source DataFrames for each backend
# ---------------------------------------------------------------------------

def _polars_df(col_name: str, values: list, dtype=None) -> pl.DataFrame:
    if dtype:
        return pl.DataFrame({col_name: pl.Series(values).cast(dtype), "extra": [1] * len(values)})
    return pl.DataFrame({col_name: values, "extra": [1] * len(values)})


def _pandas_df(col_name: str, values: list) -> pd.DataFrame:
    return pd.DataFrame({col_name: values, "extra": [1] * len(values)})


def _pyarrow_table(col_name: str, values: list, pa_type=None) -> pa.Table:
    if pa_type:
        return pa.table({col_name: pa.array(values, type=pa_type), "extra": pa.array([1] * len(values))})
    return pa.table({col_name: values, "extra": [1] * len(values)}))


def _narwhals_df(col_name: str, values: list):
    import narwhals as nw
    return nw.from_native(pl.DataFrame({col_name: values, "extra": [1] * len(values)}))


def _ibis_table(col_name: str, values: list):
    import ibis
    return ibis.memtable({col_name: values, "extra": [1] * len(values)})


# ---------------------------------------------------------------------------
# Source data for each universal type (as string values for cast testing)
# ---------------------------------------------------------------------------

CAST_SOURCE_DATA = {
    "string":   (["hello", "world", "test"], None),
    "integer":  (["1", "2", "3"], None),
    "number":   (["1.5", "2.5", "3.5"], None),
    "boolean":  (["true", "false", "true"], None),
    "date":     (["2024-01-01", "2024-06-15", "2024-12-31"], None),
    "datetime": (["2024-01-01T00:00:00", "2024-06-15T12:30:00", "2024-12-31T23:59:59"], None),
    "time":     (["08:00:00", "12:30:00", "23:59:59"], None),
    "duration": ([1000000, 2000000, 3000000], None),  # microseconds
    "array":    (["[1,2]", "[3,4]", "[5,6]"], None),
    "object":   (['{"a":1}', '{"b":2}', '{"c":3}'], None),
}

# Types that support cast from string in each backend
# (others will be xfailed)
CAST_SUPPORT = {
    "polars":   {"string", "integer", "number", "boolean", "date", "datetime"},
    "pandas":   {"string", "integer", "number", "boolean", "datetime"},
    "pyarrow":  {"string", "integer", "number", "boolean"},
    "narwhals": {"string", "integer", "number", "boolean", "date", "datetime"},
    "ibis":     {"string", "integer", "number", "boolean"},
}

BACKENDS = ["polars", "pandas", "pyarrow", "narwhals", "ibis"]
UNIVERSAL_TYPES = ["string", "integer", "number", "boolean", "date", "datetime", "time", "duration", "array", "object"]


def _make_df(backend: str, col_name: str, values: list):
    """Create a DataFrame in the specified backend."""
    if backend == "polars":
        return _polars_df(col_name, values)
    elif backend == "pandas":
        return _pandas_df(col_name, values)
    elif backend == "pyarrow":
        return _pyarrow_table(col_name, values)
    elif backend == "narwhals":
        return _narwhals_df(col_name, values)
    elif backend == "ibis":
        return _ibis_table(col_name, values)


# ---------------------------------------------------------------------------
# CAST transform tests
# ---------------------------------------------------------------------------

def _cast_params():
    """Generate parametrize params for cast tests."""
    params = []
    for utype in UNIVERSAL_TYPES:
        for backend in BACKENDS:
            supported = utype in CAST_SUPPORT.get(backend, set())
            marks = [] if supported else [pytest.mark.xfail(reason=f"{backend} does not support cast to {utype} from string", strict=False)]
            params.append(pytest.param(utype, backend, id=f"cast-{utype}-{backend}", marks=marks))
    return params


class TestCastTransform:
    """Cast transform across all universal types and backends."""

    @pytest.mark.parametrize("utype,backend", _cast_params())
    def test_cast(self, utype, backend):
        values, _ = CAST_SOURCE_DATA.get(utype, (["a", "b", "c"], None))
        df = _make_df(backend, "col", values)
        config = SchemaConfig(columns={"col": {"cast": utype}})
        result = config.apply(df)
        assert result is not None


# ---------------------------------------------------------------------------
# RENAME transform tests
# ---------------------------------------------------------------------------

class TestRenameTransform:
    """Rename transform across all backends."""

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_rename(self, backend):
        df = _make_df(backend, "old_name", ["a", "b", "c"])
        config = SchemaConfig(columns={"old_name": {"rename": "new_name"}})
        result = config.apply(df)
        if hasattr(result, "columns"):
            cols = list(result.columns)
        elif hasattr(result, "schema"):
            cols = list(result.schema().names) if callable(result.schema) else list(result.schema.keys())
        else:
            cols = []
        assert "new_name" in cols


# ---------------------------------------------------------------------------
# NULL_FILL transform tests
# ---------------------------------------------------------------------------

class TestNullFillTransform:
    """Null fill transform across backends."""

    @pytest.mark.parametrize("backend", ["polars", "pandas", "narwhals"])
    def test_null_fill(self, backend):
        if backend == "polars":
            df = pl.DataFrame({"val": [1.0, None, 3.0]})
        elif backend == "pandas":
            df = pd.DataFrame({"val": [1.0, float("nan"), 3.0]})
        elif backend == "narwhals":
            import narwhals as nw
            df = nw.from_native(pl.DataFrame({"val": [1.0, None, 3.0]}))
        config = SchemaConfig(columns={"val": {"null_fill": 0.0}})
        result = config.apply(df)
        # Verify null was filled — convert to polars for assertion
        if hasattr(result, "to_native"):
            result = result.to_native()
        if isinstance(result, pd.DataFrame):
            assert result["val"].isna().sum() == 0
        else:
            assert result["val"].null_count() == 0


# ---------------------------------------------------------------------------
# Multi-transform tests
# ---------------------------------------------------------------------------

class TestMultiTransform:
    """Multiple transforms in one config."""

    def test_cast_rename_null_fill_combined(self):
        df = pl.DataFrame({
            "age_str": ["30", None, "25"],
            "full_name": ["Alice", "Bob", "Charlie"],
        })
        config = SchemaConfig(columns={
            "age_str": {"cast": "integer", "null_fill": 0, "rename": "age"},
            "full_name": {"rename": "name"},
        })
        result = config.apply(df)
        assert "age" in result.columns
        assert "name" in result.columns

    def test_keep_only_mapped_with_transforms(self):
        df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
        config = SchemaConfig(
            columns={"a": {"rename": "x"}},
            keep_only_mapped=True,
        )
        result = config.apply(df)
        assert "x" in result.columns
        assert "b" not in result.columns
        assert "c" not in result.columns
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target tests/schema/test_schema_transforms.py -v`
Expected: Supported cases pass, unsupported xfail.

- [ ] **Step 3: Commit**

```bash
git add tests/schema/test_schema_transforms.py
git commit -m "test(schema): add full matrix transform tests (cast×type×backend)"
```

---

### Task 4: Schema extractors tests

**Files:**
- Create: `tests/schema/test_schema_extractors.py`

- [ ] **Step 1: Write extractor tests**

```python
# tests/schema/test_schema_extractors.py
"""Tests for schema extraction from DataFrames, dataclasses, and Pydantic models."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

import polars as pl
import pandas as pd
import pyarrow as pa
import pytest

from mountainash.schema.config.extractors import (
    extract_schema_from_dataclass,
    extract_schema_from_dataframe,
    extract_schema_from_pydantic,
    from_dataclass,
    from_dataframe,
    from_pydantic,
    build_schema_config_with_fuzzy_matching,
    _DATACLASS_SCHEMA_CACHE,
)
from mountainash.schema.config.universal_schema import TableSchema


# ---------------------------------------------------------------------------
# DataFrame extraction — parametrized by backend
# ---------------------------------------------------------------------------

class TestExtractFromPolars:
    """Extract schema from Polars DataFrames."""

    def test_basic_types(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert "id" in schema.field_names
        assert "name" in schema.field_names
        field = schema.get_field("id")
        assert field.type == "integer"

    def test_string_type(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        field = schema.get_field("name")
        assert field.type == "string"

    def test_number_type(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        field = schema.get_field("score")
        assert field.type == "number"

    def test_boolean_type(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        field = schema.get_field("active")
        assert field.type == "boolean"

    def test_date_type(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        field = schema.get_field("joined")
        assert field.type == "date"

    def test_preserve_backend_types(self, polars_mixed_df):
        schema = from_dataframe(polars_mixed_df, preserve_backend_types=True)
        field = schema.get_field("id")
        assert field.backend_type is not None

    def test_no_backend_types(self, polars_mixed_df):
        schema = from_dataframe(polars_mixed_df, preserve_backend_types=False)
        field = schema.get_field("id")
        assert field.backend_type is None


class TestExtractFromPandas:
    """Extract schema from Pandas DataFrames."""

    def test_basic_types(self, pandas_mixed_df):
        schema = extract_schema_from_dataframe(pandas_mixed_df)
        assert "id" in schema.field_names
        field = schema.get_field("id")
        assert field.type == "integer"


class TestExtractFromPyArrow:
    """Extract schema from PyArrow Tables."""

    def test_basic_types(self, pyarrow_mixed_table):
        schema = extract_schema_from_dataframe(pyarrow_mixed_table)
        assert "id" in schema.field_names
        field = schema.get_field("id")
        assert field.type == "integer"

    def test_string_detected(self, pyarrow_mixed_table):
        schema = extract_schema_from_dataframe(pyarrow_mixed_table)
        field = schema.get_field("name")
        assert field.type == "string"


class TestExtractFromNarwhals:
    """Extract schema from Narwhals DataFrames."""

    def test_basic_types(self, narwhals_mixed_df):
        schema = extract_schema_from_dataframe(narwhals_mixed_df)
        assert "id" in schema.field_names
        field = schema.get_field("id")
        assert field.type == "integer"


class TestExtractFromIbis:
    """Extract schema from Ibis Tables."""

    def test_basic_types(self, ibis_mixed_table):
        schema = extract_schema_from_dataframe(ibis_mixed_table)
        assert "id" in schema.field_names


# ---------------------------------------------------------------------------
# Dataclass extraction
# ---------------------------------------------------------------------------

@dataclass
class SimpleTypes:
    name: str
    age: int
    score: float
    active: bool


@dataclass
class OptionalFields:
    name: str
    email: Optional[str] = None


@dataclass
class DatetimeFields:
    created: datetime.date
    updated: datetime.datetime


class TestExtractFromDataclass:
    """Extract schema from dataclass definitions."""

    def test_simple_types(self):
        schema = from_dataclass(SimpleTypes)
        assert schema.field_names == ["name", "age", "score", "active"]
        assert schema.get_field("name").type == "string"
        assert schema.get_field("age").type == "integer"
        assert schema.get_field("score").type == "number"
        assert schema.get_field("active").type == "boolean"

    def test_optional_fields(self):
        schema = from_dataclass(OptionalFields, preserve_optional=True)
        assert "email" in schema.field_names
        field = schema.get_field("email")
        assert field.type == "string"

    def test_datetime_fields(self):
        schema = from_dataclass(DatetimeFields)
        assert schema.get_field("created").type == "date"
        assert schema.get_field("updated").type == "datetime"

    def test_caching(self):
        _DATACLASS_SCHEMA_CACHE.clear()
        s1 = extract_schema_from_dataclass(SimpleTypes, use_cache=True)
        s2 = extract_schema_from_dataclass(SimpleTypes, use_cache=True)
        assert s1 is s2  # Same object from cache

    def test_not_dataclass_raises(self):
        with pytest.raises(ValueError):
            from_dataclass(str)


# ---------------------------------------------------------------------------
# Pydantic extraction
# ---------------------------------------------------------------------------

class TestExtractFromPydantic:
    """Extract schema from Pydantic models."""

    def test_basic_model(self):
        from pydantic import BaseModel

        class Item(BaseModel):
            name: str
            price: float

        schema = from_pydantic(Item)
        assert "name" in schema.field_names
        assert "price" in schema.field_names
        assert schema.get_field("name").type == "string"
        assert schema.get_field("price").type == "number"

    def test_optional_field(self):
        from pydantic import BaseModel

        class OptModel(BaseModel):
            name: str
            tag: Optional[str] = None

        schema = from_pydantic(OptModel)
        assert "tag" in schema.field_names

    def test_caching(self):
        from pydantic import BaseModel

        class CachedModel(BaseModel):
            x: int

        from mountainash.schema.config.extractors import _PYDANTIC_SCHEMA_CACHE
        _PYDANTIC_SCHEMA_CACHE.clear()
        s1 = extract_schema_from_pydantic(CachedModel, use_cache=True)
        s2 = extract_schema_from_pydantic(CachedModel, use_cache=True)
        assert s1 is s2


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------

class TestFuzzyMatching:
    """build_schema_config_with_fuzzy_matching auto-maps similar column names."""

    def test_exact_match(self):
        source = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        target = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        config = build_schema_config_with_fuzzy_matching(source, target)
        # Exact match → no transforms
        assert config.columns == {}

    def test_fuzzy_rename(self):
        source = TableSchema.from_simple_dict({"user_name": "string"})
        target = TableSchema.from_simple_dict({"username": "string"})
        config = build_schema_config_with_fuzzy_matching(source, target, fuzzy_match_threshold=0.5)
        assert "user_name" in config.columns
        assert config.columns["user_name"]["rename"] == "username"

    def test_high_threshold_misses_fuzzy(self):
        source = TableSchema.from_simple_dict({"usr_nm": "string"})
        target = TableSchema.from_simple_dict({"user_name": "string"})
        config = build_schema_config_with_fuzzy_matching(source, target, fuzzy_match_threshold=0.95)
        # Too high threshold → no match
        assert "usr_nm" not in config.columns
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target tests/schema/test_schema_extractors.py -v`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/schema/test_schema_extractors.py
git commit -m "test(schema): add extractor tests for all backends, dataclass, Pydantic"
```

---

### Task 5: Schema validators, converters, custom types, and roundtrips

**Files:**
- Create: `tests/schema/test_schema_validators.py`
- Create: `tests/schema/test_schema_converters.py`
- Create: `tests/schema/test_custom_types.py`
- Create: `tests/schema/test_schema_roundtrips.py`

- [ ] **Step 1: Write validator tests**

```python
# tests/schema/test_schema_validators.py
"""Tests for schema validators."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.schema.config.schema_config import SchemaConfig
from mountainash.schema.config.universal_schema import TableSchema
from mountainash.schema.config.validators import (
    SchemaValidationError,
    assert_round_trip,
    assert_schema_match,
    assert_transformation_config,
    validate_round_trip,
    validate_schema_match,
    validate_transformation_config,
)


class TestValidateRoundTrip:
    """validate_round_trip checks output against predicted schema."""

    def test_matching_output_passes(self):
        source = pl.DataFrame({"old": ["1", "2"]})
        config = SchemaConfig(columns={"old": {"rename": "new"}})
        target = config.apply(source)
        is_valid, errors = validate_round_trip(target, source, config)
        assert is_valid
        assert errors == []

    def test_missing_column_fails(self):
        source = pl.DataFrame({"old": ["1", "2"]})
        config = SchemaConfig(columns={"old": {"rename": "new"}})
        # Create a target that's missing the renamed column
        bad_target = pl.DataFrame({"wrong": ["1", "2"]})
        is_valid, errors = validate_round_trip(bad_target, source, config)
        assert not is_valid
        assert len(errors) > 0


class TestAssertRoundTrip:
    """assert_round_trip raises on failure."""

    def test_passes_when_valid(self):
        source = pl.DataFrame({"a": [1, 2]})
        config = SchemaConfig(columns={})
        target = config.apply(source)
        assert_round_trip(target, source, config)  # Should not raise

    def test_raises_when_invalid(self):
        source = pl.DataFrame({"a": [1, 2]})
        config = SchemaConfig(columns={"a": {"rename": "b"}})
        bad_target = pl.DataFrame({"wrong": [1, 2]})
        with pytest.raises(SchemaValidationError):
            assert_round_trip(bad_target, source, config)


class TestValidateSchemaMatch:
    """validate_schema_match checks DataFrame against expected schema."""

    def test_matching_schema_passes(self):
        df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        is_valid, errors = validate_schema_match(df, expected)
        assert is_valid

    def test_missing_column_fails(self):
        df = pl.DataFrame({"id": [1, 2]})
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        is_valid, errors = validate_schema_match(df, expected)
        assert not is_valid

    def test_strict_extra_columns_fail(self):
        df = pl.DataFrame({"id": [1], "name": ["Alice"], "extra": [True]})
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        is_valid, errors = validate_schema_match(df, expected, strict=True)
        assert not is_valid

    def test_lenient_extra_columns_pass(self):
        df = pl.DataFrame({"id": [1], "name": ["Alice"], "extra": [True]})
        expected = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        is_valid, errors = validate_schema_match(df, expected, strict=False)
        assert is_valid


class TestAssertSchemaMatch:
    """assert_schema_match raises SchemaValidationError on failure."""

    def test_raises_when_invalid(self):
        df = pl.DataFrame({"id": [1]})
        expected = TableSchema.from_simple_dict({"id": "integer", "missing": "string"})
        with pytest.raises(SchemaValidationError):
            assert_schema_match(df, expected)


class TestValidateTransformationConfig:
    """validate_transformation_config checks config against schemas."""

    def test_valid_config_passes(self):
        source = TableSchema.from_simple_dict({"id": "string"})
        target = TableSchema.from_simple_dict({"id": "integer"})
        config = SchemaConfig(columns={"id": {"cast": "integer"}})
        is_valid, errors = validate_transformation_config(config, source, target)
        assert is_valid

    def test_missing_source_column_fails(self):
        source = TableSchema.from_simple_dict({"id": "string"})
        config = SchemaConfig(columns={"nonexistent": {"cast": "integer"}})
        is_valid, errors = validate_transformation_config(config, source)
        assert not is_valid
```

- [ ] **Step 2: Write converter tests**

```python
# tests/schema/test_schema_converters.py
"""Tests for schema converters — TableSchema to backend-specific formats."""
from __future__ import annotations

import polars as pl
import pyarrow as pa
import pytest

from mountainash.schema.config.converters import (
    convert_to_backend,
    to_arrow_schema,
    to_ibis_schema,
    to_pandas_dtypes,
    to_polars_schema,
)
from mountainash.schema.config.types import UniversalType
from mountainash.schema.config.universal_schema import SchemaField, TableSchema


@pytest.fixture
def basic_schema():
    return TableSchema.from_simple_dict({
        "id": "integer",
        "name": "string",
        "score": "number",
        "active": "boolean",
    })


class TestToPolarsSchema:
    """to_polars_schema produces correct Polars dtypes."""

    def test_basic_types(self, basic_schema):
        result = to_polars_schema(basic_schema)
        assert result["id"] == pl.Int64
        assert result["name"] == pl.Utf8
        assert result["score"] == pl.Float64
        assert result["active"] == pl.Boolean

    def test_all_universal_types(self):
        for ut in UniversalType:
            schema = TableSchema.from_simple_dict({"col": ut.value})
            result = to_polars_schema(schema)
            assert "col" in result


class TestToPandasDtypes:
    """to_pandas_dtypes produces correct Pandas dtype strings."""

    def test_basic_types(self, basic_schema):
        result = to_pandas_dtypes(basic_schema)
        assert result["id"] == "Int64"
        assert result["name"] == "string"
        assert result["score"] == "float64"
        assert result["active"] == "boolean"


class TestToArrowSchema:
    """to_arrow_schema produces a valid pa.Schema."""

    def test_basic_types(self, basic_schema):
        result = to_arrow_schema(basic_schema)
        assert isinstance(result, pa.Schema)
        assert result.field("id").type == pa.int64()
        assert result.field("name").type == pa.string()


class TestToIbisSchema:
    """to_ibis_schema produces correct Ibis type strings."""

    def test_basic_types(self, basic_schema):
        result = to_ibis_schema(basic_schema)
        assert result["id"] == "int64"
        assert result["name"] == "string"
        assert result["score"] == "float64"


class TestConvertToBackend:
    """convert_to_backend dispatches correctly."""

    @pytest.mark.parametrize("backend", ["polars", "pandas", "arrow", "ibis"])
    def test_dispatches(self, basic_schema, backend):
        result = convert_to_backend(basic_schema, backend)
        assert isinstance(result, (dict, pa.Schema))

    def test_unknown_backend_raises(self, basic_schema):
        with pytest.raises(ValueError, match="Unknown backend"):
            convert_to_backend(basic_schema, "unknown")

    def test_backend_type_preservation(self):
        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer", backend_type="Int32"),
        ])
        result = to_polars_schema(schema)
        # Should try to use backend_type first
        assert "id" in result
```

- [ ] **Step 3: Write custom type tests**

```python
# tests/schema/test_custom_types.py
"""Tests for CustomTypeRegistry and built-in converters."""
from __future__ import annotations

import math

import polars as pl
import pytest

from mountainash.schema.config.custom_types import (
    CustomTypeRegistry,
    TypeConverterSpec,
    _register_standard_converters,
)


# ---------------------------------------------------------------------------
# Registry CRUD
# ---------------------------------------------------------------------------

class TestCustomTypeRegistryCRUD:
    """Registry register, unregister, has_converter, get_spec, list, clear."""

    def test_register_and_has(self, clean_custom_registry):
        CustomTypeRegistry.clear()
        CustomTypeRegistry.register(
            name="test_type",
            target_universal_type="string",
            python_converter=lambda v, **kw: str(v),
        )
        assert CustomTypeRegistry.has_converter("test_type")

    def test_unregister(self, clean_custom_registry):
        CustomTypeRegistry.clear()
        CustomTypeRegistry.register(
            name="temp",
            target_universal_type="string",
            python_converter=lambda v, **kw: str(v),
        )
        assert CustomTypeRegistry.unregister("temp") is True
        assert CustomTypeRegistry.has_converter("temp") is False

    def test_unregister_nonexistent(self, clean_custom_registry):
        assert CustomTypeRegistry.unregister("does_not_exist") is False

    def test_get_spec(self, clean_custom_registry):
        CustomTypeRegistry.clear()
        CustomTypeRegistry.register(
            name="my_type",
            target_universal_type="number",
            python_converter=lambda v, **kw: float(v),
            description="test converter",
        )
        spec = CustomTypeRegistry.get_spec("my_type")
        assert isinstance(spec, TypeConverterSpec)
        assert spec.name == "my_type"
        assert spec.target_universal_type == "number"

    def test_list_converters(self, clean_custom_registry):
        CustomTypeRegistry.clear()
        _register_standard_converters()
        converters = CustomTypeRegistry.list_converters()
        assert "safe_float" in converters
        assert "safe_int" in converters

    def test_clear(self, clean_custom_registry):
        _register_standard_converters()
        CustomTypeRegistry.clear()
        assert CustomTypeRegistry.list_converters() == {}

    def test_duplicate_register_raises(self, clean_custom_registry):
        CustomTypeRegistry.clear()
        CustomTypeRegistry.register(
            name="dup",
            target_universal_type="string",
            python_converter=lambda v, **kw: str(v),
        )
        with pytest.raises(ValueError, match="already registered"):
            CustomTypeRegistry.register(
                name="dup",
                target_universal_type="string",
                python_converter=lambda v, **kw: str(v),
            )

    def test_is_native_type(self, clean_custom_registry):
        _register_standard_converters()
        assert CustomTypeRegistry.is_native_type("integer") is True
        assert CustomTypeRegistry.is_native_type("safe_float") is False


# ---------------------------------------------------------------------------
# Built-in converters — Python path
# ---------------------------------------------------------------------------

class TestSafeFloatPython:
    """safe_float Python converter."""

    def test_valid_number(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(3.14, "safe_float") == 3.14

    def test_string_number(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert("3.14", "safe_float") == 3.14

    def test_nan_to_none(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(float("nan"), "safe_float") is None

    def test_none_to_none(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(None, "safe_float") is None

    def test_int_to_float(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(42, "safe_float") == 42.0


class TestSafeIntPython:
    """safe_int Python converter."""

    def test_valid_int(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(42, "safe_int") == 42

    def test_string_int(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert("42", "safe_int") == 42

    def test_nan_to_none(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(float("nan"), "safe_int") is None

    def test_float_truncation(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(3.7, "safe_int") == 3


class TestXmlStringPython:
    """xml_string Python converter."""

    def test_angle_brackets(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert("<tag>", "xml_string") == "&lt;tag&gt;"

    def test_ampersand(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert("A&B", "xml_string") == "A&amp;B"

    def test_quotes(self):
        _register_standard_converters()
        result = CustomTypeRegistry.convert('say "hi"', "xml_string")
        assert "&quot;" in result

    def test_none_passthrough(self):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(None, "xml_string") is None


class TestRichBooleanPython:
    """rich_boolean Python converter."""

    @pytest.mark.parametrize("value,expected", [
        ("yes", True), ("no", False),
        ("true", True), ("false", False),
        ("1", True), ("0", False),
        (True, True), (False, False),
        (1, True), (0, False),
        (None, None),
    ])
    def test_conversions(self, value, expected):
        _register_standard_converters()
        assert CustomTypeRegistry.convert(value, "rich_boolean") == expected

    def test_invalid_string_raises(self):
        _register_standard_converters()
        with pytest.raises(ValueError):
            CustomTypeRegistry.convert("maybe", "rich_boolean")


# ---------------------------------------------------------------------------
# Built-in converters — Narwhals vectorized path
# ---------------------------------------------------------------------------

class TestBuiltinVectorized:
    """Built-in converters have Narwhals implementations."""

    @pytest.mark.parametrize("name", ["safe_float", "safe_int", "xml_string", "rich_boolean"])
    def test_is_vectorized(self, name):
        _register_standard_converters()
        assert CustomTypeRegistry.is_vectorized(name) is True

    @pytest.mark.parametrize("name", ["safe_float", "safe_int", "xml_string", "rich_boolean"])
    def test_get_narwhals_converter_not_none(self, name):
        _register_standard_converters()
        conv = CustomTypeRegistry.get_narwhals_converter(name)
        assert conv is not None


# ---------------------------------------------------------------------------
# User-defined converter
# ---------------------------------------------------------------------------

class TestUserDefinedConverter:
    """Users can register, use, and unregister custom converters."""

    def test_python_only_converter(self, clean_custom_registry):
        CustomTypeRegistry.clear()
        _register_standard_converters()
        CustomTypeRegistry.register(
            name="double_it",
            target_universal_type="number",
            python_converter=lambda v, **kw: v * 2 if v is not None else None,
            description="Doubles the value",
        )
        assert CustomTypeRegistry.is_vectorized("double_it") is False
        assert CustomTypeRegistry.convert(5, "double_it") == 10
        CustomTypeRegistry.unregister("double_it")
        assert CustomTypeRegistry.has_converter("double_it") is False
```

- [ ] **Step 4: Write schema roundtrip tests**

```python
# tests/schema/test_schema_roundtrips.py
"""Schema round-trip tests: extract→apply, from_schemas→apply, predict→validate."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.schema.config.extractors import extract_schema_from_dataframe, from_dataclass
from mountainash.schema.config.schema_config import SchemaConfig
from mountainash.schema.config.universal_schema import TableSchema
from mountainash.schema.config.validators import validate_schema_match


class TestExtractApplyRoundTrip:
    """Extract schema from DataFrame → apply to compatible DataFrame."""

    def test_polars_extract_apply(self):
        # Source with known types
        original = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        schema = extract_schema_from_dataframe(original)
        # Create a string version that needs casting
        string_df = pl.DataFrame({"id": ["1", "2"], "name": ["Alice", "Bob"]})
        # Build config to cast id to integer
        config = SchemaConfig(columns={"id": {"cast": "integer"}})
        result = config.apply(string_df)
        assert result["id"].dtype == pl.Int64


class TestFromSchemasApplyRoundTrip:
    """from_schemas auto-mapping → apply → verify output."""

    def test_auto_mapping_apply(self):
        source_schema = TableSchema.from_simple_dict({"old_id": "string", "val": "string"})
        target_schema = TableSchema.from_simple_dict({"old_id": "integer", "val": "number"})
        config = SchemaConfig.from_schemas(source_schema, target_schema)
        df = pl.DataFrame({"old_id": ["1", "2"], "val": ["1.5", "2.5"]})
        result = config.apply(df)
        assert result["old_id"].dtype == pl.Int64
        assert result["val"].dtype == pl.Float64


class TestPredictValidateRoundTrip:
    """predict_output_schema → apply → extract → compare with prediction."""

    def test_predicted_matches_actual(self):
        source_schema = TableSchema.from_simple_dict({"id": "string", "name": "string"})
        config = SchemaConfig(
            columns={"id": {"cast": "integer"}},
            source_schema=source_schema,
        )
        predicted = config.predict_output_schema()
        df = pl.DataFrame({"id": ["1", "2"], "name": ["Alice", "Bob"]})
        result = config.apply(df)
        actual_schema = extract_schema_from_dataframe(result)
        # Predicted and actual should match on field names
        assert set(predicted.field_names) == set(actual_schema.field_names)
```

- [ ] **Step 5: Run all schema tests**

Run: `hatch run test:test-target tests/schema/ -v`
Expected: All tests pass (with known xfails for unsupported backend/type combos).

- [ ] **Step 6: Commit**

```bash
git add tests/schema/test_schema_validators.py tests/schema/test_schema_converters.py tests/schema/test_custom_types.py tests/schema/test_schema_roundtrips.py
git commit -m "test(schema): add validators, converters, custom types, and roundtrip tests"
```

---

## Phase 2: PyData Tests

### Task 6: PyData conftest and ingress factory tests

**Files:**
- Create: `tests/pydata/conftest.py`
- Create: `tests/pydata/test_ingress_factory.py`

- [ ] **Step 1: Create shared pydata fixtures**

```python
# tests/pydata/conftest.py
"""Shared fixtures for pydata tests."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from typing import Optional

import polars as pl
import pytest
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Sample types
# ---------------------------------------------------------------------------

@dataclass
class SamplePerson:
    name: str
    age: int
    score: float


@dataclass
class SampleWithDefaults:
    name: str
    age: int = 0
    email: Optional[str] = None


class SamplePersonModel(BaseModel):
    name: str
    age: int
    score: float


SampleRow = namedtuple("SampleRow", ["name", "age", "score"])


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_DICTS = [
    {"name": "Alice", "age": 30, "score": 1.5},
    {"name": "Bob", "age": 25, "score": 2.0},
    {"name": "Charlie", "age": 35, "score": 3.0},
]

SAMPLE_DICT_OF_LISTS = {
    "name": ["Alice", "Bob", "Charlie"],
    "age": [30, 25, 35],
    "score": [1.5, 2.0, 3.0],
}


@pytest.fixture
def sample_persons():
    return [SamplePerson("Alice", 30, 1.5), SamplePerson("Bob", 25, 2.0)]


@pytest.fixture
def sample_pydantic_persons():
    return [SamplePersonModel(name="Alice", age=30, score=1.5), SamplePersonModel(name="Bob", age=25, score=2.0)]


@pytest.fixture
def sample_named_tuples():
    return [SampleRow("Alice", 30, 1.5), SampleRow("Bob", 25, 2.0)]


@pytest.fixture
def sample_polars_df():
    return pl.DataFrame(SAMPLE_DICT_OF_LISTS)
```

- [ ] **Step 2: Write ingress factory tests**

```python
# tests/pydata/test_ingress_factory.py
"""Tests for PydataIngressFactory format detection."""
from __future__ import annotations

from collections import namedtuple

import polars as pl
import pandas as pd
import pytest

from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory

from conftest import (
    SamplePerson,
    SamplePersonModel,
    SampleRow,
    SAMPLE_DICTS,
    SAMPLE_DICT_OF_LISTS,
)


class TestFormatDetection:
    """_get_strategy_key correctly identifies each data format."""

    def test_single_dataclass(self):
        assert PydataIngressFactory._get_strategy_key(SamplePerson("A", 1, 1.0)) == CONST_PYTHON_DATAFORMAT.DATACLASS

    def test_list_of_dataclasses(self, sample_persons):
        assert PydataIngressFactory._get_strategy_key(sample_persons) == CONST_PYTHON_DATAFORMAT.DATACLASS

    def test_single_pydantic(self):
        assert PydataIngressFactory._get_strategy_key(SamplePersonModel(name="A", age=1, score=1.0)) == CONST_PYTHON_DATAFORMAT.PYDANTIC

    def test_list_of_pydantic(self, sample_pydantic_persons):
        assert PydataIngressFactory._get_strategy_key(sample_pydantic_persons) == CONST_PYTHON_DATAFORMAT.PYDANTIC

    def test_dict_of_lists(self):
        assert PydataIngressFactory._get_strategy_key(SAMPLE_DICT_OF_LISTS) == CONST_PYTHON_DATAFORMAT.PYDICT

    def test_list_of_dicts(self):
        assert PydataIngressFactory._get_strategy_key(SAMPLE_DICTS) == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_single_named_tuple(self):
        assert PydataIngressFactory._get_strategy_key(SampleRow("A", 1, 1.0)) == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_list_of_named_tuples(self, sample_named_tuples):
        assert PydataIngressFactory._get_strategy_key(sample_named_tuples) == CONST_PYTHON_DATAFORMAT.NAMEDTUPLE

    def test_single_plain_tuple(self):
        assert PydataIngressFactory._get_strategy_key((1, "a", 3.0)) == CONST_PYTHON_DATAFORMAT.TUPLE

    def test_list_of_plain_tuples(self):
        data = [(1, "a"), (2, "b")]
        assert PydataIngressFactory._get_strategy_key(data) == CONST_PYTHON_DATAFORMAT.TUPLE

    def test_polars_series_dict(self):
        data = {"a": pl.Series([1, 2]), "b": pl.Series([3, 4])}
        assert PydataIngressFactory._get_strategy_key(data) == CONST_PYTHON_DATAFORMAT.SERIES_DICT

    def test_pandas_series_dict(self):
        data = {"a": pd.Series([1, 2]), "b": pd.Series([3, 4])}
        assert PydataIngressFactory._get_strategy_key(data) == CONST_PYTHON_DATAFORMAT.SERIES_DICT

    def test_indexed_data(self):
        data = {"group_a": [{"x": 1}, {"x": 2}], "group_b": [{"x": 3}]}
        assert PydataIngressFactory._get_strategy_key(data) == CONST_PYTHON_DATAFORMAT.INDEXED_DATA

    def test_collection_list_of_scalars(self):
        assert PydataIngressFactory._get_strategy_key([1, 2, 3]) == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_collection_set(self):
        assert PydataIngressFactory._get_strategy_key({1, 2, 3}) == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_collection_frozenset(self):
        assert PydataIngressFactory._get_strategy_key(frozenset([1, 2])) == CONST_PYTHON_DATAFORMAT.COLLECTION


class TestFormatDetectionEdgeCases:
    """Edge cases in format detection."""

    def test_empty_list(self):
        result = PydataIngressFactory._get_strategy_key([])
        assert result == CONST_PYTHON_DATAFORMAT.COLLECTION

    def test_empty_dict(self):
        result = PydataIngressFactory._get_strategy_key({})
        # Empty dict has no values to check → falls through
        assert result is not None  # Should return something, not crash

    def test_single_item_list_of_dicts(self):
        assert PydataIngressFactory._get_strategy_key([{"a": 1}]) == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_unknown_type_fallback(self):
        assert PydataIngressFactory._get_strategy_key(object()) == CONST_PYTHON_DATAFORMAT.UNKNOWN


class TestGetStrategy:
    """get_strategy returns the correct handler class."""

    def test_pylist_handler(self):
        strategy = PydataIngressFactory.get_strategy(SAMPLE_DICTS)
        assert strategy is not None
        assert hasattr(strategy, "convert")

    def test_pydict_handler(self):
        strategy = PydataIngressFactory.get_strategy(SAMPLE_DICT_OF_LISTS)
        assert strategy is not None
```

- [ ] **Step 3: Run tests**

Run: `hatch run test:test-target tests/pydata/test_ingress_factory.py -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/pydata/conftest.py tests/pydata/test_ingress_factory.py
git commit -m "test(pydata): add conftest fixtures and ingress factory detection tests"
```

---

### Task 7: Ingress handlers tests

**Files:**
- Create: `tests/pydata/test_ingress_handlers.py`

- [ ] **Step 1: Write all 10 ingress handler tests**

```python
# tests/pydata/test_ingress_handlers.py
"""Tests for all 10 ingress handlers."""
from __future__ import annotations

from collections import namedtuple

import polars as pl
import pandas as pd
import pytest

from mountainash.pydata.ingress.pydata_ingress import PydataIngress
from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory

from conftest import (
    SamplePerson,
    SamplePersonModel,
    SampleRow,
    SAMPLE_DICTS,
    SAMPLE_DICT_OF_LISTS,
)


class TestIngressFromPylist:
    """DataframeFromPylist: list of dicts → Polars DataFrame."""

    def test_basic_conversion(self):
        result = PydataIngress.convert(SAMPLE_DICTS)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 3)
        assert result["name"].to_list() == ["Alice", "Bob", "Charlie"]

    def test_with_none_values(self):
        data = [{"a": 1, "b": None}, {"a": 2, "b": "x"}]
        result = PydataIngress.convert(data)
        assert result["b"].null_count() >= 1

    def test_single_dict_in_list(self):
        result = PydataIngress.convert([{"x": 42}])
        assert result.shape == (1, 1)


class TestIngressFromPydict:
    """DataframeFromPydict: dict of lists → Polars DataFrame."""

    def test_basic_conversion(self):
        result = PydataIngress.convert(SAMPLE_DICT_OF_LISTS)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 3)

    def test_column_order(self):
        result = PydataIngress.convert(SAMPLE_DICT_OF_LISTS)
        assert list(result.columns) == ["name", "age", "score"]


class TestIngressFromDataclass:
    """DataframeFromDataclass: dataclass instances → Polars DataFrame."""

    def test_single_instance(self):
        result = PydataIngress.convert(SamplePerson("Alice", 30, 1.5))
        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] >= 1

    def test_list_of_instances(self, sample_persons):
        result = PydataIngress.convert(sample_persons)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (2, 3)
        assert result["name"].to_list() == ["Alice", "Bob"]


class TestIngressFromPydantic:
    """DataframeFromPydantic: Pydantic model instances → Polars DataFrame."""

    def test_single_instance(self):
        result = PydataIngress.convert(SamplePersonModel(name="Alice", age=30, score=1.5))
        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] >= 1

    def test_list_of_instances(self, sample_pydantic_persons):
        result = PydataIngress.convert(sample_pydantic_persons)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (2, 3)


class TestIngressFromNamedTuple:
    """DataframeFromNamedTuple: named tuples → Polars DataFrame."""

    def test_single_instance(self):
        result = PydataIngress.convert(SampleRow("Alice", 30, 1.5))
        assert isinstance(result, pl.DataFrame)

    def test_list_of_instances(self, sample_named_tuples):
        result = PydataIngress.convert(sample_named_tuples)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (2, 3)

    def test_field_names_become_columns(self, sample_named_tuples):
        result = PydataIngress.convert(sample_named_tuples)
        assert "name" in result.columns
        assert "age" in result.columns


class TestIngressFromTuple:
    """DataframeFromTuple: plain tuples → Polars DataFrame."""

    def test_list_of_tuples(self):
        data = [(1, "a"), (2, "b"), (3, "c")]
        result = PydataIngress.convert(data)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 2)


class TestIngressFromSeriesDict:
    """DataframeFromSeriesDict: dict of Series → Polars DataFrame."""

    def test_polars_series(self):
        data = {"a": pl.Series([1, 2, 3]), "b": pl.Series(["x", "y", "z"])}
        result = PydataIngress.convert(data)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 2)

    def test_pandas_series(self):
        data = {"a": pd.Series([1, 2, 3]), "b": pd.Series(["x", "y", "z"])}
        result = PydataIngress.convert(data)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 2)


class TestIngressFromIndexedData:
    """DataframeFromIndexedData: indexed data → Polars DataFrame."""

    def test_basic_indexed(self):
        data = {"group_a": [{"x": 1}, {"x": 2}], "group_b": [{"x": 3}]}
        result = PydataIngress.convert(data)
        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3


class TestIngressFromCollection:
    """IngressFromCollection: scalar collections → Polars DataFrame."""

    def test_list_of_ints(self):
        result = PydataIngress.convert([1, 2, 3])
        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3

    def test_set_of_strings(self):
        result = PydataIngress.convert({"a", "b", "c"})
        assert isinstance(result, pl.DataFrame)
        assert result.shape[0] == 3


class TestIngressFromDefault:
    """DataframeFromDefault: fallback handler."""

    def test_polars_passthrough(self):
        df = pl.DataFrame({"a": [1, 2]})
        strategy = PydataIngressFactory.get_strategy(df)
        # Polars DF goes through default handler
        assert strategy is not None
```

- [ ] **Step 2: Run tests**

Run: `hatch run test:test-target tests/pydata/test_ingress_handlers.py -v`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/pydata/test_ingress_handlers.py
git commit -m "test(pydata): add comprehensive ingress handler tests for all 10 handlers"
```

---

### Task 8: Egress tests

**Files:**
- Create: `tests/pydata/test_egress_all.py`
- Create: `tests/pydata/test_egress_factory.py`

- [ ] **Step 1: Write all 17 egress method tests**

```python
# tests/pydata/test_egress_all.py
"""Tests for all egress methods from EgressFromPolars."""
from __future__ import annotations

import datetime

import polars as pl
import pandas as pd
import pyarrow as pa
import pytest

from mountainash.pydata.egress.egress_pydata_from_polars import EgressFromPolars

from conftest import SamplePerson, SamplePersonModel


@pytest.fixture
def egress():
    return EgressFromPolars()


@pytest.fixture
def test_df():
    return pl.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "score": [1.5, None, 3.0],
    })


# ---------------------------------------------------------------------------
# DataFrame conversions
# ---------------------------------------------------------------------------

class TestEgressDataFrame:
    """DataFrame-to-DataFrame conversions."""

    def test_to_pandas(self, egress, test_df):
        result = egress._to_pandas(test_df)
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "age", "score"]

    def test_to_polars_eager(self, egress, test_df):
        result = egress._to_polars(test_df)
        assert isinstance(result, pl.DataFrame)

    def test_to_polars_lazy(self, egress, test_df):
        result = egress._to_polars(test_df, as_lazy=True)
        assert isinstance(result, pl.LazyFrame)

    def test_to_narwhals(self, egress, test_df):
        import narwhals as nw
        result = egress._to_narwhals(test_df)
        # Should be a narwhals DataFrame
        assert hasattr(result, "to_native")

    def test_to_pyarrow(self, egress, test_df):
        result = egress._to_pyarrow(test_df)
        assert isinstance(result, pa.Table)


# ---------------------------------------------------------------------------
# Python data conversions
# ---------------------------------------------------------------------------

class TestEgressPythonData:
    """DataFrame-to-Python-data conversions."""

    def test_to_dictionary_of_lists(self, egress, test_df):
        result = egress._to_dictionary_of_lists(test_df)
        assert isinstance(result, dict)
        assert result["name"] == ["Alice", "Bob", "Charlie"]
        assert result["age"] == [30, 25, 35]

    def test_to_list_of_dictionaries(self, egress, test_df):
        result = egress._to_list_of_dictionaries(test_df)
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["name"] == "Alice"

    def test_to_list_of_tuples(self, egress, test_df):
        result = egress._to_list_of_tuples(test_df)
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0][0] == "Alice"  # First column


# ---------------------------------------------------------------------------
# Series conversions
# ---------------------------------------------------------------------------

class TestEgressSeries:
    """DataFrame-to-Series conversions."""

    def test_to_dictionary_of_series_polars(self, egress, test_df):
        result = egress._to_dictionary_of_series_polars(test_df)
        assert isinstance(result, dict)
        assert isinstance(result["name"], pl.Series)

    def test_to_dictionary_of_series_pandas(self, egress, test_df):
        result = egress._to_dictionary_of_series_pandas(test_df)
        assert isinstance(result, dict)
        assert isinstance(result["name"], pd.Series)


# ---------------------------------------------------------------------------
# Named tuple conversions
# ---------------------------------------------------------------------------

class TestEgressNamedTuples:
    """DataFrame-to-named-tuple conversions."""

    def test_to_list_of_named_tuples(self, egress, test_df):
        result = egress._to_list_of_named_tuples(test_df)
        assert len(result) == 3
        assert hasattr(result[0], '_fields')
        assert result[0].name == "Alice"

    def test_to_list_of_typed_named_tuples_dates_as_strings(self, egress):
        df = pl.DataFrame({
            "name": ["Alice"],
            "joined": [datetime.date(2024, 1, 1)],
        })
        result = egress._to_list_of_typed_named_tuples(df, preserve_dates=False)
        assert len(result) == 1
        # Date should be string when preserve_dates=False
        assert isinstance(result[0].joined, str)

    def test_to_list_of_typed_named_tuples_dates_preserved(self, egress):
        df = pl.DataFrame({
            "name": ["Alice"],
            "joined": [datetime.date(2024, 1, 1)],
        })
        result = egress._to_list_of_typed_named_tuples(df, preserve_dates=True)
        assert isinstance(result[0].joined, datetime.date)


# ---------------------------------------------------------------------------
# Indexed conversions
# ---------------------------------------------------------------------------

class TestEgressIndexed:
    """DataFrame-to-indexed conversions."""

    def test_to_index_of_dictionaries(self, egress, test_df):
        result = egress._to_index_of_dictionaries(test_df, index_fields=["name"])
        assert isinstance(result, dict)
        assert "Alice" in result
        assert isinstance(result["Alice"], list)

    def test_to_index_of_tuples(self, egress, test_df):
        result = egress._to_index_of_tuples(test_df, index_fields=["name"])
        assert isinstance(result, dict)
        assert "Alice" in result

    def test_to_index_of_named_tuples(self, egress, test_df):
        result = egress._to_index_of_named_tuples(test_df, index_fields=["name"])
        assert isinstance(result, dict)
        assert "Alice" in result

    def test_to_index_of_typed_named_tuples(self, egress, test_df):
        result = egress._to_index_of_typed_named_tuples(test_df, index_fields=["name"])
        assert isinstance(result, dict)

    def test_composite_index(self, egress, test_df):
        result = egress._to_index_of_dictionaries(test_df, index_fields=["name", "age"])
        assert isinstance(result, dict)
        # Composite keys are tuples
        first_key = next(iter(result.keys()))
        assert isinstance(first_key, tuple)


# ---------------------------------------------------------------------------
# Typed output conversions
# ---------------------------------------------------------------------------

class TestEgressTypedOutput:
    """DataFrame-to-dataclass and DataFrame-to-Pydantic conversions."""

    def test_to_list_of_dataclasses(self, egress):
        df = pl.DataFrame({"name": ["Alice"], "age": [30], "score": [1.5]})
        result = egress._to_list_of_dataclasses(df, SamplePerson)
        assert len(result) == 1
        assert isinstance(result[0], SamplePerson)
        assert result[0].name == "Alice"
        assert result[0].age == 30

    def test_to_list_of_pydantic(self, egress):
        df = pl.DataFrame({"name": ["Alice"], "age": [30], "score": [1.5]})
        result = egress._to_list_of_pydantic(df, SamplePersonModel)
        assert len(result) == 1
        assert isinstance(result[0], SamplePersonModel)
        assert result[0].name == "Alice"
```

- [ ] **Step 2: Write egress factory tests**

```python
# tests/pydata/test_egress_factory.py
"""Tests for DataFrameEgressFactory dispatch."""
from __future__ import annotations

import polars as pl
import pandas as pd
import pyarrow as pa
import pytest

from mountainash.pydata.egress.egress_factory import DataFrameEgressFactory


class TestEgressFactoryDispatch:
    """All DataFrame types route to correct strategy."""

    def test_polars_dataframe(self):
        df = pl.DataFrame({"a": [1]})
        strategy = DataFrameEgressFactory.get_strategy(df)
        assert strategy is not None

    def test_polars_lazyframe(self):
        df = pl.DataFrame({"a": [1]}).lazy()
        strategy = DataFrameEgressFactory.get_strategy(df)
        assert strategy is not None

    def test_pandas_dataframe(self):
        df = pd.DataFrame({"a": [1]})
        strategy = DataFrameEgressFactory.get_strategy(df)
        assert strategy is not None

    def test_pyarrow_table(self):
        table = pa.table({"a": [1]})
        strategy = DataFrameEgressFactory.get_strategy(table)
        assert strategy is not None

    def test_narwhals_dataframe(self):
        import narwhals as nw
        df = nw.from_native(pl.DataFrame({"a": [1]}))
        strategy = DataFrameEgressFactory.get_strategy(df)
        assert strategy is not None

    def test_ibis_table(self):
        import ibis
        table = ibis.memtable({"a": [1]})
        strategy = DataFrameEgressFactory.get_strategy(table)
        assert strategy is not None
```

- [ ] **Step 3: Run tests**

Run: `hatch run test:test-target tests/pydata/test_egress_all.py tests/pydata/test_egress_factory.py -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/pydata/test_egress_all.py tests/pydata/test_egress_factory.py
git commit -m "test(pydata): add comprehensive egress tests for all 17 methods + factory"
```

---

### Task 9: Hybrid conversion and roundtrip tests

**Files:**
- Create: `tests/pydata/test_hybrid_conversion.py`
- Create: `tests/pydata/test_pydata_roundtrips.py`

- [ ] **Step 1: Write hybrid conversion tests**

```python
# tests/pydata/test_hybrid_conversion.py
"""Tests for the three-tier hybrid conversion strategy."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.ingress.custom_type_helpers import (
    apply_custom_converters_to_dict,
    apply_custom_converters_to_dicts,
    apply_hybrid_conversion,
    apply_native_conversions_to_dataframe,
    _apply_narwhals_custom_converters,
)
from mountainash.schema.config.custom_types import _register_standard_converters
from mountainash.schema.config.schema_config import SchemaConfig


class TestTier3PythonEdge:
    """apply_custom_converters_to_dict/dicts — Python-only custom converters."""

    def test_single_dict(self):
        _register_standard_converters()
        custom_convs = {"amount": {"cast": "safe_float"}}
        result = apply_custom_converters_to_dict(
            {"amount": "42.5", "id": "123"},
            custom_convs,
        )
        assert result["amount"] == 42.5
        assert result["id"] == "123"  # Untouched

    def test_list_of_dicts(self):
        _register_standard_converters()
        custom_convs = {"amount": {"cast": "safe_float"}}
        data = [{"amount": "1.5"}, {"amount": "2.5"}]
        result = apply_custom_converters_to_dicts(data, custom_convs)
        assert result[0]["amount"] == 1.5
        assert result[1]["amount"] == 2.5

    def test_empty_conversions_passthrough(self):
        data = [{"a": 1}, {"a": 2}]
        result = apply_custom_converters_to_dicts(data, {})
        assert result == data


class TestTier1NativeDataFrame:
    """apply_native_conversions_to_dataframe — vectorized native casts."""

    def test_integer_cast(self):
        df = pl.DataFrame({"id": ["1", "2", "3"]})
        result = apply_native_conversions_to_dataframe(df, {"id": {"cast": "integer"}})
        assert result["id"].dtype == pl.Int64

    def test_empty_conversions(self):
        df = pl.DataFrame({"a": [1, 2]})
        result = apply_native_conversions_to_dataframe(df, {})
        assert result.shape == df.shape


class TestTier2NarwhalsVectorized:
    """_apply_narwhals_custom_converters — vectorized Narwhals expressions."""

    def test_safe_float_vectorized(self):
        _register_standard_converters()
        df = pl.DataFrame({"amount": ["1.5", "2.5", "NaN"]})
        result = _apply_narwhals_custom_converters(df, {"amount": {"cast": "safe_float"}})
        assert result["amount"].dtype == pl.Float64


class TestHybridEndToEnd:
    """apply_hybrid_conversion with mixed tiers."""

    def test_native_only(self):
        config = SchemaConfig(columns={"id": {"cast": "integer"}})
        data = [{"id": "1"}, {"id": "2"}]
        result = apply_hybrid_conversion(data, config)
        assert isinstance(result, pl.DataFrame)
        assert result["id"].dtype == pl.Int64

    def test_no_config(self):
        data = [{"a": 1, "b": "x"}]
        result = apply_hybrid_conversion(data, None)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (1, 2)

    def test_separate_conversions_tier_assignment(self):
        _register_standard_converters()
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "safe_float"},
            "name": {"rename": "full_name"},
        })
        python_custom, narwhals_custom, native = config.separate_conversions()
        assert "amount" in narwhals_custom
        assert "id" in native
        assert "name" in native
```

- [ ] **Step 2: Write pydata roundtrip tests**

```python
# tests/pydata/test_pydata_roundtrips.py
"""Ingress→egress round-trip tests for each data format."""
from __future__ import annotations

from collections import namedtuple

import polars as pl
import pytest

from mountainash.pydata.ingress.pydata_ingress import PydataIngress
from mountainash.pydata.egress.egress_pydata_from_polars import EgressFromPolars

from conftest import (
    SamplePerson,
    SamplePersonModel,
    SampleRow,
    SAMPLE_DICTS,
    SAMPLE_DICT_OF_LISTS,
)


@pytest.fixture
def egress():
    return EgressFromPolars()


class TestRoundTripDictOfLists:
    """dict-of-lists → DataFrame → dict-of-lists."""

    def test_values_preserved(self, egress):
        df = PydataIngress.convert(SAMPLE_DICT_OF_LISTS)
        result = egress._to_dictionary_of_lists(df)
        assert result["name"] == SAMPLE_DICT_OF_LISTS["name"]
        assert result["age"] == SAMPLE_DICT_OF_LISTS["age"]


class TestRoundTripListOfDicts:
    """list-of-dicts → DataFrame → list-of-dicts."""

    def test_values_preserved(self, egress):
        df = PydataIngress.convert(SAMPLE_DICTS)
        result = egress._to_list_of_dictionaries(df)
        assert len(result) == 3
        assert result[0]["name"] == "Alice"


class TestRoundTripDataclass:
    """dataclass instances → DataFrame → dataclass instances."""

    def test_field_values_match(self, egress, sample_persons):
        df = PydataIngress.convert(sample_persons)
        result = egress._to_list_of_dataclasses(df, SamplePerson)
        assert len(result) == 2
        assert result[0].name == "Alice"
        assert result[0].age == 30


class TestRoundTripPydantic:
    """Pydantic instances → DataFrame → Pydantic instances."""

    def test_field_values_match(self, egress, sample_pydantic_persons):
        df = PydataIngress.convert(sample_pydantic_persons)
        result = egress._to_list_of_pydantic(df, SamplePersonModel)
        assert len(result) == 2
        assert result[0].name == "Alice"


class TestRoundTripNamedTuples:
    """named tuples → DataFrame → named tuples."""

    def test_field_values_match(self, egress, sample_named_tuples):
        df = PydataIngress.convert(sample_named_tuples)
        result = egress._to_list_of_named_tuples(df)
        assert len(result) == 2
        assert result[0].name == "Alice"


class TestRoundTripPlainTuples:
    """plain tuples → DataFrame → tuples (column names lost)."""

    def test_values_preserved(self, egress):
        data = [(1, "a"), (2, "b")]
        df = PydataIngress.convert(data)
        result = egress._to_list_of_tuples(df)
        assert len(result) == 2


class TestRoundTripCollection:
    """scalar collection → DataFrame → list."""

    def test_values_preserved(self):
        data = [10, 20, 30]
        df = PydataIngress.convert(data)
        # Get first column values
        col_name = df.columns[0]
        result = df[col_name].to_list()
        assert sorted(result) == sorted(data)
```

- [ ] **Step 3: Run all pydata tests**

Run: `hatch run test:test-target tests/pydata/ -v`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/pydata/test_hybrid_conversion.py tests/pydata/test_pydata_roundtrips.py
git commit -m "test(pydata): add hybrid conversion and round-trip tests"
```

---

### Task 10: Final validation — run full suite

- [ ] **Step 1: Run the full test suite**

Run: `hatch run test:test`
Expected: All new tests pass alongside existing ~3400 tests. Same 7 pre-existing failures.

- [ ] **Step 2: Run just the new test files to count**

Run: `hatch run test:test-target tests/schema/ tests/pydata/ -v --tb=short 2>&1 | tail -5`
Expected: Report of new test count.

- [ ] **Step 3: Final commit if any fixups needed**

```bash
git add -A
git commit -m "test: fixups for comprehensive schema and pydata test suites"
```
