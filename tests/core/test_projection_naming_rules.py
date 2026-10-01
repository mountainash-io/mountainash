"""Backend-independent authoring contracts for projection declarations."""

from dataclasses import replace
from enum import Enum

import pytest

import mountainash as ma
from mountainash.core.constants import SortField
from mountainash.expressions.core.expression_nodes import (
    FieldReferenceNode,
    LiteralNode,
    ScalarFunctionNode,
    SingularOrListNode,
    WindowFunctionNode,
)
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import WindowSpec
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_NAME,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
    FKEY_MOUNTAINASH_WINDOW,
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
    FKEY_SUBSTRAIT_SCALAR_STRING,
    SUBSTRAIT_ARITHMETIC_WINDOW,
)
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)


def test_registered_operations_declare_projection_semantics():
    missing = [
        key
        for key in ExpressionFunctionRegistry.list_all()
        if getattr(ExpressionFunctionRegistry.get(key), "projection_rule", None) is None
    ]
    assert not missing, f"Missing projection semantics: {missing}"


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"name_kind": "guess"}, "Unknown projection rule kind"),
        ({"cardinality_kind": "guess"}, "Unknown projection rule kind"),
        ({"operand": -1}, "operand index"),
        ({"operand": True}, "operand index"),
        ({"operand": 1.5}, "operand index"),
        ({"name_kind": "fixed"}, "requires a value"),
        ({"name_kind": "option"}, "requires a value"),
        ({"name_kind": "requires_alias"}, "requires a reason"),
        ({"name_kind": "internal", "reason": ""}, "requires a reason"),
    ],
)
def test_projection_rule_rejects_invalid_declarations(kwargs, message):
    from mountainash.expressions.core.expression_system.function_mapping.output_rules import (
        ProjectionRule,
    )

    arguments = {"name_kind": "operand", "cardinality_kind": "propagate", **kwargs}
    with pytest.raises(ValueError, match=message):
        ProjectionRule(**arguments)


def test_function_definition_validates_optional_projection_rule():
    definition = ExpressionFunctionRegistry.get(ExpressionFunctionRegistry.list_all()[0])
    with pytest.raises(TypeError, match="projection_rule must be"):
        replace(definition, projection_rule="operand")
    # Custom/temporary definitions may still compile without projection metadata.
    assert replace(definition, projection_rule=None).projection_rule is None


# Pure AST contracts: no backend is compiled or executed by these tests.
# These counterexamples catch first-child-only traversal, invented cardinality,
# and backend-name guessing; declaration inventory tests cannot detect those.
@pytest.mark.parametrize(
    "build, expected",
    [
        (lambda: ma.col("n").fill_null(0), ("n",)),
        (lambda: ma.lit(1) + ma.col("n"), ("literal",)),
        (lambda: ma.col("n").alias("z").fill_null(0), ("z",)),
        (lambda: ma.col("n").fill_null(0).name.suffix("_f"), ("n_f",)),
        (lambda: ma.col("n").alias(""), ("",)),
        (lambda: ma.col("n").alias("z").name.prefix("p_").alias("q"), ("q",)),
        (lambda: ma.col("n").name.to_uppercase(), ("N",)),
        (lambda: ma.col("N").name.to_lowercase(), ("n",)),
        (lambda: ma.when(ma.col("n") > 0).then(ma.col("m")).otherwise(ma.col("n")), ("m",)),
        (lambda: ma.col("n").is_in([2, 4]), ("n",)),
        (lambda: ma.col("n").t_is_in([]), ("n",)),
        (lambda: ma.col("n") + ma.col("^absent$"), ()),
        (lambda: ma.when(ma.col("^absent$") > 0).then(ma.col("n")).otherwise(ma.col("m")), ()),
        (lambda: ma.when(ma.col("n") > 0).then(ma.col("n")).otherwise(ma.col("^absent$")), ()),
        (
            lambda: (
                ma.when(ma.col("n") > 0).then(ma.col("n")).when(ma.col("m") > 0).then(ma.col("^absent$")).otherwise(0)
            ),
            (),
        ),
        (lambda: ma.col("^absent$").cast(int).alias("x").name.suffix("!"), ()),
        (lambda: ma.col("*").name.prefix("p_"), ("p_n", "p_m")),
        (lambda: ma.col("n") + ma.col("*"), (None, None)),
        (lambda: ma.col("*") + ma.col("n"), (None, None)),
        (lambda: ma.col("*").alias("x"), ("x", "x")),
        (lambda: ma.col("n").sum().over("m"), ("n",)),
        (lambda: ma.col("n").shift(1).over("m"), ("n",)),
        (lambda: FieldReferenceNode(field="n"), ("n",)),
        (lambda: "^absent$", ()),
        (lambda: "*", ("n", "m")),
        (
            lambda: SingularOrListNode(
                value=FieldReferenceNode(field="n"), options=[FieldReferenceNode(field="^absent$")]
            ),
            (),
        ),
        (
            lambda: ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT_WS,
                arguments=[LiteralNode(value=","), FieldReferenceNode(field="n"), FieldReferenceNode(field="m")],
            ),
            ("n",),
        ),
        (
            lambda: ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONCAT_WS,
                arguments=[FieldReferenceNode(field="^absent$"), FieldReferenceNode(field="n")],
            ),
            (),
        ),
        (
            lambda: ScalarFunctionNode(function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT_RECORDS, arguments=[]),
            ("len",),
        ),
    ],
)
def test_ast_output_names_and_cardinality(build, expected):
    from mountainash.expressions.core.output_names import resolve_output_names

    result = resolve_output_names(build(), input_names=("n", "m"))
    assert result.names == expected
    if not expected or len(expected) > 1:
        assert result.kind == "expansion"
        assert result.scalar_name is None


