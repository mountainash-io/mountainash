"""Closed lineage rules for structured physical transport."""
from __future__ import annotations

from enum import Enum
from types import MappingProxyType, SimpleNamespace

import pytest
from fixtures.backend_registry import ALL_BACKENDS

import mountainash as ma
from mountainash.conform.errors import UnsupportedStructuredTransportUse
from mountainash.conform.structured_transport import (
    StructuredCarrier,
    StructuredFieldPlan,
    StructuredRoot,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL as RM,
    RKEY_SUBSTRAIT_REL as RS,
)
from mountainash.relations.core.relation_system.relation_mapping.registry import (
    RelationOperationRegistry,
)
from mountainash.relations.core.structured_lineage import (
    TRANSPORT_LINEAGE_POLICIES,
    propagate_structured_plans,
)


def transport_plan(name: str = "payload") -> StructuredFieldPlan:
    return StructuredFieldPlan(
        field_name=name,
        root=StructuredRoot.ARRAY,
        carrier=StructuredCarrier.JSON_TEXT,
        configured_action="coerce",
        apply_value_transforms=True,
        missing_values=(),
        null_fill=None,
        declaration_fingerprint="schema",
        origin_node_id="conform",
    )


@pytest.mark.parametrize("selector,target", [("^absent$", "payload"), ("^payload$", "payload"), ("*", "*")])
def test_selector_alias_replacement_requires_actual_output(selector, target):
    """Polars selector expansion boundary: a zero-output alias is a no-op."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )
    result = relation.with_columns(ma.col(selector).alias(target)).to_polars()
    expected = {"payload": [[1]]}
    if target == "*":
        expected["*"] = [[1]]
    assert result.to_dict(as_series=False) == expected


@pytest.mark.parametrize("selector", ["*", "^payload$"])
@pytest.mark.parametrize("as_string", [False, True])
def test_select_selector_carries_structured_transport(selector, as_string):
    """Existing Polars selector lowering must retain logical terminal decoding."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )
    expression = selector if as_string else ma.col(selector)
    assert relation.select(expression).to_dict() == {"payload": [[1]]}


@pytest.mark.parametrize("operation", ["select", "with_columns"])
@pytest.mark.parametrize("shape", ["regex-alias", "native", "selector-suffix"])
def test_unresolved_projection_cannot_discard_transport(operation, shape):
    """Polars native/regex selectors have no portable source mapping."""
    import polars as pl

    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )
    expression = {
        "native": ma.native(pl.col("payload")),
        "regex-alias": ma.col("^pay.*$").alias("payload"),
        "selector-suffix": ma.col("^payload$").name.suffix("_copy"),
    }[shape]
    with pytest.raises((IncompleteProjectionSchemaError, UnsupportedStructuredTransportUse), match="projection|payload"):
        getattr(relation, operation)(expression).to_polars()


def node(operation_key, **attrs):
    return SimpleNamespace(operation_key=operation_key, **attrs)


def test_every_relation_operation_declares_transport_lineage():
    """The policy registry closes over the runtime operation registry."""
    assert set(RelationOperationRegistry.list_all()) == set(TRANSPORT_LINEAGE_POLICIES)


@pytest.mark.parametrize("operation", [RS.FETCH, RM.SAMPLE, RM.WITH_ROW_INDEX, RM.FETCH_FROM_END])
def test_preserving_operations_retain_transport_plans(operation):
    """Row-preserving operations do not consume a carried structured field."""
    plans = MappingProxyType({"payload": transport_plan()})

    result = propagate_structured_plans(node(operation), [plans], MappingProxyType({}))

    assert result == plans
    assert result is not plans


def test_direct_project_select_and_alias_preserve_transport_plan():
    """A direct field carriage preserves tags under its final output name."""
    plans = MappingProxyType({"payload": transport_plan()})

    selected = propagate_structured_plans(
        node(RS.PROJECT_SELECT, expressions=["payload"]), [plans], MappingProxyType({})
    )
    aliased = propagate_structured_plans(
        node(RS.PROJECT_SELECT, expressions=[ma.col("payload").alias("body")]),
        [plans],
        MappingProxyType({}),
    )

    assert set(selected) == {"payload"}
    assert set(aliased) == {"body"}
    assert aliased["body"].field_name == "body"


