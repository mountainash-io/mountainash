"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import DivergenceManifestation
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.declarations import ManifestationKey
from mountainash.core.capabilities.schema import CaptureValue
from mountainash.core.capabilities.schema import DivergenceKind
from mountainash.core.capabilities.schema import EntrypointStage
from mountainash.core.capabilities.schema import ExternalCallableRef
from mountainash.core.capabilities.schema import ExternalEntrypointTarget
from mountainash.core.capabilities.schema import Scenario

SEGMENT = CapabilitySegment(
    domain=Domain.NATIVE_INPUT,
    capabilities=(),
    manifestations=(
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.sqlite", qualname="Backend.create_table"),
                    stage=EntrypointStage.CONSTRUCTION,
                ),
                scenario=Scenario(
                    arguments=(
                        (
                            "obj",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "addr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "street",
                                                            CaptureValue(tag="text", value="Main St"),
                                                        ),
                                                        (
                                                            "zip",
                                                            CaptureValue(tag="text", value="12345"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "name",
                            CaptureValue(tag="text", value="test_table"),
                        ),
                        (
                            "overwrite",
                            CaptureValue(tag="bool", value="true"),
                        ),
                    ),
                    input_schema=(
                        (
                            "addr",
                            CaptureValue(tag="text", value="native struct/object"),
                        ),
                        (
                            "python_input",
                            CaptureValue(tag="text", value="Dict[str, List]"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "addr",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "street",
                                                            CaptureValue(tag="text", value="Main St"),
                                                        ),
                                                        (
                                                            "zip",
                                                            CaptureValue(tag="text", value="12345"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "CONSTRUCTION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "rows",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "addr",
                                                        CaptureValue(
                                                            tag="mapping",
                                                            value=(
                                                                (
                                                                    "street",
                                                                    CaptureValue(tag="text", value="Main St"),
                                                                ),
                                                                (
                                                                    "zip",
                                                                    CaptureValue(tag="text", value="12345"),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "schema",
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "addr",
                                                CaptureValue(
                                                    tag="text", value="Struct({'street': String, 'zip': String})"
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="constructed"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "exception",
                                    CaptureValue(tag="text", value="ibis.common.exceptions.UnsupportedBackendType"),
                                ),
                                (
                                    "message",
                                    CaptureValue(tag="text", value="Struct types aren't supported in SQLite"),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="raised"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            impact="conform() with a native OBJECT source raises UnsupportedBackendType on ibis-sqlite; other supported native structured backends execute it",
            since="2026-08-18",
            workaround="Use a non-SQLite Ibis backend or a Polars-backed backend for native struct conform",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.sqlite", qualname="Backend.create_table"),
                    stage=EntrypointStage.CONSTRUCTION,
                ),
                scenario=Scenario(
                    arguments=(
                        (
                            "obj",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "a",
                                                            CaptureValue(tag="integer", value="1"),
                                                        ),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "a",
                                                            CaptureValue(tag="integer", value="2"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "name",
                            CaptureValue(tag="text", value="test_table"),
                        ),
                        (
                            "overwrite",
                            CaptureValue(tag="bool", value="true"),
                        ),
                    ),
                    input_schema=(
                        (
                            "payload",
                            CaptureValue(tag="text", value="native struct/object"),
                        ),
                        (
                            "python_input",
                            CaptureValue(tag="text", value="Dict[str, List]"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "a",
                                                            CaptureValue(tag="integer", value="1"),
                                                        ),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "a",
                                                            CaptureValue(tag="integer", value="2"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "CONSTRUCTION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "rows",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "payload",
                                                        CaptureValue(
                                                            tag="mapping",
                                                            value=(
                                                                (
                                                                    "a",
                                                                    CaptureValue(tag="integer", value="1"),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "payload",
                                                        CaptureValue(
                                                            tag="mapping",
                                                            value=(
                                                                (
                                                                    "a",
                                                                    CaptureValue(tag="integer", value="2"),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "schema",
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "payload",
                                                CaptureValue(tag="text", value="Struct({'a': Int64})"),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="constructed"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "exception",
                                    CaptureValue(tag="text", value="ibis.common.exceptions.UnsupportedBackendType"),
                                ),
                                (
                                    "message",
                                    CaptureValue(tag="text", value="Struct types aren't supported in SQLite"),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="raised"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            impact="conform() with a native OBJECT source raises UnsupportedBackendType on ibis-sqlite; other supported native structured backends execute it",
            since="2026-08-18",
            workaround="Use a non-SQLite Ibis backend or a Polars-backed backend for native struct conform",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.sqlite", qualname="Backend.create_table"),
                    stage=EntrypointStage.CONSTRUCTION,
                ),
                scenario=Scenario(
                    arguments=(
                        (
                            "obj",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "id",
                                                            CaptureValue(tag="integer", value="0"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "name",
                            CaptureValue(tag="text", value="test_table"),
                        ),
                        (
                            "overwrite",
                            CaptureValue(tag="bool", value="true"),
                        ),
                    ),
                    input_schema=(
                        (
                            "payload",
                            CaptureValue(tag="text", value="native struct/object"),
                        ),
                        (
                            "python_input",
                            CaptureValue(tag="text", value="Dict[str, List]"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="mapping",
                                                    value=(
                                                        (
                                                            "id",
                                                            CaptureValue(tag="integer", value="0"),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "CONSTRUCTION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "rows",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "payload",
                                                        CaptureValue(
                                                            tag="mapping",
                                                            value=(
                                                                (
                                                                    "id",
                                                                    CaptureValue(tag="integer", value="0"),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "schema",
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "payload",
                                                CaptureValue(tag="text", value="Struct({'id': Int64})"),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="constructed"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "exception",
                                    CaptureValue(tag="text", value="ibis.common.exceptions.UnsupportedBackendType"),
                                ),
                                (
                                    "message",
                                    CaptureValue(tag="text", value="Struct types aren't supported in SQLite"),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="raised"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            impact="conform() with a native OBJECT source raises UnsupportedBackendType on ibis-sqlite; other supported native structured backends execute it",
            since="2026-08-18",
            workaround="Use a non-SQLite Ibis backend or a Polars-backed backend for native struct conform",
            issue=None,
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.sqlite", qualname="Backend.create_table"),
                    stage=EntrypointStage.CONSTRUCTION,
                ),
                scenario=Scenario(
                    arguments=(
                        (
                            "obj",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="3"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    options=(
                        (
                            "name",
                            CaptureValue(tag="text", value="test_table"),
                        ),
                        (
                            "overwrite",
                            CaptureValue(tag="bool", value="true"),
                        ),
                    ),
                    input_schema=(
                        (
                            "payload",
                            CaptureValue(tag="text", value="native list/array"),
                        ),
                        (
                            "python_input",
                            CaptureValue(tag="text", value="Dict[str, List]"),
                        ),
                    ),
                    input_data=(
                        (
                            "fixture",
                            CaptureValue(
                                tag="mapping",
                                value=(
                                    (
                                        "payload",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(
                                                    tag="sequence",
                                                    value=(
                                                        CaptureValue(tag="integer", value="1"),
                                                        CaptureValue(tag="integer", value="2"),
                                                    ),
                                                ),
                                                CaptureValue(
                                                    tag="sequence", value=(CaptureValue(tag="integer", value="3"),)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    execution=(
                        (
                            "stage",
                            CaptureValue(
                                tag="enum",
                                value=(
                                    "mountainash.core.capabilities.schema",
                                    "EntrypointStage",
                                    "CONSTRUCTION",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            kind=DivergenceKind.ENGINE_LENIENCY,
            expected=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "rows",
                                    CaptureValue(
                                        tag="sequence",
                                        value=(
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "payload",
                                                        CaptureValue(
                                                            tag="sequence",
                                                            value=(
                                                                CaptureValue(tag="integer", value="1"),
                                                                CaptureValue(tag="integer", value="2"),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "payload",
                                                        CaptureValue(
                                                            tag="sequence",
                                                            value=(CaptureValue(tag="integer", value="3"),),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "schema",
                                    CaptureValue(
                                        tag="mapping",
                                        value=(
                                            (
                                                "payload",
                                                CaptureValue(tag="text", value="List(Int64)"),
                                            ),
                                        ),
                                    ),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="constructed"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            observed=CaptureValue(
                tag="mapping",
                value=(
                    (
                        "engines",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "ibis-duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-sqlite",
                                    CaptureValue(tag="text", value="3.53.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "fresh_native_result",
                        CaptureValue(tag="bool", value="true"),
                    ),
                    (
                        "observation_layer",
                        CaptureValue(tag="text", value="native"),
                    ),
                    (
                        "packages",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "duckdb",
                                    CaptureValue(tag="text", value="1.2.2"),
                                ),
                                (
                                    "ibis-framework",
                                    CaptureValue(tag="text", value="12.0.0"),
                                ),
                                (
                                    "pandas",
                                    CaptureValue(tag="text", value="3.0.5"),
                                ),
                                (
                                    "polars",
                                    CaptureValue(tag="text", value="1.44.2"),
                                ),
                                (
                                    "pyarrow",
                                    CaptureValue(tag="text", value="25.0.1"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "result",
                        CaptureValue(
                            tag="mapping",
                            value=(
                                (
                                    "exception",
                                    CaptureValue(tag="text", value="ibis.common.exceptions.UnsupportedBackendType"),
                                ),
                                (
                                    "message",
                                    CaptureValue(tag="text", value="Array types aren't supported in SQLite"),
                                ),
                                (
                                    "status",
                                    CaptureValue(tag="text", value="raised"),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stage",
                        CaptureValue(tag="text", value="construction"),
                    ),
                    (
                        "status",
                        CaptureValue(tag="text", value="captured_direct_native_observation"),
                    ),
                ),
            ),
            impact="conform() with a native OBJECT source raises UnsupportedBackendType on ibis-sqlite; other supported native structured backends execute it",
            since="2026-08-18",
            workaround="Use a non-SQLite Ibis backend or a Polars-backed backend for native struct conform",
            issue=None,
        ),
    ),
    changes=(),
)
