import pytest

@pytest.fixture
def test_config():
    return {
        "name": "test_agent",
        "version": "0.1.0"
    }
