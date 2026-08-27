"""The public exceptions façade re-exports the whole family (no shadow copies)."""
from __future__ import annotations


def test_facade_reexports_are_same_objects():
    from mountainash import exceptions as exc

    from mountainash.core.errors import BackendConversionError, MountainashError
    from mountainash.conform.errors import ConformError, MissingFieldsError
    from mountainash.relations.dag.errors import (
        DAGError, RelationDAGRequired, MissingResourceSchema, UnsupportedResourceFormat,
    )
    from mountainash.core.dtypes.errors import DtypeError, UnknownDtypeError, DtypeMappingError
    from mountainash.core.types import BackendCapabilityError
    from mountainash.typespec.validation import SchemaValidationError
    from mountainash.pipelines.errors import StepEmptyError

    expected = {
        "MountainashError": MountainashError,
        "BackendConversionError": BackendConversionError,
        "ConformError": ConformError,
        "MissingFieldsError": MissingFieldsError,
        "DAGError": DAGError,
        "RelationDAGRequired": RelationDAGRequired,
        "MissingResourceSchema": MissingResourceSchema,
        "UnsupportedResourceFormat": UnsupportedResourceFormat,
        "DtypeError": DtypeError,
        "UnknownDtypeError": UnknownDtypeError,
        "DtypeMappingError": DtypeMappingError,
        "BackendCapabilityError": BackendCapabilityError,
        "SchemaValidationError": SchemaValidationError,
        "StepEmptyError": StepEmptyError,
    }
    for name, cls in expected.items():
        assert getattr(exc, name) is cls, name


def test_facade_import_does_not_run_at_package_init():
    # Circular-import discipline: importing the package must NOT pull the façade.
    # Run in a fresh subprocess so import state is fully isolated — mutating the
    # live interpreter's sys.modules would be order-sensitive and flaky, since
    # other tests in this session import mountainash.exceptions.
    import subprocess
    import sys

    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, mountainash; "
            "sys.exit(1 if 'mountainash.exceptions' in sys.modules else 0)",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        "importing `mountainash` pulled in `mountainash.exceptions` at package "
        f"init (circular-import discipline violated).\nstderr:\n{proc.stderr}"
    )


def test_facade_imports_cleanly_after_package():
    import mountainash  # noqa: F401
    import mountainash.exceptions  # noqa: F401
