"""Disposable codec lowering; intentionally a Python UDF, not native-only proof."""
import polars as pl
from mountainash.core.dtypes.spike_numeric import numeric_text, numeric_native
from mountainash.core.dtypes.targets import TypeTarget


class SpikePolarsNumeric:
    def numeric_cast(self, x, /, dtype, rounding="TIE_TO_EVEN", failure_behavior="throw", preserve=False):
        text = x.cast(pl.String).map_elements(
            lambda value: numeric_text(value, dtype, rounding, failure_behavior, preserve),
            return_dtype=pl.String,
        )
        return text.cast(numeric_native(dtype, TypeTarget.POLARS), strict=True)
