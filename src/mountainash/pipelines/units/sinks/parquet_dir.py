# src/mountainash/pipelines/units/sinks/parquet_dir.py
from __future__ import annotations
import shutil, uuid
from pathlib import Path
from mountainash.core.lazy_imports import import_pyarrow
from mountainash.pipelines.core.values import LocatorReference, Value, ValueKind
from mountainash.pipelines.errors import UnsupportedValueKind
from mountainash.pipelines.units.dag import DagUnit
from mountainash.pipelines.units.sinks.base import SinkUnit, WriteMode


class ParquetDirectorySink(SinkUnit):
    def __init__(self, path, **kw) -> None:
        if kw.get("mode") is WriteMode.UPSERT:
            raise UnsupportedValueKind("ParquetDirectorySink does not support UPSERT")        # before key validation (F23)
        super().__init__(**kw); self.path = Path(path).resolve()

    def destination(self) -> str: return f"parquet://{self.path}"
    def reference_exists(self, ref) -> bool: return ref.locator == self.destination() and self.path.exists()

    def _arrow(self, value: Value):
        if value.kind is ValueKind.RECORDS: return DagUnit.adapt(value)
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
        return get_relation_system(value.location.family)().export(value.payload, source=value.location)

    def _part_dir(self, p) -> Path:
        d = self.path
        for col, v in zip(self.partition_columns, p if isinstance(p, tuple) else (p,)): d = d / f"{col}={v}"
        return d

    def write(self, value: Value) -> LocatorReference:
        import_pyarrow()                                    # optional-dependency guard
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
        table = self._arrow(value); self.path.mkdir(parents=True, exist_ok=True)
        if self.mode is WriteMode.REPLACE:
            shutil.rmtree(self.path); self.path.mkdir(); pq.write_table(table, self.path / f"{uuid.uuid4().hex}.parquet")
        elif self.mode is WriteMode.APPEND:
            pq.write_table(table, self.path / f"{uuid.uuid4().hex}.parquet")
        else:  # REPLACE_PARTITION: exactly coverage.succeeded; composite partitions nest directories (F18); an empty success clears
            for p in value.coverage.succeeded:
                d = self._part_dir(p)
                if d.exists(): shutil.rmtree(d)
                mask = None
                for col, v in zip(self.partition_columns, p if isinstance(p, tuple) else (p,)):
                    m = pc.equal(table[col], v); mask = m if mask is None else pc.and_(mask, m)
                sub = table.filter(mask)
                if sub.num_rows: d.mkdir(parents=True); pq.write_table(sub, d / f"{uuid.uuid4().hex}.parquet")
        return LocatorReference(self.destination(), table.num_rows)
