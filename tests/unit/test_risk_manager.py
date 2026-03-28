"""Tests for risk manager."""

import pytest


def test_risk_manager_exists():
    """Test that risk manager module exists."""
    from src.core import risk_manager
    assert risk_manager is not None