def test_project_drop_and_rename_update_transport_field_names():
    """Field-removing and field-renaming projections update plan keys exactly."""
    plans = MappingProxyType({"payload": transport_plan()})

    dropped = propagate_structured_plans(
        node(RS.PROJECT_DROP, expressions=["payload"]), [plans], MappingProxyType({})
    )
    renamed = propagate_structured_plans(
        node(RS.PROJECT_RENAME, rename_mapping={"payload": "body"}),
        [plans],
        MappingProxyType({}),
    )

    assert dropped == {}
    assert set(renamed) == {"body"}
    assert renamed["body"].field_name == "body"


def test_scalar_expression_reading_transported_field_is_rejected_before_compile():
    """A physical JSON carrier cannot enter an arbitrary scalar expression."""
    plans = MappingProxyType({"payload": transport_plan()})

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        propagate_structured_plans(
            node(RS.PROJECT_SELECT, expressions=[ma.col("payload").str.length()]),
            [plans],
            MappingProxyType({}),
        )


def test_untagged_projection_expression_does_not_disrupt_transport_plans():
    """Expressions over ordinary fields are safe while a tag is carried elsewhere."""
    plans = MappingProxyType({"payload": transport_plan()})

    result = propagate_structured_plans(
        node(RS.PROJECT_WITH_COLUMNS, expressions=[ma.col("name").str.to_uppercase()]),
        [plans],
        MappingProxyType({}),
    )

    assert result == plans


def test_native_ibis_deferred_without_structured_plan_is_ignored():
    """A raw Ibis deferred must not recurse during lineage inspection."""
    import ibis

    result = propagate_structured_plans(
        node(RS.FILTER, predicate=ibis._.col > 1),
        [MappingProxyType({})],
        MappingProxyType({}),
    )

    assert result == {}


@pytest.mark.parametrize("raw", [False, True])
@pytest.mark.parametrize("consumes", [False, True])
def test_computed_overwrite_distinguishes_consumption_from_replacement(raw, consumes):
    """Raw normalized aliases must retire stale tags but never hide consumption."""
    expression = (ma.col("payload" if consumes else "id") + 1).alias("payload")
    if raw:
        expression = expression._node
    project = ma.relation({"id": [1], "payload": ["[2]"]}).with_columns(expression)._node
    plans = {"payload": transport_plan()}
    if consumes:
        with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
            propagate_structured_plans(project, [plans], {})
    else:
        assert propagate_structured_plans(project, [plans], {}) == {}


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("names", [None, set(), {"id", "payload"}])
def test_join_ref_names_distinguish_unknown_empty_and_collision(names, nested):
    """An unresolved ref cannot license an unsuffixed carrier mapping."""
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

    left = Relation(RefRelNode(name="left"))
    if nested:
        left = left.head(1)
    joined = left.join(ma.relation({"id": [1], "payload": ["[2]"]}), on="id")._node

    def resolve(ref):
        assert ref.name == "left"
        return names

    # No right metadata means no collision decision is required.
    assert propagate_structured_plans(joined, [{}, {}], {}, output_names_resolver=resolve) == {}
    if names is None:
        with pytest.raises(IncompleteProjectionSchemaError, match="lineage.*left"):
            propagate_structured_plans(
                joined, [{}, {"payload": transport_plan()}], {}, output_names_resolver=resolve,
            )
    else:
        result = propagate_structured_plans(
            joined, [{}, {"payload": transport_plan()}], {}, output_names_resolver=resolve,
        )
        expected = "payload_right" if names else "payload"
        assert set(result) == {expected}
        assert result[expected].field_name == expected


