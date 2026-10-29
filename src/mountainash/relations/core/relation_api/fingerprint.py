"""Thin fingerprint terminal orchestration over existing relation execution."""
from __future__ import annotations

from uuid import uuid4

from mountainash.core.limitations import enrich_materialization
from mountainash.relations.core.batch_materialization import consume_native_batches
from mountainash.relations.core.fingerprint_profile import FingerprintAccumulator, normalize_request

from .relation import _compiler_identity, _finish_terminal, _guard_native_terminal


def fingerprint_relation(relation, *, keys, columns, batch_size=5_000):
    """Project at source, check each source batch, then finalize the small result."""
    keys, columns, batch_size = normalize_request(keys, columns, batch_size)
    names = tuple(dict.fromkeys((*keys, *columns)))
    # Ordinary Relation.select intentionally supports wildcard/regex selectors.
    # Rename selector-shaped *names* through the existing AST before projecting;
    # restore their public names only at the schema/batch boundary. Opaque aliases
    # avoid requiring complete AST schema inference for executable projections.
    # Native rename still validates collisions/missing names; no source is replayed.
    mapping = {}
    special = [name for name in names if name == "*" or (name.startswith("^") and name.endswith("$"))]
    if special:
        occupied = set(names)
        for name in special:
            alias = f"__ma_fingerprint_{uuid4().hex}"
            while alias in occupied:
                alias = f"__ma_fingerprint_{uuid4().hex}"
            mapping[name] = alias
            occupied.add(alias)
        relation = relation.rename(mapping)
    reverse = {alias: name for name, alias in mapping.items()}
    selected = relation.select(*(mapping.get(name, name) for name in names))
    native, visitor = selected._compile_and_execute_with_visitor(retain_execution_scope=True)

    def calculate():
        _guard_native_terminal(visitor.structured_field_plans)
        checks = tuple(visitor.terminal_residue_checks())
        accumulator = None

        def on_schema(schema):
            nonlocal accumulator
            restored = {reverse.get(name, name): dtype for name, dtype in schema.items()}
            accumulator = FingerprintAccumulator(restored, keys=keys, columns=columns)

        def on_batch(batch):
            cleaned = enrich_materialization(
                visitor.backend, lambda: batch,
                diagnostic_trace=visitor._active_diagnostic_trace(),
                residue_checks=checks, execution_context=visitor.execution_context,
            )
            if accumulator is None:
                raise RuntimeError("Fingerprint reader supplied rows before schema")
            accumulator.update(cleaned.rename(reverse) if reverse else cleaned)

        consume_native_batches(
            native, compiler_identity=_compiler_identity(visitor), batch_size=batch_size,
            on_schema=on_schema, on_batch=on_batch,
        )
        if accumulator is None:
            raise RuntimeError("Fingerprint reader did not supply a schema")
        return accumulator.finish()

    return _finish_terminal(visitor, lambda: enrich_materialization(
        visitor.backend, calculate,
        diagnostic_trace=visitor._active_diagnostic_trace(),
        residue_checks=(), execution_context=visitor.execution_context,
    ), release_owned_on_success=True)
