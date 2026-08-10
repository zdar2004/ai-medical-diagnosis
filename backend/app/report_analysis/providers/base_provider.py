"""Abstract provider interface for the AI Clinical Assistant module.

This module defines :class:`BaseProvider`, the abstract interface that
every LLM provider (Dummy, Gemini, OpenAI) must implement. It also
provides shared, provider-agnostic prompt validation logic so that
input validation is not duplicated across every concrete provider.
"""

from abc import ABC, abstractmethod

from app.ai_clinical_assistant.exceptions import InvalidUserInputError
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class BaseProvider(ABC):
    """Abstract base class defining the interface for every LLM provider.

    Every concrete provider (for example ``DummyProvider``,
    ``GeminiProvider``, or ``OpenAIProvider``) must implement
    :meth:`generate`, :meth:`provider_name`, and :meth:`is_available`.
    This base class contributes exactly one piece of shared behavior,
    :meth:`validate_prompt`, so that prompt validation is written once
    and reused by every provider rather than duplicated in each one.

    This class contains no provider-specific logic: it never calls an
    external API, never builds prompts, and never stores conversation
    state.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt.

        Concrete implementations are responsible for calling
        :meth:`validate_prompt` on ``prompt`` before using it, and for
        translating any provider-specific failures into the appropriate
        exception from ``exceptions.py``.

        Args:
            prompt: The complete prompt text to send to the provider.

        Returns:
            str: The generated response text.
        """
        raise NotImplementedError

    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical name of this provider.

        Returns:
            str: The provider's name (for example ``"dummy"``,
            ``"gemini"``, or ``"openai"``).
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether this provider is currently usable.

        Returns:
            bool: ``True`` if the provider is configured and ready to
            generate responses, ``False`` otherwise.
        """
        raise NotImplementedError

    def validate_prompt(self, prompt: str) -> None:
        """Validate that a prompt is usable before sending it to a provider.

        Shared by every concrete provider so that prompt validation is
        implemented exactly once. Prompt content is never logged.

        Args:
            prompt: The prompt text to validate.

        Raises:
            InvalidUserInputError: If ``prompt`` is ``None``, empty, or
                whitespace-only.
        """
        if prompt is None or not prompt.strip():
            logger.warning("Prompt validation failed: prompt was empty or whitespace-only.")
            raise InvalidUserInputError("Prompt must not be empty.")