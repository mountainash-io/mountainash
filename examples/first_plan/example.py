"""Build a relation plan on the shared orders table and collect the result."""

from datetime import date

import mountainash as ma
import polars as pl


def main() -> None:
    orders = pl.DataFrame(
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

    plan = (
        ma.relation(orders)
        .filter(ma.col("status") == "shipped")
        .with_columns((ma.col("amount") * 1.1).alias("amount_with_tax"))
        .select("order_id", "amount", "amount_with_tax")
        .sort("order_id")
    )
    rows = plan.to_dicts()

    assert [row["order_id"] for row in rows] == [1, 3, 5]
    assert rows[1]["amount_with_tax"] is None
    for row in rows:
        print({key: None if value is None else round(value, 2) if isinstance(value, float) else value
               for key, value in row.items()})


if __name__ == "__main__":
    main()
