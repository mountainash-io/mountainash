# Substrait arithmetic fixture pin

- Release: `v0.98.0` (published 2026-07-19)
- Commit: `b322d463804660674e43c9d2b659730375e3026e`
- Source: <https://raw.githubusercontent.com/substrait-io/substrait/b322d463804660674e43c9d2b659730375e3026e/extensions/functions_arithmetic.yaml>
- SHA-256: `278e62f76a7a1cada90f65bc60b940bfb0bcb8a7ce8d1d80ce780f6bc18c15f7`

## Rationale

This pin deliberately selects the newest stable Substrait specification release
available on 2026-07-21. The release tag resolves directly to the full commit
above, so the fixture and generated constants cannot drift with mutable
`main`. The per-topic `PIN_arithmetic.txt` pointer prevents other Substrait
fixture topics or later re-pins from being selected by directory ordering.

## Observed option encoding

At this revision, `scalar_functions` is a list of 34 function groups and each
`impls[].options` value is a mapping. Each option name maps to a mapping whose
`values` member is a list, for example:

```yaml
options:
  overflow:
    values: [SILENT, SATURATE, ERROR]
```

The fixture guard additionally accepts historical list-encoded options so a
future deliberate re-pin fails on domain drift rather than parser shape alone.