@pytest.mark.parametrize(
    ("how", "side", "requires_names"),
    [
        ("inner", "left", False),
        ("inner", "right", True),
        ("right", "left", False),
        ("right", "right", True),
        ("semi", "left", False),
        ("anti", "left", False),
    ],
)
def test_join_requests_unknown_names_only_for_the_suffixed_metadata_side(how, side, requires_names):
    """Left names never change (join_layout); only right-side metadata needs a collision decision."""
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    opaque = ma.relation({"id": [1], "payload": ["[2]"]}).with_columns(ma.native(object()).alias("extra"))
    joined = opaque.join(opaque, on="id", how=how)._node
    inputs = [{"payload": transport_plan()} if side == "left" else {},
              {"payload": transport_plan()} if side == "right" else {}]
    if requires_names:
        with pytest.raises(IncompleteProjectionSchemaError, match="output"):
            propagate_structured_plans(joined, inputs, {})
    else:
        result = propagate_structured_plans(joined, inputs, {})
        assert set(result) == {"payload"}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("structured", [False, True])
def test_opaque_left_join_requires_names_only_for_metadata(backend_name, backend_factory, structured):
    """Opaque passthrough remains valid unless a physical carrier needs suffixing."""
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    left_source, right_source = backend_factory.create_pair(
        {"id": [1], "payload": ["left"]}, {"id": [1], "payload": ["[2]"]}, backend_name,
    )
    native = (ma.col("id") + 1).compile(left_source)
    if backend_name.startswith("ibis"):
        native = native.resolve(left_source)
    left = ma.relation(left_source).with_columns(ma.native(native).alias("extra"))
    right = ma.relation(right_source)
    if structured:
        right = right.conform(TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
        ))
    # Check the actual metadata boundary: native structured backends need no
    # carrier suffix mapping, while JSON transport does.
    _, right_visitor = right._compile_and_execute_with_visitor()
    if right_visitor.structured_field_plans or right_visitor.owned_residue_checks:
        with pytest.raises(IncompleteProjectionSchemaError, match="output|projection|lineage"):
            left.join(right, on="id").to_polars()
    else:
        result = left.join(right, on="id").to_polars()
        assert result["payload"].to_list() == ["left"]
        assert result["extra"].to_list() == [2]
        assert result["payload_right"].to_list() == ([[2]] if structured else ["[2]"])


@pytest.mark.parametrize(
    ("operation", "attrs"),
    [
        (RS.FILTER, {"predicate": ma.col("payload").is_not_null()}),
        (RS.SORT, {"sort_fields": ["payload"]}),
        (RM.DROP_NULLS, {"options": {"subset": ["payload"]}}),
        (RM.TOP_K, {"options": {"by": "payload"}}),
        (RM.EXPLODE, {"options": {"columns": ["payload"]}}),
        (RM.UNNEST, {"options": {"columns": ["payload"]}}),
        (RS.AGGREGATE, {"keys": [ma.col("payload")], "measures": []}),
    ],
)
def test_structured_consumers_reject_tagged_input(operation, attrs):
    """Operations that inspect a physical carrier fail before native execution."""
    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        propagate_structured_plans(
            node(operation, **attrs),
            [MappingProxyType({"payload": transport_plan()})],
            MappingProxyType({}),
        )


def test_union_all_requires_equal_transport_declarations():
    """Union-all can preserve a tag only when every input agrees exactly."""
    plan = transport_plan()
    aligned = propagate_structured_plans(
        node(RS.UNION_ALL),
        [MappingProxyType({"payload": plan}), MappingProxyType({"payload": plan})],
        MappingProxyType({}),
    )
    assert aligned == {"payload": plan}

    with pytest.raises(UnsupportedStructuredTransportUse, match="UNION_ALL"):
        propagate_structured_plans(
            node(RS.UNION_ALL),
            [MappingProxyType({"payload": plan}), MappingProxyType({})],
            MappingProxyType({}),
        )


@pytest.mark.parametrize("operation", [RS.DISTINCT, RS.UNION_DISTINCT])
def test_equality_operations_reject_remaining_transport_plans(operation):
    """Physical JSON representation cannot participate in equality set semantics."""
    with pytest.raises(UnsupportedStructuredTransportUse):
        propagate_structured_plans(
            node(operation), [MappingProxyType({"payload": transport_plan()})], MappingProxyType({})
        )


def test_unknown_relation_operation_is_rejected_when_transport_is_present():
    """An unclassified operation fails closed instead of silently dropping transport safety."""
    class UnknownOperation(Enum):
        UNKNOWN = "unknown"

    with pytest.raises(UnsupportedStructuredTransportUse):
        propagate_structured_plans(
            node(UnknownOperation.UNKNOWN),
            [MappingProxyType({"payload": transport_plan()})],
            MappingProxyType({}),
        )


