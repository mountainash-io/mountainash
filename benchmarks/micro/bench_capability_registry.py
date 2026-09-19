"""Portable, stage-isolated evidence capsule for item 231.

Run this file explicitly with pytest-benchmark.  It is intentionally outside
``tests/`` and carries the registered ``perf`` marker, so ordinary test
collection never selects it.  Each invocation measures exactly one
``ITEM231_VARIANT`` in a separate interpreter/source-root binding.

The baseline adapters are deliberately process-local measurement models.  They
never alter package files, are restored after the pytest session, and are not
accepted registry implementations.  ``selected`` refuses every adapter and
requires the immutable-state registry interfaces delivered by item 231.
"""

from __future__ import annotations

import gc
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import runpy
import sys
import subprocess
import tracemalloc
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import Any, Iterator

import pytest


_VARIANTS = frozenset(
    {
        "source",
        "predicate-only",
        "names-gates",
        "reporting-only",
        "selected",
        "parent-controls",
    }
)
_BASELINE_VARIANTS = frozenset({"predicate-only", "names-gates", "reporting-only"})
_SOURCE_REVISION = "b9c0ab4"
_PARENT_REVISION = "3dcf0cba"
_RULES_REVISION = "fd7c0a30"
_ROUNDS = 5
_ITERATIONS = 8
_CAPSULE = Path(__file__).resolve()
_CAPSULE_ROOT = _CAPSULE.parents[2]


class UnsupportedCapsuleConfiguration(RuntimeError):
    """Raised rather than silently measuring another source or variant."""


@dataclass(frozen=True)
class Provenance:
    variant: str
    source_root: str
    imported_package: str
    revision: str
    dirty_paths: tuple[str, ...]
    source_hash: str
    source_manifest: tuple[tuple[str, str], ...]
    capsule_hash: str
    rules_root: str
    rules_revision: str
    python: str
    platform: str
    dependencies: dict[str, str]
    environment: dict[str, str | None]

    def json(self) -> dict[str, Any]:
        return {
            "item": "231",
            "variant": self.variant,
            "source_root": self.source_root,
            "imported_package": self.imported_package,
            "revision": self.revision,
            "dirty_paths": self.dirty_paths,
            "source_hash": self.source_hash,
            "source_manifest": self.source_manifest,
            "capsule_hash": self.capsule_hash,
            "rules_root": self.rules_root,
            "rules_revision": self.rules_revision,
            "python": self.python,
            "platform": self.platform,
            "cpu_count": os.cpu_count(),
            "cpu_affinity": sorted(os.sched_getaffinity(0)),
            "warmup": "one untimed asserted invocation before pedantic rounds; cold children are always fresh",
            "dependencies": self.dependencies,
            "environment": self.environment,
            "warm_definition": "package/imports and registry load already completed in this process",
            "cold_definition": "a new Python subprocess imports the requested source root and loads declarations",
        }


_MISSING = object()


@dataclass
class Adapter:
    """A reversible process-local baseline hook set."""

    restore: list[tuple[object, str, object]]

    def replace(self, owner: object, name: str, replacement: object) -> None:
        self.restore.append((owner, name, getattr(owner, name, _MISSING)))
        setattr(owner, name, replacement)

    def close(self) -> None:
        for owner, name, original in reversed(self.restore):
            if original is _MISSING:
                delattr(owner, name)
            else:
                setattr(owner, name, original)
        self.restore.clear()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_manifest(source_root: Path) -> tuple[str, tuple[tuple[str, str], ...]]:
    files = tuple(path for path in sorted(source_root.rglob("*")) if path.is_file() and "__pycache__" not in path.parts)
    manifest = tuple((str(path.relative_to(source_root)), _sha256(path)) for path in files)
    digest = hashlib.sha256("\n".join(f"{name}:{content_hash}" for name, content_hash in manifest).encode()).hexdigest()
    return digest, manifest


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise UnsupportedCapsuleConfiguration(f"source root {root} is not a verifiable git worktree: {exc}") from exc


def _source_root_for(package_file: Path) -> Path:
    # package_file is <root>/src/mountainash/__init__.py
    return package_file.resolve().parents[1]


def _configured_root(variant: str) -> Path:
    explicit = os.environ.get("ITEM231_SOURCE_ROOT")
    if explicit:
        return Path(explicit).expanduser().resolve()
    if variant == "parent-controls":
        return (_CAPSULE_ROOT.parent / "mountainash" / "src").resolve()
    if variant in {"source", "predicate-only", "names-gates", "reporting-only"}:
        return (_CAPSULE_ROOT.parent / "mountainash-rules-boolean-dependency" / "src").resolve()
    return (_CAPSULE_ROOT / "src").resolve()


def _expected_revision(variant: str) -> str:
    if variant == "parent-controls":
        return os.environ.get("ITEM231_PARENT_REVISION", _PARENT_REVISION)
    if variant == "selected":
        return os.environ.get("ITEM231_SELECTED_REVISION", _SOURCE_REVISION)
    return os.environ.get("ITEM231_SOURCE_REVISION", _SOURCE_REVISION)


def _variant() -> str:
    value = os.environ.get("ITEM231_VARIANT")
    if value not in _VARIANTS:
        choices = ", ".join(sorted(_VARIANTS))
        raise UnsupportedCapsuleConfiguration(
            f"ITEM231_VARIANT must select exactly one supported variant ({choices}); got {value!r}"
        )
    return value


def _select_cases() -> None:
    """Select supported cases at module import; test modules are not hook plugins."""
    variant = _variant()
    oracle_enabled = os.environ.get("ITEM231_RULES_ORACLE") == "1"
    if oracle_enabled and variant not in {"source", "predicate-only", "selected"}:
        raise UnsupportedCapsuleConfiguration("Rules oracle requires source, predicate-only, or selected")
    for name, case in tuple(globals().items()):
        if not name.startswith("test_item231_"):
            continue
        if oracle_enabled:
            allowed = name == "test_item231_rules_oracle"
        elif variant == "parent-controls":
            allowed = name == "test_item231_parent_arithmetic_controls"
        else:
            allowed = name not in {"test_item231_rules_oracle", "test_item231_parent_arithmetic_controls"}
            if variant != "selected" and name == "test_item231_selected_preparation":
                allowed = False
        case.__test__ = allowed


