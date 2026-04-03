# mountainash

[![PyPI](https://img.shields.io/pypi/v/mountainash.svg)](https://pypi.org/project/mountainash/)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Build DataFrame expressions and query plans once, execute on any backend. Mountainash provides a unified API for expressions, relations, schema management, and Python data ingress/egress across Polars, Pandas, Ibis, Narwhals, and PyArrow.

## Installation

```bash
pip install mountainash                    # Core (Polars + Narwhals)
pip install 'mountainash[pandas]'          # + Pandas backend
pip install 'mountainash[ibis]'            # + Ibis backend (SQL databases)
pip install 'mountainash[pyarrow]'         # + PyArrow backend
pip install 'mountainash[pydantic]'        # + Pydantic model support
pip install 'mountainash[all]'             # Everything
```

## Quick Start

### Expressions — build once, compile to any backend

```python
import mountainash as ma

# Build a backend-agnostic expression
expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))

# Compile to any backend — auto-detected from DataFrame type
polars_expr = expr.compile(polars_df)
pandas_expr = expr.compile(pandas_df)
ibis_expr = expr.compile(ibis_table)
```

### Relations — fluent query plans

```python
result = (
    ma.relation(df)
    .filter(ma.col("age").gt(30))
    .sort("name")
    .head(10)
    .to_polars()
)
```

### Python data — no DataFrame needed

```python
# Python data in, Python data out
result = (
    ma.relation([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ])
    .filter(ma.col("age").gt(25))
    .to_dicts()
)
# [{"name": "Alice", "age": 30}]
```

### Schema — deferred definition and application

```python
schema = ma.schema({
    "age": {"cast": "integer"},
    "name": {"rename": "full_name"},
    "score": {"null_fill": 0.0},
})
result = schema.apply(df)  # Backend auto-detected
```

## Features

- **Cross-backend expressions** — same expression compiles to Polars, Pandas, Ibis, Narwhals, or PyArrow
- **Relational query plans** — filter, sort, join, group_by, window functions — all backend-agnostic
- **Schema management** — define, extract, validate, and apply schemas across backends
- **Python data support** — ingest lists, dicts, dataclasses, Pydantic models; output to any format
- **Ternary logic** — three-valued TRUE/FALSE/UNKNOWN semantics for real-world data with missing values
- **Automatic backend detection** — no manual configuration; backend determined from DataFrame type
- **Substrait-aligned** — expression and relation ASTs follow the [Substrait](https://substrait.io/) specification

## Backend Support

| Backend | Install | Expressions | Relations | Schema |
|---------|---------|:-----------:|:---------:|:------:|
| Polars | *(included)* | Full | Full | Full |
| Narwhals | *(included)* | Full | Full | Full |
| Pandas | `[pandas]` | Full | Via Narwhals | Full |
| Ibis | `[ibis]` | Full | Full | Partial |
| PyArrow | `[pyarrow]` | Via Narwhals | Via Narwhals | Partial |

## Architecture

Mountainash separates **building** from **execution**. Expressions, relations, and schemas are defined as backend-agnostic AST nodes. Execution happens when a terminal method is called (`.compile()`, `.collect()`, `.apply()`), which auto-detects the backend and produces native operations.

```
Build phase (no backend needed)     Execute phase (backend auto-detected)
─────────────────────────────────   ──────────────────────────────────────
ma.col("x").gt(5)                   .compile(polars_df) → pl.col("x") > 5
ma.relation(df).filter(...)         .to_polars()        → pl.DataFrame
ma.schema({"x": {"cast": "int"}})  .apply(df)          → transformed df
```

For deeper architectural details, see the [design principles](https://github.com/mountainash-io/mountainash-central/tree/main/01.principles/mountainash-expresions).

## Development

```bash
git clone https://github.com/mountainash-io/mountainash.git
cd mountainash

# Run tests
hatch run test:test              # Full suite with coverage
hatch run test:test-quick        # Fast iteration (no coverage)

# Linting
hatch run ruff:check
hatch run ruff:fix

# Type checking
hatch run mypy:check
```

## License

MIT License. See [LICENSE](LICENSE) for details.
