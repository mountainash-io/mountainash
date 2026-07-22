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
        # No transitive ibis import occurred: the declaration path never
        # successfully imported the blocked backend.
        assert "ibis" not in sys.modules, "ibis was imported despite being blocked"
        facts = CapabilityRegistry.facts()
        refs = {f.upstream_ref for f in facts if f.upstream_ref}
        ibis_facts = [f for f in facts if str(f.backend) == "ibis"]
        n_ibis = len(ibis_facts)
        n_ibis_options = sum(f.option_value is not None for f in ibis_facts)
        assert "IB-DT-01" in refs, "IB-DT-01 missing without ibis: " + repr(sorted(refs))
        assert n_ibis_options == 304, (
            "expected 304 option_value-scoped ibis arithmetic facts "
            "(152 family defaults + 152 ibis-duckdb refinements), got %d"
            % n_ibis_options
        )
        assert n_ibis == 324, (
            "expected 324 ibis facts (20 existing import-safe facts + 304 "
            "option_value-scoped arithmetic facts), got %d" % n_ibis
        )
        print("OK", n_ibis, n_ibis_options)
        '''
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        "subprocess failed:\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr
    )
    assert "OK 324 304" in result.stdout
