"""Public schema inspection describes actual outputs without collecting rows."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D, dtype_family
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY

SCHEMA_BACKENDS = [*ALL_BACKENDS, "pyarrow", "narwhals-pyarrow"]
NAME_BACKENDS = list(dict.fromkeys([*SCHEMA_BACKENDS, "ibis-polars"]))


def _source(backend_name, data, name):
    if backend_name in {"pandas", "narwhals-pandas"} and isinstance(data, pl.DataFrame):
        import narwhals as nw

        frame = data.to_pandas()
        return nw.from_native(frame) if backend_name == "narwhals-pandas" else frame
    if backend_name in {"pyarrow", "narwhals-pyarrow"}:
        import narwhals as nw
        import pyarrow as pa

        table = data.to_arrow() if isinstance(data, pl.DataFrame) else pa.table(data)
        return nw.from_native(table) if backend_name == "narwhals-pyarrow" else table
    if backend_name == "ibis-polars":
        import ibis

        frame = data if isinstance(data, pl.DataFrame) else pl.DataFrame(data)
        return ibis.polars.connect().create_table(name, frame.to_arrow())
    return REGISTRY[backend_name].build(data, name)


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_computed_schema_is_complete_and_replaces_input_names(backend_name):
    source = _source(backend_name, {"n": [2, 7]}, "schema_computed")
    relation = ma.relation(source).select(ma.col("n").add(1).alias("next"))
    schema = relation.schema
    assert list(schema) == ["next"]
    assert dtype_family(schema["next"]) == D.I64
    assert relation.collect_schema() == schema
    assert relation.collect_schema(allow_execution=True) == schema
    assert relation.to_dict() == {"next": [3, 8]}


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_returned_schema_is_independent_of_subsequent_inspection(backend_name):
    source = _source(backend_name, {"n": [2, 7]}, "schema_independent")
    relation = ma.relation(source).select(ma.col("n").add(1).alias("next"))
    first = relation.collect_schema()
    first.clear()
    actual = relation.schema
    assert list(actual) == ["next"]
    assert dtype_family(actual["next"]) == D.I64


@pytest.mark.parametrize("backend_name", [name for name in SCHEMA_BACKENDS if name != "ibis-sqlite"])
@pytest.mark.parametrize("timezone", [None, "Europe/London"])
def test_union_schema_describes_widened_timestamp_output(backend_name, timezone):
    # SQLite physical temporal storage is qualified in the SQL owner suite.
    left = pl.DataFrame({"at": pl.Series([1], dtype=pl.Datetime("ms", timezone))})
    right = pl.DataFrame({"at": pl.Series([2], dtype=pl.Datetime("ns", timezone))})
    source_left = _source(backend_name, left, "schema_union_left")
    if backend_name.startswith("ibis-"):
        source_right = source_left._find_backend().create_table("schema_union_right", right)
    else:
        source_right = _source(backend_name, right, "schema_union_right")
    relation = ma.concat([ma.relation(source_left), ma.relation(source_right)])
    schema = relation.schema
    sql_aware = bool(timezone) and backend_name == "ibis-duckdb"
    assert schema["at"].precision == (6 if sql_aware else 9)
    assert schema["at"].timezone_aware is (timezone is not None)
    assert schema["at"].timezone == (None if backend_name == "ibis-duckdb" else timezone)
    assert relation.collect_schema() == schema
    assert relation.collect_schema(allow_execution=True) == schema
    actual = relation.to_polars()
    output_zone = "UTC" if timezone and backend_name == "ibis-duckdb" else timezone
    assert actual.schema["at"] == pl.Datetime("us" if sql_aware else "ns", output_zone)
    assert actual["at"].cast(pl.Int64).to_list() == (
        [1_000, 0] if sql_aware else [1_000_000, 2]
    )


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_dag_named_and_fluent_schema_use_output_types(backend_name):
    source = _source(backend_name, {"n": [2, 7]}, "schema_dag")
    dag = ma.RelationDAG()
    dag.add("base", ma.relation(source))
    output = dag.ref("base").select(ma.col("n").add(1).alias("next"))
    dag.add("output", output)
    named = dag.schema("output")
    assert list(named) == ["next"]
    assert dtype_family(named["next"]) == D.I64
    assert output.schema == named
    assert output.collect_schema() == named
    assert output.collect_schema(allow_execution=True) == named
    assert output.to_dict() == {"next": [3, 8]}


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_metadata_does_not_enforce_conform_freeze_but_execution_does(backend_name):
    from mountainash.conform.errors import SchemaDriftError
    from mountainash.typespec.spec import FieldDefinition, TableSchema
    from mountainash.typespec.universal_types import UniversalType

    source = _source(backend_name, {"n": [2, 7], "extra": [3, 4]}, "schema_freeze")
    spec = TableSchema(fields={"n": FieldDefinition(type=UniversalType.INTEGER)}, fields_match="open")
    relation = ma.relation(source).conform(spec, contract={"extra_columns": "freeze"})
    schema = relation.collect_schema()
    # The frozen extra column has no successful execution to describe; only the
    # declared field's type and the execution-time refusal are contractual.
    assert dtype_family(schema["n"]) is D.I64
    with pytest.raises(SchemaDriftError):
        relation.to_dict()


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_join_schema_does_not_copy_types_before_nullable_promotion(backend_name):
    from mountainash.core.dtypes import SchemaTypeStatus
    from mountainash.exceptions import IncompleteSchemaError

    left = _source(backend_name, {"k": [1, 2]}, "schema_join_left")
    if backend_name.startswith("ibis-"):
        right = left._find_backend(use_default=False).create_table(
            "schema_join_right", pl.DataFrame({"k": [1], "value": [9]}).to_arrow(),
        )
    else:
        right = _source(backend_name, {"k": [1], "value": [9]}, "schema_join_right")
    relation = ma.relation(left).join(right, on="k", how="left")
    if backend_name in {"pandas", "narwhals-pandas"}:
        assert relation.schema["value"] is SchemaTypeStatus.UNKNOWN
        with pytest.raises(IncompleteSchemaError):
            relation.collect_schema()
        expected = D.FP64
    else:
        assert dtype_family(relation.collect_schema()["value"]) is D.I64
        expected = D.I64
    assert dtype_family(relation.collect_schema(allow_execution=True)["value"]) is expected
    result = relation.to_polars().sort("k")
    assert result.to_dict(as_series=False) == {"k": [1, 2], "value": [9, None]}
    assert result.schema["value"] == (pl.Float64 if expected is D.FP64 else pl.Int64)


@pytest.mark.parametrize("backend_name", ["pandas", "narwhals-pandas"])
def test_asof_schema_does_not_certify_empty_pandas_integer_payload(backend_name):
    """pandas promotes unmatched ASOF payloads just as in a left join."""
    from mountainash.core.dtypes import SchemaTypeStatus
    from mountainash.exceptions import IncompleteSchemaError

    left = _source(backend_name, {"k": [1, 2]}, "schema_asof_left")
    right = _source(backend_name, {"k": [2], "value": [9]}, "schema_asof_right")
    relation = ma.relation(left).join_asof(right, on="k", strategy="backward")
    assert relation.schema["value"] is SchemaTypeStatus.UNKNOWN
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
    assert dtype_family(relation.collect_schema(allow_execution=True)["value"]) is D.FP64
    assert relation.to_polars().to_dict(as_series=False) == {"k": [1, 2], "value": [None, 9.0]}


# ---------------------------------------------------------------------------
# Output-name inference: native row-index / cross-join layouts (item 370)
# ---------------------------------------------------------------------------

_POLARS_FAMILY = ["polars", "polars-lazy", "narwhals-polars"]
_ROW_INDEX_FIRST = [
    "polars", "polars-lazy", "pandas", "narwhals-polars", "narwhals-pandas",
    "pyarrow", "narwhals-pyarrow",
]
_ROW_INDEX_LAST = ["ibis-duckdb", "ibis-sqlite"]
_IBIS_NAME_BACKENDS = ["ibis-duckdb", "ibis-sqlite", "ibis-polars"]


def _peer(backend_name, left_source, data, name):
    """A right operand on the left operand's own connection for Ibis."""
    if backend_name.startswith("ibis-"):
        frame = data if isinstance(data, pl.DataFrame) else pl.DataFrame(data)
        return left_source._find_backend(use_default=False).create_table(name, frame.to_arrow())
    return _source(backend_name, data, name)


