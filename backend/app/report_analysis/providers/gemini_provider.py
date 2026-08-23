"""
Gemini-backed provider for the AI Clinical Assistant module.
"""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

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

    Supports text and multimodal attachments.
    """

    def __init__(self) -> None:
        self._client: genai.Client | None = None

        logger.info("GeminiProvider initialized.")

    # =========================================================
    # Provider information
    # =========================================================

    def provider_name(self) -> str:
        return GEMINI_PROVIDER_NAME

    # =========================================================
    # Availability
    # =========================================================

    def is_available(self) -> bool:
        return bool(
            settings.gemini_api_key
        ) and bool(
            settings.gemini_model
        )

    # =========================================================
    # Generate
    # =========================================================

    def generate(
        self,
        prompt: str,
        attachments: list[Any] | None = None,
    ) -> str:
        """
        Generate a Gemini response using text and optional attachments.
        """

        self.validate_prompt(prompt)

        client = self._get_client()

        contents: list[Any] = []

        # -----------------------------------------------------
        # Add multimodal attachments
        # -----------------------------------------------------

        if attachments:

            for attachment in attachments:

                logger.info(
                    "Adding attachment to Gemini request: "
                    "filename='%s', type='%s', size=%d bytes.",
                    attachment.filename,
                    attachment.content_type,
                    len(attachment.data),
                )

                # TXT files are converted into text so the model receives
                # their contents directly.
                if attachment.content_type == "text/plain":

                    try:
                        text_content = attachment.data.decode(
                            "utf-8",
                            errors="replace",
                        )

                    except Exception as error:
                        raise ProviderError(
                            f"Failed to decode text file '{attachment.filename}'.",
                            provider_name=GEMINI_PROVIDER_NAME,
                        ) from error

                    contents.append(
                        f"\n\n--- BEGIN FILE: {attachment.filename} ---\n"
                        f"{text_content}\n"
                        f"--- END FILE: {attachment.filename} ---\n"
                    )

                    continue

                # Images and PDFs are passed directly to Gemini.
                contents.append(
                    types.Part.from_bytes(
                        data=attachment.data,
                        mime_type=attachment.content_type,
                    )
                )

        # -----------------------------------------------------
        # Add user prompt last
        # -----------------------------------------------------

        contents.append(prompt)

        try:
            logger.info(
                "Generating Gemini response using model '%s' "
                "with %d attachment(s).",
                settings.gemini_model,
                len(attachments or []),
            )

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
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

    # =========================================================
    # Client initialization
    # =========================================================

    def _get_client(self) -> genai.Client:

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