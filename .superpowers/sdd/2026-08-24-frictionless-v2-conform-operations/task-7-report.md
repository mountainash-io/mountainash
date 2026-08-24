
## Backend parser investigation

The proposed LIST.PARSE scalar route was probed and rejected for valid-token support: Narwhals pandas requires PyArrow-backed strings, Ibis DuckDB rejects the NUL delimiter SQL, unsupported dialects have exact LIST.PARSE gates, and custom token values fail the existing boolean list parser. The branch was restored to the established backend-safe boolean mapping and the incompatible regression removed. A dedicated scalar boolean operation/backend matrix is required to satisfy throw-on-`maybe` without regressing valid tokens.
