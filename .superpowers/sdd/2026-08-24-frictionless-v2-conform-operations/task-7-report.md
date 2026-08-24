
## Recursive struct diagnostic correction

`_shape_detail` now renders ordered recursive struct children as `STRUCT{field:<child detail>}`. Added a nested same-key differing-child regression asserting both actual `source_detail` and declared `requirement` retain child evidence.

Focused evaluator gate: 18 passed; diff check passed.
