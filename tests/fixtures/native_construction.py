"""Test-owned expectations for actual native construction, not runtime gates."""
from contextlib import contextmanager
from importlib.metadata import version

from mountainash.core.capabilities.applicability import (
    Applicability,
    ApplicabilityResult,
    CoordinateConstraint,
    Region,
    prepare_environment,
)
from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate

from fixtures.call_expectations import expect_call_failure


# Only Python-timedelta inference on this observed stack. Explicit nanosecond
# inputs also fail with pandas 3 and are not covered by this expectation.
_IBIS_PYTHON_TIMEDELTA = Applicability((Region((
    CoordinateConstraint("package", "pandas", specifier=">=2.2,<3"),
    CoordinateConstraint("package", "ibis-framework", specifier="==12.0.0"),
    CoordinateConstraint("package", "duckdb", specifier="==1.5.6"),
    CoordinateConstraint("package", "sqlglot", specifier="==30.17.0"),
)),))


@contextmanager
def expect_ibis_python_timedelta_construction():
    """Wrap only DuckDB create_table with Python-timedelta dictionary input."""
    from duckdb import ParserException

    claim = _IBIS_PYTHON_TIMEDELTA
    environment = Environment(tuple(
        EnvironmentCoordinate("package", name, version(name))
        for name in ("pandas", "ibis-framework", "duckdb", "sqlglot")
    ))
    applies = claim.match(prepare_environment(environment, claim.requirements)) is ApplicabilityResult.APPLICABLE
    with expect_call_failure(
        reason="https://github.com/mountainash-io/mountainash/issues/386: native Python-timedelta construction emits INTERVAL NANOSECOND; compilation is not reached.",
        errors=(ParserException,),
        when=applies,
    ):
        try:
            yield
        except ParserException as exc:
            if applies:
                assert 'syntax error at or near "NANOSECOND"' in str(exc), f"Unrelated native construction failure: {exc}"
            raise
