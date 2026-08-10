"""Service-layer orchestration for the AI Clinical Assistant module.

This module implements :class:`AssistantService`, the single component
responsible for orchestrating a full chat turn: resolving the
conversation, storing the user message, building structured clinical
context, constructing the prompt, invoking the configured LLM provider,
validating the response, storing the assistant message, and returning a
:class:`~app.ai_clinical_assistant.schemas.ChatResponse`.

``AssistantService`` contains no business logic of its own. It never
builds prompts, builds context, validates responses, manages
conversation storage directly, or calls a provider SDK directly; those
responsibilities belong entirely to :class:`ContextBuilder`,
:class:`PromptBuilder`, :class:`ResponseValidator`,
:class:`ConversationMemory`, and the concrete provider classes obtained
through :class:`ProviderFactory`.
"""

from typing import Any

from app.ai_clinical_assistant.config import AIClinicalAssistantConfig, settings
from app.ai_clinical_assistant.context_builder import ContextBuilder
from app.ai_clinical_assistant.conversation_memory import ConversationMemory
from app.ai_clinical_assistant.exceptions import (
    ConversationMemoryError,
    InvalidUserInputError,
    ResponseValidationError,
)
from app.ai_clinical_assistant.prompt_builder import PromptBuilder
from app.ai_clinical_assistant.provider_factory import ProviderFactory
from app.ai_clinical_assistant.response_validator import ResponseValidator
from app.ai_clinical_assistant.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationContext,
    ConversationHistory,
)
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class AssistantService:
    """Orchestrate a full AI Clinical Assistant chat turn.

    This class coordinates :class:`ConversationMemory`,
    :class:`ContextBuilder`, :class:`PromptBuilder`,
    :class:`ProviderFactory`, and :class:`ResponseValidator` to fulfill
    a :class:`ChatRequest`. It contains no prompt-building, context-
    building, response-validation, or provider-calling logic of its
    own; each of those responsibilities is delegated to its owning
    component.

    Attributes:
        _config: The active :class:`AIClinicalAssistantConfig`.
        _memory: The :class:`ConversationMemory` used to store and
            retrieve conversations.
        _context_builder: The :class:`ContextBuilder` used to build
            structured clinical context.
        _prompt_builder: The :class:`PromptBuilder` used to construct
            prompts.
        _response_validator: The :class:`ResponseValidator` used to
            sanitize provider responses.
        _provider_factory: The :class:`ProviderFactory` used to obtain
            the configured LLM provider.
    """

    def __init__(
        self,
        config: AIClinicalAssistantConfig | None = None,
        memory: ConversationMemory | None = None,
    ) -> None:
        """Initialize the AssistantService.

        Args:
            config: The configuration to use. If ``None``, the shared
                :data:`app.ai_clinical_assistant.config.settings`
                singleton is used.
            memory: The conversation memory to use. If ``None``, a new
                :class:`ConversationMemory` instance is created.
        """
        self._config: AIClinicalAssistantConfig = config if config is not None else settings
        self._memory: ConversationMemory = memory if memory is not None else ConversationMemory()
        self._context_builder: ContextBuilder = ContextBuilder(self._memory)
        self._prompt_builder: PromptBuilder = PromptBuilder()
        self._response_validator: ResponseValidator = ResponseValidator()
        self._provider_factory: ProviderFactory = ProviderFactory()

        logger.info(
            "AssistantService initialized with provider='%s'.",
            self._config.get_provider_name(),
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return the assistant's response.

        Workflow: validate the request, resolve (or create) the
        conversation, store the user message, build structured clinical
        context, build the prompt, generate a response from the
        configured provider, validate that response, store the
        assistant message, and return a :class:`ChatResponse`.

        Args:
            request: The incoming chat request.

        Returns:
            ChatResponse: The validated assistant response.

        Raises:
            InvalidUserInputError: If the request message is empty or
                whitespace-only.
            ConversationMemoryError: If ``request.conversation_id`` is
                provided but does not correspond to an existing
                conversation.
            ProviderError: If the configured provider fails to generate
                a response.
            ResponseValidationError: If the provider's response fails
                validation.
        """
        self._validate_request(request)

        conversation_id = self._resolve_conversation_id(request.conversation_id)
        self._memory.add_user_message(conversation_id, request.message)

        conversation_history = (
            self._memory.get_recent_messages(conversation_id)
            if self._config.enable_memory
            else []
        )

        clinical_context = request.context

        if isinstance(clinical_context, dict):
            clinical_context = ConversationContext(**clinical_context)

        structured_context = (
            self._context_builder.build_context(
                conversation_id,
                clinical_context,
            )
            if self._config.enable_context
            else {}
        )

        prompt = self._prompt_builder.build_complete_prompt(request.message, structured_context)

        provider = self._provider_factory.get_provider(self._config.get_provider_name())
        raw_response = provider.generate(prompt)

        validated_response = self._validate_response(raw_response)

        self._memory.add_assistant_message(conversation_id, validated_response)

        logger.info(
            "Chat turn completed for conversation '%s' using provider '%s'.",
            conversation_id,
            provider.provider_name(),
        )

        return ChatResponse(
            response=validated_response,
            provider=provider.provider_name(),
            conversation_id=conversation_id,
        )

    def create_conversation(self) -> str:
        """Create a new, empty conversation.

        Returns:
            str: The newly created conversation id.
        """
        return self._memory.create_conversation()

    def get_conversation(self, conversation_id: str) -> ConversationHistory:
        """Retrieve the full history of a conversation.

        Args:
            conversation_id: The id of the conversation to retrieve.

        Returns:
            ConversationHistory: The complete stored conversation.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        return self._memory.get_history(conversation_id)

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation entirely.

        Args:
            conversation_id: The id of the conversation to delete.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        self._memory.delete_conversation(conversation_id)

    def clear_conversation(self, conversation_id: str) -> None:
        """Remove every message from a conversation, keeping its id.

        Args:
            conversation_id: The id of the conversation to clear.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        self._memory.clear_conversation(conversation_id)

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check whether a conversation exists.

        Args:
            conversation_id: The conversation id to check.

        Returns:
            bool: ``True`` if the conversation exists, ``False``
            otherwise.
        """
        return self._memory.conversation_exists(conversation_id)

    def list_conversations(self) -> list[str]:
        """List the ids of every stored conversation.

        Returns:
            list[str]: All currently stored conversation ids.
        """
        return self._memory.list_conversations()

    def conversation_count(self) -> int:
        """Count how many conversations are currently stored.

        Returns:
            int: The total number of stored conversations.
        """
        return self._memory.conversation_count()

    def health(self) -> dict[str, Any]:
        """Report the current operational status of the assistant.

        Returns:
            dict[str, Any]: A dictionary with keys ``"provider"``,
            ``"provider_available"``, ``"model"``, ``"memory_enabled"``,
            ``"context_enabled"``, and ``"conversation_count"``. Never
            includes API keys or other secrets.
        """
        provider = self._provider_factory.get_provider(self._config.get_provider_name())

        return {
            "provider": self._config.get_provider_name(),
            "provider_available": provider.is_available(),
            "model": self._config.get_model_name(),
            "memory_enabled": self._config.enable_memory,
            "context_enabled": self._config.enable_context,
            "conversation_count": self._memory.conversation_count(),
        }

    def _validate_request(self, request: ChatRequest) -> None:
        """Validate a chat request before processing it.

        Args:
            request: The chat request to validate.

        Raises:
            InvalidUserInputError: If ``request.message`` is empty or
                whitespace-only.
        """
        if not request.message or not request.message.strip():
            raise InvalidUserInputError("Chat request message must not be empty.")

    def _resolve_conversation_id(self, conversation_id: str | None) -> str:
        """Resolve the conversation to use for a chat request.

        Creates a new conversation if none was specified, otherwise
        verifies that the specified conversation already exists.

        Args:
            conversation_id: The conversation id supplied in the
                request, or ``None`` to start a new conversation.

        Returns:
            str: The resolved conversation id.

        Raises:
            ConversationMemoryError: If ``conversation_id`` is provided
                but does not correspond to an existing conversation.
        """
        if conversation_id is None:
            new_conversation_id = self._memory.create_conversation()
            logger.info("New conversation created for incoming chat request.")
            return new_conversation_id

        if not self._memory.conversation_exists(conversation_id):
            raise ConversationMemoryError(
                f"Conversation not found: {conversation_id}",
                conversation_id=conversation_id,
            )

        return conversation_id

    def _validate_response(self, raw_response: str) -> str:
        """Validate and sanitize a raw provider response.

        Args:
            raw_response: The unvalidated response text returned by the
                LLM provider.

        Returns:
            str: The validated, sanitized response text.

        Raises:
            ResponseValidationError: If the response fails validation.
        """
        try:
            return self._response_validator.validate(raw_response)
        except ValueError as error:
            raise ResponseValidationError(str(error)) from error