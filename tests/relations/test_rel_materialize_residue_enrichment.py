"""Native relation errors require identified issues and reachable consumers."""
from __future__ import annotations

import narwhals as nw
import pandas as pd
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL


def test_error_policy_cannot_target_a_handler_without_native_dispatch():
    snapshot = CapabilityRegistry.snapshot()
    scope = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pandas"))
    key = CapabilityKey(RKEY_MOUNTAINASH_REL.REF, "*")
    try:
        segment = BoundSegment(
            "mountainash.relations.backends.capabilities.narwhals.dialects.narwhals_pandas.extensions_mountainash.relation",
            scope,
            CapabilitySegment(Domain.RELATION, policies=(
                CapabilityPolicyRule(
                    key=key,
                    level=CapabilityLevel.UNSUPPORTED,
                    since="2026-09-18",
                    message="A reference cannot produce a native storage issue.",
                    consumer=PolicyConsumer.MATERIALIZATION_ERROR,
                    action=PolicyAction.ENRICH,
                    native_errors=(TypeError,),
                    native_issue="narwhals:arrow-list-storage",
                ),
            )),
        )
        with pytest.raises(ValueError):
            CapabilityRegistry.register_segment(segment)
        assert CapabilityRegistry.reader(scope).policy_optional(key) is None
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("backend_name,native_error", [
    ("polars", pl.exceptions.SchemaError),
    ("narwhals-polars", nw.exceptions.NarwhalsError),
    ("narwhals-pandas", TypeError),
])
def test_invalid_split_delimiter_is_not_a_storage_limitation(backend_name, native_error, backend_factory):
    """An invalid delimiter on valid string storage keeps the native error."""
    if backend_name == "narwhals-pandas":
        import pyarrow as pa

        dataframe = nw.from_native(pd.DataFrame({
            "text": pd.Series(["a,b", "c"], dtype=pd.ArrowDtype(pa.string())),
        }))
    else:
        dataframe = backend_factory.create({"text": ["a,b", "c"]}, backend_name)
    expression = ma.col("text").str.string_split(1)
    with pytest.raises(native_error) as raised:
        ma.relation(dataframe).select(expression).collect()
    assert not isinstance(raised.value, BackendCapabilityError)


@pytest.mark.parametrize("backend_name", [
    "ibis-duckdb", "ibis-polars", "narwhals-polars", "narwhals-pandas",
])
def test_native_collect_protects_xsd_results_without_exposing_markers(backend_name, backend_factory):
    """Only scopes with explicit XSD residue policies participate."""
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME as FK,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    snapshot = CapabilityRegistry.snapshot()
    family = CONST_BACKEND.IBIS if backend_name.startswith("ibis-") else CONST_BACKEND.NARWHALS
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            f"mountainash.expressions.backends.capabilities.{family.value}.dialects.{backend_name.replace('-', '_')}.extensions_mountainash.datetime",
            Scope(family, Dialect(backend_name)),
            CapabilitySegment(Domain.DATETIME, policies=tuple(
                CapabilityPolicyRule(
                    key=CapabilityKey(operation, "*"),
                    level=CapabilityLevel.UNSUPPORTED,
                    since="2026-09-18",
                    message="Invalid lexical input became null.",
                    consumer=PolicyConsumer.RESULT_PROTECTION,
                    action=PolicyAction.DETECT_NON_NULL_TO_NULL,
                )
                for operation in (FK.PARSE_XSD_DURATION, FK.PARSE_XSD_PARTIAL_DATE)
            )),
        ))
        spec = TypeSpec(fields_match="open", fields=[
            FieldSpec(name="duration", type=UniversalType.DURATION),
            FieldSpec(name="year", type=UniversalType.YEAR),
        ])
        values = {"duration": ["P1D", None], "year": ["2024", None]}
        native = ma.relation(backend_factory.create(values, backend_name)).conform(spec).collect()
        assert ma.relation(native).to_polars().to_dict(as_series=False) == values

        invalid = backend_factory.create({"duration": ["P1D"], "year": ["invalid"]}, backend_name)
        with pytest.raises(BackendCapabilityError) as raised:
            ma.relation(invalid).conform(spec).collect()
        assert raised.value.context["field_name"] == "year"
        assert raised.value.function_key is FK.PARSE_XSD_PARTIAL_DATE
        assert raised.value.limitation.consumer is PolicyConsumer.RESULT_PROTECTION
    finally:
        CapabilityRegistry.restore(snapshot)
