<!--
DRAFT ONLY — NOT FILED.

Tracked internally as IB-DT-19 in registry/upstream-issues.yaml
(status: needs_filing). This file is a ready-to-file draft for
https://github.com/ibis-project/issues/new — copy the section below the
divider into a new issue when someone decides to file it. Do not open the
upstream issue as part of landing this PR.
-->

# Draft: `ibis.sqlite` `create_table`/in-memory registration crashes on a null date/timestamp value (`NaTType` binding error)

---

## Bug

`Backend.create_table()` (and any expression execution that registers an
in-memory table, e.g. `ibis.memtable(...)` compiled against a SQLite
connection) crashes with `sqlite3.ProgrammingError` when the input contains a
null `date`/`timestamp` value, for **every** input shape I tried — a plain
dict, an explicit-schema PyArrow table, `ibis.memtable(..., schema=...)`, and
an object-dtype pandas column all hit the identical crash.

### Reproduction

```python
import ibis
import datetime as dt

data = {
    "id": [1, 2],
    "ts": [None, dt.datetime(2024, 1, 1, 12, 0, 0)],
}

conn = ibis.sqlite.connect(":memory:")
t = conn.create_table("t", data, overwrite=True)
```

```
Traceback (most recent call last):
  ...
  File ".../ibis/backends/sqlite/__init__.py", line 382, in _register_in_memory_table
    cur.executemany(insert_stmt, data)
sqlite3.ProgrammingError: Error binding parameter 2: type 'NaTType' is not supported
```

A null `date32` value happens to work — but only incidentally, via PyArrow's
`Table.to_pandas(date_as_object=True)` default converting it to Python `None`
before the pandas roundtrip. A null `timestamp` has no such incidental
escape hatch: PyArrow's `to_pandas()` always maps a null timestamp to
`datetime64[ns]`'s `NaT`, and `sqlite3` has no adapter for `NaTType`.

### Root cause

`ibis.backends.sqlite.Backend._register_in_memory_table` always stages the
in-memory table via a pandas roundtrip before binding rows:

```python
def _register_in_memory_table(self, op: ops.InMemoryTable) -> None:
    ...
    df = op.data.to_frame()
    data = df.itertuples(index=False)
    ...
    with self.begin() as cur:
        cur.execute(create_stmt)
        cur.executemany(insert_stmt, data)
```

`op.data.to_frame()` always produces a pandas `datetime64` column for a
timestamp field, and pandas has no way to represent a missing value in a
`datetime64` column other than `NaT`. Because the roundtrip happens
internally, no input shape avoids it — I confirmed all of the following still
crash the same way:

- Explicit-schema `pyarrow.Table` (`pa.schema([("ts", pa.timestamp("us"))])`)
- `ibis.memtable(data, schema=ibis.schema({"ts": "timestamp"}))`
- A pandas `DataFrame` with the timestamp column forced to `dtype=object`
  before being passed in (ibis re-normalises it to `datetime64` internally
  regardless)

### Expected behavior

A null timestamp/date value should round-trip through `create_table`/table
registration the same way it does for every other ibis-supported backend —
binding as SQL `NULL`, not raising `ProgrammingError`.

### Suggested fix direction

Register a `sqlite3.register_adapter` for the pandas `NaTType` (or,
upstream, whatever internal NaT-like sentinel `_register_in_memory_table`
produces) that converts it to `None` before binding — this is the smallest
fix, doesn't change any other type's binding behavior, and matches how every
other backend already treats a missing temporal value.

### Environment

- ibis: 12.0.0
- python: 3.12.12
- pandas: 3.0.5
- sqlite3 (stdlib): module 2.6.0, libsqlite3 3.50.4
- platform: macOS-26.4-arm64-arm-64bit

### Downstream impact (context, not required for the upstream report)

Found via [mountainash](https://github.com/mountainash-io/mountainash)'s
cross-backend test suite and confirmed to also affect mountainash's own
production code (any relation that cross-type-joins a null-timestamp frame
against, or ingests one into, an ibis-sqlite-backed relation). Worked around
downstream with the `sqlite3.register_adapter` technique described above
(`relations/backends/relation_systems/ibis/_sqlite_compat.py`), tracked
internally as `IB-DT-19` pending this upstream report.
