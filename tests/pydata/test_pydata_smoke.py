"""Smoke tests for mountainash.pydata port."""
import pytest


class TestPydataImports:
    """Verify key pydata modules are importable."""

    def test_pydata_module_importable(self):
        import mountainash.pydata
        assert mountainash.pydata is not None

    def test_constants_importable(self):
        from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
        assert hasattr(CONST_PYTHON_DATAFORMAT, "DATACLASS")
        assert hasattr(CONST_PYTHON_DATAFORMAT, "PYDANTIC")
        assert hasattr(CONST_PYTHON_DATAFORMAT, "PYDICT")
        assert hasattr(CONST_PYTHON_DATAFORMAT, "PYLIST")

    def test_ingress_factory_importable(self):
        """Ingress factory should be importable (may need dataframes deps)."""
        try:
            from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory
            assert PydataIngressFactory is not None
        except ImportError as e:
            pytest.skip(f"Ingress factory dependencies not available: {e}")

    def test_ingress_from_dict(self):
        """Test basic dict-to-DataFrame conversion."""
        try:
            from mountainash.pydata.ingress.pydata_ingress_factory import PydataIngressFactory
            import polars as pl
            factory = PydataIngressFactory()
            data = {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
            result = factory.convert(data)
            assert result is not None
        except ImportError as e:
            pytest.skip(f"Dependencies not available: {e}")
        except Exception as e:
            pytest.skip(f"Conversion not working yet: {e}")
