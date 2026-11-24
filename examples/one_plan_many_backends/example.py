"""Run one plan function on a Polars frame, a pandas frame and an Ibis DuckDB table."""

from datetime import date

import ibis
import mountainash as ma
import polars as pl


def revenue_by_region(source):
    return (
        ma.relation(source)
        .filter(ma.col("amount").is_not_null())
        .join(
            pl.DataFrame(
                {
                    "customer_id": [10, 11, 12],
                    "region": ["north", "south", "east"],
                }
            ),
            on="customer_id",
        )
        .group_by("region")
        .agg(ma.col("amount").sum().alias("revenue"))
        .sort("region")
    )


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
    connection = ibis.duckdb.connect()
    sources = {
        "polars": orders,
        "pandas": orders.to_pandas(),
        "ibis-duckdb": connection.create_table("orders", orders.to_arrow()),
    }

    results = {}
    for backend, source in sources.items():
        results[backend] = revenue_by_region(source).to_dicts()
        print(f"{backend}: {results[backend]}")

    assert results["polars"] == results["pandas"] == results["ibis-duckdb"]


if __name__ == "__main__":
    main()
