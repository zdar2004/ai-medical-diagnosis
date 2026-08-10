import pytest

from app.ai_clinical_assistant.assistant_service import AssistantService
from app.ai_clinical_assistant.schemas import ChatRequest
from app.ai_clinical_assistant.exceptions import InvalidUserInputError


def test_service_initialization():
    service = AssistantService()

    assert service is not None


def test_create_conversation():

    service = AssistantService()

    conversation_id = service.create_conversation()

    assert conversation_id is not None
    assert service.conversation_exists(conversation_id)


def test_chat_empty_message():

    service = AssistantService()

    request = ChatRequest(
        message=" "
    )

    with pytest.raises(InvalidUserInputError):
        service.chat(request)


def test_create_and_get_conversation():

    service = AssistantService()

    conversation_id = service.create_conversation()

    history = service.get_conversation(conversation_id)

    assert history.conversation_id == conversation_id
    assert len(history.messages) == 0


def test_clear_conversation():

    service = AssistantService()

    conversation_id = service.create_conversation()

    service._memory.add_user_message(
        conversation_id,
        "I have fever"
    )

    service.clear_conversation(conversation_id)

    history = service.get_conversation(conversation_id)

    assert len(history.messages) == 0


def test_delete_conversation():

    service = AssistantService()

    conversation_id = service.create_conversation()

    service.delete_conversation(conversation_id)

    assert not service.conversation_exists(conversation_id)


def test_list_conversations():

    service = AssistantService()

    id1 = service.create_conversation()
    id2 = service.create_conversation()

    conversations = service.list_conversations()

    assert id1 in conversations
    assert id2 in conversations


def test_conversation_count():

    service = AssistantService()

    service.create_conversation()
    service.create_conversation()

    assert service.conversation_count() == 2


def test_health():

    service = AssistantService()

    health = service.health()

    assert "provider" in health
    assert "provider_available" in health
    assert "conversation_count" in health


def test_complete_chat_flow():

    service = AssistantService()

    request = ChatRequest(
        message="I have high blood pressure"
    )

    response = service.chat(request)

    assert response.response is not None
    assert response.provider is not None
    assert response.conversation_id is not None