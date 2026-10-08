"""Optional physical support must not affect base execution or AST building."""
from __future__ import annotations

import subprocess
import sys
import textwrap


def test_missing_physical_dependency_is_lazy_and_actionable():
    body = textwrap.dedent("""
        import importlib.abc
        import sys

        class BlockData(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "mountainash_data" or fullname.startswith("mountainash_data."):
                    raise ModuleNotFoundError("blocked optional dependency", name=fullname)

        sys.meta_path.insert(0, BlockData())
        import mountainash as ma
        import polars as pl
        import narwhals as nw
        ma.col("x").add(1)
        for frame in (pl.DataFrame({"x": [1]}), nw.from_native(pl.DataFrame({"x": [1]}))):
            assert ma.relation(frame).to_polars()["x"].to_list() == [1]
        import ibis
        from mountainash.relations.core.owned_copy import owned_copy
        connection = ibis.polars.connect()
        source = connection.create_table("source", pl.DataFrame({"x": [7]}))
        copy = owned_copy(source)
        name = copy.value.op().name
        connection.drop_table("source")
        assert ma.relation(copy.value).to_dicts() == [{"x": 7}]
        copy.release()
        assert name not in connection.list_tables()
        connection.disconnect()
        assert "mountainash_data" not in sys.modules
        from mountainash.core.lazy_imports import import_mountainash_data
        try:
            import_mountainash_data()
        except ImportError as exc:
            assert "mountainash[ibis]" in str(exc)
            assert exc.__cause__ is not None
        else:
            raise AssertionError("missing dependency was silently accepted")
    """)
    result = subprocess.run([sys.executable, "-c", body], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