@pytest.mark.parametrize("input_names, expected", [(None, None), ((), ()), (("n",), ("n",))])
def test_selector_evidence_distinguishes_unknown_empty_and_one(input_names, expected):
    from mountainash.expressions.core.output_names import resolve_output_names

    result = resolve_output_names(ma.col("*"), input_names=input_names)
    assert (result.kind, result.names, result.scalar_name) == ("expansion", expected, None)


@pytest.mark.parametrize(
    "build, kind, hint",
    [
        (lambda: ma.col("^n.*$"), "expansion", None),
        (lambda: ma.col("*") + ma.col("^n$"), "expansion", None),
        (lambda: ma.col("n") + ma.native(object()), "opaque", "n"),
        (lambda: ma.when(ma.native(object())).then(ma.col("n")).otherwise(0), "opaque", "n"),
        (lambda: ma.when(ma.col("n") > 0).then(ma.col("n")).otherwise(ma.native(object())), "opaque", "n"),
        (lambda: ma.native(object()).alias("x").name.suffix("_f"), "opaque", "x_f"),
        (
            lambda: ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
                arguments=[LiteralNode(value=object(), is_native=True)],
                options={"name": ""},
            ),
            "opaque",
            "",
        ),
    ],
)
def test_unknown_cardinality_survives_composition(build, kind, hint):
    from mountainash.expressions.core.output_names import resolve_output_names

    result = resolve_output_names(build(), input_names=("n", "m"))
    assert (result.kind, result.names, result.name_hint) == (kind, None, hint)
    assert result.scalar_name is None


def test_non_ast_objects_are_not_probed_for_synthetic_attributes():
    from mountainash.expressions.core.output_names import resolve_output_names

    class NativeLike:
        def __getattr__(self, name):
            raise AssertionError(f"native object inspected: {name}")

    result = resolve_output_names(NativeLike())
    assert (result.kind, result.names) == ("opaque", None)


class UnregisteredKey(Enum):
    OPERATION = "operation"


@pytest.mark.parametrize("registered", [False, True])
@pytest.mark.parametrize(
    "wrap",
    [
        lambda expr: expr,
        lambda expr: expr.alias("x"),
        lambda expr: ma.col("n") + expr,
        lambda expr: (ma.col("n") + expr).alias("x"),
        lambda expr: ma.col("n").list.agg(expr),
        lambda expr: ma.col("n").t_is_in([expr]),
    ],
)
def test_missing_classification_is_not_hidden_by_composition(registered, wrap, monkeypatch):
    from mountainash.expressions.core.output_names import resolve_output_names

    key = UnregisteredKey.OPERATION
    if registered:
        definition = ExpressionFunctionRegistry.get(ExpressionFunctionRegistry.list_all()[0])
        monkeypatch.setitem(
            ExpressionFunctionRegistry._functions, key, replace(definition, function_key=key, projection_rule=None)
        )
    expr = ma.col("n").create(ScalarFunctionNode(function_key=key, arguments=[FieldReferenceNode(field="n")]))
    result = resolve_output_names(wrap(expr), input_names=("n",))
    assert result.kind == "unclassified"
    assert result.names is None
    assert result.function_key == key
    assert result.reason
    if not registered:
        with pytest.raises(KeyError):
            ExpressionFunctionRegistry.get(key)


