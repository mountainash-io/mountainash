"""Run one function on a local Parquet extract with Polars, then on a DuckDB table."""

import tempfile
from datetime import date
from pathlib import Path

import ibis
import mountainash as ma
import polars as pl


def customer_revenue(orders):
    return (
        ma.relation(orders)
        .filter(ma.col("amount").is_not_null())
        .group_by("customer_id")
        .agg(ma.col("amount").sum().alias("revenue"))
        .sort("customer_id")
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

    with tempfile.TemporaryDirectory() as tmp:
        extract_path = Path(tmp) / "orders_extract.parquet"
        orders.head(4).write_parquet(extract_path)

        warehouse = ibis.duckdb.connect(str(Path(tmp) / "warehouse.duckdb"))
        warehouse.create_table("orders", orders.to_arrow())

        dev_result = customer_revenue(pl.read_parquet(extract_path)).to_dicts()
        prod_table = warehouse.table("orders")
        prod_result = customer_revenue(prod_table).to_dicts()
        prod_first_four = customer_revenue(
            prod_table.filter(prod_table.order_id <= 4)
        ).to_dicts()
        warehouse.disconnect()

    print("dev: ", dev_result)
    print("prod:", prod_result)

    assert dev_result == prod_first_four
    assert dev_result != prod_result


if __name__ == "__main__":
    main()
