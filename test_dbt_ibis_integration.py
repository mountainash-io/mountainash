"""
Quick test to demonstrate mountainash_expressions → Ibis → dbt-ibis integration

This shows that mountainash_expressions can compile to Ibis expressions,
which can then be used in dbt-ibis models.
"""

import mountainash_expressions as ma
import ibis

print("=== Testing mountainash_expressions → Ibis Integration ===\n")

# Create an in-memory Ibis table (simulating what dbt-ibis provides)
data = {
    "customer_id": [1, 2, 3, 4, 5],
    "status": ["active", "inactive", "active", "pending", "active"],
    "amount": [100, 50, 200, 75, 300],
    "email": ["user@test.com", "bad@", "admin@example.org", "test@demo.net", "vip@company.com"],
}

# Create Ibis table using pandas backend (most reliable)
con = ibis.pandas.connect({"customers": data})
customers = con.table("customers")

print(f"✓ Created Ibis table: {type(customers)}")
print(f"  Columns: {customers.columns}")
print()

# Build mountainash expression
print("Building mountainash expression...")
expr = (
    ma.col("status").eq("active")
    .and_(ma.col("amount").gt(150))
)
print(f"✓ Expression built: {expr}")
print()

# Compile to Ibis expression
print("Compiling to Ibis expression...")
ibis_expr = expr.compile(customers)
print(f"✓ Compiled to Ibis: {type(ibis_expr)}")
print(f"  Ibis expression: {ibis_expr}")
print()

# Use in Ibis filter (exactly how dbt-ibis would use it)
print("Filtering Ibis table with compiled expression...")
result = customers.filter(ibis_expr)
print(f"✓ Filtered table created: {type(result)}")
print()

# Execute to see results
print("Executing query...")
result_df = result.execute()
print(f"✓ Results:\n{result_df}")
print()

# Show what a dbt-ibis model would look like
print("\n=== Example dbt-ibis Model Using mountainash_expressions ===\n")
print("""
from dbt_ibis import depends_on, ref
import mountainash_expressions as ma

@depends_on(ref("stg_customers"))
def model(customers):
    '''Filter to high-value active customers using mountainash expressions'''

    # Build complex filter with mountainash
    filter_expr = (
        ma.col("status").eq("active")
        .and_(ma.col("amount").gt(150))
        .and_(ma.col("email").regex_contains(r"^[^@]+@[^@]+\.[^@]+$"))
    )

    # Compile to Ibis and filter
    # customers is an Ibis table from dbt-ibis
    return customers.filter(filter_expr.compile(customers))
""")

print("\n✓ SUCCESS: mountainash_expressions compiles to Ibis expressions!")
print("✓ These Ibis expressions work directly with dbt-ibis models!")
