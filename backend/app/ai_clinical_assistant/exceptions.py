"""Custom exceptions for the AI Clinical Assistant module.

Every exception raised anywhere in the AI Clinical Assistant module
inherits, directly or transitively, from a single base exception,
:class:`AIClinicalAssistantError`. This allows calling code to catch
all module-specific failures with one except clause, while still
allowing precise handling of specific failure modes where needed.
"""

from __future__ import annotations


class AIClinicalAssistantError(Exception):
    """Base exception for every error raised by the AI Clinical Assistant.

    All other exceptions in this module inherit from this class, either
    directly or through an intermediate subclass such as
    :class:`ProviderError`.

    Attributes:
        message: A human-readable description of the error.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: A human-readable description of the error.
        """
        self.message = message
        super().__init__(message)


class ProviderError(AIClinicalAssistantError):
    """Base exception for errors raised by an LLM provider.

    Attributes:
        message: A human-readable description of the error.
        provider_name: Name of the provider that raised the error, if
            known.
    """

    def __init__(self, message: str, provider_name: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: A human-readable description of the error.
            provider_name: Name of the provider that raised the error,
                if known.
        """
        self.provider_name = provider_name
        super().__init__(message)


class ProviderUnavailableError(ProviderError):
    """Raised when an LLM provider cannot be reached or is not configured."""


class PromptGenerationError(AIClinicalAssistantError):
    """Raised when prompt construction fails."""


class ContextBuilderError(AIClinicalAssistantError):
    """Raised when structured clinical context cannot be built."""


class ConversationMemoryError(AIClinicalAssistantError):
    """Raised when a conversation memory operation fails.

    Attributes:
        message: A human-readable description of the error.
        conversation_id: The id of the conversation involved in the
            error, if known.
    """

    def __init__(self, message: str, conversation_id: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: A human-readable description of the error.
            conversation_id: The id of the conversation involved in the
                error, if known.
        """
        self.conversation_id = conversation_id
        super().__init__(message)


class ResponseValidationError(AIClinicalAssistantError):
    """Raised when an AI-generated response fails validation."""


class InvalidUserInputError(AIClinicalAssistantError):
    """Raised when user-supplied input fails validation."""


class ConfigurationError(AIClinicalAssistantError):
    """Raised when the assistant is misconfigured or configuration is missing."""


class RateLimitError(ProviderError):
    """Raised when an LLM provider reports that a rate limit was exceeded.

    Attributes:
        message: A human-readable description of the error.
        provider_name: Name of the provider that raised the error, if
            known.
        retry_after_seconds: Suggested wait time, in seconds, before
            retrying, if known.
    """

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: A human-readable description of the error.
            provider_name: Name of the provider that raised the error,
                if known.
            retry_after_seconds: Suggested wait time, in seconds, before
                retrying, if known.
        """
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message, provider_name=provider_name)


class AuthenticationError(ProviderError):
    """Raised when authentication with an LLM provider fails."""


class ModelError(ProviderError):
    """Raised when an LLM provider's underlying model fails to generate a response.

    Attributes:
        message: A human-readable description of the error.
        provider_name: Name of the provider that raised the error, if
            known.
        model_name: Name of the model that failed, if known.
    """

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        model_name: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: A human-readable description of the error.
            provider_name: Name of the provider that raised the error,
                if known.
            model_name: Name of the model that failed, if known.
        """
        self.model_name = model_name
        super().__init__(message, provider_name=provider_name)