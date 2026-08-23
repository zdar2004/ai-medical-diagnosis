"""
Service-layer orchestration for the AI Clinical Assistant module.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.ai_clinical_assistant.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationContext,
    ConversationHistory,
)
from app.ai_clinical_assistant.attachment_processor import (
    Attachment,
    AttachmentProcessor,
)
from app.ai_clinical_assistant.config import (
    AIClinicalAssistantConfig,
    settings,
)
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
    AttachmentInfo,
    ChatRequest,
    ChatResponse,
    ConversationContext,
    ConversationHistory,
)
from app.risk_assessment.utils.logging_utils import get_logger


logger = get_logger(__name__)


class AssistantService:
    """Orchestrate a complete AI Clinical Assistant chat turn."""

    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        config: AIClinicalAssistantConfig | None = None,
        memory: ConversationMemory | None = None,
    ) -> None:

        self._config = (
            config
            if config is not None
            else settings
        )

        self._memory = (
            memory
            if memory is not None
            else ConversationMemory(database)
        )

        self._context_builder = ContextBuilder(
            self._memory
        )

        self._prompt_builder = PromptBuilder()

        self._response_validator = ResponseValidator()

        self._provider_factory = ProviderFactory()

        self._attachment_processor = AttachmentProcessor()

        logger.info(
            "AssistantService initialized with provider='%s'.",
            self._config.get_provider_name(),
        )

    # =========================================================
    # Chat
    # =========================================================

    async def chat(
        self,
        request: ChatRequest,
        files: list[UploadFile] | None = None,
    ) -> ChatResponse:

        await self._validate_request(request)

        conversation_id = await self._resolve_conversation_id(
            request.conversation_id
        )

        clinical_context = request.context

        if isinstance(clinical_context, dict):
            clinical_context = ConversationContext(
                **clinical_context
            )

        # -----------------------------------------------------
        # Process attachments
        # -----------------------------------------------------

        attachments = await self._attachment_processor.process(
            files
        )

        # -----------------------------------------------------
        # Build structured clinical context
        # -----------------------------------------------------

        if self._config.enable_context:

            structured_context = (
                await self._context_builder.build_context(
                    conversation_id,
                    clinical_context,
                )
            )

        else:
            structured_context = {}

        # -----------------------------------------------------
        # Build prompt
        # -----------------------------------------------------

        prompt = self._prompt_builder.build_complete_prompt(
            request.message,
            structured_context,
        )

        # -----------------------------------------------------
        # Get provider
        # -----------------------------------------------------

        provider = self._provider_factory.get_provider(
            self._config.get_provider_name()
        )

        # -----------------------------------------------------
        # Store user message
        # -----------------------------------------------------

        user_content = request.message

        if attachments:

            attachment_names = ", ".join(
                attachment.filename
                for attachment in attachments
            )

            user_content = (
                f"{request.message}\n\n"
                f"[Attachments: {attachment_names}]"
            )

        await self._memory.add_user_message(
            conversation_id,
            user_content,
        )

        # -----------------------------------------------------
        # Generate response
        #
        # GeminiProvider.generate() is synchronous.
        # Run it in a worker thread so FastAPI's event loop
        # is not blocked during the external API call.
        # -----------------------------------------------------

        raw_response = await asyncio.to_thread(
            provider.generate,
            prompt,
            attachments,
        )

        # -----------------------------------------------------
        # Validate response
        # -----------------------------------------------------

        validated_response = await self._validate_response(
            raw_response
        )

        # -----------------------------------------------------
        # Store assistant response
        # -----------------------------------------------------

        await self._memory.add_assistant_message(
            conversation_id,
            validated_response,
        )

        logger.info(
            "Chat turn completed for conversation '%s' "
            "using provider '%s'.",
            conversation_id,
            provider.provider_name(),
        )

        attachment_info = [
            AttachmentInfo(
                filename=attachment.filename,
                content_type=attachment.content_type,
                size=len(attachment.data),
            )
            for attachment in attachments
        ]

        return ChatResponse(
            response=validated_response,
            provider=provider.provider_name(),
            conversation_id=conversation_id,
            attachments=attachment_info,
        )

    # =========================================================
    # Conversation
    # =========================================================

    async def create_conversation(self) -> str:
        return await self._memory.create_conversation()

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> ConversationHistory:

        return await self._memory.get_history(
            conversation_id
        )

    async def delete_conversation(
        self,
        conversation_id: str,
    ) -> None:

        await self._memory.delete_conversation(
            conversation_id
        )

    async def clear_conversation(
        self,
        conversation_id: str,
    ) -> None:

        await self._memory.clear_conversation(
            conversation_id
        )

    async def conversation_exists(
        self,
        conversation_id: str,
    ) -> bool:

        return await self._memory.conversation_exists(
            conversation_id
        )

    async def list_conversations(self) -> list[str]:

        return await self._memory.list_conversations()

    async def conversation_count(self) -> int:

        return await self._memory.conversation_count()

    # =========================================================
    # Health
    # =========================================================

    async def health(self) -> dict[str, Any]:

        provider = self._provider_factory.get_provider(
            self._config.get_provider_name()
        )

        return {
            "provider": self._config.get_provider_name(),
            "provider_available": provider.is_available(),
            "model": self._config.get_model_name(),
            "memory_enabled": self._config.enable_memory,
            "context_enabled": self._config.enable_context,
            "conversation_count": (
                await self._memory.conversation_count()
            ),
        }

    # =========================================================
    # Validation
    # =========================================================

    async def _validate_request(
        self,
        request: ChatRequest,
    ) -> None:

        if (
            not request.message
            or not request.message.strip()
        ):
            raise InvalidUserInputError(
                "Chat request message must not be empty."
            )

    async def _resolve_conversation_id(
        self,
        conversation_id: str | None,
    ) -> str:

        if conversation_id is None:

            new_conversation_id = (
                await self._memory.create_conversation()
            )

            logger.info(
                "New conversation created for incoming "
                "chat request."
            )

            return new_conversation_id

        if not await self._memory.conversation_exists(
            conversation_id
        ):

            raise ConversationMemoryError(
                f"Conversation not found: {conversation_id}",
                conversation_id=conversation_id,
            )

        return conversation_id

    async def _validate_response(
        self,
        raw_response: str,
    ) -> str:

        try:

            return self._response_validator.validate(
                raw_response
            )

        except ValueError as error:

            raise ResponseValidationError(
                str(error)
            ) from error