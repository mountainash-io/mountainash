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
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType

from ibis.common.exceptions import UnsupportedBackendType

from mountainash.conform.errors import ConformTransformError
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure


_NATIVE_CONTAINER_BACKENDS = [b for b in ALL_BACKENDS if b not in ("pandas", "narwhals-pandas")]

_OPAQUE_BACKENDS = ["polars", "pandas", "narwhals-polars", "narwhals-pandas"]

_OPAQUE_EGRESS_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
]

_SUPPORTED_TERMINALS = (
    "validation",
    "to_polars",
    "to_pandas",
    "to_dict",
    "to_dicts",
    "to_tuples",
    "item",
    "to_dataclasses",
    "to_pydantic",
)


def _json_relation(backend_name, backend_factory, *, action: str = "coerce"):
    df = backend_factory.create({"payload": ["[1,2]", "[3]"]}, backend_name)
    spec = TableSchema(fields_match="open", fields={"payload": FieldDefinition(type=UniversalType.ARRAY)})
    return ma.relation(df).conform(spec, contract={"data_type": action})


def _json_object_relation(backend_name, backend_factory):
    df = backend_factory.create({"payload": ['{"a": 1, "nested": {"ok": true}}', "{}"]}, backend_name)
    spec = TableSchema(fields_match="open", fields={"payload": FieldDefinition(type=UniversalType.OBJECT)})
    return ma.relation(df).conform(spec, contract={"data_type": "coerce"})

def _parameterized_array_relation(backend_name, backend_factory, values):
    from mountainash.core.dtypes import ArrayDtype, MountainashDtype

    df = backend_factory.create({"payload": values}, backend_name)
    field = FieldDefinition(
        type=UniversalType.ARRAY,
        dtype=ArrayDtype(element=MountainashDtype.I16, dimensions=(2,)),
    )
    return ma.relation(df).conform(
        TableSchema(fields_match="open", fields={"payload": field}),
        contract={"data_type": "coerce"},
    )




@pytest.mark.parametrize("terminal", ["to_polars", "to_pandas", "to_dicts"])
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_nested_logical_cells_require_removed_converter_capability(
    backend_name, terminal, backend_factory
):
    from mountainash.core.types import BackendCapabilityError
    from mountainash.core.dtypes import (
        DecimalDtype, MountainashDtype,
    )

    payload = FieldDefinition(
        type=UniversalType.OBJECT,
        fields={"amount": FieldDefinition(
                dtype=DecimalDtype(precision=6, scale=2),
                decimal_char=",", group_char=".", rounding="half_to_even",
            ),
            "enabled": FieldDefinition(
                type=UniversalType.BOOLEAN,
                dtype=MountainashDtype.BOOL, true_values=["yes"], false_values=["no"],
            ),},
    )
    source = backend_factory.create(
        {"payload": ['{"amount":"1.234,50","enabled":"yes"}']}, backend_name,
    )
    relation = ma.relation(source).conform(
        TableSchema(fields_match="open", fields={"payload": payload}),
        contract={"data_type": "coerce"},
    )

    with pytest.raises(BackendCapabilityError) as error:
        getattr(relation, terminal)()

    assert error.value.function_key is None
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_parameterized_array_width_is_enforced_by_pandas_egress(
    backend_name, backend_factory
):
    """Pandas egress must not bypass native materialization of declared widths."""
    from mountainash.conform.errors import ConformTransformError

    rel = _parameterized_array_relation(backend_name, backend_factory, ["[1]"])

    with pytest.raises(ConformTransformError):
        rel.to_pandas()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_parameterized_array_to_dicts_preserves_declared_width_values(
    backend_name, backend_factory
):
    rel = _parameterized_array_relation(backend_name, backend_factory, ["[1,2]"])

    assert rel.to_dicts() == [{"payload": [1, 2]}]

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_parameterized_array_native_dtypes_survive_all_logical_egress(
    backend_name, backend_factory
):
    import polars as pl

    rel = _parameterized_array_relation(backend_name, backend_factory, ["[1,2]"])
    polars_result = rel.to_polars()
    pandas_result = rel.to_pandas()

    assert polars_result["payload"].dtype == pl.Array(pl.Int16, 2)
    assert polars_result["payload"].to_list() == [[1, 2]]
    assert pandas_result["payload"].tolist() == [[1, 2]]
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
def test_json_object_egress_to_polars_uses_object_column(backend_name, backend_factory):
    import polars as pl

    rel = _json_object_relation(backend_name, backend_factory)
    result = rel.to_polars()
    assert result["payload"].dtype == pl.Object
    assert result["payload"].to_list() == [
        {"a": 1, "nested": {"ok": True}},
        {},
    ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_json_object_egress_to_pandas_preserves_object_containers(backend_name, backend_factory):
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

    def test_error_reports_fields_roots_and_terminals_without_leaking_values(self, backend_name, backend_factory):
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

    def test_structural_only_collects_natively_without_decoding(self, backend_name, backend_factory, monkeypatch):
        import mountainash.conform.structured_transport as transport

        def decode_must_not_run(*args, **kwargs):
            raise AssertionError("structural-only conform invoked the structured decoder")

        monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)

        df = backend_factory.create({"payload": ["[1,2]", "[3]"]}, backend_name)
        spec = TableSchema(fields_match="open", fields={"payload": FieldDefinition(type=UniversalType.ARRAY)})
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"}, apply_value_transforms=False)
        result = rel.collect()
        assert result is not None


