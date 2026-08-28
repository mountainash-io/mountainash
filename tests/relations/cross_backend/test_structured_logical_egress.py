"""Cross-backend structured JSON ingress: fail-closed native terminals and
complete logical egress (spec Task 5).

Covers the full ``ALL_BACKENDS`` matrix for the JSON-text carrier. The
schema-proven native LIST/STRUCT carrier is scoped to the backends that
have a genuine native list/struct dtype -- Polars, its Narwhals wrappers,
and Ibis; pandas has no native container dtype, so a pandas or
narwhals-pandas source is always OPAQUE (schema evidence is unavailable),
never NATIVE, regardless of the physical values it already holds. The
opaque carrier itself (a Python-object-typed source column holding raw
Python containers, no JSON encoding) is scoped to the backends that can
physically hold a Python object column -- Polars, pandas, and the Narwhals
dialects wrapping them; PyArrow and the SQL-backed Ibis dialects have no
native "arbitrary Python object" column type, so an opaque source cannot
exist there. Neither scoping is a narrowed test
(cross-backend-test-coverage.md) -- both are genuine construction limits.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import LogicalTerminalRequired
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence

_NATIVE_CONTAINER_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("MA-CONF-04", backend=b)) if b == "ibis-sqlite" else b
    for b in ALL_BACKENDS
    if b not in ("pandas", "narwhals-pandas")
]

_OPAQUE_BACKENDS = ["polars", "pandas", "narwhals-polars", "narwhals-pandas"]

_OPAQUE_EGRESS_BACKENDS = [
    "polars",
    "pandas",
    pytest.param("narwhals-polars", marks=xfail_divergence("MA-CONF-06", backend="narwhals-polars")),
    "narwhals-pandas",
]

_SUPPORTED_TERMINALS = (
    "validation", "to_polars", "to_pandas", "to_dict", "to_dicts",
    "to_tuples", "item", "to_dataclasses", "to_pydantic",
)


def _json_relation(backend_name, backend_factory, *, action: str = "coerce"):
    df = backend_factory.create({"payload": ["[1,2]", "[3]"]}, backend_name)
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    return ma.relation(df).conform(spec, contract={"data_type": action})


def _json_object_relation(backend_name, backend_factory):
    df = backend_factory.create(
        {"payload": ['{"a": 1, "nested": {"ok": true}}', "{}"]}, backend_name
    )
    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)])
    return ma.relation(df).conform(spec, contract={"data_type": "coerce"})


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_json_object_egress_returns_python_dictionaries(backend_name, backend_factory):
    rel = _json_object_relation(backend_name, backend_factory)
    assert rel.to_dicts() == [
        {"payload": {"a": 1, "nested": {"ok": True}}},
        {"payload": {}},
    ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_evolve_preserves_structured_source_values(backend_name, backend_factory):
    rel = _json_relation(backend_name, backend_factory, action="evolve")
    result = rel.to_polars()
    assert result["payload"].to_list() == ["[1,2]", "[3]"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_json_object_egress_to_polars_uses_object_column(
    backend_name, backend_factory
):
    import polars as pl

    rel = _json_object_relation(backend_name, backend_factory)
    result = rel.to_polars()
    assert result["payload"].dtype == pl.Object
    assert result["payload"].to_list() == [
        {"a": 1, "nested": {"ok": True}},
        {},
    ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_json_object_egress_to_pandas_preserves_object_containers(
    backend_name, backend_factory
):
    rel = _json_object_relation(backend_name, backend_factory)
    result = rel.to_pandas()
    assert result["payload"].dtype == object
    assert result["payload"].tolist() == [
        {"a": 1, "nested": {"ok": True}},
        {},
    ]



# ---------------------------------------------------------------------------
# Step 1: native-terminal failure -- fail closed, zero materialization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNativeTerminalFailsClosed:
    @pytest.mark.parametrize("terminal", ["collect", "collect_with_drift"])
    def test_raises_logical_terminal_required(self, backend_name, backend_factory, terminal):
        rel = _json_relation(backend_name, backend_factory)
        with pytest.raises(LogicalTerminalRequired):
            getattr(rel, terminal)()

    def test_zero_materialize_native_calls(self, backend_name, backend_factory, monkeypatch):
        import mountainash.relations.core.materialization as materialization_module

        rel = _json_relation(backend_name, backend_factory)
        calls = []
        original = materialization_module.materialize_native

        def spy(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)

        monkeypatch.setattr(materialization_module, "materialize_native", spy)

        with pytest.raises(LogicalTerminalRequired):
            rel.collect()
        assert calls == []

        with pytest.raises(LogicalTerminalRequired):
            rel.collect_with_drift()
        assert calls == []

    def test_error_reports_fields_roots_and_terminals_without_leaking_values(
        self, backend_name, backend_factory
    ):
        rel = _json_relation(backend_name, backend_factory)
        with pytest.raises(LogicalTerminalRequired) as exc_info:
            rel.collect()

        err = exc_info.value
        assert err.fields == ("payload",)
        assert err.roots == ("array",)
        assert set(err.supported_terminals) == set(_SUPPORTED_TERMINALS)
        message = str(err)
        assert "[1,2]" not in message
        assert "[3]" not in message


# ---------------------------------------------------------------------------
# Step 2: native-terminal success -- native carriers, evolve, structural-only
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNativeTerminalSuccessForEvolveAndStructural:
    def test_evolve_collects_natively_without_decoding(self, backend_name, backend_factory, monkeypatch):
        import mountainash.conform.structured_transport as transport

        def decode_must_not_run(*args, **kwargs):
            raise AssertionError("evolve invoked the structured decoder")

        monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)

        rel = _json_relation(backend_name, backend_factory, action="evolve")
        result = rel.collect()
        assert result is not None

    def test_structural_only_collects_natively_without_decoding(
        self, backend_name, backend_factory, monkeypatch
    ):
        import mountainash.conform.structured_transport as transport

        def decode_must_not_run(*args, **kwargs):
            raise AssertionError("structural-only conform invoked the structured decoder")

        monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)

        df = backend_factory.create({"payload": ["[1,2]", "[3]"]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]
        )
        rel = ma.relation(df).conform(
            spec, contract={"data_type": "coerce"}, apply_value_transforms=False
        )
        result = rel.collect()
        assert result is not None

@pytest.mark.parametrize("backend_name", _NATIVE_CONTAINER_BACKENDS)
class TestNativeTerminalSuccessForNativeContainers:
    def test_native_list_source_collects_without_decoding(self, backend_name, backend_factory, monkeypatch):
        import mountainash.conform.structured_transport as transport

        def decode_must_not_run(*args, **kwargs):
            raise AssertionError("a native LIST source invoked the structured decoder")

        monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)

        df = backend_factory.create({"payload": [[1, 2], [3]]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()
        assert result["payload"].to_list() == [[1, 2], [3]]

    def test_native_struct_source_collects_without_decoding(self, backend_name, backend_factory, monkeypatch):
        import mountainash.conform.structured_transport as transport

        def decode_must_not_run(*args, **kwargs):
            raise AssertionError("a native STRUCT source invoked the structured decoder")

        monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)

        df = backend_factory.create({"payload": [{"a": 1}, {"a": 2}]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()
        assert result["payload"].to_list() == [{"a": 1}, {"a": 2}]


@pytest.mark.parametrize("backend_name", ["pandas", "narwhals-pandas"])
class TestPandasNativePythonContainerIsOpaqueNotNative:
    """pandas has no native list/struct dtype: a column already holding raw
    Python lists/dicts is still schema-evidence-free (OPAQUE), so the
    decoder still runs -- it just always succeeds immediately because the
    value is already a native Python container (spec Task 4's
    ``_normalize_native`` path)."""

    def test_native_python_list_resolves_through_the_opaque_path(
        self, backend_name, backend_factory
    ):
        df = backend_factory.create({"payload": [[1, 2], [3]]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()
        assert result["payload"].to_list() == [[1, 2], [3]]


# ---------------------------------------------------------------------------
# Step 3: complete logical egress -- JSON text across every terminal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCompleteLogicalEgressJsonText:
    def test_to_polars_returns_object_column(self, backend_name, backend_factory):
        import polars as pl

        rel = _json_relation(backend_name, backend_factory)
        result = rel.to_polars()
        assert result["payload"].dtype == pl.Object
        assert result["payload"].to_list() == [[1, 2], [3]]

    def test_to_pandas_returns_object_column(self, backend_name, backend_factory):
        rel = _json_relation(backend_name, backend_factory)
        result = rel.to_pandas()
        assert result["payload"].dtype == object
        assert result["payload"].tolist() == [[1, 2], [3]]

    def test_to_dict_and_to_dicts_return_python_containers(self, backend_name, backend_factory):
        rel = _json_relation(backend_name, backend_factory)
        assert rel.to_dict()["payload"] == [[1, 2], [3]]
        assert rel.to_dicts() == [{"payload": [1, 2]}, {"payload": [3]}]

    def test_to_tuples_and_item_return_python_containers(self, backend_name, backend_factory):
        rel = _json_relation(backend_name, backend_factory)
        assert rel.to_tuples() == [([1, 2],), ([3],)]
        assert rel.item("payload", 0) == [1, 2]
        assert rel.item("payload", 1) == [3]

    def test_decoder_runs_exactly_once_per_cell_for_a_python_egress_terminal(
        self, backend_name, backend_factory, monkeypatch
    ):
        """`to_dicts()` delegates through `to_polars()`; the decoder must not
        run a second time for the Python egress step (spec Task 5 step 3)."""
        import mountainash.conform.structured_transport as transport

        calls = []
        original = transport.decode_structured_value

        def spy(value, *, expected_root):
            calls.append(value)
            return original(value, expected_root=expected_root)

        monkeypatch.setattr(transport, "decode_structured_value", spy)

        rel = _json_relation(backend_name, backend_factory)
        rel.to_dicts()

        assert len(calls) == 2


def _opaque_relation(backend_name):
    import pandas as pd
    import polars as pl

    spec = TypeSpec(
        fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]
    )
    if backend_name in ("polars", "narwhals-polars"):
        df = pl.DataFrame({"payload": pl.Series([[1, 2], [3]], dtype=pl.Object)})
    else:
        df = pd.DataFrame({"payload": pd.Series([[1, 2], [3]], dtype=object)})
    if backend_name.startswith("narwhals"):
        import narwhals as nw

        df = nw.from_native(df, eager_only=True)
    return ma.relation(df).conform(spec, contract={"data_type": "coerce"})


@pytest.mark.parametrize("backend_name", _OPAQUE_EGRESS_BACKENDS)
class TestCompleteLogicalEgressOpaqueNative:
    def test_to_polars_resolves_opaque_native_container(self, backend_name):
        import polars as pl

        rel = _opaque_relation(backend_name)
        result = rel.to_polars()
        assert result["payload"].dtype == pl.Object
        assert result["payload"].to_list() == [[1, 2], [3]]

    def test_to_pandas_resolves_opaque_native_container(self, backend_name):
        rel = _opaque_relation(backend_name)
        result = rel.to_pandas()
        assert result["payload"].tolist() == [[1, 2], [3]]


@pytest.mark.parametrize("backend_name", _OPAQUE_BACKENDS)
class TestOpaqueNativeTerminalFailsClosed:
    def test_native_terminal_still_fails_closed(self, backend_name):
        rel = _opaque_relation(backend_name)
        with pytest.raises(LogicalTerminalRequired):
            rel.collect()
