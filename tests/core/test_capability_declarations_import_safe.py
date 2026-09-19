"""Declaration import remains independent of optional backend packages."""
from __future__ import annotations

import subprocess
import sys
import textwrap


def test_ibis_information_and_policies_load_without_ibis_installed():
    script = textwrap.dedent(
        """
        import sys

        class BlockIbis:
            def find_spec(self, name, path=None, target=None):
                if name == "ibis" or name.startswith("ibis."):
                    raise ModuleNotFoundError("blocked optional backend: " + name)
                return None

        sys.meta_path.insert(0, BlockIbis())
        from mountainash.core.capabilities import CapabilityRegistry
        from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
        from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery, PolicyQuery

        load_all_capability_declarations()
        assert "ibis" not in sys.modules
        captured = CapabilityRegistry.capture()
        result = captured.search(CatalogueQuery(information=InformationQuery(), policies=PolicyQuery()))
        assert result.information is not None
        assert result.policies is not None
        print("OK")
        """
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout
