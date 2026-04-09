"""
mountainash-pydata: Python Data Conversion for DataFrames

This package provides bidirectional conversion between Python data structures
and DataFrames:

- **Ingress**: Python data (dataclass, Pydantic, dict, list) → Polars DataFrame
- **Egress**: DataFrame → Python data (dataclass, Pydantic, dict, list)

Example:
    from mountainash.pydata import constants

    # Ingress: Python → DataFrame
    from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory

    # Egress: DataFrame → Python
    from mountainash.pydata.egress.egress_factory import EgressFactory
"""
from __future__ import annotations

__all__: list[str] = [
    # Public API will be added as modules are stabilized
]
