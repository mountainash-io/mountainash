"""Disposable DuckDB UDF lowering; not a native-only or other-dialect claim."""
import ibis
from mountainash.core.dtypes.spike_numeric import numeric_text, numeric_native
from mountainash.core.dtypes.targets import TypeTarget


class SpikeIbisNumeric:
    def numeric_cast(self, x, /, dtype, rounding="TIE_TO_EVEN", failure_behavior="throw", preserve=False):
        @ibis.udf.scalar.python(signature=(("string",), "string"), null_handling="special")
        def item241_numeric_text(value):
            return numeric_text(value, dtype, rounding, failure_behavior, preserve)

        text = item241_numeric_text(x.cast("string"))
        return text.cast(numeric_native(dtype, TypeTarget.IBIS))
