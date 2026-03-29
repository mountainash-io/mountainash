import sqlite3
import pandas as pd

# Create test data
df = pd.DataFrame({
    'a': [10, 20, 30],
    'b': [2, 3, 4],
    'c': [5, 10, 15]
})

conn = sqlite3.connect(':memory:')
df.to_sql('test', conn, index=False, if_exists='replace')

cursor = conn.cursor()

# Test 1: Just division
print("Test 1: Just division (a / b)")
print("=" * 60)
cursor.execute("SELECT a, b, CAST(a AS REAL) / b AS result FROM test")
for row in cursor.fetchall():
    print(f"  {row[0]} / {row[1]} = {row[2]}")

# Test 2: Full expression
print("\nTest 2: Full expression ((a + b) * c - CAST(a AS REAL) / b)")
print("=" * 60)
cursor.execute("""
    SELECT
        a, b, c,
        ((a + b) * c) - (CAST(a AS REAL) / b) AS result
    FROM test
""")
for row in cursor.fetchall():
    a, b, c, result = row
    expected = ((a + b) * c) - (float(a) / b)
    print(f"  (({a}+{b})*{c}) - ({a}/{b}) = {result} (Python says: {expected})")

# Test 3: Check type of result
print("\nTest 3: Type of intermediate results")
print("=" * 60)
cursor.execute("""
    SELECT
        typeof((a + b) * c) as mult_type,
        typeof(CAST(a AS REAL) / b) as div_type,
        typeof(((a + b) * c) - (CAST(a AS REAL) / b)) as final_type
    FROM test LIMIT 1
""")
row = cursor.fetchone()
print(f"  Type of (a+b)*c: {row[0]}")
print(f"  Type of CAST(a AS REAL)/b: {row[1]}")
print(f"  Type of full expression: {row[2]}")

# Test 4: Step by step
print("\nTest 4: Step by step for row 2 (20, 3, 10)")
print("=" * 60)
cursor.execute("""
    SELECT
        a, b, c,
        a + b as sum_ab,
        (a + b) * c as product,
        CAST(a AS REAL) / b as division,
        ((a + b) * c) - (CAST(a AS REAL) / b) as final
    FROM test WHERE a = 20
""")
row = cursor.fetchone()
print(f"  a = {row[0]}, b = {row[1]}, c = {row[2]}")
print(f"  a + b = {row[3]}")
print(f"  (a + b) * c = {row[4]}")
print(f"  CAST(a AS REAL) / b = {row[5]}")
print(f"  Final = {row[6]}")
print(f"  Python calc: 230 - 6.666... = {230 - (20/3)}")

conn.close()