@pytest.mark.parametrize("backend_name", _NATIVE_CONTAINER_BACKENDS)
class TestNativeTerminalSuccessForNativeContainers:
    def test_native_list_source_collects_without_decoding(self, backend_name, backend_factory, monkeypatch):
        import mountainash.conform.structured_transport as transport

        def decode_must_not_run(*args, **kwargs):
            raise AssertionError("a native LIST source invoked the structured decoder")

        monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)

        with expect_call_failure(
            when=backend_name == "ibis-sqlite",
            errors=(UnsupportedBackendType,),
            reason="SQLite cannot construct the native Array source; no terminal operation has run",
        ):
            df = backend_factory.create({"payload": [[1, 2], [3]]}, backend_name)
        spec = TableSchema(fields_match="open", fields={"payload": FieldDefinition(type=UniversalType.ARRAY)})
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()
        assert result["payload"].to_list() == [[1, 2], [3]]

    def test_native_struct_source_collects_without_decoding(self, backend_name, backend_factory, monkeypatch):
        import mountainash.conform.structured_transport as transport

        def decode_must_not_run(*args, **kwargs):
            raise AssertionError("a native STRUCT source invoked the structured decoder")

        monkeypatch.setattr(transport, "decode_structured_value", decode_must_not_run)

        with expect_call_failure(
            when=backend_name == "ibis-sqlite",
            errors=(UnsupportedBackendType,),
            reason="SQLite cannot construct the native Struct source; no terminal operation has run",
        ):
            df = backend_factory.create({"payload": [{"a": 1}, {"a": 2}]}, backend_name)
        spec = TableSchema(fields_match="open", fields={"payload": FieldDefinition(type=UniversalType.OBJECT)})
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

    def test_native_python_list_resolves_through_the_opaque_path(self, backend_name, backend_factory):
        df = backend_factory.create({"payload": [[1, 2], [3]]}, backend_name)
        spec = TableSchema(fields_match="open", fields={"payload": FieldDefinition(type=UniversalType.ARRAY)})
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

    spec = TableSchema(fields_match="open", fields={"payload": FieldDefinition(type=UniversalType.ARRAY)})
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
        with expect_call_failure(
            when=backend_name == "narwhals-polars",
            errors=(ConformTransformError,),
            reason="an opaque-carrier structured field (no schema evidence, already-native Python container) fails to decode through logical egress when the source is a Narwhals-wrapped Polars frame",
        ):
            result = rel.to_polars()
            assert result["payload"].dtype == pl.Object
            assert result["payload"].to_list() == [[1, 2], [3]]

    def test_to_pandas_resolves_opaque_native_container(self, backend_name):
        rel = _opaque_relation(backend_name)
        with expect_call_failure(
            when=backend_name == "narwhals-polars",
            errors=(ConformTransformError,),
            reason="an opaque-carrier structured field (no schema evidence, already-native Python container) fails to decode through logical egress when the source is a Narwhals-wrapped Polars frame",
        ):
            result = rel.to_pandas()
            assert result["payload"].tolist() == [[1, 2], [3]]


@pytest.mark.parametrize("backend_name", _OPAQUE_BACKENDS)
class TestOpaqueNativeTerminalFailsClosed:
    def test_native_terminal_still_fails_closed(self, backend_name):
        rel = _opaque_relation(backend_name)
        with pytest.raises(LogicalTerminalRequired):
            rel.collect()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("terminal", ["to_polars", "to_pandas"])
def test_structured_timestamp_egress_preserves_nanoseconds(backend_name, backend_factory, terminal):
    import pyarrow as pa
    import pyarrow.compute as pc
    from mountainash.core.dtypes import StructDtype, TimestampDtype

    source = backend_factory.create(
        {"payload": ['{"at":"2026-01-01T00:00:00.123456789Z"}', None]}, backend_name,
    )
    target = StructDtype((("at", TimestampDtype(9, True, "UTC")),))
    result = getattr(ma.relation(source).conform(
        TableSchema(fields={"payload": FieldDefinition(dtype=target)}, missing_values=[]),
    ), terminal)()
    column = result["payload"]
    arrow = column.to_arrow() if terminal == "to_polars" else column.array.__arrow_array__()
    timestamps = pc.struct_field(arrow, "at")
    assert timestamps.type == pa.timestamp("ns", "UTC")
    assert timestamps.cast(pa.int64()).to_pylist() == [1767225600123456789, None]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("action", ["discard_value", "discard_row"])