def _dependency_versions() -> dict[str, str]:
    names = ("pytest", "pytest-benchmark", "polars", "ibis-framework", "duckdb", "pyarrow", "narwhals", "pandas")
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def _provenance(variant: str) -> Provenance:
    import mountainash

    expected_root = _configured_root(variant)
    imported = _source_root_for(Path(mountainash.__file__))
    if imported != expected_root:
        raise UnsupportedCapsuleConfiguration(
            "imported mountainash source does not match ITEM231_SOURCE_ROOT: "
            f"imported={imported}, expected={expected_root}. Bind PYTHONPATH to the intended src root."
        )
    root = imported.parent
    revision = _git(root, "rev-parse", "HEAD")
    expected_revision = _expected_revision(variant)
    if not revision.startswith(expected_revision):
        raise UnsupportedCapsuleConfiguration(
            f"{variant} must use revision {expected_revision}, imported revision is {revision}"
        )
    rules_root = Path(os.environ.get("ITEM231_RULES_ROOT", _CAPSULE_ROOT.parent / "mountainash-rules"))
    rules_revision = _git(rules_root, "rev-parse", "HEAD")
    expected_rules_revision = os.environ.get("ITEM231_RULES_REVISION", _RULES_REVISION)
    if not rules_revision.startswith(expected_rules_revision):
        raise UnsupportedCapsuleConfiguration(
            f"Rules must use revision {expected_rules_revision}, imported revision is {rules_revision}"
        )
    source_hash, source_manifest = _source_manifest(imported)
    return Provenance(
        variant=variant,
        source_root=str(imported),
        imported_package=str(Path(mountainash.__file__).resolve()),
        revision=revision,
        dirty_paths=tuple(filter(None, _git(root, "status", "--porcelain").splitlines())),
        source_hash=source_hash,
        source_manifest=source_manifest,
        capsule_hash=_sha256(_CAPSULE),
        rules_root=str(rules_root.resolve()),
        rules_revision=rules_revision,
        python=sys.version,
        platform=platform.platform(),
        dependencies=_dependency_versions(),
        environment={
            name: os.environ.get(name)
            for name in ("PYTHONPATH", "POLARS_MAX_THREADS", "PYTHONHASHSEED", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
    )


def _assert_selected_interfaces() -> None:
    from mountainash.core.capabilities.registry import CapabilityRegistry
    import mountainash.core.capabilities.registry as registry_module

    missing = [
        name
        for name in ("metadata_operand_names", "register_segment", "_report_inputs")
        if not callable(getattr(CapabilityRegistry, name, None))
    ]
    missing.extend(
        name
        for name in ("_prepare_state", "_empty_state")
        if not callable(getattr(registry_module, name, None))
    )
    if getattr(CapabilityRegistry, "_state", None) is None:
        missing.append("CapabilityRegistry._state")
    if missing:
        raise UnsupportedCapsuleConfiguration(
            "selected requires the completed immutable registry interfaces; missing " + ", ".join(missing)
        )


def _metadata_names_for_facts(
    facts: tuple[Any, ...], operation_key: Any, backend: Any, dialect: str
) -> frozenset[str]:
    from mountainash.core.capabilities.predicates import metadata_arguments
    from mountainash.core.capabilities.schema import Enforcement

    return frozenset().union(
        *(
            metadata_arguments(fact.predicate)
            for fact in facts
            if fact.operation_key == operation_key
            and fact.backend is backend
            and fact.dialect == dialect
            and fact.enforcement is Enforcement.GATE
            and fact.predicate is not None
        )
    )


def _install_predicate_only_adapter() -> Adapter:
    """Reference model: scan the published policy view for each metadata query."""
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
    from mountainash.expressions.core.expression_nodes import ExpressionNode
    from mountainash.expressions.core.unified_visitor.visitor import _param_name_for, _protocol_sig_params
    from mountainash.core.capabilities.predicates import metadata_arguments
    from mountainash.core.capabilities.schema import Enforcement

    adapter = Adapter([])
    original_facts = CapabilityRegistry.facts

    def predicate_facts():
        return tuple(
            fact for fact in original_facts(enforcement=Enforcement.GATE)
            if fact.predicate is not None
        )

    def required(self, func_def, protocol_method, arguments):
        required = set(func_def.type_arguments)
        if self.enforce_capabilities:
            for fact in predicate_facts():
                if (
                    fact.operation_key == func_def.function_key
                    and fact.backend is self.backend.backend_type
                    and fact.dialect == getattr(self.backend, "dialect", None)
                ):
                    required.update(metadata_arguments(fact.predicate))
        if not required:
            return {}
        resolved: dict[str, Any] = {}
        for index, argument in enumerate(arguments):
            name = _param_name_for(_protocol_sig_params(protocol_method), index)
            if name is not None and name in required and isinstance(argument, ExpressionNode):
                resolved[name] = self.type_context.resolve(argument)
        missing = required.difference(resolved)
        if missing:
            raise self.type_context._unresolved(
                func_def.function_key, f"required operands are not bound: {', '.join(sorted(missing))}"
            )
        return resolved

    adapter.replace(UnifiedExpressionVisitor, "_required_operand_types", required)
    adapter.replace(
        CapabilityRegistry,
        "metadata_operand_names",
        classmethod(
            lambda cls, operation_key, backend, dialect=None: _metadata_names_for_facts(
                predicate_facts(), operation_key, backend, dialect
            )
        ),
    )
    return adapter


def _install_names_gates_adapter() -> Adapter:
    """Reference model: local names/buckets rebuilt after each segment publication."""
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
    from mountainash.expressions.core.expression_nodes import ExpressionNode
    from mountainash.expressions.core.unified_visitor.visitor import _param_name_for, _protocol_sig_params
    from mountainash.core.capabilities.predicates import metadata_arguments, predicate_holds
    from mountainash.core.capabilities.schema import CapabilityLevel, Enforcement

    adapter = Adapter([])
    original_facts = CapabilityRegistry.facts
    buckets: dict[tuple[Any, Any], tuple[tuple[Any, frozenset[str]], ...]] = {}
    names: dict[tuple[Any, Any, str], frozenset[str]] = {}

    def rebuild() -> None:
        nonlocal buckets, names
        buckets = {}
        names = {}
        for fact in original_facts(enforcement=Enforcement.GATE):
            if fact.predicate is None or fact.dialect is None:
                continue
            extracted = metadata_arguments(fact.predicate)
            bucket_key = (fact.operation_key, fact.backend)
            buckets[bucket_key] = buckets.get(bucket_key, ()) + ((fact, extracted),)
            key = (*bucket_key, fact.dialect)
            names[key] = names.get(key, frozenset()) | extracted

    rebuild()
    original_register = CapabilityRegistry.register_segment
    original_restore = CapabilityRegistry.restore
    original_reset = CapabilityRegistry.reset

    def lookup(operation_key, backend, dialect=None):
        return names.get((operation_key, backend, dialect), frozenset())

    def required(self, func_def, protocol_method, arguments):
        declared = frozenset(func_def.type_arguments)
        required_names = (
            lookup(func_def.function_key, self.backend.backend_type, getattr(self.backend, "dialect", None))
            if self.enforce_capabilities
            else frozenset()
        )
        required = declared if not required_names else (required_names if not declared else declared | required_names)
        if not required:
            return {}
        resolved: dict[str, Any] = {}
        for index, argument in enumerate(arguments):
            name = _param_name_for(_protocol_sig_params(protocol_method), index)
            if name is not None and name in required and isinstance(argument, ExpressionNode):
                resolved[name] = self.type_context.resolve(argument)
        missing = required.difference(resolved)
        if missing:
            raise self.type_context._unresolved(
                func_def.function_key, f"required operands are not bound: {', '.join(sorted(missing))}"
            )
        return resolved

    def violations(cls, bound_call, *, phase="complete"):
        if phase not in ("raw", "complete"):
            raise ValueError(f"unknown capability evaluation phase {phase!r}")
        out = set()
        for fact, extracted in buckets.get((bound_call.operation_key, bound_call.backend), ()):
            if fact.dialect != bound_call.dialect:
                continue
            if fact.enforcement is not Enforcement.GATE or fact.level is not CapabilityLevel.UNSUPPORTED:
                continue
            if phase == "raw" and extracted:
                continue
            if predicate_holds(
                fact.predicate, bound_call.bindings, bound_call.supplied, operand_types=bound_call.operand_types
            ):
                out.add(fact)
        return frozenset(out)

    def register(cls, segment):
        result = original_register(segment)
        rebuild()
        return result

    def restore(cls, token):
        result = original_restore(token)
        rebuild()
        return result

    def reset(cls):
        result = original_reset()
        rebuild()
        return result

    adapter.replace(
        CapabilityRegistry,
        "metadata_operand_names",
        classmethod(lambda cls, operation_key, backend, dialect=None: lookup(operation_key, backend, dialect)),
    )
    adapter.replace(UnifiedExpressionVisitor, "_required_operand_types", required)
    adapter.replace(CapabilityRegistry, "violations_for", classmethod(violations))
    adapter.replace(CapabilityRegistry, "register_segment", classmethod(register))
    adapter.replace(CapabilityRegistry, "restore", classmethod(restore))
    adapter.replace(CapabilityRegistry, "reset", classmethod(reset))
    return adapter


def _install_reporting_only_adapter() -> Adapter:
    """Reference model: canonical policy-report order prepared per publication."""
    from mountainash.core.capabilities.registry import CapabilityRegistry

    adapter = Adapter([])
    original_facts = CapabilityRegistry.facts
    original_register = CapabilityRegistry.register_segment
    original_restore = CapabilityRegistry.restore
    original_reset = CapabilityRegistry.reset
    prepared: tuple[Any, ...] = ()

    def rebuild() -> None:
        nonlocal prepared
        prepared = tuple(original_facts())

    rebuild()

    def facts(cls, *, level=None, backend=None, boundary=None, conditioned=None, enforcement=None):
        return [
            fact
            for fact in prepared
            if (level is None or fact.level is level)
            and (backend is None or fact.backend is backend)
            and (boundary is None or fact.boundary is boundary)
            and (conditioned is None or (fact.condition is not None) == conditioned)
            and (enforcement is None or fact.enforcement is enforcement)
        ]

    def register(cls, segment):
        result = original_register(segment)
        rebuild()
        return result

    def restore(cls, token):
        result = original_restore(token)
        rebuild()
        return result

    def reset(cls):
        result = original_reset()
        rebuild()
        return result

    adapter.replace(CapabilityRegistry, "facts", classmethod(facts))
    adapter.replace(CapabilityRegistry, "register_segment", classmethod(register))
    adapter.replace(CapabilityRegistry, "restore", classmethod(restore))
    adapter.replace(CapabilityRegistry, "reset", classmethod(reset))
    return adapter


def _adapter_for(variant: str) -> Adapter | None:
    if variant == "predicate-only":
        return _install_predicate_only_adapter()
    if variant == "names-gates":
        return _install_names_gates_adapter()
    if variant == "reporting-only":
        return _install_reporting_only_adapter()
    return None


@pytest.fixture(scope="session")
def capsule() -> Iterator[dict[str, Any]]:
    variant = _variant()
    provenance = _provenance(variant)
    if variant != "parent-controls":
        from mountainash.core.capabilities import CapabilityRegistry

        CapabilityRegistry.ensure_loaded()
        ordered_keys = tuple(fact.fact_key for fact in CapabilityRegistry.facts())
        gate_error = _verify_metadata_gate()
    if variant == "selected":
        _assert_selected_interfaces()
    adapter = _adapter_for(variant)
    if variant != "parent-controls":
        assert tuple(fact.fact_key for fact in CapabilityRegistry.facts()) == ordered_keys
        assert _verify_metadata_gate() == gate_error
    yield {"variant": variant, "provenance": provenance, "adapter": adapter}
    if adapter is not None:
        adapter.close()


@pytest.fixture(scope="session")
def backends() -> dict[str, Any]:
    import ibis
    import polars as pl

    polars = pl.DataFrame({"x": [0, 1]})
    connection = ibis.duckdb.connect()
    ibis_table = connection.create_table("item231_two_rows", {"x": [0, 1]}, overwrite=True)
    return {"polars": polars, "ibis-duckdb": ibis_table}


def _build_relation(workload: str, frame: Any):
    import mountainash as ma

    if workload == "projection":
        expressions = (ma.col("x"),)
    elif workload == "one-addition":
        expressions = ((ma.col("x") + 1).name.alias("y"),)
    elif workload == "width-four":
        expressions = tuple((ma.col("x") + index).name.alias(f"y{index}") for index in range(4))
    elif workload == "depth-eight":
        expression = ma.col("x")
        for _ in range(8):
            expression = expression + 1
        expressions = (expression.name.alias("y"),)
    elif workload == "metadata-abs":
        expressions = tuple(ma.col("x").abs().name.alias(f"a{index}") for index in range(4))
    else:
        raise UnsupportedCapsuleConfiguration(f"unknown workload {workload!r}")
    return ma.relation(frame).select(*expressions)


def _expected(workload: str) -> dict[str, list[int]]:
    if workload == "projection":
        return {"x": [0, 1]}
    if workload == "one-addition":
        return {"y": [1, 2]}
    if workload == "width-four":
        return {f"y{index}": [index, index + 1] for index in range(4)}
    if workload == "depth-eight":
        return {"y": [8, 9]}
    if workload == "metadata-abs":
        return {f"a{index}": [0, 1] for index in range(4)}
    raise UnsupportedCapsuleConfiguration(f"unknown workload {workload!r}")


def _terminal_dict(relation: Any) -> dict[str, list[Any]]:
    return relation.to_polars().to_dict(as_series=False)


def _compile(relation: Any) -> Any:
    return relation.compile()


def _compile_for_explicit_egress(relation: Any) -> tuple[Any, Any]:
    from mountainash.relations.core.relation_api.relation import _compiler_identity

    compiled, visitor = relation._compile_and_execute_with_visitor()
    return compiled, _compiler_identity(visitor)


def _execute_compiled(compiled: tuple[Any, Any]) -> dict[str, list[Any]]:
    from mountainash.relations.core.materialization import (
        MaterializationPurpose,
        explicit_polars_egress,
        materialize_native,
    )

    value, compiler_identity = compiled
    return explicit_polars_egress(
        materialize_native(value, compiler_identity, MaterializationPurpose.EXPLICIT_EGRESS)
    ).to_dict(as_series=False)


def _assert_workload_oracle(workload: str, relation: Any) -> None:
    actual = _terminal_dict(relation)
    assert actual == _expected(workload), (workload, actual)


def _add_extra_info(benchmark: Any, capsule: dict[str, Any], **extra: Any) -> None:
    benchmark.extra_info.update(capsule["provenance"].json())
    benchmark.extra_info.update(extra)


def _cold_process() -> dict[str, float]:
    """Independent fresh children measure cold load and immutable segment collection."""
    code = """
import json, sys, time
start = time.perf_counter()
import mountainash
imports = time.perf_counter()
if sys.argv[1] == "load":
    from mountainash.core.capabilities import CapabilityRegistry
    CapabilityRegistry.ensure_loaded()
    print(json.dumps({"imports_s": imports-start, "registry_load_total_s": time.perf_counter()-imports}))
else:
    import mountainash.core.capabilities.bootstrap as bootstrap
    from mountainash.core.capabilities.capture import require_immutable
    segments = bootstrap._load_segments()
    collected = time.perf_counter()
    for segment in segments:
        require_immutable(segment)
    print(json.dumps({"declaration_collection_s": collected-imports,
                      "immutable_segment_validation_s": time.perf_counter()-collected}))
"""
    samples = {}
    for stage in ("load", "validation"):
        completed = subprocess.run(
            [sys.executable, "-c", code, stage],
            text=True,
            capture_output=True,
            check=True,
            env=dict(os.environ),
        )
        samples.update(json.loads(completed.stdout))
    return samples


def _state_prepare_once() -> object:
    """Call the selected writer-path preparation boundary directly."""
    from mountainash.core.capabilities.registry import CapabilityRegistry
    import mountainash.core.capabilities.registry as registry_module

    state = CapabilityRegistry._state
    return registry_module._prepare_state(
        segments=state.segments,
        information=state.information,
        policies=state.policies,
        policy_origins={key: policy.origins for key, policy in state.policies.items()},
        policy_facts=state.policy_facts,
        policy_value_class_facts=state.policy_value_class_facts,
        policy_predicate_facts=state.policy_predicate_facts,
        load_state=state.load_state,
        load_error=state.load_error,
    )


def _scope_for_backend(backend_name: str):
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.constants import CONST_BACKEND

    families = {"polars": CONST_BACKEND.POLARS, "ibis-duckdb": CONST_BACKEND.IBIS}
    try:
        return Scope(families[backend_name], Dialect(backend_name))
    except KeyError as exc:
        raise UnsupportedCapsuleConfiguration(f"unknown benchmark dialect {backend_name!r}") from exc


def _synthetic_segment(*, backend_name: str, policy: Any, label: str, index: int):
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityInformation,
        CapabilitySegment,
        Domain,
        QualifiedInformationKey,
    )
    from mountainash.core.capabilities.schema import InformationLayer

    scope = _scope_for_backend(backend_name)
    information = CapabilityInformation(
        key=policy.key,
        layer=InformationLayer.NATIVE,
        level=policy.level,
        since=policy.since,
        message=policy.message,
    )
    qualified_information = QualifiedInformationKey(scope, information.key, information.layer)
    return BoundSegment(
        "mountainash.expressions.backends.capabilities."
        f"{scope.backend.value}.dialects.{backend_name.replace('-', '_')}.substrait."
        f"arithmetic.benchmark_{label.replace('-', '_')}_{index}",
        scope,
        CapabilitySegment(
            Domain.ARITHMETIC,
            information=(information,),
            policies=(replace(policy, information=qualified_information),),
        ),
    )


def _register_synthetic_policies(backend_name: str, policies: tuple[Any, ...], label: str) -> None:
    from mountainash.core.capabilities import CapabilityRegistry

    for index, policy in enumerate(policies):
        CapabilityRegistry.register_segment(
            _synthetic_segment(backend_name=backend_name, policy=policy, label=label, index=index)
        )


def _metadata_gate_policy(*, backend_name: str = "polars", index: int = 0) -> Any:
    from mountainash.core.capabilities.declarations import CapabilityKey, CapabilityPolicyRule, Selector
    from mountainash.core.capabilities.schema import CapabilityLevel, Clause, ClauseOp, PolicyAction, PolicyConsumer, Predicate
    from mountainash.core.dtypes.metadata import STORAGE_KINDS
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    alternatives = sorted(STORAGE_KINDS - {"native"})
    assert 0 <= index < 1 << len(alternatives)
    storage = frozenset({"native"} | {kind for bit, kind in enumerate(alternatives) if index & (1 << bit)})
    return CapabilityPolicyRule(
        key=CapabilityKey(
            FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            "x",
            Selector(
                "predicate",
                Predicate(
                    (
                        Clause("__operand_types__.x.logical_kind", ClauseOp.EQ, "float"),
                        Clause("__operand_types__.x.storage_kind", ClauseOp.IN, storage),
                    )
                ),
            ),
        ),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-15",
        message=f"item231 benchmark metadata ABS blocker {index}",
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
    )


@contextmanager
def _metadata_population(backend: str, count: int) -> Iterator[None]:
    from mountainash.core.capabilities import CapabilityRegistry

    token = CapabilityRegistry.snapshot()
    try:
        _register_synthetic_policies(
            backend,
            tuple(_metadata_gate_policy(backend_name=backend, index=index) for index in range(count)),
            "metadata",
        )
        yield
    finally:
        CapabilityRegistry.restore(token)


@pytest.fixture()
def populated_metadata(workload: str, backend: str) -> Iterator[None]:
    """Eight declared blockers make metadata extraction/gating observable."""
    with _metadata_population(backend, 8 if workload == "metadata-abs" else 0):
        yield


@contextmanager
def _temporary_metadata_gate() -> Iterator[None]:
    from mountainash.core.capabilities import CapabilityRegistry

    token = CapabilityRegistry.snapshot()
    try:
        _register_synthetic_policies("polars", (_metadata_gate_policy(),), "metadata_gate")
        yield
    finally:
        CapabilityRegistry.restore(token)


def _verify_metadata_gate() -> tuple[str, str]:
    import mountainash as ma
    import polars as pl
    from mountainash.core.types import BackendCapabilityError

    with _temporary_metadata_gate():
        with pytest.raises(BackendCapabilityError) as raised:
            ma.col("x").abs().compile(pl.DataFrame({"x": [0.0, 1.0]}))
        assert "item231 benchmark metadata ABS blocker" in str(raised.value)
        assert ma.col("x").abs().compile(pl.DataFrame({"x": [0, 1]})) is not None
        return type(raised.value).__qualname__, str(raised.value)


def _residue_policy() -> Any:
    from mountainash.core.capabilities.declarations import CapabilityKey, CapabilityPolicyRule
    from mountainash.core.capabilities.schema import CapabilityLevel, PolicyAction, PolicyConsumer
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    return CapabilityPolicyRule(
        key=CapabilityKey(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS, "x"),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-15",
        message="item231 benchmark residue enrichment",
        consumer=PolicyConsumer.MATERIALIZATION_ERROR,
        action=PolicyAction.ENRICH,
        native_errors=(ValueError,),
        native_issue="benchmark:item231-native-sentinel",
    )


def _enrichment_case(path: str):
    from mountainash.conform.diagnostics import OperationDiagnostic, OperationDiagnosticTrace
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.limitations import enrich_materialization
    from mountainash.core.types import BackendCapabilityError

    policy = _residue_policy()
    fact = policy.qualify(_scope_for_backend("polars"))

    class Backend:
        backend_type = CONST_BACKEND.POLARS
        dialect = "polars"
        BACKEND_NAME = "polars"

        @staticmethod
        def identify_native_issue(error):
            if type(error) is ValueError and str(error) == "item231 native sentinel":
                return "benchmark:item231-native-sentinel"
            return None

    def native_failure():
        raise ValueError("item231 native sentinel")

    trace = None
    if path == "trace":
        trace = OperationDiagnosticTrace()
        trace._records.append(
            OperationDiagnostic(
                function_key=fact.operation_key,
                backend_family="polars",
                dialect="polars",
                conform_node_id="item231-trace",
                routing_fingerprint=(),
                failure_behavior="throw",
                field_name="x",
                logical_type="integer",
                format="default",
            )
        )
        assert trace.records
    elif path != "legacy":
        raise UnsupportedCapsuleConfiguration(f"unknown enrichment path {path!r}")

    backend = Backend()

    def enrich_once():
        try:
            enrich_materialization(
                backend,
                native_failure,
                prefer_operation_keys=frozenset({fact.operation_key}),
                diagnostic_trace=trace,
            )
        except BackendCapabilityError as raised:
            cause = raised.__cause__
            return (
                type(raised).__qualname__,
                raised.limitation.fact_key,
                type(cause).__qualname__ if cause is not None else "None",
                raised.context,
            )
        raise AssertionError("residue policy did not enrich the native sentinel")

    return enrich_once


def _report_inputs() -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    from mountainash.core.capabilities.registry import CapabilityRegistry

    helper = getattr(CapabilityRegistry, "_report_inputs", None)
    if not callable(helper):
        raise UnsupportedCapsuleConfiguration("selected registry does not expose reporting inputs")
    return helper()

def _profile_call(call) -> dict[str, Any]:
    """Instrumentation uses sys.setprofile/tracemalloc, never selected code patches."""
    counters: Counter[str] = Counter()
    tracked = {
        "visit_scalar_function",
        "_enum_key",
        "fact_key",
        "predicate_holds",
        "_predicate_digest",
        "metadata_arguments",
        "resolve",
        "metadata_operand_names",
        "violations_for",
        "_prepare_state",
    }

    def profile(frame, event, arg):
        if event == "call" and frame.f_code.co_name in tracked:
            counters[frame.f_code.co_name] += 1
        return profile

    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        call()
    finally:
        sys.setprofile(previous)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "calls": dict(sorted(counters.items())),
        "bucket_candidates": _bucket_candidate_count(),
        "retained_bytes": current - before,
        "peak_bytes": peak - before,
    }


