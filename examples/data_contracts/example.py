"""Declare a data contract on orders and read the result per check."""

from datetime import date

import mountainash as ma
import polars as pl
from mountainash.datacontracts import BaseDataContract, Rule, RuleRegistry, Validator, guarded


class Orders(BaseDataContract):
    order_id = ma.FieldDefinition(dtype=ma.MountainashDtype.I64, required=True)
    customer_id = ma.FieldDefinition(dtype=ma.MountainashDtype.I64)
    amount = ma.FieldDefinition(dtype=ma.MountainashDtype.FP64)
    status = ma.FieldDefinition(
        dtype=ma.MountainashDtype.STRING, enum=["shipped", "pending", "cancelled"]
    )

    ordered_at = ma.FieldDefinition(dtype=ma.MountainashDtype.DATE)

    class Config:
        name = "orders"
        natural_key = ["order_id"]


def main() -> None:
    orders = pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6, 7],
            "customer_id": [10, 11, 10, 12, 11, 12, 10],
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0, -5.0],
            "status": ["shipped", "pending", "shipped", "cancelled", "shipped", "pending", "lost"],
            "ordered_at": [
                date(2026, 1, 5), date(2026, 1, 9), date(2026, 2, 2), date(2026, 2, 14),
                date(2026, 3, 1), date(2026, 3, 20), date(2026, 4, 2),
            ],
        }
    )

    rules = RuleRegistry(
        [
            Rule("amount_positive", expr=ma.col("amount").gt(0)),
            Rule(
                "shipped_has_amount",
                expr=guarded(ma.col("status").eq("shipped"), ma.col("amount").gt(0)),
            ),
            Rule(
                "shipped_has_amount_lenient",
                expr=guarded(ma.col("status").eq("shipped"), ma.col("amount").gt(0)),
                booleanizer="t_maybe_true",
            ),
        ]
    )
    result = Validator(name="orders_check", contract=Orders, rules=rules).validate(orders)

    summaries = result.check_summaries.sort("check_id")
    type_format = summaries.filter(pl.col("check_id").str.ends_with("_type_format"))
    assert type_format.height > 0
    assert type_format["status"].to_list() == ["passed"] * type_format.height
    shown = summaries.filter(~pl.col("check_id").str.ends_with("_type_format"))
    for row in shown.select("check_id", "status", "pass_count", "fail_count", "unknown_count").to_dicts():
        print(row)

    by_check = {row["check_id"]: row for row in summaries.to_dicts()}
    assert not result.passes
    assert by_check["amount_positive"]["fail_count"] == 1
    assert by_check["amount_positive"]["unknown_count"] == 1
    assert by_check["shipped_has_amount"]["fail_count"] == 0
    assert by_check["shipped_has_amount"]["unknown_count"] == 1
    assert by_check["shipped_has_amount"]["status"] == "failed"
    assert by_check["shipped_has_amount_lenient"]["status"] == "passed"
    assert by_check["status_enum_membership"]["fail_count"] == 1


if __name__ == "__main__":
    main()
