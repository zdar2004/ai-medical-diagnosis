"""OpenAI-backed provider for the AI Clinical Assistant module.

This module implements :class:`OpenAIProvider`, an LLM provider backed
by the official OpenAI SDK's Chat Completions API. The API key and
model name are supplied at construction time, falling back to the
``OPENAI_API_KEY`` environment variable when no key is passed
explicitly.
"""

import os

from openai import OpenAI

from app.ai_clinical_assistant.exceptions import ConfigurationError, ProviderError
from app.report_analysis.providers.base_provider import BaseProvider
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

OPENAI_PROVIDER_NAME: str = "openai"
DEFAULT_MODEL_NAME: str = "gpt-4.1-mini"
DEFAULT_TEMPERATURE: float = 0.2
DEFAULT_MAX_TOKENS: int = 500
OPENAI_API_KEY_ENV_VAR: str = "OPENAI_API_KEY"


class OpenAIProvider(BaseProvider):
    """LLM provider backed by the OpenAI Chat Completions API.

    The API key is supplied explicitly at construction time, or read
    from the ``OPENAI_API_KEY`` environment variable if not provided.
    The underlying OpenAI client is initialized once, in the
    constructor, and reused for every subsequent call.

    Attributes:
        _client: The initialized OpenAI SDK client.
        _model_name: The model name used for chat completions.
        _api_key_present: Whether a non-empty API key was resolved at
            construction time.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        """Initialize the OpenAIProvider.

        Args:
            api_key: The OpenAI API key to use. If ``None``, the
                ``OPENAI_API_KEY`` environment variable is used instead.
            model_name: The OpenAI model to use for chat completions.
                Defaults to :data:`DEFAULT_MODEL_NAME`.

        Raises:
            ConfigurationError: If no API key is provided and
                ``OPENAI_API_KEY`` is not set in the environment.
            ProviderError: If the OpenAI client fails to initialize.
        """
        resolved_api_key = api_key if api_key is not None else os.environ.get(OPENAI_API_KEY_ENV_VAR)

        if not resolved_api_key:
            logger.error("OpenAIProvider is missing a required API key.")
            raise ConfigurationError(
                "OpenAI API key is not configured. Set the OPENAI_API_KEY "
                "environment variable or pass api_key explicitly."
            )

        self._model_name: str = model_name
        self._api_key_present: bool = True

        try:
            self._client: OpenAI = OpenAI(api_key=resolved_api_key)
        except Exception as error:
            logger.error("Failed to initialize the OpenAI client.")
            raise ProviderError(
                "Failed to initialize the OpenAI client.", provider_name=OPENAI_PROVIDER_NAME
            ) from error

        logger.info("OpenAIProvider initialized with model '%s'.", self._model_name)

    def provider_name(self) -> str:
        """Return the canonical name of this provider.

        Returns:
            str: ``"openai"``.
        """
        logger.info("OpenAI provider selected.")
        return OPENAI_PROVIDER_NAME

    def is_available(self) -> bool:
        """Check whether the OpenAI provider is configured and usable.

        Returns:
            bool: ``True`` if an API key was resolved and the client
            was initialized, ``False`` otherwise.
        """
        return self._api_key_present and self._client is not None

    def generate(self, prompt: str) -> str:
        """Generate a response from OpenAI for the given prompt.

        Args:
            prompt: The complete prompt text to send to OpenAI.

        Returns:
            str: The generated response text.

        Raises:
            InvalidUserInputError: If ``prompt`` is ``None``, empty, or
                whitespace-only.
            ProviderError: If the OpenAI API call fails or returns an
                empty response.
        """
        self.validate_prompt(prompt)

        logger.info("OpenAIProvider request started using model '%s'.", self._model_name)

        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS,
            )
        except Exception as error:
            logger.error("OpenAIProvider request failed.")
            raise ProviderError(
                "OpenAI API call failed.", provider_name=OPENAI_PROVIDER_NAME
            ) from error

        content = response.choices[0].message.content

        if content is None:
            logger.error("OpenAIProvider request failed: empty response content.")
            raise ProviderError(
                "OpenAI returned an empty response.", provider_name=OPENAI_PROVIDER_NAME
            )

        logger.info("OpenAIProvider request succeeded.")
        return content