def _profile_compilation(relation: Any) -> dict[str, Any]:
    return _profile_call(lambda: _compile(relation))


def _bucket_candidate_count() -> int:
    from mountainash.core.capabilities.registry import CapabilityRegistry
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    return len(
        CapabilityRegistry._state.predicate_buckets.get(
            (FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS, CONST_BACKEND.POLARS), ()
        )
    )


def _lifetime_memory() -> dict[str, int]:
    from mountainash.core.capabilities import CapabilityRegistry

    original = CapabilityRegistry.snapshot()
    tracemalloc.start()
    baseline = tracemalloc.get_traced_memory()[0]
    held = []
    try:
        for index in range(8):
            CapabilityRegistry.register_segment(
                _synthetic_segment(
                    backend_name="polars",
                    policy=_metadata_gate_policy(index=index),
                    label="lifetime",
                    index=index,
                )
            )
            held.append(CapabilityRegistry.snapshot())
        CapabilityRegistry.restore(original)
        gc.collect()
        with_held = tracemalloc.get_traced_memory()[0] - baseline
        held.clear()
        gc.collect()
        released = tracemalloc.get_traced_memory()[0] - baseline
        return {"held_generations": 8, "held_snapshot_bytes": with_held, "released_snapshot_bytes": released}
    finally:
        CapabilityRegistry.restore(original)
        tracemalloc.stop()


