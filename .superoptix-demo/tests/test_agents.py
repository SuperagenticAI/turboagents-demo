import pytest
from .superoptix-demo.agents import Agent

def test_agent_creation(test_config):
    """Test basic agent creation."""
    agent = Agent(test_config)
    assert agent.name == "test_agent"
    assert agent.version == "0.1.0"
