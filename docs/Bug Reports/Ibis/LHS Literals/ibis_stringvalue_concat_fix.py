#!/usr/bin/env python3
"""
Demonstration of the fix for StringValue.concat() to support reverse operators.

This shows the proposed change to ibis/expr/types/strings.py::StringValue.concat()
"""

import ibis
import polars as pl


def demonstrate_current_behavior():
    """Show current broken behavior."""
    print("=" * 80)
    print("CURRENT BEHAVIOR (BROKEN)")
    print("=" * 80)

    conn = ibis.polars.connect()
    df = pl.DataFrame({'x_str': ['hello']})
    table = conn.create_table('test', df, overwrite=True)

    col_str = ibis._['x_str']
    lit_str = ibis.literal(' world')

    print("\n1. Forward operator (col + lit): Works ✅")
    try:
        expr = col_str + lit_str
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"   Result: '{result}'")
    except Exception as e:
        print(f"   ❌ Failed: {type(e).__name__}")

    print("\n2. Reverse with raw Python (' world' + col): Works ✅")
    try:
        expr = ' world' + col_str
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"   Result: '{result}'")
    except Exception as e:
        print(f"   ❌ Failed: {type(e).__name__}")

    print("\n3. Reverse with literal (lit + col): FAILS ❌")
    try:
        expr = lit_str + col_str
        result = table.select(expr.name('r'))['r'].execute().tolist()[0]
        print(f"   ✅ Result: '{result}'")
    except Exception as e:
        print(f"   ❌ Failed: {type(e).__name__}")
        print(f"      Error: {str(e)[:100]}...")


def demonstrate_proposed_fix():
    """Demonstrate what the fix would look like."""
    print("\n\n" + "=" * 80)
    print("PROPOSED FIX")
    print("=" * 80)

    print("\nFile: ibis/expr/types/strings.py")
    print("Method: StringValue.concat()")
    print("Line: ~1580")
    print()

    print("CURRENT CODE:")
    print("-" * 80)
    print("""
    def concat(
        self, other: str | StringValue, /, *args: str | StringValue
    ) -> StringValue:
        '''Concatenate strings.'''
        return ops.StringConcat((self, other, *args)).to_expr()
    """)

    print("\nPROPOSED FIX (APPROACH 1 - Exception Handling):")
    print("-" * 80)
    print("""
    def concat(
        self, other: str | StringValue, /, *args: str | StringValue
    ) -> StringValue:
        '''Concatenate strings.'''
        try:
            return ops.StringConcat((self, other, *args)).to_expr()
        except ValidationError:
            return NotImplemented
    """)

    print("\nALTERNATIVE FIX (APPROACH 2 - Deferred Check):")
    print("-" * 80)
    print("""
    def concat(
        self, other: str | StringValue, /, *args: str | StringValue
    ) -> StringValue:
        '''Concatenate strings.'''
        from ibis.common.deferred import Deferred

        # Check if any argument is a Deferred (unbound reference)
        if isinstance(other, Deferred) or any(isinstance(a, Deferred) for a in args):
            return NotImplemented

        return ops.StringConcat((self, other, *args)).to_expr()
    """)

    print("\nREQUIRED IMPORT (for Approach 1):")
    print("-" * 80)
    print("Add to imports at top of file:")
    print("    from ibis.common.annotations import ValidationError")


def explain_fix():
    """Explain why the fix works."""
    print("\n\n" + "=" * 80)
    print("WHY THE FIX WORKS")
    print("=" * 80)

    print("""
When Python evaluates: literal('world') + ibis._['x']

Step 1: Python tries literal('world').__add__(ibis._['x'])
        → calls StringValue.__add__(Deferred)
        → calls concat(Deferred)

BEFORE FIX:
        → ops.StringConcat((self, Deferred)).to_expr()
        → ValidationError raised
        → Exception propagates to user ❌

AFTER FIX:
        → ops.StringConcat((self, Deferred)).to_expr()
        → ValidationError raised
        → concat() catches it and returns NotImplemented ✅

Step 2: Because __add__ returned NotImplemented, Python tries reverse operator
        → Python calls ibis._['x'].__radd__(literal('world'))
        → Deferred.__radd__() creates the expression ✅
        → Success!
    """)

    print("\n" + "=" * 80)
    print("CONSISTENCY WITH _binop")
    print("=" * 80)

    print("""
This fix makes StringValue.concat() behave consistently with _binop():

_binop (in ibis/expr/types/core.py):
    def _binop(op_class, left, right):
        try:
            node = op_class(left, right)
        except (ValidationError, NotImplementedError):
            return NotImplemented  # ← Returns NotImplemented
        else:
            return node.to_expr()

StringValue.concat() (proposed fix):
    def concat(self, other, /, *args):
        try:
            return ops.StringConcat((self, other, *args)).to_expr()
        except ValidationError:
            return NotImplemented  # ← Same pattern!
    """)


def compare_approaches():
    """Compare the two fix approaches."""
    print("\n\n" + "=" * 80)
    print("COMPARING FIX APPROACHES")
    print("=" * 80)

    print("\n┌────────────────────┬─────────────────┬─────────────────────────┐")
    print("│ Aspect             │ Approach 1      │ Approach 2              │")
    print("├────────────────────┼─────────────────┼─────────────────────────┤")
    print("│ Method             │ Try/except      │ Check for Deferred      │")
    print("│ Lines of code      │ +3 lines        │ +4 lines                │")
    print("│ Consistency        │ ✅ Matches _binop│ ❌ Different pattern    │")
    print("│ Performance        │ Exception cost  │ ✅ No exception         │")
    print("│ Handles all cases  │ ✅ Yes          │ ⚠️  Only Deferred       │")
    print("│ Import needed      │ ValidationError │ Deferred                │")
    print("│ Maintainability    │ ✅ Standard      │ ✅ Explicit             │")
    print("└────────────────────┴─────────────────┴─────────────────────────┘")

    print("\n\nRECOMMENDATION: Approach 1 (Exception Handling)")
    print("Reason: Consistent with existing _binop pattern")


def main():
    """Run all demonstrations."""
    demonstrate_current_behavior()
    demonstrate_proposed_fix()
    explain_fix()
    compare_approaches()

    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
To fix StringScalar reverse operators:

1. File to modify: ibis/expr/types/strings.py
2. Method to modify: StringValue.concat() (line ~1580)
3. Change: Wrap ops.StringConcat call in try/except
4. Import needed: from ibis.common.annotations import ValidationError

This is a SEPARATE fix from the main InputTypeError fix for numeric types.
Both fixes follow the same pattern: return NotImplemented when encountering
unbound references so Python can try the reverse operator.
    """)


if __name__ == '__main__':
    main()
