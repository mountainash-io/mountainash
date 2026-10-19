"""Compiled validation-plan snapshot tests."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.checks import RowRule
from mountainash.validation.plan import build_compiled_plan, thaw_value


def test_compiled_plan_copies_mutable_check_declarations():
    fields = ["id"]
    metadata = {"provenance": {"source": "initial"}}
    check = RowRule(
        id="id_present",
        expr=ma.col("id").is_not_null(),
        fields=fields,
        metadata=metadata,
    )

    plan = build_compiled_plan(
        TypeSpec(fields={"id": FieldSpec(type=UniversalType.INTEGER)}),
        [check],
    )
    fields.append("later")
    metadata["provenance"]["source"] = "mutated"

    compiled_check = plan.checks[0]
    assert compiled_check is not check
    assert compiled_check.fields == ("id",)
    assert compiled_check.metadata["provenance"]["source"] == "initial"
    with pytest.raises(TypeError):
        compiled_check.metadata["new"] = "value"




def test_thaw_restores_named_field_order_at_every_declaration_level():
    spec = TypeSpec(fields={
        "outer": FieldSpec(fields={
            "second": FieldSpec(type=UniversalType.INTEGER),
            "first": FieldSpec(type=UniversalType.STRING),
        }),
        "tail": FieldSpec(type=UniversalType.BOOLEAN),
    })
    plan = build_compiled_plan(spec, [])
    spec.fields = {"tail": spec.fields["tail"], "outer": spec.fields["outer"]}
    thawed = thaw_value(plan.declaration)
    assert list(thawed.fields) == ["outer", "tail"]
    assert list(thawed.fields["outer"].fields) == ["second", "first"]
def test_thaw_rejects_unregistered_dataclass_identifiers():
    with pytest.raises(ValueError, match="unsupported frozen dataclass"):
        thaw_value(
            {
                "__dataclass__": "pathlib:Path",
                "fields": {},
            }
        )


from fixtures.backend_registry import ALL_BACKENDS  # noqa: E402
from mountainash.validation.checks import RelationRule, ScalarRule  # noqa: E402
from mountainash.validation.identity import RowIdentity  # noqa: E402
from mountainash.validation.runner import ValidationRunner  # noqa: E402

_SPEC = TypeSpec(fields={
    "v": FieldSpec(type=UniversalType.INTEGER),
    "g": FieldSpec(type=UniversalType.INTEGER),
})

def _run(plan, data):
    return ValidationRunner().validate_relation(
        ma.relation(data), plan=plan, identity=RowIdentity(kind="none")
    )


@pytest.mark.parametrize("dtype,value", [
    (ma.MountainashDtype.I8, 127),
    (ma.DecimalDtype(5, 2), 12),
])
def test_precise_declarations_execute_through_compiled_validation(dtype, value):
    import polars as pl
    field = FieldSpec(dtype=dtype,
                      rounding="half_to_even" if isinstance(dtype, ma.DecimalDtype) else None)
    spec = TypeSpec(fields={"value": field}, missing_values=[])
    plan = build_compiled_plan(spec, [
        RowRule(id="value_kept", expr=ma.col("value").eq(value)),
    ])
    spec.fields["value"] = FieldSpec(dtype=ma.MountainashDtype.BOOL)
    for _ in range(2):
        assert _run(plan, pl.DataFrame({"value": [value]})).passes


def test_native_validation_snapshot_owns_executable_parameters():
    # Native Polars override ownership is exercised on its owning backend.
    import datetime
    import polars as pl
    native = pl.Datetime("ns")
    field = FieldSpec(backend_type=native)
    spec = TypeSpec(fields={"at": field}, missing_values=[])
    checks = [RowRule(id="instant", expr=ma.col("at").eq(datetime.datetime(1970, 1, 1, microsecond=1000)))]
    old = build_compiled_plan(spec, checks)
    native.time_unit = "us"
    new_spec = TypeSpec(fields={"at": FieldSpec(backend_type=native)}, missing_values=[])
    new = build_compiled_plan(new_spec, checks)
    data = pl.DataFrame({"at": [1_000_000]})
    assert not _run(new, data).passes
    for _ in range(2):
        assert _run(old, data).passes


def _threshold():
    expr = ma.col("v").lt(ma.lit(10))

    def mutate():
        expr._node.arguments[1] = ma.lit(1)._node

    return RowRule(id="limit", expr=expr), mutate, {"v": [5], "g": [1]}


def _membership():
    expr = ma.col("v").is_in([1, 2])

    def mutate():
        expr._node.arguments[1] = ma.col("v").is_in([1, 2, 5])._node.arguments[1]
        expr._node.options.update(ma.col("v").is_in([1, 2, 5])._node.options)

    return RowRule(id="member", expr=expr), mutate, {"v": [5], "g": [1]}


def _conditional():
    expr = ma.when(ma.col("v").gt(1)).then(ma.lit(True)).otherwise(ma.lit(False))

    def mutate():
        expr._node.conditions[0] = (ma.col("v").gt(100)._node, ma.lit(True)._node)

    return RowRule(id="cond", expr=expr), mutate, {"v": [5], "g": [1]}


def _window_partition():
    expr = ma.col("v").sum().over("g").gt(5)

    def mutate():
        expr._node.arguments[0].window_spec.partition_by.clear()

    return RowRule(id="window", expr=expr), mutate, {"v": [3, 3, 3], "g": [1, 1, 2]}


def _scalar_rule():
    expr = ma.col("v").sum().gt(ma.lit(10))

    def mutate():
        expr._node.arguments[1] = ma.lit(1)._node

    return ScalarRule(id="total", expr=expr), mutate, {"v": [5], "g": [1]}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    "case",
    [_threshold, _membership, _conditional, _window_partition, _scalar_rule],
    ids=lambda f: f.__name__.strip("_"),
)
def test_compiled_plan_owns_expression_declarations(
    case, backend_name, backend_factory, request
):
    if case is _window_partition and backend_name == "ibis-polars":
        request.applymarker(
            pytest.mark.xfail(
                strict=True,
                reason="Ibis Polars cannot compile window functions (BackendCapabilityError)",
            )
        )
    check, mutate, rows = case()
    old = build_compiled_plan(_SPEC, [check])
    verdict_before = _run(old, backend_factory.create(rows, backend_name)).passes
    mutate()
    new = build_compiled_plan(_SPEC, [check])
    data = backend_factory.create(rows, backend_name)
    # Mutation flips the verdict of newly compiled plans only.
    assert verdict_before != _run(new, data).passes
    for _ in range(2):
        assert _run(old, data).passes is verdict_before


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_relation_rule_callback_stays_executable(backend_name, backend_factory):
    class NoCopy:
        def __deepcopy__(self, memo):
            raise AssertionError("opaque callback state must not be copied")

        def __call__(self, relation):
            return relation.filter(ma.col("v").gt(10))

    plan = build_compiled_plan(_SPEC, [RelationRule(id="none_over_ten", plan=NoCopy())])
    data = backend_factory.create({"v": [1, 2], "g": [1, 1]}, backend_name)
    assert _run(plan, data).passes