def _forbid_work(guard):
    from mountainash.relations.core.execution.compilation import CompilationSession
    from mountainash.typespec import source_shape

    def forbidden(*args, **kwargs):
        raise AssertionError("proven names must not compile or decode types")

    guard.setattr(CompilationSession, "compile_root", forbidden)
    guard.setattr(source_shape, "extract_source_shapes", forbidden)


def _duplicate_errors():
    import narwhals.exceptions as nw_exc

    return (pl.exceptions.DuplicateError, nw_exc.DuplicateError)


@pytest.mark.parametrize("backend_name", NAME_BACKENDS)
def test_cross_names_need_neither_compilation_nor_type_shapes(backend_name, monkeypatch):
    left = ma.relation(_source(backend_name, {"x": [1], "v": [2]}, "name_cross"))
    right = left.select("x", ma.col("v").alias("w"))
    relation = left.cross_join(right)
    expected = ["x", "v", "x_right", "w"]
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == expected
        assert relation.width == 4
    assert relation.to_polars().columns == expected


@pytest.mark.parametrize("backend_name", NAME_BACKENDS)
def test_cross_custom_suffix_names(backend_name, monkeypatch):
    left_source = _source(backend_name, {"x": [1], "v": [2]}, "name_suffix_left")
    right_source = _peer(backend_name, left_source, {"x": [3], "w": [4]}, "name_suffix_right")
    relation = ma.relation(left_source).join(right_source, how="cross", suffix="_r")
    expected = ["x", "v", "x_r", "w"]
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == expected
    assert relation.to_polars().columns == expected


