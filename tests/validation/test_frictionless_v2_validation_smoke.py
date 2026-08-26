"""End-to-end Frictionless package → DAG validation smoke proof."""

import mountainash as ma

from mountainash.typespec import DataPackage, DataResource, FieldConstraints, FieldSpec, ForeignKey, ForeignKeyReference, TypeSpec, UniversalType


def test_frictionless_v2_validation_smoke() -> None:
    """An invalid foreign key survives package construction and DAG validation."""
    customers = TypeSpec(
        fields=[FieldSpec(name="id", type=UniversalType.INTEGER, constraints=FieldConstraints(required=True))],
        primary_key=["id"],
    )
    orders = TypeSpec(
        fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="customer_id", type=UniversalType.INTEGER),
        ],
        primary_key=["id"],
        foreign_keys=[
            ForeignKey(
                fields=["customer_id"],
                reference=ForeignKeyReference(resource="customers", fields=["id"]),
            )
        ],
    )
    package = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "customers",
                    "type": "table",
                    "data": [{"id": 1}],
                    "schema": customers.to_frictionless(),
                },
                {
                    "name": "orders",
                    "type": "table",
                    "data": [{"id": 10, "customer_id": 99}],
                    "schema": orders.to_frictionless(),
                },
            ]
        }
    )
    dag = package.to_relation_dag()
    dag.add("active_orders", dag.ref("orders").filter(ma.col("id").gt(0)))

    result = dag.validate(
        {"customers": customers, "orders": orders, "active_orders": orders}
    )

    assert set(result.results) == {"customers", "orders", "active_orders"}
    assert result.results["customers"].passes
    assert not result.fk_result.passes
    assert dag.dependency_edges == {("orders", "active_orders")}
    assert ("customers", "orders") in dag.constraint_edges
