"""Run row, scalar and relation rules, then check a foreign key from orders to customers."""

from datetime import date

import mountainash as ma
import polars as pl
from mountainash.validation import (
    ForeignKeyRule,
    RelationRule,
    RowRule,
    ScalarRule,
    ValidationRunner,
    resolve_identity,
)


def main() -> None:
    orders = pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6, 7],
            "customer_id": [10, 11, 10, 12, 11, 12, 99],
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0, -5.0],
            "status": ["shipped", "pending", "shipped", "cancelled", "shipped", "pending", "shipped"],
            "ordered_at": [
                date(2026, 1, 5), date(2026, 1, 9), date(2026, 2, 2), date(2026, 2, 14),
                date(2026, 3, 1), date(2026, 3, 20), date(2026, 4, 2),
            ],
        }
    )
    customers = pl.DataFrame(
        {"customer_id": [10, 11, 12], "name": ["Avery", "Blake", "Casey"], "region": ["north", "south", "east"]}
    )

    rules = [
        RowRule(id="amount_non_negative", expr=ma.col("amount").ge(0), fields=["amount"]),
        ScalarRule(id="largest_order_under_500", expr=ma.col("amount").max().lt(500)),
        RelationRule(
            id="order_id_unique",
            plan=lambda rel: rel.group_by("order_id")
            .agg(ma.count_records().alias("n"))
            .filter(ma.col("n").gt(1)),
        ),
    ]
    runner = ValidationRunner()
    result = runner.validate_relation(
        ma.relation(orders), rules, identity=resolve_identity(natural_key=["order_id"])
    )
    for row in result.check_summaries.sort("check_id").select(
        "check_id", "check_kind", "status", "pass_count", "fail_count", "unknown_count"
    ).to_dicts():
        print(row)

    for row in result.failure_cases.sort("check_id", "order_id").select(
        "check_id", "outcome", "order_id", "value"
    ).to_dicts():
        print(row)

    dag = ma.RelationDAG()
    dag.add("customers", ma.relation(customers))
    dag.add("orders", ma.relation(orders))
    orders_fk = ForeignKeyRule(
        id="orders_customer",
        child="orders",
        parent="customers",
        child_fields=["customer_id"],
        parent_fields=["customer_id"],
    )
    dag_result = runner.validate_dag(dag, {"orders": [orders_fk]})
    failures = dag_result.fk_result.failure_cases.sort("row")
    print("foreign key passes:", dag_result.passes)
    for row in failures.to_dicts():
        print({"check_id": row["check_id"], "outcome": row["outcome"],
               "order_id": row["row"]["order_id"], "customer_id": row["row"]["customer_id"]})

    by_check = {row["check_id"]: row for row in result.check_summaries.to_dicts()}
    assert by_check["amount_non_negative"]["fail_count"] == 1
    assert by_check["amount_non_negative"]["unknown_count"] == 1
    assert by_check["largest_order_under_500"]["status"] == "passed"
    assert by_check["order_id_unique"]["status"] == "passed"
    assert not dag_result.passes
    assert failures.height == 1


if __name__ == "__main__":
    main()
