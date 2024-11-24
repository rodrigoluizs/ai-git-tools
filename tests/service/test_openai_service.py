import os
from unittest.mock import patch

import pytest
from src.service.openai_service import call_openai_api


def test_call_openai_api_no_api_key():
    """
    Test call_openai_api when OPENAI_API_KEY is not set.
    """
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as excinfo:
            call_openai_api("Test prompt")
        assert excinfo.value.code == 1  # Ensure it exits with code 1


@patch("src.service.openai_service.openai.ChatCompletion.create")
def test_call_openai_api_success(mock_create):
    """
    Test call_openai_api with a successful response from OpenAI API.
    """
    # Mock the OpenAI response
    mock_create.return_value = {"choices": [{"message": {"content": "Mocked response from OpenAI"}}]}

    # Set the OPENAI_API_KEY
    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
        response = call_openai_api("Test prompt")

    # Assertions
    assert response == "Mocked response from OpenAI"
    mock_create.assert_called_once_with(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=0.7,
    )


@patch("src.service.openai_service.openai.ChatCompletion.create", side_effect=Exception("API Error"))
def test_call_openai_api_error(mock_create):
    """
    Test call_openai_api when the OpenAI API raises an error.
    """
    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
        with pytest.raises(SystemExit) as excinfo:
            call_openai_api("Test prompt")
        assert excinfo.value.code == 1  # Ensure it exits with code 1

    # Ensure the error message is printed
    mock_create.assert_called_once_with(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=0.7,
    )
