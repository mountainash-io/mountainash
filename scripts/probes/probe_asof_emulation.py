"""Version-stamped probe for the item-108 Ibis asof dispatch (spec §9.3).
Run: hatch run test:python scripts/probes/probe_asof_emulation.py
"""
from __future__ import annotations
from datetime import datetime, timedelta

import duckdb
import ibis
import polars as pl
import pyarrow

print(
    f"polars {pl.__version__} | ibis {ibis.__version__} | "
    f"duckdb {duckdb.__version__} | pyarrow {pyarrow.__version__}"
)


def native_asof(left, right, *, on, by, tolerance, dialect):
    """backward-only, duckdb+polars."""
    by_cols = list(by) if by else []
    if dialect == "ibis-duckdb":
        # Determinism fix (IB-REL-11 class): duckdb's ASOF JOIN has no stable
        # tiebreak for duplicate (by, on) left rows without an explicit
        # secondary sort key (probe-confirmed: order varied across 20 fresh-
        # connection reps without this). Row order for INTERLEAVED by-groups
        # still diverges from Polars even with this fix (declared: IB-REL-17)
        # -- this fixes nondeterminism, not full order parity.
        left_id = left.mutate(_ma_left_id=ibis.row_number())
        predicates = [left_id[c] == right[c] for c in by_cols]
        result = left_id.asof_join(right, on=on, predicates=predicates, tolerance=tolerance)
        on_right = f"{on}_right"
        drop = [c for c in ([on_right] + [f"{c}_right" for c in by_cols]) if c in result.columns]
        if drop:
            result = result.drop(*drop)
        return result.order_by([*by_cols, on, "_ma_left_id"]).drop("_ma_left_id")
    # ibis-polars: delegates directly to real Polars' own join_asof, which
    # already preserves left input order natively and stably (probe-
    # confirmed: 20/20 identical reps, including for interleaved by-groups) --
    # no order_by needed or wanted here.
    predicates = [left[c] == right[c] for c in by_cols]
    result = left.asof_join(right, on=on, predicates=predicates, tolerance=tolerance)
    on_right = f"{on}_right"
    drop = [c for c in ([on_right] + [f"{c}_right" for c in by_cols]) if c in result.columns]
    if drop:
        result = result.drop(*drop)
    return result


def emulate_asof(left, right, *, on, by, strategy, tolerance):
    left_cols = list(left.columns)
    right_cols = list(right.columns)
    by_cols = list(by) if by else []

    is_temporal = left[on].type().is_temporal()
    if is_temporal and isinstance(tolerance, timedelta):
        tolerance = tolerance.total_seconds()

    def _distance(a, b):
        return a.delta(b, unit="second").abs() if is_temporal else (a - b).abs()

    left_sorted = left.order_by([*by_cols, on])
    right_sorted = right.order_by([*by_cols, on])
    left_id = left_sorted.mutate(_ma_left_id=ibis.row_number())
    right_id = right_sorted.mutate(_ma_right_id=ibis.row_number())

    if strategy == "forward":
        pred = right_id[on] >= left_id[on]
    elif strategy == "backward":
        pred = right_id[on] <= left_id[on]
    else:
        pred = ibis.literal(True)
    for col in by_cols:
        pred = pred & (right_id[col] == left_id[col])
    if tolerance is not None:
        pred = pred & (_distance(right_id[on], left_id[on]) <= tolerance)

    cand = left_id.join(right_id, pred)
    on_right = f"{on}_right" if on in left_cols else on
    if strategy == "forward":
        rank_order = [cand[on_right], cand["_ma_right_id"]]
    elif strategy == "backward":
        rank_order = [ibis.desc(cand[on_right]), ibis.desc(cand["_ma_right_id"])]
    else:
        rank_order = [_distance(cand[on_right], cand[on]), ibis.desc(cand["_ma_right_id"])]

    ranked = cand.mutate(
        _ma_rank=ibis.row_number().over(ibis.window(group_by="_ma_left_id", order_by=rank_order))
    )
    right_out_cols = [c if c not in left_cols else f"{c}_right" for c in right_cols]
    best = ranked.filter(ranked["_ma_rank"] == 0).select("_ma_left_id", *right_out_cols)

    result = left_id.left_join(best, "_ma_left_id")
    drop_cols = {"_ma_left_id_right", on_right} | {f"{c}_right" for c in by_cols}
    result = result.drop(*[c for c in drop_cols if c in result.columns])
    result = result.order_by([*by_cols, on, "_ma_left_id"])
    return result.select(*[c for c in result.columns if c != "_ma_left_id"])


