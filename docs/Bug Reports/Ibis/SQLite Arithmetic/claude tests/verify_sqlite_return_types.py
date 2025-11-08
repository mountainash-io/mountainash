"""
Verify what types SQLite actually returns.
"""
import sqlite3

conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create table
cursor.execute("CREATE TABLE test (a INTEGER, b INTEGER, c INTEGER)")
cursor.execute("INSERT INTO test VALUES (10, 2, 5), (20, 3, 10), (30, 4, 15)")
conn.commit()

# Test the exact SQL that Ibis generates
sql = """
SELECT
  ((a + b) * c) - (CAST(a AS REAL) / b) AS result
FROM test
"""

print("=" * 80)
print("SQLITE RETURN TYPES")
print("=" * 80)
print(f"SQL:\n{sql}")

cursor.execute(sql)
rows = cursor.fetchall()

print(f"\nRows: {rows}")
for i, row in enumerate(rows):
    print(f"  Row {i}: {row}")
    print(f"    Value: {row[0]}")
    print(f"    Type: {type(row[0])}")
    print(f"    Python repr: {repr(row[0])}")

# Test simpler expressions
print("\n" + "=" * 80)
print("SIMPLER TEST CASES")
print("=" * 80)

tests = [
    ("SELECT 55.0", "Literal 55.0"),
    ("SELECT 55", "Literal 55"),
    ("SELECT 60 - 5.0", "60 - 5.0"),
    ("SELECT 60 - 5", "60 - 5"),
    ("SELECT CAST(10 AS REAL) / 2", "CAST(10 AS REAL) / 2"),
    ("SELECT (10 + 2) * 5", "(10 + 2) * 5"),
    ("SELECT ((10 + 2) * 5) - (CAST(10 AS REAL) / 2)", "Full expression"),
]

for sql, desc in tests:
    cursor.execute(sql)
    result = cursor.fetchone()[0]
    print(f"{desc:40s}: {result:20} (type: {type(result).__name__})")

conn.close()