@pytest.mark.perf
@pytest.mark.parametrize("backend", ("polars", "ibis-duckdb"), ids=("polars", "ibis-duckdb"))
def test_item231_cold_startup(benchmark, capsule, backend):
    """Fresh-process startup with raw child boundary samples retained in JSON extra_info."""
    samples: list[dict[str, float]] = []

    def cold() -> dict[str, float]:
        sample = _cold_process()
        samples.append(sample)
        return sample

    first = cold()
    expected_keys = {
        "imports_s",
        "declaration_collection_s",
        "registry_load_total_s",
        "immutable_segment_validation_s",
    }
    assert set(first) == expected_keys
    benchmark.pedantic(cold, rounds=_ROUNDS, iterations=1)
    assert all(set(sample) == expected_keys for sample in samples)
    _add_extra_info(
        benchmark,
        capsule,
        stage="cold-process-import-collection-validation-and-load",
        backend=backend,
        cold_child_samples=samples,
        cold_adapters_applied=False,
        assertion="fresh load child measures total registry load; separate fresh child isolates declaration collection and immutable segment validation",
    )


_WORKLOADS = ("projection", "one-addition", "width-four", "depth-eight", "metadata-abs")
_WORKLOAD_IDS = ("projection", "one_addition", "width4", "depth8", "metadata_abs")


