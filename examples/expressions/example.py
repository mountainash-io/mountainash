"""Build expressions with operators, conditions, casts and null handling."""

from datetime import date

import mountainash as ma
import polars as pl


def orders_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6],
            "customer_id": [10, 11, 10, 12, 11, 12],
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0],
            "status": ["shipped", "pending", "shipped", "cancelled", "shipped", "pending"],
            "ordered_at": [
                date(2026, 1, 5), date(2026, 1, 9), date(2026, 2, 2),
                date(2026, 2, 14), date(2026, 3, 1), date(2026, 3, 20),
            ],
        }
    )



def main() -> None:
    plan = ma.relation(orders_frame()).select(
        "order_id",
        (ma.col("amount") * 1.1).alias("with_tax"),
        ma.when(ma.col("amount") >= 100).then("large").otherwise("small").alias("size"),
        ma.col("amount").fill_null(0.0).cast("i64").alias("whole"),
        (ma.col("amount").is_between(60, 130) & (ma.col("status") != "cancelled")).alias("mid_open"),
    ).sort("order_id")
    rows = plan.to_dicts()

    by_id = {row["order_id"]: row for row in rows}
    assert by_id[3]["with_tax"] is None
    assert by_id[3]["whole"] == 0
    assert by_id[3]["size"] == "small"
    assert by_id[1]["size"] == "large"
    for row in rows:
        print({
            "order_id": row["order_id"],
            "with_tax": None if row["with_tax"] is None else round(row["with_tax"], 2),
            "size": row["size"],
            "whole": row["whole"],
            "mid_open": row["mid_open"],
        })


if __name__ == "__main__":
    main()
