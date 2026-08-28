"""Native structured (LIST/STRUCT) sources never round-trip through JSON
text (Task 10 step 3).

A schema-bearing native LIST/STRUCT carrier (Polars, its Narwhals wrappers,
Ibis) is decoded purely from schema metadata (`extract_source_shapes` --
`collect_schema()`/table schema only, spec `typespec/source_shape.py`);
`json.loads()` never runs because there is no JSON text to parse, and no
row value is ever inspected to determine ARRAY/OBJECT-ness. An opaque
native-Python-container carrier (pandas, narwhals-pandas -- no native
list/struct dtype) also never calls `json.loads()`: the cell already holds
a real Python list/dict, so the transport action normalizes it directly
(spec Task 4's `_normalize_native` path) without any text decode.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence

_NATIVE_CONTAINER_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("MA-CONF-04", backend=b)) if b == "ibis-sqlite" else b
    for b in ALL_BACKENDS
    if b not in ("pandas", "narwhals-pandas")
]


def _patch_json_loads(monkeypatch):
    import mountainash.conform.structured_transport as transport

    calls: list[str] = []
    original = transport.json.loads

    def spy(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(transport.json, "loads", spy)
    return calls


def _patch_extract_source_shapes(monkeypatch):
    from mountainash.typespec import source_shape as source_shape_module

    calls: list[str] = []
    original = source_shape_module.extract_source_shapes

    def spy(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(source_shape_module, "extract_source_shapes", spy)
    return calls


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NATIVE_CONTAINER_BACKENDS)
class TestSchemaBearingNativeContainersNeverParseJSON:
    def test_native_list_source_never_calls_json_loads(
        self, backend_name, backend_factory, monkeypatch
    ):
        json_calls = _patch_json_loads(monkeypatch)
        shape_calls = _patch_extract_source_shapes(monkeypatch)

        df = backend_factory.create({"payload": [[1, 2], [3]]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()

        assert result["payload"].to_list() == [[1, 2], [3]], backend_name
        assert json_calls == [], backend_name
        # Schema evidence alone drove ARRAY dispatch -- extract_source_shapes
        # (collect_schema()/table-schema only) ran; no row was ever sniffed.
        assert shape_calls, backend_name

    def test_native_struct_source_never_calls_json_loads(
        self, backend_name, backend_factory, monkeypatch
    ):
        json_calls = _patch_json_loads(monkeypatch)
        shape_calls = _patch_extract_source_shapes(monkeypatch)

        df = backend_factory.create({"payload": [{"a": 1}, {"a": 2}]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()

        assert result["payload"].to_list() == [{"a": 1}, {"a": 2}], backend_name
        assert json_calls == [], backend_name
        assert shape_calls, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["pandas", "narwhals-pandas"])
class TestOpaquePandasContainersStayOnLogicalConversion:
    """No native list/struct dtype exists here, so schema evidence is
    unavailable -- the already-native Python container resolves through
    logical conversion (spec Task 4), never through a JSON-text decode."""

    def test_native_python_list_resolves_without_parsing_json(
        self, backend_name, backend_factory, monkeypatch
    ):
        json_calls = _patch_json_loads(monkeypatch)

        df = backend_factory.create({"payload": [[1, 2], [3]]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()

        assert result["payload"].to_list() == [[1, 2], [3]], backend_name
        assert json_calls == [], backend_name

    def test_native_python_dict_resolves_without_parsing_json(
        self, backend_name, backend_factory, monkeypatch
    ):
        json_calls = _patch_json_loads(monkeypatch)

        df = backend_factory.create({"payload": [{"a": 1}, {"a": 2}]}, backend_name)
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = rel.to_polars()

        assert result["payload"].to_list() == [{"a": 1}, {"a": 2}], backend_name
        assert json_calls == [], backend_name
