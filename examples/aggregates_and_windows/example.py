"""Group, aggregate and window the orders on Polars and Ibis DuckDB."""

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



def run(source) -> tuple[list[dict], list[dict]]:
    totals = (
        ma.relation(source)
        .group_by("customer_id")
        .agg(
            ma.col("amount").sum().alias("total"),
            ma.col("amount").count().alias("amounts_seen"),
            ma.count_records().alias("orders"),
        )
        .sort("customer_id")
        .to_dicts()
    )
    windowed = (
        ma.relation(source)
        .with_columns(ma.col("amount").sum().over("customer_id").alias("customer_total"))
        .select("order_id", "customer_id", "customer_total")
        .sort("order_id")
        .to_dicts()
    )
    return totals, windowed


def main() -> None:
    import ibis

    orders = orders_frame()
    con = ibis.duckdb.connect()
    orders_db = con.create_table("orders", orders.to_arrow())

    polars_result = run(orders)
    duckdb_result = run(orders_db)
    assert polars_result == duckdb_result

    totals, windowed = polars_result
    assert totals[0] == {"customer_id": 10, "total": 120.0, "amounts_seen": 1, "orders": 2}
    print("group_by")
    for row in totals:
        print(row)
    print("over")
    for row in windowed:
        print(row)


if __name__ == "__main__":
    main()
