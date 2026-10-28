
## P1 rereview repair

Follow-up repair commit adds outer-marker-dependent native-array paths for Narwhals and Ibis, typed top-level-null handling for Ibis native objects, executes Polars lazy GeoJSON in the matrix, and expands ALL_BACKENDS execution coverage for supported native throw paths and exact unsupported gates.

- P1 regression matrix: **22 passed**, 296 deselected.
- Scoped Ruff: all checks passed.


## Exhaustive ALL_BACKENDS matrix

Added the complete Sections 17.3–17.4 cross-backend matrix to
`tests/conform/cross_backend/test_v2_operations.py`.

- Every geopoint format/source cell (`default/lexical`, `array/lexical`,
  `array/native`, and `object/native`) now runs both `throw` and `null`
  through every `ALL_BACKENDS` entry.
- Supported cells materialize valid values and top-level nulls, and exercise
  invalid default text, lexical JSON arrays, native array length/null/nonfinite
  coordinates, and native object null/nonfinite coordinates.
- Unsupported lexical/native-array/object cells assert the exact predicate
  gate, including the SQLite-specific overlap between the native null and
  dialect facts.
- GeoJSON parse (`default` and `topojson`) covers both failure modes, valid
  object roots, top-level null, malformed JSON, non-object roots, and
  canonical JSON revalidation. GeoJSON serialization covers both formats and
  failure modes, with exact gates for every non-Polars backend.

Evidence:

```text
280 passed, 290 deselected
ruff: all checks passed
```

## P1 exceptional GeoJSON/TopoJSON document repair

Replaced grouped parse inputs with independently parameterized documents
through every `ALL_BACKENDS` cell for both `default` and `topojson` formats
and both failure behaviors. The matrix now executes one document per
supported test and asserts the exact whole-operation capability gate for
unsupported backends.

Covered documents:

- valid object, empty object, and leading-whitespace object;
- JSON `null`, string, number, boolean, and array roots;
- malformed JSON; and
- non-canonical JSON with a trailing comma.

Throw-mode assertions now scope `pytest.raises` to exactly one document,
so an early failing row cannot mask later inputs.

Evidence:

```text
360 passed, 498 deselected
406 passed, 478 deselected
ruff: All checks passed
```