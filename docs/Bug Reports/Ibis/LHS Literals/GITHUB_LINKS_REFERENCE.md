# GitHub Links Reference for Polars Bug Report

This document provides properly formatted GitHub links for all resources referenced in our bug investigation.

## Commit Links

To link to a specific commit, use:
```
https://github.com/pola-rs/polars/commit/{COMMIT_HASH}
```

**The Problematic Commit (introduced the bug)**:
- Short hash: `30edab06f`
- Full link: https://github.com/pola-rs/polars/commit/30edab06f
- GitHub accepts shortened hashes and redirects to the full commit

## Pull Request Links

Format: `https://github.com/pola-rs/polars/pull/{PR_NUMBER}`

**PR #10446** (The one that introduced the bug):
- Link: https://github.com/pola-rs/polars/pull/10446
- Title: "feat(rust, python): preserve base dtype when raising to uint power"

**PR #3768** (Added basic literal pow support):
- Link: https://github.com/pola-rs/polars/pull/3768

## Issue Links

Format: `https://github.com/pola-rs/polars/issues/{ISSUE_NUMBER}`

**Related Issues**:

- **#21596** (OPEN - Related): https://github.com/pola-rs/polars/issues/21596
  - "Pow operator takes the type of a literal base over the type of the column exponent"

- **#3764** (CLOSED - Basic pow support): https://github.com/pola-rs/polars/issues/3764
  - "pow() operation does not support having a literal on the left"

**Other Overflow Issues (Different focus)**:
- **#1941**: https://github.com/pola-rs/polars/issues/1941 - "Integer overflow issues" (aggregations)
- **#8595**: https://github.com/pola-rs/polars/issues/8595 - "Protection against integer overflows" (general)
- **#21318**: https://github.com/pola-rs/polars/issues/21318 - "rolling_sum with small integer types does not cast to Int64"

## Source Code Links

### Direct File Links

Format: `https://github.com/pola-rs/polars/blob/{BRANCH}/{PATH}`

**The Bug Location**:
```
https://github.com/pola-rs/polars/blob/main/crates/polars-plan/src/plans/aexpr/function_expr/schema.rs
```

**How Other Operators Handle It**:
```
https://github.com/pola-rs/polars/blob/main/crates/polars-plan/src/plans/conversion/type_coercion/binary.rs
```

### Line-Specific Links

Format: `https://github.com/pola-rs/polars/blob/{BRANCH}/{PATH}#L{LINE}`

**The pow_dtype() function (lines 711-720)**:
```
https://github.com/pola-rs/polars/blob/main/crates/polars-plan/src/plans/aexpr/function_expr/schema.rs#L711-L720
```

**The get_supertype() call (line 242 in binary.rs)**:
```
https://github.com/pola-rs/polars/blob/main/crates/polars-plan/src/plans/conversion/type_coercion/binary.rs#L242
```

## Markdown Link Formats

### Standard Link
```markdown
[Link text](URL)
```

### Link with Code
```markdown
See [`pow_dtype()`](https://github.com/pola-rs/polars/blob/main/crates/polars-plan/src/plans/aexpr/function_expr/schema.rs#L711-L720)
```

### Commit Reference
```markdown
Introduced in [commit 30edab06f](https://github.com/pola-rs/polars/commit/30edab06f)
```

### Issue Cross-Reference
```markdown
Related to #21596 (or use full link: https://github.com/pola-rs/polars/issues/21596)
```

## Usage in Bug Report

When filing the bug report on GitHub, you can use short references that GitHub will auto-link:
- `#21596` → Auto-links to issue 21596
- `30edab06f` → Auto-links to commit (if typing in GitHub issue/PR)
- `#10446` → Auto-links to PR 10446

Or use full links for clarity:
- `https://github.com/pola-rs/polars/commit/30edab06f`
- `https://github.com/pola-rs/polars/issues/21596`
- `https://github.com/pola-rs/polars/pull/10446`

## Quick Copy-Paste References

For your bug report, here are the key links ready to copy:

**The Culprit**:
```
Introduced in commit 30edab06f (https://github.com/pola-rs/polars/commit/30edab06f)
via PR #10446 (https://github.com/pola-rs/polars/pull/10446)
```

**Related Issues**:
```
Related to #21596 (type handling) but focuses on integer overflow
Previously #3764 added basic pow support
```

**Source Code**:
```
Bug in pow_dtype(): https://github.com/pola-rs/polars/blob/main/crates/polars-plan/src/plans/aexpr/function_expr/schema.rs#L711-L720
How it should work: https://github.com/pola-rs/polars/blob/main/crates/polars-plan/src/plans/conversion/type_coercion/binary.rs#L242
```
