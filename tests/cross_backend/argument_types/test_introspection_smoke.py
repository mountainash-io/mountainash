from cross_backend.argument_types._introspection import ProtocolParam, introspect_protocols
from cross_backend.argument_types._coverage_guard_helpers import (
    canonicalize_tested_param,
    registry_protocol_ref,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_DT,
)


def test_introspector_returns_non_empty():
    params = introspect_protocols()
    assert len(params) > 0, "introspector found no parameters"
    assert all(isinstance(p, ProtocolParam) for p in params)


def test_introspector_classifies_contains_substring_as_argument():
    params = introspect_protocols()
    match = [p for p in params if p.op_name == "contains" and p.param_name == "substring"]
    assert len(match) == 1
    assert match[0].kind == "argument"


def test_introspector_classifies_round_s_as_option():
    # Note: the rounding protocol's round() uses param name `s` (Substrait spec),
    # not `decimals`, so the smoke test matches the actual signature.
    params = introspect_protocols()
    match = [p for p in params if p.op_name == "round" and p.param_name == "s"]
    assert len(match) == 1
    assert match[0].kind == "option"


def test_registry_protocol_ref_resolves_enum_to_protocol_method_name():
    ref = registry_protocol_ref(FK_ARITH.MODULO)
    assert ref is not None
    assert ref.protocol_name == "SubstraitScalarArithmeticExpressionSystemProtocol"
    assert ref.op_name == "modulus"


def test_canonicalize_tested_param_preserves_category_provenance():
    ref = canonicalize_tested_param("test_arg_types_arithmetic", FK_ARITH.ADD, "x")
    assert ref.protocol_name == "SubstraitScalarArithmeticExpressionSystemProtocol"
    assert ref.op_name == "add"
    assert ref.param_name == "x"
    assert ref.category == "arithmetic"
    assert ref.registry_wired is True


def test_canonicalize_tested_param_resolves_unregistered_enum_by_name():
    ref = canonicalize_tested_param(
        module_name="test_arg_types_datetime",
        original_key=FK_DT.LOCAL_TIMESTAMP,
        param_name="x",
    )
    assert ref.protocol_name == "SubstraitScalarDatetimeExpressionSystemProtocol"
    assert ref.op_name == "local_timestamp"
    assert ref.registry_wired is False
