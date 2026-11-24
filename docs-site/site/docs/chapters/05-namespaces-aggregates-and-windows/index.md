---
title: Namespaces, aggregates and windows
---

# Namespaces, aggregates and windows

Type-specific operations on expressions live in namespaces: `.str` for text, `.dt` for dates and times, `.list` for list columns and a few more. Alongside them sit the row-wise horizontal functions, membership tests with `is_in`, aggregate expressions for `group_by(...).agg(...)` and window expressions built with `.over(...)`. All of them build the same backend-agnostic expression tree as the operators, so one plan runs on Polars, Narwhals-reached libraries and Ibis.

Assumes: [Building expressions](../04-building-expressions/index.md), in particular [output names](../04-building-expressions/index.md#output-names) and [combining columns](../04-building-expressions/index.md#combining-columns).

## Namespaces

<!-- concept:335 -->
A namespace is an attribute on an expression that groups the operations for one kind of data. Reading `ma.col("name").str` returns a builder bound to that expression; each method on it returns a new expression, so calls chain across namespaces exactly as they chain across ordinary methods. The expression runs when you compile it against a dataframe (see [Compiling an expression](../04-building-expressions/index.md#compiling-an-expression)).

| Namespace | Operates on | Typical methods |
|---|---|---|
| `.str` | Text | `to_uppercase`, `strip_chars`, `contains`, `replace`, `slice`, `regex_contains` |
| `.dt` | Dates, datetimes, durations | `year`, `month`, `add_days`, `diff_days`, `truncate`, `strftime` |
| `.name` | The output column name | `alias`, `prefix`, `suffix`, `to_uppercase`, `to_lowercase` |
| `.struct` | Struct columns | `field`, `cast` |
| `.list` | List columns | `len`, `sum`, `get`, `contains`, `filter`, `agg` |
| `.cat` | Categorical field values | `cast` |
| `.geo` | Geopoint and GeoJSON field values | `parse_geopoint`, `parse_geojson`, `serialize_geojson` |

Operations that apply to any value (arithmetic, comparison, null handling, aggregates, window functions) are methods directly on the expression.

```python
import polars as pl
import mountainash as ma

clean_name = ma.col("name").str.strip_chars().str.to_uppercase().name.suffix("_clean")
print(type(ma.col("name").str).__name__)
print(type(clean_name).__name__)
```

```text
StringAPIBuilder
BooleanExpressionAPI
```

Method names follow Polars where Polars has a name for the operation, and the Substrait-standard name is usually available as well: `str.to_uppercase()` and `str.upper()` build the same node, as do `str.strip_chars()` and `str.trim()`. The full method list for every namespace is in the API reference.

## Strings and dates

<!-- concept:336 -->
The `.str` namespace covers case conversion, trimming and padding, slicing, searching, replacement, splitting and parsing text into other types (`to_integer`, `to_date`, `to_datetime`). `str.contains` and `str.replace` match a literal substring and take a `case_sensitive` flag; regular expressions go through `regex_contains`, `regex_replace` and the `regexp_*` methods.

<!-- concept:337 -->
The `.dt` namespace extracts components (`year`, `month`, `day_of_week`, `hour`), does calendar arithmetic (`add_days`, `add_months`, `diff_days`), rounds and truncates to units, converts and assigns time zones, and formats with `strftime`. The entry points `ma.today()` and `ma.now()` are covered in [Columns, literals and conditions](../04-building-expressions/index.md#columns-literals-and-conditions).

```python
from datetime import date

people = pl.DataFrame({
    "name": ["  ada lovelace", "Grace Hopper ", None],
    "email": ["ada@example.org", "grace@navy.mil", "anon@example.org"],
    "joined": [date(2021, 3, 14), date(2023, 11, 2), date(2024, 1, 31)],
})

tidy = ma.relation(people).select(
    clean_name,
    ma.col("email").str.contains("example").alias("is_example"),
    ma.col("email").str.replace("@", " at ").alias("spoken"),
    ma.col("joined").dt.year().alias("year"),
    ma.col("joined").dt.add_months(1).alias("renewal"),
    ma.col("joined").dt.strftime("%d %b %Y").alias("label"),
)
print(tidy.to_polars())
```

```text
shape: (3, 6)
┌──────────────┬────────────┬─────────────────────┬──────┬────────────┬─────────────┐
│ name_clean   ┆ is_example ┆ spoken              ┆ year ┆ renewal    ┆ label       │
│ ---          ┆ ---        ┆ ---                 ┆ ---  ┆ ---        ┆ ---         │
│ str          ┆ bool       ┆ str                 ┆ i32  ┆ date       ┆ str         │
╞══════════════╪════════════╪═════════════════════╪══════╪════════════╪═════════════╡
│ ADA LOVELACE ┆ true       ┆ ada at example.org  ┆ 2021 ┆ 2021-04-14 ┆ 14 Mar 2021 │
│ GRACE HOPPER ┆ false      ┆ grace at navy.mil   ┆ 2023 ┆ 2023-12-02 ┆ 02 Nov 2023 │
│ null         ┆ true       ┆ anon at example.org ┆ 2024 ┆ 2024-02-29 ┆ 31 Jan 2024 │
└──────────────┴────────────┴─────────────────────┴──────┴────────────┴─────────────┘
```

`add_months(1)` on 31 January clamps to the last day of February. The same expressions run unchanged on a pandas frame, which mountainash reaches through Narwhals:

```python
print(ma.relation(people.to_pandas()).select(
    ma.col("joined").dt.year().alias("year"),
    ma.col("email").str.contains("example").alias("is_example"),
).to_polars())
```

```text
shape: (3, 2)
┌──────┬────────────┐
│ year ┆ is_example │
│ ---  ┆ ---        │
│ i32  ┆ bool       │
╞══════╪════════════╡
│ 2021 ┆ true       │
│ 2023 ┆ false      │
│ 2024 ┆ true       │
└──────┴────────────┘
```

!!! warning "Backend limit"
    Some text and date operations lack a correct native implementation on some backends. There mountainash raises a `BackendCapabilityError`, so wherever an operation runs it returns the same result:

    - Every Ibis dialect refuses `str.title()`, `str.initcap()` and `str.swapcase()`; every Narwhals backend refuses `str.capitalize()` and `str.swapcase()`.
    - `str.to_time()`, `dt.parse_default()` and `dt.parse_temporal_any()` run on Polars only.
    - mountainash refuses case-insensitive and flag-bearing regex options, and some `dt.truncate`/`dt.round` units (sub-day units on SQLite, week units through Narwhals), on engines that cannot honour them.

    The capability declarations under `src/mountainash/expressions/backends/capabilities/` (for example `ibis/family/substrait/string.py`, `narwhals/family/substrait/string.py` and the `extensions_mountainash/datetime.py` files) define these limits. See [Backend support and known limits](../16-backend-support-and-limits/index.md).

```python
import ibis

con = ibis.duckdb.connect()
people_db = con.create_table("people", people)
try:
    ma.relation(people_db).select(ma.col("email").str.title()).to_polars()
except ma.MountainashError as exc:
    print(type(exc).__name__, exc)
```

```text
BackendCapabilityError [ibis] The Mountainash Ibis backend does not implement title.
```

## Names, structs and lists

<!-- concept:338 -->
The `.name` namespace renames the output column and leaves its values as they are. `name.alias(...)` is the same operation as the flat `.alias(...)` described in [Output names](../04-building-expressions/index.md#output-names); `name.prefix(...)` and `name.suffix(...)` derive the new name from the existing one, and `name.to_uppercase()` / `name.to_lowercase()` change its case (`name_to_upper` and `name_to_lower` are the canonical spellings).

<!-- concept:339 -->
The `.struct` namespace reads named fields from struct columns. `struct.field("country")` returns the field's values, and the output column takes the field name. `struct.cast(...)` converts a whole struct to a target struct dtype and its main user is [conforming data](../11-conforming-data/index.md).

<!-- concept:340 -->
The `.list` namespace works on list columns row by row: size (`len`), element access (`get`, `first`, `last`, `slice`), per-list statistics (`sum`, `mean`, `max`, `n_unique`), set operations between lists, sorting, joining into a string and membership (`contains`, plus the ternary `t_contains`, see [Ternary logic](../06-ternary-logic/index.md)). `list.filter(...)` and `list.agg(...)` take an expression evaluated once per element; inside it, `ma.element()` refers to the current element.

```python
orders = pl.DataFrame({
    "order_id": [1, 2, 3],
    "customer": [
        {"name": "Ada", "country": "GB"},
        {"name": "Grace", "country": "US"},
        {"name": "Alan", "country": "GB"},
    ],
    "quantities": [[2, 5, 1], [10], []],
})

print(ma.relation(orders).select(
    ma.col("order_id").name.prefix("src_"),
    ma.col("customer").struct.field("country"),
    ma.col("quantities").list.len().name.suffix("_n"),
    ma.col("quantities").list.sum().alias("total"),
    ma.col("quantities").list.contains(5).alias("has_five"),
    ma.col("quantities").list.filter(ma.element() > 1).alias("big"),
    ma.col("quantities").list.agg(ma.element().max()).alias("largest"),
).to_polars())
```

```text
shape: (3, 7)
┌──────────────┬─────────┬──────────────┬───────┬──────────┬───────────┬─────────┐
│ src_order_id ┆ country ┆ quantities_n ┆ total ┆ has_five ┆ big       ┆ largest │
│ ---          ┆ ---     ┆ ---          ┆ ---   ┆ ---      ┆ ---       ┆ ---     │
│ i64          ┆ str     ┆ u32          ┆ i64   ┆ bool     ┆ list[i64] ┆ i64     │
╞══════════════╪═════════╪══════════════╪═══════╪══════════╪═══════════╪═════════╡
│ 1            ┆ GB      ┆ 3            ┆ 8     ┆ true     ┆ [2, 5]    ┆ 5       │
│ 2            ┆ US      ┆ 1            ┆ 10    ┆ false    ┆ [10]      ┆ 10      │
│ 3            ┆ GB      ┆ 0            ┆ 0     ┆ false    ┆ []        ┆ null    │
└──────────────┴─────────┴──────────────┴───────┴──────────┴───────────┴─────────┘
```

!!! warning "Backend limit"
    mountainash refuses `list.contains()` and `list.t_contains()` on pandas through Narwhals: the pandas list accessor works only on Arrow-backed lists, and Narwhals lacks a `contains` implementation there (`narwhals/dialects/narwhals_pandas/extensions_mountainash/list.py`). It also refuses `list.get()` with some index forms on Narwhals over Polars, and `list.cast_items()` with `failure_behavior=NULL` on the Ibis and Narwhals dialects listed in the capability declarations.

## Categoricals and geometry

<!-- concept:341 -->
The `.cat` namespace has one method, `cat.cast(...)`, which converts values to the base scalar type of a categorical field: `value_type="string"` or `"integer"`. It also records the declared `categories` and whether they are `ordered`, and a `field_name` used in error messages. The cast keeps values outside `categories`: in the example below, 9 passes through. [Validation](../13-validation/index.md) checks that values belong to the category list. With the default `failure_behavior=ma.CaseFailureBehaviour.THROW` a value that fails to convert raises; with `NULL` it becomes null.

<!-- concept:342 -->
The `.geo` namespace parses and checks the geographic field formats from Frictionless Table Schema. `geo.parse_geopoint(...)` accepts the `default` (`"lon, lat"` text), `array` and `object` formats, with `source_representation` saying whether the input is text (`lexical`) or already a native list or struct (`native`). `geo.parse_geojson(...)` and `geo.serialize_geojson(...)` read and write GeoJSON (`format="default"`) or TopoJSON. Their main use is [conforming data](../11-conforming-data/index.md) to a schema with geographic fields.

```python
survey = pl.DataFrame({
    "rating": ["1", "2", "9", "x"],
    "location": ["151.2, -33.9", "bad", None, "0, 0"],
})

print(ma.relation(survey).select(
    ma.col("rating").cat.cast(
        value_type="integer",
        categories=(1, 2, 3),
        ordered=True,
        field_name="rating",
        failure_behavior=ma.CaseFailureBehaviour.NULL,
    ),
    ma.col("location").geo.parse_geopoint(
        format="default",
        source_representation="lexical",
        field_name="location",
        failure_behavior=ma.CaseFailureBehaviour.NULL,
    ),
).to_polars())
```

```text
shape: (4, 2)
┌────────┬──────────────┐
│ rating ┆ location     │
│ ---    ┆ ---          │
│ i64    ┆ str          │
╞════════╪══════════════╡
│ 1      ┆ 151.2, -33.9 │
│ 2      ┆ null         │
│ 9      ┆ null         │
│ null   ┆ 0, 0         │
└────────┴──────────────┘
```

!!! warning "Backend limit"
    `geo.parse_geojson()` and `geo.serialize_geojson()` run on Polars only; Narwhals and Ibis refuse them. `geo.parse_geopoint()` runs on every backend in `default` lexical form with `failure_behavior=NULL`; Narwhals and Ibis refuse several other format, representation and failure-behaviour combinations, and SQLite also refuses `default` with `THROW`. Ibis over SQLite refuses `cat.cast()` with integer values, and Narwhals refuses it with integer values plus `failure_behavior=NULL` on pandas, Polars and lazy frames. The declarations are in `narwhals/family/extensions_mountainash/geospatial.py`, `ibis/family/extensions_mountainash/geospatial.py`, `ibis/dialects/ibis_sqlite/extensions_mountainash/geospatial.py` and the categorical declarations under the same tree.

## Membership

<!-- concept:333 -->
`is_in` tests whether each value appears in a fixed set of members, and `is_not_in` is its complement. Members can be passed as one list, tuple or set, or as separate arguments; members may also be expressions such as other columns, in which case the test compares against each one per row. Members keep the types they are given; membership applies no coercion.

Nulls follow the ternary rules in [Ternary logic](../06-ternary-logic/index.md), then reduce to a plain boolean. A null value has unknown membership, which reduces to `false`: both `is_in` and `is_not_in` return `false` for it. A null member makes every non-match uncertain, so `is_not_in` returns `false` for every unmatched value. The ternary forms `t_is_in` and `t_is_not_in` expose that uncertainty as UNKNOWN.

```python
countries = pl.DataFrame({"country": ["GB", "US", None, "FR"]})

print(ma.relation(countries).with_columns(
    ma.col("country").is_in(["GB", "FR"]).alias("in_list"),
    ma.col("country").is_in("GB", "FR").alias("variadic"),
    ma.col("country").is_not_in(["GB", "FR"]).alias("not_in"),
    ma.col("country").is_not_in(["GB", None]).alias("not_in_null_member"),
).to_polars())
```

```text
shape: (4, 5)
┌─────────┬─────────┬──────────┬────────┬────────────────────┐
│ country ┆ in_list ┆ variadic ┆ not_in ┆ not_in_null_member │
│ ---     ┆ ---     ┆ ---      ┆ ---    ┆ ---                │
│ str     ┆ bool    ┆ bool     ┆ bool   ┆ bool               │
╞═════════╪═════════╪══════════╪════════╪════════════════════╡
│ GB      ┆ true    ┆ true     ┆ false  ┆ false              │
│ US      ┆ false   ┆ false    ┆ true   ┆ false              │
│ null    ┆ false   ┆ false    ┆ false  ┆ false              │
│ FR      ┆ true    ┆ true     ┆ false  ┆ false              │
└─────────┴─────────┴──────────┴────────┴────────────────────┘
```

The same table is asserted on every backend by the membership acceptance tests (`tests/expressions/membership/test_acceptance.py`). Building the expression raises a subclass of `ma.MountainashError` for ambiguous arguments: a nested collection, a backend-native expression as a member, an unsupported collection type such as a NumPy array or a mapping, or a single bare expression as the whole collection. To test against a list column, use `list.contains`:

```python
try:
    ma.col("country").is_in(ma.col("allowed"))
except ma.MountainashError as exc:
    print(type(exc).__name__, exc)
```

```text
BareExpressionCollectionError A bare expression was passed as the membership-test collection. Use .list.contains() or .list.t_contains() to check membership against a list column.
```

## Horizontal functions

<!-- concept:328 -->
Horizontal functions combine several expressions within each row. They are free functions on `ma`, follow Polars naming, and take two or more arguments.

| Function | Result per row | Nulls |
|---|---|---|
| `ma.max_horizontal(...)` | Largest value; alias of `ma.greatest` | Ignored |
| `ma.min_horizontal(...)` | Smallest value; alias of `ma.least` | Ignored |
| `ma.all_horizontal(...)` | Boolean AND of all inputs | Kleene logic: `true` and null is null |
| `ma.any_horizontal(...)` | Boolean OR of all inputs | Kleene logic: `true` or null is `true` |
| `ma.sum_horizontal(...)` | Sum of the inputs | A null input gives null |

`greatest`, `least` and `coalesce` are described in [Combining columns](../04-building-expressions/index.md#combining-columns).

```python
readings = pl.DataFrame({"a": [1, None, 3], "b": [10, 20, None], "c": [5, 5, 5]})

print(ma.relation(readings).select(
    ma.max_horizontal(ma.col("a"), ma.col("b"), ma.col("c")).alias("max"),
    ma.min_horizontal(ma.col("a"), ma.col("b"), ma.col("c")).alias("min"),
    ma.all_horizontal(ma.col("a") > 0, ma.col("b") > 0).alias("all_positive"),
    ma.any_horizontal(ma.col("a") > 2, ma.col("b") > 15).alias("any_high"),
).to_polars())
```

```text
shape: (3, 4)
┌─────┬─────┬──────────────┬──────────┐
│ max ┆ min ┆ all_positive ┆ any_high │
│ --- ┆ --- ┆ ---          ┆ ---      │
│ i64 ┆ i64 ┆ bool         ┆ bool     │
╞═════╪═════╪══════════════╪══════════╡
│ 10  ┆ 1   ┆ true         ┆ false    │
│ 20  ┆ 5   ┆ null         ┆ true     │
│ 5   ┆ 3   ┆ null         ┆ true     │
└─────┴─────┴──────────────┴──────────┘
```

`ma.sum_horizontal(a, b, c)` builds the same expression as `a + b + c`, so a null input makes that row's sum null, where Polars' own `sum_horizontal` skips nulls. Its result keeps the first input's column name. In this release it has no `.alias()`; write `(ma.col("a") + ma.col("b") + ma.col("c")).alias("total")` when the sum needs a new name.

## Aggregates

<!-- concept:329 -->
An aggregate expression reduces many rows to one value: `sum`, `mean` (alias of `avg`), `min`, `max`, `count` (non-null values), `n_unique`, `std_dev`, `variance`, `product`, `mode`, `any_value`, and the boolean `all` and `any`. Free functions cover aggregates independent of any single column: `ma.count_records()` (also `ma.len()`) counts all rows including nulls, and `ma.corr`, `ma.median` and `ma.quantile` take their arguments explicitly.

Aggregates are evaluated per group inside `group_by(...).agg(...)` on a [relation](../07-relations/index.md#grouping-and-reshaping). Each aggregate needs an output name, usually set with `.alias()`.

```python
sales = pl.DataFrame({
    "region": ["north", "north", "south", "south", "south"],
    "product": ["tea", "coffee", "tea", "tea", "coffee"],
    "units": [10, 4, 7, None, 12],
})

def summarise(source):
    return (
        ma.relation(source)
        .group_by("region")
        .agg(
            ma.col("units").sum().alias("units"),
            ma.col("units").mean().alias("avg_units"),
            ma.col("units").count().alias("units_reported"),
            ma.count_records().alias("rows"),
            ma.col("product").n_unique().alias("products"),
        )
        .sort("region")
    )

print(summarise(sales).to_polars())
```

```text
shape: (2, 6)
┌────────┬───────┬───────────┬────────────────┬──────┬──────────┐
│ region ┆ units ┆ avg_units ┆ units_reported ┆ rows ┆ products │
│ ---    ┆ ---   ┆ ---       ┆ ---            ┆ ---  ┆ ---      │
│ str    ┆ i64   ┆ f64       ┆ u32            ┆ u32  ┆ u32      │
╞════════╪═══════╪═══════════╪════════════════╪══════╪══════════╡
│ north  ┆ 14    ┆ 7.0       ┆ 2              ┆ 2    ┆ 2        │
│ south  ┆ 19    ┆ 9.5       ┆ 2              ┆ 3    ┆ 2        │
└────────┴───────┴───────────┴────────────────┴──────┴──────────┘
```

`sum` and `mean` skip the null in the south group, `count` counts only reported values, and `count_records` counts every row. The same plan against a DuckDB table through Ibis returns the same values:

```python
sales_db = con.create_table("sales", sales)
print(summarise(sales_db).to_polars().equals(summarise(sales).to_polars()))
```

```text
True
```

For a whole-relation result, scalar terminals such as `relation.sum("units")` compute one aggregate over the whole relation and return a Python value; they are built from these aggregate expressions (see [Scalar terminals](../08-collecting-results/index.md#scalar-terminals)).

!!! warning "Backend limit"
    `product()` runs on Polars. mountainash refuses it on every Ibis dialect and every Narwhals backend, because neither offers a product aggregate (`ibis/family/substrait/aggregate.py`, `narwhals/family/substrait/aggregate.py`).

## Windows with over

<!-- concept:330 -->
`.over(*partition_by, order_by=...)` evaluates an expression within groups of rows while keeping every row, like a SQL window. Applied to an aggregate, it broadcasts the group result to each row. Applied to an order-dependent function (`cum_sum`, `lag`, `lead`, `shift`, `diff`, `first_value`, `forward_fill` and others), `order_by` fixes the row order inside each partition; prefix a column name with `-` to order it descending. Ranking functions (`rank`, `dense_rank`, `row_number`, `percent_rank`, `ntile`) carry their own ordering: `rank(method="dense", descending=True)` ranks by the column itself.

```python
monthly = pl.DataFrame({
    "region": ["north", "north", "south", "south", "south"],
    "month": [1, 2, 1, 2, 3],
    "units": [10, 4, 7, 3, 12],
})

def with_windows(source):
    return ma.relation(source).with_columns(
        ma.col("units").sum().over("region").alias("region_units"),
        ma.col("units").cum_sum().over("region", order_by="month").alias("running"),
        ma.col("units").lag(1).over("region", order_by="month").alias("previous"),
        ma.col("units").rank(method="dense", descending=True).over("region").alias("rank"),
    ).sort("region", "month")

print(with_windows(monthly).to_polars())
```

```text
shape: (5, 7)
┌────────┬───────┬───────┬──────────────┬─────────┬──────────┬──────┐
│ region ┆ month ┆ units ┆ region_units ┆ running ┆ previous ┆ rank │
│ ---    ┆ ---   ┆ ---   ┆ ---          ┆ ---     ┆ ---      ┆ ---  │
│ str    ┆ i64   ┆ i64   ┆ i64          ┆ i64     ┆ i64      ┆ u32  │
╞════════╪═══════╪═══════╪══════════════╪═════════╪══════════╪══════╡
│ north  ┆ 1     ┆ 10    ┆ 14           ┆ 10      ┆ null     ┆ 1    │
│ north  ┆ 2     ┆ 4     ┆ 14           ┆ 14      ┆ 10       ┆ 2    │
│ south  ┆ 1     ┆ 7     ┆ 22           ┆ 7       ┆ null     ┆ 2    │
│ south  ┆ 2     ┆ 3     ┆ 22           ┆ 10      ┆ 7        ┆ 3    │
│ south  ┆ 3     ┆ 12    ┆ 22           ┆ 22      ┆ 3        ┆ 1    │
└────────┴───────┴───────┴──────────────┴─────────┴──────────┴──────┘
```

The DuckDB table from the previous section gives the same values:

```python
monthly_db = con.create_table("monthly", monthly)
print(with_windows(monthly_db).to_polars().equals(with_windows(monthly).to_polars()))
```

```text
True
```

!!! warning "Backend limit"
    Narwhals windows carry no sort direction, so mountainash refuses order-dependent window functions with a descending `order_by` on every Narwhals backend (`narwhals/family/substrait/window.py`, `narwhals/family/extensions_mountainash/window.py`). Pandas-like frames order by the last key only, so it also refuses windows ordered by several keys on pandas through Narwhals, and ranking by several sort keys on pandas, PyArrow and DuckDB through Narwhals.

```python
try:
    ma.relation(monthly.to_pandas()).with_columns(
        ma.col("units").lag(1).over("region", order_by="-month").alias("next"),
    ).to_polars()
except ma.MountainashError as exc:
    print(type(exc).__name__, exc)
```

```text
BackendCapabilityError [narwhals] Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported.
```