base = datetime(2026, 1, 1)
EMULATION_CASES = [
    ("forward", {"t": [1, 3, 5, 7], "val": ["a", "b", "c", "d"]},
     {"t": [2, 4, 6], "score": [20, 40, 60]}, "t", None, "forward", None),
    ("nearest", {"t": [1, 3, 5, 7], "val": ["a", "b", "c", "d"]},
     {"t": [2, 4, 6], "score": [20, 40, 60]}, "t", None, "nearest", None),
    ("nearest_tie", {"t": [5], "val": ["x"]}, {"t": [4, 6], "score": [40, 60]}, "t", None, "nearest", None),
    ("by_grouping_contiguous", {"g": ["a", "a", "b", "b"], "t": [1, 3, 5, 7], "val": ["a1", "a3", "b5", "b7"]},
     {"g": ["a", "a", "b", "b"], "t": [2, 4, 6, 8], "score": [20, 40, 60, 80]}, "t", ["g"], "backward", None),
    ("tolerance", {"t": [10, 20, 30], "val": ["a", "b", "c"]}, {"t": [5, 27], "score": [50, 270]}, "t", None, "backward", 2),
    ("dup_left", {"t": [5, 5], "val": ["r1", "r2"]}, {"t": [4, 6], "score": [40, 60]}, "t", None, "backward", None),
    ("null_keys", {"t": [None, 3], "val": ["n", "b"]}, {"t": [None, 2], "score": [99, 20]}, "t", None, "backward", None),
    ("temporal_nearest", {"t": [base, base + timedelta(minutes=3)], "val": ["a", "b"]},
     {"t": [base + timedelta(minutes=1), base + timedelta(minutes=4)], "score": [10, 40]}, "t", None, "nearest", None),
]

failures = 0
for name, left_d, right_d, on, by, strategy, tolerance in EMULATION_CASES:
    left_pl, right_pl = pl.DataFrame(left_d), pl.DataFrame(right_d)
    oracle = left_pl.join_asof(right_pl, on=on, by=by, strategy=strategy, tolerance=tolerance).sort([*(by or []), on]).to_dicts()
    for dialect, con in (("duckdb", ibis.duckdb.connect()), ("sqlite", ibis.sqlite.connect())):
        L = con.create_table(f"L_{name}", left_pl.to_arrow(), overwrite=True)
        R = con.create_table(f"R_{name}", right_pl.to_arrow(), overwrite=True)
        # IB-REL-14: ibis-sqlite has no TimestampDelta translation; a temporal
        # `on` column combined with nearest (distance needed) cannot compile
        # there. Confirm the expected upstream error instead of crashing --
        # this is exactly the gap the production `_emulate_asof` raises
        # BackendCapabilityError for.
        is_temporal_nearest = name == "temporal_nearest" and dialect == "sqlite"
        if is_temporal_nearest:
            try:
                emulate_asof(L, R, on=on, by=by, strategy=strategy, tolerance=tolerance).to_polars()
            except ibis.common.exceptions.OperationNotDefinedError as e:
                print(f"{name} [{dialect}] OK (confirms IB-REL-14: {type(e).__name__})")
            else:
                failures += 1
                print(f"{name} [{dialect}] MISMATCH: expected OperationNotDefinedError (IB-REL-14), got no error")
            continue
        got = emulate_asof(L, R, on=on, by=by, strategy=strategy, tolerance=tolerance).to_polars().sort([*(by or []), on]).to_dicts()
        ok = got == oracle
        failures += 0 if ok else 1
        print(f"{name} [{dialect}] {'OK' if ok else 'MISMATCH: got=' + str(got) + ' oracle=' + str(oracle)}")

# native path: determinism + Polars-parity outside the declared IB-REL-17 cells
for name, left_d, right_d, by, dialect in (
    ("native_dup_left", {"t": [5, 5], "val": ["r1", "r2"]}, {"t": [4, 6], "score": [40, 60]}, None, "ibis-duckdb"),
    ("native_temporal_tol", {"t": [base, base + timedelta(minutes=3)], "val": ["a", "b"]},
     {"t": [base + timedelta(minutes=1), base + timedelta(minutes=4)], "score": [10, 40]}, None, "ibis-duckdb"),
    (
        "native_dup_right_ascending",
        {"t": [5], "val": ["x"]},
        {"t": [4, 4, 6], "score": [41, 42, 60]},
        None,
        "ibis-duckdb",
    ),
    (
        "native_dup_right_descending",
        {"t": [5], "val": ["x"]},
        {"t": [4, 4, 6], "score": [42, 41, 60]},
        None,
        "ibis-duckdb",
    ),
    (
        "native_dup_right_exact",
        {"t": [5], "val": ["x"]},
        {"t": [5, 5, 7], "score": [51, 52, 70]},
        None,
        "ibis-duckdb",
    ),
):
    left_pl, right_pl = pl.DataFrame(left_d), pl.DataFrame(right_d)
    tol = timedelta(minutes=2) if "tol" in name else None
    oracle = left_pl.join_asof(right_pl, on="t", by=by, strategy="backward", tolerance=tol).to_dicts()
    orders = set()
    for i in range(10):
        con = ibis.duckdb.connect()
        L = con.create_table(f"n_{name}_{i}", left_pl, overwrite=True)
        R = con.create_table(f"n_{name}_{i}r", right_pl, overwrite=True)
        got = native_asof(L, R, on="t", by=by, tolerance=tol, dialect=dialect).to_polars().to_dicts()
        orders.add(tuple(str(d) for d in got))
    ok = len(orders) == 1 and list(orders)[0] == tuple(str(d) for d in oracle)
    failures += 0 if ok else 1
    print(f"{name} [{dialect}] determinism+parity: {'OK' if ok else 'FAIL: ' + str(orders) + ' vs oracle ' + str(oracle)}")

print("ALL PASS" if failures == 0 else f"{failures} FAILURES")
assert failures == 0
