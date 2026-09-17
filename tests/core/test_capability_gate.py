"""Compile-time capability gate at the expression visitor (spec Section 2)."""

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.core.capabilities import (
    Boundary,
    WILDCARD_PARAM,
    Enforcement,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)
from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


@pytest.fixture(autouse=True)
def _isolated_registry():
    snapshot = CapabilityRegistry.snapshot()
    yield
    CapabilityRegistry.restore(snapshot)


def _register(level, param="substring", condition=None, **kw):
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_STR.CONTAINS,
                param=param,
                level=level,
                backend=CONST_BACKEND.POLARS,
                message="test-fact: contains substring gated",
                workaround="use a literal",
                since="2026-07-05",
                condition=condition,
                **kw,
            )
        ],
    )


DF = pl.DataFrame({"text": ["abc"], "pat": ["b"]})


class TestLiteralOnlyGate:
    def test_dynamic_arg_raises_at_compile_with_metadata(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        with pytest.raises(BackendCapabilityError) as exc_info:
            ma.col("text").str.contains(ma.col("pat")).compile(DF)
        assert "test-fact" in str(exc_info.value)
        assert "Workaround: use a literal" in str(exc_info.value)

    def test_literal_arg_passes_raw_value(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        compiled = ma.col("text").str.contains("b").compile(DF)
        assert DF.select(compiled).to_series().to_list() == [True]

    def test_lit_node_unwrapped_to_raw(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        compiled = ma.col("text").str.contains(ma.lit("b")).compile(DF)
        assert DF.select(compiled).to_series().to_list() == [True]


class TestUnsupportedGate:
    def test_raises_before_backend_call(self):
        _register(CapabilityLevel.UNSUPPORTED)
        with pytest.raises(BackendCapabilityError):
            ma.col("text").str.contains("b").compile(DF)


class TestConditionIsProseOnly:
    """Backlog 66a: a prose condition no longer disables gating.

    This class previously asserted the inverse (TestConditionedFactsDoNotGate).
    The spec makes that behaviour the defect: adding documentation to a fact
    silently turned its capability off, with every test still passing.
    """

    def test_conditioned_fact_with_default_enforcement_gates(self):
        _register(CapabilityLevel.LITERAL_ONLY, condition="only when x")
        with pytest.raises(BackendCapabilityError):
            ma.col("text").str.contains(ma.col("pat")).compile(DF)

    def test_non_gate_enforcement_skips_the_structural_gate(self):
        from mountainash.core.capabilities import Boundary, Enforcement

        _register(
            CapabilityLevel.LITERAL_ONLY,
            condition="collection compiles to an expression",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            boundary=Boundary.MATERIALIZE,
            native_errors=(ValueError,),
        )
        compiled = ma.col("text").str.contains(ma.col("pat")).compile(DF)
        assert compiled is not None


class TestGateBypass:
    def test_enforce_capabilities_false_skips_gate(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        from mountainash.expressions.backends.expression_systems.polars import (
            PolarsExpressionSystem,  # composed system, exported by polars/__init__.py
        )
        from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

        visitor = UnifiedExpressionVisitor(PolarsExpressionSystem(), enforce_capabilities=False)
        node = ma.col("text").str.contains(ma.col("pat"))._node
        assert visitor.visit(node) is not None  # native polars accepts Expr here


class TestPolymorphicPreserved:
    def test_is_in_literal_list_and_expression_paths_still_work(self):
        # Regression: _raw_value_functions semantics now come from core facts.
        df = pl.DataFrame({"v": [1, 2], "other": [1, 3]})
        lit_path = ma.t_col("v").t_is_in([1, 5]).compile(df)
        assert lit_path is not None
        # Expression MEMBERS (OR-chain path) still work. A *bare* column
        # collection now raises BareExpressionCollectionError — use
        # .list.t_contains for per-row list membership.
        expr_path = ma.t_col("v").t_is_in([ma.col("other")]).compile(df)
        assert expr_path is not None


def _compile_polars(expr):
    system = get_expression_system(CONST_BACKEND.POLARS)(dialect="polars")
    return UnifiedExpressionVisitor(system, enforce_capabilities=True).visit(expr._node)


@pytest.fixture
def isolated_registry():
    snap = CapabilityRegistry.snapshot()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snap)


def test_op_level_gate_raises_for_zero_arg_op(isolated_registry):
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_DT.TODAY,
                param=WILDCARD_PARAM,
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect=None,
                message="today unsupported (test)",
                since="2026-07-29",
            )
        ],
    )
    with pytest.raises(BackendCapabilityError):
        _compile_polars(ma.today())


