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
                    entrypoint=ExternalCallableRef(module="ibis.backends.duckdb", qualname="Backend.create_table"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                            "a",
                            CaptureValue(tag="text", value="inferred integer"),
                        ),
                        (
                            "b",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                                CaptureValue(tag="integer", value="3"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                                                        "a",
                                                        CaptureValue(tag="integer", value="1"),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
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
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
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
                                                "a",
                                                CaptureValue(tag="text", value="Int64"),
                                            ),
                                            (
                                                "b",
                                                CaptureValue(tag="text", value="Null"),
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
                                    CaptureValue(tag="text", value="ibis.common.exceptions.IbisTypeError"),
                                ),
                                (
                                    "message",
                                    CaptureValue(
                                        tag="text",
                                        value="DuckDB does not support creating tables with NULL typed columns. Ensure that every column has non-NULL type. NULL columns: ('b',)",
                                    ),
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
            impact="Projections whose column is entirely null raise a type resolution error",
            since="2026-07-05",
            workaround="cast the null column to an explicit type first",
            issue="IB-REL-06",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.duckdb", qualname="Backend.create_table"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                            "a",
                            CaptureValue(tag="text", value="inferred integer"),
                        ),
                        (
                            "b",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="integer", value="3"),
                                                CaptureValue(tag="integer", value="1"),
                                                CaptureValue(tag="integer", value="2"),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                                                        "a",
                                                        CaptureValue(tag="integer", value="3"),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="integer", value="1"),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
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
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
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
                                                "a",
                                                CaptureValue(tag="text", value="Int64"),
                                            ),
                                            (
                                                "b",
                                                CaptureValue(tag="text", value="Null"),
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
                                    CaptureValue(tag="text", value="ibis.common.exceptions.IbisTypeError"),
                                ),
                                (
                                    "message",
                                    CaptureValue(
                                        tag="text",
                                        value="DuckDB does not support creating tables with NULL typed columns. Ensure that every column has non-NULL type. NULL columns: ('b',)",
                                    ),
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
            impact="Projections whose column is entirely null raise a type resolution error",
            since="2026-07-05",
            workaround="cast the null column to an explicit type first",
            issue="IB-REL-06",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.duckdb", qualname="Backend.create_table"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                            "a",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
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
                                                "a",
                                                CaptureValue(tag="text", value="Null"),
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
                                    CaptureValue(tag="text", value="ibis.common.exceptions.IbisTypeError"),
                                ),
                                (
                                    "message",
                                    CaptureValue(
                                        tag="text",
                                        value="DuckDB does not support creating tables with NULL typed columns. Ensure that every column has non-NULL type. NULL columns: ('a',)",
                                    ),
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
            impact="Projections whose column is entirely null raise a type resolution error",
            since="2026-07-05",
            workaround="cast the null column to an explicit type first",
            issue="IB-REL-06",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.duckdb", qualname="Backend.create_table"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                            "a",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
                        ),
                        (
                            "b",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
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
                                                "a",
                                                CaptureValue(tag="text", value="Null"),
                                            ),
                                            (
                                                "b",
                                                CaptureValue(tag="text", value="Null"),
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
                                    CaptureValue(tag="text", value="ibis.common.exceptions.IbisTypeError"),
                                ),
                                (
                                    "message",
                                    CaptureValue(
                                        tag="text",
                                        value="DuckDB does not support creating tables with NULL typed columns. Ensure that every column has non-NULL type. NULL columns: ('a', 'b')",
                                    ),
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
            impact="Projections whose column is entirely null raise a type resolution error",
            since="2026-07-05",
            workaround="cast the null column to an explicit type first",
            issue="IB-REL-06",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.duckdb", qualname="Backend.create_table"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                    (
                                        "c",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                            "a",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
                        ),
                        (
                            "b",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
                        ),
                        (
                            "c",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
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
                                        "a",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                    (
                                        "b",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                            ),
                                        ),
                                    ),
                                    (
                                        "c",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "c",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "c",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "a",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "b",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                    (
                                                        "c",
                                                        CaptureValue(tag="null", value=""),
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
                                                "a",
                                                CaptureValue(tag="text", value="Null"),
                                            ),
                                            (
                                                "b",
                                                CaptureValue(tag="text", value="Null"),
                                            ),
                                            (
                                                "c",
                                                CaptureValue(tag="text", value="Null"),
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
                                    CaptureValue(tag="text", value="ibis.common.exceptions.IbisTypeError"),
                                ),
                                (
                                    "message",
                                    CaptureValue(
                                        tag="text",
                                        value="DuckDB does not support creating tables with NULL typed columns. Ensure that every column has non-NULL type. NULL columns: ('a', 'b', 'c')",
                                    ),
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
            impact="Projections whose column is entirely null raise a type resolution error",
            since="2026-07-05",
            workaround="cast the null column to an explicit type first",
            issue="IB-REL-06",
        ),
        DivergenceManifestation(
            key=ManifestationKey(
                target=ExternalEntrypointTarget(
                    entrypoint=ExternalCallableRef(module="ibis.backends.duckdb", qualname="Backend.create_table"),
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
                                        "age",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                            "age",
                            CaptureValue(tag="text", value="inferred untyped NULL"),
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
                                        "age",
                                        CaptureValue(
                                            tag="sequence",
                                            value=(
                                                CaptureValue(tag="null", value=""),
                                                CaptureValue(tag="null", value=""),
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
                                                        "age",
                                                        CaptureValue(tag="null", value=""),
                                                    ),
                                                ),
                                            ),
                                            CaptureValue(
                                                tag="mapping",
                                                value=(
                                                    (
                                                        "age",
                                                        CaptureValue(tag="null", value=""),
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
                                                "age",
                                                CaptureValue(tag="text", value="Null"),
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
                                    CaptureValue(tag="text", value="ibis.common.exceptions.IbisTypeError"),
                                ),
                                (
                                    "message",
                                    CaptureValue(
                                        tag="text",
                                        value="DuckDB does not support creating tables with NULL typed columns. Ensure that every column has non-NULL type. NULL columns: ('age',)",
                                    ),
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
            impact="Projections whose column is entirely null raise a type resolution error",
            since="2026-07-05",
            workaround="cast the null column to an explicit type first",
            issue="IB-REL-06",
        ),
    ),
    changes=(),
)
