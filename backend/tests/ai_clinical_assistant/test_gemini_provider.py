"""Tests for GeminiProvider."""

import pytest
from unittest.mock import MagicMock, patch

from app.report_analysis.providers.gemini_provider import GeminiProvider
from app.ai_clinical_assistant.exceptions import (
    ProviderError,
    ProviderUnavailableError,
    InvalidUserInputError,
)


def test_provider_name():
    """Gemini provider name should be returned correctly."""
    provider = GeminiProvider()

    assert provider.provider_name() == "gemini"


def test_provider_unavailable_without_configuration():
    """Gemini should be unavailable without API key/model."""

    provider = GeminiProvider()

    with patch(
        "app.report_analysis.providers.gemini_provider.settings"
    ) as mock_settings:
        mock_settings.gemini_api_key = None
        mock_settings.gemini_model = None

        assert provider.is_available() is False


def test_provider_available_with_configuration():
    """Gemini should be available when configured."""

    provider = GeminiProvider()

    with patch(
        "app.report_analysis.providers.gemini_provider.settings"
    ) as mock_settings:
        mock_settings.gemini_api_key = "fake-key"
        mock_settings.gemini_model = "gemini-test-model"

        assert provider.is_available() is True


def test_generate_empty_prompt():
    """Empty prompts should raise validation error."""

    provider = GeminiProvider()

    with pytest.raises(InvalidUserInputError):
        provider.generate("")


def test_generate_whitespace_prompt():
    """Whitespace prompts should raise validation error."""

    provider = GeminiProvider()

    with pytest.raises(InvalidUserInputError):
        provider.generate("   ")


def test_generate_when_provider_unavailable():
    """Unavailable Gemini should raise error."""

    provider = GeminiProvider()

    with patch(
        "app.report_analysis.providers.gemini_provider.settings"
    ) as mock_settings:
        mock_settings.gemini_api_key = None
        mock_settings.gemini_model = None

        with pytest.raises(ProviderUnavailableError):
            provider.generate("Explain diabetes risk")


def test_generate_success():
    """Gemini should return generated text."""

    provider = GeminiProvider()

    fake_response = MagicMock()
    fake_response.text = "Gemini response"

    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response

    provider._model = fake_model

    with patch(
        "app.report_analysis.providers.gemini_provider.settings"
    ) as mock_settings:
        mock_settings.gemini_model = "gemini-test"

        result = provider.generate("Explain hypertension")

    assert result == "Gemini response"


def test_generate_api_failure():
    """Gemini API failure should raise ProviderError."""

    provider = GeminiProvider()

    fake_model = MagicMock()
    fake_model.generate_content.side_effect = Exception("API failed")

    provider._model = fake_model

    with pytest.raises(ProviderError):
        provider.generate("Explain symptoms")


def test_get_model_cached():
    """Gemini model should be reused."""

    provider = GeminiProvider()

    fake_model = MagicMock()
    provider._model = fake_model

    result = provider._get_model()

    assert result is fake_model