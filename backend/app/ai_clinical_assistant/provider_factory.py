"""
Provider factory for the AI Clinical Assistant module.

This module implements ProviderFactory, responsible only for creating
and returning LLM provider instances.
"""

from typing import Optional

from app.ai_clinical_assistant.config import settings
from app.ai_clinical_assistant.exceptions import ConfigurationError
from app.report_analysis.providers.base_provider import BaseProvider
from app.report_analysis.providers.dummy_provider import DummyProvider
from app.report_analysis.providers.gemini_provider import GeminiProvider
from app.report_analysis.providers.openai_provider import OpenAIProvider
from app.risk_assessment.utils.logging_utils import get_logger


logger = get_logger(__name__)


class ProviderFactory:
    """Factory responsible for constructing LLM providers."""

    def __init__(self) -> None:
        logger.info("ProviderFactory initialized.")

    def get_provider(
        self,
        provider_name: Optional[str] = None,
    ) -> BaseProvider:
        """
        Return the requested provider instance.

        Args:
            provider_name:
                Name of provider. If None, the configured provider
                from settings is used.

        Returns:
            BaseProvider instance.

        Raises:
            ConfigurationError:
                If the provider name is unsupported.
        """

        provider = (
            provider_name
            or settings.get_provider_name()
        ).strip().lower()

        logger.info(
            "Loading provider '%s'.",
            provider,
        )

        if provider == "dummy":
            return DummyProvider()

        if provider == "gemini":
            return GeminiProvider()

        if provider == "openai":
            return OpenAIProvider(
                api_key=settings.openai_api_key,
                model_name=settings.get_model_name(),
            )

        raise ConfigurationError(
            f"Unsupported provider '{provider}'."
        )

