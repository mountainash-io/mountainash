"""
Test the EXACT failing expression.
"""
import ibis
import pandas as pd

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

con = ibis.sqlite.connect()
t = con.create_table('test', df)

# The EXACT expression that was failing
expr = (t.a + t.b) * t.c - t.a / t.b

sql = ibis.to_sql(t.select(expr.name('result')), dialect='sqlite')
print("=" * 80)
print("GENERATED SQL")
print("=" * 80)
print(sql)

# Test cursor directly
print("\n" + "=" * 80)
print("CURSOR DIRECT")
print("=" * 80)
cursor = con.con.cursor()
cursor.execute(sql)
rows = cursor.fetchall()
print(f"Rows: {rows}")
print(f"Types: {[type(r[0]) for r in rows]}")

# Test via Ibis
print("\n" + "=" * 80)
print("IBIS .execute()")
print("=" * 80)
result = t.select(expr.name('result')).execute()
print(f"Values: {result['result'].tolist()}")
print(f"Dtype: {result['result'].dtype}")

# Compare
print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)
expected = [r[0] for r in rows]
actual = result['result'].tolist()
print(f"Expected (cursor): {expected}")
print(f"Actual (Ibis):     {actual}")
print(f"Match: {expected == actual}")

con.con.close()
