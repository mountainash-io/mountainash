"""Backwards-compatibility shim for mountainash_expressions.

This package has been renamed to ``mountainash``.
Please update your imports::

    import mountainash as ma            # NEW
    import mountainash_expressions as ma  # DEPRECATED
"""
import importlib
import importlib.abc
import importlib.machinery
import sys
import warnings

warnings.warn(
    "mountainash_expressions is deprecated. "
    "Use 'import mountainash as ma' instead.",
    DeprecationWarning,
    stacklevel=2,
)


class _ShimFinder(importlib.abc.MetaPathFinder):
    """Import hook: mountainash_expressions.X -> mountainash.expressions.X."""

    PREFIX = "mountainash_expressions."
    TARGET = "mountainash.expressions."

    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith(self.PREFIX):
            return None
        new_name = self.TARGET + fullname[len(self.PREFIX):]
        # Try to find the real module spec
        try:
            real_spec = importlib.util.find_spec(new_name)
        except (ModuleNotFoundError, ValueError):
            return None
        if real_spec is None:
            return None
        # Return a spec that will load the real module, then alias it
        return importlib.machinery.ModuleSpec(
            fullname,
            _ShimLoader(new_name),
            origin=real_spec.origin,
            is_package=real_spec.submodule_search_locations is not None,
        )


class _ShimLoader(importlib.abc.Loader):
    """Loader that imports the target module and aliases it."""

    def __init__(self, target_name):
        self.target_name = target_name

    def create_module(self, spec):
        return None  # Use default module creation

    def exec_module(self, module):
        real_mod = importlib.import_module(self.target_name)
        # Copy all attributes from the real module
        module.__dict__.update(real_mod.__dict__)
        # Also register the real module under the old name
        sys.modules[module.__name__] = real_mod
        # Ensure submodule paths work
        if hasattr(real_mod, '__path__'):
            module.__path__ = real_mod.__path__


# Install the import hook BEFORE any re-exports
sys.meta_path.insert(0, _ShimFinder())

# Re-export top-level API
from mountainash import *  # noqa: F401,F403
from mountainash import __version__  # noqa: F401
