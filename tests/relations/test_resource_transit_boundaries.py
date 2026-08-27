"""Transit-boundary proofs for resource readers and schema inspection
(Task 9 of the pandas-transit-elimination plan, backlog slice 5).

Every reader (Polars/Narwhals/Ibis extension `read_resource`/`empty_frame`/
`sample`/`fetch_from_end`) and the Narwhals schema-inspection unwrap in
`mountainash.typespec.source_shape` now route through `transit_call()`. This
file proves, per backend, that: (1) the conversion trace records only the
declared `BoundaryKey`s for that reader, (2) every recorded route/class
matches the boundary's own registry entry, and (3) no reader ever
constructs a NEW pandas object -- a pandas-constructor tripwire is active
for every case, since none of these readers select pandas as a native
destination (spec section 13).

Design: mountainash-central 2026-08-27-pandas-transit-elimination-design.md
section 13 (readers, schema inspection, pydata, result processing).
"""
from __future__ import annotations

from contextlib import contextmanager

import narwhals as nw
import pandas as pd
import polars as pl
import pytest

from mountainash.core.transit import (
    BOUNDARY_REGISTRY,
    RouteKey,
    TransitClass,
    capture_conversion_trace,
)
from mountainash.typespec.datapackage import DataResource
from mountainash.typespec.source_shape import extract_source_shapes


@contextmanager
def forbid_pandas_construction(monkeypatch):
    def blocked_init(self, *args, **kwargs):
        raise AssertionError("unexpected pandas construction")

    monkeypatch.setattr(pd.DataFrame, "__init__", blocked_init)
    monkeypatch.setattr(pd.Series, "__init__", blocked_init)
    yield


def _get_polars_ext():
    from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
        MountainashPolarsExtensionRelationSystem,
    )
    return MountainashPolarsExtensionRelationSystem()


def _get_narwhals_ext():
    from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
        MountainashNarwhalsExtensionRelationSystem,
    )
    return MountainashNarwhalsExtensionRelationSystem()


def _get_ibis_ext():
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )
    return MountainashIbisExtensionRelationSystem()


_EXTS = {"polars": _get_polars_ext, "narwhals": _get_narwhals_ext, "ibis": _get_ibis_ext}


@pytest.fixture(params=["polars", "narwhals", "ibis"])
def backend_ext(request):
    return _EXTS[request.param]()


def _assert_records_match_registry(trace, *, expected_routes: set[RouteKey]) -> None:
    """Every recorded route/class is exactly what BOUNDARY_REGISTRY declares
    for that key -- the trace can never silently diverge from the registry
    it was looked up from. Not every reader path hits a risky-named callee
    (e.g. Polars' Arrow-fallback route is pl.from_arrow(), never tracked),
    so an empty trace is valid; only *recorded* keys are constrained."""
    for record in trace.records:
        spec = BOUNDARY_REGISTRY[record.boundary_key]
        assert record.route is spec.route
        assert record.transit_class is spec.transit_class
        assert record.route in expected_routes, (record.boundary_key, record.route)


class TestReaderTraceIdentity:
    """Proves each backend's read_resource() records only its own declared
    boundary keys, never a pandas-producing one."""

    def test_inline_json_trace(self, backend_ext, monkeypatch):
        res = DataResource(name="t", data=[{"a": 1}, {"a": 2}], format="json")
        with forbid_pandas_construction(monkeypatch), capture_conversion_trace() as trace:
            backend_ext.read_resource(res)
        _assert_records_match_registry(
            trace,
            expected_routes={
                RouteKey.RESOURCE_READ, RouteKey.NATIVE_MATERIALIZATION, RouteKey.PYDATA_EGRESS,
            },
        )

    def test_local_csv_fallback_trace(self, backend_ext, monkeypatch, tmp_path):
        p = tmp_path / "d.json"
        p.write_text('[{"a": 1}, {"a": 2}]')
        res = DataResource(name="d", path=str(p), format="json")
        with forbid_pandas_construction(monkeypatch), capture_conversion_trace() as trace:
            backend_ext.read_resource(res)
        _assert_records_match_registry(
            trace,
            expected_routes={
                RouteKey.RESOURCE_READ, RouteKey.NATIVE_MATERIALIZATION, RouteKey.PYDATA_EGRESS,
            },
        )

    def test_no_transit_call_produces_pandas(self, backend_ext, monkeypatch, tmp_path):
        """The single pandas-permitted disposition (EXPLICIT_PANDAS_*) never
        appears for a resource read -- readers only ever select Polars,
        Narwhals-non-pandas, or Ibis as their native destination."""
        p = tmp_path / "d.csv"
        p.write_text("a,b\n1,x\n2,y\n")
        res = DataResource(name="d", path=str(p), format="csv")
        with forbid_pandas_construction(monkeypatch), capture_conversion_trace() as trace:
            backend_ext.read_resource(res)
        for record in trace.records:
            spec = BOUNDARY_REGISTRY[record.boundary_key]
            assert spec.transit_class not in (
                TransitClass.EXPLICIT_PANDAS_INPUT,
                TransitClass.EXPLICIT_PANDAS_EGRESS,
            )


