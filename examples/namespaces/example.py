"""Use the str and dt namespaces on customer names and order dates."""

from datetime import date

import ibis
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
    customers = pl.DataFrame({"customer_id": [10, 11, 12], "name": ["Avery", "Blake", "Casey"]})
    def name_columns(relation):
        return relation.select(
            "customer_id",
            ma.col("name").str.to_uppercase().alias("shout"),
            ma.col("name").str.contains("a").alias("has_a"),
        ).sort("customer_id").to_dicts()

    names = name_columns(ma.relation(customers))
    duck = ibis.duckdb.connect()
    on_duckdb = name_columns(ma.relation(duck.create_table("customers", customers.to_arrow())))
    assert on_duckdb == names
    dates = ma.relation(orders_frame()).select(
        "order_id",
        ma.col("ordered_at").dt.year().alias("year"),
        ma.col("ordered_at").dt.add_months(1).alias("renewal"),
        ma.col("ordered_at").dt.strftime("%d %b %Y").alias("label"),
    ).sort("order_id").to_dicts()

    assert names[0]["shout"] == "AVERY"
    assert dates[0]["renewal"] == date(2026, 2, 5)
    assert dates[0]["label"] == "05 Jan 2026"
    for row in names:
        print(row)
    for row in dates[:3]:
        print({**row, "renewal": row["renewal"].isoformat()})


if __name__ == "__main__":
    main()
