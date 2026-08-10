"""
Gemini-backed provider for the AI Clinical Assistant module.

This module implements GeminiProvider using Google's Gemini API.

Configuration is read from:
    app.ai_clinical_assistant.config.settings

The Gemini client is initialized lazily and reused for subsequent
generation requests.
"""

from __future__ import annotations

from typing import Any

from google import genai

from app.ai_clinical_assistant.config import settings
from app.ai_clinical_assistant.exceptions import (
    ProviderError,
    ProviderUnavailableError,
)
from app.report_analysis.providers.base_provider import BaseProvider
from app.risk_assessment.utils.logging_utils import get_logger


logger = get_logger(__name__)

GEMINI_PROVIDER_NAME: str = "gemini"


class GeminiProvider(BaseProvider):
    """
    LLM provider backed by Google's Gemini API.

    The Gemini client is initialized lazily on the first generation
    request and then reused.
    """

    def __init__(self) -> None:
        """
        Initialize the Gemini provider.

        No API call is made during initialization.
        """
        self._client: genai.Client | None = None

        logger.info(
            "GeminiProvider initialized."
        )

    # ---------------------------------------------------------
    # Provider information
    # ---------------------------------------------------------

    def provider_name(self) -> str:
        """
        Return the canonical provider name.
        """

        return GEMINI_PROVIDER_NAME

    # ---------------------------------------------------------
    # Availability
    # ---------------------------------------------------------

    def is_available(self) -> bool:
        """
        Check whether Gemini is configured.

        Returns:
            True when both API key and model name are configured.
        """

        return bool(
            settings.gemini_api_key
        ) and bool(
            settings.gemini_model
        )

    # ---------------------------------------------------------
    # Generate
    # ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response using Gemini.

        Args:
            prompt:
                Complete prompt sent to Gemini.

        Returns:
            Generated response text.

        Raises:
            ProviderUnavailableError:
                Gemini is not configured.

            ProviderError:
                Gemini request fails or returns empty output.
        """

        self.validate_prompt(prompt)

        client = self._get_client()

        try:
            logger.info(
                "Generating Gemini response using model '%s'.",
                settings.gemini_model,
            )

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )

        except Exception as error:
            logger.exception(
                "Gemini API call failed."
            )

            raise ProviderError(
                "Gemini API call failed.",
                provider_name=GEMINI_PROVIDER_NAME,
            ) from error

        generated_text = getattr(
            response,
            "text",
            None,
        )

        if not generated_text or not generated_text.strip():
            logger.error(
                "Gemini returned an empty response."
            )

            raise ProviderError(
                "Gemini returned an empty response.",
                provider_name=GEMINI_PROVIDER_NAME,
            )

        logger.info(
            "Gemini response generated successfully."
        )

        return generated_text.strip()

    # ---------------------------------------------------------
    # Client initialization
    # ---------------------------------------------------------

    def _get_client(self) -> genai.Client:
        """
        Lazily initialize and return the Gemini client.

        Returns:
            Initialized Gemini client.

        Raises:
            ProviderUnavailableError:
                API key or model configuration is missing.

            ProviderError:
                Gemini client initialization fails.
        """

        if self._client is not None:
            return self._client

        if not self.is_available():
            logger.error(
                "Gemini provider unavailable: "
                "API key or model name is missing."
            )

            raise ProviderUnavailableError(
                "Gemini provider is not available: "
                "missing API key or model name.",
                provider_name=GEMINI_PROVIDER_NAME,
            )

        try:
            self._client = genai.Client(
                api_key=settings.gemini_api_key
            )

            logger.info(
                "Gemini client initialized successfully."
            )

            return self._client

        except Exception as error:
            logger.exception(
                "Failed to initialize Gemini client."
            )

            raise ProviderError(
                "Failed to initialize Gemini client.",
                provider_name=GEMINI_PROVIDER_NAME,
            ) from error

