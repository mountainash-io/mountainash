"""Explicit test observers of scoped claims; no execution or ID-based routing."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from mountainash.core.capabilities.capture import (
    BindingRole,
    CapturedAddress,
    CapturedAssertion,
    Environment,
    EnvironmentCoordinate,
    EvidenceCapture,
    VerificationBinding,
)
from mountainash.core.capabilities.schema import CaptureValue, ExternalCallableRef

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from mountainash.core.capabilities.catalogue import CatalogueCapture
    from mountainash.core.capabilities.declarations import QualifiedManifestationKey

_ROOT = Path(__file__).resolve().parents[2]
_CALL_EXPECTATION = pytest.StashKey[tuple[str, bool, tuple[type[BaseException], ...]]]()


@dataclass(frozen=True)
class ObserverSpec:
    """One exact observer cell, with its separately located result oracle."""

    path: str
    function: str
    parameters: tuple[tuple[str, str | int | float | bool | None], ...]
    key: QualifiedManifestationKey
    oracle: str
    stage: str
    errors: tuple[tuple[str, str], ...]
    strict: bool = True


def observer_specs() -> tuple[ObserverSpec, ...]:
    from tests.fixtures._manifestation_observers import OBSERVERS

    return OBSERVERS


def _assertion_digest(assertion: object) -> str:
    return hashlib.sha256(repr(assertion).encode("utf-8")).hexdigest()


def _require_qualified_assertion(
    observation: Mapping[str, object],
    assertion: object,
    qualified_artifacts: Mapping[str, object],
    *,
    label: str,
) -> CapturedAddress:
    qualification = observation.get("qualification")
    if type(qualification) is not dict:
        raise ValueError(f"retained {label} outcome has no assertion qualification")
    qualified_at = qualification.get("qualified_at")
    digest = qualification.get("assertion_digest")
    source = qualification.get("source")
    if type(qualified_at) is not str or type(digest) is not dict or type(source) is not dict:
        raise ValueError(f"retained {label} outcome has invalid assertion qualification")
    if (
        digest.get("encoding") != "dataclass-repr-utf8-sha256"
        or type(digest.get("sha256")) is not str
        or digest["sha256"] != _assertion_digest(assertion)
    ):
        raise ValueError(f"retained {label} assertion digest does not match the selected claim")
    artifact_digest = source.get("artifact_digest")
    if (
        type(artifact_digest) is not str
        or any(type(source.get(field)) is not str for field in ("repository", "path", "entry"))
        or type(qualified_artifacts.get(artifact_digest)) is not str
    ):
        raise ValueError(f"retained {label} outcome has invalid qualified source")
    try:
        artifact = base64.b64decode(qualified_artifacts[artifact_digest], validate=True)
    except ValueError as error:
        raise ValueError(f"retained {label} outcome has invalid qualified source") from error
    if hashlib.sha256(artifact).hexdigest() != artifact_digest:
        raise ValueError(f"retained {label} outcome has invalid qualified source")
    return CapturedAddress(source["repository"], source["path"], source["entry"], artifact=artifact)


def capture_bindings(
    catalogue: CatalogueCapture,
    specs: tuple[ObserverSpec, ...] | None = None,
    sources: Mapping[QualifiedManifestationKey, CapturedAddress] | None = None,
) -> tuple[VerificationBinding, ...]:
    """Retain current payloads and source bytes, independent of later publication."""
    if specs is None:
        specs = observer_specs()
    artifacts: dict[str, bytes] = {}
    claims: dict[QualifiedManifestationKey, CapturedAssertion] = {}

    def address(path: str, entry: str) -> CapturedAddress:
        if path not in artifacts:
            artifacts[path] = (_ROOT / path).read_bytes()
        return CapturedAddress("mountainash", path, entry, artifact=artifacts[path])

    result = []
    for spec in specs:
        if spec.key not in claims:
            record = catalogue.get(spec.key)
            source = None if sources is None else sources.get(spec.key)
            if source is None:
                origin = record.origins[0]
                source = origin.captured or address(
                    f"src/{origin.module.replace('.', '/')}.py",
                    origin.entry,
                )
            claims[spec.key] = CapturedAssertion(
                "manifestation",
                spec.key,
                record.assertion,
                source,
            )
        oracle_path, _, oracle_entry = spec.oracle.partition("::")
        if not oracle_entry:
            oracle_path, _, oracle_entry = spec.oracle.partition(":")
        result.append(
            VerificationBinding(
                captured_claim=claims[spec.key],
                scenario=spec.key.local.scenario,
                role=BindingRole.OPERATIONAL_CONTRACT,
                observer=address(spec.path, f"{spec.function}::{spec.parameters!r}"),
                scope=spec.key.scope,
                oracle=address(oracle_path, oracle_entry),
                stage=spec.stage,
            )
        )
    return tuple(result)


def capture_native_observations(
    catalogue: CatalogueCapture,
) -> tuple[tuple[VerificationBinding, ...], tuple[EvidenceCapture, ...]]:
    """Read retained native captures; refuse changed payloads rather than retarget."""
    path = "tests/fixtures/observations/external_native_construction.json"
    artifact = (_ROOT / path).read_bytes()
    raw = json.loads(artifact)
    qualified_artifacts = raw.get("qualified_source_artifacts")
    if type(qualified_artifacts) is not dict:
        raise ValueError("retained native outcome has no qualified sources")
    environment = Environment(
        tuple(
            EnvironmentCoordinate(kind, name, version)
            for kind, key in (("package", "packages"), ("engine", "engines"))
            for name, version in raw[key].items()
        )
    )
    specs = tuple({spec.key: spec for spec in observer_specs() if spec.oracle.startswith(path + "::")}.values())
    validated = []
    for spec in specs:
        match = re.fullmatch(r"observations\[(\d+)\]\.oracle", spec.oracle.split("::", 1)[1])
        if match is None:
            raise ValueError(f"invalid retained native oracle: {spec.oracle}")
        index = int(match[1])
        observation = raw["observations"][index]
        record = catalogue.get(spec.key)
        expected = CaptureValue.of(
            {
                "status": "captured_direct_native_observation",
                "fresh_native_result": True,
                "observation_layer": "native",
                "stage": "construction",
                "packages": raw["packages"],
                "engines": raw["engines"],
                "result": observation["oracle"],
            }
        )
        observed = CaptureValue.of(
            {
                "status": "captured_direct_native_observation",
                "fresh_native_result": True,
                "observation_layer": "native",
                "stage": "construction",
                "packages": raw["packages"],
                "engines": raw["engines"],
                "result": observation["observed"],
            }
        )
        if (
            record.assertion.expected != expected
            or record.assertion.observed != observed
            or spec.key.scope.dialect != observation["scope"]
            or spec.key.local.target.entrypoint != ExternalCallableRef(*observation["entrypoint"])
            or dict(spec.key.local.scenario.input_data).get("fixture") != CaptureValue.of(observation["input_data"])
            or observation["layer"] != "native"
            or observation["stage"] != "construction"
            or observation["mountainash_entrypoint_called"]
        ):
            raise ValueError("retained native outcome does not match the selected claim")
        source = _require_qualified_assertion(observation, record.assertion, qualified_artifacts, label="native")
        validated.append((spec, index, observation, source))

    operational = capture_bindings(
        catalogue,
        specs,
        sources={spec.key: source for spec, _, _, source in validated},
    )
    bindings = []
    evidence = []
    for (_, index, observation, _), bound in zip(validated, operational, strict=True):
        claim = bound.captured_claim
        capture = CapturedAddress("mountainash", path, f"observations[{index}]", artifact=artifact)
        observer = CapturedAddress("mountainash", path, f"probe_source::observations[{index}]", artifact=artifact)
        fixture = CapturedAddress("mountainash", path, f"observations[{index}].input_data", artifact=artifact)
        bindings.append(
            VerificationBinding(
                claim,
                bound.scenario,
                BindingRole.DIRECT_CURRENT_STATE,
                observer,
                bound.scope,
                bound.oracle,
                "construction",
            )
        )
        evidence.append(
            EvidenceCapture(
                capture,
                (claim,),
                raw["captured_at"],
                environment,
                (fixture,),
                "native",
                CaptureValue.of(observation["observed"]),
                (observer,),
            )
        )
    return tuple(bindings), tuple(evidence)


def capture_selected_observations(
    catalogue: CatalogueCapture,
) -> tuple[tuple[VerificationBinding, ...], tuple[EvidenceCapture, ...]]:
    """Attach actual native/public results only to their exact scoped scenarios."""
    from mountainash.core.capabilities.catalogue import CatalogueQuery, ManifestationQuery
    from mountainash.core.capabilities.schema import CompositionTarget, EntrypointStage, OperationTarget

    path = "tests/fixtures/observations/selected_materialization.json"
    artifact = (_ROOT / path).read_bytes()
    raw = json.loads(artifact)
    qualified_artifacts = raw.get("qualified_source_artifacts")
    if type(qualified_artifacts) is not dict:
        raise ValueError("retained materialization outcome has no qualified sources")
    environment = Environment(
        tuple(
            EnvironmentCoordinate(kind, name, version)
            for kind, key in (("package", "packages"), ("engine", "engines"))
            for name, version in raw[key].items()
        )
        + (EnvironmentCoordinate("interpreter", "python", raw["python"]),)
    )
    records = catalogue.search(CatalogueQuery(manifestations=ManifestationQuery())).manifestations
    bindings = []
    evidence = []
    for index, observation in enumerate(raw["observations"]):
        fixture = observation["input_data"]
        if observation["cohort"] == "nan":
            fixture = {"val": [float("nan") if value == {"float": "nan"} else value for value in fixture["val"]]}
        matches = []
        for record in records:
            target = record.key.local.target
            if isinstance(target, OperationTarget):
                method = target.operation.name.lower()
            elif isinstance(target, CompositionTarget):
                method = target.entrypoint.qualname.rsplit(".", 1)[-1]
            else:
                continue
            if (
                record.key.scope.dialect == observation["scope"]
                and method == observation["method"]
                and dict(record.key.local.scenario.input_data).get("fixture") == CaptureValue.of(fixture)
            ):
                matches.append(record)
        if len(matches) != 1:
            raise ValueError("retained materialization outcome requires exactly one scoped scenario")
        record = matches[0]
        scenario = record.key.local.scenario
        if record.assertion.expected.tag != "mapping" or record.assertion.observed.tag != "mapping":
            raise ValueError("retained materialization outcome does not match the selected claim")
        expected = dict(record.assertion.expected.value)
        observed = dict(record.assertion.observed.value)
        value_field = "outcome" if observation["cohort"] == "nan" else "values"
        if (
            expected.get(value_field) != CaptureValue.of(observation["expected"])
            or observed.get(value_field) != CaptureValue.of(observation["observed"])
            or dict(scenario.arguments)
            != {name: CaptureValue.of(value) for name, value in observation["arguments"].items()}
            or dict(scenario.options)
            != {name: CaptureValue.of(value) for name, value in observation["options"].items()}
            or dict(scenario.execution).get("stage")
            not in (CaptureValue.of("materialization"), CaptureValue.of(EntrypointStage.MATERIALIZATION))
            or observation["stage"] != "materialization"
            or observation["observation_layer"] != "native"
        ):
            raise ValueError("retained materialization outcome does not match the selected claim")
        source = _require_qualified_assertion(
            observation, record.assertion, qualified_artifacts, label="materialization"
        )
        claim = CapturedAssertion("manifestation", record.key, record.assertion, source)
        address = CapturedAddress("mountainash", path, f"observations[{index}]", artifact=artifact)
        observer = CapturedAddress(
            "mountainash", path, f"probe_sources.{observation['cohort']}::{observation['method']}", artifact=artifact
        )
        oracle = CapturedAddress("mountainash", path, f"observations[{index}].expected", artifact=artifact)
        fixture_ref = CapturedAddress("mountainash", path, f"observations[{index}].input_data", artifact=artifact)
        bindings.append(
            VerificationBinding(
                claim,
                scenario,
                BindingRole.DIRECT_CURRENT_STATE,
                observer,
                record.key.scope,
                oracle,
                "materialization",
            )
        )
        evidence.append(
            EvidenceCapture(
                address,
                (claim,),
                raw["captured_at"],
                environment,
                (fixture_ref,),
                "native",
                CaptureValue.of(observation),
                (observer, oracle),
            )
        )
    return tuple(bindings), tuple(evidence)


def _applicable_specs(
    specs: tuple[ObserverSpec, ...],
    requested: Iterable[str] | None,
    *,
    root: Path,
) -> frozenset[ObserverSpec]:
    """Return only observer specs covered by complete CLI path selectors."""
    if requested is None:
        return frozenset(specs)
    requested = tuple(requested)
    if not requested:
        return frozenset(specs)

    applicable: set[ObserverSpec] = set()
    for selector in requested:
        path_text, separator, function = selector.partition("::")
        if not path_text or (separator and "[" in function):
            continue
        function = function.replace("::", ".")
        selected_path = Path(path_text).resolve()
        for spec in specs:
            spec_path = (root / spec.path).resolve()
            if separator:
                if spec_path == selected_path and (
                    spec.function == function or spec.function.startswith(function + ".")
                ):
                    applicable.add(spec)
            elif selected_path.is_dir():
                if spec_path.is_relative_to(selected_path):
                    applicable.add(spec)
            elif spec_path == selected_path:
                applicable.add(spec)
    return frozenset(applicable)


def attach_expectations(
    items: Iterable[pytest.Item],
    specs: tuple[ObserverSpec, ...],
    *,
    reasons: Mapping[QualifiedManifestationKey, str],
    root: Path = _ROOT,
    requested: Iterable[str] | None = None,
) -> None:
    """Select exact cells and require exactly one match for each applicable observer."""
    index: dict[tuple[str, str], list[ObserverSpec]] = {}
    for spec in specs:
        index.setdefault((spec.path, spec.function), []).append(spec)
    applicable = _applicable_specs(specs, requested, root=root)
    matches = {spec: 0 for spec in applicable}
    for item in items:
        function = getattr(item, "function", None)
        if function is None or not item.path.is_relative_to(root):
            continue
        candidates = index.get((item.path.relative_to(root).as_posix(), function.__qualname__), ())
        params = getattr(getattr(item, "callspec", None), "params", {})
        matched = [
            spec
            for spec in candidates
            if all(
                name in params and type(params[name]) is type(value) and params[name] == value
                for name, value in spec.parameters
            )
        ]
        for spec in matched:
            if spec in matches:
                matches[spec] += 1
        if not matched:
            continue
        messages = []
        errors = []
        for spec in matched:
            messages.append(reasons[spec.key])
            if not spec.errors:
                raise ValueError(f"observer has no expected error: {spec.path}::{spec.function}")
            for module, qualname in spec.errors:
                error = import_module(module)
                for part in qualname.split("."):
                    error = getattr(error, part)
                if not isinstance(error, type) or not issubclass(error, BaseException):
                    raise TypeError(f"observer error is not an exception type: {module}.{qualname}")
                if error not in errors:
                    errors.append(error)
        item.stash[_CALL_EXPECTATION] = (
            "; ".join(dict.fromkeys(messages)),
            all(spec.strict for spec in matched),
            tuple(errors),
        )
    unmatched = [(spec, count) for spec, count in matches.items() if count != 1]
    if unmatched:
        rendered = ", ".join(
            f"{spec.path}::{spec.function}{spec.parameters!r} matched {count}" for spec, count in unmatched
        )
        raise ValueError(f"observer did not match exactly one collected test cell: {rendered}")


def classify_call(item: pytest.Item, call: pytest.CallInfo, report: pytest.TestReport) -> None:
    """Only the selected call can satisfy an expectation; setup/teardown cannot."""
    expected = item.stash.get(_CALL_EXPECTATION, None)
    if call.when != "call" or expected is None or report.skipped:
        return
    reason, strict, errors = expected
    if call.excinfo is not None and type(call.excinfo.value) in errors:
        report.outcome = "skipped"
        report.wasxfail = reason
    elif report.passed:
        if strict:
            report.outcome = "failed"
            report.longrepr = f"[XPASS(strict)] {reason}"
        else:
            report.wasxfail = reason
