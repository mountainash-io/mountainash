"""Selected SQL sessions for physical ownership qualification (including 257).

Local runs cover SQLite/DuckDB. Explicit live selection must be configured and
reachable; it never skips. Credentials stay in the upstream live harness.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import ibis
import pytest


_CASES = os.environ.get("MA_TRANSACTION_CASES", "sqlite,duckdb").split(",")
if not _CASES or any(case not in {"sqlite", "duckdb", "postgres-on", "postgres-off"} for case in _CASES):
    raise ValueError("MA_TRANSACTION_CASES must select sqlite, duckdb, postgres-on or postgres-off")


@pytest.fixture(params=_CASES)
def connection(request):
    if request.param in {"sqlite", "duckdb"}:
        con = getattr(ibis, request.param).connect()
        try:
            yield con
        finally:
            con.disconnect()
        return

    # Test-only use of the existing upstream source harness, not a runtime dependency.
    repo = str(Path(os.environ["MOUNTAINASH_DATA_REPO"]).resolve())
    sys.path.insert(0, repo)
    try:
        from scripts.live_db_harness.config import (
            build_backend_selection,
            load_unresolved_harness,
            require_destructive_consent,
        )
    finally:
        sys.path.remove(repo)
    from mountainash_data import IbisBackend

    config = json.loads(os.environ["MOUNTAINASH_LIVE_DB_CONFIG"])
    if not isinstance(config, list) or not config or not all(
        isinstance(value, str) and Path(value).is_absolute() for value in config
    ):
        raise ValueError("MOUNTAINASH_LIVE_DB_CONFIG must be a nonempty JSON list of absolute paths")
    loaded = load_unresolved_harness(
        tuple(Path(p) for p in config),
        selected_target=os.environ["MOUNTAINASH_LIVE_DB_TARGET"],
        selected_backend="postgres",
    )
    selection = build_backend_selection(loaded)
    require_destructive_consent(selection)
    owner = IbisBackend(selection.settings_parameters)
    try:
        owner.connect(auth_profile=selection.auth_profile)
        con = owner.ibis_connection()
        con.con.rollback()
        con.con.autocommit = request.param == "postgres-on"
        yield con
    finally:
        owner.close()
