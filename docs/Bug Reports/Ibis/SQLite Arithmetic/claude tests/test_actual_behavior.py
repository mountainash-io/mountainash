"""
Test to verify actual behavior of division and modulo in Ibis SQLite backend.
This tests whether the issues documented in BACKEND_INCONSISTENCIES.md still exist.
"""
import ibis
import pandas as pd

print("=" * 80)
print("TESTING DIVISION")
print("=" * 80)

# Test 1: Division with integer columns
df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

con = ibis.sqlite.connect()
t = con.create_table('test_div', df)

# Test: (a + b) * c - a / b
expr = (t.a + t.b) * t.c - t.a / t.b
result = t.select(expr.name('result')).execute()['result'].tolist()

# Expected (with float division):
# (10+2)*5 - 10/2 = 60 - 5.0 = 55.0
# (20+3)*10 - 20/3 = 230 - 6.666... = 223.333...
# (30+4)*15 - 30/4 = 510 - 7.5 = 502.5
expected = [55.0, 230.0 - (20.0/3.0), 502.5]

print(f"Result:   {result}")
print(f"Expected: {expected}")
print(f"Match: {all(abs(r - e) < 0.0001 for r, e in zip(result, expected))}")

# Show SQL
sql = ibis.to_sql(t.select((t.a / t.b).name('result')), dialect='sqlite')
print(f"\nGenerated SQL for a / b:")
print(sql)

print("\n" + "=" * 80)
print("TESTING MODULO")
print("=" * 80)

# Test 2: Modulo with negative numbers
df2 = pd.DataFrame({
    'a': [-10, 10, -10],
    'b': [3, -3, -3]
})

con2 = ibis.sqlite.connect()
t2 = con2.create_table('test_mod', df2)

expr2 = t2.a % t2.b
result2 = t2.select(expr2.name('result')).execute()['result'].tolist()

# Python modulo (expected): result has same sign as divisor
expected2 = [2, -2, -1]
print(f"Result:   {result2}")
print(f"Expected: {expected2}")
print(f"Match: {result2 == expected2}")

# Show SQL
sql2 = ibis.to_sql(t2.select((t2.a % t2.b).name('result')), dialect='sqlite')
print(f"\nGenerated SQL for a % b:")
print(sql2)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Division issue exists: {not all(abs(r - e) < 0.0001 for r, e in zip(result, expected))}")
print(f"Modulo issue exists:   {result2 != expected2}")
