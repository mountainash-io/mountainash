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
        super().__init__(**kw)
        self.con, self.table = connection, table

    def destination(self) -> str:  # restart-stable: physical database + table (F16/F17)
        from mountainash.pipelines.units.dag import database_identity

        return f"ibis://{database_identity(self.con)}/{self.table}"

    def reference_exists(self, ref) -> bool:
        return ref.locator == self.destination() and self.table in self.con.list_tables()

    def _count(self) -> int:
        return int(self.con.table(self.table).count().execute())

    def _tx_exec(self, sql: str) -> None:
        self.con.raw_sql(sql)  # never close the returned object: on DuckDB it IS the backend's connection (F28)

    def _cleanup(self, *names: str) -> None:
        for n in names:
            self.con.drop_table(n, force=True)

    def _as_expr(self, value: Value):
        if value.kind is ValueKind.TABULAR and getattr(value.location, "connection", None) is self.con:
            return value.payload  # same connection: native, zero export
        from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

        if value.kind is ValueKind.RECORDS:
            arrow = DagUnit.adapt(value)
        else:  # foreign: export once
            arrow = get_relation_system(value.location.family)().export(value.payload, source=value.location)
        destination = LocationResolver(IdentityTokens()).resolve_target(self.con)
        # the destination family's own import: check_import refuses what this connection cannot store (e.g. SQLite NaN)
        return get_relation_system(destination.family)().import_into(arrow, location=destination, owned=False).value

    def _q(self, name: str) -> str:
        """Quote an identifier in the destination's dialect."""
        from sqlglot import exp

        return exp.to_identifier(name, quoted=True).sql(dialect=self.con.compiler.dialect)

    def _key_table(self, expr, value: Value):
        """Succeeded partition keys typed like the staged columns, so NULL keys keep a comparable type."""
        schema = expr.schema()
        typed = import_ibis().schema({c: schema[c] for c in self.partition_columns})
        return import_ibis().memtable(_key_rows(self.partition_columns, value.coverage.succeeded), schema=typed)

    def _scoped(self, expr, value: Value):
        """REPLACE_PARTITION: restrict staged rows to coverage.succeeded — never touch failed partitions (F19)."""
        if self.mode is not WriteMode.REPLACE_PARTITION:
            return expr
        keys = self._key_table(expr, value)
        return expr.semi_join(keys, [expr[c].identical_to(keys[c]) for c in self.partition_columns])  # NULL-safe

    def _delete_matching(self, source: str, columns) -> str:
        """DELETE the destination rows whose ``columns`` match a ``source`` row, NULL-safely (IN would drop NULL)."""
        on = " AND ".join(
            f"{self._q(self.table)}.{self._q(c)} IS NOT DISTINCT FROM {self._q(source)}.{self._q(c)}" for c in columns
        )
        return f"DELETE FROM {self._q(self.table)} WHERE EXISTS (SELECT 1 FROM {self._q(source)} WHERE {on})"

    def write(self, value: Value) -> LocatorReference:
        if (
            self.mode is WriteMode.REPLACE_PARTITION and not value.coverage.succeeded
        ):  # nothing to delete, nothing to insert (F33)
            if self.table not in self.con.list_tables():
                self.con.create_table(
                    self.table, self._as_expr(value).limit(0)
                )  # schema-correct empty destination (F37)
            return LocatorReference(self.destination(), self._count())
        expr = self._scoped(self._as_expr(value), value)
        stage, keys = f"_ma_stage_{self.table}", f"_ma_keys_{self.table}"
        columns = ", ".join(self._q(c) for c in expr.columns)  # by name, never by position
        if self.table not in self.con.list_tables():
            self.con.create_table(self.table, expr)
        else:
            self.con.create_table(
                stage, expr, temp=True, overwrite=True
            )  # snapshot BEFORE any delete: self-dependent input (B4)
            if self.mode is WriteMode.REPLACE_PARTITION:
                self.con.create_table(keys, self._key_table(expr, value), temp=True, overwrite=True)
            self._tx_exec("BEGIN")
            try:
                if self.mode is WriteMode.REPLACE:
                    self._tx_exec(f"DELETE FROM {self._q(self.table)}")
                elif self.mode is WriteMode.REPLACE_PARTITION:
                    self._tx_exec(self._delete_matching(keys, self.partition_columns))
                elif self.mode is WriteMode.UPSERT:
                    self._tx_exec(self._delete_matching(stage, self.keys))
                self._tx_exec(f"INSERT INTO {self._q(self.table)} ({columns}) SELECT {columns} FROM {self._q(stage)}")
                self._tx_exec("COMMIT")
            except Exception:
                self._tx_exec("ROLLBACK")
                raise
            try:  # post-commit: ambiguity handling covers cleanup too (F20)
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
