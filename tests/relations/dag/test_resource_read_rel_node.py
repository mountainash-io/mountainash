from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    ResourceReadRelNode,
)
from mountainash.typespec.datapackage import DataResource


def test_resource_read_rel_node_holds_resource():
    res = DataResource(name="orders", path="orders.csv", format="csv")
    node = ResourceReadRelNode(resource=res)
    assert node.resource is res


def test_resource_read_applies_raw_schema_by_default():
    res = DataResource(name="orders", data=[{"n": "1"}])
    node = ResourceReadRelNode(resource=res)
    assert node.apply_schema_conform is True


def test_validation_copy_suppresses_builtin_conform():
    res = DataResource(name="orders", data=[{"n": "1"}])
    node = ResourceReadRelNode(resource=res)
    validation_node = node.model_copy(update={"apply_schema_conform": False})
    assert validation_node.apply_schema_conform is False






def test_validation_relation_copy_disables_schema_conform():
    from mountainash.relations.core.relation_api.relation import Relation

    res = DataResource(name="orders", data=[{"n": "1"}])
    node = ResourceReadRelNode(resource=res)
    validation_relation = Relation(node)._without_resource_schema_conform()

    assert node.apply_schema_conform is True
    assert validation_relation._node.apply_schema_conform is False




def test_validation_copy_applies_one_compiled_conform_plan(monkeypatch):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    calls = 0
    original = UnifiedRelationVisitor.apply_conform

    def counted(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        return original(self, *args, **kwargs)

    monkeypatch.setattr(UnifiedRelationVisitor, "apply_conform", counted)
    spec = TypeSpec(
        fields=[FieldSpec(name="n", type=UniversalType.INTEGER)],
        fields_match="open",
    )
    resource = DataResource(
        name="orders",
        type="table",
        data=[{"n": "1"}],
        schema=spec,
    )
    relation = Relation(
        ResourceReadRelNode(resource=resource),
    )._without_resource_schema_conform().conform(spec)

    RelationDAG().execute(relation, backend="polars")

    assert calls == 1


def test_resource_read_validation_copy_skips_builtin_conform():
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.relations.core.relation_protocols.relsys_base import (
        get_relation_system,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    backend = CONST_BACKEND.POLARS
    rel_sys = get_relation_system(backend)()
    expr_sys = get_expression_system(backend)()
    visitor = UnifiedRelationVisitor(
        rel_sys,
        UnifiedExpressionVisitor(expr_sys),
    )
    calls = []
    visitor.apply_conform = lambda *args, **kwargs: calls.append((args, kwargs))
    spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])
    res = DataResource(name="orders", data=[{"n": "1"}], schema=spec)
    node = ResourceReadRelNode(
        resource=res,
        apply_schema_conform=False,
    )

    visitor.visit(node)

    assert calls == []


def test_resource_read_rel_node_dispatches():
    """ResourceReadRelNode.accept() routes through visitor.visit() (registry dispatch)."""
    seen = []

    class V:
        def visit(self, node):
            seen.append(node.resource.name)
            return "visited"

    res = DataResource(name="orders", path="orders.csv")
    assert ResourceReadRelNode(resource=res).accept(V()) == "visited"
    assert seen == ["orders"]


def test_resource_read_rel_node_threads_resource_name_into_drift():
    """item 48 Task 7: _visit_resource_read_rel passes resource.name through
    to apply_conform(resource_name=...), which lands on the ConformDrift."""
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.relations.core.relation_protocols.relsys_base import (
        get_relation_system,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    backend = CONST_BACKEND.POLARS
    rel_sys = get_relation_system(backend)()
    expr_sys = get_expression_system(backend)()
    expr_visitor = UnifiedExpressionVisitor(expr_sys)
    visitor = UnifiedRelationVisitor(rel_sys, expr_visitor)

    spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])
    res = DataResource(name="orders", type="table", data=[{"n": "1"}, {"n": "2"}], schema=spec)
    node = ResourceReadRelNode(resource=res)

    visitor.visit(node)

    assert len(visitor.drift_reports) == 1
    assert visitor.drift_reports[0].resource_name == "orders"