@pytest.mark.parametrize("backend_name", _IBIS_NAME_BACKENDS)
def test_ibis_cross_empty_suffix_uses_native_right_suffix(backend_name, monkeypatch):
    left_source = _source(backend_name, {"x": [1], "v": [2]}, "name_empty_left")
    right_source = _peer(backend_name, left_source, {"x": [3], "w": [4]}, "name_empty_right")
    relation = ma.relation(left_source).join(right_source, how="cross", suffix="")
    expected = ["x", "v", "x_right", "w"]
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == expected
    assert relation.to_polars().columns == expected


@pytest.mark.parametrize("backend_name", _POLARS_FAMILY)
def test_polars_cross_empty_suffix_collision_keeps_native_duplicate_error(backend_name):
    left_source = _source(backend_name, {"x": [1], "v": [2]}, "name_dup_left")
    right_source = _source(backend_name, {"x": [3], "w": [4]}, "name_dup_right")
    relation = ma.relation(left_source).join(right_source, how="cross", suffix="")
    with pytest.raises(_duplicate_errors()):
        relation.to_polars()


@pytest.mark.parametrize("backend_name", _POLARS_FAMILY)
def test_cross_output_name_collision_keeps_native_duplicate_error(backend_name):
    left_source = _source(backend_name, {"x": [1], "x_right": [2]}, "name_collide_left")
    right_source = _source(backend_name, {"x": [3], "w": [4]}, "name_collide_right")
    relation = ma.relation(left_source).cross_join(right_source)
    with pytest.raises(_duplicate_errors()):
        relation.to_polars()


def test_sqlite_cross_output_name_collision_inspects_but_execution_fails():
    from ibis.common.exceptions import IntegrityError

    left_source = _source("ibis-sqlite", {"x": [1], "x_right": [2]}, "name_collide_sqlite_left")
    right_source = _peer("ibis-sqlite", left_source, {"x": [3], "w": [4]}, "name_collide_sqlite_right")
    relation = ma.relation(left_source).cross_join(right_source)
    assert relation.columns == ["x", "x_right", "w"]
    with pytest.raises(IntegrityError):
        relation.to_polars()


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars"])
def test_cross_with_key_options_keeps_native_failure(backend_name):
    left_source = _source(backend_name, {"x": [1], "v": [2]}, "name_keyed_left")
    right_source = _source(backend_name, {"x": [3], "w": [4]}, "name_keyed_right")
    relation = ma.relation(left_source).join(right_source, how="cross", on="x")
    with pytest.raises(ValueError):
        _ = relation.columns
    with pytest.raises(ValueError):
        relation.to_polars()


@pytest.mark.parametrize("backend_name", NAME_BACKENDS)
@pytest.mark.parametrize("empty_side", ["left", "right", "both"])
def test_cross_names_survive_empty_inputs(backend_name, empty_side, monkeypatch):
    def frame(columns, empty):
        data = {name: [] if empty else [index] for index, name in enumerate(columns)}
        return pl.DataFrame(data, schema={name: pl.Int64 for name in columns})

    left_source = _source(
        backend_name, frame(["x", "v"], empty_side in {"left", "both"}), "name_rows_left",
    )
    right_source = _peer(
        backend_name, left_source, frame(["x", "w"], empty_side in {"right", "both"}), "name_rows_right",
    )
    relation = ma.relation(left_source).cross_join(right_source)
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == ["x", "v", "x_right", "w"]


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars"])
def test_zero_column_sources_have_known_empty_names(backend_name, monkeypatch):
    zero = ma.relation(_source(backend_name, {}, "name_zero"))
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert zero.columns == []
        assert zero.width == 0
        assert zero.with_row_index(name="index").columns == ["index"]
        assert zero.cross_join(pl.DataFrame({"y": [1]})).columns == ["y"]


