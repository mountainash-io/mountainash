# src/mountainash/pipelines/units/dag.py
from __future__ import annotations
from typing import Any, Mapping
from mountainash.pipelines.core.digest import structural_digest
from mountainash.pipelines.core.values import Value, ValueKind
from mountainash.pipelines.errors import UnsupportedValueKind
from mountainash.pipelines.units.base import BaseUnit


def _memory_token(con: Any) -> str:
    """Per-connection token for in-memory databases: minted once and stored on the connection object, so it is never
    recycled (unlike ``id()``) and never equal across connections or processes. Ibis backend objects accept attributes
    (verified on ibis 12 SQLite/DuckDB/PostgreSQL); a connection that refuses them raises AttributeError here — unsupported, not silently degraded."""
    import uuid
    tok = getattr(con, "_mountainash_memory_token", None)
    if tok is None:
        tok = f"memory#{uuid.uuid4().hex}"
        setattr(con, "_mountainash_memory_token", tok)
    return tok


def database_identity(con: Any) -> str:
    """Restart-stable identity of the physical database behind an Ibis connection (F6/F17). ``current_database`` is a
    *schema* on DuckDB/PostgreSQL and the constant ``main`` on SQLite, so it is not used."""
    name = con.name
    schema = getattr(con, "current_database", "")                    # the ACTIVE SCHEMA on DuckDB/PostgreSQL ('main' on SQLite) — kept (F40/P15)
    memory = _memory_token(con)                                      # an in-memory database is this connection and nothing else; token is a UUID
    if name == "sqlite":                                             # minted once per connection object (never recycled like id()) → never reused against another db
        (_, _, path), *_ = con.con.execute("PRAGMA database_list").fetchall()
        return f"sqlite:{path or memory}/{schema}"
    if name == "duckdb":
        (path,), = con.con.execute("SELECT path FROM duckdb_databases() WHERE database_name = current_catalog()").fetchall()
        return f"duckdb:{path or memory}/{schema}"                   # physical file path, not the catalog name (F6/F17: /a/x.duckdb ≠ /b/x.duckdb)
    if name == "postgres":
        info = con.con.info                                          # psycopg ConnectionInfo
        return f"postgres:{info.host}:{info.port}/{info.dbname}/{schema}"
    return f"{name}:{getattr(con, 'current_catalog', None) or memory}/{schema}"


def _target_key(target: Any) -> Any:
    """Restart-stable destination identity for DagUnit(target=): family, dialect, binding, physical database."""
    if target is None: return None
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
    loc = LocationResolver(IdentityTokens()).resolve_target(target)
    db = database_identity(loc.connection) if loc.connection is not None else None
    return (loc.family.value if loc.family else None, loc.dialect, loc.binding, db)


class DagUnit(BaseUnit):
    def __init__(self, template, target_name: str, *, name: str, inputs: Mapping[str, str], target: Any = None, version: str = "1") -> None:
        self.template, self.target_name, self.name, self.target, self.version = template, target_name, name, target, version
        self.inputs_map = dict(inputs); self.depends_on = tuple(self.inputs_map)

    def _extras(self):
        return {"inputs": self.inputs_map, "target_name": self.target_name, "target": _target_key(self.target),
                "digest": structural_digest(self.template, self.target_name, set(self.inputs_map.values()))}

    @staticmethod
    def adapt(value: Value) -> Any:
        if value.kind is ValueKind.RECORDS:
            from mountainash.relations.core.materialization import rows_to_arrow
            if isinstance(value.payload, list):
                return rows_to_arrow(value.payload)
            from mountainash.core.lazy_imports import import_pyarrow
            return import_pyarrow().table(value.payload)
        if value.kind is ValueKind.REFERENCE:
            raise UnsupportedValueKind("a REFERENCE is not table contents; read it back with a SourceUnit")
        return value.payload                               # TABULAR native; OPAQUE → existing ingress decides

    def run(self, upstream, ctx):
        exec_dag = self.template.bind(**{src: self.adapt(upstream[up]) for up, src in self.inputs_map.items()})
        return exec_dag.collect(self.target_name, target=self.target)
