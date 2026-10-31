"""Explain a plan, compare fingerprints across engines and freeze a snapshot."""

import ibis
import mountainash as ma
import polars as pl


def main() -> None:
    orders = pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6],
            "customer_id": [10, 11, 10, 12, 11, 12],
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0],
        }
    )

    con = ibis.duckdb.connect()
    orders_db = con.create_table("orders", orders.to_arrow())

    def large(source):
        return ma.relation(source).filter(ma.col("amount") > 90).select("order_id", "amount")

    polars_plan = large(orders)
    sql_plan = large(orders_db)

    print("polars plan:")
    for line in polars_plan.explain().splitlines():
        print("  " + line)
    print("sql plan:")
    for line in sql_plan.explain().splitlines():
        print("  " + line)

    keys, values = ["order_id"], ["amount", "customer_id"]
    local = ma.relation(orders).fingerprint(keys=keys, columns=values)
    remote = ma.relation(orders_db).fingerprint(keys=keys, columns=values)
    print("same content, different engines:", local.equals(remote))

    changed = ma.relation(orders.with_columns(pl.col("amount") + 1)).fingerprint(
        keys=keys, columns=values
    )
    print("changed amounts:", local.equals(changed))

    live = large(orders_db)
    frozen = live.snapshot()
    con.insert(
        "orders",
        pl.DataFrame({"order_id": [7], "customer_id": [10], "amount": [500.0]}).to_arrow(),
    )
    print("rows, snapshot vs live:", frozen.count_rows(), live.count_rows())

    assert local.equals(remote)
    assert not local.equals(changed)
    assert frozen.count_rows() == 3
    assert live.count_rows() == 4
    con.disconnect()


if __name__ == "__main__":
    main()
