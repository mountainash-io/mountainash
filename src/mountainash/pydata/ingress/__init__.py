"""
Ingress module: Python data -> Polars DataFrame conversion.

Supports conversion from:
- dataclass instances and lists
- Pydantic models and lists
- Python dictionaries (column-oriented)
- Python lists of dictionaries (row-oriented)
- Named tuples
- Series objects
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules=[],
    submod_attrs={
        "base_pydata_ingress_handler": ["BasePydataIngressHandler"],
        "pydata_ingress_factory": ["PydataIngressFactory"],
        "pydata_ingress": ["PydataIngress"],
        "ingress_from_dataclass": ["DataframeFromDataclass"],
        "ingress_from_pydantic": ["DataframeFromPydantic"],
        "ingress_from_pydict": ["DataframeFromPydict"],
        "ingress_from_pylist": ["DataframeFromPylist"],
        "ingress_from_namedtuple": ["DataframeFromNamedTuple"],
        "ingress_from_tuple": ["DataframeFromTuple"],
        "ingress_from_indexed": ["DataframeFromIndexedData"],
        "ingress_from_series": ["DataframeFromSeriesDict"],
        "ingress_from_collection": ["IngressFromCollection"],
        "ingress_from_default": ["DataframeFromDefault"],
    },
)
