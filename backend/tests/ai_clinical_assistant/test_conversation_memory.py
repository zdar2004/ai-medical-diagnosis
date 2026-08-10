import pytest

from app.ai_clinical_assistant.conversation_memory import (
    ConversationMemory,
    MAX_STORED_MESSAGES,
)
from app.ai_clinical_assistant.exceptions import (
    ConversationMemoryError,
    InvalidUserInputError,
)


def test_create_conversation():
    memory = ConversationMemory()

    conversation_id = memory.create_conversation()

    assert isinstance(conversation_id, str)
    assert memory.conversation_exists(conversation_id)
    assert memory.conversation_count() == 1


def test_create_multiple_conversations():
    memory = ConversationMemory()

    id1 = memory.create_conversation()
    id2 = memory.create_conversation()

    assert id1 != id2
    assert memory.conversation_count() == 2


def test_add_user_message():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "Hello")

    history = memory.get_history(conversation_id)

    assert len(history.messages) == 1
    assert history.messages[0].role == "user"
    assert history.messages[0].content == "Hello"


def test_add_assistant_message():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    memory.add_assistant_message(conversation_id, "Hi there")

    history = memory.get_history(conversation_id)

    assert history.messages[0].role == "assistant"
    assert history.messages[0].content == "Hi there"


def test_add_system_message():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    memory.add_system_message(conversation_id, "System Prompt")

    history = memory.get_history(conversation_id)

    assert history.messages[0].role == "system"
    assert history.messages[0].content == "System Prompt"


def test_invalid_empty_message():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    with pytest.raises(InvalidUserInputError):
        memory.add_user_message(conversation_id, "")


def test_invalid_whitespace_message():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    with pytest.raises(InvalidUserInputError):
        memory.add_user_message(conversation_id, "    ")


def test_get_history():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "Question")
    memory.add_assistant_message(conversation_id, "Answer")

    history = memory.get_history(conversation_id)

    assert len(history.messages) == 2
    assert history.messages[0].role == "user"
    assert history.messages[1].role == "assistant"


def test_get_recent_messages():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    for i in range(5):
        memory.add_user_message(conversation_id, f"Message {i}")

    recent = memory.get_recent_messages(conversation_id, limit=2)

    assert len(recent) == 2
    assert recent[0].content == "Message 3"
    assert recent[1].content == "Message 4"


def test_recent_messages_zero_limit():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "Hello")

    assert memory.get_recent_messages(conversation_id, 0) == []


def test_clear_conversation():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "Hello")
    memory.add_assistant_message(conversation_id, "Hi")

    memory.clear_conversation(conversation_id)

    history = memory.get_history(conversation_id)

    assert len(history.messages) == 0


def test_delete_conversation():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    memory.delete_conversation(conversation_id)

    assert not memory.conversation_exists(conversation_id)

    with pytest.raises(ConversationMemoryError):
        memory.get_history(conversation_id)


def test_list_conversations():
    memory = ConversationMemory()

    id1 = memory.create_conversation()
    id2 = memory.create_conversation()

    conversations = memory.list_conversations()

    assert id1 in conversations
    assert id2 in conversations
    assert len(conversations) == 2


def test_conversation_not_found():
    memory = ConversationMemory()

    with pytest.raises(ConversationMemoryError):
        memory.get_history("invalid-id")


def test_message_limit_enforced():
    memory = ConversationMemory()
    conversation_id = memory.create_conversation()

    for i in range(MAX_STORED_MESSAGES + 10):
        memory.add_user_message(conversation_id, f"Message {i}")

    history = memory.get_history(conversation_id)

    assert len(history.messages) == MAX_STORED_MESSAGES

    assert history.messages[0].content == "Message 10"
    assert history.messages[-1].content == f"Message {MAX_STORED_MESSAGES + 9}"


def test_conversation_count():
    memory = ConversationMemory()

    assert memory.conversation_count() == 0

    memory.create_conversation()

    assert memory.conversation_count() == 1