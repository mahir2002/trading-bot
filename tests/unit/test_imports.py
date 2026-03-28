"""Test that core modules can be imported."""


def test_import_src_package():
    """Test that src package can be imported."""
    import src

    assert src.__version__ == "2.0.0"


def test_import_agents():
    """Test that agents module can be imported."""
    import src.agents

    assert src.agents is not None


def test_import_core():
    """Test that core module can be imported."""
    import src.core

    assert src.core is not None


def test_import_api():
    """Test that api module can be imported."""
    import src.api

    assert src.api is not None


def test_import_trading():
    """Test that trading module can be imported."""
    import src.trading

    assert src.trading is not None
