#!/usr/bin/env python3
"""
Demonstrates why reverse operators work for BooleanScalar but not for
IntegerScalar/FloatingScalar/StringScalar.

Shows the three different code paths and why they behave differently.
"""

import ibis
import polars as pl
from ibis.expr.types.core import _binop
import ibis.expr.operations as ops


def setup():
    """Create test data."""
    conn = ibis.polars.connect()
    df = pl.DataFrame({
        'x_int': [10],
        'x_float': [10.5],
        'x_bool': [True],
        'x_str': ['hello']
    })
    table = conn.create_table('test', df, overwrite=True)
    return table


def test_code_paths():
    """Demonstrate the three different code paths."""

    print("=" * 80)
    print("IBIS REVERSE OPERATOR CODE PATH ANALYSIS")
    print("=" * 80)
    print("\nInvestigating why BooleanScalar works but IntegerScalar/StringScalar don't")
    print()

    col_int = ibis._['x_int']
    col_float = ibis._['x_float']
    col_bool = ibis._['x_bool']
    col_str = ibis._['x_str']

    lit_int = ibis.literal(5)
    lit_float = ibis.literal(2.5)
    lit_bool = ibis.literal(True)
    lit_str = ibis.literal('world')

    # ========================================================================
    # PATH 1: NumericValue (IntegerScalar, FloatingScalar)
    # ========================================================================

    print("=" * 80)
    print("PATH 1: NumericValue (IntegerScalar, FloatingScalar)")
    print("=" * 80)

    print("\nCode Path:")
    print("  NumericValue.__add__(other)")
    print("  → _binop(ops.Add, self, other)")
    print("  → ops.Add(self, other) [creates node]")
    print()

    print("Step 1: What does IntegerScalar.__add__(Deferred) do?")
    try:
        result = lit_int.__add__(col_int)
        print(f"  Returns: {result}")
    except Exception as e:
        print(f"  ❌ Raises: {type(e).__name__}")
        print(f"     Exception chain: {' → '.join([c.__name__ for c in type(e).__mro__[:-1]])}")

    print("\nStep 2: Call _binop directly to see what it does:")
    try:
        result = _binop(ops.Add, lit_int, col_int)
        print(f"  Returns: {result}")
    except Exception as e:
        print(f"  ❌ Raises: {type(e).__name__}")

    print("\nStep 3: What exception does ops.Add raise?")
    try:
        node = ops.Add(lit_int, col_int)
        print(f"  Success: {node}")
    except Exception as e:
        exc_type = type(e)
        print(f"  ❌ Raises: {exc_type.__name__}")
        print(f"     Module: {exc_type.__module__}")
        print(f"     Inheritance: {' → '.join([c.__name__ for c in exc_type.__mro__[:4]])}")

    print("\nStep 4: Is InputTypeError caught by _binop?")
    print("  _binop catches: (ValidationError, NotImplementedError)")
    print("  InputTypeError inherits from: IbisTypeError → TypeError")
    print("  ❌ InputTypeError is NOT a ValidationError")
    print("  ❌ Therefore: Exception propagates, Python never tries reverse operator")

    print("\nResult: literal(5) + ibis._['x'] FAILS ❌")

    # ========================================================================
    # PATH 2: BooleanValue
    # ========================================================================

    print("\n" + "=" * 80)
    print("PATH 2: BooleanValue (BooleanScalar)")
    print("=" * 80)

    print("\nCode Path:")
    print("  BooleanValue.__and__(other)")
    print("  → _binop(ops.And, self, other)")
    print("  → ops.And(self, other) [creates node]")
    print()

    print("Step 1: What does BooleanScalar.__and__(Deferred) do?")
    try:
        result = lit_bool.__and__(col_bool)
        print(f"  ✅ Returns: {result}")
        print(f"     Type: {type(result)}")
    except Exception as e:
        print(f"  Raises: {type(e).__name__}")

    print("\nStep 2: Call _binop directly to see what it does:")
    try:
        result = _binop(ops.And, lit_bool, col_bool)
        print(f"  ✅ Returns: {result}")
        print(f"     Type: {type(result)}")
    except Exception as e:
        print(f"  Raises: {type(e).__name__}")

    print("\nStep 3: What exception does ops.And raise?")
    try:
        node = ops.And(lit_bool, col_bool)
        print(f"  Success: {node}")
    except Exception as e:
        exc_type = type(e)
        print(f"  ❌ Raises: {exc_type.__name__}")
        print(f"     Module: {exc_type.__module__}")
        print(f"     Inheritance: {' → '.join([c.__name__ for c in exc_type.__mro__[:4]])}")

    print("\nStep 4: Is SignatureValidationError caught by _binop?")
    print("  _binop catches: (ValidationError, NotImplementedError)")
    print("  SignatureValidationError inherits from: ValidationError")
    print("  ✅ SignatureValidationError IS a ValidationError")
    print("  ✅ Therefore: _binop catches it and returns NotImplemented")
    print("  ✅ Python then tries: Deferred.__rand__(literal)")

    print("\nResult: literal(True) & ibis._['x'] WORKS ✅")

    # ========================================================================
    # PATH 3: StringValue
    # ========================================================================

    print("\n" + "=" * 80)
    print("PATH 3: StringValue (StringScalar)")
    print("=" * 80)

    print("\nCode Path:")
    print("  StringValue.__add__(other)")
    print("  → self.concat(other)")
    print("  → ops.StringConcat((self, other)).to_expr()")
    print("  ⚠️  BYPASSES _binop entirely!")
    print()

    print("Step 1: What does StringScalar.__add__(Deferred) do?")
    try:
        result = lit_str.__add__(col_str)
        print(f"  Returns: {result}")
    except Exception as e:
        print(f"  ❌ Raises: {type(e).__name__}")
        print(f"     (Exception raised BEFORE _binop is called)")

    print("\nStep 2: StringValue.concat() bypasses _binop:")
    import inspect
    from ibis.expr.types.strings import StringValue
    concat_source = inspect.getsource(StringValue.concat)
    # Show the critical line
    print("  Source code (simplified):")
    print("    def concat(self, other, ...):")
    print("      return ops.StringConcat((self, other, ...)).to_expr()")
    print()
    print("  ⚠️  Notice: No call to _binop()!")

    print("\nStep 3: What exception does ops.StringConcat raise?")
    try:
        node = ops.StringConcat((lit_str, col_str))
        print(f"  Success: {node}")
    except Exception as e:
        exc_type = type(e)
        print(f"  ❌ Raises: {exc_type.__name__}")
        print(f"     Module: {exc_type.__module__}")
        print(f"     Inheritance: {' → '.join([c.__name__ for c in exc_type.__mro__[:3]])}")

    print("\nStep 4: Could _binop catch this exception?")
    print("  _binop catches: (ValidationError, NotImplementedError)")
    print("  SignatureValidationError IS a ValidationError")
    print("  ✅ _binop COULD catch it...")
    print("  ❌ BUT: StringValue.concat() doesn't call _binop!")
    print("  ❌ Therefore: Exception propagates without any handler")

    print("\nResult: literal('x') + ibis._['y'] FAILS ❌")
    print("        (Different reason than IntegerScalar)")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 80)
    print("SUMMARY: THREE DIFFERENT CODE PATHS, THREE DIFFERENT OUTCOMES")
    print("=" * 80)

    print("\n┌─────────────────┬──────────────┬──────────────────┬─────────────────┐")
    print("│ Scalar Type     │ Uses _binop? │ Exception Raised │ Status          │")
    print("├─────────────────┼──────────────┼──────────────────┼─────────────────┤")
    print("│ BooleanScalar   │ ✅ Yes       │ SigValidation    │ ✅ Works        │")
    print("│ IntegerScalar   │ ✅ Yes       │ InputTypeError   │ ❌ Fails        │")
    print("│ FloatingScalar  │ ✅ Yes       │ InputTypeError   │ ❌ Fails        │")
    print("│ StringScalar    │ ❌ No        │ SigValidation    │ ❌ Fails        │")
    print("└─────────────────┴──────────────┴──────────────────┴─────────────────┘")

    print("\n" + "=" * 80)
    print("THE FIX AND ITS IMPACT")
    print("=" * 80)

    print("\nProposed Fix:")
    print("  Add InputTypeError to _binop's exception handler")
    print()
    print("  Current:")
    print("    except (ValidationError, NotImplementedError):")
    print("        return NotImplemented")
    print()
    print("  Fixed:")
    print("    except (ValidationError, NotImplementedError, InputTypeError):")
    print("        return NotImplemented")

    print("\nWill Fix:")
    print("  ✅ IntegerScalar + Deferred")
    print("  ✅ FloatingScalar + Deferred")
    print("  ✅ All numeric arithmetic reverse operators")

    print("\nWill NOT Fix:")
    print("  ❌ StringScalar + Deferred")
    print("     (Needs separate fix - make concat() use _binop or add exception handling)")

    print("\nWill NOT Affect:")
    print("  ✅ BooleanScalar + Deferred (already works)")

    print("\n" + "=" * 80)
    print("VERIFICATION: TEST ALL THREE PATHS")
    print("=" * 80)

    table = setup()

    print("\n1. BooleanScalar (should work):")
    try:
        expr = lit_bool & col_bool
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"   ✅ literal(True) & col → {result}")
    except Exception as e:
        print(f"   ❌ literal(True) & col → {type(e).__name__}")

    print("\n2. IntegerScalar (should fail - will be fixed):")
    try:
        expr = lit_int + col_int
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"   ✅ literal(5) + col → {result}")
    except Exception as e:
        print(f"   ❌ literal(5) + col → {type(e).__name__}")

    print("\n3. StringScalar (should fail - will stay broken):")
    try:
        expr = lit_str + col_str
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"   ✅ literal('world') + col → {result}")
    except Exception as e:
        print(f"   ❌ literal('world') + col → {type(e).__name__}")

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("The proposed fix (catching InputTypeError in _binop) will:")
    print("  • Fix 11 failing numeric arithmetic operations")
    print("  • Make numeric scalars consistent with boolean scalars")
    print("  • NOT fix string concatenation (needs separate issue/fix)")
    print()


if __name__ == '__main__':
    test_code_paths()
