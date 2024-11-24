import pytest

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Automatically set environment variables for all tests."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")