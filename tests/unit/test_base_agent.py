"""Tests for base agent."""


def test_base_agent_exists():
    """Test that base agent module exists."""
    from src.agents import base_agent

    assert base_agent is not None
