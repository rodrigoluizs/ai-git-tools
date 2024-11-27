import os
import pytest
from unittest.mock import patch, MagicMock
from src.service.openai_service import OpenAiService


def test_no_api_key():
    """Test that the service exits if the API key is not set."""
    with patch.dict(os.environ, {}, clear=True):  # Clear environment variables
        with pytest.raises(SystemExit) as excinfo:
            OpenAiService()
        assert excinfo.value.code == 1


@patch("src.service.openai_service.openai.OpenAI")
def test_call_success(mock_openai):
    """Test a successful API call."""
    mock_response = MagicMock()
    mock_response.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"key": "value"}'))]
    )
    mock_openai.return_value = mock_response

    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
        service = OpenAiService()
        response = service.call("Test prompt")

    assert response == {"key": "value"}
    mock_response.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Test prompt"}],
    )


@patch("src.service.openai_service.openai.OpenAI")
def test_call_api_error(mock_openai):
    """Test API call when an error occurs."""
    mock_response = MagicMock()
    mock_response.chat.completions.create.side_effect = Exception("API Error")
    mock_openai.return_value = mock_response

    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
        service = OpenAiService()
        with pytest.raises(SystemExit) as excinfo:
            service.call("Test prompt")

        assert excinfo.value.code == 1
    mock_response.chat.completions.create.assert_called_once_with(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Test prompt"}],
    )