def test_structured_narrowing_obeys_discard_policy(backend_name, backend_factory, action):
    import polars as pl
    from mountainash.core.dtypes import ListDtype, MountainashDtype as D

    source = backend_factory.create({"payload": ["[1]", "[300]", None]}, backend_name)
    result = ma.relation(source).conform(
        TableSchema(fields={"payload": FieldDefinition(dtype=ListDtype(D.I8))}, missing_values=[]),
        contract={"data_type": action},
    ).to_polars()
    assert result.schema["payload"] == pl.List(pl.Int8)
    assert result["payload"].to_list() == (
        [[1], None, None] if action == "discard_value" else [[1], None]
    )


def test_polars_native_child_override_survives_pandas_logical_egress():
    # Native overrides are deliberately scoped to their owning execution target.
    import polars as pl
    from mountainash.core.dtypes import MountainashDtype as D

    spec = TableSchema(fields={"payload": FieldDefinition(
        fields={"a": FieldDefinition(dtype=D.I64, backend_type=pl.Float64)},
    )}, missing_values=[])
    result = ma.relation(pl.DataFrame({"payload": ['{"a":"1.5"}']})).conform(spec).to_pandas()
    assert result["payload"].tolist() == [{"a": 1.5}]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_multidimensional_array_logical_conversion(backend_name, backend_factory):
    import polars as pl
    from mountainash.core.dtypes import ArrayDtype, MountainashDtype as D

    source = backend_factory.create({"payload": ['[["1","2"],["3","4"]]', None]}, backend_name)
    result = ma.relation(source).conform(TableSchema(
        fields={"payload": FieldDefinition(dtype=ArrayDtype(D.I16, (2, 2)))},
        missing_values=[],
    )).to_polars()
    assert result.schema["payload"] == pl.Array(pl.Int16, (2, 2))
    assert result["payload"].to_list() == [[[1, 2], [3, 4]], None]


@pytest.mark.parametrize("action", ["coerce", "discard_value", "discard_row"])
def test_native_enum_refinement_is_unsupported_for_logical_egress(action):
    import polars as pl
    from mountainash.core.types import BackendCapabilityError

    relation = ma.relation(
        pl.DataFrame({"payload": ['{"v":"a"}', '{"v":"c"}', None]})
    ).conform(
        TableSchema(fields={"payload": FieldDefinition(
            type=UniversalType.OBJECT,
            backend_type=pl.Struct({"v": pl.Enum(["a", "b"])}),
        )}, missing_values=[]),
        contract={"data_type": action},
    )

    with pytest.raises(BackendCapabilityError) as error:
        relation.to_polars()

    assert error.value.backend == "polars"
    assert error.value.function_key is None


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("terminal", ["to_polars", "to_pandas"])
def test_partial_struct_logical_egress_promotes_null_child_evidence(backend_name, backend_factory, terminal):
    from mountainash.core.dtypes import StructDtype, MountainashDtype as D, SchemaTypeStatus as S
    import pyarrow as pa

    target = StructDtype((("a", D.I16), ("b", S.UNKNOWN)))
    source = backend_factory.create(
        {"payload": ['{"a":"2","b":null}', '{"a":"3","b":true}', None]}, backend_name,
    )
    result = getattr(ma.relation(source).conform(TableSchema(
        fields={"payload": FieldDefinition(dtype=target)}, missing_values=[],
    )), terminal)()
    column = result["payload"]
    arrow = column.to_arrow() if terminal == "to_polars" else column.array.__arrow_array__()
    assert arrow.type == pa.struct([("a", pa.int16()), ("b", pa.bool_())])
    assert arrow.to_pylist() == [{"a": 2, "b": None}, {"a": 3, "b": True}, None]
    assert target.fields[1][1] is S.UNKNOWN

def test_logical_json_transport_does_not_wrap_sibling_native_struct_scalars():
    import polars as pl
    from mountainash.core.dtypes import StructDtype, MountainashDtype as D

    source = pl.DataFrame({
        "native": pl.Series([{"id": 7}], dtype=pl.Struct({"id": pl.Int64})),
        "payload": ['{"items":[1,2]}'],
    })
    relation = ma.relation(source).conform(TableSchema(
        fields={"native": FieldDefinition(dtype=StructDtype((("id", D.I64),))),
            "payload": FieldDefinition(type=UniversalType.OBJECT),},
        missing_values=[],
    ))

    result = relation.to_polars()

    assert result["native"].to_list() == [{"id": 7}]
    assert result["payload"].to_list() == [{"items": [1, 2]}]