@pytest.mark.perf
@pytest.mark.parametrize("backend", ("polars", "ibis-duckdb"), ids=("polars", "ibis-duckdb"))
@pytest.mark.parametrize("workload", _WORKLOADS, ids=_WORKLOAD_IDS)
def test_item231_ast_and_compile(benchmark, capsule, backends, backend, workload, populated_metadata):
    relation = _build_relation(workload, backends[backend])
    _assert_workload_oracle(workload, relation)
    benchmark.pedantic(
        _build_relation,
        args=(workload, backends[backend]),
        rounds=_ROUNDS,
        iterations=_ITERATIONS,
    )
    _add_extra_info(
        benchmark,
        capsule,
        stage="ast-construction",
        backend=backend,
        workload=workload,
        assertion="two-row public terminal equals expected representation",
    )


@pytest.mark.perf
@pytest.mark.parametrize("backend", ("polars", "ibis-duckdb"), ids=("polars", "ibis-duckdb"))
@pytest.mark.parametrize("workload", _WORKLOADS, ids=_WORKLOAD_IDS)
def test_item231_compile(benchmark, capsule, backends, backend, workload, populated_metadata):
    relation = _build_relation(workload, backends[backend])
    _assert_workload_oracle(workload, relation)
    assert _execute_compiled(_compile_for_explicit_egress(relation)) == _expected(workload)
    benchmark.pedantic(_compile, args=(relation,), rounds=_ROUNDS, iterations=_ITERATIONS)
    _add_extra_info(
        benchmark,
        capsule,
        stage="compilation",
        backend=backend,
        workload=workload,
        assertion="public Relation.compile result agrees with explicit-egress oracle",
    )


