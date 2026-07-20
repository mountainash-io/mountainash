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

        from mountainash.core.capabilities import CapabilityRegistry
        from mountainash.core.capabilities.bootstrap import load_all_capability_declarations
        load_all_capability_declarations()
        refs = {f.upstream_ref for f in CapabilityRegistry.facts() if f.upstream_ref}
        n_ibis = sum(1 for f in CapabilityRegistry.facts() if str(f.backend) == "ibis")
        assert "IB-DT-01" in refs, "IB-DT-01 missing without ibis: " + repr(sorted(refs))
        assert n_ibis == 19, "expected 19 ibis facts, got %d" % n_ibis
        print("OK", n_ibis)
        '''
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        "subprocess failed:\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr
    )
    assert "OK 19" in result.stdout
