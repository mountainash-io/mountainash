"""Real source streaming and cleanup at the batch-materialization boundary."""
from __future__ import annotations

import ibis
import polars as pl
import pytest

from mountainash.core.backend_detection import identify_backend_identity
from mountainash.core.types import BackendCapabilityError


@pytest.fixture(params=["polars", "polars-lazy", "ibis-duckdb"])
def stream_source(request, tmp_path):
    frame = pl.DataFrame({"k": range(10003), "v": range(10003)})
    if request.param == "polars":
        yield frame
    elif request.param == "polars-lazy":
        path = tmp_path / "source.parquet"
        frame.write_parquet(path)
        yield pl.scan_parquet(path)
    else:
        connection = ibis.duckdb.connect()
        try:
            yield connection.create_table("batch_source", frame.to_arrow(), temp=True)
        finally:
            connection.disconnect()


def consume(source, schema, batch):
    from mountainash.relations.core.batch_materialization import consume_native_batches
    consume_native_batches(source, compiler_identity=identify_backend_identity(source),
                           batch_size=127, on_schema=schema, on_batch=batch)


def test_schema_then_bounded_batches(stream_source):
    schemas, sizes = [], []
    def batch(frame):
        assert schemas == [pl.Schema({"k": pl.Int64, "v": pl.Int64})]
        sizes.append(frame.height)
    consume(stream_source, schemas.append, batch)
    assert sum(sizes) == 10003
    assert max(sizes) <= 127


def test_consumer_failure_stops_and_source_remains_usable(stream_source):
    sizes = []
    class ConsumerFailed(RuntimeError):
        pass
    original = ConsumerFailed("after one accepted batch")
    def batch(frame):
        sizes.append(frame.height)
        if len(sizes) == 2:
            raise original
    with pytest.raises(ConsumerFailed) as caught:
        consume(stream_source, lambda schema: None, batch)
    assert caught.value is original
    assert len(sizes) == 2
    later = []
    consume(stream_source, lambda schema: None, lambda frame: later.append(frame.height))
    assert sum(later) == 10003


def test_schema_failure_does_not_deliver_rows(stream_source):
    delivered = []
    def fail(schema):
        raise ValueError("rejected domain")
    with pytest.raises(ValueError, match="rejected domain"):
        consume(stream_source, fail, delivered.append)
    assert delivered == []


def test_empty_source_still_delivers_schema(stream_source):
    if isinstance(stream_source, (pl.DataFrame, pl.LazyFrame)):
        empty = stream_source.filter(pl.col("k") < 0)
    else:
        empty = stream_source.filter(stream_source.k < 0)
    schemas, sizes = [], []
    consume(empty, schemas.append, lambda frame: sizes.append(frame.height))
    assert schemas == [pl.Schema({"k": pl.Int64, "v": pl.Int64})]
    assert sum(sizes) == 0


def test_ibis_polars_batch_api_is_not_a_bounded_reader():
    con = ibis.polars.connect()
    try:
        source = con.create_table("source", pl.DataFrame({"k": [1], "v": [2]}))
        with pytest.raises(BackendCapabilityError, match="bounded"):
            consume(source, lambda schema: None, lambda frame: None)
    finally:
        con.disconnect()


def test_lazy_source_error_is_preserved():
    source = pl.DataFrame({"k": [1], "v": ["bad"]}).lazy().with_columns(pl.col("v").cast(pl.Int64))
    with pytest.raises(pl.exceptions.InvalidOperationError):
        consume(source, lambda schema: None, lambda frame: None)
