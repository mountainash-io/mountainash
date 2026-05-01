"""BaseDataContract — pandera DataFrameModel with multi-framework input support."""
from __future__ import annotations

from typing import Any, Optional

import polars as pl
import pandera.polars as pa


class BaseDataContract(pa.DataFrameModel):
    """Base class for data contracts.

    Accepts polars or pandas DataFrames as input. All inputs are converted
    to Polars before validation. Always returns polars.DataFrame.
    """

    class Config:
        coerce = True

    @classmethod
    def _to_polars(cls, data: Any) -> pl.DataFrame:
        if isinstance(data, pl.DataFrame):
            return data
        if isinstance(data, pl.LazyFrame):
            return data.collect()
        # pandas
        try:
            import pandas as pd

            if isinstance(data, pd.DataFrame):
                return pl.from_pandas(data)
        except ImportError:
            pass
        raise TypeError(f"Unsupported data type: {type(data)}")

    @classmethod
    def validate_datacontract(
        cls,
        data: Any,
        *,
        head: Optional[int] = None,
        tail: Optional[int] = None,
        sample: Optional[int] = None,
        random_seed: Optional[int] = None,
    ) -> pl.DataFrame:
        """Validate data against this contract (lazy — collects all errors)."""
        df = cls._to_polars(data)
        if head is not None:
            df = df.head(head)
        if tail is not None:
            df = df.tail(tail)
        if sample is not None:
            df = df.sample(n=sample, seed=random_seed)
        return cls.validate(df, lazy=True)

    @classmethod
    def validate_datacontract_quick(
        cls,
        data: Any,
        *,
        head: Optional[int] = None,
        tail: Optional[int] = None,
        sample: Optional[int] = None,
        random_seed: Optional[int] = None,
    ) -> pl.DataFrame:
        """Validate data against this contract (eager — fails on first error)."""
        df = cls._to_polars(data)
        if head is not None:
            df = df.head(head)
        if tail is not None:
            df = df.tail(tail)
        if sample is not None:
            df = df.sample(n=sample, seed=random_seed)
        return cls.validate(df, lazy=False)