def test_filter_rejects_transport_before_backend_filter_dispatch(monkeypatch):
    """The visitor checks lineage before compiling a predicate or calling Polars."""
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def filter_must_not_run(*args, **kwargs):
        raise AssertionError("backend filter received a transported physical field")

    monkeypatch.setattr(PolarsRelationSystem, "filter", filter_must_not_run)
    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.filter(ma.col("payload").is_not_null()).to_polars()


def test_sort_rejects_transport_before_backend_sort_dispatch(monkeypatch):
    """The visitor checks lineage on real ``SortField`` payloads before calling Polars.

    Regression coverage for item 115: the other tests in this module drive
    ``propagate_structured_plans`` directly with a synthetic ``SimpleNamespace``, so a
    real ``SortRelNode`` (whose ``sort_fields`` are genuine ``SortField`` instances,
    not bare strings) is never exercised end-to-end elsewhere.
    """
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def sort_must_not_run(*args, **kwargs):
        raise AssertionError("backend sort received a transported physical field")

    monkeypatch.setattr(PolarsRelationSystem, "sort", sort_must_not_run)
    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.sort("payload").to_polars()


def test_aggregate_rejects_transport_before_backend_aggregate_dispatch(monkeypatch):
    """The visitor checks lineage on real ``AggregateRelNode`` keys before calling Polars.

    Regression coverage for item 115: exercises the ``_AGGREGATE`` policy's
    ``vars(node)`` walk (which includes the node's own ``input`` child relation
    alongside ``keys``/``measures``) against a real relation, not a synthetic
    ``SimpleNamespace``.
    """
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def aggregate_must_not_run(*args, **kwargs):
        raise AssertionError("backend aggregate received a transported physical field")

    monkeypatch.setattr(PolarsRelationSystem, "aggregate", aggregate_must_not_run)
    relation = ma.relation(pl.DataFrame({"payload": ["[1]"], "other": [1]})).conform(
        TypeSpec(
            fields=[
                FieldSpec(name="payload", type=UniversalType.ARRAY),
                FieldSpec(name="other", type=UniversalType.INTEGER),
            ]
        )
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.group_by("payload").agg(ma.col("other").sum()).to_polars()

def test_open_conform_preserves_incoming_structured_transport_lineage():
    """An open conform keeps a transported field it does not redeclare."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    first = ma.relation(pl.DataFrame({"payload": ["[1]"], "other": [1]})).conform(
        TypeSpec(
            fields_match="open",
            fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
        ),
        contract={"data_type": "coerce"},
    )
    second = first.conform(
        TypeSpec(
            fields_match="open",
            fields=[FieldSpec(name="other", type=UniversalType.INTEGER)],
        ),
        contract={"data_type": "coerce"},
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        second.filter(ma.col("payload").is_not_null()).to_polars()

    from mountainash.relations import LogicalTerminalRequired

    with pytest.raises(LogicalTerminalRequired):
        second.collect()

def test_with_columns_overwrite_clears_stale_transport_lineage():
    """Replacing a transported output with a computed value drops its old plan."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )

    result = relation.with_columns(ma.lit("not-json").alias("payload")).to_polars()

    assert result["payload"].to_list() == ["not-json"]

def test_native_with_columns_overwrite_rejects_when_transport_is_active():
    """Raw backend expressions fail closed while a transported field is carried."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    relation = ma.relation(pl.DataFrame({"payload": ["[1]"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.with_columns(pl.lit("not-json").alias("payload")).to_polars()


def test_join_resolves_ref_left_output_names_for_suffix():
    """A ref-backed left relation still participates in join suffix detection."""
    import polars as pl

    from mountainash.relations.dag import RelationDAG
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    dag = RelationDAG()
    dag.add("left", ma.relation(pl.DataFrame({"id": [1], "payload": ["left"]})))
    dag.add(
        "right",
        ma.relation(pl.DataFrame({"id": [1], "payload": ["[2]"]})).conform(
            TypeSpec(
                fields_match="open",
                fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
            )
        ),
    )

    result = dag.ref("left").join(dag.ref("right"), on="id").to_polars()

    assert result["payload"].to_list() == ["left"]
    assert result["payload_right"].to_list() == [[2]]


def test_direct_ref_join_does_not_replay_resolution_for_lineage():
    """Polars visitor lifecycle wiring; DAG execution separately covers adoption."""
    import polars as pl

    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    left = ma.relation(pl.DataFrame({"id": [1], "payload": ["left"]}))
    right = ma.relation(pl.DataFrame({"id": [1], "payload": ["[2]"]})).conform(
        TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )
    left_value, visitor = left._compile_and_execute_with_visitor()
    visitor = type(visitor)(visitor.backend, visitor.expr_visitor, execution_context=visitor.execution_context)
    right_value, right_visitor = right._compile_and_execute_with_visitor()
    calls = []

    class Resolver:
        def __call__(self, name):
            calls.append(name)
            return {"left": left_value, "right": right_value}[name]

        def structured_plans(self, name):
            return right_visitor.structured_field_plans if name == "right" else {}

    visitor.ref_resolver = Resolver()
    joined = Relation(RefRelNode(name="left")).join(Relation(RefRelNode(name="right")), on="id")
    native = visitor.visit(joined._node)
    result = joined._polars_from_compiled(native, visitor)
    assert result["payload"].to_list() == ["left"]
    assert result["payload_right"].to_list() == [[2]]
    assert calls == ["left", "right"]


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "narwhals-pandas", "ibis-duckdb"])
def test_right_join_suffixes_right_side_transport(backend_name, backend_factory):
    """RIGHT joins name columns like every other join: the right field takes the suffix."""
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    left_source, right_source = backend_factory.create_pair(
        {"id": [1], "payload": ["[1]"]}, {"id": [1], "payload": ["[2]"]}, backend_name,
    )
    left = ma.relation(left_source)
    right = ma.relation(right_source).conform(
        TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    )

    result = left.join(right, on="id", how="right").to_dicts()

    assert result == [{"id": 1, "payload": "[1]", "payload_right": [2]}]


def test_lineage_multi_clash_order_matches_execution():
    """`_n` increments follow right-column order in lineage exactly as in execution."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    left = ma.relation(pl.DataFrame({"id": [1], "a": ["x"], "a_1": ["y"]}))
    right = ma.relation(pl.DataFrame({"id": [1], "a_1": ["[5]"], "a": ["[7]"]})).conform(
        TypeSpec(fields_match="open", fields=[FieldSpec(name="a", type=UniversalType.ARRAY)])
    )
    rel = left.join(right, on="id", suffix="_1")
    assert rel.columns == ["id", "a", "a_1", "a_1_1", "a_1_2"]
    out = rel.to_polars()
    assert out["a_1_2"].to_list() == [[7]]
    assert out["a_1_1"].to_list() == ["[5]"]


def test_nested_join_lineage_tracks_each_level():
    """Nested joins on the same fields decode each level under its own name."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="p", type=UniversalType.ARRAY)])
    base = ma.relation(pl.DataFrame({"id": [1], "p": ["[0]"]})).conform(spec)
    lookup = ma.relation(pl.DataFrame({"id": [1], "p": ["[9]"]})).conform(spec)
    rel = base.join(lookup, on="id").join(lookup, on="id")
    assert rel.columns == ["id", "p", "p_right", "p_right_1"]
    assert rel.to_dicts() == [{"id": 1, "p": [0], "p_right": [9], "p_right_1": [9]}]


def test_join_tracks_right_transport_under_backend_suffix():
    """A colliding right-side transported field is decoded under payload_right."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    left = ma.relation(pl.DataFrame({"id": [1], "payload": ["left"]}))
    right = ma.relation(pl.DataFrame({"id": [1], "payload": ["[2]"]})).conform(
        TypeSpec(
            fields_match="open",
            fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
        )
    )

    result = left.join(right, on="id").to_polars()

    assert result["payload"].to_list() == ["left"]
    assert result["payload_right"].to_list() == [[2]]

def test_join_asof_rejects_transport_used_as_group_key(monkeypatch):
    """A transported ``by`` key is rejected before join-asof dispatch."""
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def join_asof_must_not_run(*args, **kwargs):
        raise AssertionError("backend join_asof received a transported group key")

    monkeypatch.setattr(PolarsRelationSystem, "join_asof", join_asof_must_not_run)
    left = ma.relation(
        pl.DataFrame({"time": [1], "payload": ["[1]"]})
    ).conform(
        TypeSpec(
            fields_match="open",
            fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
        )
    )
    right = ma.relation(pl.DataFrame({"time": [1], "payload": ["[1]"]}))

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        left.join_asof(right, on="time", by="payload").to_polars()

def test_drop_nulls_without_subset_rejects_every_transported_field(monkeypatch):
    """An implicit all-column drop-nulls consumer cannot inspect a carrier."""
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def drop_nulls_must_not_run(*args, **kwargs):
        raise AssertionError("backend drop_nulls received a transported field")

    monkeypatch.setattr(PolarsRelationSystem, "drop_nulls", drop_nulls_must_not_run)
    relation = ma.relation(pl.DataFrame({"payload": ["{broken"]})).conform(
        TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]),
        contract={"data_type": "discard_value"},
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.drop_nulls().to_polars()

