"""Inline data reader for DataResource.data — uses pydata ingress machinery."""
from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from mountainash.typespec.datapackage import DataResource


def read_inline(res: DataResource) -> pl.LazyFrame:
    """Convert inline DataResource.data to a Polars LazyFrame via pydata ingress."""
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress

    df = PydataIngress.convert(res.data)
    return df.lazy()
