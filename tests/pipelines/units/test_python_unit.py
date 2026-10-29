# tests/pipelines/units/test_python_unit.py
import pytest
from mountainash.pipelines.units.python import PythonUnit, unit
from mountainash.pipelines.core.values import Identity, Value, RunContext, Affinity

@pytest.mark.cell("unit:PythonUnit")
def test_unit_decorator_keeps_function_testable():
    @unit(depends_on=("a",), version="2")
    def double(rows, ctx): return [{"x": r["x"] * 2} for r in rows]
    assert double.__wrapped__([{"x": 1}], None) == [{"x": 2}]
    assert double.fn is double.__wrapped__ and double.inputs() == ("a",) and double.affinity is Affinity.WORKER

@pytest.mark.cell("unit:PythonUnit")
def test_python_unit_identity_changes_with_version_params_upstream():
    u1 = PythonUnit(lambda ctx: 1, name="u", version="1"); u2 = PythonUnit(lambda ctx: 1, name="u", version="2")
    base = u1.identity({}, {"p": 1}, None)
    assert base != u2.identity({}, {"p": 1}, None) and base != u1.identity({}, {"p": 2}, None)
    assert base == u1.identity({}, {"p": 1}, None)
