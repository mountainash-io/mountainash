# Polars Documentation References

## Key Quote

From [`pl.duration()` API documentation](https://docs.pola.rs/api/python/stable/reference/api/polars.duration.html):

> **Notes**
> A `duration` represents a **fixed amount of time**. For example, `pl.duration(days=1)` means "exactly 24 hours". By contrast, `Expr.dt.offset_by('1d')` means "1 calendar day", which could sometimes be 23 hours or 25 hours depending on Daylight Savings Time.
>
> **For non-fixed durations such as "calendar month" or "calendar day", please use `Expr.dt.offset_by()` instead.**

## Documentation Links

### API References

1. **`pl.duration()` - Fixed durations only**
   https://docs.pola.rs/api/python/stable/reference/api/polars.duration.html

   Parameters: `weeks`, `days`, `hours`, `minutes`, `seconds`, `milliseconds`, `microseconds`, `nanoseconds`
   ❌ Does NOT support: `months`, `years`

2. **`Expr.dt.offset_by()` - Calendar-based intervals**
   https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.dt.offset_by.html

   Format: String like `"3mo"`, `"1y"`, `"-2mo"`, `"1y2mo3d"`
   ✅ Supports: `y`, `mo`, `w`, `d`, `h`, `m`, `s`, `ms`, `us`, `ns`

### User Guides

3. **Temporal Data in Polars**
   https://docs.pola.rs/user-guide/expressions/temporal/

   General guide on working with dates, times, and durations

## Function Signatures

### `pl.duration()`
```python
polars.duration(
    *,
    weeks: Expr | str | int | float | None = None,
    days: Expr | str | int | float | None = None,
    hours: Expr | str | int | float | None = None,
    minutes: Expr | str | int | float | None = None,
    seconds: Expr | str | int | float | None = None,
    milliseconds: Expr | str | int | float | None = None,
    microseconds: Expr | str | int | float | None = None,
    nanoseconds: Expr | str | int | float | None = None,
    time_unit: TimeUnit | None = None
) -> Expr
```

Note: No `months` or `years` parameters!

### `Expr.dt.offset_by()`
```python
Expr.dt.offset_by(by: str | Expr) -> Expr
```

String format examples:
- `"3mo"` - Add 3 months
- `"-1y"` - Subtract 1 year
- `"1y2mo3d"` - Add 1 year, 2 months, and 3 days
- `"2h30m"` - Add 2 hours and 30 minutes

## Why This Matters for Ibis

Ibis represents intervals as separate parameters:
```python
ibis.interval(months=3)  # Ibis API
ibis.interval(years=1)   # Ibis API
```

But the Polars backend tries to compile this to:
```python
pl.duration(months=3)  # ❌ Doesn't exist!
pl.duration(years=1)   # ❌ Doesn't exist!
```

The correct Polars approach would be:
```python
expr.dt.offset_by("3mo")  # ✅ Correct
expr.dt.offset_by("1y")   # ✅ Correct
```

But this requires architectural changes in Ibis to convert from structured parameters to string format.
