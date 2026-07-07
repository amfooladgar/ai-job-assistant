import pytest
from unittest.mock import MagicMock, patch
from src.llm.gemini_client import GeminiClient

def test_gemini_client_missing_key():
    # If no key is set or passed, is_configured should return False
    client = GeminiClient(api_key="")
    assert client.is_configured() is False
    
    # generate_text should raise ValueError
    with pytest.raises(ValueError) as excinfo:
        client.generate_text("Hello")
    assert "Gemini API key is not configured" in str(excinfo.value)

def test_gemini_client_no_external_call_on_init():
    # Patch google.genai.Client to ensure it isn't instantiated when API key is missing
    with patch("google.genai.Client") as mock_client:
        client = GeminiClient(api_key="")
        assert client.is_configured() is False
        mock_client.assert_not_called()

def test_gemini_client_external_call_only_on_generate():
    # Patch google.genai.Client
    with patch("google.genai.Client") as mock_client_class:
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        
        # Initialize client with a key
        client = GeminiClient(api_key="fake-api-key")
        assert client.is_configured() is True
        
        # Verify genai.Client was instantiated
        mock_client_class.assert_called_once_with(api_key="fake-api-key")
        
        # Verify generate_content was not called yet
        mock_instance.models.generate_content.assert_not_called()
        
        # Call generate_text
        mock_instance.models.generate_content.return_value = MagicMock(text="Gemini response text")
        response = client.generate_text("Explain quantum computing")
        
        # Verify generate_content was called on models
        mock_instance.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="Explain quantum computing"
        )
        assert response == "Gemini response text"
