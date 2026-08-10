"""
Tests for OpenAIProvider.

These tests verify:
- provider initialization
- provider name
- availability check
- missing API key handling
- successful response generation
- API failure handling
- empty response handling
- client reuse
"""

import pytest
from unittest.mock import Mock, patch

from app.report_analysis.providers.openai_provider import (
    OpenAIProvider,
    OPENAI_PROVIDER_NAME,
    DEFAULT_MODEL_NAME,
)

from app.ai_clinical_assistant.exceptions import (
    ConfigurationError,
    ProviderError,
)


def test_provider_name():
    """OpenAI provider should return correct name."""

    provider = OpenAIProvider(api_key="test-key")

    assert provider.provider_name() == OPENAI_PROVIDER_NAME


def test_provider_available():
    """Provider should be available when API key exists."""

    provider = OpenAIProvider(api_key="test-key")

    assert provider.is_available() is True


def test_missing_api_key():

    """Provider should raise configuration error without API key."""

    with patch(
        "app.report_analysis.providers.openai_provider.os.environ.get",
        return_value=None,
    ):
        with pytest.raises(ConfigurationError):
            OpenAIProvider()


def test_custom_model_name():

    """Provider should accept custom model."""

    provider = OpenAIProvider(
        api_key="test-key",
        model_name="custom-model",
    )

    assert provider._model_name == "custom-model"


def test_generate_success():

    """Provider should return generated OpenAI response."""

    provider = OpenAIProvider(api_key="test-key")

    mock_response = Mock()

    mock_response.choices = [
        Mock(
            message=Mock(
                content="AI clinical response"
            )
        )
    ]

    provider._client.chat.completions.create = Mock(
        return_value=mock_response
    )

    result = provider.generate(
        "Explain diabetes risk."
    )

    assert result == "AI clinical response"


def test_generate_empty_prompt():

    """Empty prompt should fail validation."""

    provider = OpenAIProvider(api_key="test-key")

    with pytest.raises(Exception):
        provider.generate("")


def test_generate_api_failure():

    """OpenAI API failure should raise ProviderError."""

    provider = OpenAIProvider(api_key="test-key")

    provider._client.chat.completions.create = Mock(
        side_effect=Exception("API failed")
    )

    with pytest.raises(ProviderError):
        provider.generate(
            "Generate medical summary."
        )


def test_generate_empty_response():

    """Empty OpenAI response should raise ProviderError."""

    provider = OpenAIProvider(api_key="test-key")

    mock_response = Mock()

    mock_response.choices = [
        Mock(
            message=Mock(
                content=None
            )
        )
    ]

    provider._client.chat.completions.create = Mock(
        return_value=mock_response
    )

    with pytest.raises(ProviderError):
        provider.generate(
            "Explain report."
        )


def test_client_initialized():

    """OpenAI client should initialize during construction."""

    provider = OpenAIProvider(
        api_key="test-key"
    )

    assert provider._client is not None


def test_default_model():

    """Default model should be used."""

    provider = OpenAIProvider(
        api_key="test-key"
    )

    assert provider._model_name == DEFAULT_MODEL_NAME