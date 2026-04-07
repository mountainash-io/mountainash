from cross_backend.argument_types._introspection import ProtocolParam, introspect_protocols


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
