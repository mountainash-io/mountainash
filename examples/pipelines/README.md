# Pipelines

How do I run a chain of units with a checkpoint and resume without redoing finished work?

The pipelines API is evolving, so expect names and behaviour to change between versions.

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/pipelines/example.py
```

Expected output:

```text
first run:  {'orders': 'complete', 'totals': 'complete', 'export': 'complete'}
second run: {'orders': 'complete', 'totals': 'complete', 'export': 'reused'}
rows exported: 2
```

Two `@unit` functions produce the orders frame and the shipped-order totals per customer, and a `ParquetDirectorySink` writes the totals to a temporary directory. Both runs use a `FileCheckpoint` on the same state directory. The second run marks `export` as `reused` because everything that determines it is unchanged. `orders` and `totals` run again as `complete`, since the file checkpoint does not retain dataframes. The checkpoint and the exported files live in a temporary directory that the recipe removes.

Book: [Values, identity and checkpoints](https://docs.mountainash.io/mountainash/chapters/15-pipelines/#values-identity-and-checkpoints). Next: [custom_validation_rule](../custom_validation_rule/).
