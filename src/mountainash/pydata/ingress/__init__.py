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
        "ingress_from_dataclass": ["IngressFromDataclass"],
        "ingress_from_pydantic": ["IngressFromPydantic"],
        "ingress_from_pydict": ["IngressFromPydict"],
        "ingress_from_pylist": ["IngressFromPylist"],
        "ingress_from_namedtuple": ["IngressFromNamedtuple"],
        "ingress_from_tuple": ["IngressFromTuple"],
        "ingress_from_indexed": ["IngressFromIndexed"],
        "ingress_from_series": ["IngressFromSeries"],
        "ingress_from_collection": ["IngressFromCollection"],
        "ingress_from_default": ["IngressFromDefault"],
    },
)
