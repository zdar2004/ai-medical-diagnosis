"""
Unit tests for schemas.py
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.ai_clinical_assistant.schemas import (
    AssistantConfig,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationContext,
    ConversationHistory,
)


# ---------------------------------------------------------
# ChatMessage
# ---------------------------------------------------------

def test_chat_message_creation():
    msg = ChatMessage(
        role="user",
        content="Hello"
    )

    assert msg.role == "user"
    assert msg.content == "Hello"
    assert isinstance(msg.timestamp, datetime)


def test_chat_message_empty_content():
    with pytest.raises(ValidationError):
        ChatMessage(
            role="user",
            content=""
        )


# ---------------------------------------------------------
# ConversationContext
# ---------------------------------------------------------

def test_conversation_context_defaults():
    context = ConversationContext()

    assert context.medical_history == []
    assert context.current_medications == []
    assert context.allergies == []
    assert context.risk_assessment == {}
    assert context.laboratory_results == {}
    assert context.report_analysis == {}


def test_conversation_context_values():
    context = ConversationContext(
        patient_id="123",
        patient_age=45,
        patient_gender="Male",
        medical_history=["Diabetes"],
        current_medications=["Metformin"],
        allergies=["Penicillin"],
        risk_assessment={"risk": "Low"},
        laboratory_results={"HbA1c": 7.2},
        clinical_summary="Stable",
        report_analysis={"status": "Reviewed"},
    )

    assert context.patient_id == "123"
    assert context.patient_age == 45
    assert context.patient_gender == "Male"
    assert context.medical_history == ["Diabetes"]
    assert context.current_medications == ["Metformin"]
    assert context.allergies == ["Penicillin"]


def test_conversation_context_invalid_age():
    with pytest.raises(ValidationError):
        ConversationContext(patient_age=-1)


# ---------------------------------------------------------
# ChatRequest
# ---------------------------------------------------------

def test_chat_request_creation():
    request = ChatRequest(
        message="Explain diabetes"
    )

    assert request.message == "Explain diabetes"
    assert request.stream is False
    assert request.temperature == 0.2
    assert request.max_tokens == 500


def test_chat_request_invalid_temperature():
    with pytest.raises(ValidationError):
        ChatRequest(
            message="Hello",
            temperature=2.0
        )


# ---------------------------------------------------------
# ChatResponse
# ---------------------------------------------------------

def test_chat_response_creation():
    response = ChatResponse(
        response="Sample answer",
        provider="dummy"
    )

    assert response.provider == "dummy"
    assert response.response == "Sample answer"
    assert isinstance(response.generated_at, datetime)


# ---------------------------------------------------------
# ConversationHistory
# ---------------------------------------------------------

def test_conversation_history_creation():
    history = ConversationHistory(
        conversation_id="abc123"
    )

    assert history.conversation_id == "abc123"
    assert history.messages == []
    assert isinstance(history.created_at, datetime)
    assert isinstance(history.updated_at, datetime)


# ---------------------------------------------------------
# AssistantConfig
# ---------------------------------------------------------

def test_assistant_config_defaults():
    config = AssistantConfig()

    assert config.provider_name == "dummy"
    assert config.enable_memory is True
    assert config.enable_context is True
    assert config.temperature == 0.2
    assert config.max_tokens == 500


def test_assistant_config_invalid_provider():
    with pytest.raises(ValidationError):
        AssistantConfig(provider_name="invalid")