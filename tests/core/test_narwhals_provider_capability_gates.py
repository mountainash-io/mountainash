"""Public provider paths retain working neighbors around qualified refusals."""

from __future__ import annotations

from decimal import Decimal

import duckdb
import narwhals as nw
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError

_PROVIDERS = ["polars", "narwhals-polars", "ibis-duckdb", "narwhals-pyarrow", "narwhals-duckdb"]


@pytest.fixture
def qualified_environment(monkeypatch):
    """Control gate applicability, not providers or native execution."""
    import importlib.metadata

    original_version = importlib.metadata.version
    qualified = {"narwhals": "2.27.1", "pyarrow": "26.0.0", "duckdb": "1.5.6"}
    monkeypatch.setattr(
        importlib.metadata,
        "version",
        lambda name: qualified[name] if name in qualified else original_version(name),
    )


@pytest.fixture(params=_PROVIDERS)
def provider_frame(request, backend_factory):
    data = {"value": ["AU", "NZ"], "pattern": ["^AU$", "^AU$"], "number": ["1.25", "2.50"]}
    provider = request.param
    if provider == "narwhals-pyarrow":
        yield provider, nw.from_native(pa.table(data))
    elif provider == "narwhals-duckdb":
        with duckdb.connect() as connection:
            yield provider, nw.from_native(connection.from_arrow(pa.table(data)))
    else:
        yield provider, backend_factory.create(data, provider)


@pytest.mark.parametrize("pattern_kind", ["string", "literal-expression", "dynamic"])
def test_regex_patterns_preserve_provider_boundaries(provider_frame, pattern_kind, qualified_environment):
    provider, frame = provider_frame
    pattern = {"string": "^AU$", "literal-expression": ma.lit("^AU$"), "dynamic": ma.col("pattern")}[pattern_kind]
    query = ma.relation(frame).select(ma.col("value").str.regex_contains(pattern).alias("match"))
    if provider == "narwhals-pyarrow" and pattern_kind == "dynamic":
        with pytest.raises(BackendCapabilityError) as error:
            query.to_polars()
        assert error.value.function_key.name == "REGEX_CONTAINS"
    else:
        result = query.to_polars()
        assert result["match"].to_list() == [True, False]
        assert result.schema["match"] == pl.Boolean


def test_decimal_refusal_does_not_block_ordinary_conversion(provider_frame, qualified_environment):
    provider, frame = provider_frame
    expression = ma.col("number").cast(ma.DecimalDtype(12, 2), rounding="half_to_even")
    query = ma.relation(frame).select(expression.alias("amount"))
    if provider.startswith("narwhals-"):
        with pytest.raises(BackendCapabilityError) as error:
            query.to_polars()
        assert error.value.function_key.name == "DECIMAL_CAST"
    else:
        result = query.to_polars()
        assert result["amount"].to_list() == [Decimal("1.25"), Decimal("2.50")]
        assert result.schema["amount"] == pl.Decimal(12, 2)
    neighbor = ma.relation(frame).select(ma.col("number").cast(float).alias("amount")).to_polars()
    assert neighbor["amount"].to_list() == [1.25, 2.5]


@pytest.mark.parametrize(
    "provider_frame,kind",
    [("narwhals-pyarrow", "regex"), ("narwhals-pyarrow", "decimal"), ("narwhals-duckdb", "decimal")],
    indirect=["provider_frame"],
)
@pytest.mark.parametrize("selection", ["trusted", "newer-version", "unknown-version"])
def test_unselected_provider_gate_preserves_native_failure(provider_frame, kind, selection, monkeypatch):
    import importlib.metadata

    _, frame = provider_frame
    if selection != "trusted":
        original_version = importlib.metadata.version

        def observed_version(name):
            if name == "narwhals":
                if selection == "unknown-version":
                    raise importlib.metadata.PackageNotFoundError(name)
                return "2.28.0"
            return original_version(name)

        monkeypatch.setattr(importlib.metadata, "version", observed_version)
    expression = (
        ma.col("value").str.regex_contains(ma.col("pattern"))
        if kind == "regex"
        else ma.col("number").cast(ma.DecimalDtype(12, 2), rounding="half_to_even")
    )
    policy = ma.CapabilityPolicy.trusted() if selection == "trusted" else ma.CapabilityPolicy.checked()
    with ma.capability_policy(policy):
        with pytest.raises(TypeError if kind == "regex" else NotImplementedError) as error:
            ma.relation(frame).select(expression.alias("result")).to_polars()
    assert not isinstance(error.value, BackendCapabilityError)
