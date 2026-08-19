"""Compatibility shim for Ibis's SQLite backend.

Ibis's SQLite backend (``ibis.backends.sqlite.Backend._register_in_memory_table``)
always stages an in-memory table via a pandas roundtrip (``op.data.to_frame()``)
before binding rows through the stdlib ``sqlite3`` module -- regardless of
whether the table was built from a dict, a PyArrow table, or an
``ibis.memtable(..., schema=...)`` call with an explicit temporal schema. A null
``date``/``timestamp`` value becomes pandas ``NaT`` during that roundtrip, and
``sqlite3`` has no adapter for ``NaTType`` -- ``cur.executemany()`` raises
``sqlite3.ProgrammingError("Error binding parameter N: type 'NaTType' is not
supported")`` before Mountainash's own visitor/compile machinery ever runs.

Verified empirically against ibis 12.0.0 (2026-08-18): explicit PyArrow
schemas, ``ibis.memtable(schema=...)``, and object-dtype pandas columns all
still crash, because Ibis re-normalises the input internally before reaching
the pandas roundtrip. Tracked upstream as ``IB-DT-19`` in
``registry/upstream-issues.yaml`` (status: ``needs_filing`` as of 2026-08-18 --
no upstream ibis issue exists yet).

This module registers a single process-global ``sqlite3`` adapter that binds
``NaT`` as ``NULL``, matching how every other backend already treats a missing
temporal value. It does not touch Ibis's own type inference, so schema
fidelity (including ``Boolean`` columns, which a naive ``pandas.to_sql``
bypass would silently degrade to ``Int64``) is unaffected.
"""
from __future__ import annotations

_NAT_ADAPTER_INSTALLED = False


def ensure_sqlite_nat_adapter() -> None:
    """Register a ``sqlite3`` adapter so pandas ``NaT`` binds as ``NULL``.

    Idempotent and process-global: ``sqlite3.register_adapter`` just
    overwrites one dict entry, so repeated calls are a cheap no-op. Must be
    called before any Ibis-SQLite table is created/executed with data that
    might contain a null temporal value -- call sites include every place
    Mountainash builds an ``ibis.memtable()``/``create_table()`` from
    caller- or file-supplied data that could reach a SQLite-backed
    connection (cross-type join coercion, resource ingestion, and the
    cross-backend test-fixture factory).

    Silently returns if pandas is not importable: Ibis's own SQLite roundtrip
    requires pandas too (``ibis-framework[sqlite]`` depends on it), so if
    pandas is missing here, the crash this guards against cannot occur either.
    """
    global _NAT_ADAPTER_INSTALLED
    if _NAT_ADAPTER_INSTALLED:
        return

    import sqlite3

    try:
        import pandas as pd
    except ImportError:
        return

    sqlite3.register_adapter(type(pd.NaT), lambda _: None)
    _NAT_ADAPTER_INSTALLED = True