@pytest.mark.perf
@pytest.mark.parametrize("backend", ("polars", "ibis-duckdb"), ids=("polars", "ibis-duckdb"))
@pytest.mark.parametrize("workload", _WORKLOADS, ids=_WORKLOAD_IDS)
def test_item231_native_execution_and_terminal(benchmark, capsule, backends, backend, workload, populated_metadata):
    relation = _build_relation(workload, backends[backend])
    compiled = _compile_for_explicit_egress(relation)
    assert _execute_compiled(compiled) == _expected(workload)
    benchmark.pedantic(_execute_compiled, args=(compiled,), rounds=_ROUNDS, iterations=_ITERATIONS)
    _add_extra_info(
        benchmark,
        capsule,
        stage="native-execution-and-explicit-polars-egress",
        backend=backend,
        workload=workload,
        assertion="materialize_native(EXPLICIT_EGRESS) plus explicit_polars_egress equals expected representation",
    )


@pytest.mark.perf
@pytest.mark.parametrize("backend", ("polars", "ibis-duckdb"), ids=("polars", "ibis-duckdb"))
@pytest.mark.parametrize("workload", _WORKLOADS, ids=_WORKLOAD_IDS)
def test_item231_public_terminal(benchmark, capsule, backends, backend, workload, populated_metadata):
    relation = _build_relation(workload, backends[backend])
    _assert_workload_oracle(workload, relation)
    benchmark.pedantic(_terminal_dict, args=(relation,), rounds=_ROUNDS, iterations=_ITERATIONS)
    _add_extra_info(
        benchmark,
        capsule,
        stage="public-terminal",
        backend=backend,
        workload=workload,
        assertion="public terminal output equals deterministic two-row oracle",
    )


@pytest.mark.perf
def test_item231_reporting_inputs(benchmark, capsule):
    policy_facts, segments = _report_inputs()
    benchmark.pedantic(_report_inputs, rounds=_ROUNDS, iterations=_ITERATIONS)
    _add_extra_info(
        benchmark,
        capsule,
        stage="reporting-inputs",
        assertion="reporting consumes the prepared policy view and bound segments",
        policy_facts=len(policy_facts),
        segments=len(segments),
    )


def _publication_attribution():
    from mountainash.core.capabilities.registry import CapabilityRegistry, _empty_state

    original = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.restore(_empty_state())
        bulk = _profile_call(CapabilityRegistry.ensure_loaded)
        segment = _exact_registration_segment()
        accepted = _profile_call(lambda: CapabilityRegistry.register_segment(segment))

        def rejected():
            with pytest.raises(ValueError):
                CapabilityRegistry.register_segment(segment)

        failed = _profile_call(rejected)
        assert bulk["calls"]["_prepare_state"] == accepted["calls"]["_prepare_state"] == 1
        assert failed["calls"].get("_prepare_state", 0) == 0
        return {"bulk_load": bulk, "accepted_segment": accepted, "rejected_segment": failed}
    finally:
        CapabilityRegistry.restore(original)


@pytest.mark.perf
def test_item231_selected_preparation(benchmark, capsule):
    from mountainash.core.capabilities.registry import CapabilityRegistry

    prepared = _state_prepare_once()
    assert prepared.metadata_names == CapabilityRegistry._state.metadata_names
    benchmark.pedantic(_state_prepare_once, rounds=_ROUNDS, iterations=1)
    preparation = _profile_call(_state_prepare_once)
    publication = _publication_attribution()
    _add_extra_info(
        benchmark,
        capsule,
        stage="derived-state-preparation-private-boundary",
        preparation=preparation,
        publication=publication,
        assertion="selected preparation rebuilds the captured generation's metadata index",
    )


