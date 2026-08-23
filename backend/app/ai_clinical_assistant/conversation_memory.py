"""MongoDB-backed conversation storage for the AI Clinical Assistant."""

import uuid
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai_clinical_assistant.exceptions import (
    ConversationMemoryError,
    InvalidUserInputError,
)
from app.ai_clinical_assistant.schemas import (
    ChatMessage,
    ConversationHistory,
)
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

MAX_STORED_MESSAGES: int = 100


class ConversationMemory:
    """Store and retrieve clinical assistant conversations in MongoDB."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize MongoDB-backed conversation storage."""
        self._collection = database["chat_sessions"]

        logger.info("MongoDB ConversationMemory initialized.")

    async def create_conversation(self) -> str:
        """Create and store a new empty conversation."""
        conversation_id = uuid.uuid4().hex
        now = datetime.now(UTC)

        document = {
            "_id": conversation_id,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }

        try:
            await self._collection.insert_one(document)

        except Exception as error:
            logger.exception("Failed to create conversation.")
            raise ConversationMemoryError(
                "Failed to create conversation."
            ) from error

        logger.info("Conversation created: %s", conversation_id)

        return conversation_id

    async def conversation_exists(self, conversation_id: str) -> bool:
        """Check whether a conversation exists."""
        document = await self._collection.find_one(
            {"_id": conversation_id},
            {"_id": 1},
        )

        return document is not None

    async def add_user_message(
        self,
        conversation_id: str,
        message: str,
    ) -> None:
        """Append a user message."""
        await self._append_message(
            conversation_id,
            role="user",
            message=message,
        )

    async def add_assistant_message(
        self,
        conversation_id: str,
        message: str,
    ) -> None:
        """Append an assistant message."""
        await self._append_message(
            conversation_id,
            role="assistant",
            message=message,
        )

    async def add_system_message(
        self,
        conversation_id: str,
        message: str,
    ) -> None:
        """Append a system message."""
        await self._append_message(
            conversation_id,
            role="system",
            message=message,
        )

    async def get_history(
        self,
        conversation_id: str,
    ) -> ConversationHistory:
        """Retrieve the complete conversation history."""

        document = await self._get_conversation_or_raise(
            conversation_id
        )

        return ConversationHistory(
            conversation_id=document["_id"],
            messages=[
                ChatMessage(**message)
                for message in document.get("messages", [])
            ],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    async def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> list[ChatMessage]:
        """Retrieve recent conversation messages."""

        if limit <= 0:
            return []

        document = await self._get_conversation_or_raise(
            conversation_id
        )

        messages = document.get("messages", [])

        recent_messages = messages[-limit:]

        return [
            ChatMessage(**message)
            for message in recent_messages
        ]

    async def clear_conversation(
        self,
        conversation_id: str,
    ) -> None:
        """Remove all messages while keeping the conversation."""

        result = await self._collection.update_one(
            {"_id": conversation_id},
            {
                "$set": {
                    "messages": [],
                    "updated_at": datetime.now(UTC),
                }
            },
        )

        if result.matched_count == 0:
            raise ConversationMemoryError(
                f"Conversation not found: {conversation_id}",
                conversation_id=conversation_id,
            )

        logger.info("Conversation cleared: %s", conversation_id)

    async def delete_conversation(
        self,
        conversation_id: str,
    ) -> None:
        """Delete a conversation completely."""

        result = await self._collection.delete_one(
            {"_id": conversation_id}
        )

        if result.deleted_count == 0:
            raise ConversationMemoryError(
                f"Conversation not found: {conversation_id}",
                conversation_id=conversation_id,
            )

        logger.info("Conversation deleted: %s", conversation_id)

    async def list_conversations(self) -> list[str]:
        """Return all conversation IDs."""

        cursor = self._collection.find(
            {},
            {"_id": 1},
        )

        conversation_ids = []

        async for document in cursor:
            conversation_ids.append(document["_id"])

        return conversation_ids

    async def conversation_count(self) -> int:
        """Return total number of conversations."""

        return await self._collection.count_documents({})

    async def _get_conversation_or_raise(
        self,
        conversation_id: str,
    ) -> dict:
        """Retrieve a conversation or raise an error."""

        document = await self._collection.find_one(
            {"_id": conversation_id}
        )

        if document is None:
            raise ConversationMemoryError(
                f"Conversation not found: {conversation_id}",
                conversation_id=conversation_id,
            )

        return document

    @staticmethod
    def _validate_message_content(message: str) -> None:
        """Validate message content."""

        if not message or not message.strip():
            raise InvalidUserInputError(
                "Message content must not be empty."
            )

    async def _append_message(
        self,
        conversation_id: str,
        role: str,
        message: str,
    ) -> None:
        """Validate and append a message."""

        self._validate_message_content(message)

        chat_message = ChatMessage(
            role=role,
            content=message,
        )

        message_data = chat_message.model_dump()

        result = await self._collection.update_one(
            {"_id": conversation_id},
            {
                "$push": {
                    "messages": {
                        "$each": [message_data],
                        "$slice": -MAX_STORED_MESSAGES,
                    }
                },
                "$set": {
                    "updated_at": datetime.now(UTC),
                },
            },
        )

        if result.matched_count == 0:
            raise ConversationMemoryError(
                f"Conversation not found: {conversation_id}",
                conversation_id=conversation_id,
            )

        logger.info(
            "Message added to conversation '%s' with role '%s'.",
            conversation_id,
            role,
        )