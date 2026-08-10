"""
Unit tests for AI Clinical Assistant custom exceptions.
"""

import pytest

from app.ai_clinical_assistant.exceptions import (
    AIClinicalAssistantError,
    AuthenticationError,
    ConfigurationError,
    ContextBuilderError,
    ConversationMemoryError,
    InvalidUserInputError,
    ModelError,
    PromptGenerationError,
    ProviderError,
    ProviderUnavailableError,
    RateLimitError,
    ResponseValidationError,
)


def test_base_exception():
    error = AIClinicalAssistantError("Base error")

    assert str(error) == "Base error"
    assert error.message == "Base error"


def test_provider_error():
    error = ProviderError(
        "Provider failed",
        provider_name="gemini",
    )

    assert str(error) == "Provider failed"
    assert error.provider_name == "gemini"


def test_provider_unavailable_error():
    error = ProviderUnavailableError(
        "Unavailable",
        provider_name="openai",
    )

    assert isinstance(error, ProviderError)
    assert error.provider_name == "openai"


def test_prompt_generation_error():
    error = PromptGenerationError("Prompt failed")

    assert isinstance(error, AIClinicalAssistantError)
    assert str(error) == "Prompt failed"


def test_context_builder_error():
    error = ContextBuilderError("Context failed")

    assert isinstance(error, AIClinicalAssistantError)
    assert str(error) == "Context failed"


def test_conversation_memory_error():
    error = ConversationMemoryError(
        "Conversation missing",
        conversation_id="abc123",
    )

    assert error.conversation_id == "abc123"
    assert str(error) == "Conversation missing"


def test_response_validation_error():
    error = ResponseValidationError("Invalid response")

    assert isinstance(error, AIClinicalAssistantError)
    assert str(error) == "Invalid response"


def test_invalid_user_input_error():
    error = InvalidUserInputError("Invalid input")

    assert isinstance(error, AIClinicalAssistantError)
    assert str(error) == "Invalid input"


def test_configuration_error():
    error = ConfigurationError("Bad configuration")

    assert isinstance(error, AIClinicalAssistantError)
    assert str(error) == "Bad configuration"


def test_rate_limit_error():
    error = RateLimitError(
        "Rate limited",
        provider_name="gemini",
        retry_after_seconds=60,
    )

    assert error.provider_name == "gemini"
    assert error.retry_after_seconds == 60


def test_authentication_error():
    error = AuthenticationError(
        "Authentication failed",
        provider_name="openai",
    )

    assert isinstance(error, ProviderError)
    assert error.provider_name == "openai"


def test_model_error():
    error = ModelError(
        "Model crashed",
        provider_name="gemini",
        model_name="gemini-2.5-pro",
    )

    assert error.provider_name == "gemini"
    assert error.model_name == "gemini-2.5-pro"