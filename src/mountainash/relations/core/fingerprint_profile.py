"""Version-scoped typed fingerprints over an explicitly selected row domain."""
from __future__ import annotations

from collections.abc import Sequence
import json

import polars as pl

_MASK = (1 << 64) - 1
_SEEDS = (17, 991)
_SCALARS = {
    pl.Boolean: "Boolean", pl.Int8: "Int8", pl.Int16: "Int16", pl.Int32: "Int32", pl.Int64: "Int64",
    pl.UInt8: "UInt8", pl.UInt16: "UInt16", pl.UInt32: "UInt32", pl.UInt64: "UInt64",
    pl.Float32: "Float32", pl.Float64: "Float64", pl.String: "String", pl.Binary: "Binary",
    pl.Date: "Date", pl.Time: "Time",
}


def normalize_request(keys, columns, batch_size):
    """Validate without compiling or observing a source."""
    normalized = []
    for label, names in (("keys", keys), ("columns", columns)):
        if isinstance(names, (str, bytes)) or not isinstance(names, Sequence):
            raise TypeError(f"{label} must be an ordered sequence of column names")
        names = tuple(names)
        if not names:
            raise ValueError(f"{label} must not be empty")
        if any(not isinstance(name, str) for name in names):
            raise TypeError(f"{label} must contain only column names")
        if len(set(names)) != len(names):
            raise ValueError(f"{label} must not contain repeated names")
        normalized.append(names)
    if isinstance(batch_size, bool) or not isinstance(batch_size, int):
        raise TypeError("batch_size must be a positive integer")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return normalized[0], normalized[1], batch_size


def describe_dtype(dtype, *, path="value"):
    """Encode the supported logical type domain, including nested field order."""
    if dtype in _SCALARS:
        return {"type": _SCALARS[dtype]}
    if isinstance(dtype, pl.Decimal) and dtype.precision is not None:
        return {"type": "decimal", "precision": dtype.precision, "scale": dtype.scale}
    if isinstance(dtype, pl.Datetime):
        return {"type": "datetime", "unit": dtype.time_unit, "timezone": dtype.time_zone}
    if isinstance(dtype, pl.Duration):
        return {"type": "duration", "unit": dtype.time_unit}
    if isinstance(dtype, pl.List):
        return {"type": "list", "element": describe_dtype(dtype.inner, path=f"{path}[]")}
    if isinstance(dtype, pl.Struct):
        return {"type": "struct", "fields": [
            [field.name, describe_dtype(field.dtype, path=f"{path}.{field.name}")]
            for field in dtype.fields
        ]}
    raise TypeError(f"Unsupported fingerprint type at {path}: {dtype}")


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class FingerprintAccumulator:
    """Fixed-size aggregate state; callers retain ownership of all source batches."""

    def __init__(self, schema, *, keys, columns):
        self._keys, self._columns, _ = normalize_request(keys, columns, 1)
        self._names = tuple(dict.fromkeys((*self._keys, *self._columns)))
        missing = set(self._names).difference(schema)
        if missing:
            raise ValueError(f"Fingerprint fields missing from schema: {sorted(missing)}")
        fields = {name: [name, describe_dtype(schema[name], path=name)] for name in self._names}
        self._schema = pl.Schema({name: schema[name] for name in self._names})
        self._key_schema = _json([fields[name] for name in self._keys])
        self._value_schemas = [None, *(_json(fields[name]) for name in self._columns)]
        self._expressions = []
        for index, name in enumerate((None, *self._columns)):
            members = [pl.col(key).alias(f"k{i}") for i, key in enumerate(self._keys)]
            if name is not None:
                members.append(pl.col(name).alias("v"))
            for seed in _SEEDS:
                self._expressions.append(pl.struct(members).hash(
                    seed=seed, seed_1=seed, seed_2=seed, seed_3=seed,
                ).sum().alias(f"d{index}_{seed}"))
        self._totals = [0] * len(self._expressions)
        self._count = 0

    def update(self, batch):
        """Merge a batch only if its selected schema still matches the domain."""
        selected = batch.select(self._names)
        if selected.schema != self._schema:
            raise ValueError("Fingerprint batch schema differs from the initial schema")
        count = self._count + batch.height
        if count > _MASK:
            raise OverflowError("Fingerprint row count exceeds UInt64")
        partials = selected.select(self._expressions).row(0)
        self._totals = [(old + part) & _MASK for old, part in zip(self._totals, partials)]
        self._count = count

    def finish(self):
        """Return a detached, serializable result, including for typed empty input."""
        size = len(self._columns) + 1
        return pl.DataFrame({
            "kind": pl.Series(["keys", *(["column"] * len(self._columns))], dtype=pl.String),
            "column": pl.Series([None, *self._columns], dtype=pl.String),
            "row_count": pl.Series([self._count] * size, dtype=pl.UInt64),
            "fingerprint": pl.Series([
                f"{self._totals[i]:016x}{self._totals[i + 1]:016x}"
                for i in range(0, len(self._totals), 2)
            ], dtype=pl.String),
            "profile": pl.Series([
                f"ma-fingerprint/polars-struct-sum64x2/v1;polars={pl.__version__}"
            ] * size, dtype=pl.String),
            "key_schema": pl.Series([self._key_schema] * size, dtype=pl.String),
            "value_schema": pl.Series(self._value_schemas, dtype=pl.String),
        })