@pytest.mark.perf
@pytest.mark.parametrize("path", ("legacy", "trace"))
def test_item231_legacy_and_trace_error_enrichment(benchmark, capsule, path):
    from mountainash.core.capabilities import CapabilityRegistry

    token = CapabilityRegistry.snapshot()
    policy = _residue_policy()
    fact = policy.qualify(_scope_for_backend("polars"))
    try:
        CapabilityRegistry.register_segment(
            _synthetic_segment(backend_name="polars", policy=policy, label="enrichment", index=0)
        )
        enrich = _enrichment_case(path)
        outcome = enrich()
        assert outcome[:3] == ("BackendCapabilityError", fact.fact_key, "ValueError")
        if path == "legacy":
            assert outcome[3] is None
        else:
            assert outcome[3] == {
                "field_name": "x",
                "logical_type": "integer",
                "format": "default",
            }
        benchmark.pedantic(enrich, rounds=_ROUNDS, iterations=_ITERATIONS)
    finally:
        CapabilityRegistry.restore(token)
    _add_extra_info(
        benchmark,
        capsule,
        stage=f"{path}-error-enrichment",
        assertion="legacy uses an explicit native issue; trace uses an actual matching nonempty OperationDiagnosticTrace",
        outcome=outcome,
    )


@pytest.mark.perf
@pytest.mark.parametrize("cardinality", (1, 16, 256), ids=("negative1", "negative16", "negative256"))
def test_item231_negative_lookup_scaling(benchmark, capsule, cardinality):
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    lookup = CapabilityRegistry.metadata_operand_names

    for _ in range(cardinality):
        assert lookup(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS, CONST_BACKEND.POLARS, "missing-dialect") == frozenset()

    def absent_queries():
        return tuple(
            lookup(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS, CONST_BACKEND.POLARS, f"absent-{index}")
            for index in range(cardinality)
        )

    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    absent_queries()
    gc.collect()
    retained, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result = benchmark.pedantic(absent_queries, rounds=_ROUNDS, iterations=_ITERATIONS)
    assert result == (frozenset(),) * cardinality
    _add_extra_info(
        benchmark,
        capsule,
        stage="negative-query-cardinality",
        cardinality=cardinality,
        retained_query_bytes=retained - before,
        peak_query_bytes=peak - before,
        assertion="all absent lookup results are the shared empty semantic value",
    )


@contextmanager
def _unrelated_registry_population(kind: str, count: int) -> Iterator[None]:
    """Vary exact-policy and predicate-policy populations outside the ABS bucket."""
    from mountainash.core.capabilities.declarations import CapabilityKey, CapabilityPolicyRule, Selector
    from mountainash.core.capabilities.schema import CapabilityLevel, Clause, ClauseOp, PolicyAction, PolicyConsumer, Predicate
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    token = CapabilityRegistry.snapshot()
    try:
        policies = []
        for index in range(count):
            key = CapabilityKey(
                FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN,
                "x",
                Selector("predicate", Predicate((Clause("x", ClauseOp.EQ, index),))),
            ) if kind == "unrelated-predicates" else CapabilityKey(
                FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN,
                "x",
                Selector("exact", str(index)),
            )
            if kind not in {"unrelated-predicates", "unrelated-facts"}:
                raise UnsupportedCapsuleConfiguration(f"unknown registry population axis {kind!r}")
            policies.append(
                CapabilityPolicyRule(
                    key=key,
                    level=CapabilityLevel.UNSUPPORTED,
                    since="2026-09-15",
                    message=f"item231 unrelated {kind} {index}",
                    consumer=PolicyConsumer.GATE,
                    action=PolicyAction.BLOCK,
                )
            )
        _register_synthetic_policies("polars", tuple(policies), f"unrelated_{kind}")
        yield
    finally:
        CapabilityRegistry.restore(token)


def _scaled_relation(axis: str, size: int, frame: Any):
    import mountainash as ma

    if axis == "width":
        expressions = tuple((ma.col("x") + index).name.alias(f"w{index}") for index in range(size))
    elif axis == "depth":
        expression = ma.col("x")
        for _ in range(size):
            expression = expression + 1
        expressions = (expression.name.alias("depth"),)
    elif axis == "shared-subexpressions":
        shared = ma.col("x") + 1
        expressions = tuple(shared.name.alias(f"shared{index}") for index in range(size))
    else:
        raise UnsupportedCapsuleConfiguration(f"unknown AST scaling axis {axis!r}")
    return ma.relation(frame).select(*expressions)


@pytest.mark.perf
@pytest.mark.parametrize(
    ("axis", "size"),
    (
        ("width", 1),
        ("width", 16),
        ("depth", 1),
        ("depth", 16),
        ("shared-subexpressions", 1),
        ("shared-subexpressions", 16),
        ("repeated-collections", 1),
        ("repeated-collections", 16),
        ("unrelated-facts", 1),
        ("unrelated-facts", 64),
        ("unrelated-predicates", 1),
        ("unrelated-predicates", 64),
    ),
    ids=(
        "width1",
        "width16",
        "depth1",
        "depth16",
        "shared1",
        "shared16",
        "collections1",
        "collections16",
        "facts1",
        "facts64",
        "predicates1",
        "predicates64",
    ),
)
def test_item231_independent_scaling_axes(benchmark, capsule, backends, axis, size):
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    lookup = CapabilityRegistry.metadata_operand_names

    if axis.startswith("unrelated-"):
        with _unrelated_registry_population(axis, size):
            assert lookup(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS, CONST_BACKEND.POLARS, "polars") == frozenset()
            benchmark.pedantic(
                lookup,
                args=(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS, CONST_BACKEND.POLARS, "polars"),
                rounds=_ROUNDS,
                iterations=_ITERATIONS,
            )
            attribution = _profile_call(
                lambda: lookup(FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS, CONST_BACKEND.POLARS, "polars")
            )
    elif axis == "repeated-collections":
        relation = _build_relation("one-addition", backends["polars"])
        assert _terminal_dict(relation) == _expected("one-addition")

        def repeated_public_collect() -> dict[str, list[Any]]:
            result: dict[str, list[Any]] = {}
            for _ in range(size):
                result = _terminal_dict(relation)
            return result

        assert repeated_public_collect() == _expected("one-addition")
        benchmark.pedantic(repeated_public_collect, rounds=_ROUNDS, iterations=_ITERATIONS)
        attribution = _profile_call(repeated_public_collect)
    else:
        relation = _scaled_relation(axis, size, backends["polars"])
        if axis == "width":
            expected = {f"w{index}": [index, index + 1] for index in range(size)}
        elif axis == "depth":
            expected = {"depth": [size, size + 1]}
        else:
            expected = {f"shared{index}": [1, 2] for index in range(size)}
        assert _terminal_dict(relation) == expected
        benchmark.pedantic(_compile, args=(relation,), rounds=_ROUNDS, iterations=_ITERATIONS)
        attribution = _profile_compilation(relation)
    _add_extra_info(
        benchmark,
        capsule,
        stage="independent-scaling-axis",
        axis=axis,
        size=size,
        attribution=attribution,
        assertion="axis is varied independently; registry lookup and scaled AST retain their observable result",
    )


