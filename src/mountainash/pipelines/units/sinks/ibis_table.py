# src/mountainash/pipelines/units/sinks/ibis_table.py
from __future__ import annotations
from mountainash.core.lazy_imports import import_ibis
from mountainash.pipelines.core.values import LocatorReference, Value, ValueKind
from mountainash.pipelines.errors import AmbiguousWrite
from mountainash.pipelines.units.dag import DagUnit
from mountainash.pipelines.units.sinks.base import SinkUnit, WriteMode


def _key_rows(columns, partitions):
    return [dict(zip(columns, p if isinstance(p, tuple) else (p,))) for p in partitions]


class IbisTableSink(SinkUnit):
    """Native write on a bound Ibis connection. Transactions use the dialect's own BEGIN/COMMIT/ROLLBACK through
    ``connection.raw_sql`` — DuckDB, SQLite and PostgreSQL accept these verbatim; Ibis 12 has no common ``begin()`` (F15)."""

    def __init__(self, connection, table: str, **kw) -> None:
        super().__init__(**kw); self.con, self.table = connection, table

    def destination(self) -> str:                                                            # restart-stable: physical database + table (F16/F17)
        from mountainash.pipelines.units.dag import database_identity
        return f"ibis://{database_identity(self.con)}/{self.table}"
    def reference_exists(self, ref) -> bool: return ref.locator == self.destination() and self.table in self.con.list_tables()
    def _count(self) -> int: return int(self.con.table(self.table).count().execute())
    def _tx_exec(self, sql: str) -> None:
        self.con.raw_sql(sql)          # never close the returned object: on DuckDB it IS the backend's connection (F28)
    def _cleanup(self, *names: str) -> None:
        for n in names: self.con.drop_table(n, force=True)

    def _as_expr(self, value: Value):
        ibis = import_ibis()
        if value.kind is ValueKind.TABULAR and getattr(value.location, "connection", None) is self.con:
            return value.payload                                                               # same connection: native, zero export
        if value.kind is ValueKind.RECORDS:
            return ibis.memtable(DagUnit.adapt(value))
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
        arrow = get_relation_system(value.location.family)().export(value.payload, source=value.location)   # foreign: export once
        return ibis.memtable(arrow)

    def _scoped(self, expr, value: Value):
        """REPLACE_PARTITION: restrict staged rows to coverage.succeeded — never touch failed partitions (F19)."""
        if self.mode is not WriteMode.REPLACE_PARTITION: return expr
        keys = import_ibis().memtable(_key_rows(self.partition_columns, value.coverage.succeeded))
        return expr.semi_join(keys, list(self.partition_columns))

    def write(self, value: Value) -> LocatorReference:
        if self.mode is WriteMode.REPLACE_PARTITION and not value.coverage.succeeded:      # nothing to delete, nothing to insert (F33)
            if self.table not in self.con.list_tables():
                self.con.create_table(self.table, self._as_expr(value).limit(0))              # schema-correct empty destination (F37)
            return LocatorReference(self.destination(), self._count())
        expr = self._scoped(self._as_expr(value), value)
        stage, keys = f"_ma_stage_{self.table}", f"_ma_keys_{self.table}"
        cols = lambda cs: ", ".join(cs)      # noqa: E731
        if self.table not in self.con.list_tables():
            self.con.create_table(self.table, expr)
        else:
            self.con.create_table(stage, expr, temp=True, overwrite=True)         # snapshot BEFORE any delete: self-dependent input (B4)
            if self.mode is WriteMode.REPLACE_PARTITION:
                self.con.create_table(keys, import_ibis().memtable(_key_rows(self.partition_columns, value.coverage.succeeded)), temp=True, overwrite=True)
            self._tx_exec("BEGIN")
            try:
                if self.mode is WriteMode.REPLACE:
                    self._tx_exec(f"DELETE FROM {self.table}")
                elif self.mode is WriteMode.REPLACE_PARTITION:
                    self._tx_exec(f"DELETE FROM {self.table} WHERE ({cols(self.partition_columns)}) IN (SELECT {cols(self.partition_columns)} FROM {keys})")
                elif self.mode is WriteMode.UPSERT:
                    self._tx_exec(f"DELETE FROM {self.table} WHERE ({cols(self.keys)}) IN (SELECT {cols(self.keys)} FROM {stage})")
                self._tx_exec(f"INSERT INTO {self.table} SELECT * FROM {stage}")
                self._tx_exec("COMMIT")
            except Exception:
                self._tx_exec("ROLLBACK"); raise
            try:                                                                   # post-commit: ambiguity handling covers cleanup too (F20)
                self._cleanup(stage, keys)
            except Exception as e:
                if self.mode is WriteMode.APPEND and not self.allow_duplicate:
                    raise AmbiguousWrite(f"{self.name}: post-write cleanup failed; append has committed") from e
                raise
        try:
            n = self._count()
        except Exception as e:
            if self.mode is WriteMode.APPEND and not self.allow_duplicate:
                raise AmbiguousWrite(f"{self.name}: post-write verification failed; append may have committed") from e
            raise
        return LocatorReference(self.destination(), n)
