"""Native type adapter contracts: one stateless adapter per type target.

Signatures alone do not qualify the design, so these cases pin behaviour the
registry must delegate: native equivalence in the owning domain, recursive
lowering that stays inside one target, per-nested-child target identity, the
schema-versus-cast distinction, and lazy native-library loading.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from typing import Any

import ibis.expr.datatypes as dt
import narwhals as nw
import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from mountainash.core.dtypes import (
    ArrayDtype,
    DtypeMappingError,
    ListDtype,
    MountainashDtype as D,
    NativeDtype,
    SchemaTypeStatus,
    StructDtype,
    TimestampDtype,
    TypeTarget,
    registry,
)
from mountainash.core.dtypes.protocols import (
    NativeArrowTransportAdapter,
    NativeTypeAdapter,
)

ALL_TARGETS = list(TypeTarget)


class TestAdapterContracts:
    @pytest.mark.parametrize("target", ALL_TARGETS)
    def test_each_target_has_one_retained_adapter_for_both_contracts(self, target):
        adapter = registry._adapter(target)
        assert registry._adapter(target) is adapter
        assert isinstance(adapter, NativeTypeAdapter)
        assert isinstance(adapter, NativeArrowTransportAdapter)
        assert adapter.target is target


class TestTypesEqual:
    @pytest.mark.parametrize("target,left,right,expected", [
        (TypeTarget.POLARS, pl.Datetime("us", "UTC"), pl.Datetime("us", "UTC"), True),
        (TypeTarget.POLARS, pl.Datetime("us"), pl.Datetime("ms"), False),
        (TypeTarget.PYARROW, pa.timestamp("us"), pa.timestamp("us"), True),
        (TypeTarget.PYARROW, pa.timestamp("us"), pa.timestamp("ms"), False),
        (TypeTarget.NARWHALS, nw.Datetime("us"), nw.Datetime("us"), True),
        (TypeTarget.NARWHALS, nw.Int32, nw.Int64, False),
        (TypeTarget.PYTHON, list[int], list[int], True),
        (TypeTarget.PYTHON, list[int], list[str], False),
        # Ibis compares parsed datatypes, so a type string equals its datatype.
        (TypeTarget.IBIS, "int64", dt.int64, True),
        (TypeTarget.IBIS, "int64", dt.int32, False),
        (TypeTarget.IBIS, dt.Timestamp(scale=6), dt.Timestamp(scale=3), False),
        # pandas compares normalised dtypes, so a dtype string equals its dtype.
        (TypeTarget.PANDAS, "Int64", pd.Int64Dtype(), True),
        (TypeTarget.PANDAS, "datetime64[ns]", np.dtype("datetime64[ns]"), True),
        (TypeTarget.PANDAS, "int64", "Int64", False),
    ])
    def test_equivalence_is_decided_in_the_owning_domain(self, target, left, right, expected):
        assert registry.types_equal(left, right, target) is expected
        assert registry.types_equal(right, left, target) is expected
        assert registry._adapter(target).types_equal(left, right) is expected

    def test_arrow_field_evidence_compares_its_qualifiers(self):
        required = pa.field("", pa.int64(), nullable=False)
        labelled = pa.field("", pa.int64(), metadata={b"label": b"source"})
        assert registry.types_equal(required, pa.field("", pa.int64(), nullable=False), TypeTarget.PYARROW)
        assert not registry.types_equal(required, pa.field("", pa.int64()), TypeTarget.PYARROW)
        assert not registry.types_equal(labelled, pa.field("", pa.int64()), TypeTarget.PYARROW)
        assert not registry.types_equal(required, pa.int64(), TypeTarget.PYARROW)


class TestUntypedPythonHints:
    """Authored Any is an absent constraint (not missing evidence); it is a
    sentinel value rather than a bare None from the decoder."""

    def test_untyped_hint_decodes_to_unconstrained_not_none(self):
        assert registry.from_native(Any, TypeTarget.PYTHON) is SchemaTypeStatus.UNCONSTRAINED

    def test_untyped_element_keeps_its_intent(self):
        assert registry.from_native(list[Any], TypeTarget.PYTHON) == ListDtype(
            element=SchemaTypeStatus.UNCONSTRAINED
        )


class TestNestedTargetIdentity:
    @pytest.mark.parametrize("target,foreign", [
        (TypeTarget.PYARROW, TypeTarget.POLARS),
        (TypeTarget.POLARS, TypeTarget.PYARROW),
        (TypeTarget.IBIS, TypeTarget.POLARS),
        (TypeTarget.NARWHALS, TypeTarget.POLARS),
        (TypeTarget.PANDAS, TypeTarget.POLARS),
        (TypeTarget.PYTHON, TypeTarget.POLARS),
    ])
    @pytest.mark.parametrize("shape", ["list", "struct", "array", "deep"])
    def test_foreign_native_child_is_rejected_at_any_depth(self, target, foreign, shape):
        child = NativeDtype(value=object(), target=foreign)
        dtype = {
            "list": ListDtype(child),
            "struct": StructDtype((("x", child),)),
            "array": ArrayDtype(child, (2,)),
            "deep": ListDtype(StructDtype((("x", ListDtype(child)),))),
        }[shape]
        with pytest.raises(DtypeMappingError):
            registry.to_native_schema(dtype, target)

    def test_nested_native_child_of_the_same_target_is_unwrapped(self):
        child = NativeDtype(value=pl.Datetime("ms", "UTC"), target=TypeTarget.POLARS)
        lowered = registry.to_native_schema(StructDtype((("at", ListDtype(child)),)), TypeTarget.POLARS)
        assert lowered == pl.Struct({"at": pl.List(pl.Datetime("ms", "UTC"))})


class TestNativeRepresentationLimits:
    def test_arrow_field_qualifiers_are_refused_by_dtype_only_lowering(self):
        field = NativeDtype(value=pa.field("", pa.int64(), nullable=False), target=TypeTarget.PYARROW)
        with pytest.raises(DtypeMappingError, match="qualifiers"):
            registry.to_native_schema(field, TypeTarget.PYARROW)
        with pytest.raises(DtypeMappingError, match="qualifiers"):
            registry.to_native_schema(ListDtype(field), TypeTarget.PYARROW)

    def test_ibis_physical_sql_refinement_is_not_an_ibis_dtype(self):
        refinement = NativeDtype(value="NUMERIC", target=TypeTarget.IBIS)
        with pytest.raises(DtypeMappingError, match="Physical SQL"):
            registry.to_native_schema(refinement, TypeTarget.IBIS)
        with pytest.raises(DtypeMappingError, match="Physical SQL"):
            registry.to_native_schema(StructDtype((("x", refinement),)), TypeTarget.IBIS)

    @pytest.mark.parametrize("target", [
        TypeTarget.POLARS, TypeTarget.PYARROW, TypeTarget.PANDAS,
        TypeTarget.NARWHALS, TypeTarget.IBIS,
    ])
    @pytest.mark.parametrize("container", [D.LIST, D.STRUCT])
    def test_bare_container_casts_require_element_or_member_shape(self, target, container):
        with pytest.raises(DtypeMappingError):
            registry.to_native_cast(container, target)

    @pytest.mark.parametrize("target", ALL_TARGETS)
    @pytest.mark.parametrize("sentinel", [SchemaTypeStatus.UNKNOWN, SchemaTypeStatus.UNCONSTRAINED])
    def test_construction_sentinels_are_never_native_cast_types(self, target, sentinel):
        with pytest.raises(DtypeMappingError):
            registry.to_native_cast(sentinel, target)

    def test_timestamp_precision_failure_is_a_mapping_error_for_schema_and_cast(self):
        dtype = TimestampDtype(5, True, "UTC")
        with pytest.raises(DtypeMappingError):
            registry.to_native_schema(dtype, TypeTarget.PYARROW)
        with pytest.raises(DtypeMappingError):
            registry.to_native_cast(dtype, TypeTarget.PYARROW)


def _loaded_libraries(statements: str) -> list[str]:
    script = textwrap.dedent("""
        import sys
        from mountainash.core.dtypes import registry, TypeTarget, MountainashDtype as D
        before = set(sys.modules)
        {statements}
        loaded = {{name.split('.')[0] for name in set(sys.modules) - before}}
        print(sorted(loaded & {{'polars', 'pandas', 'pyarrow', 'ibis', 'narwhals'}}))
    """).format(statements=textwrap.dedent(statements).strip())
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    return eval(result.stdout.strip())  # noqa: S307 - sorted list of known library names


class TestLazyNativeLibraries:
    def test_python_target_selection_loads_no_dataframe_library(self):
        assert _loaded_libraries("""
            registry.to_native_schema(D.I64, TypeTarget.PYTHON)
            registry.parse_type_string('int', TypeTarget.PYTHON)
        """) == []

    def test_canonical_transport_loads_arrow_only(self):
        assert _loaded_libraries("""
            registry.to_arrow_transport(D.I64)
        """) == ["pyarrow"]

    @pytest.mark.parametrize("statements,libraries", [
        ("""
            import polars as pl
            registry.to_arrow_transport(NativeDtype(value=pl.Int16, target=TypeTarget.POLARS))
        """, {"polars", "pyarrow"}),
        ("""
            import pandas as pd
            registry.to_arrow_transport(NativeDtype(value=pd.Int16Dtype(), target=TypeTarget.PANDAS))
        """, {"pandas", "pyarrow"}),
        ("""
            import ibis.expr.datatypes as dt
            registry.to_arrow_transport(NativeDtype(value=dt.int16, target=TypeTarget.IBIS))
        """, {"ibis", "pyarrow"}),
        ("""
            import narwhals as nw
            registry.to_arrow_transport(NativeDtype(value=nw.Int16, target=TypeTarget.NARWHALS))
        """, {"narwhals", "pyarrow"}),
        ("""
            import pyarrow as pa
            registry.to_arrow_transport(NativeDtype(value=pa.int16(), target=TypeTarget.PYARROW))
        """, {"pyarrow"}),
    ], ids=["polars", "pandas", "ibis", "narwhals", "pyarrow"])
    def test_native_transport_loads_only_its_owner_and_arrow(self, statements, libraries):
        assert set(_loaded_libraries(
            "from mountainash.core.dtypes import NativeDtype\n" + textwrap.dedent(statements)
        )) <= libraries


def _runs_without(blocked: tuple[str, ...], statements: str) -> None:
    """Run ``statements`` in a fresh process where the blocked libraries cannot be imported."""
    script = "import sys\n" + "".join(f"sys.modules[{name!r}] = None\n" for name in blocked) + textwrap.dedent(statements)
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-1500:]


class TestOptionalLibraryAbsence:
    """An unavailable optional library only matters to the routes that use it."""

    def test_declarations_and_the_frictionless_codec_do_not_need_ibis(self):
        _runs_without(("ibis",), """
            from mountainash.core.dtypes import MountainashDtype as D
            from mountainash.typespec import FieldDefinition, TableSchema
            from mountainash.typespec.adapter_registry import get_schema_codec

            codec = get_schema_codec("frictionless")
            descriptor = codec.encode(TableSchema(fields={"a": FieldDefinition(dtype=D.I64)}))
            assert [field["name"] for field in descriptor["fields"]] == ["a"]
            assert list(codec.decode(descriptor).fields) == ["a"]
        """)

    def test_polars_acquisition_and_schema_construction_do_not_need_pandas_or_ibis(self):
        _runs_without(("pandas", "ibis"), """
            import polars as pl

            from mountainash.core.dtypes import MountainashDtype as D
            from mountainash.typespec import FieldDefinition, TableSchema
            from mountainash.typespec.converters import to_polars_schema
            from mountainash.typespec.source_shape import extract_source_shapes

            frame = pl.DataFrame({"a": [1]})
            assert list(extract_source_shapes(frame)) == ["a"]
            assert list(extract_source_shapes(frame.lazy())) == ["a"]
            schema = TableSchema(fields={"a": FieldDefinition(dtype=D.I64)})
            assert to_polars_schema(schema) == {"a": pl.Int64}
        """)
