"""Owned snapshot orchestration and public checkpoint scopes."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
import threading
from typing import ClassVar
import uuid

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError, is_ibis_table
from mountainash.relations.core.errors import CompileRequiresExecutionError, MaterializationScopeClosedError
from mountainash.relations.core.execution.preparation import ExecutionPhase, prepare_execution
from mountainash.relations.core.materialization import MaterializationScope
from mountainash.relations.core.owned_copy import (
    OwnedCopy, assert_prepared_owned_open, bind_owned_alias, invalidate_owned,
    owned_copy, owned_dependencies, require_copy_idle, drain_pending_drops,
)
from mountainash.relations.core.relation_nodes import ReadRelNode


@dataclass(frozen=True)
class CheckpointPolicy:
    """Copy every stage, every kth stage, or never; no implicit exit copy."""
    interval: int | None
    EVERY_STAGE: ClassVar[CheckpointPolicy]
    NEVER: ClassVar[CheckpointPolicy]

    def __post_init__(self):
        if self.interval is not None and (type(self.interval) is not int or self.interval < 1):
            raise ValueError("checkpoint interval must be a positive integer")

    @classmethod
    def every(cls, k: int) -> CheckpointPolicy:
        if type(k) is not int or k < 1:
            raise ValueError("checkpoint interval must be a positive integer")
        return cls(k)


CheckpointPolicy.EVERY_STAGE = CheckpointPolicy(1)
CheckpointPolicy.NEVER = CheckpointPolicy(None)
_local = threading.local()


def _prepared(rel):
    dag = getattr(rel, "_dag", None)
    prepared = prepare_execution(
        rel._node, phase=ExecutionPhase.EXPLAIN,
        identity_resolver=(lambda name: dag.relations[name]._node) if dag is not None else None,
    )
    assert_prepared_owned_open(prepared)
    return prepared


def _refusal(reason):
    return BackendCapabilityError(reason, backend="materialization", function_key="OWNED_COPY")


def _placement(rel):
    prepared = _prepared(rel)
    location = prepared.locations[prepared.root_key]
    if location.family is CONST_BACKEND.IBIS:
        if location.connection is None:
            raise _refusal("Snapshot requires an explicit Ibis connection")
        if location.connection.name not in {"polars", "sqlite", "duckdb", "postgres"}:
            raise _refusal("Unsupported snapshot backend")
        if any(loc.connection is not None and loc.connection is not location.connection
               for loc in prepared.locations.values()):
            raise _refusal("Snapshot requires one physical connection")
    return location


def _discard(visitor, primary):
    session = getattr(visitor, "_execution_session", None)
    if session is not None:
        try:
            session.close(release_owned=True)
        except BaseException as cleanup:
            primary.add_note(f"Compilation cleanup also failed: {type(cleanup).__name__}")


def _compile(rel, location):
    from .relation import _guard_native_terminal
    sql = location.connection is not None and location.connection.name != "polars"
    require_copy_idle(location.connection)
    try:
        native, visitor = rel._compile_and_execute_with_visitor(
            phase=ExecutionPhase.COMPILE if sql else ExecutionPhase.EXECUTE,
        )
    except CompileRequiresExecutionError as error:
        raise _refusal("Snapshot preparation requires execution; use a phase-safe plan") from error
    try:
        require_copy_idle(location.connection)
        _guard_native_terminal(visitor.structured_field_plans)
        if location.family is CONST_BACKEND.IBIS:
            from mountainash.core.lazy_imports import import_ibis_expr_ops
            if native.op().find(import_ibis_expr_ops().ScalarParameter):
                raise _refusal("Snapshot cannot contain unbound scalar parameters")
        return native, visitor
    except BaseException as error:
        _discard(visitor, error)
        raise


def detach_snapshot_plans(plans, finished_columns, *, namespace):
    columns = set(finished_columns)
    return tuple(replace(plan, origin_node_id=(
        plan.origin_node_id if plan.origin_node_id.startswith("snapshot:")
        else f"snapshot:{namespace}:{plan.origin_node_id}"
    )) for name, plan in plans.items() if name in columns)


def _finish(rel, copy, visitor):
    from mountainash.core.limitations import enrich_materialization
    from .relation import _finish_terminal

    finished = _finish_terminal(visitor, lambda: enrich_materialization(
        visitor.backend, lambda: copy.value,
        diagnostic_trace=visitor._active_diagnostic_trace(),
        residue_checks=visitor.terminal_residue_checks(),
        execution_context=visitor.execution_context,
    ))
    bind_owned_alias(finished, copy.value)
    node = ReadRelNode(dataframe=finished, structured_field_plans=detach_snapshot_plans(
        visitor.structured_field_plans, finished.columns, namespace=uuid.uuid4().hex,
    ))
    return rel._make(node), OwnedCopy(finished, copy.release)


def _release_failed(copies, primary):
    for copy in reversed(copies):
        invalidate_owned(copy.value)
        if copy.release is not None:
            try:
                copy.release()
            except BaseException as cleanup:
                primary.add_note(f"Owned-copy cleanup also failed: {type(cleanup).__name__}")


def _snapshot(rel, scope=None):
    if scope is not None:
        scope._assert_open()
    location = _placement(rel)
    native, visitor = _compile(rel, location)
    copies = []
    try:
        copy = owned_copy(native)
        copies.append(copy)
        result, published = _finish(rel, copy, visitor)
        if scope is not None:
            scope._own(published)
        return result
    except BaseException as error:
        _discard(visitor, error)
        _release_failed(copies, error)
        raise


def snapshot(rel):
    """Use the innermost scope, or let the caller own the result by reachability."""
    stack = getattr(_local, "stack", ())
    return _snapshot(rel, stack[-1] if stack else None)


def _dependencies(rel):
    prepared = _prepared(rel)
    return set(state for node in prepared.nodes.values() if isinstance(node, ReadRelNode)
               for state in owned_dependencies(node.dataframe))


def _noop():
    pass


class MaterializationScopeHandle:
    """Hold snapshots until close, explicit detach, or checkpoint replacement."""
    def __init__(self, checkpoint):
        if not isinstance(checkpoint, CheckpointPolicy):
            raise TypeError("checkpoint must be a CheckpointPolicy")
        self._policy = checkpoint
        self._stage = 0
        self._closed = False
        self._scope = MaterializationScope()
        self._copies = {}
        self._connections = {}

    def _assert_open(self):
        if self._closed:
            raise MaterializationScopeClosedError("materialization scope is closed")

    def _own(self, copy):
        self._scope.own(copy.release or _noop, owner=copy.value)
        for state in owned_dependencies(copy.value):
            self._copies[state] = copy
        if is_ibis_table(copy.value):
            connection = copy.value._find_backend(use_default=False)
            self._connections[id(connection)] = connection

    def snapshot(self, rel):
        """Copy now and hold the result until this scope releases ownership."""
        return _snapshot(rel, self)

    def _handoff(self, states):
        copies = [self._copies[state] for state in states if state in self._copies]
        self._scope.handoff(tuple(copy.value for copy in copies))
        for state in states:
            self._copies.pop(state, None)

    def detach(self, rel):
        """Detach every copy this scope owns that is reachable from rel."""
        self._assert_open()
        states = _dependencies(rel) & self._copies.keys()
        if not states:
            raise ValueError("relation reaches no snapshot owned by this scope")
        self._handoff(states)
        return rel

    def checkpoint(self, rel, *, replaces=None):
        """Advance a successful stage, optionally cutting its plan with a copy."""
        self._assert_open()
        previous = _dependencies(replaces) if replaces is not None else set()
        _dependencies(rel)
        stage = self._stage + 1
        interval = self._policy.interval
        result = self.snapshot(rel) if interval is not None and stage % interval == 0 else rel
        self._handoff(previous - _dependencies(result))
        self._stage = stage
        return result

    def close(self):
        """Invalidate held values and hand physical deletion to the committed queue."""
        if self._closed:
            return
        self._closed = True
        for copy in self._copies.values():
            invalidate_owned(copy.value)
        errors = []
        try:
            self._scope.close()
        except BaseException as error:
            errors.append(error)
        finally:
            self._copies.clear()
        for connection in self._connections.values():
            try:
                drain_pending_drops(connection)
            except BaseException as error:
                errors.append(error)
        self._connections.clear()
        if errors:
            for extra in errors[1:]:
                errors[0].add_note(f"Additional owned-resource cleanup failed: {type(extra).__name__}")
            raise errors[0]


@contextmanager
def materialization_scope(*, checkpoint=CheckpointPolicy.EVERY_STAGE):
    """Scope native snapshots; detach results that must outlive the computation."""
    handle = MaterializationScopeHandle(checkpoint)
    if not hasattr(_local, "stack"):
        _local.stack = []
    _local.stack.append(handle)
    try:
        yield handle
    except BaseException as primary:
        try:
            handle.close()
        except BaseException as cleanup:
            primary.add_note(f"Owned-resource cleanup also failed: {type(cleanup).__name__}")
        raise
    else:
        handle.close()
    finally:
        _local.stack.pop()