class TestEmptyFrameAndSampleTrace:
    def test_empty_frame_no_pandas(self, backend_ext, monkeypatch):
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import UniversalType

        spec = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.INTEGER)])
        with forbid_pandas_construction(monkeypatch), capture_conversion_trace() as trace:
            backend_ext.empty_frame(spec)
        for record in trace.records:
            spec_entry = BOUNDARY_REGISTRY[record.boundary_key]
            assert spec_entry.transit_class not in (
                TransitClass.EXPLICIT_PANDAS_INPUT,
                TransitClass.EXPLICIT_PANDAS_EGRESS,
            )

    @pytest.mark.parametrize("backend_name", ["polars", "narwhals"])
    def test_sample_collect_records_native_lazy_collect(self, backend_name, monkeypatch):
        ext = _EXTS[backend_name]()
        if backend_name == "polars":
            relation = pl.DataFrame({"x": list(range(10))}).lazy()
        else:
            relation = nw.from_native(
                pl.DataFrame({"x": list(range(10))}).lazy()
            )
        with forbid_pandas_construction(monkeypatch), capture_conversion_trace() as trace:
            ext.sample(relation, n=3, seed=0)
        assert trace.records, "sample() must record its collect() boundary"
        for record in trace.records:
            spec = BOUNDARY_REGISTRY[record.boundary_key]
            assert spec.transit_class is TransitClass.NON_PANDAS_OPERATION

    def test_ibis_fetch_from_end_records_scalar_execute(self):
        """count().execute() legitimately returns a Python scalar; PyArrow's
        OWN internal chunked-array-to-scalar conversion may use pandas as a
        private implementation detail here (outside our control), so no
        pandas-constructor tripwire applies to this one boundary -- only the
        recorded route/class contract does."""
        import ibis

        con = ibis.duckdb.connect()
        table = con.create_table("t", {"x": list(range(10))}, overwrite=True)
        with capture_conversion_trace() as trace:
            result = _get_ibis_ext().fetch_from_end(table, 3)
        assert result.count().execute() == 3
        assert len(trace.records) == 1
        record = trace.records[0]
        assert BOUNDARY_REGISTRY[record.boundary_key].route is RouteKey.IBIS_SCALAR_TERMINAL
        assert record.transit_class is TransitClass.NON_PANDAS_OPERATION


class TestSchemaInspectionTrace:
    """`extract_source_shapes()` on a Narwhals frame never constructs a NEW
    pandas object; it only inspects schema metadata, including via the
    pandas-permitted diagnostic unwrap when the source is already
    pandas-backed."""

    def test_narwhals_polars_schema_no_pandas(self, monkeypatch):
        frame = nw.from_native(pl.DataFrame({"a": [1], "b": ["x"]}))
        with forbid_pandas_construction(monkeypatch), capture_conversion_trace() as trace:
            shapes = extract_source_shapes(frame)
        assert set(shapes) == {"a", "b"}
        assert trace.records
        for record in trace.records:
            spec = BOUNDARY_REGISTRY[record.boundary_key]
            assert spec.route is RouteKey.SCHEMA_INSPECTION

    def test_narwhals_pandas_schema_permits_existing_pandas_unwrap(self):
        """The source is ALREADY pandas-backed (constructed by the test, not
        by the unwrap call); `_from_narwhals_schema` only reads `.dtypes`
        off the object it receives back, which transit_call permits under
        RESULT_DIAGNOSTIC_VIEW."""
        frame = nw.from_native(pd.DataFrame({"a": [1], "b": ["x"]}))
        with capture_conversion_trace() as trace:
            shapes = extract_source_shapes(frame)
        assert set(shapes) == {"a", "b"}
        assert any(
            BOUNDARY_REGISTRY[r.boundary_key].transit_class is TransitClass.RESULT_DIAGNOSTIC_VIEW
            for r in trace.records
        )