@pytest.mark.parametrize("backend_name", NAME_BACKENDS)
def test_row_index_names_follow_native_placement(backend_name, monkeypatch):
    relation = ma.relation(
        _source(backend_name, {"x": [1], "v": [2]}, "name_row"),
    ).with_row_index(name="ordinal")
    if backend_name == "narwhals-lazy":
        with pytest.raises(TypeError):
            _ = relation.columns
        with pytest.raises(TypeError):
            relation.to_polars()
        return
    if backend_name == "ibis-polars":
        from mountainash.core.types import BackendCapabilityError

        with pytest.raises(BackendCapabilityError):
            _ = relation.columns
        with pytest.raises(BackendCapabilityError):
            relation.to_polars()
        return
    assert backend_name in _ROW_INDEX_FIRST or backend_name in _ROW_INDEX_LAST
    expected = ["ordinal", "x", "v"] if backend_name in _ROW_INDEX_FIRST else ["x", "v", "ordinal"]
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == expected
    assert relation.to_polars().columns == expected


@pytest.mark.parametrize("backend_name", [*_ROW_INDEX_FIRST, *_ROW_INDEX_LAST])
def test_default_row_index_name(backend_name, monkeypatch):
    relation = ma.relation(_source(backend_name, {"x": [1], "v": [2]}, "name_row_default")).with_row_index()
    expected = ["index", "x", "v"] if backend_name in _ROW_INDEX_FIRST else ["x", "v", "index"]
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == expected
    assert relation.to_polars().columns == expected


@pytest.mark.parametrize("backend_name", _ROW_INDEX_LAST)
def test_ibis_row_index_replaces_existing_name_in_place(backend_name, monkeypatch):
    relation = ma.relation(_source(backend_name, {"x": [1], "v": [2]}, "name_row_replace")).with_row_index(name="x")
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == ["x", "v"]
    assert relation.to_polars().columns == ["x", "v"]


@pytest.mark.parametrize("backend_name", _POLARS_FAMILY)
def test_polars_row_index_existing_name_keeps_descriptive_names_and_native_error(backend_name):
    relation = ma.relation(_source(backend_name, {"x": [1], "v": [2]}, "name_row_dup")).with_row_index(name="x")
    assert relation.columns == ["x", "v"]
    with pytest.raises(_duplicate_errors()):
        relation.to_polars()


@pytest.mark.parametrize("backend_name", ["polars", "polars-lazy", "narwhals-polars", "ibis-duckdb"])
def test_row_index_then_cross_names(backend_name, monkeypatch):
    left = ma.relation(_source(backend_name, {"value": [8, 3]}, "name_row_cross")).with_row_index(name="ordinal")
    relation = left.cross_join(left.select(ma.col("value").alias("other")))
    expected = ["value", "ordinal", "other"] if backend_name.startswith("ibis-") else ["ordinal", "value", "other"]
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == expected
    assert relation.to_polars().columns == expected


@pytest.mark.parametrize("backend_name", _POLARS_FAMILY)
def test_names_are_not_an_execution_certificate(backend_name, monkeypatch):
    import narwhals.exceptions as nw_exc

    failures = (pl.exceptions.ColumnNotFoundError, nw_exc.ColumnNotFoundError)
    relation = ma.relation(_source(backend_name, {"x": [1]}, "name_missing")).filter(
        ma.col("missing") > 0
    ).cross_join(pl.DataFrame({"y": [2]}))
    with monkeypatch.context() as guard:
        _forbid_work(guard)
        assert relation.columns == ["x", "y"]
    if backend_name == "narwhals-polars":
        from mountainash.core.dtypes import SchemaTypeStatus

        # Eager Narwhals already defers this computation at the schema boundary.
        assert relation.schema == {"x": SchemaTypeStatus.UNKNOWN, "y": SchemaTypeStatus.UNKNOWN}
    else:
        with pytest.raises(failures):
            _ = relation.schema
    with pytest.raises(failures):
        relation.to_polars()


# --- Native metadata methods, called directly with route evidence only ------


class _ForbiddenNative:
    """Location connection/prototype stand-in: any use is a contract breach."""

    def __getattr__(self, name):
        raise AssertionError(f"name inference touched location data ({name})")

    def __bool__(self):
        raise AssertionError("name inference touched location data")


def _location(family, dialect, form="EAGER", binding="bound"):
    from mountainash.relations.core.execution.location import ExecutionLocation
    from mountainash.relations.core.materialization import ExecutionForm

    return ExecutionLocation(
        family, dialect, ExecutionForm[form], binding,
        connection=_ForbiddenNative(), prototype=_ForbiddenNative(),
    )


