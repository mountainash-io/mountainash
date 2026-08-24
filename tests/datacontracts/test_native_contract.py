"""Native BaseDataContract: declaration collection, TypeSpec round trip, validate."""
import polars as pl
import pytest

from mountainash.datacontracts.compiler import contract_from_typespec
from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.field import Field
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.errors import IdentityInvalidError


class UserContract(BaseDataContract):
    id: int = Field(nullable=False, unique=True)
    email: str = Field(nullable=False, str_matches=r".+@.+")
    age: int = Field(ge=0)
    note: str  # type-only column

    class Config:
        name = "users"
        natural_key = ["id"]


class TestDeclarationCollection:
    def test_fields_and_annotations_collected(self):
        assert set(UserContract._contract_fields) == {"id", "email", "age"}
        assert set(UserContract._contract_annotations) == {"id", "email", "age", "note"}

    def test_declaration_syntax_preserved(self):
        assert isinstance(UserContract._contract_fields["age"], Field)
        assert UserContract._contract_fields["age"].ge == 0


class TestToTypespec:
    def test_types_and_constraints(self):
        spec = UserContract.to_typespec()
        by_name = {f.name: f for f in spec.fields}
        assert by_name["id"].type == UniversalType.INTEGER
        assert by_name["email"].constraints.pattern == r".+@.+"
        assert by_name["note"].constraints is None

    def test_natural_key_survives_as_primary_key(self):
        # Config.natural_key must survive the TypeSpec round-trip as
        # primary_key so DAG validation resolves keyed identity for
        # natural_key-only contracts.
        assert UserContract.to_typespec().primary_key == ["id"]

    def test_to_checks_ids(self):
        ids = [c.id for c in UserContract.to_checks()]
        assert "id__not_null" in ids
        assert "email__not_null" in ids
        assert "email__pattern" in ids
        assert "age__ge" in ids

    def test_to_checks_includes_primary_key_unique(self):
        ids = [c.id for c in UserContract.to_checks()]
        assert "primary_key_unique" in ids  # UserContract: Config.natural_key = ["id"]

    def test_to_checks_includes_primary_key_unique_for_primary_key_config(self):
        class OrderContract(BaseDataContract):
            order_id: int = Field(nullable=False)

            class Config:
                name = "orders"
                primary_key = ["order_id"]

        ids = [c.id for c in OrderContract.to_checks()]
        assert "primary_key_unique" in ids


def test_to_checks_matches_compile_datacontract_check_ids():
    from mountainash.datacontracts.compiler import compile_datacontract, contract_from_typespec

    spec = UserContract.to_typespec()
    compiled_ids = {c.id for c in compile_datacontract(spec)}
    contract_ids = {c.id for c in contract_from_typespec(spec).to_checks()}
    assert compiled_ids == contract_ids


class TestValidate:
    def test_valid_data_passes(self):
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df)
        assert result.passes
        assert result.datacontract_name == "users"

    def test_invalid_data_returns_not_raises(self):
        # ids stay unique here: UserContract's natural_key=["id"] means duplicate
        # ids raise IdentityInvalidError before checks run (that path is tested
        # in test_runner_mechanics); this test exercises failing CHECKS.
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["nope", "d@e.f"], "age": [-1, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df)
        assert result.passes is False
        failing = set(
            result.check_summaries.filter(
                result.check_summaries["status"] != "passed"
            )["check_id"].to_list()
        )
        assert {"email__pattern", "age__ge"} <= failing

    def test_keyed_identity_from_natural_key(self):
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["nope", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df)
        assert result.identity.kind == "keyed"
        assert "id" in result.failure_cases.columns

    def test_quick_is_fail_fast_same_shapes(self):
        df = pl.DataFrame(
            {"id": [1, 2], "email": ["nope", "d@e.f"], "age": [-1, 40], "note": ["x", "y"]}
        )
        full = UserContract.validate_datacontract(df)
        quick = UserContract.validate_datacontract_quick(df)
        assert list(full.check_summaries.columns) == list(quick.check_summaries.columns)
        assert list(full.failure_cases.columns) == list(quick.failure_cases.columns)
        assert quick.check_summaries.height <= full.check_summaries.height

    def test_validate_datacontract_raises_by_default_on_duplicate_key(self):
        df = pl.DataFrame(
            {"id": [1, 1], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        with pytest.raises(IdentityInvalidError):
            UserContract.validate_datacontract(df)

    def test_validate_datacontract_allow_imperfect_key_reports_primary_key_unique(self):
        df = pl.DataFrame(
            {"id": [1, 1], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract(df, allow_imperfect_key=True)
        assert result.passes is False
        failing = set(
            result.check_summaries.filter(
                result.check_summaries["status"] != "passed"
            )["check_id"].to_list()
        )
        assert "primary_key_unique" in failing
        assert result.identity_diagnostics["duplicate_key_tuples"] == 1

    def test_validate_datacontract_quick_allow_imperfect_key_same_shape(self):
        df = pl.DataFrame(
            {"id": [1, 1], "email": ["a@b.c", "d@e.f"], "age": [30, 40], "note": ["x", "y"]}
        )
        result = UserContract.validate_datacontract_quick(df, allow_imperfect_key=True)
        assert result.passes is False
        assert result.identity_diagnostics["duplicate_key_tuples"] == 1


class NoKeyContract(BaseDataContract):
    id: int = Field(unique=True)

    class Config:
        coerce = False


# ============================================================================
# TestSemanticStringNativeContract (item 113 Unit B, Task 2)
#
# DURATION/YEAR/YEARMONTH now compile to `str` Python annotations — their
# canonical mapping changed to the semantic-string XSD_* types (spec §8.2),
# so a native contract's Python type must be truthful about that, not still
# claim datetime.timedelta / int.
# ============================================================================

class TestSemanticStringNativeContract:
    @pytest.mark.parametrize(
        "universal",
        [UniversalType.DURATION, UniversalType.YEAR, UniversalType.YEARMONTH],
    )
    def test_semantic_string_fields_compile_to_str(self, universal) -> None:
        contract = contract_from_typespec(
            TypeSpec(fields=[FieldSpec("value", universal)])
        )
        assert contract.__annotations__["value"] is str


def test_unique_failure_without_key_identity():
    """unique needs no key identity — duplicate ids fail the CHECK when no
    natural_key/primary_key declares them as identity."""
    df = pl.DataFrame({"id": [1, 1, 2]})
    result = NoKeyContract.validate_datacontract(df)
    assert result.passes is False
    assert result.identity.kind == "none"
    summary = result.check_summaries.row(0, named=True)
    assert summary["check_id"] == "id__unique"
    assert summary["fail_count"] == 2  # both duplicated rows flagged