def test_op_level_gate_ignores_dialect_scoped_expr_capable(isolated_registry):
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_DT.TODAY,
                param=WILDCARD_PARAM,
                level=CapabilityLevel.EXPR_CAPABLE,
                backend=CONST_BACKEND.POLARS,
                dialect="polars",
                message="refinement (test)",
                since="2026-07-29",
                probe_exempt="refinement",
            )
        ],
    )
    _compile_polars(ma.today())  # no raise


def test_op_level_gate_ignores_router_metadata(isolated_registry):
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_DT.TODAY,
                param=WILDCARD_PARAM,
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect=None,
                message="router only (test)",
                since="2026-07-29",
                enforcement=Enforcement.ROUTER_METADATA,  # boundary defaults to BUILD (legal)
            )
        ],
    )
    _compile_polars(ma.today())  # no raise


def test_op_level_gate_ignores_materialize_residue(isolated_registry):
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_DT.TODAY,
                param=WILDCARD_PARAM,
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect=None,
                message="residue only (test)",
                since="2026-07-29",
                enforcement=Enforcement.MATERIALIZE_RESIDUE,
                boundary=Boundary.MATERIALIZE,
                native_errors=(ValueError,),  # required for MATERIALIZE
            )
        ],
    )
    _compile_polars(ma.today())  # no raise


def test_op_level_gate_no_fact_compiles():
    _compile_polars(ma.today())  # no raise


def test_enforced_visitor_construction_bootstraps_declarations():
    """An enforcing visitor loads declarations; imports and disabled mode do not."""
    import subprocess
    import sys

    code = (
        "import mountainash.core.capabilities.bootstrap as b\n"
        "from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor\n"
        "from mountainash.core.capabilities.registry import (\n"
        "    CapabilityRegistry, _LoadState,\n"
        ")\n"
        "assert CapabilityRegistry.snapshot().load_state is _LoadState.UNINITIALIZED, (\n"
        "    'importing the visitor must not bootstrap by itself'\n"
        ")\n"
        "UnifiedExpressionVisitor(object(), enforce_capabilities=False)\n"
        "assert CapabilityRegistry.snapshot().load_state is _LoadState.UNINITIALIZED, (\n"
        "    'a non-enforcing visitor must not bootstrap'\n"
        ")\n"
        "UnifiedExpressionVisitor(object(), enforce_capabilities=True)\n"
        "assert CapabilityRegistry.snapshot().load_state is _LoadState.LOADED, (\n"
        "    'enforced visitor construction did not bootstrap declarations'\n"
        ")\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_predicate_fact_gates_expression_call():
    from mountainash.core.capabilities.schema import CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    )

    # ABS protocol: def abs(self, x, /, overflow=None) — the literal arg maps to param "x".
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_ARITH.ABS,
                param="x",
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect="polars",
                message="abs blocked when x==7",
                since="2026-08-15",
                predicate=Predicate((Clause("x", ClauseOp.EQ, 7),)),
            ),
        ],
    )
    with pytest.raises(BackendCapabilityError) as exc_info:
        ma.lit(7).abs().compile(DF)
    assert exc_info.value.limitation.predicate is not None
    assert "abs blocked" in str(exc_info.value)


def test_predicate_fact_does_not_fire_when_predicate_false():
    from mountainash.core.capabilities.schema import CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    )

    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_ARITH.ABS,
                param="x",
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect="polars",
                message="abs blocked when x==7",
                since="2026-08-15",
                predicate=Predicate((Clause("x", ClauseOp.EQ, 7),)),
            ),
        ],
    )
    compiled = ma.lit(9).abs().compile(DF)  # [x EQ 7] does not hold
    assert compiled is not None


