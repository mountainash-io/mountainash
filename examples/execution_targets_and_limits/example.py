"""Choose where a join runs, then meet a backend limit and a capability policy."""

import ibis
import mountainash as ma
import polars as pl
from mountainash.exceptions import BackendCapabilityError


def main() -> None:
    orders = pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6],
            "customer_id": [10, 11, 10, 12, 11, 12],
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0],
        }
    )
    customers = pl.DataFrame(
        {"customer_id": [10, 11, 12], "name": ["Avery", "Blake", "Casey"]}
    )

    con = ibis.duckdb.connect()
    orders_db = con.create_table("orders", orders.to_arrow())

    # Placement: by default a join runs where its left input lives.
    on_duckdb = ma.relation(orders_db).join(ma.relation(customers), on="customer_id")
    on_polars = ma.relation(orders_db).join(
        ma.relation(customers), on="customer_id", execute_on="right"
    )
    print("default placement:")
    print(on_duckdb.explain())
    print("execute_on='right':")
    print(on_polars.explain())
    print("result types:", type(on_duckdb.collect()).__module__.split(".")[0],
          type(on_polars.collect()).__module__.split(".")[0])

    # A limit: exact-count sampling with a seed is refused on Ibis.
    numbers = con.create_table("numbers", pl.DataFrame({"n": range(100)}).to_arrow())
    sampled = ma.relation(numbers).sample(n=5, seed=7)
    try:
        sampled.to_polars()
    except BackendCapabilityError as exc:
        print("refused:", exc)
        print("dialect and parameter:", exc.limitation.dialect, exc.limitation.param)
    else:
        raise AssertionError("seeded exact sampling should be refused on Ibis")

    # The refusal gate is classed UNCLASSIFIED, so a policy that protects only
    # AVAILABILITY does not cover it and the call runs. The price: the seed is
    # no longer honoured, so repeated runs draw different rows.
    only_availability = ma.CapabilityPolicy(
        protection=frozenset({ma.CapabilityIssueClass.AVAILABILITY})
    )
    with ma.capability_policy(only_availability):
        draws = {tuple(row["n"] for row in sampled.to_dicts()) for _ in range(20)}
    print("rows per draw under a narrower policy:", {len(d) for d in draws})
    print("seed honoured (draws identical):", len(draws) == 1)

    assert "root: JoinRelNode on ibis-duckdb" in on_duckdb.explain()
    assert "root: JoinRelNode on polars" in on_polars.explain()
    assert len(draws) > 1
    con.disconnect()


if __name__ == "__main__":
    main()
