"""Capability declarations must load without optional backends installed
(spine Finding A: the typed join must not false-orphan ibis-linked open
entries in a minimal install)."""
import subprocess
import sys
import textwrap


def test_ibis_capabilities_register_without_ibis_installed():
    script = textwrap.dedent(
        '''
        import sys
        class _BlockIbis:
            def find_spec(self, name, path=None, target=None):
                if name == "ibis" or name.startswith("ibis."):
                    raise ModuleNotFoundError("No module named %r (blocked by test)" % name)
                return None
        sys.meta_path.insert(0, _BlockIbis())
        try:
            import ibis  # noqa: F401
        except ModuleNotFoundError:
            pass
        else:
            print("SETUP-FAIL: ibis still importable"); sys.exit(3)

        from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
        from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
        from mountainash.core.constants import CONST_BACKEND
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
        )
        load_all_capability_declarations()
        # No transitive ibis import occurred: the declaration path never
        # successfully imported the blocked backend.
        assert "ibis" not in sys.modules, "ibis was imported despite being blocked"
        facts = CapabilityRegistry.facts()
        refs = {f.upstream_ref for f in facts if f.upstream_ref}
        assert "IB-DT-01" in refs, "IB-DT-01 missing without ibis: " + repr(sorted(refs))
        family = CapabilityRegistry.capability_for(
            FK_ARITH.ABS, "overflow", CONST_BACKEND.IBIS, None,
            option_value="ERROR",
        )
        duckdb = CapabilityRegistry.capability_for(
            FK_ARITH.ABS, "overflow", CONST_BACKEND.IBIS, "ibis-duckdb",
            option_value="ERROR",
        )
        assert family is not None and family.level is CapabilityLevel.UNSUPPORTED
        assert duckdb is not None and duckdb.level is CapabilityLevel.EXPR_CAPABLE
        assert duckdb.probe_exempt
        print("OK")
        '''
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        "subprocess failed:\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr
    )
    assert "OK" in result.stdout
