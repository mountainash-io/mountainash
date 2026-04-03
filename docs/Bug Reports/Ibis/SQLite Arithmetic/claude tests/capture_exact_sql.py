"""
Capture the exact SQL that Ibis executes.
"""
import ibis
import pandas as pd
import sqlite3

# Monkey-patch the execute method to capture SQL
original_execute = sqlite3.Cursor.execute

def traced_execute(self, sql, *args, **kwargs):
    if 'SELECT' in sql.upper() and 'result' in sql:
        print(f"\n[TRACE] Executing SQL:")
        print(sql)
        print()
    return original_execute(self, sql, *args, **kwargs)

sqlite3.Cursor.execute = traced_execute

# Run the test
print("=" * 80)
print("CAPTURING SQL EXECUTION")
print("=" * 80)

df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

con = ibis.sqlite.connect()
t = con.create_table('test', df)

expr = (t.a + t.b) * t.c - t.a / t.b
sql_expected = ibis.to_sql(t.select(expr.name('result')), dialect='sqlite')

print("\nExpected SQL (from ibis.to_sql()):")
print(sql_expected)

print("\n" + "=" * 80)
print("EXECUTING VIA IBIS")
print("=" * 80)
result = t.select(expr.name('result')).execute()

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)
print(f"Values: {result['result'].tolist()}")

# Now test the expected SQL directly
print("\n" + "=" * 80)
print("TESTING EXPECTED SQL DIRECTLY")
print("=" * 80)
cursor = con.con.cursor()
cursor.execute(sql_expected)
rows = cursor.fetchall()
print(f"Direct execution result: {rows}")
print(f"Types: {[type(r[0]) for r in rows]}")

# Restore
sqlite3.Cursor.execute = original_execute

con.con.close()