def _system(family, dialect):
    import mountainash.relations.backends  # noqa: F401
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

    return get_relation_system(family)(dialect=dialect)


def test_polars_native_name_methods():
    from mountainash.core.constants import CONST_BACKEND as B

    system = _system(B.POLARS, "polars")
    location = _location(B.POLARS, "polars", "LAZY")
    assert system.infer_row_index_names(("x", "v"), name="ordinal", location=location) == ("ordinal", "x", "v")
    assert system.infer_row_index_names((), name="index", location=location) == ("index",)
    assert system.infer_row_index_names(("x", "v"), name="x", location=location) is None
    cross = system.infer_cross_join_names
    assert cross(("x", "v"), ("x", "w"), suffix="_right", location=location) == ("x", "v", "x_right", "w")
    assert cross(("x", "v"), ("x", "w"), suffix="_r", location=location) == ("x", "v", "x_r", "w")
    assert cross(("x", "v"), ("y",), suffix="", location=location) == ("x", "v", "y")
    assert cross((), ("y",), suffix="_right", location=location) == ("y",)
    assert cross(("x",), (), suffix="_right", location=location) == ("x",)
    assert cross((), (), suffix="_right", location=location) == ()
    assert cross(("x", "v"), ("x", "w"), suffix="", location=location) is None
    assert cross(("x", "x_right"), ("x", "w"), suffix="_right", location=location) is None
    assert cross(("x",), ("y", "y"), suffix="_right", location=location) is None


@pytest.mark.parametrize("dialect", ["narwhals-polars", "narwhals-pandas", "narwhals-pyarrow", "narwhals-other"])
def test_narwhals_native_name_methods_accept_any_eager_form(dialect):
    from mountainash.core.constants import CONST_BACKEND as B

    system = _system(B.NARWHALS, dialect)
    eager = _location(B.NARWHALS, dialect, "EAGER")
    assert system.infer_row_index_names(("x", "v"), name="ordinal", location=eager) == ("ordinal", "x", "v")
    assert system.infer_row_index_names(("x", "v"), name="x", location=eager) is None
    assert system.infer_cross_join_names(
        ("x", "v"), ("x", "w"), suffix="_right", location=eager,
    ) == ("x", "v", "x_right", "w")
    assert system.infer_cross_join_names(("x",), ("x",), suffix="", location=eager) is None


@pytest.mark.parametrize("form", ["LAZY", "DEFERRED"])
def test_narwhals_row_index_needs_proven_eager_form(form):
    from mountainash.core.constants import CONST_BACKEND as B

    system = _system(B.NARWHALS, "narwhals-polars")
    location = _location(B.NARWHALS, "narwhals-polars", form)
    assert system.infer_row_index_names(("x",), name="ordinal", location=location) is None
    # Cross-join layout does not depend on the effective form.
    assert system.infer_cross_join_names(
        ("x",), ("x",), suffix="_right", location=location,
    ) == ("x", "x_right")


@pytest.mark.parametrize("dialect", ["ibis-duckdb", "ibis-sqlite", "ibis-postgres"])
def test_ibis_native_name_methods_for_bound_dialects(dialect):
    from mountainash.core.constants import CONST_BACKEND as B

    system = _system(B.IBIS, dialect)
    location = _location(B.IBIS, dialect, "DEFERRED")
    assert system.infer_row_index_names(("x", "v"), name="ordinal", location=location) == ("x", "v", "ordinal")
    assert system.infer_row_index_names(("x", "v"), name="x", location=location) == ("x", "v")
    assert system.infer_row_index_names((), name="index", location=location) == ("index",)
    cross = system.infer_cross_join_names
    assert cross(("x", "v"), ("x", "w"), suffix="_r", location=location) == ("x", "v", "x_r", "w")
    assert cross(("x", "v"), ("x", "w"), suffix="", location=location) == ("x", "v", "x_right", "w")
    assert cross(("x", "x_right"), ("x", "w"), suffix="_right", location=location) is None
    assert cross(("x", "x_right"), ("x", "w"), suffix="", location=location) is None


@pytest.mark.parametrize("dialect", [None, "ibis-polars"])
def test_ibis_row_index_without_supported_dialect_is_unproven(dialect):
    from mountainash.core.constants import CONST_BACKEND as B

    system = _system(B.IBIS, dialect)
    location = _location(B.IBIS, dialect, "DEFERRED", binding="memory" if dialect is None else "bound")
    assert system.infer_row_index_names(("x",), name="ordinal", location=location) is None
