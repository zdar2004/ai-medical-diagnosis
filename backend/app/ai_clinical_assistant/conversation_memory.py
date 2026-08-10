"""In-memory conversation storage for the AI Clinical Assistant.

This module implements :class:`ConversationMemory`, the single
component responsible for storing and retrieving conversation history.
It has exactly one responsibility: conversation storage and retrieval.

``ConversationMemory`` does not call any LLM, build prompts, validate
responses, access a database, call providers, or modify patient
context. It only manages :class:`~app.ai_clinical_assistant.schemas.ConversationHistory`
instances, keyed by conversation id, entirely in process memory.
"""

import threading
import uuid
from datetime import UTC, datetime

from app.ai_clinical_assistant.exceptions import (
    ConversationMemoryError,
    InvalidUserInputError,
)
from app.ai_clinical_assistant.schemas import ChatMessage, ConversationHistory
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)

MAX_STORED_MESSAGES: int = 100


class ConversationMemory:
    """Store and retrieve clinical assistant conversations in memory.

    This class maintains an in-process mapping of conversation id to
    :class:`ConversationHistory`. All write operations (creating,
    appending to, clearing, or deleting a conversation) are protected by
    a single lock to make the class safe for concurrent use. Each stored
    conversation is capped at :data:`MAX_STORED_MESSAGES` messages; once
    the cap is exceeded, the oldest messages are removed first (FIFO),
    and the most recently added messages are never removed.

    Attributes:
        _memory: Mapping of conversation id to its
            :class:`ConversationHistory`.
        _lock: A :class:`threading.Lock` protecting every write
            operation against concurrent access.
    """

    def __init__(self) -> None:
        """Initialize an empty, thread-safe conversation store."""
        self._memory: dict[str, ConversationHistory] = {}
        self._lock: threading.Lock = threading.Lock()
        logger.info("ConversationMemory initialized.")

    def create_conversation(self) -> str:
        """Create a new, empty conversation.

        Generates a unique conversation id and stores an empty
        :class:`ConversationHistory` under it.

        Returns:
            str: The newly generated conversation id.
        """
        conversation_id = uuid.uuid4().hex

        with self._lock:
            self._memory[conversation_id] = ConversationHistory(conversation_id=conversation_id)

        logger.info("Conversation created: %s", conversation_id)
        return conversation_id

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check whether a conversation exists.

        Args:
            conversation_id: The conversation id to check.

        Returns:
            bool: ``True`` if the conversation exists, ``False``
            otherwise.
        """
        return conversation_id in self._memory

    def add_user_message(self, conversation_id: str, message: str) -> None:
        """Append a user message to a conversation.

        Args:
            conversation_id: The id of the conversation to append to.
            message: The text content of the user's message.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
            InvalidUserInputError: If ``message`` is empty or
                whitespace-only.
        """
        self._append_message(conversation_id, role="user", message=message)

    def add_assistant_message(self, conversation_id: str, message: str) -> None:
        """Append an assistant message to a conversation.

        Args:
            conversation_id: The id of the conversation to append to.
            message: The text content of the assistant's message.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
            InvalidUserInputError: If ``message`` is empty or
                whitespace-only.
        """
        self._append_message(conversation_id, role="assistant", message=message)

    def add_system_message(self, conversation_id: str, message: str) -> None:
        """Append a system message to a conversation.

        Args:
            conversation_id: The id of the conversation to append to.
            message: The text content of the system message.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
            InvalidUserInputError: If ``message`` is empty or
                whitespace-only.
        """
        self._append_message(conversation_id, role="system", message=message)

    def get_history(self, conversation_id: str) -> ConversationHistory:
        """Retrieve the full conversation history.

        Args:
            conversation_id: The id of the conversation to retrieve.

        Returns:
            ConversationHistory: The complete stored conversation, with
            messages in chronological order.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        return self._get_conversation_or_raise(conversation_id)

    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> list[ChatMessage]:
        """Retrieve the most recent messages from a conversation.

        The stored conversation history is never modified by this
        method; a new list is returned, and chronological ordering is
        preserved.

        Args:
            conversation_id: The id of the conversation to read from.
            limit: The maximum number of most recent messages to return.
                Defaults to ``10``. Values less than or equal to zero
                return an empty list.

        Returns:
            list[ChatMessage]: Up to ``limit`` of the most recent
            messages, in chronological order.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        history = self._get_conversation_or_raise(conversation_id)

        if limit <= 0:
            return []

        return list(history.messages[-limit:])

    def clear_conversation(self, conversation_id: str) -> None:
        """Remove every message from a conversation, keeping its id.

        Args:
            conversation_id: The id of the conversation to clear.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        with self._lock:
            history = self._get_conversation_or_raise(conversation_id)
            history.messages.clear()
            history.updated_at = datetime.now(UTC)

        logger.info("Conversation cleared: %s", conversation_id)

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation entirely.

        Args:
            conversation_id: The id of the conversation to delete.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        with self._lock:
            self._get_conversation_or_raise(conversation_id)
            del self._memory[conversation_id]

        logger.info("Conversation deleted: %s", conversation_id)

    def list_conversations(self) -> list[str]:
        """List the ids of every stored conversation.

        Returns:
            list[str]: All currently stored conversation ids.
        """
        return list(self._memory.keys())

    def conversation_count(self) -> int:
        """Count how many conversations are currently stored.

        Returns:
            int: The total number of stored conversations.
        """
        return len(self._memory)

    def _get_conversation_or_raise(self, conversation_id: str) -> ConversationHistory:
        """Look up a stored conversation, raising if it does not exist.

        Args:
            conversation_id: The id of the conversation to look up.

        Returns:
            ConversationHistory: The stored conversation.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
        """
        try:
            return self._memory[conversation_id]
        except KeyError as error:
            raise ConversationMemoryError(
                f"Conversation not found: {conversation_id}",
                conversation_id=conversation_id,
            ) from error

    @staticmethod
    def _validate_message_content(message: str) -> None:
        """Validate that message content is non-empty.

        Args:
            message: The message content to validate.

        Raises:
            InvalidUserInputError: If ``message`` is ``None``, empty, or
                whitespace-only.
        """
        if not message or not message.strip():
            raise InvalidUserInputError("Message content must not be empty.")

    def _enforce_message_limit(self, history: ConversationHistory) -> None:
        """Trim the oldest messages once the storage limit is exceeded.

        Removes messages from the front of the list (FIFO) until the
        conversation holds at most :data:`MAX_STORED_MESSAGES` messages.
        The most recently added messages are never removed, and
        chronological ordering of the remaining messages is preserved.

        Args:
            history: The conversation history to trim in place.
        """
        while len(history.messages) > MAX_STORED_MESSAGES:
            history.messages.pop(0)

    def _append_message(self, conversation_id: str, role: str, message: str) -> None:
        """Validate and append a single message to a conversation.

        This shared helper is used by :meth:`add_user_message`,
        :meth:`add_assistant_message`, and :meth:`add_system_message`.
        Message content is never logged, and no protected health
        information is exposed in any log statement.

        Args:
            conversation_id: The id of the conversation to append to.
            role: The role of the message sender (``"user"``,
                ``"assistant"``, or ``"system"``).
            message: The text content of the message.

        Raises:
            ConversationMemoryError: If the conversation does not exist.
            InvalidUserInputError: If ``message`` is empty or
                whitespace-only.
        """
        self._validate_message_content(message)

        with self._lock:
            history = self._get_conversation_or_raise(conversation_id)
            history.messages.append(ChatMessage(role=role, content=message))
            history.updated_at = datetime.now(UTC)
            self._enforce_message_limit(history)

        logger.info("Message added to conversation '%s' with role '%s'.", conversation_id, role)