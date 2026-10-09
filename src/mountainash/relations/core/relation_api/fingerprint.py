"""Thin fingerprint terminal orchestration over existing relation execution."""
from __future__ import annotations

from mountainash.core.limitations import enrich_materialization
from mountainash.relations.core.batch_materialization import consume_native_batches
from mountainash.relations.core.fingerprint_profile import FingerprintAccumulator, normalize_request

from .relation import _compiler_identity, _finish_terminal, _guard_native_terminal


def fingerprint_relation(relation, *, keys, columns, batch_size=5_000):
    """Project at source, check each source batch, then finalize the small result."""
    keys, columns, batch_size = normalize_request(keys, columns, batch_size)
    selected = relation.select(*dict.fromkeys((*keys, *columns)))
    native, visitor = selected._compile_and_execute_with_visitor()

    def calculate():
        _guard_native_terminal(visitor.structured_field_plans)
        checks = tuple(visitor.terminal_residue_checks())
        accumulator = None

        def on_schema(schema):
            nonlocal accumulator
            accumulator = FingerprintAccumulator(schema, keys=keys, columns=columns)

        def on_batch(batch):
            cleaned = enrich_materialization(
                visitor.backend, lambda: batch,
                diagnostic_trace=visitor._active_diagnostic_trace(),
                residue_checks=checks, execution_context=visitor.execution_context,
            )
            if accumulator is None:
                raise RuntimeError("Fingerprint reader supplied rows before schema")
            accumulator.update(cleaned)

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
