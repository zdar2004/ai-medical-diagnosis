"""
Integration tests for AI Clinical Assistant.

Tests complete flow:
Conversation Memory
        ↓
Context Builder
        ↓
Prompt Builder
        ↓
Dummy Provider
        ↓
Response
"""

from app.ai_clinical_assistant.conversation_memory import ConversationMemory
from app.ai_clinical_assistant.context_builder import ContextBuilder
from app.ai_clinical_assistant.prompt_builder import PromptBuilder
from app.ai_clinical_assistant.schemas import ConversationContext

from app.report_analysis.providers.dummy_provider import (
    DummyProvider,
)


def test_complete_ai_clinical_assistant_flow():
    """
    Test complete assistant pipeline.
    """

    # 1. Create memory
    memory = ConversationMemory()

    conversation_id = memory.create_conversation()

    # 2. Add conversation messages
    memory.add_user_message(
        conversation_id,
        message="I have high blood pressure."
    )

    # 3. Create clinical context
    context = ConversationContext(
        patient_id="P001",
        patient_age=45,
        patient_gender="Male",
        medical_history=[
            "Hypertension"
        ],
        current_medications=[
            "Amlodipine"
        ],
        allergies=[
            "None"
        ],
    )

    # 4. Build structured context
    context_builder = ContextBuilder(memory)

    structured_context = context_builder.build_context(
        conversation_id,
        context
    )

    assert "patient" in structured_context
    assert "conversation_history" in structured_context


    # 5. Build prompt
    prompt_builder = PromptBuilder()

    prompt = prompt_builder.build_complete_prompt(
        "Explain my condition.",
        structured_context
    )

    assert "AI Clinical Assistant" in prompt
    assert "USER QUESTION" in prompt


    # 6. Generate response using dummy provider
    provider = DummyProvider()

    response = provider.generate(prompt)


    # 7. Validate response
    assert response is not None
    assert len(response) > 0


def test_empty_context_flow():

    """
    Test assistant works without clinical data.
    """

    memory = ConversationMemory()

    conversation_id = memory.create_conversation()


    context_builder = ContextBuilder(memory)

    structured_context = context_builder.build_context(
        conversation_id,
        None
    )


    prompt_builder = PromptBuilder()

    prompt = prompt_builder.build_complete_prompt(
        "What can you tell me?",
        structured_context
    )


    provider = DummyProvider()

    response = provider.generate(prompt)


    assert response is not None
    assert len(response) > 0