@pytest.mark.parametrize(
    "key",
    [SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK, SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST],
)
def test_declared_single_requires_alias_can_be_named(key):
    from mountainash.expressions.core.output_names import resolve_output_names

    node = WindowFunctionNode(function_key=key, window_spec=WindowSpec(order_by=[SortField("*")]))
    result = resolve_output_names(node)
    assert (result.kind, result.names, result.function_key) == ("unclassified", (None,), key)
    assert result.reason
    aliased = ScalarFunctionNode(function_key=FKEY_MOUNTAINASH_NAME.ALIAS, arguments=[node], options={"name": "x"})
    result = resolve_output_names(aliased)
    assert (result.kind, result.names, result.scalar_name) == ("single", ("x",), "x")


@pytest.mark.parametrize(
    "compose",
    [
        lambda unnamed: ma.col("n") + unnamed,
        lambda unnamed: ma.when(unnamed > 0).then(ma.col("n")).otherwise(0),
        lambda unnamed: ma.when(ma.col("m") > 0).then(ma.col("n")).otherwise(unnamed),
    ],
)
def test_non_naming_operand_limitation_does_not_invalidate_resolved_name(compose):
    from mountainash.expressions.core.output_names import resolve_output_names

    unnamed = ma.col("n").create(WindowFunctionNode(function_key=SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK))
    result = resolve_output_names(compose(unnamed))
    assert (result.kind, result.names, result.scalar_name) == ("single", ("n",), "n")
    assert result.function_key is None
    assert result.reason is None
    # The same limitation still matters when this operand supplies the name.
    result = resolve_output_names(unnamed + ma.col("n"))
    assert (result.kind, result.names) == ("unclassified", (None,))
    assert result.function_key == SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK


@pytest.mark.parametrize(
    "compose, hint",
    [
        (lambda expr: expr, None),
        (lambda expr: expr.alias("x"), "x"),
        (lambda expr: expr.alias("x").name.suffix("!"), "x!"),
        (lambda expr: ma.col("n") + expr, "n"),
    ],
)
def test_requires_alias_preserves_native_passthrough_uncertainty(compose, hint):
    from mountainash.expressions.core.output_names import resolve_output_names

    node = WindowFunctionNode(
        function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTILE,
        arguments=[LiteralNode(value=object(), is_native=True)],
    )
    result = resolve_output_names(compose(ma.col("n").create(node)))
    assert (result.kind, result.names, result.name_hint) == ("opaque", None, hint)
    assert result.scalar_name is None


def test_naming_only_limitation_cannot_mask_opaque_later_operand():
    from mountainash.expressions.core.output_names import resolve_output_names

    unnamed = ma.col("n").create(WindowFunctionNode(function_key=SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK))
    result = resolve_output_names((unnamed + ma.native(object())).alias("x"))
    assert (result.kind, result.names, result.name_hint) == ("opaque", None, "x")


@pytest.mark.parametrize(
    "key",
    [
        SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
        SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
        SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
        FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE,
        FKEY_MOUNTAINASH_WINDOW.RANK_MAX,
    ],
)
@pytest.mark.parametrize(
    "order, kind, names",
    [
        ("n", "single", ("n",)),
        (None, "unclassified", (None,)),
        (object(), "opaque", None),
        ("^absent$", "expansion", ()),
        ("*", "expansion", (None, None)),
    ],
)
def test_first_order_context_is_retained_without_partition_fallback(key, order, kind, names):
    from mountainash.expressions.core.output_names import resolve_output_names

    node = WindowFunctionNode(
        function_key=key,
        window_spec=WindowSpec(partition_by=["partition"], order_by=[] if order is None else [SortField(order)]),
    )
    result = resolve_output_names(node, input_names=("n", "m"))
    assert (result.kind, result.names) == (kind, names)
    if kind == "unclassified":
        assert result.function_key == key
        assert result.reason


