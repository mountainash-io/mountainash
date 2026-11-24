"""Load a DataPackage as a RelationDAG, derive a relation, check its foreign key and export it."""

import tempfile
from pathlib import Path

import mountainash as ma


def main() -> None:
    package = ma.DataPackage.from_path(Path(__file__).parent / "datapackage.json")
    shop = package.to_relation_dag()
    print("resources:", sorted(shop.relations))
    print("constraint edges:", shop.constraint_edges)

    shop.add(
        "order_totals",
        shop.ref("orders").group_by("customer_id").agg(ma.col("amount").sum().alias("total")),
    )
    totals = shop.ref("order_totals").sort("customer_id").to_dicts()
    for row in totals:
        print(row)
    assert totals[0] == {"customer_id": 10, "total": 120.0}

    specs = {r.name: r.to_table_schema() for r in package.resources}
    result = shop.validate(specs)
    print("foreign keys pass:", result.fk_result.passes)
    for case in result.fk_result.failure_cases.to_dicts():
        print(case["check_id"], case["row"]["customer_id"])
    assert not result.fk_result.passes

    exported = shop.to_package()
    names = sorted(resource.name for resource in exported.resources)
    print("exported:", names)
    assert "order_totals" in names

    with tempfile.TemporaryDirectory() as tmp:
        exported.write(Path(tmp) / "datapackage.json")
        again = ma.DataPackage.from_path(Path(tmp) / "datapackage.json")
        print("round trip:", sorted(r.name for r in again.resources))
        assert sorted(r.name for r in again.resources) == names


if __name__ == "__main__":
    main()
