"""Join orders to customers four ways and stack two relations with concat."""

from datetime import date

import mountainash as ma
import polars as pl


def main() -> None:
    orders = pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6, 7],
            "customer_id": [10, 11, 10, 12, 11, 12, 99],  # order 7: unknown customer
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0, 30.0],
            "status": ["shipped", "pending", "shipped", "cancelled", "shipped", "pending", "pending"],
            "ordered_at": [
                date(2026, 1, 5), date(2026, 1, 9), date(2026, 2, 2),
                date(2026, 2, 14), date(2026, 3, 1), date(2026, 3, 20), date(2026, 3, 25),
            ],
        }
    )
    customers = pl.DataFrame(
        {
            "customer_id": [10, 11, 12, 13],  # customer 13 has no orders
            "name": ["Avery", "Blake", "Casey", "Drew"],
            "region": ["north", "south", "east", "west"],
        }
    )

    orders_plan = ma.relation(orders)
    customers_plan = ma.relation(customers)

    def ids(plan) -> list[int]:
        return sorted(row["order_id"] for row in plan.to_dicts())

    inner = orders_plan.join(customers_plan, on="customer_id", how="inner")
    left = orders_plan.join(customers_plan, on="customer_id", how="left")
    semi = orders_plan.join(customers_plan, on="customer_id", how="semi")
    anti = orders_plan.join(customers_plan, on="customer_id", how="anti")

    print("inner", ids(inner))
    print("left ", ids(left))
    print("semi ", ids(semi))
    print("anti ", ids(anti))
    print("left, order 7 name:", [r["name"] for r in left.to_dicts() if r["order_id"] == 7])
    print("semi columns:", semi.columns)

    late = ma.relation(orders.head(2).with_columns(pl.col("order_id") + 100))
    stacked = ma.concat([orders_plan.select("order_id", "amount"), late.select("order_id", "amount")])
    print("concat rows:", stacked.count_rows())
    print("concat order ids:", sorted(row["order_id"] for row in stacked.to_dicts()))

    assert ids(inner) == [1, 2, 3, 4, 5, 6]
    assert ids(left) == [1, 2, 3, 4, 5, 6, 7]
    assert ids(semi) == ids(inner)
    assert ids(anti) == [7]
    assert semi.columns == orders_plan.columns
    assert stacked.count_rows() == 9


if __name__ == "__main__":
    main()
