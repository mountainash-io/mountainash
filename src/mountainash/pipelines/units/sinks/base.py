# src/mountainash/pipelines/units/sinks/base.py
from __future__ import annotations
from abc import abstractmethod
from enum import Enum
from mountainash.pipelines.core.values import LocatorReference, Value, ValueKind
from mountainash.pipelines.errors import IncompleteCoverage, UnsupportedValueKind
from mountainash.pipelines.units.base import BaseUnit


class WriteMode(Enum):
    APPEND = "append"
    UPSERT = "upsert"
    REPLACE_PARTITION = "replace_partition"
    REPLACE = "replace"


class SinkUnit(BaseUnit):
    def __init__(
        self, *, name, depends_on, mode: WriteMode, keys=(), partition_columns=(), allow_duplicate=False, version="1"
    ) -> None:
        if len(tuple(depends_on)) != 1:
            raise ValueError("a sink consumes exactly one upstream")
        self.name, self.depends_on, self.mode, self.keys, self.partition_columns, self.allow_duplicate, self.version = (
            name,
            tuple(depends_on),
            mode,
            tuple(keys),
            tuple(partition_columns),
            allow_duplicate,
            version,
        )
        if mode is WriteMode.UPSERT and not self.keys:
            raise ValueError("UPSERT requires keys")
        if mode is WriteMode.REPLACE_PARTITION and not self.partition_columns:
            raise ValueError("REPLACE_PARTITION requires partition_columns")

    def _extras(self):  # destination/mode/keys/partitions are output-affecting (F17)
        return {
            "destination": self.destination(),
            "mode": self.mode.value,
            "keys": self.keys,
            "partition_columns": self.partition_columns,
        }

    @abstractmethod
    def destination(self) -> str: ...
    @abstractmethod
    def write(self, value: Value) -> LocatorReference: ...

    def run(self, upstream, ctx):
        v = upstream[self.depends_on[0]]
        if v.kind not in (ValueKind.TABULAR, ValueKind.RECORDS):
            raise UnsupportedValueKind(f"{self.name}: sinks accept TABULAR or RECORDS, got {v.kind.value}")
        cov = v.coverage
        if self.mode is WriteMode.REPLACE and cov is not None and not cov.complete:
            raise IncompleteCoverage(f"{self.name}: REPLACE from an incomplete value would delete earlier successes")
        if self.mode is WriteMode.REPLACE_PARTITION and (cov is None or (not cov.attempted and not cov.complete)):
            raise IncompleteCoverage(
                f"{self.name}: REPLACE_PARTITION needs partition sets (direct source or partitions_preserved chain)"
            )
        return self.write(v)
