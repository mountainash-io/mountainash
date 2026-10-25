"""Class -> TableSchema -> contract checks conform first, then check, on every backend."""

import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.typespec import FieldDefinition, UniversalType
from mountainash.validation import ValidationRunner


class Quantity(BaseDataContract):
    qty: int = FieldDefinition(type=UniversalType.INTEGER, required=True, minimum=0)


class WarnedQuantity(BaseDataContract):
    qty: int = FieldDefinition(type=UniversalType.INTEGER, minimum=0, severity="warning")


class WarnedQuantityBlockingCode(BaseDataContract):
    qty: int = FieldDefinition(type=UniversalType.INTEGER, minimum=0, severity="warning")
    code: str = FieldDefinition(type=UniversalType.STRING, pattern="[A-Z]{2}")


ROUTES = ("class", "schema_contract", "compiled_plan")


def _validate(route, contract, data):
    """The same declaration reached through each supported contract route."""
    if route == "class":
        return contract.validate_datacontract(data)
    if route == "schema_contract":
        return contract.to_table_schema().to_contract().validate_datacontract(data)
    return ValidationRunner().validate_relation(
        ma.relation(data), plan=compile_datacontract(contract.to_table_schema())
    )


def _summary(result, check_id):
    frame = result.check_summaries.filter(result.check_summaries["check_id"] == check_id)
    return frame.row(0, named=True)


@pytest.mark.cross_backend
@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_negative_value_conforms_then_fails_the_check(route, backend_name, backend_factory):
    data = backend_factory.create({"qty": ["4", "-1", "7"]}, backend_name)

    result = _validate(route, Quantity, data)

    assert _summary(result, "qty_type_format")["status"] == "passed", backend_name
    range_row = _summary(result, "qty_range")
    assert (range_row["status"], range_row["fail_count"]) == ("failed", 1), backend_name
    assert _summary(result, "qty__not_null")["status"] == "passed", backend_name
    assert not result.passes


@pytest.mark.cross_backend
@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_warning_failure_is_reported_without_blocking(route, backend_name, backend_factory):
    data = backend_factory.create({"qty": ["4", "-1"]}, backend_name)

    result = _validate(route, WarnedQuantity, data)

    assert _summary(result, "qty_range")["status"] == "failed", backend_name
    assert result.passes


@pytest.mark.cross_backend
@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_blocking_failure_blocks_beside_a_warning(route, backend_name, backend_factory):
    data = backend_factory.create({"qty": ["4", "-1"], "code": ["AB", "ab"]}, backend_name)

    result = _validate(route, WarnedQuantityBlockingCode, data)

    assert _summary(result, "qty_range")["status"] == "failed", backend_name
    assert _summary(result, "code_pattern")["status"] == "failed", backend_name
    assert not result.passes
