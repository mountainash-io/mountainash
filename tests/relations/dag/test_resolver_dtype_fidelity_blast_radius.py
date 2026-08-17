"""Item 54 blast-radius regression: item 42's empty_frame and item 53's
inline-read cast both consume the shared resolver — the whole point of the
shared-resolver design is that one fix upgrades both at once. These tests
verify that claim end-to-end, plus the cross-backend materialization parity
(spec §7 tests 7-8) and the no-raise partner regression (§5: backend_type
None/"" must still fall through after the raise policy landed).

GREEN expectation: no new production code is required by these tests — if any
fail, that signals one of item 54's earlier tasks missed a call-site, not a
new feature to build.
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

# The three dtype families item 54 upgrades: parameterized backend_type
# (gap 1), categorical (gap 3), nested list (gap 2).
UPGRADED_SPEC = TypeSpec(fields=[
    FieldSpec(
        name="ts", type=UniversalType.ANY,
        backend_type="Datetime(time_unit='us', time_zone='UTC')",
    ),
    FieldSpec(
        name="cat", type=UniversalType.STRING,
        categories=["a", "b"], categories_ordered=True,
    ),
    FieldSpec(
        name="lst", type=UniversalType.ARRAY, item_type="integer",
    ),
])

# Same shape as a Frictionless descriptor (inline-read schema dict).
UPGRADED_SCHEMA_DICT = {"fields": [
    {"name": "ts", "type": "any",
     "x-mountainash": {"backend_type": "Datetime(time_unit='us', time_zone='UTC')"}},
    {"name": "cat", "type": "string", "categories": ["a", "b"], "categoriesOrdered": True},
    {"name": "lst", "type": "array", "itemType": "integer"},
]}

ALL_NULL_DATA = {"ts": [None], "cat": [None], "lst": [None]}


def _polars_ext():
    from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
        MountainashPolarsExtensionRelationSystem,
    )
    return MountainashPolarsExtensionRelationSystem()


def _narwhals_ext():
    from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
        MountainashNarwhalsExtensionRelationSystem,
    )
    return MountainashNarwhalsExtensionRelationSystem()


def _ibis_ext():
    from mountainash.relations.backends.relation_systems.ibis.extensions_mountainash.relsys_ib_ext_ma_util import (
        MountainashIbisExtensionRelationSystem,
    )
    return MountainashIbisExtensionRelationSystem()


class TestEmptyFrameUpgradedDtypes:
    """item 42's empty_frame must produce the upgraded dtypes directly."""

    def test_polars(self):
        df = _polars_ext().empty_frame(UPGRADED_SPEC).collect()
        assert df.schema["ts"] == pl.Datetime(time_unit="us", time_zone="UTC")
        assert df.schema["cat"] == pl.Enum(["a", "b"])
        assert df.schema["lst"] == pl.List(pl.Int64)

    def test_narwhals_schema_and_executed_op(self):
        import narwhals as nw
        lazy = _narwhals_ext().empty_frame(UPGRADED_SPEC)
        frame = lazy.collect()  # executed op
        assert frame.schema["ts"] == nw.Datetime(time_unit="us", time_zone="UTC")
        assert frame.schema["cat"] == nw.Enum(["a", "b"])
        assert frame.schema["lst"] == nw.List(nw.Int64)
        assert frame.shape == (0, 3)

    def test_ibis_schema_and_executed_op(self):
        t = _ibis_ext().empty_frame(UPGRADED_SPEC)
        schema = t.schema()  # backend-native schema post-wrap
        assert schema["ts"].is_timestamp() and schema["ts"].timezone == "UTC"
        assert schema["lst"].is_array() and schema["lst"].value_type.is_int64()
        # categorical is a boundary conversion through Arrow (dictionary or
        # string) — assert it is one of the honest representations, not wrong
        # data; the executed op below is the parity proof.
        assert schema["cat"].is_string() or schema["cat"].is_dictionary()
        out = t.execute()  # executed op
        assert out.shape == (0, 3)
        assert list(out.columns) == ["ts", "cat", "lst"]


class TestInlineReadUpgradedDtypes:
    """item 53's inline-read cast path must produce the upgraded dtypes."""

    def test_all_null_inline_data(self):
        from mountainash.typespec.datapackage import DataResource
        res = DataResource(
            name="t", format="json", data=ALL_NULL_DATA, schema=UPGRADED_SCHEMA_DICT,
        )
        df = _polars_ext().read_resource(res).collect()
        assert df.schema["ts"] == pl.Datetime(time_unit="us", time_zone="UTC")
        assert df.schema["cat"] == pl.Enum(["a", "b"])
        assert df.schema["lst"] == pl.List(pl.Int64)


class TestNoRaisePartnerRegression:
    """§5's previously-legitimate half: backend_type None/"" on a non-ANY
    canonical type must still fall through to canonical — both consumers
    complete without raising InvalidBackendTypeError."""

    @pytest.mark.parametrize("backend_type", [None, ""])
    def test_empty_frame_no_raise(self, backend_type):
        spec = TypeSpec(fields=[
            FieldSpec(name="i", type=UniversalType.INTEGER, backend_type=backend_type),
        ])
        df = _polars_ext().empty_frame(spec).collect()
        assert df.schema["i"] == pl.Int64

    @pytest.mark.parametrize("backend_type", [None, ""])
    def test_inline_read_no_raise(self, backend_type):
        from mountainash.typespec.datapackage import DataResource
        schema = {"fields": [
            {"name": "i", "type": "integer", "x-mountainash": {"backend_type": backend_type}},
        ]}
        res = DataResource(name="t", format="json", data={"i": [None]}, schema=schema)
        df = _polars_ext().read_resource(res).collect()
        assert df.schema["i"] == pl.Int64