def test_unpivot_preserves_transport_on_explicit_index():
    """An index carrier survives unpivot while value columns are melted."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    relation = ma.relation(
        pl.DataFrame({"payload": ["[1]", "[2]"], "metric": [10, 20]})
    ).conform(
        TypeSpec(
            fields=[
                FieldSpec(name="payload", type=UniversalType.ARRAY),
                FieldSpec(name="metric", type=UniversalType.INTEGER),
            ]
        )
    )

    result = relation.unpivot(on="metric", index="payload").to_polars()

    assert result["payload"].to_list() == [[1], [2]]

def test_join_keeps_both_transport_plans_when_right_name_collides():
    """Both colliding carriers remain tracked under their final output names."""
    import polars as pl

    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)],
    )
    left = ma.relation(pl.DataFrame({"id": [1], "payload": ["[1]"]})).conform(spec)
    right = ma.relation(pl.DataFrame({"id": [1], "payload": ["[2]"]})).conform(spec)

    result = left.join(right, on="id").to_polars()

    assert result["payload"].to_list() == [[1]]
    assert result["payload_right"].to_list() == [[2]]


def test_unpivot_rejects_transport_used_as_value(monkeypatch):
    """A transported ``on`` field is rejected before unpivot dispatch."""
    import polars as pl

    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    def unpivot_must_not_run(*args, **kwargs):
        raise AssertionError("backend unpivot received a transported value")

    monkeypatch.setattr(PolarsRelationSystem, "unpivot", unpivot_must_not_run)
    relation = ma.relation(
        pl.DataFrame({"payload": ["[1]"], "metric": [10]})
    ).conform(
        TypeSpec(
            fields=[
                FieldSpec(name="payload", type=UniversalType.ARRAY),
                FieldSpec(name="metric", type=UniversalType.INTEGER),
            ]
        )
    )

    with pytest.raises(UnsupportedStructuredTransportUse, match="payload"):
        relation.unpivot(on="payload", index="metric").to_polars()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_opaque_aggregate_join_never_guesses_carrier_collision(backend_name, backend_factory):
    import ibis

    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    left_source, right_source = backend_factory.create_pair(
        {"id": [1, 1], "payload": [2, 3]}, {"id": [1], "payload": ["[7]"]}, backend_name,
    )
    native = ma.col("payload").sum().compile(left_source)
    if isinstance(native, ibis.Deferred):
        native = native.resolve(left_source)
    left = ma.relation(left_source).group_by("id").agg(ma.native(native).alias("payload"))
    assert left.to_dicts() == [{"id": 1, "payload": 5}]
    right = ma.relation(right_source).conform(
        TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)]),
    )
    try:
        rows = left.join(right, on="id").to_dicts()
    except IncompleteProjectionSchemaError:
        # Metadata needs complete names; failing explicitly is safe.
        return
    assert rows == [{"id": 1, "payload": 5, "payload_right": [7]}]
