import datetime
import importlib
import inspect
import pkgutil

import pytest

import mountainash.pipelines as P
from mountainash.pipelines.core.values import Status, ValueKind
from mountainash.pipelines.units.base import BaseUnit
from mountainash.pipelines.units.sinks.base import WriteMode

EXPECTED_UNITS = {"PythonUnit", "DagUnit", "SourceUnit", "CallableSource", "SinkUnit", "IbisTableSink", "ParquetDirectorySink", "PipelineUnit"}
EXPECTED_CHECKPOINTS = {"MemoryCheckpoint", "FileCheckpoint"}
EXCEPTIONS: dict[str, tuple[str, str]] = {}   # name -> (reason, date)

_CP_METHODS = ("lookup", "record", "last_status", "progress", "set_progress", "pending", "pending_all", "set_pending", "clear_pending", "invalidate", "scoped")


def _production_classes():
    for m in pkgutil.walk_packages(P.__path__, P.__name__ + "."):
        mod = importlib.import_module(m.name)
        for _, c in inspect.getmembers(mod, inspect.isclass):
            if c.__module__ == mod.__name__:
                yield c


def _production_subclasses(base):
    return {c.__name__ for c in _production_classes() if issubclass(c, base) and c is not base}     # production only (F24)


def test_every_unit_kind_is_known():
    assert _production_subclasses(BaseUnit) - set(EXCEPTIONS) == EXPECTED_UNITS


def test_every_checkpoint_impl_is_known():
    impls = {c.__name__ for c in _production_classes() if c.__name__ != "Checkpoint" and all(hasattr(c, n) for n in _CP_METHODS)}
    assert impls - set(EXCEPTIONS) == EXPECTED_CHECKPOINTS


# Join discovered scope to behavioural cells (P4). Tests carry `@pytest.mark.cell("<kind>:<name>")`
# (e.g. "unit:IbisTableSink", "checkpoint:FileCheckpoint", "mode:ParquetDirectorySink:UPSERT", "status:PARTIAL");
# tests/conftest.py registers the marker and provides the session fixture `collected_cells` (set of all marker args).
def test_every_discovered_item_has_a_behavioural_cell(collected_cells):
    want = ({f"unit:{n}" for n in EXPECTED_UNITS} | {f"checkpoint:{n}" for n in EXPECTED_CHECKPOINTS}
            | {f"mode:{snk}:{m.name}" for snk in ("IbisTableSink", "ParquetDirectorySink") for m in WriteMode}
            | {f"status:{st.name}" for st in Status} | {f"kind:{k.name}" for k in ValueKind})
    missing = want - collected_cells - set(EXCEPTIONS)
    assert not missing, f"discovered items without a behavioural test cell: {sorted(missing)}"
    for name, (reason, date) in EXCEPTIONS.items():
        assert reason and datetime.date.fromisoformat(date)


def test_enums_pinned():
    assert {e.name for e in ValueKind} == {"TABULAR", "RECORDS", "REFERENCE", "OPAQUE"}
    assert {e.name for e in Status} == {"COMPLETE", "PARTIAL", "FAILED", "SKIPPED", "REUSED"}
    assert {e.name for e in WriteMode} == {"APPEND", "UPSERT", "REPLACE_PARTITION", "REPLACE"}


def test_old_module_gone():
    for mod in ("mountainash.pipelines.orchestration", "mountainash.pipelines.storage", "mountainash.pipelines.integration", "mountainash.pipelines.fluent"):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(mod)
    from mountainash.relations.core.relation_api.relation import Relation
    assert not hasattr(Relation, "params")
