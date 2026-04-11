
from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.typespec.datapackage import DataResource
    import polars as pl

"""Inline data reader for DataResource.data — uses pydata ingress machinery."""

def read_inline(res: DataResource) -> pl.LazyFrame:
    """Convert inline DataResource.data to a Polars LazyFrame via pydata ingress."""
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress

    df = PydataIngress.convert(res.data)
    return df.lazy()