@pytest.mark.parametrize("method", ["filter", "agg"])
@pytest.mark.parametrize("field, expected", [("n", ("n",)), ("*", ("n", "m")), ("^absent$", ())])
def test_list_context_consumes_body_without_inventing_outer_outputs(method, field, expected):
    from mountainash.expressions.core.output_names import resolve_output_names

    expression = getattr(ma.col(field).list, method)(ma.native(object()))
    result = resolve_output_names(expression, input_names=("n", "m"))
    assert result.names == expected


@pytest.mark.parametrize(
    "receiver, field, kind, names",
    [
        ("n", "child", "single", ("child",)),
        ("n", "*", "expansion", None),
        ("n", "^child$", "expansion", None),
        ("^absent$", "child", "expansion", ()),
        ("*", "child", "expansion", ("child", "child")),
    ],
)
def test_struct_field_uses_nested_names_not_top_level_selector_evidence(receiver, field, kind, names):
    from mountainash.expressions.core.output_names import resolve_output_names

    result = resolve_output_names(ma.col(receiver).struct.field(field), input_names=("n", "m"))
    assert (result.kind, result.names) == (kind, names)


def test_internal_collection_is_not_projectable():
    from mountainash.expressions.core.output_names import resolve_output_names

    node = ScalarFunctionNode(function_key=FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES, arguments=[])
    result = resolve_output_names(node)
    assert result.kind == "internal"
    assert result.scalar_name is None
    assert result.reason


def test_ntile_bucket_operand_can_expand_without_a_portable_name():
    from mountainash.expressions.core.output_names import resolve_output_names

    node = WindowFunctionNode(
        function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTILE, arguments=[FieldReferenceNode(field="^absent$")]
    )
    result = resolve_output_names(node, input_names=("n",))
    assert result.names == ()


@pytest.mark.parametrize(
    "wrap, expected",
    [
        (lambda expr: expr, (None, None)),
        (lambda expr: expr + 1, (None, None)),
        (lambda expr: expr.alias("x"), ("x", "x")),
        (lambda expr: expr.alias("x").name.suffix("!"), ("x!", "x!")),
    ],
)
def test_requires_alias_does_not_collapse_known_multiple_outputs(wrap, expected):
    from mountainash.expressions.core.output_names import resolve_output_names

    node = WindowFunctionNode(function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTILE, arguments=[FieldReferenceNode(field="*")])
    expression = ma.col("n").create(node)
    result = resolve_output_names(wrap(expression), input_names=("n", "m"))
    assert result.names == expected
    assert result.scalar_name is None


@pytest.mark.parametrize("body", [ma.col("^absent$"), ma.col("*")])
def test_list_body_selectors_are_consumed_in_nested_context(body):
    from mountainash.expressions.core.output_names import resolve_output_names

    result = resolve_output_names(ma.col("n").list.agg(body), input_names=("n", "m"))
    assert (result.kind, result.names) == ("single", ("n",))


@pytest.mark.parametrize("unnamed_receiver, expected", [(True, (None,)), (False, ("n",))])
def test_list_context_keeps_cardinality_separate_from_missing_names(unnamed_receiver, expected):
    from mountainash.expressions.core.output_names import resolve_output_names

    unnamed = ma.col("n").create(WindowFunctionNode(function_key=SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK))
    expression = unnamed.list.agg(ma.lit(1)) if unnamed_receiver else ma.col("n").list.agg(unnamed)
    result = resolve_output_names(expression)
    assert result.names == expected
    aliased = resolve_output_names(expression.alias("x"))
    assert (aliased.kind, aliased.names) == ("single", ("x",))


def test_resolver_is_immutable_for_reused_expression():
    from dataclasses import FrozenInstanceError

    from mountainash.expressions.core.output_names import resolve_output_names

    expr = ma.col("*").alias("x")
    before = expr._node.model_dump()
    first = resolve_output_names(expr, input_names=("n", "m"))
    second = resolve_output_names(expr, input_names=())
    assert first.names == ("x", "x")
    assert second.names == ()
    assert expr._node.model_dump() == before
    with pytest.raises(FrozenInstanceError):
        first.names = ()