@pytest.mark.perf
@pytest.mark.parametrize("count", (0, 8, 64), ids=("metadata0", "metadata8", "metadata64"))
def test_item231_applicable_metadata_population(benchmark, capsule, count):
    """Vary only applicable ABS metadata predicates and observe the gating result."""
    import polars as pl
    from mountainash.core.types import BackendCapabilityError

    with _metadata_population("polars", count):
        relation = _build_relation("metadata-abs", pl.DataFrame({"x": [0.0, 1.0]}))

        def compile_outcome() -> str:
            try:
                _compile(relation)
            except BackendCapabilityError:
                return "blocked"
            return "allowed"

        expected = "allowed" if count == 0 else "blocked"
        assert compile_outcome() == expected
        benchmark.pedantic(compile_outcome, rounds=_ROUNDS, iterations=_ITERATIONS)
        attribution = _profile_call(compile_outcome)
    _add_extra_info(
        benchmark,
        capsule,
        stage="applicable-metadata-population",
        applicable_predicates=count,
        attribution=attribution,
        assertion="only applicable metadata count varies; float ABS is allowed at zero and blocked otherwise",
    )


@pytest.mark.perf
def test_item231_metadata_gate_and_lifecycle(benchmark, capsule):
    error_type, error_message = _verify_metadata_gate()
    lifecycle = _lifetime_memory()
    from mountainash.core.capabilities import CapabilityRegistry

    token = CapabilityRegistry.snapshot()

    def reset_restore():
        CapabilityRegistry.reset()
        CapabilityRegistry.restore(token)

    benchmark.pedantic(reset_restore, rounds=_ROUNDS, iterations=_ITERATIONS)
    _add_extra_info(
        benchmark,
        capsule,
        stage="reset-restore-and-metadata-gate",
        error_type=error_type,
        error_message=error_message,
        assertion="float ABS blocks; integer ABS compiles; snapshot restore preserves registry",
        **lifecycle,
    )


def _exact_registration_segment():
    from mountainash.core.capabilities.declarations import CapabilityKey, CapabilityPolicyRule, Selector
    from mountainash.core.capabilities.schema import CapabilityLevel, PolicyAction, PolicyConsumer
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    return _synthetic_segment(
        backend_name="polars",
        label="registration",
        index=0,
        policy=CapabilityPolicyRule(
            key=CapabilityKey(
                FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
                "x",
                Selector("exact", "item231-registration-duplicate"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-09-15",
            message="item231 exact registration duplicate",
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
        ),
    )


@pytest.mark.perf
def test_item231_registration_refresh_and_failures(benchmark, capsule):
    from mountainash.core.capabilities import CapabilityRegistry

    segment = _exact_registration_segment()
    policy = segment.segment.policies[0]
    base = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_segment(segment)
        assert policy.qualify(segment.scope) in CapabilityRegistry.facts()
        with pytest.raises(ValueError) as raised:
            CapabilityRegistry.register_segment(segment)
        failure = type(raised.value).__qualname__
    finally:
        CapabilityRegistry.restore(base)

    def accepted_segment():
        CapabilityRegistry.restore(base)
        CapabilityRegistry.register_segment(segment)

    benchmark.pedantic(accepted_segment, rounds=_ROUNDS, iterations=1)
    CapabilityRegistry.restore(base)
    _add_extra_info(
        benchmark,
        capsule,
        stage="accepted-segment-registration-refresh",
        failure_type=failure,
        assertion="accepted policy segment is visible; duplicate segment address rejects outside timing",
    )


@pytest.mark.perf
def test_item231_instrumented_attribution(benchmark, capsule, backends):
    relation = _build_relation("width-four", backends["polars"])
    _assert_workload_oracle("width-four", relation)
    attribution = _profile_compilation(relation)
    # The profiler is itself the separate attribution pass; it is never used for an
    # uninstrumented comparison row.
    benchmark.pedantic(_profile_compilation, args=(relation,), rounds=_ROUNDS, iterations=1)
    _add_extra_info(
        benchmark,
        capsule,
        stage="instrumented-attribution",
        assertion="instrumented compilation follows an independently checked public terminal oracle",
        **attribution,
    )


@pytest.mark.perf
@pytest.mark.parametrize("backend", ("polars", "ibis-duckdb"), ids=("polars", "ibis-duckdb"))
@pytest.mark.parametrize("workload", _WORKLOADS[:-1], ids=_WORKLOAD_IDS[:-1])
def test_item231_parent_arithmetic_controls(benchmark, capsule, backends, backend, workload):
    """Compile and collect the same prebuilt arithmetic relation as selected/source."""
    relation = _build_relation(workload, backends[backend])
    _assert_workload_oracle(workload, relation)
    result = benchmark.pedantic(_terminal_dict, args=(relation,), rounds=_ROUNDS, iterations=_ITERATIONS)
    assert result == _expected(workload)
    _add_extra_info(
        benchmark,
        capsule,
        stage="public-terminal",
        backend=backend,
        workload=workload,
        assertion="same prebuilt Mountainash relation and terminal representation as selected/source",
    )


def _rules_oracle():
    import mountainash_rules

    rules_root = Path(os.environ.get("ITEM231_RULES_ROOT", _CAPSULE_ROOT.parent / "mountainash-rules")).resolve()
    assert Path(mountainash_rules.__file__).resolve().is_relative_to(rules_root / "src")
    namespace = runpy.run_path(str(rules_root / "tests" / "accumulator" / "test_correctness.py"))
    method = namespace["TestThreeWayEquivalence"]().test_compatible_iff_nonempty_iff_joint_match

    def run_complete_oracle():
        for min_inc, max_inc in ((True, True), (True, False), (False, True), (False, False)):
            method(min_inc, max_inc)

    return run_complete_oracle


@pytest.mark.perf
def test_item231_rules_oracle(benchmark, capsule):
    """Explicit opt-in distribution oracle: unchanged Rules equivalence assertions."""
    oracle = _rules_oracle()
    oracle()
    benchmark.pedantic(oracle, rounds=3, iterations=1)
    _add_extra_info(
        benchmark,
        capsule,
        stage="rules-three-way-equivalence-distribution-oracle",
        assertion="unchanged Rules TestThreeWayEquivalence assertions, all four inclusivity combinations per round",
    )


_select_cases()
