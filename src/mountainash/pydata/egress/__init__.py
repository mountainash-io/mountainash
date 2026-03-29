"""
Egress module: DataFrame -> Python data conversion.

Supports conversion to:
- List of dataclass instances
- List of Pydantic models
- Dictionary of lists (column-oriented)
- List of dictionaries (row-oriented)
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules=[],
    submod_attrs={
        "base_egress_strategy": ["BaseEgressStrategy"],
        "egress_factory": ["DataFrameEgressFactory"],
        "egress_pydata_from_polars": ["EgressPydataFromPolars"],
        "egress_to_pythondata": ["EgressToPythonData"],
        "egress_helpers": ["EgressHelpers"],
    },
)
