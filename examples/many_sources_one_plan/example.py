"""Combine a DuckDB table, a CSV file and plain Python data in one plan."""

import tempfile
from datetime import date
from pathlib import Path

import ibis
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
    customers_frame = pl.DataFrame(
        {
            "customer_id": [10, 11, 12],
            "name": ["Avery", "Blake", "Casey"],
            "region": ["north", "south", "east"],
        }
    )
    targets = [
        {"region": "north", "target": 100.0},
        {"region": "south", "target": 150.0},
        {"region": "east", "target": 250.0},
    ]

    with tempfile.TemporaryDirectory() as tmp:
        customers_frame.write_csv(Path(tmp) / "customers.csv")
        warehouse = ibis.duckdb.connect(str(Path(tmp) / "warehouse.duckdb"))
        warehouse.create_table("orders", orders.to_arrow())

        orders_table = warehouse.table("orders")  # database table
        customers = pl.read_csv(Path(tmp) / "customers.csv")  # local file

        report = (
            ma.relation(orders_table)
            .join(customers, on="customer_id")
            .group_by("region")
            .agg(ma.col("amount").sum().alias("revenue"))
            .join(targets, on="region")
            .with_columns((ma.col("revenue") >= ma.col("target")).alias("on_target"))
            .sort("region")
        )
        result = report.to_polars().sort("region")
        explain = report.explain()
        warehouse.disconnect()

    print(result)
    for line in explain.splitlines():
        if line.strip().startswith("transfer"):
            print(line.strip())

    compute_lines = [
        line for line in explain.splitlines()
        if " on " in line and "ReadRelNode" not in line
    ]
    assert compute_lines
    assert all(" on ibis-duckdb " in line for line in compute_lines)
    assert result["region"].to_list() == ["east", "north", "south"]
    assert result["on_target"].to_list() == [True, True, False]


if __name__ == "__main__":
    main()
