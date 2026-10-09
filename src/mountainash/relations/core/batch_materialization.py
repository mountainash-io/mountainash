"""Bounded, scoped ingestion for the fingerprint materializing terminal."""
from __future__ import annotations

from threading import Lock

import polars as pl

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.core.types import BackendCapabilityError


def _unsupported(identity):
    return BackendCapabilityError(
        f"No qualified bounded fingerprint reader for {identity.family.value}/{identity.dialect}",
        backend=identity.dialect or identity.family.value, function_key="FINGERPRINT",
    )


def consume_native_batches(value, *, compiler_identity, batch_size, on_schema, on_batch):
    """Supply schema once and batches in scope; never close a borrowed connection.

    The consumer may fail at any point. No partial result or implicit source
    replay is performed. A batch-shaped API alone does not qualify a route.
    """
    def deliver(frame):
        for part in frame.iter_slices(batch_size):
            on_batch(part)

    if compiler_identity.family == CONST_BACKEND.POLARS:
        if isinstance(value, pl.DataFrame):
            on_schema(value.schema)
            deliver(value)
            return
        if not isinstance(value, pl.LazyFrame) or not hasattr(value, "sink_batches"):
            raise _unsupported(compiler_identity)
        on_schema(value.collect_schema())
        lock = Lock()
        failure = None

        def callback(frame):
            nonlocal failure
            with lock:
                if failure is not None:
                    return True
                try:
                    deliver(frame)
                except BaseException as exc:
                    failure = exc
                    return True
                return False

        try:
            value.sink_batches(callback, chunk_size=batch_size, maintain_order=True,
                               lazy=False, engine="streaming")
        except BaseException as termination:
            if failure is None:
                raise
            failure.add_note(f"Batch sink termination also failed: {type(termination).__name__}")
            raise failure from termination
        if failure is not None:
            raise failure
        return

    if (compiler_identity.family != CONST_BACKEND.IBIS
            or compiler_identity.dialect not in {"ibis-duckdb", "ibis-postgres"}
            or not hasattr(value, "to_pyarrow_batches")):
        raise _unsupported(compiler_identity)
    on_schema(pl.Schema(value.schema().to_pyarrow()))
    reader = value.to_pyarrow_batches(chunk_size=batch_size)
    try:
        for record_batch in reader:
            frame = transit_call(BoundaryKey.ARROW_TO_POLARS_EGRESS, pl.from_arrow, record_batch)
            deliver(frame)
    except BaseException as primary:
        try:
            reader.close()
        except BaseException as cleanup:
            primary.add_note(f"Batch reader cleanup also failed: {type(cleanup).__name__}")
        raise
    else:
        reader.close()