def test_metadata_predicate_is_evaluated_after_scope_resolution():
    """A metadata fact defers in raw phase, then blocks only its matching type."""
    from mountainash.core.capabilities.schema import (
        CapabilityFact,
        CapabilityLevel,
        Clause,
        ClauseOp,
        Predicate,
    )
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    )

    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [
            CapabilityFact(
                operation_key=FK_ARITH.ABS,
                param="x",
                level=CapabilityLevel.UNSUPPORTED,
                backend=CONST_BACKEND.POLARS,
                dialect="polars",
                message="float abs blocked after metadata resolution",
                since="2026-09-14",
                predicate=Predicate((Clause("__operand_types__.x.logical_kind", ClauseOp.EQ, "float"),)),
            ),
        ],
    )

    with pytest.raises(BackendCapabilityError, match="float abs blocked"):
        ma.col("value").abs().compile(pl.DataFrame({"value": [1.0]}))

    compiled = ma.col("value").abs().compile(pl.DataFrame({"value": [1]}))
    assert compiled is not None


def _structural_fact(dataframe, operation, param, **selectors):
    from mountainash.core.backend_detection import identify_backend_identity

    identity = identify_backend_identity(dataframe)
    fact = CapabilityFact(
        operation_key=operation,
        param=param,
        level=CapabilityLevel.UNSUPPORTED,
        backend=identity.family,
        dialect=identity.dialect,
        message="structural invocation restriction",
        since="2026-09-15",
        **selectors,
    )
    CapabilityRegistry.register_backend(identity.family, [fact])
    return fact


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
class TestStructuralInvocationGates:
    def test_zero_argument_window_gate_preserves_unrelated_operation(
        self, backend_name, backend_factory, collect_expr
    ):
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            SUBSTRAIT_ARITHMETIC_WINDOW as WINDOW,
        )

        df = backend_factory.create({"value": [1, 2, 3], "group": ["a"] * 3}, backend_name)
        fact = _structural_fact(df, WINDOW.ROW_NUMBER, WILDCARD_PARAM)
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(df, ma.col("value").row_number().over("group"))
        assert error.value.limitation is fact
        assert collect_expr(df, ma.col("value").abs()) == [1, 2, 3]

    def test_ntile_binds_its_real_protocol_argument(self, backend_name, backend_factory, collect_expr):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            SUBSTRAIT_ARITHMETIC_WINDOW as WINDOW,
        )

        df = backend_factory.create({"value": [1, 2, 3], "group": ["a"] * 3}, backend_name)
        fact = _structural_fact(
            df, WINDOW.NTILE, "x", predicate=Predicate((Clause("x", ClauseOp.EQ, 2),))
        )
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(df, ma.col("value").ntile(2).over("group"))
        assert error.value.limitation is fact

    @pytest.mark.parametrize("blocked", [False, True])
    def test_window_effective_descending_is_supplied(
        self, backend_name, backend_factory, collect_expr, blocked
    ):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            SUBSTRAIT_ARITHMETIC_WINDOW as WINDOW,
        )

        df = backend_factory.create({"value": [1, 2, 3], "group": ["a"] * 3}, backend_name)
        fact = _structural_fact(
            df, WINDOW.ROW_NUMBER, "descending",
            predicate=Predicate((
                Clause("descending", ClauseOp.EQ, blocked),
                Clause("descending", ClauseOp.IS_SET),
            )),
        )
        for options in ({"descending": False}, {}, {"descending": True}):
            expr = ma.col("value").row_number(**options).over("group")
            if options.get("descending", False) is blocked:
                with pytest.raises(BackendCapabilityError) as error:
                    collect_expr(df, expr)
                assert error.value.limitation is fact
            else:
                values = (
                    ma.relation(df).select(ma.col("value"), expr.alias("position"))
                    .sort("value").to_dict()["position"]
                )
                # Ibis' retained zero-based divergence does not change ordering.
                offsets = [value - min(values) for value in values]
                assert offsets == ([2, 1, 0] if options.get("descending", False) else [0, 1, 2])

    @pytest.mark.parametrize("blocked", ["throw", "null"])
    @pytest.mark.parametrize("selector", ["option", "predicate"])
    def test_cast_effective_failure_behavior_is_supplied(
        self, backend_name, backend_factory, collect_expr, blocked, selector
    ):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

        df = backend_factory.create({"value": ["1", "2"]}, backend_name)
        restriction = (
            {"option_value": blocked}
            if selector == "option"
            else {"predicate": Predicate((
                Clause("failure_behavior", ClauseOp.EQ, blocked),
                Clause("failure_behavior", ClauseOp.IS_SET),
            ))}
        )
        fact = _structural_fact(df, FKEY_SUBSTRAIT_CAST.CAST, "failure_behavior", **restriction)
        for options in ({}, {"failure_behavior": "throw"}, {"failure_behavior": "null"}):
            expr = ma.col("value").cast("i64", **options)
            if options.get("failure_behavior", "throw") == blocked:
                with pytest.raises(BackendCapabilityError) as error:
                    collect_expr(df, expr)
                assert error.value.limitation is fact
            elif backend_name == "narwhals-polars" and options.get("failure_behavior") == "null":
                # The existing native adapter refuses null-on-failure independently
                # of this injected predicate; it must not acquire its limitation.
                with pytest.raises(BackendCapabilityError) as error:
                    collect_expr(df, expr)
                assert error.value.limitation is None
            else:
                assert collect_expr(df, expr) == [1, 2]

    def test_cast_metadata_uses_current_input_scope(
        self, backend_name, backend_factory, collect_expr
    ):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

        floats = backend_factory.create({"value": [1.25, 2.25]}, backend_name)
        integers = backend_factory.create({"value": [1, 2]}, backend_name)
        fact = _structural_fact(
            floats, FKEY_SUBSTRAIT_CAST.CAST, "x",
            predicate=Predicate((Clause("__operand_types__.x.logical_kind", ClauseOp.EQ, "float"),)),
        )
        expr = ma.col("value").cast("i64")
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(floats, expr)
        assert error.value.limitation is fact
        assert collect_expr(integers, expr) == [1, 2]

    def test_window_order_operand_metadata_uses_current_input_scope(
        self, backend_name, backend_factory, collect_expr
    ):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            SUBSTRAIT_ARITHMETIC_WINDOW as WINDOW,
        )

        floats = backend_factory.create({"value": [1.25, 2.25], "group": ["a", "a"]}, backend_name)
        integers = backend_factory.create({"value": [1, 2], "group": ["a", "a"]}, backend_name)
        fact = _structural_fact(
            floats, WINDOW.ROW_NUMBER, "order_by_col",
            predicate=Predicate((
                Clause("__operand_types__.order_by_col.logical_kind", ClauseOp.EQ, "float"),
            )),
        )
        expr = ma.col("value").row_number().over("group")
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(floats, expr)
        assert error.value.limitation is fact
        values = collect_expr(integers, expr)
        assert values[1] - values[0] == 1

    def test_cast_dtype_selector_uses_canonical_value(
        self, backend_name, backend_factory, collect_expr
    ):
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

        df = backend_factory.create({"value": [1.25, 2.25]}, backend_name)
        fact = _structural_fact(df, FKEY_SUBSTRAIT_CAST.CAST, "dtype", option_value="i64")
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(df, ma.col("value").cast("i64"))
        assert error.value.limitation is fact
        assert collect_expr(df, ma.col("value").cast("f64")) == [1.25, 2.25]


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
class TestConditionalInvocationGates:
    def test_empty_chain_has_no_conditional_invocation(self, backend_name, backend_factory, collect_expr):
        from mountainash.expressions.core.expression_nodes import IfThenNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL

        df = backend_factory.create({"value": [-1, 1, 3]}, backend_name)
        fact = _structural_fact(df, FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE, WILDCARD_PARAM)
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(df, ma.when(ma.col("value") > 0).then(7).otherwise(9))
        assert error.value.limitation is fact
        literal = ma.lit(11)
        empty = type(literal).create(IfThenNode(conditions=[], else_clause=literal.node))
        result = ma.relation(df).select(ma.col("value"), empty.alias("result")).to_dict()
        assert result["result"] == [11, 11, 11]

    @pytest.mark.parametrize("blocked", [7, 8, 42])
    def test_each_link_binds_all_protocol_operands(
        self, backend_name, backend_factory, collect_expr, blocked
    ):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL

        df = backend_factory.create({"value": [-1, 1, 3]}, backend_name)
        fact = _structural_fact(
            df, FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE, "if_true",
            predicate=Predicate((
                Clause("if_true", ClauseOp.EQ, blocked),
                Clause("condition", ClauseOp.IS_SET),
                Clause("if_true", ClauseOp.IS_SET),
                Clause("if_false", ClauseOp.IS_SET),
            )),
        )
        expr = ma.when(ma.col("value") < 0).then(7).when(ma.col("value") < 2).then(8).otherwise(9)
        if blocked in (7, 8):
            with pytest.raises(BackendCapabilityError) as error:
                collect_expr(df, expr)
            assert error.value.limitation is fact
        else:
            assert collect_expr(df, expr) == [7, 8, 9]

    @pytest.mark.parametrize("branch", [7, 8])
    def test_false_operand_distinguishes_literal_from_logical_tail(
        self, backend_name, backend_factory, collect_expr, branch
    ):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL

        df = backend_factory.create({"value": [-1, 1, 3]}, backend_name)
        fact = _structural_fact(
            df, FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE, "if_false",
            predicate=Predicate((
                Clause("if_true", ClauseOp.EQ, branch),
                Clause("if_false", ClauseOp.IS_LITERAL),
            )),
        )
        expr = ma.when(ma.col("value") < 0).then(7).when(ma.col("value") < 2).then(8).otherwise(9)
        if branch == 8:
            with pytest.raises(BackendCapabilityError) as error:
                collect_expr(df, expr)
            assert error.value.limitation is fact
        else:
            assert collect_expr(df, expr) == [7, 8, 9]

    @pytest.mark.parametrize("branch", [7, 8])
    def test_link_metadata_describes_its_logical_false_operand(
        self, backend_name, backend_factory, collect_expr, branch
    ):
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL

        df = backend_factory.create({"value": [-1, 1, 3]}, backend_name)
        fact = _structural_fact(
            df, FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE, "if_false",
            predicate=Predicate((
                Clause("if_true", ClauseOp.EQ, branch),
                Clause("__operand_types__.if_false.logical_kind", ClauseOp.EQ, "integer"),
            )),
        )
        matching = ma.when(ma.col("value") < 0).then(7).when(ma.col("value") < 2).then(8).otherwise(9)
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(df, matching)
        assert error.value.limitation is fact
        nonmatching = ma.when(ma.col("value") < 0).then(7).when(ma.col("value") < 2).then(8.5).otherwise(9.5)
        assert collect_expr(df, nonmatching) == [7.0, 8.5, 9.5]

    def test_false_ordinary_clause_still_requires_operand_metadata(
        self, backend_name, backend_factory, collect_expr
    ):
        from mountainash.core.backend_detection import identify_backend_identity
        from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL

        df = backend_factory.create({"value": [1]}, backend_name)
        _structural_fact(
            df, FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE, "if_false",
            predicate=Predicate((
                Clause("if_true", ClauseOp.EQ, 42),
                Clause("__operand_types__.if_false.logical_kind", ClauseOp.EQ, "integer"),
            )),
        )
        expr = ma.when(ma.lit(True)).then(7).otherwise(9)
        identity = identify_backend_identity(df)
        system = get_expression_system(identity.family)(dialect=identity.dialect)
        with pytest.raises(BackendCapabilityError) as error:
            UnifiedExpressionVisitor(system).visit(expr.node)
        assert error.value.limitation is None
        assert collect_expr(df, expr) == [7]

