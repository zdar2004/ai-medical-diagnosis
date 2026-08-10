"""Runtime configuration for the AI Clinical Assistant module.

This module defines :class:`AIClinicalAssistantConfig`, a
``pydantic-settings`` model that loads AI Clinical Assistant
configuration from environment variables (and an optional ``.env``
file), validates it, and exposes it through a single settings
singleton, :data:`settings`.
"""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.ai_clinical_assistant.exceptions import ConfigurationError
from app.ai_clinical_assistant.schemas import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROVIDER_NAME,
    DEFAULT_TEMPERATURE,
    MAX_MAX_TOKENS,
    MAX_TEMPERATURE,
    MIN_MAX_TOKENS,
    MIN_TEMPERATURE,
)
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

SUPPORTED_PROVIDERS: frozenset[str] = frozenset({"dummy", "gemini", "openai"})
DEFAULT_GEMINI_MODEL: str = "gemini-1.5-flash"
DEFAULT_OPENAI_MODEL: str = "gpt-4o-mini"
DUMMY_PROVIDER_MODEL_NAME: str = "dummy"


class AIClinicalAssistantConfig(BaseSettings):
    """Configuration for the AI Clinical Assistant module.

    Values are read from environment variables and, if present, a
    ``.env`` file. All values are validated on load; invalid
    configuration raises :class:`ConfigurationError` rather than a
    generic exception.

    Attributes:
        provider: Name of the LLM provider to use. One of ``"dummy"``,
            ``"gemini"``, or ``"openai"``.
        gemini_api_key: API key for the Gemini provider, if configured.
        openai_api_key: API key for the OpenAI provider, if configured.
        gemini_model: Model name to use with the Gemini provider.
        openai_model: Model name to use with the OpenAI provider.
        temperature: Default sampling temperature for response
            generation.
        max_tokens: Default maximum tokens for generated responses.
        enable_memory: Whether to maintain conversation memory.
        enable_context: Whether to use clinical context in responses.
    """

    provider: str = Field(
        default=DEFAULT_PROVIDER_NAME,
        description="Name of the LLM provider to use: 'dummy', 'gemini', or 'openai'.",
    )
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    openai_api_key: str | None = Field(
        default=None,
        description="API key for the OpenAI provider.",
    )
    gemini_model: str = Field(
        default=DEFAULT_GEMINI_MODEL,
        description="Model name to use with the Gemini provider.",
    )
    openai_model: str = Field(
        default=DEFAULT_OPENAI_MODEL,
        description="Model name to use with the OpenAI provider.",
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        description="Default sampling temperature for response generation.",
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        description="Default maximum tokens for generated responses.",
    )
    enable_memory: bool = Field(
        default=True,
        description="Whether to maintain conversation memory.",
    )
    enable_context: bool = Field(
        default=True,
        description="Whether to use clinical context in responses.",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        """Validate that the configured provider is supported.

        Args:
            value: The raw provider name read from configuration.

        Returns:
            str: The normalized (lowercase, stripped) provider name.

        Raises:
            ConfigurationError: If ``value`` is not one of
                :data:`SUPPORTED_PROVIDERS`.
        """
        normalized_value = value.strip().lower()
        if normalized_value not in SUPPORTED_PROVIDERS:
            raise ConfigurationError(
                f"Unsupported provider {value!r}. Supported providers: "
                f"{sorted(SUPPORTED_PROVIDERS)}."
            )
        return normalized_value

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float) -> float:
        """Validate that the temperature is within the allowed range.

        Args:
            value: The raw temperature read from configuration.

        Returns:
            float: The validated temperature.

        Raises:
            ConfigurationError: If ``value`` is outside
                ``[MIN_TEMPERATURE, MAX_TEMPERATURE]``.
        """
        if not MIN_TEMPERATURE <= value <= MAX_TEMPERATURE:
            raise ConfigurationError(
                f"temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}, "
                f"got {value}."
            )
        return value

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, value: int) -> int:
        """Validate that max_tokens is within the allowed range.

        Args:
            value: The raw max_tokens value read from configuration.

        Returns:
            int: The validated max_tokens value.

        Raises:
            ConfigurationError: If ``value`` is outside
                ``[MIN_MAX_TOKENS, MAX_MAX_TOKENS]``.
        """
        if not MIN_MAX_TOKENS <= value <= MAX_MAX_TOKENS:
            raise ConfigurationError(
                f"max_tokens must be between {MIN_MAX_TOKENS} and {MAX_MAX_TOKENS}, "
                f"got {value}."
            )
        return value

    def get_provider_name(self) -> str:
        """Return the name of the currently configured provider.

        Returns:
            str: The configured provider name.
        """
        return self.provider

    def get_model_name(self) -> str:
        """Return the model name associated with the configured provider.

        Returns:
            str: The Gemini or OpenAI model name if one of those
            providers is configured, otherwise
            :data:`DUMMY_PROVIDER_MODEL_NAME`.
        """
        if self.provider == "gemini":
            return self.gemini_model
        if self.provider == "openai":
            return self.openai_model
        return DUMMY_PROVIDER_MODEL_NAME

    def provider_available(self) -> bool:
        """Check whether the configured provider has the credentials it needs.

        The dummy provider never requires credentials. The Gemini and
        OpenAI providers require their respective API key to be set.

        Returns:
            bool: ``True`` if the configured provider is ready to use,
            ``False`` otherwise.
        """
        if self.provider == "dummy":
            return True
        if self.provider == "gemini":
            return bool(self.gemini_api_key)
        if self.provider == "openai":
            return bool(self.openai_api_key)
        return False

    def model_post_init(self, __context: Any) -> None:
        """Log a configuration summary once settings have been loaded.

        Never logs API key values.

        Args:
            __context: Pydantic-provided post-init context (unused).
        """
        logger.info(
            "AI Clinical Assistant configured: provider=%s, model=%s, "
            "enable_memory=%s, enable_context=%s.",
            self.provider,
            self.get_model_name(),
            self.enable_memory,
            self.enable_context,
        )
        if not self.provider_available():
            logger.warning(
                "Configured provider '%s' is missing required credentials.",
                self.provider,
            )


settings = AIClinicalAssistantConfig()